"""
Luogu Problem Analysis Tool
- Fetches problem info and solutions from Luogu (www.luogu.com.cn)
- Filters solutions by code quality when no API key is provided
- Analyzes solutions with DeepSeek API when API key is provided
- Runs as a portless desktop app via pywebview (no HTTP server needed)
"""

import re
import sys
import json
import os
import uuid
import base64
import logging
import threading
import time
import shutil
import tempfile
import subprocess
import urllib.parse
import requests
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- PyInstaller resource path resolution ---
# When bundled with PyInstaller (onefile), resources are extracted to
# sys._MEIPASS at runtime. In dev mode, use the script's directory.
def _resource_path(relative):
    """Get absolute path to a bundled resource, works in dev and PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)

# --- Config file location ---
# Store config.json NEXT TO the executable (not inside the bundle) so user
# settings persist across runs. When frozen, sys.executable is the exe path.
if getattr(sys, "frozen", False):
    _APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Server-side config persistence (API key & Cookie)
# ---------------------------------------------------------------------------
CONFIG_FILE = os.path.join(_APP_DIR, "config.json")


def load_config():
    """Load saved config from config.json. Returns dict with api_key, glm_api_key, model, cookie."""
    default = {
        "api_key": "", "glm_api_key": "", "model": "", "cookie": "",
        "vjudge_cookie": "", "vjudge_username": "", "vjudge_password": "",
    }
    if not os.path.exists(CONFIG_FILE):
        return default
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return default
        return {
            "api_key": str(data.get("api_key", "")),
            "glm_api_key": str(data.get("glm_api_key", "")),
            "model": str(data.get("model", "")),
            "cookie": str(data.get("cookie", "")),
            "vjudge_cookie": str(data.get("vjudge_cookie", "")),
            "vjudge_username": str(data.get("vjudge_username", "")),
            "vjudge_password": str(data.get("vjudge_password", "")),
        }
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load config.json: %s", e)
        return default


def save_config(api_key=None, model=None, cookie=None, glm_api_key=None,
                vjudge_cookie=None, vjudge_username=None, vjudge_password=None):
    """Persist config to config.json. Only non-None fields are updated."""
    current = load_config()
    if api_key is not None:
        current["api_key"] = api_key
    if glm_api_key is not None:
        current["glm_api_key"] = glm_api_key
    if model is not None:
        current["model"] = model
    if cookie is not None:
        current["cookie"] = cookie
    if vjudge_cookie is not None:
        current["vjudge_cookie"] = vjudge_cookie
    if vjudge_username is not None:
        current["vjudge_username"] = vjudge_username
    if vjudge_password is not None:
        current["vjudge_password"] = vjudge_password
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        logger.info("Config saved to %s", CONFIG_FILE)
        return True
    except OSError as e:
        logger.error("Failed to write config.json: %s", e)
        return False

# ---------------------------------------------------------------------------
# In-memory + JSON cache layer (persistent to disk, with TTL)
# ---------------------------------------------------------------------------
CACHE_DIR = os.path.join(_APP_DIR, "cache")

def _ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(key):
    """Return the file path for a cache key (sanitized)."""
    _ensure_cache_dir()
    # Sanitize key: replace non-alphanumeric chars with underscore
    safe = re.sub(r'[^a-zA-Z0-9_]', '_', str(key))
    return os.path.join(CACHE_DIR, f"{safe}.json")

def _cache_get(key, ttl_seconds=3600):
    """Get cached data if it exists and hasn't expired. Returns None if not found or expired."""
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ts = data.get("_cached_at", 0)
        if time.time() - ts > ttl_seconds:
            os.remove(path)
            return None
        return data.get("_payload")
    except (json.JSONDecodeError, OSError, KeyError):
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
        return None

def _cache_set(key, data):
    """Store data in cache with current timestamp."""
    path = _cache_path(key)
    _ensure_cache_dir()
    try:
        payload = {"_cached_at": time.time(), "_payload": data}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except OSError as e:
        logger.warning("Cache write failed for %s: %s", key, e)
        return False

def _cache_clear():
    """Delete all cached files."""
    _ensure_cache_dir()
    for fname in os.listdir(CACHE_DIR):
        if fname.endswith(".json"):
            try:
                os.remove(os.path.join(CACHE_DIR, fname))
            except OSError:
                pass
    return True


# ---------------------------------------------------------------------------
# 免责声明 (Disclaimer)
# ---------------------------------------------------------------------------
# 初次启动时展示的免责声明。正文以《免责声明.md》为准（随 EXE 一并打包），
# 文件缺失时回退到内嵌文本，确保应用在任意环境下都能正常展示。
_DISCLAIMER_FALLBACK = (
    "一、用途限制\n"
    "本工具仅供个人学习、交流与算法练习使用，不得用于商业用途及违法违规活动。\n\n"
    "二、数据来源与版权\n"
    "题目、题解、评测数据等来源于洛谷（luogu.com.cn）公开接口或您本人授权的账号数据，"
    "知识产权归洛谷及原出题人所有，本工具不对其完整性、准确性作任何保证。\n\n"
    "三、AI 分析说明\n"
    "AI 智能分析、翻译、讲解等内容由第三方大语言模型生成，仅供参考，请结合判断谨慎使用。\n\n"
    "四、账号与凭证安全\n"
    "您填写的 Cookie、Vjudge 账号密码等凭证仅保存在本机，请妥善保管，因泄露造成的损失本工具及开发者不承担责任。\n\n"
    "五、责任限制\n"
    "本工具按「现状」提供，因使用本工具或第三方接口异常造成的任何损失，本工具及开发者不承担责任。\n\n"
    "六、合规使用\n"
    "请遵守所在国家或地区的法律法规，不得利用本工具进行作弊、侵权、滥用或破坏行为。\n\n"
    "七、条款变更\n"
    "本工具及开发者保留修改本免责声明的权利，修改后自发布之日起生效。"
)


def _load_disclaimer():
    """Read the disclaimer text (prefer the bundled 免责声明.md)."""
    try:
        path = _resource_path("免责声明.md")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return content
    except OSError:
        pass
    return _DISCLAIMER_FALLBACK


def _cache_delete(key):
    """Delete one cached entry by key (best-effort)."""
    try:
        path = _cache_path(key)
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Unsaved code drafts (per-problem autosave, stored next to config.json)
# ---------------------------------------------------------------------------
DRAFTS_FILE = os.path.join(_APP_DIR, "drafts.json")


def _load_drafts():
    """Load {problem_id: code} drafts from drafts.json."""
    if not os.path.exists(DRAFTS_FILE):
        return {}
    try:
        with open(DRAFTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load drafts.json: %s", e)
        return {}


def _save_draft(problem_id, code):
    """Persist a code draft for a problem; empty code removes the draft."""
    drafts = _load_drafts()
    if code.strip():
        drafts[problem_id] = code
    else:
        drafts.pop(problem_id, None)
    with open(DRAFTS_FILE, "w", encoding="utf-8") as f:
        json.dump(drafts, f, ensure_ascii=False, indent=2)


def _get_draft(problem_id):
    """Return the saved draft for a problem (empty string if none)."""
    return _load_drafts().get(problem_id, "")


# ---------------------------------------------------------------------------
# Local submission records (persistent, per-problem history)
# ---------------------------------------------------------------------------
LOCAL_RECORDS_FILE = os.path.join(_APP_DIR, "local_records.json")


def _load_local_records():
    """Load all local records. Returns dict: {pid: [record, ...]}."""
    if not os.path.exists(LOCAL_RECORDS_FILE):
        return {}
    try:
        with open(LOCAL_RECORDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_local_records(data):
    """Save the full local records dict."""
    try:
        with open(LOCAL_RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def _add_local_record(pid, rid, code, lang, status, score, enable_o2):
    """Add a single record to local storage."""
    records = _load_local_records()
    if pid not in records:
        records[pid] = []
    records[pid].insert(0, {
        "rid": rid,
        "code": code,
        "lang": lang,
        "status": status,
        "score": score,
        "enable_o2": bool(enable_o2),
        "timestamp": int(time.time()),
    })
    # Keep only the last 50 records per problem
    records[pid] = records[pid][:50]
    _save_local_records(records)
    return True


def _get_local_records(pid=None):
    """Get local records. If pid is None, return all records grouped by pid."""
    records = _load_local_records()
    if pid:
        return records.get(pid, [])
    return records


def _get_local_stats():
    """Compute local statistics from all records."""
    records = _load_local_records()
    total_submissions = 0
    total_passed = 0
    problem_set = set()
    for pid, recs in records.items():
        problem_set.add(pid)
        for rec in recs:
            total_submissions += 1
            if rec.get("status") == 12:  # AC
                total_passed += 1
    return {
        "totalSubmissions": total_submissions,
        "totalPassed": total_passed,
        "totalProblems": len(problem_set),
        "problems": list(problem_set),
    }


# ---------------------------------------------------------------------------
# Problem collections (题单/收藏), stored next to config.json
# ---------------------------------------------------------------------------
COLLECTIONS_FILE = os.path.join(_APP_DIR, "collections.json")

DEFAULT_COLLECTION_ID = "default"


def _load_collections():
    """Load {lists: [{id, name, problems: [{pid, title, difficulty, addedAt}]}]}.

    A "default" collection is always ensured to exist.
    """
    data = {"lists": []}
    if os.path.exists(COLLECTIONS_FILE):
        try:
            with open(COLLECTIONS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict) and isinstance(loaded.get("lists"), list):
                data = loaded
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load collections.json: %s", e)
    if not any(lst.get("id") == DEFAULT_COLLECTION_ID for lst in data["lists"]):
        data["lists"].insert(0, {
            "id": DEFAULT_COLLECTION_ID,
            "name": "默认题单",
            "problems": [],
        })
    return data


def _save_collections(data):
    """Persist the full collections data to collections.json."""
    with open(COLLECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_collection(name):
    """Create a new collection and return it. Raises ValueError on bad input."""
    name = (name or "").strip()
    if not name:
        raise ValueError("题单名称不能为空")
    data = _load_collections()
    for lst in data["lists"]:
        if lst.get("name", "").lower() == name.lower():
            raise ValueError("已存在同名题单")
    cid = "c_" + uuid.uuid4().hex[:8]
    lst = {"id": cid, "name": name, "problems": []}
    data["lists"].append(lst)
    _save_collections(data)
    return lst


def add_to_collection(pid, list_id, title="", difficulty=0):
    """Add a problem to a collection (idempotent). Returns the collection."""
    pid = (pid or "").strip()
    if not pid:
        raise ValueError("缺少题号")
    data = _load_collections()
    lst = next((x for x in data["lists"] if x.get("id") == list_id), None)
    if not lst:
        raise ValueError("题单不存在")
    if any(p.get("pid") == pid for p in lst["problems"]):
        return lst
    lst["problems"].append({
        "pid": pid,
        "title": title or "",
        "difficulty": int(difficulty or 0),
        "addedAt": int(time.time()),
    })
    _save_collections(data)
    return lst


def remove_from_collection(pid, list_id=None):
    """Remove a problem from a collection (or all lists when list_id is None).

    Returns the updated list of collections.
    """
    pid = (pid or "").strip()
    if not pid:
        raise ValueError("缺少题号")
    data = _load_collections()
    changed = False
    for lst in data["lists"]:
        if list_id is not None and lst.get("id") != list_id:
            continue
        before = len(lst["problems"])
        lst["problems"] = [p for p in lst["problems"] if p.get("pid") != pid]
        if len(lst["problems"]) != before:
            changed = True
    if changed:
        _save_collections(data)
    return data["lists"]


# ---------------------------------------------------------------------------
# Luogu API helpers
# ---------------------------------------------------------------------------

LUOGU_BASE = "https://www.luogu.com.cn"
LUOGU_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.luogu.com.cn/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SCRIPT_DATA_RE = re.compile(r'<script[^>]*>(\{"instance".*?)</script>', re.DOTALL)

# Cache for Luogu tag ID -> name mapping
_TAG_CACHE = None


def fetch_luogu_tags():
    """Fetch and cache Luogu problem tag ID -> name mapping."""
    global _TAG_CACHE
    if _TAG_CACHE is not None:
        return _TAG_CACHE

    url = f"{LUOGU_BASE}/_lfe/tags"
    try:
        resp = requests.get(url, headers=LUOGU_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
        logger.warning("Failed to fetch Luogu tags: %s", e)
        _TAG_CACHE = {}
        return _TAG_CACHE

    tag_list = data.get("tags", []) or []
    mapping = {}
    for t in tag_list:
        if isinstance(t, dict) and "id" in t:
            mapping[int(t["id"])] = t.get("name", "")
    _TAG_CACHE = mapping
    logger.info("Loaded %d Luogu tags", len(mapping))
    return mapping

# Full-width to half-width character mappings commonly mistyped in cookies
FULLWIDTH_REPLACEMENTS = {
    "\uff1b": ";",  # ；
    "\uff0c": ",",  # ，
    "\uff1a": ":",  # ：
    "\uff1d": "=",  # ＝
    "\uff08": "(",  # （
    "\uff09": ")",  # ）
    "\u3000": " ",  # 全角空格
}


def sanitize_cookie(cookie):
    """Replace common full-width characters with half-width equivalents."""
    if not cookie:
        return cookie
    for full, half in FULLWIDTH_REPLACEMENTS.items():
        cookie = cookie.replace(full, half)
    return cookie.strip()


def extract_luogu_data(html):
    """Extract embedded JSON data from Luogu HTML page (script tag starting with {"instance")."""
    match = SCRIPT_DATA_RE.search(html)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def _format_tags(raw_tags, tag_map=None):
    """Map numeric Luogu tag IDs to human-readable names (str tags pass through)."""
    if tag_map is None:
        tag_map = fetch_luogu_tags()
    out = []
    for t in raw_tags or []:
        if isinstance(t, int):
            name = tag_map.get(t, "")
            if name:
                out.append(name)
        elif isinstance(t, str) and t:
            out.append(t)
    return out


def _query_luogu_search(keyword, page=1, session=None):
    """Single search request to Luogu. Returns (total_count, raw_result_list).

    If `session` is provided, it is reused to benefit from HTTP keep-alive
    (connection pooling), which significantly reduces per-request latency.
    """
    url = f"{LUOGU_BASE}/problem/list"
    params = {"keyword": keyword, "page": page, "type": "P", "_contentOnly": 1}
    try:
        resp = (session or requests).get(url, headers=LUOGU_HEADERS, params=params, timeout=8)
        resp.raise_for_status()
    except requests.RequestException as e:
        code = getattr(getattr(e, "response", None), "status_code", None)
        if code in (403, 429):
            raise RuntimeError("洛谷接口访问受限（403），请稍后重试或重新填入 Cookie")
        logger.error("Failed to search problems for %s: %s", keyword, e)
        raise RuntimeError(f"搜索题库失败: {e}")

    data = extract_luogu_data(resp.text)
    if not data:
        raise RuntimeError("无法解析搜索结果页面数据")
    if data.get("status") != 200:
        err_msg = data.get("data", {}).get("errorMessage", "搜索失败")
        raise RuntimeError(err_msg)

    problems_data = data.get("data", {}).get("problems", {})
    total = problems_data.get("count", 0)
    raw_list = problems_data.get("result", []) or []
    return total, raw_list


def search_problems(keyword, page=1):
    """Search Luogu problem database by keyword.

    Luogu's search endpoint does substring matching that is too loose
    (e.g. searching "P78" returns problems whose pid contains any of 7/8).
    To support partial pid matching for bare numbers AND keep results strict,
    we:
      1. Generate query variants (bare number <-> prefixed pid) so Luogu can
         return candidate problems it would otherwise miss.
      2. Filter the merged results locally so that either the pid or the title
         fully contains the original keyword string.
      3. Luogu sorts by relevance, so matching pids may appear on later pages.
         We fetch the first page of all query variants IN PARALLEL using a
         shared session (HTTP keep-alive), then only fetch additional pages
         for variants that produced matches.
    """
    cache_key = f"search_{keyword}_{page}"
    cached = _cache_get(cache_key, ttl_seconds=1800)
    if cached is not None:
        return cached
    if not keyword or not keyword.strip():
        return {"count": 0, "problems": []}
    keyword = keyword.strip()

    queries = [keyword]
    # If keyword is a pure number (e.g. "78"), also try all common pid prefixes
    if keyword.isdigit():
        for prefix in ("P", "B", "CF", "SP", "AT", "UVA"):
            queries.append(prefix + keyword)
    # If keyword is an already-prefixed pid like "P78", also try the digits
    elif re.match(r"^[A-Za-z]+\d+$", keyword):
        queries.append(keyword[1:])

    MAX_MATCHES = 50        # stop after collecting this many strict matches
    MAX_PAGES_PER_QUERY = 3  # hard cap on pages to fetch per query variant

    kw_lower = keyword.lower()
    seen_pids = set()
    merged = []

    def _filter_and_collect(q_list):
        """Filter a raw result list and append strict matches to merged."""
        for p in q_list:
            pid = p.get("pid", "")
            title = p.get("name", "")
            if not pid or pid in seen_pids:
                continue
            # Strict filter: the original keyword must appear in pid OR title.
            if kw_lower not in pid.lower() and kw_lower not in title.lower():
                continue
            seen_pids.add(pid)
            merged.append({
                "pid": pid,
                "title": title,
                "difficulty": p.get("difficulty", 0),
                "tags": _format_tags(p.get("tags", [])),
                "totalSubmit": p.get("totalSubmit", 0),
                "totalAccepted": p.get("totalAccepted", 0),
            })
            if len(merged) >= MAX_MATCHES:
                break

    # Use a single session with HTTP keep-alive so all parallel requests
    # reuse the same TCP/TLS connection, dramatically cutting latency.
    session = requests.Session()
    session.headers.update(LUOGU_HEADERS)
    adapter = requests.adapters.HTTPAdapter(pool_connections=8, pool_maxsize=8)
    session.mount("https://", adapter)
    # Warm up so Luogu's anti-bot sets the C3VK challenge cookie; otherwise
    # the first parallel batch can be answered with 403.
    _warm_session(session)

    # Phase 1: Fetch page 1 of ALL query variants in parallel
    failed_count = 0  # number of query variants that errored (e.g. 403)
    with ThreadPoolExecutor(max_workers=min(8, len(queries))) as executor:
        future_to_query = {
            executor.submit(_query_luogu_search, q, 1, session): q for q in queries
        }
        # Track which queries have more pages and might yield additional matches.
        # Only queries that produced >= 1 strict match on page 1 are eligible
        # for additional page fetches (Luogu sorts by relevance, so if page 1
        # had zero matches, later pages almost certainly won't either).
        query_more = {}  # query -> (total_count, last_page_fetched)
        for future in as_completed(future_to_query):
            if len(merged) >= MAX_MATCHES:
                break
            q = future_to_query[future]
            try:
                q_total, q_list = future.result()
            except RuntimeError:
                failed_count += 1
                continue
            if not q_list:
                continue
            before = len(merged)
            _filter_and_collect(q_list)
            # Only fetch more pages if this query produced strict matches
            if len(merged) > before and q_total > 50 and len(merged) < MAX_MATCHES:
                query_more[q] = (q_total, 1)

    # Phase 2: Fetch additional pages for promising queries, also in parallel.
    while query_more and len(merged) < MAX_MATCHES:
        tasks = {}
        with ThreadPoolExecutor(max_workers=min(8, len(query_more))) as executor:
            for q, (q_total, last_page) in list(query_more.items()):
                next_page = last_page + 1
                if next_page > MAX_PAGES_PER_QUERY:
                    query_more.pop(q, None)
                    continue
                if next_page * 50 >= q_total:
                    query_more.pop(q, None)
                    continue
                tasks[executor.submit(_query_luogu_search, q, next_page, session)] = (q, next_page)
            if not tasks:
                break
            for future in as_completed(tasks):
                if len(merged) >= MAX_MATCHES:
                    break
                q, fetched_page = tasks[future]
                try:
                    q_total, q_list = future.result()
                except RuntimeError:
                    query_more.pop(q, None)
                    continue
                if not q_list:
                    query_more.pop(q, None)
                    continue
                before = len(merged)
                _filter_and_collect(q_list)
                # Only keep fetching if this page produced matches
                if len(merged) > before and fetched_page * 50 < q_total and fetched_page < MAX_PAGES_PER_QUERY:
                    query_more[q] = (q_total, fetched_page)
                else:
                    query_more.pop(q, None)

    session.close()

    # Empty-result handling: distinguish "blocked by Luogu" from "no results",
    # and fall back to a direct problem-page fetch for pids that Luogu's
    # search index missed. Luogu's fuzzy search fails to return exact CF/SP/UVA
    # pids with a trailing letter (e.g. CF1551A, CF1551B1), so accept any
    # pid-like keyword (letters/digits/underscores with at least one digit,
    # e.g. P3740, CF1551A, AT_abc001_a) for the direct fetch.
    if not merged and failed_count > 0:
        raise RuntimeError("洛谷接口访问受限（403），请稍后重试或重新填入洛谷 Cookie")
    if not merged and failed_count == 0 and re.match(r"^[A-Za-z][A-Za-z0-9_]*\d[A-Za-z0-9_]*$", keyword):
        try:
            direct = fetch_problem(keyword, load_config().get("cookie", ""))
            if direct.get("pid"):
                merged.append({
                    "pid": direct["pid"],
                    "title": direct.get("title", ""),
                    "difficulty": direct.get("difficulty", 0),
                    "tags": direct.get("tags", []),
                    "totalSubmit": direct.get("totalSubmit", 0),
                    "totalAccepted": direct.get("totalAccepted", 0),
                })
        except Exception:
            logger.warning("Direct pid fallback failed for %s", keyword)

    result = {"count": len(merged), "problems": merged}
    _cache_set(cache_key, result)
    return result


def search_users(keyword, limit=10):
    """Search Luogu users by name or UID.

    Uses the official /api/user/search endpoint (returns JSON, no auth
    required). Numeric keywords also match UIDs directly.
    Returns a list of {uid, name, avatar, background, slogan, ccfLevel,
    xcpcLevel, color, isAdmin, isBanned}.
    """
    keyword = (keyword or "").strip()
    if not keyword:
        raise RuntimeError("缺少搜索关键词")
    url = f"{LUOGU_BASE}/api/user/search"
    try:
        resp = requests.get(url, headers=LUOGU_HEADERS,
                            params={"keyword": keyword}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
        logger.error("Failed to search users for %s: %s", keyword, e)
        raise RuntimeError(f"搜索用户失败: {e}")

    users = (data or {}).get("users", []) or []
    out = []
    for u in users[:limit]:
        if not isinstance(u, dict):
            continue
        out.append({
            "uid": u.get("uid", 0),
            "name": u.get("name", ""),
            "avatar": u.get("avatar", ""),
            "background": u.get("background", ""),
            "slogan": u.get("slogan", "") or "",
            "ccfLevel": u.get("ccfLevel", 0),
            "xcpcLevel": u.get("xcpcLevel", 0),
            "color": u.get("color", ""),
            "isAdmin": bool(u.get("isAdmin", False)),
            "isBanned": bool(u.get("isBanned", False)),
        })
    return out


def fetch_default_problems(page=1):
    """Fetch Luogu's default problem list (no keyword search).

    Mirrors the default list shown on luogu.com.cn/problem/list.
    Returns {"count": N, "problems": [...]}.
    """
    cache_key = f"default_problems_{page}"
    cached = _cache_get(cache_key, ttl_seconds=1800)
    if cached is not None:
        return cached
    url = f"{LUOGU_BASE}/problem/list"
    params = {"page": page, "type": "P", "_contentOnly": 1}
    session = _warm_session(build_luogu_session(""))
    try:
        resp = session.get(url, params=params, timeout=8)
        resp.raise_for_status()
    except requests.RequestException as e:
        code = getattr(getattr(e, "response", None), "status_code", None)
        if code in (403, 429):
            raise RuntimeError("洛谷接口访问受限（403），请稍后重试或重新填入 Cookie")
        raise RuntimeError(f"获取题目列表失败: {e}")

    data = extract_luogu_data(resp.text)
    if not data:
        raise RuntimeError("无法解析题目列表数据")

    problems_data = data.get("data", {}).get("problems", {})
    total = problems_data.get("count", 0)
    raw_list = problems_data.get("result", []) or []

    formatted = []
    for p in raw_list:
        formatted.append({
            "pid": p.get("pid", ""),
            "title": p.get("name", ""),
            "difficulty": p.get("difficulty", 0),
            "tags": _format_tags(p.get("tags", [])),
            "totalSubmit": p.get("totalSubmit", 0),
            "totalAccepted": p.get("totalAccepted", 0),
        })
    result = {"count": total, "problems": formatted}
    _cache_set(cache_key, result)
    return result


def _extract_uid_from_cookie(cookie):
    """Extract _uid value from a cookie string. Returns None if not found."""
    if not cookie:
        return None
    for part in cookie.split(";"):
        part = part.strip()
        if part.startswith("_uid="):
            return part[5:].strip()
    return None


def fetch_user_info(cookie="", uid=None):
    """Fetch user profile info (uid, name, avatar, ranking, rating) from Luogu.

    `uid` may be given explicitly to view ANY user (cookie optional, used as
    the viewing session). When `uid` is omitted it is derived from `_uid` in
    the cookie (i.e. the logged-in user themselves).

    Uses the _contentOnly JSON endpoint so we get structured data without
    parsing HTML. Returns dict with uid, name, avatar, ranking, rating, etc.
    """
    cookie = sanitize_cookie(cookie or "")
    uid = str(uid or _extract_uid_from_cookie(cookie) or "").strip()
    if not uid:
        raise RuntimeError("缺少用户 ID，无法获取用户信息")

    session = build_luogu_session(cookie)
    # Warm up to get challenge cookies
    try:
        session.get(f"{LUOGU_BASE}/", timeout=10)
    except requests.RequestException:
        pass

    url = f"{LUOGU_BASE}/user/{uid}"
    try:
        resp = session.get(url, timeout=15)
    except requests.RequestException as e:
        raise RuntimeError(f"获取用户信息失败: {e}")

    if "auth/login" in (resp.url or "").lower():
        raise RuntimeError("Cookie 已失效，请重新填入洛谷 Cookie")

    data = extract_luogu_data(resp.text)
    if not isinstance(data, dict):
        raise RuntimeError("无法解析用户页面数据")

    # 用户主页数据在顶层 data.user 键（页面无 currentData）
    dd = data.get("data") or {}
    if isinstance(dd, dict) and dd.get("errorMessage"):
        # e.g. 403-restricted accounts return an error payload instead of a user
        raise RuntimeError(dd.get("errorMessage") or "无法获取用户数据")
    user = dd.get("user") or data.get("user", {})
    if not user:
        raise RuntimeError("用户数据为空，可能 Cookie 已失效")

    # Public rich data available on the homepage page: contest prizes,
    # 综合分 (gu) breakdown and elo history.
    prizes = []
    for p in (dd.get("prizes") or []):
        if not isinstance(p, dict):
            continue
        inner = p.get("prize") or {}
        if isinstance(inner, dict):
            prizes.append({
                "year": inner.get("year", 0),
                "contest": inner.get("contest", ""),
                "event": inner.get("event", ""),
                "prize": inner.get("prize", ""),
            })
    gu = dd.get("gu") or {}
    if not isinstance(gu, dict):
        gu = {}
    gu_scores = gu.get("scores") or {}
    if not isinstance(gu_scores, dict):
        gu_scores = {}
    gu_out = {
        "rating": gu.get("rating", 0) or gu_scores.get("rating", 0),
        "social": gu_scores.get("social", 0),
        "basic": gu_scores.get("basic", 0),
        "contest": gu_scores.get("contest", 0),
        "practice": gu_scores.get("practice", 0),
        "prize": gu_scores.get("prize", 0),
    }
    elo_history = []
    for e in (dd.get("elo") or []):
        if not isinstance(e, dict):
            continue
        elo_history.append({
            "rating": e.get("rating", 0),
            "time": e.get("time", 0),
            "latest": bool(e.get("latest", False)),
            "contest": ((e.get("contest") or {}).get("name", "")
                        if isinstance(e.get("contest"), dict) else ""),
        })

    return {
        "uid": user.get("uid", uid),
        "name": user.get("name", ""),
        "avatar": user.get("avatar", ""),
        "background": user.get("background", ""),
        "ranking": user.get("ranking", 0),
        "rating": user.get("rating", 0) or user.get("ratingValue", 0) or user.get("eloValue", 0),
        "slogan": user.get("slogan", ""),
        "ccfLevel": user.get("ccfLevel", 0),
        "xcpcLevel": user.get("xcpcLevel", 0),
        "verified": bool(user.get("verified", False)),
        "followerCount": user.get("followerCount", 0),
        "followingCount": user.get("followingCount", 0),
        "registerTime": user.get("registerTime", 0),
        "introduction": user.get("introduction", ""),
        "blogAddress": user.get("blogAddress", ""),
        "passedProblemCount": user.get("passedProblemCount", 0),
        "submittedProblemCount": user.get("submittedProblemCount", 0),
        "prizes": prizes,
        "guScore": gu_out,
        "eloHistory": elo_history,
    }


def fetch_user_practice_detail(cookie="", uid=None):
    """Fetch practice detail from Luogu /user/{uid}/practice page.

    `uid` may be given explicitly to view ANY user (practice data is public).
    When omitted it is derived from the cookie's _uid.

    Returns dict with:
      - passedProblems: list of {pid, title, difficulty}
      - submittedProblems: list of {pid, title, difficulty} (attempted, not passed)
      - difficultyStats: {difficulty: {passed, submitted}} where submitted
        counts every submitted problem (passed counts only AC problems)
      - totalPassed, totalSubmitted, totalAttempted
    """
    cookie = sanitize_cookie(cookie or "")
    uid = str(uid or _extract_uid_from_cookie(cookie) or "").strip()
    if not uid:
        raise RuntimeError("缺少用户 ID，无法获取练习数据")

    session = build_luogu_session(cookie)
    # Warm up
    try:
        session.get(f"{LUOGU_BASE}/", timeout=10)
    except requests.RequestException:
        pass

    url = f"{LUOGU_BASE}/user/{uid}/practice"
    try:
        resp = session.get(url, timeout=15)
    except requests.RequestException as e:
        raise RuntimeError(f"获取练习数据失败: {e}")

    if "auth/login" in (resp.url or "").lower():
        raise RuntimeError("Cookie 已失效，请重新填入洛谷 Cookie")

    data = extract_luogu_data(resp.text)
    if not isinstance(data, dict):
        raise RuntimeError("无法解析练习页面数据")

    # 练习页数据在 data.passed（已通过）和 data.submitted（尝试未通过）
    dd = data.get("data", {})
    if not isinstance(dd, dict):
        raise RuntimeError("练习页面数据为空")

    passed_list = dd.get("passed") or []
    submitted_list = dd.get("submitted") or []  # 尝试过但未通过
    user_stats = dd.get("user") or {}
    passed_count = user_stats.get("passedProblemCount") or len(passed_list)
    submitted_count = user_stats.get("submittedProblemCount") or (
        len(passed_list) + len(submitted_list))

    # Build difficulty stats: submitted 计入所有提交过的题，passed 仅计入通过的题
    # Luogu now has 9 difficulty levels (0-8) after the 2026-06 restructure.
    difficulty_stats = {}
    type_stats = {}
    for i in range(9):
        difficulty_stats[i] = {"passed": 0, "submitted": 0}

    for p in submitted_list:  # 未通过的题：计入 submitted
        if not isinstance(p, dict):
            continue
        diff = p.get("difficulty", 0)
        if diff not in difficulty_stats:
            difficulty_stats[diff] = {"passed": 0, "submitted": 0}
        difficulty_stats[diff]["submitted"] += 1
        ptype = p.get("type", "") or "?"
        ts = type_stats.setdefault(ptype, {"passed": 0, "submitted": 0})
        ts["submitted"] += 1

    for p in passed_list:  # 已通过的题：计入 submitted 和 passed
        if not isinstance(p, dict):
            continue
        diff = p.get("difficulty", 0)
        if diff not in difficulty_stats:
            difficulty_stats[diff] = {"passed": 0, "submitted": 0}
        difficulty_stats[diff]["submitted"] += 1
        difficulty_stats[diff]["passed"] += 1
        ptype = p.get("type", "") or "?"
        ts = type_stats.setdefault(ptype, {"passed": 0, "submitted": 0})
        ts["submitted"] += 1
        ts["passed"] += 1

    # Format problem lists (keep only essential fields)
    fmt_problems = lambda lst: [
        {"pid": p.get("pid", ""), "title": p.get("title", p.get("name", "")),
         "difficulty": p.get("difficulty", 0)}
        for p in lst if isinstance(p, dict)
    ]

    return {
        "passedProblems": fmt_problems(passed_list),
        "submittedProblems": fmt_problems(submitted_list),
        "difficultyStats": difficulty_stats,
        "typeStats": type_stats,
        "totalPassed": passed_count,
        "totalSubmitted": submitted_count,
        "totalAttempted": max(0, submitted_count - passed_count),
    }


def fetch_recent_submissions(cookie="", uid=None, limit=20):
    """Fetch the most recent submission records from Luogu /record/list.

    `uid` may be given explicitly to view ANY user's records (needs a logged
    in session — the cookie — since /record/list requires authentication).
    When omitted it is derived from the cookie's _uid.

    Returns a list of up to `limit` records, each formatted as
    {pid, title, type, status, score, fullScore, timeMs, memoryKB, submitTime}.
    """
    cookie = sanitize_cookie(cookie or "")
    uid = str(uid or _extract_uid_from_cookie(cookie) or "").strip()
    if not uid:
        raise RuntimeError("缺少用户 ID，无法获取提交记录")

    session = build_luogu_session(cookie)
    # Warm up
    try:
        session.get(f"{LUOGU_BASE}/", timeout=10)
    except requests.RequestException:
        pass

    url = f"{LUOGU_BASE}/record/list"
    params = {"user": uid, "page": 1, "_contentOnly": 1}
    try:
        resp = session.get(url, params=params, timeout=15)
    except requests.RequestException as e:
        raise RuntimeError(f"获取提交记录失败: {e}")

    if "auth/login" in (resp.url or "").lower():
        raise RuntimeError("该用户的提交记录未公开或需登录后查看")

    try:
        data = resp.json()
    except (json.JSONDecodeError, ValueError):
        data = extract_luogu_data(resp.text)
    if not isinstance(data, dict):
        raise RuntimeError("无法解析提交记录数据")

    cd = data.get("currentData")
    if not isinstance(cd, dict):
        dd = data.get("data")
        cd = dd.get("currentData") if isinstance(dd, dict) else None
    if not isinstance(cd, dict) or not isinstance(cd.get("records"), dict):
        raise RuntimeError("提交记录数据为空")

    records = cd["records"].get("result") or []
    out = []
    for rec in records[:limit]:
        if not isinstance(rec, dict):
            continue
        problem = rec.get("problem") or {}
        out.append({
            "rid": rec.get("id", 0),
            "pid": problem.get("pid", ""),
            "title": problem.get("title", ""),
            "type": problem.get("type", ""),
            "status": rec.get("status", 0),
            "score": rec.get("score", 0),
            "fullScore": problem.get("fullScore", 100),
            "timeMs": rec.get("time", 0),
            "memoryKB": rec.get("memory", 0),
            "submitTime": rec.get("submitTime", 0),
        })

    # Luogu's record-level status 14 is the generic "Unaccepted" (未通过)
    # aggregate. The specific verdict (TLE/WA/RE...) only lives in the record
    # detail's test cases, so fetch those and derive the real verdict.
    VERDICT_RANK = {14: 0, 11: 1, 9: 2, 4: 3, 5: 4, 7: 5, 6: 6, 8: 7, 12: 8}

    def _derive_verdict(rid):
        """Return the specific status code from a record's test cases."""
        if not rid:
            return None
        try:
            resp = session.get(f"{LUOGU_BASE}/record/{rid}?_contentOnly=1", timeout=15)
            if "auth/login" in (resp.url or "").lower():
                return None
            try:
                data = resp.json()
            except (json.JSONDecodeError, ValueError):
                data = extract_luogu_data(resp.text)
            if not isinstance(data, dict):
                return None
            rd = _find_record_data(data)
            if not isinstance(rd, dict):
                return None
            subtasks = ((rd.get("detail") or {}).get("judgeResult") or {}).get("subtasks") or []
            seen = set()
            for st in subtasks:
                if not isinstance(st, dict):
                    continue
                tc_dict = st.get("testCases", {})
                tc_iter = tc_dict.values() if isinstance(tc_dict, dict) else (tc_dict or [])
                for tc in tc_iter:
                    if isinstance(tc, dict):
                        seen.add(tc.get("status", 0))
            non_ac = [s for s in seen if s not in (8, 12)]
            if not non_ac:
                return 12
            return min(non_ac, key=lambda s: VERDICT_RANK.get(s, 99))
        except requests.RequestException:
            return None

    to_derive = [rec for rec in out if rec.get("status") == 14]
    if to_derive:
        with ThreadPoolExecutor(max_workers=10) as executor:
            derived = dict(executor.map(
                lambda rec: (rec["rid"], _derive_verdict(rec["rid"])), to_derive))
        for rec in out:
            if rec.get("status") == 14 and derived.get(rec["rid"]):
                rec["status"] = derived[rec["rid"]]

    return out


def fetch_user_practice(cookie):
    """Fetch the user's submission status on Luogu.

    Fetches ALL submission records (no status filter) from /record/list,
    then classifies each problem pid into:
      - "passed": at least one submission with full score (status == 12)
      - "submitted": has at least one submission (any status)

    Returns a dict {"passed": set(...), "submitted": set(...)}.
    Returns empty sets if cookie is missing, _uid cannot be parsed, or
    the fetch fails.

    Luogu's anti-crawl requires warming up the session first (visiting the
    homepage) so that the C3VK challenge cookie is set. Pages are fetched
    in parallel via ThreadPoolExecutor for speed.
    """
    empty = {"passed": set(), "submitted": set()}
    cookie = sanitize_cookie(cookie)
    if not cookie:
        return empty

    uid = _extract_uid_from_cookie(cookie)
    if not uid:
        return empty

    session = build_luogu_session(cookie)

    # Warm up: visit homepage so the server sets any challenge cookies
    # (C3VK etc.). Without this, /record/list redirects to /auth/login.
    try:
        session.get(f"{LUOGU_BASE}/", timeout=10)
    except requests.RequestException:
        pass

    url = f"{LUOGU_BASE}/record/list"

    def _fetch_page(page):
        """Fetch one page of records. Returns list of record dicts or []."""
        params = {"user": uid, "page": page, "_contentOnly": 1}
        try:
            resp = session.get(url, params=params, timeout=15)
            if "auth/login" in resp.url:
                return []
            try:
                data = resp.json()
            except (json.JSONDecodeError, ValueError):
                data = extract_luogu_data(resp.text)
            if not isinstance(data, dict):
                return []
            cd = data.get("currentData")
            if not isinstance(cd, dict):
                dd = data.get("data")
                cd = dd.get("currentData") if isinstance(dd, dict) else None
                if not isinstance(cd, dict):
                    return []
            records = cd.get("records")
            if not isinstance(records, dict):
                return []
            return records.get("result") or []
        except requests.RequestException:
            return []

    # Fetch page 1 to get total count
    first_page = _fetch_page(1)
    if not first_page:
        logger.warning("Failed to fetch first page of records for uid=%s", uid)
        return empty

    # Determine total pages from count (20 records per page)
    try:
        resp = session.get(url, params={"user": uid, "page": 1, "_contentOnly": 1}, timeout=15)
        total_count = 0
        if "auth/login" not in resp.url:
            try:
                d = resp.json()
            except (json.JSONDecodeError, ValueError):
                d = extract_luogu_data(resp.text)
            if isinstance(d, dict):
                cd = d.get("currentData") or (d.get("data", {}) or {}).get("currentData")
                if isinstance(cd, dict) and isinstance(cd.get("records"), dict):
                    total_count = cd["records"].get("count", 0)
    except requests.RequestException:
        total_count = 0

    total_pages = max(1, (total_count + 19) // 20) if total_count else 1
    MAX_PAGES = 100  # safety cap; 100 * 20 = 2000 records
    total_pages = min(total_pages, MAX_PAGES)

    logger.info("Fetching %d pages of records for uid=%s", total_pages, uid)

    # Fetch remaining pages in parallel
    all_records = list(first_page)
    if total_pages > 1:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(_fetch_page, p): p for p in range(2, total_pages + 1)}
            for future in as_completed(futures):
                all_records.extend(future.result())

    # Classify each problem
    passed = set()
    submitted = set()
    for rec in all_records:
        if not isinstance(rec, dict):
            continue
        problem = rec.get("problem")
        if not isinstance(problem, dict) or not problem.get("pid"):
            continue
        pid = problem["pid"]
        submitted.add(pid)
        # status 12 = AC (full score)
        if rec.get("status") == 12:
            passed.add(pid)

    logger.info("Fetched %d records: %d submitted, %d passed for uid=%s",
                len(all_records), len(submitted), len(passed), uid)
    return {"passed": passed, "submitted": submitted}


def _fetch_all_remote_records(cookie, ttl_seconds=3600, max_age_days=None):
    """Fetch submission records from Luogu, keeping timestamps.

    Unlike fetch_user_practice (which collapses records into passed/submitted
    sets), this keeps each raw record so the heatmap and advanced stats can
    reflect every submission. Results are disk-cached for `ttl_seconds`.

    If `max_age_days` is given, pagination stops as soon as a whole page is
    older than that window (records are returned newest-first), so callers
    that only need recent history don't download hundreds of pages.

    Returns a list of {rid, pid, status, score, lang, submitTime}.
    Empty list if the cookie is missing, uid cannot be parsed, or fetch fails.
    """
    cookie = sanitize_cookie(cookie or "")
    uid = _extract_uid_from_cookie(cookie) if cookie else ""
    if not uid:
        return []
    # Include the window in the cache key so the full-history and windowed
    # (heatmap) variants never share/corrupt each other's cached payload.
    cache_key = f"all_records_{uid}" if max_age_days is None else f"all_records_{uid}_w{int(max_age_days)}"
    cached = _cache_get(cache_key, ttl_seconds=ttl_seconds)
    if cached is not None:
        return cached

    session = build_luogu_session(cookie)
    # Warm up: visit homepage so the server sets any challenge cookies.
    try:
        session.get(f"{LUOGU_BASE}/", timeout=10)
    except requests.RequestException:
        pass

    url = f"{LUOGU_BASE}/record/list"

    def _fetch_page(page):
        params = {"user": uid, "page": page, "_contentOnly": 1}
        try:
            resp = session.get(url, params=params, timeout=15)
            if "auth/login" in resp.url:
                return [], 0
            try:
                data = resp.json()
            except (json.JSONDecodeError, ValueError):
                data = extract_luogu_data(resp.text)
            if not isinstance(data, dict):
                return [], 0
            cd = data.get("currentData")
            if not isinstance(cd, dict):
                dd = data.get("data")
                cd = dd.get("currentData") if isinstance(dd, dict) else None
                if not isinstance(cd, dict):
                    return [], 0
            records = cd.get("records")
            if not isinstance(records, dict):
                return [], 0
            return records.get("result") or [], records.get("count") or 0
        except requests.RequestException:
            return [], 0

    first_page, total_count = _fetch_page(1)
    if not first_page:
        logger.warning("Failed to fetch first page of records for uid=%s", uid)
        return []

    # 20 records per page; cap at 500 pages (10000 records) so heavy users'
    # full history isn't truncated.
    total_pages = max(1, (total_count + 19) // 20) if total_count else 1
    total_pages = min(total_pages, 500)
    logger.info("Fetching %d pages of records for uid=%s", total_pages, uid)

    all_raw = list(first_page)
    if total_pages > 1:
        # Records are sorted newest-first. When a max-age window is set
        # (e.g. heatmap only needs recent history), stop paging once the whole
        # page is older than the cutoff so we skip the oldest pages.
        if max_age_days is not None:
            cutoff = int(time.time()) - int(max_age_days) * 86400
            page = 2
            while page <= total_pages:
                recs, _ = _fetch_page(page)
                if not recs:
                    break
                all_raw.extend(recs)
                oldest = min((r.get("submitTime") or 0) for r in recs if isinstance(r, dict))
                if oldest and oldest < cutoff:
                    break
                page += 1
        else:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(_fetch_page, p): p for p in range(2, total_pages + 1)}
                for future in as_completed(futures):
                    all_raw.extend(future.result()[0])

    out = []
    for rec in all_raw:
        if not isinstance(rec, dict):
            continue
        problem = rec.get("problem")
        pid = problem.get("pid", "") if isinstance(problem, dict) else ""
        if not pid:
            continue
        out.append({
            "rid": rec.get("id", 0),
            "pid": pid,
            "status": rec.get("status", 0),
            "score": rec.get("score", 0) or 0,
            "lang": rec.get("language", 0) or 0,
            "submitTime": rec.get("submitTime", 0) or 0,
        })

    _cache_set(cache_key, out)
    logger.info("Fetched %d remote records for uid=%s", len(out), uid)
    return out


def _merge_all_records(cookie, max_age_days=None):
    """Merge local records with remote Luogu records (deduped by rid).

    Local records carry the submitted code; remote records carry the full
    submission history. Remote entries are only added for rids not already
    present locally so nothing is double-counted.

    `max_age_days` (optional) limits remote pagination to a recent window
    (see _fetch_all_remote_records); local records are always included.
    """
    merged = {}
    for pid, recs in _load_local_records().items():
        for rec in recs:
            rid = rec.get("rid")
            key = rid if rid is not None else ("l", pid, rec.get("timestamp"))
            merged[key] = {
                "rid": rid,
                "pid": pid,
                "status": rec.get("status", 0),
                "score": rec.get("score", 0) or 0,
                "lang": rec.get("lang", 0) or 0,
                "timestamp": rec.get("timestamp", 0) or 0,
            }
    try:
        remote = _fetch_all_remote_records(cookie, max_age_days=max_age_days)
    except Exception:
        logger.exception("Failed to fetch remote records for stats")
        remote = []
    for rec in remote:
        rid = rec.get("rid")
        key = rid if rid is not None else ("r", rec.get("pid"), rec.get("submitTime"))
        if key in merged:
            # Keep the local entry (has code); just fill a missing timestamp.
            existing = merged[key]
            if not existing.get("timestamp") and rec.get("submitTime"):
                existing["timestamp"] = rec.get("submitTime")
            continue
        merged[key] = {
            "rid": rid,
            "pid": rec.get("pid", ""),
            "status": rec.get("status", 0),
            "score": rec.get("score", 0) or 0,
            "lang": rec.get("lang", 0) or 0,
            "timestamp": rec.get("submitTime", 0) or 0,
        }
    return list(merged.values())


# ---------------------------------------------------------------------------
# Export passed problems
# ---------------------------------------------------------------------------
DIFF_NAMES = {0: "暂无评定", 1: "入门", 2: "普及-", 3: "普及", 
              4: "普及+/提高-", 5: "提高", 6: "提高+/省选-", 7: "省选/NOI-", 8: "NOI/NOI+/CTS"}
DIFF_COLORS = {
    0: "#BFBFBF",  # 暂无评定 - 灰色
    1: "#FE4C61",  # 入门 - 红色
    2: "#F39C11",  # 普及- - 橙色
    3: "#FFC116",  # 普及 - 黄色
    4: "#52C41A",  # 普及+/提高- - 绿色
    5: "#3498DB",  # 提高 - 青色
    6: "#3498DB",  # 提高+/省选- - 蓝色
    7: "#9D3DCF",  # 省选/NOI- - 紫色
    8: "#0E1D69",  # NOI/NOI+/CTS - 黑色
}


def export_passed_problems(cookie, output_format="csv"):
    """Export the user's passed problems as CSV or Markdown.

    Args:
        cookie: Luogu cookie string
        output_format: "csv" or "markdown"

    Returns:
        dict with "success" and "content" (file content string) or "error"
    """
    if not cookie:
        return {"success": False, "error": "需要洛谷 Cookie"}

    try:
        uid = _extract_uid_from_cookie(cookie)
        if not uid:
            return {"success": False, "error": "无法从 Cookie 解析用户 ID"}

        # Use fetch_user_practice_detail to get rich problem info (pid, title, difficulty)
        detail = fetch_user_practice_detail(cookie)
        problem_list = detail.get("passedProblems", [])

        if not problem_list:
            return {"success": False, "error": "没有已通过的题目数据"}

        # Sort by pid
        problem_list.sort(key=lambda x: x.get("pid", ""))

        if output_format == "markdown":
            lines = ["# 已通过题目列表\n"]
            for p in problem_list:
                pid = p.get("pid", "")
                title = p.get("title", p.get("name", ""))
                diff = DIFF_NAMES.get(p.get("difficulty", 0), "未知")
                lines.append(f"- [x] **{pid}** {title} [{diff}]")
            content = "\n".join(lines)
        else:
            import io
            import csv
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["pid", "title", "difficulty", "type"])
            for p in problem_list:
                pid = p.get("pid", "")
                title = p.get("title", p.get("name", ""))
                diff = p.get("difficulty", 0)
                ptype = p.get("type", p.get("pid", "")[0] if pid else "")
                writer.writerow([pid, title, diff, ptype])
            content = output.getvalue()

        # Write the file next to the executable so the user can open it.
        # (Browser-style blob downloads do not work under WebView2 file://.)
        try:
            export_dir = os.path.join(_APP_DIR, "exports")
            os.makedirs(export_dir, exist_ok=True)
            ext = "md" if output_format == "markdown" else "csv"
            file_path = os.path.join(export_dir, f"luogu_passed_problems_{int(time.time())}.{ext}")
            with open(file_path, "w", encoding="utf-8-sig") as f:
                f.write(content)
        except OSError as e:
            logger.error("Failed to write export file: %s", e)
            file_path = ""

        return {
            "success": True,
            "content": content,
            "format": output_format,
            "count": len(problem_list),
            "file_path": file_path,
        }

    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.exception("Export failed")
        return {"success": False, "error": f"导出失败: {e}"}


def fetch_user_statistics(cookie="", uid=None, tag_problem_limit=40, tag_max_workers=8):
    """Fetch the user's submission timeline + tag distribution.

    `uid` may be given explicitly to view ANY user's statistics (needs a
    logged in session — the cookie — since it reads /record/list). When
    omitted it is derived from the cookie's _uid.

    Fetches the user's submission records (paginated) and aggregates:
      - trend: submission count per day for the last 180 days
      - week:  submission count per day for the last 7 days
      - tags:  top tag distribution over the most recent unique problems
        (record list items do NOT carry problem.tags, so tags must be
        fetched per-problem; we cap the number of problems and fetch in
        parallel to keep latency bounded)

    Returns {"trend": [...], "week": [...], "tags": [...]} or raises RuntimeError.
    """
    cookie = sanitize_cookie(cookie or "")
    uid = str(uid or _extract_uid_from_cookie(cookie) or "").strip()
    cache_key = f"user_stats_{uid}"
    cached = _cache_get(cache_key, ttl_seconds=300)
    if cached is not None:
        return cached
    if not uid:
        raise RuntimeError("缺少用户 ID，无法获取统计信息")

    session = build_luogu_session(cookie)
    try:
        session.get(f"{LUOGU_BASE}/", timeout=10)
    except requests.RequestException:
        pass

    url = f"{LUOGU_BASE}/record/list"

    def _fetch_page(page):
        params = {"user": uid, "page": page, "_contentOnly": 1}
        try:
            resp = session.get(url, params=params, timeout=15)
            if "auth/login" in (resp.url or "").lower():
                return [], 0
            try:
                data = resp.json()
            except (json.JSONDecodeError, ValueError):
                data = extract_luogu_data(resp.text)
            if not isinstance(data, dict):
                return [], 0
            cd = data.get("currentData")
            if not isinstance(cd, dict):
                dd = data.get("data")
                cd = dd.get("currentData") if isinstance(dd, dict) else None
                if not isinstance(cd, dict):
                    return [], 0
            records = cd.get("records")
            if not isinstance(records, dict):
                return [], 0
            return records.get("result") or [], records.get("count") or 0
        except requests.RequestException:
            return [], 0

    # Collect records, but stop paging once we have all 180 days of data
    # (records are newest-first, so old pages can be skipped once the page
    # start timestamp is older than the 180-day cutoff).
    now = int(time.time())
    cutoff = now - 180 * 86400
    all_records = []
    page = 1
    total_count = 0
    while page <= 200:  # safety cap
        recs, count = _fetch_page(page)
        total_count = count or total_count
        if not recs:
            break
        all_records.extend(recs)
        # Newest-first; if the last record of this page is already older than
        # the cutoff, the rest of the pages are too old to matter.
        last_ts = (recs[-1].get("submitTime") or 0)
        if last_ts and last_ts < cutoff:
            break
        if len(recs) < 20:
            break
        page += 1

    if not all_records:
        raise RuntimeError("提交记录为空，无法生成统计")

    # --- Per-day submission timeline ---
    trend = {}  # date_str -> count
    week = {}
    for rec in all_records:
        ts = rec.get("submitTime") or 0
        if not ts:
            continue
        day_str = time.strftime("%Y-%m-%d", time.localtime(ts))
        if ts >= cutoff:
            trend[day_str] = trend.get(day_str, 0) + 1
        if ts >= now - 7 * 86400:
            week[day_str] = week.get(day_str, 0) + 1

    # Fill missing days so charts are continuous (newest-first pages fetched
    # above; aggregate windows below end at "now")
    def _fill_days(start_ts, acc):
        out = []
        start = int(start_ts - start_ts % 86400)  # normalize to local midnight
        for i in range(180 if acc is trend else 7):
            day_ts = start - i * 86400
            day_str = time.strftime("%Y-%m-%d", time.localtime(day_ts))
            out.append({"date": day_str, "count": acc.get(day_str, 0)})
        out.reverse()
        return out

    trend_list = _fill_days(now, trend)
    week_list = _fill_days(now, week)

    # --- Tag distribution over recent unique problems ---
    # Tag fetching is best-effort: any failure must NOT lose the trend/week
    # statistics that were already computed above.
    tags_out = []
    try:
        tag_map = fetch_luogu_tags()
        seen = set()
        recent_pids = []
        for rec in all_records:
            pid = ((rec.get("problem") or {}).get("pid")) or ""
            if pid and pid not in seen:
                seen.add(pid)
                recent_pids.append(pid)
                if len(recent_pids) >= tag_problem_limit:
                    break

        def _fetch_problem_tags(pid):
            try:
                resp = session.get(f"{LUOGU_BASE}/problem/{pid}?_contentOnly=1", timeout=15)
                if "auth/login" in (resp.url or "").lower():
                    return None
                try:
                    data = resp.json()
                except (json.JSONDecodeError, ValueError):
                    data = extract_luogu_data(resp.text)
                prob = ((data or {}).get("data") or {}).get("problem") or {}
                return prob.get("tags") or []
            except Exception:
                return None

        tag_counts = {}
        if recent_pids:
            with ThreadPoolExecutor(max_workers=tag_max_workers) as executor:
                tag_results = list(executor.map(_fetch_problem_tags, recent_pids))
            for tags in tag_results:
                if not tags:
                    continue
                for t in tags:
                    name = tag_map.get(t) if isinstance(t, int) else t
                    if name:
                        tag_counts[name] = tag_counts.get(name, 0) + 1
        tag_list = sorted(tag_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:20]
        tags_out = [{"name": k, "count": v} for k, v in tag_list]
    except Exception:
        logger.exception("Tag statistics failed for uid=%s; returning trend/week only", uid)

    logger.info("Statistics for uid=%s: %d records, %d days, %d tags",
                uid, len(all_records), len(trend_list), len(tags_out))
    result = {
        "trend": trend_list,
        "week": week_list,
        "tags": tags_out,
        "totalRecords": len(all_records),
    }
    _cache_set(cache_key, result)
    return result


def fetch_trainings(page=1):
    """Fetch the list of official Luogu training plans (题单/训练计划).

    Returns a list of {id, name, type, problemCount, provider, description}.
    """
    url = f"{LUOGU_BASE}/training/list"
    try:
        resp = requests.get(url, headers=LUOGU_HEADERS,
                            params={"page": page, "_contentOnly": 1}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"获取训练计划失败: {e}")

    try:
        data = resp.json()
    except (json.JSONDecodeError, ValueError):
        data = extract_luogu_data(resp.text)
    if not isinstance(data, dict):
        raise RuntimeError("无法解析训练计划数据")

    trainings = (data.get("data") or {}).get("trainings") or {}
    result = trainings.get("result") or []
    out = []
    for t in result:
        if not isinstance(t, dict):
            continue
        provider = t.get("provider") or {}
        out.append({
            "id": t.get("id"),
            "name": t.get("name", ""),
            "type": t.get("type", 0),
            "problemCount": t.get("problemCount", 0),
            "provider": provider.get("name", ""),
            "description": t.get("description", ""),
        })
    return {
        "count": trainings.get("count") or len(out),
        "trainings": out,
    }


def fetch_training_detail(training_id):
    """Fetch the problem list of one training plan.

    Returns {id, name, description, problems: [{pid, name, difficulty, tags, totalSubmit, totalAccepted}]}.
    """
    url = f"{LUOGU_BASE}/training/{training_id}"
    try:
        resp = requests.get(url, headers=LUOGU_HEADERS,
                            params={"_contentOnly": 1}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"获取训练计划详情失败: {e}")

    try:
        data = resp.json()
    except (json.JSONDecodeError, ValueError):
        data = extract_luogu_data(resp.text)
    if not isinstance(data, dict):
        raise RuntimeError("无法解析训练计划详情数据")

    tr = (data.get("data") or {}).get("training") or {}
    tag_map = fetch_luogu_tags()
    problems = []
    for p in (tr.get("problems") or []):
        if not isinstance(p, dict):
            continue
        problems.append({
            "pid": p.get("pid", ""),
            "name": p.get("name", ""),
            "difficulty": p.get("difficulty", 0),
            "tags": _format_tags(p.get("tags") or [], tag_map),
            "totalSubmit": p.get("totalSubmit", 0),
            "totalAccepted": p.get("totalAccepted", 0),
        })
    return {
        "id": tr.get("id", training_id),
        "name": tr.get("name", ""),
        "description": tr.get("description", ""),
        "problemCount": tr.get("problemCount", len(problems)),
        "provider": (tr.get("provider") or {}).get("name", ""),
        "problems": problems,
    }


# ---------------------------------------------------------------------------
# Contest / Competition info
# ---------------------------------------------------------------------------
# Contest status: 0 = 未开始, 1 = 进行中, 2 = 已结束
def _contest_status(start_time, end_time, now=None):
    if not start_time or not end_time:
        return 0
    now = now or int(time.time())
    if now < start_time:
        return 0
    if now > end_time:
        return 2
    return 1


def fetch_contests(page=1, with_details=True):
    """Fetch contest list from Luogu. Returns {contests: [...], total: N}.

    Contest data is embedded in the /contest/list HTML page as JSON
    (data.contests.result). Public contests are visible without login.

    The list JSON does NOT carry the participant count, so each contest's
    detail page is fetched (bounded, parallel) to fill in real counts —
    unless with_details=False (used by reminders, which don't need counts).
    Every contest also gets a status: 0 未开始 / 1 进行中 / 2 已结束.
    """
    url = f"{LUOGU_BASE}/contest/list"
    try:
        resp = requests.get(url, headers=LUOGU_HEADERS,
                            params={"page": page}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"获取比赛列表失败: {e}")

    data = extract_luogu_data(resp.text)
    if not isinstance(data, dict):
        raise RuntimeError("无法解析比赛列表数据")

    contests_data = data.get("data", {}).get("contests") or {}
    if isinstance(contests_data, dict):
        contests = contests_data.get("result", [])
        total = contests_data.get("count", 0)
    elif isinstance(contests_data, list):
        contests = contests_data
        total = len(contests)
    else:
        contests = []
        total = 0

    now = int(time.time())
    result = []
    for c in contests:
        if not isinstance(c, dict):
            continue
        host = c.get("host") or {}
        start = c.get("startTime", 0) or 0
        end = c.get("endTime", 0) or 0
        result.append({
            "id": c.get("id", 0),
            "name": c.get("name", ""),
            "startTime": start,
            "endTime": end,
            "duration": max(0, end - start),
            "status": _contest_status(start, end, now),
            "participantCount": 0,
            "problemCount": c.get("problemCount", 0),
            "host": host.get("name", "") if isinstance(host, dict) else "",
        })

    # Fill real participant counts from detail pages (bounded, tolerant).
    # Detail responses are cached, so re-opening the list is cheap.
    if with_details and result:
        with ThreadPoolExecutor(max_workers=5) as executor:
            details = executor.map(
                lambda c: (c["id"], fetch_contest_detail(c["id"])),
                result)
            for cid, detail in details:
                if isinstance(detail, dict) and detail.get("participantCount"):
                    for c in result:
                        if c["id"] == cid:
                            c["participantCount"] = detail["participantCount"]
                            break

    return {"contests": result, "total": total}


def luogu_checkin(cookie=""):
    """Perform the Luogu daily check-in (打卡) for the given cookie.

    Uses GET /index/ajax_punch with the x-requested-with header. Returns:
      {"success": True, "code": 200|201, "already": bool, "message": str,
       "html": str}
    code 200 = successfully checked in just now; 201 = already checked in.

    Luogu now gates this endpoint behind a lightweight anti-bot check: the
    first request returns HTML that sets a `C3VK` cookie then redirects.
    We retry once with that cookie so the server returns real JSON.
    """
    if not cookie:
        raise RuntimeError("打卡需要登录洛谷，请填入洛谷 Cookie")
    headers = {
        "User-Agent": LUOGU_HEADERS.get("User-Agent", ""),
        "Cookie": sanitize_cookie(cookie),
        "Referer": f"{LUOGU_BASE}/",
        "x-requested-with": "XMLHttpRequest",
    }
    try:
        resp = requests.get(f"{LUOGU_BASE}/index/ajax_punch", headers=headers, timeout=10)
        resp.raise_for_status()
        # First response may be the anti-bot page instead of JSON.
        m = re.search(r"C3VK=([0-9a-f]+)", resp.text or "")
        if m:
            headers["Cookie"] = f"{headers['Cookie']}; C3VK={m.group(1)}"
            resp = requests.get(f"{LUOGU_BASE}/index/ajax_punch", headers=headers, timeout=10)
            resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"打卡请求失败: {e}")
    try:
        data = resp.json()
    except json.JSONDecodeError:
        raise RuntimeError("打卡响应解析失败，可能是 Cookie 已失效或未登录")
    code = data.get("code")
    message = data.get("message") or ""
    more = data.get("more") or {}
    html = more.get("html") if isinstance(more, dict) else ""
    if code == 200:
        return {"success": True, "code": 200, "already": False,
                "message": message or "打卡成功", "html": html}
    if code == 201:
        return {"success": True, "code": 201, "already": True,
                "message": message or "今天已经打过卡了", "html": html}
    if code == 403:
        raise RuntimeError("Cookie 已失效，请重新填入洛谷 Cookie")
    raise RuntimeError(message or f"打卡失败 (code={code})")


def get_upcoming_contests(cookie="", hours=24):
    """Return contests that start within the next `hours` (for reminders).

    Fetches the first page of contests and filters to those whose start time
    is in the future but within the window. Each item is a compact dict with
    id, name, startTime, endTime, status, minutesUntilStart.
    """
    data = fetch_contests(1, with_details=False)
    now = int(time.time())
    window = int(hours) * 3600
    upcoming = []
    for c in data.get("contests", []):
        start = c.get("startTime", 0) or 0
        end = c.get("endTime", 0) or 0
        if not start:
            continue
        delta = start - now
        if 0 < delta <= window:
            upcoming.append({
                "id": c.get("id"),
                "name": c.get("name", ""),
                "startTime": start,
                "endTime": end,
                "status": _contest_status(start, end),
                "minutesUntilStart": int(delta // 60),
            })
    upcoming.sort(key=lambda x: x["startTime"])
    return {"upcoming": upcoming}


def get_heatmap_data(cookie=""):
    """Build GitHub-style heatmap data from local + remote AC records.

    Returns {"weeks": [[{date, count, difficulty} ...] ...], "total": N} covering
    the full AC history (from the earliest AC day to today). Only AC (status==12)
    records count. Local records are merged with the user's full Luogu submission
    history so the heatmap shows every accepted submission, not just ones made
    inside this app.
    """
    cache_key = f"heatmap_data_{_extract_uid_from_cookie(cookie)}"
    cached = _cache_get(cache_key, ttl_seconds=1800)  # 30 minutes cache
    if cached is not None:
        return cached

    day_count = {}
    # Build difficulty mapping for AC submissions
    day_to_difficulty = {}

    # Fetch the submission records and the passed-problem difficulty map in
    # parallel: paging through /record/list is the slowest step, so the one
    # practice-page request rides along instead of adding to the latency.
    with ThreadPoolExecutor(max_workers=2) as _ex:
        f_records = _ex.submit(_merge_all_records, cookie)
        f_detail = _ex.submit(fetch_user_practice_detail, cookie)

        # Collect all AC submissions with their timestamps
        ac_records = []
        try:
            merged = f_records.result(timeout=45)
        except Exception:
            logger.exception("Failed to fetch merged records for heatmap")
            merged = []
        for rec in merged:
            if rec.get("status") == 12:
                ts = rec.get("timestamp", 0) or 0
                if ts:
                    ac_records.append({
                        "pid": rec.get("pid", ""),
                        "timestamp": ts,
                        "day": time.strftime("%Y-%m-%d", time.localtime(ts))
                    })

        # Get problem details for difficulty mapping
        pid_to_difficulty = {}
        try:
            detail = f_detail.result(timeout=45)
            passed_problems = detail.get("passedProblems", [])
            for problem in passed_problems:
                pid = problem.get("pid", "")
                difficulty = problem.get("difficulty", 0)
                if pid:
                    pid_to_difficulty[pid] = difficulty
        except Exception as e:
            logger.warning(f"Failed to fetch problem details for heatmap: {e}")
            # Default difficulty 0 for unknown problems
            for rec in ac_records:
                pid_to_difficulty[rec["pid"]] = 0
    
    # Group submissions by day and count difficulties
    for rec in ac_records:
        day = rec["day"]
        difficulty = pid_to_difficulty.get(rec["pid"], 0)
        
        if day not in day_count:
            day_count[day] = {}
            day_to_difficulty[day] = []
        
        if difficulty not in day_count[day]:
            day_count[day][difficulty] = 0
        day_count[day][difficulty] += 1
    
    total = sum(sum(counts.values()) for counts in day_count.values())
    streak = _compute_ac_streaks(day_count)

    # Build weeks starting from a Monday. The span is dynamic: it covers the
    # full AC history (from the earliest AC day's week to the current week)
    # instead of a fixed 52-week window, so every submission shows up.
    import datetime
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    start = monday
    if day_count:
        earliest = min(datetime.date.fromisoformat(k) for k in day_count)
        earliest_monday = earliest - datetime.timedelta(days=earliest.weekday())
        # Leave one leading empty week so the earliest column isn't clipped.
        start = earliest_monday - datetime.timedelta(weeks=1)
    num_weeks = max(1, ((monday - start).days // 7) + 1)
    weeks = []
    for w in range(num_weeks):
        week = []
        for d in range(7):
            date = start + datetime.timedelta(weeks=w, days=d)
            key = date.strftime("%Y-%m-%d")
            if key in day_count:
                # Include difficulty information for the highest difficulty that day
                difficulties = day_count[key]
                if difficulties:
                    # Use the highest difficulty for the day (Luogu rule: hue follows
                    # the highest difficulty of AC'd problems that day).
                    highest_difficulty = max(difficulties.keys())
                    week.append({
                        "date": key, 
                        "count": sum(difficulties.values()),
                        "difficulty": highest_difficulty
                    })
                else:
                    week.append({"date": key, "count": 0, "difficulty": 0})
            else:
                week.append({"date": key, "count": 0, "difficulty": 0})
        weeks.append(week)
    result = {"weeks": weeks, "total": total, "streak": streak}
    _cache_set(cache_key, result)
    return result


def _compute_ac_streaks(day_count):
    """Compute (current, longest) streak of consecutive days with AC.

    `day_count` maps "YYYY-MM-DD" -> {difficulty: count}. A day counts toward
    the streak if it has at least one AC submission. The current streak runs
    backward from today (with a one-day grace: if today has no AC yet but
    yesterday does, the streak is still alive).
    """
    import datetime
    active = set(day_count.keys())
    if not active:
        return {"current": 0, "longest": 0}

    today = datetime.date.today()
    cursor = today if today.isoformat() in active else today - datetime.timedelta(days=1)
    current = 0
    while cursor.isoformat() in active:
        current += 1
        cursor -= datetime.timedelta(days=1)

    dates = sorted(datetime.date.fromisoformat(d) for d in active)
    longest = 0
    run = 0
    prev = None
    for date in dates:
        if prev is not None and (date - prev).days == 1:
            run += 1
        else:
            run = 1
        longest = max(longest, run)
        prev = date
    return {"current": current, "longest": longest}


def smart_recommend(difficulty="", tag=""):
    """Recommend an unsolved problem, excluding ones already AC'd locally.

    Pools default-list pages and picks a random problem that the user has
    NOT yet accepted locally (local records status==12). Optional difficulty
    / tag filters apply. Returns {pid, title, difficulty, type, tags}.
    """
    import random
    solved = set()
    for pid, recs in _load_local_records().items():
        for rec in recs:
            if rec.get("status") == 12:
                solved.add(pid)
                break
    pool = []
    for page in (1, 2, 3):
        try:
            data = fetch_default_problems(page)
            pool.extend(data.get("problems", []))
        except RuntimeError:
            continue
    pool = [p for p in pool if p.get("pid") not in solved]
    if difficulty:
        try:
            diff = int(difficulty)
        except (TypeError, ValueError):
            diff = None
        if diff is not None:
            pool = [p for p in pool if p.get("difficulty") == diff]
    if tag:
        pool = [p for p in pool if tag.lower() in str(p.get("tags", [])).lower()]
    if not pool:
        raise RuntimeError("暂无可推荐题目")
    chosen = random.choice(pool)
    return {
        "pid": chosen.get("pid", ""),
        "title": chosen.get("title", ""),
        "difficulty": chosen.get("difficulty", 0),
        "type": chosen.get("type", ""),
        "tags": chosen.get("tags", []),
    }


# ---------------------------------------------------------------------------
def fetch_contest_standings(contest_id, cookie="", page=1):
    """Fetch the standings (排行榜) of a contest.

    The standings page embeds JSON with data.data.standings containing the
    player rows: {user: {name, uid, ...}, score, rank, ...}. Returns
    {contest: {...}, players: [{rank, uid, name, score}], total}.
    """
    contest_id = str(contest_id or "").strip()
    if not contest_id:
        raise RuntimeError("缺少比赛 ID")
    session = build_luogu_session(cookie or load_config().get("cookie", ""))
    url = f"{LUOGU_BASE}/contest/{contest_id}/standings"
    try:
        resp = session.get(url, params={"page": page}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"获取比赛榜单失败: {e}")

    data = extract_luogu_data(resp.text)
    if not isinstance(data, dict):
        raise RuntimeError("无法解析比赛榜单数据")

    dd = data.get("data") or {}
    if not isinstance(dd, dict):
        raise RuntimeError("比赛榜单数据为空")
    standings = dd.get("standings") or {}
    if not isinstance(standings, dict):
        standings = {}

    contest = dd.get("contest") or {}
    if not isinstance(contest, dict):
        contest = {}

    players = []
    for row in (standings.get("players") or []):
        if not isinstance(row, dict):
            continue
        user = row.get("user") or {}
        if not isinstance(user, dict):
            user = {}
        players.append({
            "rank": row.get("rank", 0),
            "uid": user.get("uid", ""),
            "name": user.get("name", ""),
            "score": row.get("score", 0),
            "time": row.get("time", row.get("penalty", 0)),
        })
    total = standings.get("count", 0) or len(players)
    return {
        "contest": {
            "id": contest.get("id", contest_id),
            "name": contest.get("name", ""),
            "startTime": contest.get("startTime", 0),
            "endTime": contest.get("endTime", 0),
            "status": _contest_status(contest.get("startTime", 0) or 0,
                                      contest.get("endTime", 0) or 0),
        },
        "players": players,
        "total": total,
    }


def get_wrong_book():
    """Return problems with failed local submissions (错题本).

    Groups local records by problem and keeps problems whose most recent
    submission is NOT AC (status != 12). Returns a list of
    {pid, count, lastStatus, lastStatusText, lastScore, lastTime}.
    """
    records = _load_local_records()
    wrong = []
    for pid, recs in records.items():
        if not recs:
            continue
        recs = sorted(recs, key=lambda r: r.get("timestamp", 0), reverse=True)
        last = recs[0]
        if last.get("status") == 12:
            continue  # latest is AC -> not in the wrong book
        wrong.append({
            "pid": pid,
            "count": len(recs),
            "lastStatus": last.get("status", 0),
            "lastStatusText": status_text(last.get("status", 0)),
            "lastScore": last.get("score", 0),
            "lastTime": last.get("timestamp", 0),
        })
    wrong.sort(key=lambda x: x["lastTime"], reverse=True)
    return wrong


# Language id -> file extension for code export
EXPORT_EXT_MAP = {
    1: "pas", 2: "c", 3: "cpp", 4: "cpp", 7: "py", 8: "java", 9: "js",
    11: "cpp", 12: "cpp", 13: "rb", 14: "go", 15: "rs", 16: "php", 17: "cs",
    19: "hs", 21: "kt", 25: "py", 27: "cpp", 28: "cpp", 33: "java",
}

EXPORT_DIR = os.path.join(_APP_DIR, "exports")


def export_submission_code(pid, rid):
    """Export a locally-saved submission's code to the exports folder.

    Returns {path, filename}. The file is written as exports/{pid}_{rid}.{ext}.
    """
    pid = str(pid or "").strip()
    if not pid:
        raise ValueError("缺少题号")
    records = _get_local_records(pid)
    rec = next((r for r in records if str(r.get("rid")) == str(rid)), None)
    if not rec:
        raise RuntimeError("未找到该提交记录")
    os.makedirs(EXPORT_DIR, exist_ok=True)
    ext = EXPORT_EXT_MAP.get(int(rec.get("lang", 0) or 0), "txt")
    filename = f"{pid}_{rid}.{ext}"
    path = os.path.join(EXPORT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(rec.get("code", "") or "")
    return {"path": path, "filename": filename}


def get_advanced_stats(cookie=""):
    """Compute richer statistics from local + remote submission records.

    Returns {totalSubmissions, totalAC, acRate, statusCounts, langCounts,
    perProblem: [{pid, submissions, ac, bestScore}], days: [{date, count}]}.
    """
    cache_key = f"advanced_stats_{_extract_uid_from_cookie(cookie)}"
    cached = _cache_get(cache_key, ttl_seconds=1800)  # 30 minutes cache
    if cached is not None:
        return cached

    all_recs = _merge_all_records(cookie)
    total_submissions = 0
    total_ac = 0
    status_counts = {}
    lang_counts = {}
    per_problem = {}
    day_count = {}

    for rec in all_recs:
        pid = rec.get("pid", "")
        if not pid:
            continue
        status = rec.get("status", 0)
        score = rec.get("score", 0) or 0
        lang = rec.get("lang", 0) or 0
        ts = rec.get("timestamp", 0) or 0

        total_submissions += 1
        if status == 12:
            total_ac += 1
        status_counts[status] = status_counts.get(status, 0) + 1
        lang_counts[lang] = lang_counts.get(lang, 0) + 1

        if pid not in per_problem:
            per_problem[pid] = {"submissions": 0, "ac": 0, "bestScore": 0, "statusCounts": {}}
        per_problem[pid]["submissions"] += 1
        per_problem[pid]["statusCounts"][status] = per_problem[pid]["statusCounts"].get(status, 0) + 1
        if status == 12:
            per_problem[pid]["ac"] += 1
        if score > per_problem[pid]["bestScore"]:
            per_problem[pid]["bestScore"] = score

        if ts:
            day = time.strftime("%Y-%m-%d", time.localtime(ts))
            day_count[day] = day_count.get(day, 0) + 1

    per_problem_list = sorted(
        [{"pid": pid, **stats} for pid, stats in per_problem.items()],
        key=lambda x: x["submissions"], reverse=True
    )
    days = [{"date": k, "count": v} for k, v in sorted(day_count.items())]
    ac_rate = round(total_ac / total_submissions * 100, 1) if total_submissions else 0
    result = {
        "totalSubmissions": total_submissions,
        "totalAC": total_ac,
        "acRate": ac_rate,
        "totalProblems": len(per_problem_list),
        "statusCounts": status_counts,
        "langCounts": lang_counts,
        "perProblem": per_problem_list,
        "days": days,
    }
    _cache_set(cache_key, result)
    return result


def fetch_contest_detail(contest_id, cookie=""):
    """Fetch contest detail. Returns {id, name, description, problems, joined, ...}.

    The contest page JSON exposes:
      - contest: meta (name, time, totalParticipants, description, ...)
      - contestProblems: [{no, score, problem:{pid,name,difficulty,type}}]
        (visible publicly after the contest ends; for ongoing/upcoming
        contests they are only visible after joining)
      - joined: whether the current session has registered

    `cookie` is the logged-in viewer session (needed to detect joined state
    and see the problems of an ongoing contest). Response is cached briefly.
    """
    contest_id = str(contest_id or "").strip()
    if not contest_id:
        raise RuntimeError("缺少比赛 ID")
    cache_key = f"contest_{contest_id}"
    cached = _cache_get(cache_key, ttl_seconds=300)
    if cached is not None:
        return cached

    cookie = sanitize_cookie(cookie or "")
    session = build_luogu_session(cookie)
    try:
        session.get(f"{LUOGU_BASE}/", timeout=10)
    except requests.RequestException:
        pass

    url = f"{LUOGU_BASE}/contest/{contest_id}"
    try:
        resp = session.get(url, timeout=15)
    except requests.RequestException as e:
        raise RuntimeError(f"获取比赛详情失败: {e}")

    if "auth/login" in (resp.url or "").lower():
        raise RuntimeError("Cookie 已失效，请重新填入洛谷 Cookie")

    data = extract_luogu_data(resp.text)
    if not isinstance(data, dict):
        raise RuntimeError("无法解析比赛详情数据")

    dd = data.get("data") or {}
    if not isinstance(dd, dict):
        raise RuntimeError("比赛数据为空")
    contest = dd.get("contest") or {}
    if not isinstance(contest, dict) or not contest:
        raise RuntimeError("比赛数据为空")

    host = contest.get("host") or {}
    start = contest.get("startTime", 0) or 0
    end = contest.get("endTime", 0) or 0
    now = int(time.time())

    # Problems: data.contestProblems -> [{no, score, problem:{...}}]
    problems = []
    for item in (dd.get("contestProblems") or []):
        if not isinstance(item, dict):
            continue
        prob = item.get("problem") or {}
        if not isinstance(prob, dict):
            continue
        problems.append({
            "pid": prob.get("pid", ""),
            "name": prob.get("name", prob.get("title", "")),
            "difficulty": prob.get("difficulty", 0),
            "type": prob.get("type", ""),
            "no": item.get("no", ""),
            "score": item.get("score", 0),
        })

    result = {
        "id": contest.get("id", contest_id),
        "name": contest.get("name", ""),
        "startTime": start,
        "endTime": end,
        "duration": max(0, end - start),
        "status": _contest_status(start, end, now),
        "participantCount": contest.get("totalParticipants",
                                        contest.get("participantCount", 0)) or 0,
        "problemCount": contest.get("problemCount", 0),
        "host": host.get("name", "") if isinstance(host, dict) else "",
        "description": contest.get("description", ""),
        "rated": contest.get("rated", 0),
        "method": contest.get("method", 0),
        "visibility": contest.get("visibility", 0),
        "joined": bool(dd.get("joined", 0)),
        "canViewScoreboard": bool(dd.get("canViewScoreboard", False)),
        "problems": problems,
    }
    _cache_set(cache_key, result)
    return result


def register_contest(contest_id, cookie):
    """Register (报名) for a Luogu contest.

    Luogu exposes the action at POST /contest/{cid}/join (requires login +
    CSRF token). After joining, the contest problems become visible.
    Returns the parsed response; raises RuntimeError on failure.
    """
    contest_id = str(contest_id or "").strip()
    if not contest_id:
        raise RuntimeError("缺少比赛 ID")
    cookie = sanitize_cookie(cookie or "")
    if not cookie:
        raise RuntimeError("报名参赛需要登录洛谷，请填入洛谷 Cookie")

    session = build_luogu_session(cookie)
    try:
        session.get(f"{LUOGU_BASE}/", timeout=10)
    except requests.RequestException:
        pass

    # Visit the contest page to obtain csrf-token
    try:
        page_resp = session.get(f"{LUOGU_BASE}/contest/{contest_id}", timeout=15)
    except requests.RequestException as e:
        raise RuntimeError(f"无法访问比赛页面: {e}")
    if "auth/login" in (page_resp.url or "").lower():
        raise RuntimeError("Cookie 已失效，请重新填入洛谷 Cookie")

    csrf_token = None
    for c in session.cookies:
        if c.name == "csrf-token":
            csrf_token = c.value
            break
    if not csrf_token:
        m = re.search(r'<meta name="csrf-token" content="([^"]+)"', page_resp.text)
        if m:
            csrf_token = m.group(1)
    if not csrf_token:
        raise RuntimeError("无法获取 CSRF Token，请检查 Cookie 是否有效")

    join_url = f"{LUOGU_BASE}/contest/{contest_id}/join"
    headers = {
        "x-csrf-token": csrf_token,
        "Content-Type": "application/json",
        "Referer": f"{LUOGU_BASE}/contest/{contest_id}",
        "Origin": LUOGU_BASE,
    }
    try:
        resp = session.post(join_url, json={}, headers=headers, timeout=15)
    except requests.RequestException as e:
        raise RuntimeError(f"报名参赛失败: {e}")

    try:
        data = resp.json()
    except json.JSONDecodeError:
        raise RuntimeError(f"报名响应解析失败 (HTTP {resp.status_code})")

    # Symfony-style failure:
    # {"errorCode": N, "errorType": "...", "errorMessage": "...", ...}
    if isinstance(data, dict) and data.get("errorCode") is not None:
        raise RuntimeError(data.get("errorMessage")
                           or f"报名参赛失败 (HTTP {resp.status_code})")

    # Other failure shapes: {"status": !=200}, or a top-level errorMessage.
    err_msg = ""
    if isinstance(data, dict):
        status = data.get("status")
        if status is not None and status != 200:
            raw = data.get("data", "")
            if isinstance(raw, dict):
                err_msg = raw.get("errorMessage", "") or raw.get("message", "")
            elif isinstance(raw, str):
                err_msg = raw
            else:
                err_msg = data.get("errorMessage", "") or str(data.get("data", ""))
        elif data.get("errorMessage"):
            err_msg = data.get("errorMessage", "")
    if err_msg:
        raise RuntimeError(err_msg)

    # Success shapes observed on Luogu: {"status":200}, {"joined":true},
    # or {"id": <cid>} (no status/joined keys) — all must count as success.
    ok = (isinstance(data, dict)
          and (data.get("status") == 200
               or "joined" in data
               or str(data.get("id")) == contest_id))
    if not ok:
        raise RuntimeError(f"报名参赛失败 (HTTP {resp.status_code})")

    # Invalidate the cached detail so the next fetch shows joined + problems
    _cache_delete(f"contest_{contest_id}")
    return data


# ---------------------------------------------------------------------------
# Blog reading
# ---------------------------------------------------------------------------
def fetch_user_blog(uid, page=1):
    """Fetch blog posts for a user. Returns {posts: [...], total: N}.

    Blog data is embedded in the /blog/{uid} HTML page as JSON. Each post
    carries a `lid` (article id) which is used to open the full article.
    """
    uid = str(uid or "").strip()
    if not uid:
        raise RuntimeError("缺少用户 ID")
    url = f"{LUOGU_BASE}/blog/{uid}"
    try:
        resp = requests.get(url, headers=LUOGU_HEADERS,
                            params={"page": page}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"获取博客列表失败: {e}")

    data = extract_luogu_data(resp.text)
    if not isinstance(data, dict):
        raise RuntimeError("无法解析博客列表数据")

    blog_data = data.get("data", {})
    if not isinstance(blog_data, dict):
        blog_data = {}
    articles = blog_data.get("articles") or {}
    if isinstance(articles, dict):
        result = articles.get("result", [])
        total = articles.get("count", 0)
    else:
        result = articles if isinstance(articles, list) else []
        total = len(result)

    posts = []
    for p in (result or []):
        if not isinstance(p, dict):
            continue
        author = p.get("author") or {}
        solution = p.get("solutionFor") or {}
        posts.append({
            "id": p.get("lid", p.get("id", 0)),
            "lid": p.get("lid", ""),
            "title": p.get("title", ""),
            "summary": p.get("summary", ""),
            "time": p.get("time", p.get("postTime", 0)),
            "likeCount": p.get("upvote", p.get("likeCount", 0)),
            "commentCount": p.get("replyCount", p.get("commentCount", 0)),
            "author": author.get("name", "") if isinstance(author, dict) else "",
            "authorId": author.get("uid", "") if isinstance(author, dict) else "",
            "solutionForPid": solution.get("pid", "") if isinstance(solution, dict) else "",
        })

    return {"posts": posts, "total": total}


def fetch_blog_detail(blog_id, author_name=""):
    """Fetch a single blog post content. Returns {title, content, ...}.

    Full article content lives on /article/{lid}. It requires a logged-in
    session (cookie) and a warm-up request to pass Luogu's outbound-link
    security check, so we reuse the session builder used elsewhere.
    """
    blog_id = str(blog_id or "").strip()
    if not blog_id:
        raise RuntimeError("缺少博客 ID")

    cookie = load_config().get("cookie", "")
    session = build_luogu_session(cookie)
    try:
        session.get(f"{LUOGU_BASE}/", timeout=10)
    except requests.RequestException:
        pass

    url = f"{LUOGU_BASE}/article/{blog_id}"
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"获取博客详情失败: {e}")

    data = extract_luogu_data(resp.text)
    if not isinstance(data, dict):
        raise RuntimeError("无法解析博客数据")

    blog = data.get("data", {})
    if isinstance(blog, dict) and isinstance(blog.get("article"), dict):
        blog = blog["article"]
    if not isinstance(blog, dict) or not blog:
        raise RuntimeError("博客数据为空")

    return {
        "id": blog.get("lid", blog.get("id", blog_id)),
        "title": blog.get("title", ""),
        "content": blog.get("content", ""),
        "time": blog.get("time", blog.get("postTime", 0)),
        "likeCount": blog.get("upvote", blog.get("likeCount", 0)),
        "commentCount": blog.get("replyCount", blog.get("commentCount", 0)),
    }


def fetch_problem(problem_id, cookie=""):
    """Fetch problem metadata + content from Luogu HTML page.

    Uses a warmed session (C3VK challenge cookie) and, when available, the
    saved Luogu cookie so the request is far less likely to be blocked by
    Luogu's CDN bot-protection than a bare anonymous request.
    """
    cached = _cache_get(f"problem_{problem_id}", ttl_seconds=3600)
    if cached is not None:
        return cached
    url = f"{LUOGU_BASE}/problem/{problem_id}"
    session = _warm_session(build_luogu_session(cookie))
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        code = getattr(getattr(e, "response", None), "status_code", None)
        if code in (403, 429):
            raise RuntimeError("洛谷接口访问受限（403），可能是请求过于频繁或 IP 被临时限制，请稍后重试，或重新填入洛谷 Cookie")
        logger.error("Failed to fetch problem %s: %s", problem_id, e)
        raise RuntimeError(f"无法获取题目信息: {e}")

    data = extract_luogu_data(resp.text)
    if not data:
        if resp.status_code in (403, 429) or "Ws-Action" in resp.text or "403 Forbidden" in resp.text:
            raise RuntimeError("洛谷接口访问受限（403），可能是请求过于频繁或 IP 被临时限制，请稍后重试，或重新填入洛谷 Cookie")
        raise RuntimeError("无法解析题目页面数据，可能页面结构已变更")

    if data.get("status") != 200:
        err_msg = data.get("data", {}).get("errorMessage", "题目不存在或无法访问")
        raise RuntimeError(err_msg)

    problem = data.get("data", {}).get("problem", {})
    if not problem:
        raise RuntimeError("题目数据为空")

    content = problem.get("content", {})

    # Convert samples from [[in, out], ...] to [{in, out}, ...]
    raw_samples = problem.get("samples", [])
    formatted_samples = []
    for s in raw_samples:
        if isinstance(s, list) and len(s) >= 2:
            formatted_samples.append({"in": s[0] or "", "out": s[1] or ""})
        elif isinstance(s, dict):
            formatted_samples.append({"in": s.get("in", ""), "out": s.get("out", "")})

    # Map numeric tag IDs to human-readable names
    raw_tags = problem.get("tags", [])
    tag_map = fetch_luogu_tags()
    formatted_tags = []
    for t in raw_tags:
        if isinstance(t, int):
            name = tag_map.get(t, "")
            if name:
                formatted_tags.append(name)
        elif isinstance(t, str) and t:
            formatted_tags.append(t)

    # Recommended problems with similar knowledge points (Luogu's 推荐题目)
    raw_recs = data.get("data", {}).get("recommendations", [])
    recommendations = []
    for r in raw_recs:
        if not isinstance(r, dict) or not r.get("pid"):
            continue
        recommendations.append({
            "pid": r.get("pid", ""),
            "title": r.get("name", ""),
            "difficulty": int(r.get("difficulty", 0)),
            "type": r.get("type", ""),
        })

    # Problem source (e.g. "[NOIP 2005 普及组] 采药" -> "NOIP 2005 普及组")
    problem_title = problem.get("name", "")
    source_match = re.match(r"^\[([^\]]+)\]", problem_title)
    source = source_match.group(1) if source_match else ""

    result = {
        "pid": problem.get("pid", problem_id),
        "title": problem.get("name", ""),
        "difficulty": problem.get("difficulty", 0),
        "tags": formatted_tags,
        "background": content.get("background", ""),
        "description": content.get("description", ""),
        "inputFormat": content.get("formatI", ""),
        "outputFormat": content.get("formatO", ""),
        "samples": formatted_samples,
        "hint": content.get("hint", ""),
        "timeLimit": problem.get("limits", {}).get("time", []),
        "memoryLimit": problem.get("limits", {}).get("memory", []),
        "totalSubmit": problem.get("totalSubmit", 0),
        "totalAccepted": problem.get("totalAccepted", 0),
        "source": source,
        "recommendations": recommendations,
    }
    _cache_set(f"problem_{problem_id}", result)
    return result


def fetch_solutions(problem_id, cookie=""):
    """Fetch solution list from Luogu. Requires login cookie.

    Luogu uses a challenge-response anti-bot mechanism:
    1. First request returns 302 + sets C3VK cookie
    2. Second request (with C3VK) returns actual content
    So we must use a Session to persist cookies across redirects.

    AtCoder problems are routed to the public AtCoder editorial page instead:
    Luogu mirrors AtCoder problem *statements* but never hosts *solution*
    pages for them (/problem/solution/AT_* always 404s), so the Luogu path
    can never return AtCoder solutions.
    """
    cookie = sanitize_cookie(cookie)
    luogu_pid = atcoder_luogu_pid(problem_id)
    if luogu_pid.upper().startswith("AT_"):
        return _fetch_atcoder_editorials(problem_id)
    problem_id = luogu_pid
    url = f"{LUOGU_BASE}/problem/solution/{problem_id}"

    # Use a session so the C3VK challenge cookie from 302 redirect is
    # automatically carried on the follow-up request.
    session = requests.Session()
    session.headers.update(LUOGU_HEADERS)

    # Load user-provided cookies into the session's cookie jar
    if cookie:
        jar = requests.cookies.RequestsCookieJar()
        for part in cookie.split(";"):
            part = part.strip()
            if "=" in part:
                name, value = part.split("=", 1)
                jar.set(name.strip(), value.strip(), domain=".luogu.com.cn", path="/")
        session.cookies = jar

    try:
        resp = session.get(url, timeout=15)
    except requests.RequestException as e:
        logger.error("Failed to fetch solutions for %s: %s", problem_id, e)
        raise RuntimeError(f"无法获取题解信息: {e}")

    data = extract_luogu_data(resp.text)
    if not data:
        if resp.status_code == 401:
            raise RuntimeError("需要登录洛谷才能查看题解，请在上方填入洛谷 Cookie")
        raise RuntimeError("无法解析题解页面数据")

    page_data = data.get("data", {})
    if "errorCode" in page_data:
        msg = page_data.get("errorMessage", "获取题解失败")
        if "login" in msg.lower() or "登录" in msg:
            raise RuntimeError("需要登录洛谷才能查看题解，请在上方填入洛谷 Cookie")
        raise RuntimeError(msg)

    solutions = page_data.get("solutions", {})
    return solutions


# ---------------------------------------------------------------------------
# Code submission & judge result
# ---------------------------------------------------------------------------

# Luogu language ID mapping
LUOGU_LANG_MAP = {
    "auto": 0,
    "pascal": 1,
    "c": 2,
    "cpp": 3,
    "cpp11": 4,
    "python3": 7,
    "java8": 8,
    "nodejs": 9,
    "cpp14": 11,
    "cpp17": 12,
    "ruby": 13,
    "go": 14,
    "rust": 15,
    "php": 16,
    "csharp": 17,
    "haskell": 19,
    "kotlin": 21,
    "pypy3": 25,
    "cpp20": 27,
    "cpp14gcc9": 28,
    "java21": 33,
}

# Reverse map for display
LUOGU_LANG_OPTIONS = [
    (0, "自动语言检测"),
    (28, "C++14 (GCC 9)"),
    (27, "C++20"),
    (12, "C++17"),
    (11, "C++14"),
    (4, "C++11"),
    (3, "C++98"),
    (2, "C"),
    (7, "Python 3"),
    (25, "PyPy 3"),
    (8, "Java 8"),
    (14, "Go"),
    (15, "Rust"),
    (1, "Pascal"),
    (17, "C# (Mono)"),
    (9, "Node.js"),
    (16, "PHP"),
    (13, "Ruby"),
    (21, "Kotlin/JVM"),
    (33, "Java 21"),
    (19, "Haskell"),
]

# ---------------------------------------------------------------------------
# Local compile & run (Online IDE test panel)
# ---------------------------------------------------------------------------
# Maps a Luogu language id to the info needed to compile/run it locally.
#   name      : display name
#   ext       : source file extension
#   type      : "compiled" (g++/gcc) or "interpreted" (python)
#   std_flag  : optional -std flag for C/C++
LANG_COMPILE_INFO = {
    2:  {"name": "C",        "ext": ".c",   "type": "compiled",    "std_flag": None},
    3:  {"name": "C++98",    "ext": ".cpp", "type": "compiled",    "std_flag": "-std=c++98"},
    4:  {"name": "C++11",    "ext": ".cpp", "type": "compiled",    "std_flag": "-std=c++11"},
    11: {"name": "C++14",    "ext": ".cpp", "type": "compiled",    "std_flag": "-std=c++14"},
    12: {"name": "C++17",    "ext": ".cpp", "type": "compiled",    "std_flag": "-std=c++17"},
    27: {"name": "C++20",    "ext": ".cpp", "type": "compiled",    "std_flag": "-std=c++20"},
    28: {"name": "C++14 GCC9", "ext": ".cpp", "type": "compiled",   "std_flag": "-std=c++14"},
    7:  {"name": "Python 3", "ext": ".py",  "type": "interpreted", "std_flag": None},
    25: {"name": "PyPy 3",   "ext": ".py",  "type": "interpreted", "std_flag": None},
}


def compile_and_run_code(code, lang_id, stdin, enable_o2,
                         compile_timeout=10, run_timeout=5):
    """Compile (if needed) and run user code locally with the given stdin.

    Returns a dict:
      - unsupported language   -> {"success": False, "error": "..."}
      - compile failure        -> {"success": True, "compile_failed": True,
                                  "compile_output": "..."}
      - run timeout            -> {"success": True, "timeout": True, ...}
      - normal                 -> {"success": True, "compile_output": "",
                                  "stdout": "...", "stderr": "...",
                                  "exit_code": N, "time_ms": N}
    """
    try:
        lang_id = int(lang_id)
    except (TypeError, ValueError):
        return {"success": False, "error": "无效的语言选项"}

    info = LANG_COMPILE_INFO.get(lang_id)
    if not info:
        return {"success": False, "error": "暂不支持该语言的本地测试"}

    code = code or ""
    stdin = stdin or ""
    tmpdir = tempfile.mkdtemp(prefix="luogu_ide_")
    try:
        src_path = os.path.join(tmpdir, "main" + info["ext"])
        # Force UTF-8 source so /utf-8 + Windows console behave consistently.
        with open(src_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(code)

        compile_output = ""
        if info["type"] == "compiled":
            exe_path = os.path.join(tmpdir, "main.exe")
            compiler = "g++" if info["ext"] == ".cpp" else "gcc"
            if shutil.which(compiler) is None:
                return {"success": False,
                        "error": f"未找到编译器 {compiler}，请确认 {compiler} 已加入系统 PATH"}
            cmd = [compiler]
            if info["std_flag"]:
                cmd.append(info["std_flag"])
            if enable_o2:
                cmd.append("-O2")
            # Force UTF-8 for both source and execution charset so Chinese
            # I/O is consistent on Windows. -w suppresses warning noise.
            cmd += ["-w", "-finput-charset=UTF-8", "-fexec-charset=UTF-8",
                    "-o", exe_path, src_path]
            try:
                cp = subprocess.run(
                    cmd, capture_output=True, timeout=compile_timeout,
                    text=True, encoding="utf-8", errors="replace",
                )
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "编译超时（超过 %ds）" % compile_timeout}
            if cp.returncode != 0:
                return {"success": True, "compile_failed": True,
                        "compile_output": (cp.stderr or cp.stdout or "").strip()}
            compile_output = ((cp.stderr or "") + (cp.stdout or "")).strip()
            run_cmd = [exe_path]
        else:
            py = shutil.which("python")
            if not py:
                return {"success": False,
                        "error": "未找到 python 解释器，请确认 python 已加入系统 PATH"}
            run_cmd = [py, src_path]
            compile_output = ""

        # Run with stdin
        t0 = time.perf_counter()
        try:
            r = subprocess.run(
                run_cmd, input=stdin, capture_output=True, timeout=run_timeout,
                text=True, encoding="utf-8", errors="replace",
            )
        except subprocess.TimeoutExpired:
            time_ms = int((time.perf_counter() - t0) * 1000)
            return {
                "success": True, "timeout": True,
                "compile_output": compile_output,
                "stdout": "", "stderr": "运行超时（超过 %ds）" % run_timeout,
                "exit_code": -1, "time_ms": time_ms,
            }
        time_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "success": True,
            "compile_output": compile_output,
            "stdout": r.stdout or "",
            "stderr": r.stderr or "",
            "exit_code": r.returncode,
            "time_ms": time_ms,
        }
    except Exception as e:
        logger.exception("compile_and_run_code failed")
        return {"success": False, "error": f"运行失败: {e}"}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def build_luogu_session(cookie):
    """Build a requests.Session loaded with user cookies (handles C3VK challenge)."""
    cookie = sanitize_cookie(cookie)
    session = requests.Session()
    session.headers.update(LUOGU_HEADERS)
    if cookie:
        jar = requests.cookies.RequestsCookieJar()
        for part in cookie.split(";"):
            part = part.strip()
            if "=" in part:
                name, value = part.split("=", 1)
                jar.set(name.strip(), value.strip(), domain=".luogu.com.cn", path="/")
        session.cookies = jar
    return session


def _warm_session(session, timeout=10):
    """Visit the Luogu homepage once so the server sets its C3VK challenge
    cookie, then return the session. Without this warm-up, requests to
    public pages (problem list, search) can be answered with 403 by
    Luogu's anti-bot layer.
    """
    try:
        session.get(f"{LUOGU_BASE}/", timeout=timeout)
    except requests.RequestException:
        pass
    return session


def _normalize_output(text):
    """Normalize program output for comparison (strip trailing spaces/newlines)."""
    return "\n".join(line.rstrip() for line in (text or "").splitlines()).strip()


def run_local_cases(code, lang_id, cases, enable_o2=False):
    """Run user code against multiple (input, expected) test cases locally.

    `cases` is a list of dicts: [{"input": "...", "expected": "..."}].
    Returns {"success": bool, "results": [...]} where each result is
    {index, passed, input, expected, actual, time_ms, compile_failed, timeout, stderr}.
    """
    results = []
    for i, case in enumerate(cases or []):
        stdin = (case or {}).get("input", "") if isinstance(case, dict) else str(case or "")
        expected = (case or {}).get("expected", "") if isinstance(case, dict) else ""
        out = compile_and_run_code(code, lang_id, stdin, bool(enable_o2))
        if not out.get("success"):
            results.append({
                "index": i, "passed": False,
                "input": stdin, "expected": expected,
                "error": out.get("error", "运行失败"),
            })
            continue
        if out.get("compile_failed"):
            results.append({
                "index": i, "passed": False,
                "input": stdin, "expected": expected,
                "compile_failed": True,
                "compile_output": (out.get("compile_output") or "").strip(),
            })
            continue
        if out.get("timeout"):
            results.append({
                "index": i, "passed": False,
                "input": stdin, "expected": expected,
                "timeout": True, "time_ms": out.get("time_ms", 0),
                "actual": "",
            })
            continue
        actual = _normalize_output(out.get("stdout", ""))
        expected_norm = _normalize_output(expected)
        results.append({
            "index": i,
            "passed": actual == expected_norm,
            "input": stdin,
            "expected": expected,
            "actual": out.get("stdout", ""),
            "time_ms": out.get("time_ms", 0),
            "stderr": out.get("stderr", ""),
            "exit_code": out.get("exit_code", 0),
        })
    return {"success": True, "results": results}


def run_duipai(code, lang_id, brute_code, brute_lang, gen_code, gen_lang,
               iterations=20, enable_o2=False, run_timeout=5):
    """对拍 (duipai): compare user code against a brute-force program.

    Runs a data generator to produce random inputs, feeds each input to both
    the user's code and the brute-force code, and compares normalized outputs.
    Stops at the first mismatch.

    Returns:
      {"success": True,
       "matched": bool,            # True if all iterations matched
       "iterations": int,          # number of iterations actually compared
       "mismatch": {...}|None,     # first mismatch detail if any
       "errors": [str]}            # per-iteration errors (e.g. timeouts)
    """
    iterations = max(1, min(int(iterations or 20), 200))
    errors = []

    # 1. Compile/check all three programs once (generator is run repeatedly)
    for label, c, lid in (("生成器", gen_code, gen_lang), ("对拍程序", brute_code, brute_lang)):
        if not (c or "").strip():
            return {"success": False, "error": f"缺少{label}代码"}
        probe = compile_and_run_code(c, lid, "", bool(enable_o2))
        if not probe.get("success"):
            return {"success": False, "error": f"{label}无法运行: {probe.get('error', '未知错误')}"}
        if probe.get("compile_failed"):
            return {"success": False, "error": f"{label}编译失败:\n{(probe.get('compile_output') or '').strip()}"}

    matched = True
    mismatch = None
    compared = 0
    for i in range(iterations):
        # 2. Generate random input
        gen = compile_and_run_code(gen_code, gen_lang, "", bool(enable_o2))
        if not gen.get("success"):
            errors.append(f"第{i+1}次: 生成器运行失败")
            continue
        if gen.get("timeout"):
            errors.append(f"第{i+1}次: 生成器运行超时")
            continue
        stdin = gen.get("stdout", "")
        if not stdin.strip():
            errors.append(f"第{i+1}次: 生成器没有输出")
            continue

        # 3. Run user code and brute code on the same input
        mine = compile_and_run_code(code, lang_id, stdin, bool(enable_o2), run_timeout=run_timeout)
        ref = compile_and_run_code(brute_code, brute_lang, stdin, bool(enable_o2), run_timeout=run_timeout)

        if not mine.get("success") or not ref.get("success"):
            errors.append(f"第{i+1}次: 运行失败 (mine={mine.get('error')}, ref={ref.get('error')})")
            continue
        if mine.get("compile_failed") or ref.get("compile_failed"):
            errors.append(f"第{i+1}次: 编译失败")
            continue
        if mine.get("timeout") or ref.get("timeout"):
            errors.append(f"第{i+1}次: 运行超时 (mine={mine.get('timeout')}, ref={ref.get('timeout')})")
            continue
        if mine.get("exit_code", 0) != 0 and not mine.get("stdout"):
            errors.append(f"第{i+1}次: 你的程序非零退出 (exit={mine.get('exit_code')})\n{mine.get('stderr', '')}")
            continue

        compared += 1
        mine_out = _normalize_output(mine.get("stdout", ""))
        ref_out = _normalize_output(ref.get("stdout", ""))
        if mine_out != ref_out:
            matched = False
            mismatch = {
                "iteration": i + 1,
                "input": stdin,
                "userOutput": mine.get("stdout", ""),
                "bruteOutput": ref.get("stdout", ""),
            }
            break

    return {
        "success": True,
        "matched": matched,
        "iterations": compared,
        "mismatch": mismatch,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Captcha -> submit flow via cookie serialization
# The captcha is tied to the HTTP session (cookies). We serialize the session
# cookies after fetching the captcha and return them to the frontend. On
# submit, we rebuild a session with those exact cookies. This avoids fragile
# in-memory session storage that breaks on server restart (debug reloader).
# ---------------------------------------------------------------------------

def _serialize_session_cookies(session):
    """Serialize a requests.Session's cookies into a cookie header string."""
    parts = []
    for c in session.cookies:
        parts.append(f"{c.name}={c.value}")
    return "; ".join(parts)


class CaptchaRequiredError(RuntimeError):
    """Raised when Luogu requires a (possibly interactive) captcha to submit.

    Distinct from ordinary RuntimeError so the frontend can detect
    "captcha required" from the backend flag instead of fragile string
    matching, and can show the captcha modal without entering a refresh loop.
    """


def fetch_captcha(problem_id, cookie, contest_id=""):
    """Fetch captcha image from Luogu for code submission.

    Returns a tuple (result_dict, session) where result_dict has:
      - image: base64-encoded captcha image (data URI)
      - sessionCookies: serialized cookie string (fallback for legacy flow)
      - csrfToken: csrf token extracted from the problem page
    The caller should keep the `session` object alive and pass it to
    submit_code() — Luogu ties captcha validation to the exact HTTP session
    that fetched the captcha image, so rebuilding a new session from
    serialized cookies is unreliable.

    `contest_id` (optional): when set, the problem is visited inside that
    contest (/problem/{pid}?contest={cid}) so submissions count towards it.
    """
    if not cookie:
        raise RuntimeError("提交代码需要登录洛谷，请填入洛谷 Cookie")

    session = build_luogu_session(cookie)

    # Visit problem page to obtain csrf-token and any challenge cookies
    problem_path = f"{LUOGU_BASE}/problem/{problem_id}"
    if contest_id:
        problem_path += f"?contest={contest_id}"
    try:
        page_resp = session.get(problem_path, timeout=15)
    except requests.RequestException as e:
        raise RuntimeError(f"无法访问题目页面: {e}")

    # Extract csrf-token from cookies or HTML meta tag
    csrf_token = None
    for c in session.cookies:
        if c.name == "csrf-token":
            csrf_token = c.value
            break
    if not csrf_token:
        m = re.search(r'<meta name="csrf-token" content="([^"]+)"', page_resp.text)
        if m:
            csrf_token = m.group(1)

    # Fetch captcha image — Luogu associates the captcha with this session's
    # cookies, so we must send the same cookies when submitting code.
    captcha_url = f"{LUOGU_BASE}/api/verify/captcha"
    try:
        resp = session.get(captcha_url, timeout=15)
    except requests.RequestException as e:
        raise RuntimeError(f"获取验证码失败: {e}")

    if resp.status_code != 200:
        raise RuntimeError(f"获取验证码失败 (HTTP {resp.status_code})")

    content_type = resp.headers.get("Content-Type", "image/png")
    image_b64 = base64.b64encode(resp.content).decode("ascii")

    # Serialize cookies as a fallback (in case the in-memory session is lost)
    session_cookies = _serialize_session_cookies(session)

    result = {
        "image": f"data:{content_type};base64,{image_b64}",
        "sessionCookies": session_cookies,
        "csrfToken": csrf_token or "",
    }
    return result, session


def submit_code(problem_id, code, lang_id, cookie, enable_o2=False, verify="",
                session_cookies="", csrf_token="", session=None, contest_id=""):
    """Submit code to Luogu. Returns the record ID (rid).

    Requires login cookie and a captcha verification (verify).
    `session` should be the exact requests.Session that fetched the captcha
    — Luogu ties captcha validation to that session's server-side state, so
    reusing it is the only reliable approach. If not provided, falls back to
    rebuilding a session from serialized cookies (may fail).
    csrf_token should be the token from fetch_captcha().
    `contest_id` (optional): submits the code as a contest submission
    (the endpoint receives ?contestId={cid}).
    """
    if not cookie:
        raise RuntimeError("提交代码需要登录洛谷，请填入洛谷 Cookie")

    # Reuse the exact session that fetched the captcha whenever possible.
    # Falling back to a cookie-rebuilt session is unreliable because Luogu's
    # captcha validation is bound to server-side session state.
    if session is None:
        if session_cookies:
            session = build_luogu_session(session_cookies)
        else:
            session = build_luogu_session(cookie)

    # Use provided csrf_token; otherwise obtain it from the problem page
    # (cookie first, then the <meta name="csrf-token"> tag). This makes a
    # direct submit — no captcha session — self-sufficient.
    if not csrf_token:
        for c in session.cookies:
            if c.name == "csrf-token":
                csrf_token = c.value
                break
    if not csrf_token:
        problem_path = f"{LUOGU_BASE}/problem/{problem_id}"
        if contest_id:
            problem_path += f"?contest={contest_id}"
        try:
            page_resp = session.get(problem_path, timeout=15)
        except requests.RequestException as e:
            raise RuntimeError(f"无法访问题目页面: {e}")
        for c in session.cookies:
            if c.name == "csrf-token":
                csrf_token = c.value
                break
        if not csrf_token:
            m = re.search(r'<meta name="csrf-token" content="([^"]+)"', page_resp.text)
            if m:
                csrf_token = m.group(1)

    if not csrf_token:
        raise RuntimeError("无法获取 CSRF Token，请检查 Cookie 是否有效")

    # Submit code (contest submissions pass ?contestId={cid})
    submit_url = f"{LUOGU_BASE}/fe/api/problem/submit/{problem_id}"
    referer = f"{LUOGU_BASE}/problem/{problem_id}"
    if contest_id:
        submit_url += f"?contestId={contest_id}"
        referer += f"?contest={contest_id}"
    submit_headers = {
        "x-csrf-token": csrf_token,
        "Content-Type": "application/json",
        "Referer": referer,
        "Origin": LUOGU_BASE,
    }

    body = {
        "code": code,
        "lang": int(lang_id),
        "enableO2": 1 if enable_o2 else 0,
        "verify": verify,
    }

    try:
        resp = session.post(submit_url, json=body, headers=submit_headers, timeout=30)
    except requests.RequestException as e:
        raise RuntimeError(f"提交代码失败: {e}")

    try:
        data = resp.json()
    except json.JSONDecodeError:
        logger.error("Submit response not JSON. HTTP %s, body: %s", resp.status_code, resp.text[:500])
        raise RuntimeError(f"提交响应解析失败 (HTTP {resp.status_code})，可能是 Cookie 失效或被反爬拦截")

    # Luogu returns {"rid":12345678} directly on success (no "status" field),
    # or {"status":200,"data":{"rid":...}} in some cases.
    # Error responses contain "status" != 200 or an "errorMessage" field.
    rid = data.get("rid")
    err_msg = ""
    if not rid:
        raw_data = data.get("data", "")
        if isinstance(raw_data, dict):
            rid = raw_data.get("rid")
            err_msg = raw_data.get("errorMessage", "") or raw_data.get("message", "")
        else:
            err_msg = str(raw_data) if raw_data else ""

    if rid:
        return rid

    # No rid found -> treat as error
    status_code = data.get("status")
    if status_code and status_code != 200:
        if not err_msg:
            err_msg = data.get("errorMessage", "") or data.get("data", "")
            if isinstance(err_msg, dict):
                err_msg = err_msg.get("errorMessage", "")
    logger.error("Submit failed. HTTP %s, response: %s", resp.status_code, json.dumps(data, ensure_ascii=False)[:500])
    if not err_msg:
        err_msg = f"提交失败 (HTTP {resp.status_code}, status={status_code}), 响应: {json.dumps(data, ensure_ascii=False)[:200]}"
    if "login" in str(err_msg).lower() or "登录" in str(err_msg):
        raise RuntimeError("需要登录洛谷才能提交代码，请检查 Cookie")
    if "验证码" in str(err_msg) or "captcha" in str(err_msg).lower() or "verify" in str(err_msg).lower():
        raise CaptchaRequiredError("洛谷要求人机验证，请输入验证码")
    raise RuntimeError(str(err_msg))


def _parse_cookie_pairs(cookie_str):
    """Parse a `; `-separated cookie string into a list of (name, value) tuples.

    Segments without '=' are skipped and surrounding whitespace is stripped.
    Values are kept raw (no URL-decoding) so Chinese/URL-encoded special
    characters pass through unchanged to the WebView2 cookie manager.
    """
    pairs = []
    if not cookie_str:
        return pairs
    for part in str(cookie_str).split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, _, value = part.partition("=")
        name = name.strip()
        value = value.strip()
        if name:
            pairs.append((name, value))
    return pairs


# ---------------------------------------------------------------------------
# Vjudge submission
# ---------------------------------------------------------------------------
VJUDGE_BASE = "https://vjudge.net"
VJUDGE_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Vjudge's persistent login cookie is named JSESSlONID (lowercase 'l' inside
# SESSlON). Reused for both validation and submission error messages.
VJUDGE_COOKIE_INVALID_MSG = (
    "Vjudge Cookie 无效或已过期，请重新登录 vjudge.net 后复制 JSESSlONID "
    "Cookie（注意 SESSlON 中是字母 l，不是大写 I）"
)


def _build_vj_pid(problem_id):
    """Build the Vjudge problem id for a Luogu problem.

    Vjudge hosts Luogu problems under the Chinese OJ name "洛谷"
    (e.g. https://vjudge.net/problem/洛谷-P1001). The URL segment must use
    the URL-encoded form, since the English "Luogu" returns a 404.
    """
    return f"{urllib.parse.quote('洛谷')}-{problem_id}"


def _vjudge_lang_id(lang_id):
    """Return the Vjudge 洛谷-origin language id for a Luogu language id.

    Vjudge mirrors Luogu's language ids for its 洛谷 origin (verified via
    /util/cfg, e.g. "12"=C++17, "7"=Python 3, "8"=Java 8), so the value can
    be passed through directly. The special value 0 ("自动语言检测") has no
    Vjudge equivalent and falls back to C++17 (12).
    """
    try:
        lid = int(lang_id)
    except (TypeError, ValueError):
        lid = 0
    return "12" if lid <= 0 else str(lid)


def _vjudge_binding_id(session):
    """Return the READY remote-account binding id for the 洛谷 origin.

    Vjudge submits remote-OJ problems through a bound account; without a
    READY binding the API answers bind_account_missing. The binding list is
    served at /user/remoteAccounts/list?oj=洛谷.
    """
    try:
        resp = session.get(
            f"{VJUDGE_BASE}/user/remoteAccounts/list",
            params={"oj": "洛谷"},
            timeout=20,
        )
        if resp.status_code != 200:
            return None
        rj = resp.json()
    except (requests.RequestException, ValueError):
        return None
    bindings = ((rj.get("groups") or {}).get("洛谷") or {}).get("bindings") or []
    for b in bindings:
        if b.get("runtimeStatus") == "READY" and b.get("id"):
            return b.get("id")
    return None


# Vjudge submission errors are returned as JSON carrying an i18nKey; translate
# the common ones into friendly Chinese messages.
_VJUDGE_SUBMIT_ERRORS = {
    "submit.error.illegal_language": "语言选项无效，请选择受支持的语言",
    "submit.error.duplicate_code": "与之前提交的代码重复，请稍作修改后再提交",
    "bind_account_missing": "Vjudge 未绑定洛谷账号，请在 vjudge.net「个人中心 → "
                            "Remote Accounts」中绑定并授权洛谷账号后重试",
    "bind_account_invalid": "Vjudge 绑定的洛谷账号无效，请在 vjudge.net 重新绑定",
    "bind_account_locked": "Vjudge 绑定的洛谷账号已被锁定，请在 vjudge.net 处理",
    "bind_account_disconnected": "Vjudge 绑定的洛谷账号已断开，请在 vjudge.net 重新授权",
}


def _vjudge_submit_error(resp_json, resp):
    """Extract a friendly error message from a failed Vjudge submit response."""
    if resp_json:
        err = resp_json.get("error") or {}
        i18n = err.get("i18nKey") if isinstance(err, dict) else err
        if i18n in _VJUDGE_SUBMIT_ERRORS:
            return _VJUDGE_SUBMIT_ERRORS[i18n]
        msg = resp_json.get("message") or ""
        if msg in _VJUDGE_SUBMIT_ERRORS:
            return _VJUDGE_SUBMIT_ERRORS[msg]
        if msg:
            return msg
    if resp is not None:
        if resp.status_code == 401 or "login" in resp.text.lower():
            return VJUDGE_COOKIE_INVALID_MSG
        return f"HTTP {resp.status_code}"
    return "未知错误"


def _build_vjudge_session(vjudge_cookie):
    """Build a requests.Session from a Vjudge cookie string.

    Accepts "JSESSIONID=xxx", "JSESSlONID=xxx" (Vjudge's current long-lived
    login cookie uses a lowercase 'l' inside SESSlON), or just "xxx".
    """
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": VJUDGE_UA,
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
    })
    cookie_val = vjudge_cookie.strip()
    # Strip any "JSESSIONID"/"JSESSlONID" prefix (case-insensitive).
    # [IiLl] covers both "SESSION" (capital I) and "SESSlON" (lowercase l).
    m = re.match(r'^\s*JSESS[IiLl]ONID\s*=\s*(.+)$', cookie_val, re.IGNORECASE)
    if m:
        cookie_val = m.group(1).strip()
    if cookie_val:
        # Vjudge reads the long-lived JSESSlONID cookie (lowercase 'l'); send
        # it under both names so either browser cookie works. Path=/ ensures it
        # is sent on every request.
        for name in ("JSESSIONID", "JSESSlONID"):
            sess.cookies.set(name, cookie_val, domain=".vjudge.net", path="/")
    return sess


def _vjudge_session_is_authenticated(session):
    """Check whether a Vjudge session is logged in.

    Vjudge renders a "login" navbar item for anonymous visitors and a
    "logout" navbar item for authenticated users; protected routes redirect to
    "/?login=1&continue=..." when not logged in. These are the reliable
    signals -- probing /problem/Luogu-P1000 (the old approach) returns HTTP
    404 even for valid sessions, causing false "invalid" results.
    """
    try:
        resp = session.get(f"{VJUDGE_BASE}/", timeout=20)
    except requests.RequestException:
        return False
    if resp.status_code != 200:
        return False
    text = resp.text
    # Authenticated navbar marker: logout item.
    if 'top-nav-logout-item' in text or 'nav-link logout' in text:
        if 'top-nav-login-item' not in text and 'nav-link login' not in text:
            return True
    # Unauthenticated navbar marker: login item.
    if 'top-nav-login-item' in text or 'nav-link login' in text \
            or 'top.nav.login' in text:
        return False
    # Neither navbar marker found: probe a protected route, which redirects to
    # /?login=1 when the session is not authenticated.
    try:
        probe = session.get(f"{VJUDGE_BASE}/problem/search", timeout=20)
        if "?login" in probe.url or "login=" in probe.url.lower():
            return False
    except requests.RequestException:
        pass
    return True


def _vjudge_login(username, password):
    """Log in to Vjudge with account credentials and return an authenticated session.

    Vjudge's session cookie (JSESSlONID) is regenerated on every login, so a
    saved cookie is not a stable credential and must be re-copied each time.
    Logging in with the account credentials on every submission yields a fresh
    session automatically -- the stable, invariant authentication method.
    Raises RuntimeError with a friendly message on failure.
    """
    username = (username or "").strip()
    password = password or ""
    if not username or not password:
        raise RuntimeError("请填写 Vjudge 用户名和密码")
    session = requests.Session()
    session.headers.update({
        "User-Agent": VJUDGE_UA,
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
    })
    try:
        resp = session.post(
            f"{VJUDGE_BASE}/user/login",
            data={"username": username, "password": password},
            timeout=20,
        )
    except requests.RequestException as e:
        raise RuntimeError(f"无法连接 Vjudge 服务器: {e}")
    if resp.status_code != 200:
        try:
            rj = resp.json()
        except ValueError:
            rj = {}
        err = rj.get("error") or {}
        i18n = err.get("i18nKey") if isinstance(err, dict) else None
        if i18n == "user.auth.error.invalid_credentials":
            raise RuntimeError("Vjudge 用户名或密码错误，请检查后重试")
        if i18n in ("user.auth.error.too_many_attempts",
                    "user.auth.error.login_attempts_exceeded",
                    "user.auth.error.rate_limit"):
            raise RuntimeError("Vjudge 登录尝试过于频繁，请稍等几分钟后再试")
        if i18n in ("user.auth.error.need_captcha",
                    "user.auth.error.verify_code"):
            raise RuntimeError("Vjudge 要求人机验证，请稍后重试或改用备用 Cookie 方式提交")
        if i18n:
            raise RuntimeError(f"Vjudge 登录失败: {i18n}")
        raise RuntimeError(f"Vjudge 登录失败 (HTTP {resp.status_code})")
    if not _vjudge_session_is_authenticated(session):
        raise RuntimeError("Vjudge 登录未生效，请稍后重试")
    return session


def submit_vjudge(problem_id, code, lang_id, vjudge_cookie, vjudge_username="", vjudge_password=""):
    """Submit code to Vjudge (洛谷 origin). Returns the evaluation page URL.

    Vjudge's current (2026-08) submission API:
      1. Problem ids use the URL-encoded Chinese OJ name, e.g.
         /problem/%E6%B4%9B%E8%B0%B7-P1001 (洛谷-P1001).
      2. Resolve the READY remote-account binding for the 洛谷 origin from
         /user/remoteAccounts/list?oj=洛谷.
      3. POST /problem/submit/<vj_pid> with form data: method=1,
         language=<Luogu lang id>, open=0, source=<plain text>, token="",
         bindingId=<binding id>.
      4. Success responds JSON {"runId": N}; the evaluation page is
         /solution/<N>.
    """
    username = (vjudge_username or "").strip()
    password = vjudge_password or ""
    if username and password:
        # Preferred stable method: auto-login with the account credentials so
        # a fresh session cookie is obtained on every submission (no manual
        # cookie re-entry). Falls back to the saved cookie when no creds.
        session = _vjudge_login(username, password)
    elif vjudge_cookie:
        session = _build_vjudge_session(vjudge_cookie)
    else:
        raise RuntimeError("提交到 Vjudge 需要登录，请填写 Vjudge 用户名和密码（或 Cookie）")

    # Step 1: fetch the problem page to get the numeric problemId
    vj_pid = _build_vj_pid(problem_id)
    problem_url = f"{VJUDGE_BASE}/problem/{vj_pid}"
    try:
        resp = session.get(problem_url, timeout=20)
    except requests.RequestException as e:
        raise RuntimeError(f"无法访问 Vjudge 题目页面: {e}")

    # Vjudge redirects unauthenticated visitors to /?login=1 even on a 200.
    if "?login" in resp.url or "login=" in resp.url.lower():
        raise RuntimeError(VJUDGE_COOKIE_INVALID_MSG)
    if resp.status_code != 200:
        # A 404 on a Luogu-* URL with a valid session means Vjudge does not
        # host this specific problem (e.g. wrong/unknown problem number) --
        # not a cookie problem. Check the session first so we give an
        # accurate message.
        if resp.status_code == 404 and _vjudge_session_is_authenticated(session):
            raise RuntimeError(
                f"Vjudge 上不存在题目 {vj_pid}：该题在 Vjudge 中不存在，"
                "请确认题号是否正确（洛谷题在 Vjudge 中的格式为 洛谷-题号，"
                "例如 洛谷-P1001）。")
        raise RuntimeError(
            f"Vjudge 返回 {resp.status_code}。{VJUDGE_COOKIE_INVALID_MSG}")

    # Step 2: resolve the remote-account binding for the 洛谷 origin.
    binding_id = _vjudge_binding_id(session)
    if not binding_id:
        raise RuntimeError(_VJUDGE_SUBMIT_ERRORS["bind_account_missing"])

    # Step 3: submit code to the per-problem endpoint. The source is sent as
    # plain text (not base64) with the Luogu language id passed through, and
    # the bound remote account identified by bindingId.
    submit_headers = {
        "Referer": problem_url,
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest",
    }
    submit_data = {
        "method": "1",
        "language": _vjudge_lang_id(lang_id),
        "open": "0",
        "source": code,
        "token": "",
        "bindingId": str(binding_id),
    }

    try:
        submit_resp = session.post(
            f"{VJUDGE_BASE}/problem/submit/{vj_pid}",
            data=submit_data,
            headers=submit_headers,
            timeout=30,
            allow_redirects=False,
        )
    except requests.RequestException as e:
        raise RuntimeError(f"提交到 Vjudge 失败: {e}")

    # Step 4: success responds {"runId": N}; the evaluation page is
    # /solution/<N> (the old /status/<N> path returns 404).
    try:
        sj = submit_resp.json()
    except Exception:
        sj = None
    if sj and sj.get("runId"):
        return f"{VJUDGE_BASE}/solution/{sj['runId']}"

    raise RuntimeError(
        f"Vjudge 提交失败: {_vjudge_submit_error(sj, submit_resp)}")


def _find_record_data(data):
    """Search for record dict in all known Luogu response shapes.

    Handles:
      Shape A (JSON _contentOnly):  {"code":200, "currentData":{"record":{...}}}
      Shape B (HTML embedded):      {"status":200, "data":{"currentData":{"record":{...}}}}
      Shape C (direct):             {"record":{...}}
    """
    if not isinstance(data, dict):
        return None
    # Shape A
    cd = data.get("currentData")
    if isinstance(cd, dict) and isinstance(cd.get("record"), dict):
        return cd["record"]
    # Shape B
    dd = data.get("data")
    if isinstance(dd, dict):
        cd2 = dd.get("currentData")
        if isinstance(cd2, dict) and isinstance(cd2.get("record"), dict):
            return cd2["record"]
        # Also try data.record directly
        if isinstance(dd.get("record"), dict):
            return dd["record"]
    # Shape C
    if isinstance(data.get("record"), dict):
        return data["record"]
    return None


def fetch_record(rid, cookie=""):
    """Fetch judge result for a given record ID. Returns parsed result dict.

    Robust against different Luogu response formats (JSON vs HTML-embedded).
    Returns partial data (status only) when the record is still being judged
    and full detail is not yet available.
    """
    session = build_luogu_session(cookie)

    # Try the _contentOnly JSON endpoint first
    url = f"{LUOGU_BASE}/record/{rid}?_contentOnly=1"
    try:
        resp = session.get(url, timeout=15)
    except requests.RequestException as e:
        raise RuntimeError(f"获取评测结果失败: {e}")

    # Detect redirect to login page (expired/invalid cookie)
    final_url = resp.url or ""
    if "login" in final_url.lower() or "auth" in final_url.lower():
        raise RuntimeError("Cookie 已失效，请重新填入洛谷 Cookie")

    # Parse response: try JSON first (from _contentOnly=1), then HTML extraction
    data = None
    try:
        data = resp.json()
    except (json.JSONDecodeError, ValueError):
        data = extract_luogu_data(resp.text)

    if not data or not isinstance(data, dict):
        raise RuntimeError("无法解析评测结果页面数据")

    # Extract error message if present (before searching for record)
    err_msg = (
        (data.get("currentData") or {}).get("errorMessage")
        or (data.get("data") or {}).get("errorMessage")
        or data.get("errorMessage")
    )

    # Find record data in all possible nested locations
    record_data = _find_record_data(data)

    if not record_data:
        # If we got an explicit error from Luogu, surface it
        if err_msg:
            raise RuntimeError(str(err_msg))
        # Check status codes — if clearly an error, report it
        code = data.get("code")
        status = data.get("status")
        if code is not None and code != 200 and status is None:
            raise RuntimeError(f"洛谷返回错误 (code={code})")
        if status is not None and status != 200 and code is None:
            raise RuntimeError(f"洛谷返回错误 (status={status})")
        raise RuntimeError("评测记录数据为空，可能记录不存在或 Cookie 已失效")

    # Build a clean result dict
    detail = record_data.get("detail") or {}
    judge_result = detail.get("judgeResult") or {}

    # Subtask results. testCases is a dict {id: testCase} in Luogu's API.
    subtasks = judge_result.get("subtasks") or []
    test_cases = []
    for st in subtasks:
        if not isinstance(st, dict):
            continue
        tc_dict = st.get("testCases", {})
        # testCases may be dict or list; normalize to iterable of cases
        tc_iter = tc_dict.values() if isinstance(tc_dict, dict) else (tc_dict or [])
        for tc in tc_iter:
            if not isinstance(tc, dict):
                continue
            test_cases.append({
                "case": tc.get("id", 0),
                "status": tc.get("status", 0),
                "time": tc.get("time", 0),
                "memory": tc.get("memory", 0),
                "score": tc.get("score", 0),
                "signal": tc.get("signal", 0),
                "message": tc.get("description", "") or tc.get("message", ""),
            })

    return {
        "rid": record_data.get("id", rid),
        "pid": (record_data.get("problem") or {}).get("pid", ""),
        "title": (record_data.get("problem") or {}).get("title", ""),
        "score": record_data.get("score", 0),
        "status": record_data.get("status", 0),
        "time": record_data.get("time", 0),
        "memory": record_data.get("memory", 0),
        "language": record_data.get("language", 0),
        "language_name": record_data.get("languageName", ""),
        "enable_o2": record_data.get("enableO2", False),
        "judge": {
            "subtask_status": judge_result.get("subtaskStatus", ""),
            "subtask_score": judge_result.get("subtaskScore", 0),
        },
        "test_cases": test_cases,
    }


# Luogu judge status code -> human-readable text
LUOGU_STATUS_MAP = {
    0: "Waiting",
    1: "Judging",
    2: "CE",
    3: "OLE",
    4: "MLE",
    5: "TLE",
    6: "WA",
    7: "RE",
    8: "AC",
    9: "Hack",
    11: "Unaccepted",
    12: "AC",
    14: "UKE",
}


# ---------------------------------------------------------------------------
# Windows system notifications (zero pip dependencies)
# ---------------------------------------------------------------------------
# Uses the Windows PowerShell WinRT Toast API (ships with Win10/11) so no
# third-party package (win10toast / plyer / etc.) is required. Everything is
# best-effort: failures are swallowed so they can never break the judge flow.
_TOAST_APP_ID = "LuoguHelper"


def _ensure_toast_shortcut():
    """Create a Start Menu shortcut with our AppUserModelID (best-effort).

    Windows 10+ only shows WinRT toasts for a desktop app when the AUMID has
    a matching shortcut in the Start Menu. Runs once; subsequent calls are
    no-ops after the shortcut exists.
    """
    try:
        if not sys.platform.startswith("win"):
            return
        start_menu = os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs",
        )
        lnk = os.path.join(start_menu, "LuoguHelper.lnk")
        if os.path.exists(lnk):
            return
        target = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
        ps = (
            "$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{lnk}'); "
            f"$s.TargetPath = '{target}'; "
            "$s.Save()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
            capture_output=True, timeout=15,
        )
    except Exception:
        pass


def show_system_notification(title, message):
    """Show a Windows 10/11 toast notification with no pip dependencies.

    Returns True when dispatched to a background thread (even if the toast
    itself later fails silently), False on non-Windows platforms.
    """
    if not sys.platform.startswith("win"):
        return False

    def _run():
        try:
            # Associate this process with our AUMID so CreateToastNotifier
            # can resolve it even before the Start Menu shortcut exists.
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(_TOAST_APP_ID)
            except Exception:
                pass
            _ensure_toast_shortcut()
            esc = lambda s: (s or "").replace("'", "''")
            ps = (
                "[Windows.UI.Notifications.ToastNotificationManager, "
                "Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
                "$t = [Windows.UI.Notifications.ToastNotificationManager]"
                "::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]"
                "::ToastText02); "
                "$nodes = $t.GetElementsByTagName('text'); "
                f"$nodes.Item(0).AppendChild($t.CreateTextNode('{esc(title)}')) | Out-Null; "
                f"$nodes.Item(1).AppendChild($t.CreateTextNode('{esc(message)}')) | Out-Null; "
                "$toast = [Windows.UI.Notifications.ToastNotification]::new($t); "
                "[Windows.UI.Notifications.ToastNotificationManager]"
                f"::CreateToastNotifier('{_TOAST_APP_ID}').Show($toast)"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                capture_output=True, timeout=10,
            )
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()
    return True


def status_text(status_code):
    """Convert Luogu status code to readable text."""
    return LUOGU_STATUS_MAP.get(status_code, f"Unknown({status_code})")


# ---------------------------------------------------------------------------
# Solution filtering (no API key mode)
# ---------------------------------------------------------------------------

CODE_BLOCK_RE = re.compile(r"```(\w*)\n?(.*?)```", re.DOTALL)

POPULAR_LANGS = {
    "cpp", "c++", "c", "python", "python3", "py", "java", "pascal",
    "go", "rust", "c#", "javascript", "js", "ruby", "php",
}

COMPLEXITY_KEYWORDS = re.compile(
    r"(时间复杂度|空间复杂度|O\(|复杂度|复杂度分析|时间|空间)", re.IGNORECASE
)


def extract_code_blocks(content):
    """Extract (language, code) tuples from markdown content."""
    matches = CODE_BLOCK_RE.findall(content or "")
    return [(lang.strip().lower() or "text", code.strip()) for lang, code in matches]


def strip_code_blocks(content):
    """Remove code blocks from markdown to get text-only content."""
    return CODE_BLOCK_RE.sub("", content or "").strip()


def score_solution(solution):
    """Score a solution by content quality, prioritising code examples."""
    content = solution.get("content", "")
    score = 0

    code_blocks = extract_code_blocks(content)
    if code_blocks:
        score += 10
        score += min(len(code_blocks) * 2, 8)
        total_code_len = sum(len(code) for _, code in code_blocks)
        score += min(total_code_len // 100, 20)
        for lang, _ in code_blocks:
            if lang in POPULAR_LANGS:
                score += 3
                break

    text = strip_code_blocks(content)
    if len(text) > 50:
        score += 5
        score += min(len(text) // 200, 15)

    if COMPLEXITY_KEYWORDS.search(content):
        score += 5

    score += solution.get("rating", 0) // 2
    return score


def filter_solutions(solutions_data, top_n=5):
    """Filter and rank solutions by quality."""
    raw_solutions = solutions_data.get("result", solutions_data.get("data", []))
    scored = []

    for sol in raw_solutions:
        content = sol.get("content", "")
        score = score_solution(sol)
        code_blocks = extract_code_blocks(content)
        scored.append({
            "id": sol.get("id"),
            "author": sol.get("author", {}).get("name", "匿名用户"),
            "content": content,
            "score": score,
            "code_blocks": code_blocks,
            "rating": sol.get("rating", 0),
            "has_code": bool(code_blocks),
        })

    scored.sort(key=lambda x: (x["has_code"], x["score"]), reverse=True)
    return scored[:top_n]


# ---------------------------------------------------------------------------
# AI model integration (DeepSeek + GLM)
# ---------------------------------------------------------------------------

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# GLM model identifiers
GLM_MODELS = {"glm-4", "glm-4-flash", "glm-4.5-air"}


def is_glm_model(model):
    """Return True if the given model name is a GLM model."""
    return (model or "").strip() in GLM_MODELS


def build_analysis_prompt(problem, solutions):
    """Build a comprehensive prompt for DeepSeek to analyse problem and solutions."""
    pid = problem["pid"]
    title = problem["title"]

    problem_text = f"""## 题目信息

**题号**: {pid}
**标题**: {title}
**题目描述**:
{problem.get('description', '（无）')}

**输入格式**:
{problem.get('inputFormat', '（无）')}

**输出格式**:
{problem.get('outputFormat', '（无）')}
"""
    samples = problem.get("samples", [])
    if samples:
        sample_text = "\n".join(
            f"样例 {i+1}:\n输入: {s.get('in', '')}\n输出: {s.get('out', '')}"
            for i, s in enumerate(samples)
        )
        problem_text += f"\n**样例**:\n{sample_text}\n"

    if problem.get("hint"):
        problem_text += f"\n**提示**:\n{problem['hint']}\n"

    # Solutions section (if available)
    if solutions:
        solution_parts = []
        for i, sol in enumerate(solutions[:5], 1):
            content = sol["content"]
            if len(content) > 3000:
                content = content[:3000] + "\n...(内容过长已截断)"
            solution_parts.append(
                f"### 题解 {i} (作者: {sol['author']}, 评分: {sol['score']})\n{content}"
            )
        solutions_text = "\n\n---\n\n".join(solution_parts)

        prompt = f"""{problem_text}

## 题解内容

以下是该题目的多个题解，请仔细阅读并分析：

{solutions_text}

## 分析要求

请作为一位经验丰富的算法竞赛教练，对以上题解进行全面分析，输出以下内容（使用 Markdown 格式）:

### 1. 题目分析
简要概括题目的要求和考察的知识点。

### 2. 解题思路总结
综合所有题解，总结主流的解题思路和算法，说明每种方法的原理和适用场景。

### 3. 算法复杂度
分析每种方法的时间复杂度和空间复杂度。

### 4. 示例代码
从题解中选取最优的代码实现，或综合多份题解给出一份完整的、带注释的示例代码。请标注编程语言，并确保代码可以直接提交通过。

### 5. 关键点与易错点
总结解题过程中的关键技巧和常见错误，帮助避免 WA / TLE / RE。

### 6. 拓展建议
给出相关的练习建议或拓展方向。
"""
    else:
        # No solutions available - ask DeepSeek to solve the problem
        prompt = f"""{problem_text}

## 分析要求

暂无题解数据，请作为一位经验丰富的算法竞赛教练，直接分析此题目并给出解答，输出以下内容（使用 Markdown 格式）:

### 1. 题目分析
简要概括题目的要求和考察的知识点。

### 2. 解题思路
给出最优的解题思路和算法，说明原理和适用场景。

### 3. 算法复杂度
分析时间复杂度和空间复杂度。

### 4. 示例代码
给出一份完整的、带注释的示例代码。请标注编程语言，并确保代码可以直接提交通过。

### 5. 关键点与易错点
总结解题过程中的关键技巧和常见错误，帮助避免 WA / TLE / RE。

### 6. 拓展建议
给出相关的练习建议或拓展方向。
"""
    return prompt


def analyze_with_deepseek(problem, solutions, api_key, model="deepseek-chat"):
    """Call an AI chat completions API (DeepSeek or GLM) to analyse solutions.

    Dispatches to the GLM endpoint when `model` is a GLM model; otherwise uses
    the DeepSeek endpoint. Both APIs share the same OpenAI-compatible schema.
    """
    prompt = build_analysis_prompt(problem, solutions)
    glm = is_glm_model(model)
    api_url = GLM_API_URL if glm else DEEPSEEK_API_URL
    provider = "GLM" if glm else "DeepSeek"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一位经验丰富的算法竞赛教练，擅长分析算法题目和题解，"
                    "能够清晰讲解解题思路、算法原理，并提供高质量的示例代码。"
                    "请使用 Markdown 格式输出，代码块请标注语言类型。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    try:
        resp = requests.post(api_url, headers=headers, json=body, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        error_body = ""
        try:
            error_body = e.response.json().get("error", {}).get("message", "")
        except Exception:
            pass
        logger.error("%s API error %s: %s", provider, status, error_body)
        raise RuntimeError(f"{provider} API 调用失败 (HTTP {status}): {error_body}")
    except requests.RequestException as e:
        logger.error("%s request failed: %s", provider, e)
        raise RuntimeError(f"{provider} API 网络错误: {e}")


def ai_translate(text, target_lang="en", model=""):
    """Translate `text` into the target language using the bound AI model.

    Uses the same provider selection as the analyzer (DeepSeek / GLM) and
    reads the API key from the saved config. target_lang is "en" or "zh".
    Returns the translated string, raising RuntimeError on failure.
    """
    model = (model or load_config().get("model") or "deepseek-chat").strip() or "deepseek-chat"
    cfg = load_config()
    if is_glm_model(model):
        api_key = (cfg.get("glm_api_key") or "").strip()
        provider = "GLM"
    else:
        api_key = (cfg.get("api_key") or "").strip()
        provider = "DeepSeek"
    if not api_key:
        raise RuntimeError(f"缺少 {provider} API Key，请先在设置中配置")

    lang_label = "English" if target_lang == "en" else "中文"
    system = (
        "你是一位专业的算法竞赛题目翻译助手。请将用户提供的题目内容翻译成"
        f"{lang_label}。要求：\n"
        "1. 只输出翻译结果，不要输出任何解释或额外文字；\n"
        "2. 保留 Markdown 格式、LaTeX 公式（$...$/$$...$$）与代码块不变；\n"
        "3. 术语翻译准确，语句通顺自然。"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]
    api_url = GLM_API_URL if is_glm_model(model) else DEEPSEEK_API_URL
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    try:
        resp = requests.post(api_url, headers=headers, json=body, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return (content or "").strip()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        error_body = ""
        try:
            error_body = e.response.json().get("error", {}).get("message", "")
        except Exception:
            pass
        logger.error("%s translate API error %s: %s", provider, status, error_body)
        raise RuntimeError(f"{provider} API 调用失败 (HTTP {status}): {error_body}")
    except requests.RequestException as e:
        logger.error("%s translate request failed: %s", provider, e)
        raise RuntimeError(f"{provider} API 网络错误: {e}")
    except (KeyError, IndexError) as e:
        logger.error("%s translate response parse error: %s", provider, e)
        raise RuntimeError(f"{provider} API 响应解析失败: {e}")


# ---------------------------------------------------------------------------
# Streaming AI chat (assistant). Uses provider SSE streaming; each content
# delta is forwarded to the frontend via on_delta(kind, text) where kind is
# "reasoning" (thinking trace) or "content" (final answer).
# ---------------------------------------------------------------------------

def stream_ai_chat(messages, api_key, model, on_delta, thinking=False):
    """Stream a chat completion, invoking on_delta(kind, text) per delta.

    Supports both DeepSeek and GLM (OpenAI-compatible) endpoints. For GLM,
    enabling "thinking" returns reasoning_content; DeepSeek reasoner models
    expose reasoning_content natively. markdown + latex are rendered client
    side, so the raw text is streamed unchanged.
    """
    model = (model or "deepseek-chat").strip() or "deepseek-chat"
    glm = is_glm_model(model)
    provider = "GLM" if glm else "DeepSeek"
    api_url = GLM_API_URL if glm else DEEPSEEK_API_URL

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 4096,
    }
    # GLM-4/GLM-4.5 family supports an explicit thinking toggle; DeepSeek
    # reasoner models think intrinsically (no request flag needed).
    if glm and thinking:
        body["thinking"] = {"type": "enabled"}

    try:
        with requests.post(api_url, headers=headers, json=body, timeout=120,
                           stream=True) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8", "ignore")
                if not line.startswith("data:"):
                    continue
                payload = line[len("data:"):].strip()
                if payload == "[DONE]":
                    break
                try:
                    obj = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                choices = obj.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                if delta.get("reasoning_content"):
                    on_delta("reasoning", delta["reasoning_content"])
                if delta.get("content"):
                    on_delta("content", delta["content"])
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        error_body = ""
        try:
            error_body = e.response.json().get("error", {}).get("message", "")
        except Exception:
            pass
        logger.error("%s stream API error %s: %s", provider, status, error_body)
        raise RuntimeError(f"{provider} API 调用失败 (HTTP {status}): {error_body}")
    except requests.RequestException as e:
        logger.error("%s stream request failed: %s", provider, e)
        raise RuntimeError(f"{provider} API 网络错误: {e}")


def build_assistant_messages(history, problem):
    """Build the message list for the assistant chat.

    `history` is a list of {"role": "user"|"assistant", "content": str}.
    When a problem is provided, its info is injected as context so the
    assistant can answer questions about the currently open problem.
    """
    system_parts = [
        "你是一位经验丰富的算法竞赛教练与编程助手。请使用 Markdown 格式回答，"
        "数学公式使用 LaTeX（行内用 $...$，独立公式用 $$...$$），代码块标注语言类型。",
    ]
    if problem and problem.get("pid"):
        system_parts.append(
            "用户当前正在查看这道题目：\n"
            f"题号 {problem.get('pid')}，标题《{problem.get('title', '')}》。\n"
            "题目描述：\n"
            f"{problem.get('description', '（无）')}\n"
            "输入格式：\n"
            f"{problem.get('inputFormat', '（无）')}\n"
            "输出格式：\n"
            f"{problem.get('outputFormat', '（无）')}\n"
            "请优先围绕这道题回答；若用户询问无关内容也可正常回答。"
        )
    messages = [{"role": "system", "content": "\n\n".join(system_parts)}]
    for msg in history or []:
        role = "assistant" if msg.get("role") == "assistant" else "user"
        messages.append({"role": role, "content": msg.get("content", "")})
    return messages


def build_failure_messages(problem, code, lang, judge):
    """Build messages for 'AI 错因讲题': analyze why a submission failed.

    `problem` is the problem info, `code` the user's code, `lang` the language
    name, and `judge` a dict with status/score/result details.
    """
    status = (judge or {}).get("status")
    status_text = "未知"
    _status_map = {12: "Accepted (AC)", 0: "Unaccepted (WA)",
                   2: "Compile Error (CE)", 3: "Runtime Error (RE)",
                   4: "Time Limit Exceeded (TLE)", 5: "Memory Limit Exceeded (MLE)",
                   7: "Wrong Answer (WA)", 11: "Score/Partial", 1: "In Queue"}
    if isinstance(status, int):
        status_text = _status_map.get(status, f"状态 {status}")
    score = (judge or {}).get("score")

    system = (
        "你是一位严谨的算法竞赛教练。用户提交的代码评测未通过，请你定位错误原因并讲解。\n"
        "请使用 Markdown 回答，包含：\n"
        "1. **错误类型分析**：根据评测状态（如 WA/RE/TLE/CE）判断可能原因；\n"
        "2. **代码审查**：指出代码中的具体问题（引用到相关行/片段）；\n"
        "3. **算法与边界**：分析思路是否正确、是否遗漏边界情况；\n"
        "4. **改进建议**：给出可运行的修改思路或正确写法。\n"
        "数学公式用 LaTeX（$...$/$$...$$），代码块标注语言类型。"
    )
    problem_part = ""
    if problem and problem.get("pid"):
        problem_part = (
            f"题目：{problem.get('pid')}《{problem.get('title', '')}》\n"
            f"题目描述：{problem.get('description', '（无）')}\n"
            f"输入格式：{problem.get('inputFormat', '（无）')}\n"
            f"输出格式：{problem.get('outputFormat', '（无）')}\n"
        )
    user = (
        f"评测状态：{status_text}\n"
        f"得分：{score if score is not None else '未知'}\n"
        f"语言：{lang or '未知'}\n"
        f"{problem_part}"
        "用户代码：\n```\n"
        f"{code}\n"
        "```\n请分析这段代码为何未通过评测并给出讲解。"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ---------------------------------------------------------------------------
# pywebview API: exposes backend functions to frontend JS without HTTP server
# ---------------------------------------------------------------------------

# JS installed into the embedded Luogu submit window after the page loads.
# It hooks window.fetch and XMLHttpRequest, captures the response of any
# request whose URL contains "/fe/api/problem/submit/", extracts {"rid": N}
# and forwards it to Python via window.pywebview.api.on_embedded_submit_rid(N).
_SUBMIT_INTERCEPTOR_JS = (
    "(function(){if(window.__luoguSubmitHook)return;window.__luoguSubmitHook=true;"
    "var f=window.fetch;if(f){window.fetch=function(){var a=arguments;return f.apply(this,a).then(function(r){try{var u=(a[0]&&a[0].url)?a[0].url:String(a[0]);if(u.indexOf('/fe/api/problem/submit/')>-1){r.clone().json().then(function(d){if(d&&d.rid){try{window.pywebview.api.on_embedded_submit_rid(d.rid);}catch(e){}}}).catch(function(){})}}catch(e){}return r})}}"
    "var X=XMLHttpRequest.prototype,o=X.open,s=X.send;X.open=function(m,u){this.__luoguUrl=String(u);return o.apply(this,arguments)};X.send=function(){var t=this;this.addEventListener('load',function(){try{var u=t.__luoguUrl||'';if(u.indexOf('/fe/api/problem/submit/')>-1){var d=JSON.parse(t.responseText);if(d&&d.rid){try{window.pywebview.api.on_embedded_submit_rid(d.rid)}catch(e){}}}}catch(e){}});return s.apply(this,arguments)}})();"
)

# Injected into the embedded submit window after the real Luogu page loads. It
# waits for the CodeMirror 6 editor ('.cm-content') to appear — which also
# implies the page is logged in with the injected cookie — then auto-fills the
# code, mirrors the O2 checkbox, selects the requested language (or auto-detect)
# and clicks 提交评测. The user is only left with solving Luogu's interactive
# (NetEase Yidun) captcha; the fetch/XHR interceptor then captures the rid.
# __CODE__ / __LANG__ / __O2__ are substituted by the caller.
_AUTO_SUBMIT_JS = (
    "(function(){"
    "if(window.__luoguAutoSubmitDone){return}window.__luoguAutoSubmitDone=true;"
    "var CODE=__CODE__;var LANG=__LANG__;var O2=__O2__;var tries=0;"
    "function clickSubmit(){"
    "var bs=document.querySelectorAll('button');"
    "for(var i=0;i<bs.length;i++){if(bs[i].textContent.indexOf('\u63d0\u4ea4\u8bc4\u6d4b')>-1){bs[i].click();return true}}return false}"
    "function setO2(){"
    "var cbs=document.querySelectorAll('input[type=checkbox]');"
    "for(var i=0;i<cbs.length;i++){if(cbs[i].checked!==O2){cbs[i].click();break}}}"
    "function submitIt(){"
    "setO2();"
    "if(LANG){"
    "var combo=document.querySelector('.combo-wrapper.lang-select');"
    "if(combo){combo.click();setTimeout(function(){"
    "var lis=document.querySelectorAll('.combo-wrapper.lang-select li');var hit=null;"
    "for(var i=0;i<lis.length;i++){if(lis[i].textContent.trim()===LANG){hit=lis[i];break}}"
    "if(hit)hit.click();"
    "setTimeout(clickSubmit,250);"
    "},250);return}}"
    "clickSubmit()}"
    "function doFill(){"
    "var ed=document.querySelector('.cm-content');"
    "if(!ed){if(tries++<60){setTimeout(doFill,500)}return}"
    "ed.focus();ed.innerText='';"
    "try{var dt=new DataTransfer();dt.setData('text/plain',CODE);"
    "ed.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}))}catch(e){}"
    "setTimeout(submitIt,400)}"
    "doFill()"
    "})();"
)

# Luogu's in-page language dropdown labels can differ from the app's
# LUOGU_LANG_OPTIONS names (e.g. "C# Mono" vs "C# (Mono)", "Node.js LTS" vs
# "Node.js"). Map the known divergences; anything unknown falls back to
# auto-detect ("自动识别语言"), which is always present in the dropdown.
_LUOGU_DROPDOWN_LANG_ALIAS = {
    0: "自动识别语言",
    17: "C# Mono",
    9: "Node.js LTS",
}
_LUOGU_DROPDOWN_LANG_BY_ID = {lid: name for lid, name in LUOGU_LANG_OPTIONS}


def _luogu_dropdown_lang_name(lang_id):
    """Map a Luogu language id to the label used in Luogu's in-page dropdown."""
    try:
        lid = int(lang_id)
    except (TypeError, ValueError):
        return "自动识别语言"
    if lid in _LUOGU_DROPDOWN_LANG_ALIAS:
        return _LUOGU_DROPDOWN_LANG_ALIAS[lid]
    return _LUOGU_DROPDOWN_LANG_BY_ID.get(lid, "自动识别语言")


def _inject_embedded_cookies(win, pairs):
    """Inject the user's Luogu cookies into the embedded window's WebView2 profile.

    WebView2 COM objects (CoreWebView2 / CookieManager) are STA thread-affine,
    so all access is marshaled onto the WinForms UI thread via Invoke. Returns
    True when the native CookieManager path succeeded (the real page can then
    load already logged-in), False otherwise (the caller should fall back to
    setting document.cookie after the page loads).
    """
    if not pairs:
        return True
    try:
        native = win.native
        if native is None:
            return False
        from System import Action
        state = {"control": None, "ready": False, "ok": False}

        def _invoke(fn):
            if native.InvokeRequired:
                native.Invoke(Action(fn))
            else:
                fn()

        def _find():
            # Run on the UI thread: locate the WebView2 control. Do NOT block
            # the message loop here waiting for CoreWebView2 — that would stall
            # the async initialization completion forever.
            try:
                control = None
                for c in native.Controls:
                    if type(c).__name__ == "WebView2":
                        control = c
                        break
                state["control"] = control
            except Exception:
                state["control"] = None

        def _ensure():
            # Kick off async CoreWebView2 initialization if not already done.
            # Returns immediately; completion runs on the UI message loop.
            try:
                c = state.get("control")
                if c is not None and c.CoreWebView2 is None:
                    c.EnsureCoreWebView2Async(None)
            except Exception:
                pass

        def _check_ready():
            try:
                c = state.get("control")
                state["ready"] = c is not None and c.CoreWebView2 is not None
            except Exception:
                state["ready"] = False

        def _inject():
            try:
                c = state.get("control")
                if c is None or c.CoreWebView2 is None:
                    return
                cm = c.CoreWebView2.CookieManager
                for name, value in pairs:
                    try:
                        cookie = cm.CreateCookie(name, value, "www.luogu.com.cn", "/")
                        cm.AddOrUpdateCookie(cookie)
                    except Exception:
                        pass
                state["ok"] = True
            except Exception:
                state["ok"] = False

        _invoke(_find)
        if state.get("control") is None:
            return False
        _invoke(_ensure)

        # Poll for readiness from the WORKER thread (time.sleep here is fine);
        # only the quick is-ready check is marshaled to the UI thread each pass.
        deadline = time.time() + 10
        while time.time() < deadline:
            _invoke(_check_ready)
            if state["ready"]:
                break
            time.sleep(0.05)
        if not state["ready"]:
            return False

        _invoke(_inject)
        return state["ok"]
    except Exception:
        return False


class EmbeddedSubmitApi:
    """JS API of the embedded Luogu submit window.

    The injected fetch/XHR interceptor calls on_embedded_submit_rid(rid) when
    Luogu returns a submission id. The rid is stored, the embedded window is
    closed and the main window is notified so evaluation polling can start.
    """

    def __init__(self, main_window):
        self._main = main_window
        self._win = None
        self._rid = None

    @property
    def rid(self):
        """The captured submission id, or None if no submit was captured."""
        return self._rid

    def set_window(self, win):
        """Store the embedded pywebview window reference for later destroy."""
        self._win = win

    def on_embedded_submit_rid(self, rid):
        """Called by the embedded page when a submit response rid is captured."""
        try:
            self._rid = int(rid)
            if self._win is not None:
                try:
                    self._win.destroy()
                except Exception:
                    pass
            if self._main is not None:
                self._main.evaluate_js("window.__onEmbeddedSubmit(%d)" % self._rid)
        except Exception:
            pass


def _filter_problem_list(problems, difficulty="", type_filter="", tag=""):
    """Apply difficulty / type / tag filters to a problem list.

    Used by the problem browser's paginated list. Difficulty is a comma
    separated list of ints, type_filter a comma separated list of pid
    prefixes (P/CF/AT/...), tag a substring match against the tag names.
    """
    filtered = list(problems)
    if difficulty:
        diff_set = set()
        for d in str(difficulty).split(","):
            try:
                diff_set.add(int(d))
            except ValueError:
                pass
        if diff_set:
            filtered = [p for p in filtered if p.get("difficulty") in diff_set]

    if type_filter:
        type_set = set(t.strip().upper() for t in str(type_filter).split(",") if t.strip())
        if type_set:
            filtered = [p for p in filtered
                        if any(p.get("pid", "").upper().startswith(t) for t in type_set)]

    if tag:
        filtered = [p for p in filtered if str(tag).lower() in str(p.get("tags", [])).lower()]

    return filtered


# ---------------------------------------------------------------------------
# AtCoder data layer (via kenkoooo.com AtCoder Problems API)
# ---------------------------------------------------------------------------

KENKOOO_BASE = "https://kenkoooo.com/atcoder/resources"
ATCODER_BASE = "https://atcoder.jp"


def fetch_atcoder_problems():
    """Fetch and cache the full AtCoder problem list from kenkoooo.com."""
    cached = _cache_get("atcoder_problems", ttl_seconds=3600)
    if cached is not None:
        return cached

    url = f"{KENKOOO_BASE}/problems.json"
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error("Failed to fetch atcoder problems: %s", e)
        raise RuntimeError("AtCoder 题库拉取失败，请稍后重试")

    problems = []
    for entry in data or []:
        if not isinstance(entry, dict):
            continue
        pid = entry.get("id", "") or ""
        if not pid:
            continue
        problems.append({
            "id": pid,
            "contest_id": entry.get("contest_id", ""),
            "problem_index": entry.get("problem_index", ""),
            "title": entry.get("title") or entry.get("name") or "",
        })

    # Only cache non-empty results: an empty list cached by an earlier
    # (buggy) fetch would otherwise mask the real data for the whole TTL.
    if problems:
        _cache_set("atcoder_problems", problems)
    return problems


def fetch_atcoder_difficulties():
    """Fetch and cache the AtCoder problem difficulty model map."""
    cached = _cache_get("atcoder_difficulties", ttl_seconds=3600)
    if cached is not None:
        return cached

    url = f"{KENKOOO_BASE}/problem-models.json"
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error("Failed to fetch atcoder difficulties: %s", e)
        raise RuntimeError("AtCoder 难度数据拉取失败，请稍后重试")

    # Only cache non-empty results (see fetch_atcoder_problems).
    if data:
        _cache_set("atcoder_difficulties", data)
    return data


def fetch_atcoder_contests():
    """Fetch and cache the AtCoder contest list from kenkoooo.com."""
    cached = _cache_get("atcoder_contests", ttl_seconds=3600)
    if cached is not None:
        return cached

    url = f"{KENKOOO_BASE}/contests.json"
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error("Failed to fetch atcoder contests: %s", e)
        raise RuntimeError("AtCoder 比赛数据拉取失败，请稍后重试")

    contests = []
    for entry in data or []:
        if not isinstance(entry, dict):
            continue
        # contests.json uses "id" for the contest id (not "contest_id")
        cid = entry.get("id", "") or entry.get("contest_id", "") or ""
        if not cid:
            continue
        contests.append({
            "contest_id": cid,
            "start_epoch_second": entry.get("start_epoch_second", 0),
            "title": entry.get("title", ""),
        })

    # Only cache non-empty results (see fetch_atcoder_problems).
    if contests:
        _cache_set("atcoder_contests", contests)
    return contests


def search_atcoder(keyword, limit=50, page=1, page_size=20):
    """Search AtCoder problems by keyword.

    Empty keyword: the full AtCoder problem bank sorted by problem id in
    lexicographic order (case-insensitive), then paginated by (page,
    page_size) — mirrors Luogu's default list.
    Non-empty keyword: matches against title (substring) or problem id
    (exact or prefix, ignoring a leading "AT_"); capped by `limit`.
    """
    keyword = (keyword or "").strip()
    page = max(1, int(page) if page else 1)
    page_size = max(1, int(page_size) if page_size else 20)
    problems = fetch_atcoder_problems()
    difficulties = fetch_atcoder_difficulties()

    if not keyword:
        # Full bank, ordered by id (dictionary order, like Luogu).
        matched = sorted(problems, key=lambda p: (str(p["id"]).lower(), str(p["id"])))
    else:
        kw_lower = keyword.lower()
        id_query = kw_lower[3:] if kw_lower.startswith("at_") else kw_lower
        matched = []
        for p in problems:
            title = (p["title"] or "").lower()
            pid_lower = p["id"].lower()
            if kw_lower in title:
                matched.append(p)
                continue
            if id_query and (pid_lower == id_query or pid_lower.startswith(id_query)):
                matched.append(p)
        matched = matched[:limit]

    # Dedupe by id (kenkoooo payload may contain duplicate entries)
    seen = set()
    unique = []
    for p in matched:
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        unique.append(p)
    matched = unique

    total = len(matched)
    total_pages = max(1, -(-total // page_size))
    start = (page - 1) * page_size
    page_items = matched[start:start + page_size]

    results = []
    for p in page_items:
        diff = difficulties.get(p["id"], {}).get("difficulty")
        results.append({
            "id": p["id"],
            "contest_id": p["contest_id"],
            "problem_index": p["problem_index"],
            "title": p["title"],
            "difficulty": diff,
        })

    return {
        "count": total,
        "problems": results,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def atcoder_luogu_pid(pid):
    """Convert an internal AtCoder pid to the pid Luogu actually hosts.

    Luogu hosts AtCoder problems under a MIXED convention: older contests
    use numeric task indices (AT_abc001_1) while newer ones use letter
    indices (AT_abc138_a). This helper therefore only guarantees the 'AT_'
    prefix (so fetch_solutions routes to the AtCoder editorial page); the
    exact task suffix is preserved and any Luogu 404 is handled by the
    AtCoder task-page fallback:
        AT_abc001_a  ->  AT_abc001_1      (letter -> numeric, old convention)
        abc001_a     ->  AT_abc001_1      (raw AtCoder id without the prefix)
        abc001_1     ->  AT_abc001_1      (already-numeric raw id)
        dp_t         ->  AT_dp_20
        1202Contest_a -> AT_1202Contest_1 (contest name may start with digits)
        AT_abc138_a  ->  AT_abc138_1
    A contest_letter pid (with or without the 'AT_' prefix) is rewritten;
    an already-numeric raw AtCoder id (e.g. "abc001_1" from kenkoooo.com)
    is also recognised and gets the AT_ prefix; anything else (Luogu pids,
    etc.) passes through unchanged.
    """
    pid = (pid or "").strip()
    # AT_xxx_letter  ->  AT_xxx_number  (e.g. AT_abc001_a -> AT_abc001_1)
    m = re.match(r"^(AT_[A-Za-z0-9]+)_([a-z])$", pid, re.IGNORECASE)
    if m:
        num = ord(m.group(2).lower()) - ord("a") + 1
        return f"{m.group(1)}_{num}"
    # Raw AtCoder task id without the 'AT_' prefix (e.g. "abc001_a",
    # "abc001_1", "dp_t", "1202Contest_a"). The contest part must contain at
    # least one letter (Luogu pids never contain '_' so they never match);
    # the suffix can be a letter (convert to number) or already a number.
    m = re.match(r"^(?=[a-z0-9]*[a-z])[a-z0-9]+_([a-z0-9]+)$", pid, re.IGNORECASE)
    if m:
        task = m.group(1).lower()
        if task.isalpha() and len(task) == 1:
            num = ord(task) - ord("a") + 1
        else:
            num = task  # already numeric, use as-is
        return f"AT_{pid.rsplit('_', 1)[0]}_{num}"
    return pid


_ATCODER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
}


class _AtCoderTaskParser(HTMLParser):
    """Parse an AtCoder task page into named markdown sections.

    AtCoder serves every task page with a <span class="lang"> wrapper that
    holds sibling <span class="lang-ja"> and <span class="lang-en"> copies
    of the statement. The English copy is preferred (Japanese is used as a
    fallback for Japanese-only problems). Within the chosen block the
    statement is a sequence of <div class="part"><section><h3>heading</h3>
    content</section></div> groups. Math lives in <var> tags and becomes
    inline $...$ for KaTeX; <code>/<pre> become code.
    """

    SECTION_MAP = {
        "problem statement": "description", "問題文": "description",
        "constraints": "constraints", "制約": "constraints",
        "input": "input", "入力": "input",
        "output": "output", "出力": "output",
        "note": "note", "注記": "note",
        "scoring": "scoring", "配点": "scoring",
    }

    def __init__(self, lang="en"):
        super().__init__(convert_charrefs=True)
        self._lang = "ja" if lang != "en" else "en"
        self._target = None          # "en"/"ja" once the lang block is entered
        self._target_depth = 0
        self._cur_id = None          # canonical id of the section being built
        self._sections = {}          # canonical id -> text
        self._buf = []               # inline text buffer for the current section
        self._in_h3 = False
        self._h3_buf = []
        self._in_pre = False
        self._pre_buf = []
        self._sample_buf = []        # pre contents of the current sample section
        self._sample_in = {}         # sample # -> input text
        self._sample_out = {}        # sample # -> output text
        self._cur_sample = 0

    def _append(self, text):
        (self._pre_buf if self._in_pre else self._buf).append(text)

    def _classify_heading(self, raw):
        h = re.sub(r"\s+", " ", (raw or "").strip().lower())
        m = re.match(r"^(sample\s*input|入力例)\s+(\d+)$", h)
        if m:
            self._cur_sample = int(m.group(2))
            return "sample_in"
        m = re.match(r"^(sample\s*output|出力例)\s+(\d+)$", h)
        if m:
            return "sample_out"
        return self.SECTION_MAP.get(h, "")

    def _flush(self):
        cur_id = self._cur_id
        if not cur_id:
            self._buf = []
            self._sample_buf = []
            return
        if cur_id in ("sample_in", "sample_out"):
            text = "\n".join(self._sample_buf).strip()
            self._sample_buf = []
            self._buf = []
            if text:
                if cur_id == "sample_in":
                    self._sample_in[self._cur_sample] = text
                else:
                    self._sample_out[self._cur_sample] = text
            return
        text = re.sub(r"[ \t]+\n", "\n", "".join(self._buf))
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        self._buf = []
        self._sample_buf = []
        if text:
            self._sections[cur_id] = self._sections.get(cur_id, "") + text

    # --- HTMLParser callbacks ---
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        classes = set((d.get("class") or "").split())
        if tag == "span" and self._target is None:
            if "lang-en" in classes and self._lang == "en":
                self._target = "en"
                self._target_depth = 1
            elif "lang-ja" in classes and self._lang == "ja":
                self._target = "ja"
                self._target_depth = 1
            return
        if not self._target or self._target_depth == 0:
            return
        if tag == "span":
            self._target_depth += 1
            return
        if tag == "h3":
            self._flush()
            self._in_h3 = True
            self._h3_buf = []
            return
        if tag == "pre":
            self._in_pre = True
            self._pre_buf = []
            return
        if tag == "var":
            self._append("$")
            return
        if tag == "code":
            self._append("`")
            return
        if tag == "li":
            self._append("\n- ")
            return
        if tag == "br":
            self._append("\n")
            return

    def handle_endtag(self, tag):
        if not self._target or self._target_depth == 0:
            return
        if tag == "h3":
            self._in_h3 = False
            heading = "".join(self._h3_buf)
            self._h3_buf = []
            self._cur_id = self._classify_heading(heading)
            return
        if tag == "pre":
            self._in_pre = False
            code = "".join(self._pre_buf).strip("\n")
            self._pre_buf = []
            if self._cur_id in ("sample_in", "sample_out"):
                self._sample_buf.append(code)
            else:
                self._buf.append("\n```\n" + code + "\n```\n")
            return
        if tag == "var":
            self._append("$")
            return
        if tag == "code":
            self._append("`")
            return
        if tag == "span":
            self._target_depth -= 1
            if self._target_depth == 0:
                self._flush()
            return
        if tag in ("p", "div", "section", "ul", "ol", "li"):
            self._append("\n")

    def handle_data(self, data):
        if self._in_h3:
            self._h3_buf.append(data)
            return
        if not self._target or self._target_depth == 0:
            return
        if self._in_pre:
            self._pre_buf.append(data)
        else:
            self._buf.append(data)


def _extract_atcoder_title(html, raw_pid):
    """Extract the problem title from the AtCoder task page header."""
    m = re.search(r'<span class="h2">(.*?)</span>', html, re.S)
    if m:
        title = re.sub(r"<[^>]+>", "", m.group(1))
        title = re.sub(r"\s+", " ", title).strip()
        if title:
            return title
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    if m and m.group(1).strip():
        return m.group(1).strip()
    return raw_pid


def _parse_atcoder_limits(html):
    """Parse the time/memory limits from the AtCoder task page meta line.
    Returns (time_ms list, memory_kb list) matching fetch_problem()'s shape."""
    time_ms = []
    mem_kb = []
    m = re.search(r"Time Limit:\s*([0-9.]+)\s*sec", html, re.IGNORECASE)
    if m:
        time_ms.append(int(round(float(m.group(1)) * 1000)))
    m = re.search(r"Memory Limit:\s*([0-9.]+)\s*MiB", html, re.IGNORECASE)
    if m:
        mem_kb.append(int(round(float(m.group(1)) * 1024)))
    return time_ms, mem_kb


def _parse_atcoder_task(html, raw_pid):
    """Parse an AtCoder task page into a fetch_problem()-shaped dict."""
    parser = _AtCoderTaskParser(lang="en")
    try:
        parser.feed(html)
    except Exception:
        logger.exception("Failed to parse AtCoder task page for %s", raw_pid)
    parser.close()

    # Japanese-only problems carry no lang-en block; retry with the
    # Japanese copy of the statement as a fallback.
    if not parser._sections and not parser._sample_in and not parser._sample_out:
        parser = _AtCoderTaskParser(lang="ja")
        try:
            parser.feed(html)
        except Exception:
            logger.exception("Failed to parse AtCoder task page for %s", raw_pid)
        parser.close()

    sections = parser._sections
    description = sections.get("description", "")
    for key, head_en, head_ja in (
        ("constraints", "Constraints", "制約"),
        ("scoring", "Score", "配点"),
    ):
        if sections.get(key):
            head = head_en if parser._lang == "en" else head_ja
            description = (description + "\n\n**" + head + "**\n\n"
                           + sections[key]).strip()

    sample_nums = set(parser._sample_in) | set(parser._sample_out)
    samples = []
    for i in range(1, max(sample_nums, default=0) + 1):
        if i in sample_nums:
            samples.append({
                "in": parser._sample_in.get(i, ""),
                "out": parser._sample_out.get(i, ""),
            })

    time_ms, mem_kb = _parse_atcoder_limits(html)

    return {
        "pid": "AT_" + raw_pid,
        "title": _extract_atcoder_title(html, raw_pid),
        "difficulty": 0,
        "tags": [],
        "background": "",
        "description": description,
        "inputFormat": sections.get("input", ""),
        "outputFormat": sections.get("output", ""),
        "samples": samples,
        "hint": sections.get("note", ""),
        "timeLimit": time_ms,
        "memoryLimit": mem_kb,
        "totalSubmit": 0,
        "totalAccepted": 0,
        "source": "AtCoder",
        "recommendations": [],
    }


def _atcoder_problem_id_map():
    """Map raw AtCoder task ids to their contest ids (best effort)."""
    try:
        return {p["id"]: p.get("contest_id") or "" for p in fetch_atcoder_problems()}
    except Exception:
        logger.debug("Failed to look up AtCoder contest ids")
        return {}


def _normalize_atcoder_task_id(pid, id_map):
    """Return the raw AtCoder task id for a Luogu-style or raw pid.

    - Strips a leading "AT_" (a Luogu convention, not used on atcoder.jp).
    - Converts a Luogu numeric task index back to its letter form
      (awc0135_2 -> awc0135_b, AT_abc138_1 -> abc138_a) when the numeric
      form is not itself a known task id (a few contests genuinely use
      numeric ids, e.g. atc001_1).
    """
    pid = (pid or "").strip()
    if pid.upper().startswith("AT_"):
        pid = pid[3:]
    if pid in id_map:
        return pid
    m = re.match(r"^([a-z0-9]+)_(\d+)$", pid, re.IGNORECASE)
    if m:
        num = int(m.group(2))
        if 1 <= num <= 26:
            alt = f"{m.group(1)}_{chr(ord('a') + num - 1)}"
            if alt in id_map:
                return alt
    return pid


def _fetch_atcoder_task(raw_pid):
    """Fetch and parse an AtCoder task page directly from atcoder.jp.

    This is the fallback used when Luogu does not host the problem. Returns a
    dict in the same shape as fetch_problem().
    """
    id_map = _atcoder_problem_id_map()
    task_id = _normalize_atcoder_task_id(raw_pid, id_map)
    contest_id = id_map.get(task_id) or (task_id.rsplit("_", 1)[0] if "_" in task_id else task_id)
    url = (f"{ATCODER_BASE}/contests/{urllib.parse.quote(contest_id)}"
           f"/tasks/{urllib.parse.quote(task_id)}")
    try:
        resp = requests.get(url, timeout=20, headers=_ATCODER_HEADERS)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("Failed to fetch AtCoder task %s: %s", raw_pid, e)
        raise RuntimeError(f"无法从 AtCoder 获取题目信息: {e}")
    return _parse_atcoder_task(resp.text, task_id)


def _is_luogu_not_found(msg):
    """True when a fetch_problem() error means the problem is simply missing
    on Luogu (not a network/anti-bot issue), so the AtCoder fallback applies."""
    msg = msg or ""
    return "404" in msg or "题目不存在" in msg


def _resolve_atcoder_link(href):
    """Resolve an AtCoder editorial link, decoding /jump?url= redirects and
    converting relative paths to absolute atcoder.jp URLs."""
    href = (href or "").strip()
    if href.startswith("/jump?url="):
        try:
            return urllib.parse.unquote(href.split("?url=", 1)[1])
        except Exception:
            return href
    if href.startswith("//"):
        return f"https:{href}"
    if href.startswith("/"):
        return f"{ATCODER_BASE}{href}"
    return href


def _parse_atcoder_editorials(html):
    """Parse an AtCoder editorial page into a list of solution entries.

    AtCoder editorial pages group links in <div class="editorial-section">
    blocks: the first block belongs to the current task (official PDF/YouTube
    editorials plus user blog editorials), the following block is the
    whole-contest editorial. Each entry is an <a href> with an optional
    "公式" (official) label and a "by <author>" attribution. The editorial
    *content* lives on external sites (PDFs / blogs), so each solution entry
    carries the link as a markdown anchor for the frontend to open.
    """
    entries = []
    for m in re.finditer(
            r"<div class=\"editorial-section\">(.*?)</div>",
            html, re.DOTALL):
        block = m.group(1)
        for li in re.findall(r"<li[^>]*>(.*?)</li>", block, re.DOTALL):
            is_official = ("公式" in li or "Official" in li or "official" in li)
            by = ""
            by_m = re.search(r"<span class=\"grey\">by</span>(.*)", li, re.DOTALL)
            if by_m:
                by = re.sub(r"<[^>]+>", "", by_m.group(1)).strip()
            link_m = re.search(r"<a href=\"([^\"]+)\"[^>]*>(.*?)</a>", li, re.DOTALL)
            if not link_m:
                continue
            href = _resolve_atcoder_link(link_m.group(1))
            label = re.sub(r"<[^>]+>", "", link_m.group(2)).strip()
            if not label:
                label = "官方题解" if is_official else "用户题解"
            entries.append({
                "official": is_official,
                "href": href,
                "label": label,
                "author": by or ("AtCoder 官方" if is_official else "AtCoder 用户"),
            })
    return entries


def _fetch_atcoder_editorials(raw_pid):
    """Fetch official/user editorial links for an AtCoder task from atcoder.jp.

    Luogu never hosts solution pages for AtCoder problems, so this is the
    primary (and only) solution source for them. Returns a dict in the same
    shape as a Luogu solutions payload so filter_solutions() can process it.
    """
    id_map = _atcoder_problem_id_map()
    task_id = _normalize_atcoder_task_id(raw_pid, id_map)
    contest_id = (id_map.get(task_id) or (task_id.rsplit("_", 1)[0]
                                          if "_" in task_id else task_id))
    url = (f"{ATCODER_BASE}/contests/{urllib.parse.quote(contest_id)}"
           f"/tasks/{urllib.parse.quote(task_id)}/editorial")
    try:
        resp = requests.get(url, timeout=20, headers=_ATCODER_HEADERS)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("Failed to fetch AtCoder editorial for %s: %s", raw_pid, e)
        raise RuntimeError(f"无法从 AtCoder 获取题解: {e}")

    entries = _parse_atcoder_editorials(resp.text)
    if not entries:
        raise RuntimeError("AtCoder 暂无该题的官方或用户题解")

    result = []
    for i, entry in enumerate(entries, 1):
        tag = "**官方题解**" if entry["official"] else "**用户题解**"
        content = (f"{tag}：{entry['label']}\n\n"
                   f"作者：{entry['author']}\n\n"
                   f"[点击查看题解 →]({entry['href']})")
        result.append({
            "id": f"atcoder-{i}",
            "author": {"name": entry["author"]},
            "content": content,
            "rating": 0,
            "source": "AtCoder",
        })
    return {"result": result, "count": len(result)}


def fetch_atcoder_problem(pid, cookie=""):
    """Fetch an AtCoder problem.

    Luogu hosts AtCoder problems under numeric task indices
    (AT_abc001_a -> AT_abc001_1). When Luogu does not host the problem (e.g.
    a niche contest such as awc0135), the official AtCoder task page is
    fetched and parsed as a fallback so the problem can still be opened.
    """
    pid = (pid or "").strip()
    if not pid:
        raise RuntimeError("题号不能为空")
    cache_key = f"atcoder_problem_{pid}"
    cached = _cache_get(cache_key, ttl_seconds=3600)
    if cached is not None:
        return cached
    if pid.upper().startswith("AT_"):
        luogu_pid = pid
    else:
        luogu_pid = "AT_" + pid
    try:
        result = fetch_problem(atcoder_luogu_pid(luogu_pid), cookie)
    except RuntimeError as e:
        if not _is_luogu_not_found(str(e)):
            raise
        logger.info("Luogu does not host %s, falling back to AtCoder", pid)
        result = _fetch_atcoder_task(pid)
    _cache_set(cache_key, result)
    return result


class Api:
    """JS-callable API. Methods are invoked via window.pywebview.api.<method>.

    Each method returns a dict with a "success" key (True/False). On error,
    "error" contains the message. This mirrors the old Flask JSON responses
    so the frontend only needs minimal changes to the transport layer.
    """

    def __init__(self):
        # Keep the requests.Session that fetched the captcha alive so that
        # submit_code() can reuse the EXACT same session. Luogu ties captcha
        # validation to the server-side session state; rebuilding a session
        # from serialized cookies is unreliable and causes every submit to
        # fail with "验证码错误".
        #
        # Sessions are keyed by a captcha id so that concurrent get_captcha()
        # calls (e.g. a double-click on the submit button) can never swap the
        # session under a pending captcha: each captcha image is paired with
        # its own session, and the frontend sends back the id on submit.
        self._captcha_session = None
        self._captcha_sessions = {}  # captcha_id -> requests.Session
        self._captcha_lock = threading.Lock()
        # Reference to the embedded Luogu submit window (opened for the
        # interactive captcha flow). None when no embedded window is open.
        self._embedded_win = None
        # Reference to the pywebview window, used to push streaming AI chunks
        # to the frontend. Assigned in main() after create_window().
        self._window = None

    def _emit(self, js):
        """Evaluate JS on the GUI window (best-effort, from any thread).

        Used to stream AI assistant tokens to the frontend in real time.
        """
        if self._window is None:
            return
        try:
            self._window.evaluate_js(js)
        except Exception:
            # Streaming is best-effort; ignore transient push failures.
            pass

    def _ai_provider_key(self, model):
        """Return (api_key, provider) for the given model, falling back to the
        saved key for the matching provider."""
        model = (model or "deepseek-chat").strip() or "deepseek-chat"
        cfg = load_config()
        if is_glm_model(model):
            return ((cfg.get("glm_api_key") or "").strip(), "GLM")
        return ((cfg.get("api_key") or "").strip(), "DeepSeek")

    # --- Config ---
    def get_config(self):
        cfg = load_config()
        return {
            "success": True,
            "api_key": cfg.get("api_key", ""),
            "glm_api_key": cfg.get("glm_api_key", ""),
            "model": cfg.get("model", ""),
            "cookie": cfg.get("cookie", ""),
            "vjudge_cookie": cfg.get("vjudge_cookie", ""),
            "vjudge_username": cfg.get("vjudge_username", ""),
            "vjudge_has_password": bool(cfg.get("vjudge_password")),
        }

    # --- Disclaimer ---
    def get_disclaimer(self):
        """Return the full disclaimer text shown on the app's first launch."""
        try:
            return {"success": True, "content": _load_disclaimer()}
        except Exception as e:
            logger.exception("Unexpected error loading disclaimer")
            return {"success": False, "error": f"加载免责声明失败: {e}"}

    def clear_cache(self):
        """Clear all cached data."""
        _cache_clear()
        return {"success": True, "message": "Cache cleared"}

    # --- Problem ---
    def get_problem(self, problem_id):
        try:
            problem = fetch_problem(problem_id, load_config().get("cookie", ""))
            return {"success": True, "problem": problem}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching problem")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Search ---
    def search(self, q):
        keyword = (q or "").strip()
        try:
            result = search_problems(keyword)
            return {
                "success": True,
                "count": result["count"],
                "problems": result["problems"],
            }
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error searching problems")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- AtCoder ---
    def atcoder_search(self, q, page=1):
        keyword = (q or "").strip()
        try:
            result = search_atcoder(keyword, page=page)
            return {
                "success": True,
                "count": result["count"],
                "problems": result["problems"],
                "page": result.get("page", 1),
                "total_pages": result.get("total_pages", 1),
            }
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error searching atcoder problems")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def get_atcoder_problem(self, pid):
        try:
            problem = fetch_atcoder_problem(pid, load_config().get("cookie", ""))
            return {"success": True, "problem": problem}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching atcoder problem")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Default problem list ---
    def get_default_problems(self, page=1):
        try:
            page = int(page) if page else 1
            if page < 1:
                page = 1
            result = fetch_default_problems(page=page)
            return {
                "success": True,
                "count": result["count"],
                "problems": result["problems"],
                "page": page,
            }
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching default problems")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Problem browser page with filters ---
    def get_problems_page(self, keyword="", difficulty="", type_filter="", tag="", page=1, page_size=20):
        """Get a paginated, filtered problem list (Luogu-style page navigation).

        Args:
            keyword: search keyword (empty = default list)
            difficulty: comma-separated difficulty values (e.g. "1,2,3")
            type_filter: comma-separated type prefixes (e.g. "P,CF,AT")
            tag: tag name filter
            page: page number (1-indexed)
            page_size: results per page
        """
        try:
            page = max(1, int(page or 1))
            page_size = max(1, int(page_size or 20))
            if keyword:
                # Search collects up to 50 strict matches in one call; the
                # returned list is paginated here.
                result = search_problems(keyword, 1)
                problems = result.get("problems", [])
                total = len(problems)
                filtered = _filter_problem_list(problems, difficulty, type_filter, tag)
                start = (page - 1) * page_size
                paged = filtered[start:start + page_size]
            else:
                # Default list: Luogu serves ~50 problems per page. Map the
                # requested window onto the matching Luogu page(s), fetching the
                # next Luogu page too when the window crosses a boundary.
                PER = 50
                start = (page - 1) * page_size
                luogu_page = start // PER + 1
                offset = start % PER
                result = fetch_default_problems(luogu_page)
                problems = list(result.get("problems", []))
                total = result.get("count", result.get("total", 0))
                if offset + page_size > len(problems):
                    next_result = fetch_default_problems(luogu_page + 1)
                    problems.extend(next_result.get("problems", []))
                filtered = _filter_problem_list(problems, difficulty, type_filter, tag)
                paged = filtered[offset:offset + page_size]

            total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
            return {
                "success": True,
                "problems": paged,
                "total": total,
                "page": page,
                "pageSize": page_size,
                "totalPages": total_pages,
                "filteredCount": len(filtered),
            }
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    # --- User practice (submission status) ---
    def get_practice(self, cookie=""):
        cookie = cookie or ""
        try:
            result = fetch_user_practice(cookie)
            return {
                "success": True,
                "passed": list(result["passed"]),
                "submitted": list(result["submitted"]),
            }
        except Exception as e:
            logger.exception("Unexpected error fetching practice")
            return {"success": False, "error": str(e), "passed": [], "submitted": []}

    # --- Solutions ---
    def get_solutions(self, problem_id, cookie=""):
        try:
            solutions_data = fetch_solutions(problem_id, cookie=cookie)
            total = solutions_data.get("count", 0)
            filtered = filter_solutions(solutions_data, top_n=5)
            return {
                "success": True,
                "total_solutions": total,
                "solutions": filtered,
            }
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching solutions")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Analyze ---
    def analyze(self, api_key, model, problem, solutions):
        """Run AI analysis. `api_key` is the key for the selected model's
        provider (DeepSeek or GLM). The caller is responsible for passing the
        correct key; we also fall back to the saved key for that provider.
        """
        model = (model or "deepseek-chat").strip() or "deepseek-chat"
        glm = is_glm_model(model)
        provider = "GLM" if glm else "DeepSeek"

        # Use the passed key, or fall back to the saved key for this provider
        cfg = load_config()
        if glm:
            api_key = (api_key or "").strip() or cfg.get("glm_api_key", "")
        else:
            api_key = (api_key or "").strip() or cfg.get("api_key", "")

        if not api_key:
            return {"success": False, "error": f"缺少 {provider} API Key"}
        if not problem:
            return {"success": False, "error": "缺少题目信息"}
        try:
            analysis = analyze_with_deepseek(problem, solutions or [], api_key, model)
            # Persist the selected model so it's restored on next launch
            save_config(model=model)
            return {"success": True, "analysis": analysis, "model": model}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error during analysis")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def assistant_chat(self, history, problem, thinking=False):
        """Stream an assistant reply. history is [{role, content}]; problem is
        the currently open problem (optional) for context.

        Runs in a background thread, pushing each token to the frontend via
        evaluate_js(window.__aiStream(...)). Returns after the stream ends.
        """
        model = (load_config().get("model") or "deepseek-chat").strip() or "deepseek-chat"
        api_key, provider = self._ai_provider_key(model)
        if not api_key:
            return {"success": False, "error": f"缺少 {provider} API Key，请先在设置中配置"}

        messages = build_assistant_messages(history or [], problem or {})
        import json as _json

        def on_delta(kind, text):
            self._emit(
                "window.__aiStream && window.__aiStream("
                + _json.dumps(kind, ensure_ascii=False) + ","
                + _json.dumps(text, ensure_ascii=False) + ");"
            )

        try:
            stream_ai_chat(messages, api_key, model, on_delta, thinking=bool(thinking))
            self._emit("window.__aiStream && window.__aiStream('done', '');")
            return {"success": True, "done": True}
        except RuntimeError as e:
            self._emit(
                "window.__aiStream && window.__aiStream('error', "
                + _json.dumps(str(e), ensure_ascii=False) + ");"
            )
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error in assistant chat")
            self._emit(
                "window.__aiStream && window.__aiStream('error', "
                + _json.dumps(f"服务器内部错误: {e}", ensure_ascii=False) + ");"
            )
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Validate API key ---
    def validate_apikey(self, api_key, model):
        """Validate an API key against the provider matching `model`.

        DeepSeek models use the DeepSeek endpoint; GLM models use the GLM
        endpoint. The key is persisted to the field matching the provider
        (api_key for DeepSeek, glm_api_key for GLM).

        Note (GLM / 智谱): a request can fail with a billing/quota error
        even though the key itself is valid — the user may hold a resource
        package (按 tokens 计量的资源包) that does not appear on the cash
        account, or may simply have exhausted quota. Such errors mean
        authentication succeeded, so the key is still accepted and saved;
        only auth errors (401 / codes 1000, 1001, 1003, 1005) are treated
        as an invalid key.
        """
        api_key = (api_key or "").strip()
        model = (model or "deepseek-chat").strip() or "deepseek-chat"
        glm = is_glm_model(model)
        provider = "GLM" if glm else "DeepSeek"
        api_url = GLM_API_URL if glm else DEEPSEEK_API_URL

        if not api_key:
            return {"success": False, "error": f"{provider} API Key 不能为空"}
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        test_body = {
            "model": model,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
            "stream": False,
        }
        try:
            resp = requests.post(api_url, headers=headers, json=test_body, timeout=30)
            if resp.status_code == 200:
                # Save only the key for this provider (not the model, so
                # validation doesn't override the user's selected model).
                if glm:
                    save_config(glm_api_key=api_key)
                else:
                    save_config(api_key=api_key)
                return {"success": True, "message": f"{provider} API Key 验证成功，已保存到服务器"}
            else:
                try:
                    err = resp.json().get("error", {})
                    err_code = str(err.get("code", ""))
                    err_msg = err.get("message", resp.text[:200])
                except Exception:
                    err_code = ""
                    err_msg = resp.text[:200]

                # GLM: billing/quota errors still prove the key is valid —
                # the user may have a token-based resource package that isn't
                # reflected in the cash balance. Save the key in that case so
                # validation doesn't fail just because the cash account is 0.
                if glm and (resp.status_code in (401, 403, 429)):
                    balance_hint = (
                        "余额" in err_msg
                        or "欠费" in err_msg
                        or "balance" in err_msg.lower()
                        or "quota" in err_msg.lower()
                        or err_code in {"1113", "1115", "1002"}
                    )
                    if balance_hint:
                        save_config(glm_api_key=api_key)
                        return {
                            "success": True,
                            "message": f"{provider} API Key 验证成功（账户余额/资源包可能不足，"
                            f"正式调用时请确保有可用余额或资源包）",
                        }
                return {"success": False, "error": f"验证失败 (HTTP {resp.status_code}): {err_msg}"}
        except requests.RequestException as e:
            return {"success": False, "error": f"网络错误: {e}"}

    # --- Validate cookie ---
    def validate_cookie(self, cookie):
        cookie = (cookie or "").strip()
        if not cookie:
            return {"success": False, "error": "Cookie 不能为空"}
        try:
            solutions_data = fetch_solutions("P1000", cookie=cookie)
            count = solutions_data.get("count", 0)
            save_config(cookie=cookie)
            return {"success": True, "message": f"Cookie 验证成功，获取到 {count} 篇题解，已保存到服务器"}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Vjudge cookie ---
    def validate_vjudge_cookie(self, vjudge_cookie):
        vjudge_cookie = (vjudge_cookie or "").strip()
        if not vjudge_cookie:
            return {"success": False, "error": "Vjudge Cookie 不能为空"}
        try:
            # Validate login state via the Vjudge homepage navbar. The old
            # approach probed /problem/Luogu-P1000 which returns HTTP 404 even
            # for valid cookies, causing false "invalid" results.
            session = _build_vjudge_session(vjudge_cookie)
            if _vjudge_session_is_authenticated(session):
                save_config(vjudge_cookie=vjudge_cookie)
                return {"success": True, "message": "Vjudge Cookie 验证成功，已保存到服务器"}
            return {"success": False, "error": VJUDGE_COOKIE_INVALID_MSG}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except requests.RequestException as e:
            return {"success": False, "error": f"无法连接 Vjudge 服务器: {e}"}
        except Exception as e:
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def submit_vjudge(self, pid, code, lang, vjudge_cookie, vjudge_username="", vjudge_password=""):
        problem_id = (pid or "").strip()
        code = code or ""
        lang_id = lang or 0
        vjudge_cookie = (vjudge_cookie or "").strip()
        username = (vjudge_username or "").strip()
        password = vjudge_password or ""

        if not problem_id:
            return {"success": False, "error": "缺少题号"}
        if not code.strip():
            return {"success": False, "error": "代码不能为空"}

        # Prefer explicit credentials, then fall back to stored config.
        if not username or not password:
            cfg = load_config()
            if not username:
                username = (cfg.get("vjudge_username") or "").strip()
            if not password:
                password = cfg.get("vjudge_password") or ""
        if not username and not password and not vjudge_cookie:
            return {"success": False, "error": "提交到 Vjudge 需要登录，请在设置中填写 Vjudge 用户名和密码（或 Cookie）"}

        try:
            url = submit_vjudge(problem_id, code, lang_id, vjudge_cookie, username, password)
            return {"success": True, "url": url}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error during Vjudge submission")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def save_vjudge_credentials(self, username, password):
        """Validate Vjudge credentials by logging in, then persist them.

        This is the stable authentication method: the JSESSlONID cookie is
        regenerated on every login, so storing the account credentials and
        auto-logging-in on each submission avoids manual cookie re-entry.
        """
        username = (username or "").strip()
        password = password or ""
        if not username or not password:
            return {"success": False, "error": "Vjudge 用户名和密码不能为空"}
        try:
            session = _vjudge_login(username, password)
            # Only persist after a successful login round-trip.
            save_config(vjudge_username=username, vjudge_password=password)
            return {"success": True, "message": "Vjudge 账号验证成功，已保存（提交时自动登录获取会话）"}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except requests.RequestException as e:
            return {"success": False, "error": f"无法连接 Vjudge 服务器: {e}"}
        except Exception as e:
            logger.exception("Unexpected error validating Vjudge credentials")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def clear_vjudge_credentials(self):
        """Clear the saved Vjudge account credentials (e.g. wrong password)."""
        try:
            save_config(vjudge_username="", vjudge_password="")
            return {"success": True, "message": "已清除保存的 Vjudge 账号信息"}
        except Exception as e:
            logger.exception("Error clearing Vjudge credentials")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Languages ---
    def get_languages(self):
        langs = [{"id": lid, "name": name} for lid, name in LUOGU_LANG_OPTIONS]
        return {"success": True, "languages": langs}

    # --- Local compile & run (Online IDE test panel) ---
    def compile_and_run(self, code, lang, stdin, enableO2):
        """Compile and run user code locally with the given stdin.

        `lang` is a Luogu language id (int or string). `enableO2` is truthy
        to enable -O2 for C/C++. Returns the compile_and_run_code() result.
        """
        return compile_and_run_code(code, lang, stdin, bool(enableO2))

    def run_local_cases(self, code, lang, cases, enableO2):
        """Run user code against multiple (input, expected) test cases."""
        try:
            lang_id = int(lang)
        except (TypeError, ValueError):
            return {"success": False, "error": "无效的语言选项"}
        if not isinstance(cases, list) or not cases:
            return {"success": False, "error": "请先添加至少一组测试用例"}
        try:
            result = run_local_cases(code, lang_id, cases, bool(enableO2))
            return result
        except Exception as e:
            logger.exception("run_local_cases failed")
            return {"success": False, "error": f"运行失败: {e}"}

    def run_duipai(self, code, lang, bruteCode, bruteLang, genCode, genLang,
                   iterations, enableO2):
        """对拍: compare user code against a brute-force program."""
        try:
            lang_id = int(lang)
            brute_lang = int(bruteLang or lang)
            gen_lang = int(genLang or lang)
        except (TypeError, ValueError):
            return {"success": False, "error": "无效的语言选项"}
        try:
            result = run_duipai(code, lang_id, bruteCode, brute_lang,
                                genCode, gen_lang, int(iterations or 20),
                                bool(enableO2))
            return result
        except Exception as e:
            logger.exception("run_duipai failed")
            return {"success": False, "error": f"对拍失败: {e}"}

    # --- Captcha ---
    # Deprecated: Luogu switched to an interactive click captcha; text captcha no longer validates.
    def get_captcha(self, pid, cookie, contest_id=""):
        problem_id = (pid or "").strip()
        cookie = (cookie or "").strip()
        contest_id = (contest_id or "").strip()
        if not problem_id:
            return {"success": False, "error": "缺少题号"}
        if not cookie:
            return {"success": False, "error": "提交代码需要洛谷 Cookie"}
        try:
            result, session = fetch_captcha(problem_id, cookie, contest_id)
            captcha_id = uuid.uuid4().hex
            # Keep the session alive for submit_code() to reuse. Keyed by id
            # so concurrent fetches can't swap the session under us.
            with self._captcha_lock:
                self._captcha_sessions[captcha_id] = session
            self._captcha_session = session
            return {
                "success": True,
                "captchaId": captcha_id,
                "image": result["image"],
                "sessionCookies": result["sessionCookies"],
                "csrfToken": result["csrfToken"],
            }
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching captcha")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Submit ---
    def submit(self, pid, code, lang, cookie, enableO2, verify, sessionCookies,
               csrfToken, contest_id="", captcha_id=""):
        problem_id = (pid or "").strip()
        code = code or ""
        lang_id = lang or 0
        cookie = (cookie or "").strip()
        enable_o2 = bool(enableO2)
        verify = (verify or "").strip()
        session_cookies = sessionCookies or ""
        csrf_token = csrfToken or ""
        contest_id = (contest_id or "").strip()
        captcha_id = (captcha_id or "").strip()

        if not problem_id:
            return {"success": False, "error": "缺少题号"}
        if not code.strip():
            return {"success": False, "error": "代码不能为空"}
        if not cookie:
            return {"success": False, "error": "提交代码需要洛谷 Cookie"}

        # Pick the session that belongs to THIS captcha. Each captcha fetch
        # stores its session under a unique id, so the session can never be
        # swapped by a concurrent get_captcha() call. Fall back to the last
        # session for legacy callers that send a captcha_id. A direct submit
        # (no captcha_id) intentionally passes session=None so submit_code()
        # builds a fresh session and fetches a fresh CSRF token.
        session = None
        if captcha_id:
            with self._captcha_lock:
                session = self._captcha_sessions.pop(captcha_id, None)
            if session is None:
                session = self._captcha_session
                self._captcha_session = None

        try:
            rid = submit_code(problem_id, code, lang_id, cookie, enable_o2, verify,
                              session_cookies, csrf_token, session=session,
                              contest_id=contest_id)
            # Submit succeeded — the captcha session is now consumed; clear it
            # so a stale session is never reused for the next submission.
            self._captcha_session = None
            return {"success": True, "rid": rid}
        except CaptchaRequiredError as e:
            # Luogu requires a (possibly interactive) captcha. The captcha
            # session is now invalid — clear it so the next attempt fetches a
            # fresh captcha + session. Signal the frontend with a dedicated
            # flag so it can show the manual browser submit guide instead of
            # the (now dead) text-captcha modal — never loop.
            self._captcha_session = None
            return {"success": False, "error": str(e), "captchaRequired": True,
                    "interactive": True}
        except RuntimeError as e:
            # If the error is captcha-related, the session is now invalid —
            # clear it so the next attempt fetches a fresh captcha + session.
            if "验证码" in str(e) or "过期" in str(e):
                self._captcha_session = None
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error during code submission")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Embedded (interactive captcha) submit window ---
    def open_luogu_submit_window(self, pid, contest_id="", cookie="", code="", lang="", enable_o2=None):
        """Open a second pywebview window for native (interactive) Luogu submit.

        Used when Luogu requires an interactive 易盾 (Yidun) click captcha that
        the app cannot solve programmatically. The embedded window loads the
        real Luogu problem submit page (#submit), is logged in with the user's
        cookie via the native WebView2 CookieManager, auto-fills the code,
        sets the language and O2 option, then clicks 提交评测 so the user is
        only left with solving the interactive captcha natively. An injected
        fetch/XHR interceptor captures the submission rid and notifies the
        main window so evaluation polling can start.
        """
        problem_id = (pid or "").strip()
        contest_id = (contest_id or "").strip()
        cookie = (cookie or "").strip()
        if not problem_id:
            return {"success": False, "error": "缺少题号"}
        if not cookie:
            return {"success": False, "error": "打开洛谷提交页需要登录 Cookie"}

        try:
            import webview
            import threading

            # Guard against opening a second embedded window while one is open.
            if self._embedded_win is not None:
                return {"success": False, "error": "内嵌提交窗口已打开"}

            # Submit page URL: /problem/{pid}[?contestId={cid}]#submit
            url = LUOGU_BASE + "/problem/" + urllib.parse.quote(problem_id)
            if contest_id:
                url += "?contestId=" + urllib.parse.quote(contest_id)
            url += "#submit"

            embedded_api = EmbeddedSubmitApi(self._window)
            # Create the window WITHOUT navigating (url=None). This lets us
            # inject the login cookies into the shared WebView2 profile BEFORE
            # the real Luogu page loads, so the page starts logged-in (no
            # manual refresh / re-login inside the embedded window).
            win = webview.create_window(
                title="洛谷提交 - " + problem_id,
                url=None,
                js_api=embedded_api,
                width=1100,
                height=800,
                min_size=(800, 600),
            )
            if win is None:
                return {"success": False, "error": "创建内嵌提交窗口失败"}
            embedded_api.set_window(win)
            self._embedded_win = win

            pairs = _parse_cookie_pairs(cookie)

            # Auto-fill script: substitute the user's code / language / O2 into
            # the template. __CODE__ / __LANG__ are JSON string literals so they
            # stay syntactically valid even with quotes, backslashes, etc.
            # A single-pass regex substitution avoids the token strings being
            # clobbered inside the (user) code content.
            lang_name = ""
            if lang:
                lang_name = _luogu_dropdown_lang_name(lang) or ""

            def _sub_token(m):
                if m.group(0) == "__CODE__":
                    return json.dumps(code or "")
                if m.group(0) == "__LANG__":
                    return json.dumps(lang_name)
                return "true" if enable_o2 else "false"

            auto_js = re.sub(r"__(CODE|LANG|O2)__", _sub_token, _AUTO_SUBMIT_JS)

            # Install the submit interceptor and the auto-fill script on every
            # page load (handlers attached BEFORE we navigate, so there is no
            # race with the initial DEFAULT_HTML load or the real Luogu page).
            def _on_loaded():
                for script in (_SUBMIT_INTERCEPTOR_JS, auto_js):
                    for _ in range(5):
                        try:
                            win.evaluate_js(script)
                            break
                        except Exception:
                            time.sleep(0.5)

            win.events.loaded += _on_loaded

            # If the user closes the embedded window without submitting, let
            # the main window know and release the window reference.
            def _on_closed():
                if embedded_api.rid is None:
                    try:
                        self._window.evaluate_js("window.__onEmbeddedClose()")
                    except Exception:
                        pass
                self._embedded_win = None

            win.events.closed += _on_closed

            # Cookie injection (marshaled to the UI thread) BEFORE navigating.
            # If the native CookieManager path fails, navigate anyway and fall
            # back to setting document.cookie after the page loads (with a
            # reload so the SPA picks up the login state).
            def _setup_and_navigate():
                ok = _inject_embedded_cookies(win, pairs)
                try:
                    win.load_url(url)
                except Exception:
                    pass
                if not ok:
                    time.sleep(1.5)
                    if win.events.loaded.wait(15):
                        for name, value in pairs:
                            try:
                                win.evaluate_js(
                                    "document.cookie="
                                    + json.dumps(f"{name}={value};path=/;domain=.luogu.com.cn")
                                )
                            except Exception:
                                pass
                        try:
                            win.load_url(url)
                        except Exception:
                            pass

            threading.Thread(target=_setup_and_navigate, daemon=True).start()

            return {"success": True, "url": url}
        except Exception as e:
            try:
                self._embedded_win = None
            except Exception:
                pass
            return {"success": False, "error": str(e)}

    # --- Problem URL ---
    def luogu_problem_url(self, pid, contest_id=""):
        """Build the Luogu problem page URL, optionally scoped to a contest."""
        problem_id = (pid or "").strip()
        contest_id = (contest_id or "").strip()
        if not problem_id:
            return {"success": False, "error": "缺少题号"}
        url = LUOGU_BASE + "/problem/" + urllib.parse.quote(problem_id)
        if contest_id:
            url += "?contest=" + urllib.parse.quote(contest_id)
        return {"success": True, "url": url}

    # --- External links ---
    def open_external(self, url):
        """Open a URL in the system's default browser.

        External links (Luogu/Vjudge/AtCoder...) are handed to the OS browser
        instead of navigating the pywebview window away, so the app always stays
        on its homepage (no more getting stuck on an external page with no way
        back).
        """
        url = (url or "").strip()
        if not url:
            return {"success": False, "error": "缺少链接"}
        try:
            import webbrowser
            webbrowser.open(url)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- User profile ---
    def get_user_info(self, cookie):
        """Fetch user info (uid, name, avatar) for header display."""
        cookie = (cookie or "").strip()
        if not cookie:
            return {"success": False, "error": "Cookie 不能为空"}
        try:
            info = fetch_user_info(cookie)
            return {"success": True, "user": info}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching user info")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- User search / other-user homepage (viewing by UID) ---
    def search_users(self, keyword):
        """Search Luogu users by name or UID."""
        try:
            users = search_users(keyword)
            return {"success": True, "users": users}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error searching users")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def get_user_info_by_uid(self, uid):
        """Fetch ANY user's homepage info by UID (viewer session = saved cookie)."""
        uid = (uid or "").strip()
        if not uid:
            return {"success": False, "error": "缺少用户 ID"}
        try:
            info = fetch_user_info(load_config().get("cookie", ""), uid=uid)
            return {"success": True, "user": info}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching user by uid")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def get_user_practice_by_uid(self, uid):
        """Fetch ANY user's practice detail by UID (public data)."""
        uid = (uid or "").strip()
        if not uid:
            return {"success": False, "error": "缺少用户 ID"}
        try:
            detail = fetch_user_practice_detail(load_config().get("cookie", ""), uid=uid)
            return {"success": True, "practice": detail}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching practice by uid")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def get_recent_submissions_by_uid(self, uid):
        """Fetch ANY user's recent submissions by UID (may be private)."""
        uid = (uid or "").strip()
        if not uid:
            return {"success": False, "error": "缺少用户 ID"}
        try:
            records = fetch_recent_submissions(load_config().get("cookie", ""), uid=uid)
            return {"success": True, "records": records}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching recent submissions by uid")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def get_user_statistics_by_uid(self, uid):
        """Fetch ANY user's statistics (trend/week/tags) by UID."""
        uid = (uid or "").strip()
        if not uid:
            return {"success": False, "error": "缺少用户 ID"}
        try:
            stats = fetch_user_statistics(load_config().get("cookie", ""), uid=uid)
            return {"success": True, "statistics": stats}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching user statistics by uid")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def get_user_blog(self, uid, page=1):
        """Get blog posts for a user."""
        try:
            data = fetch_user_blog(uid, page)
            return {"success": True, "posts": data.get("posts", []), "total": data.get("total", 0)}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching user blog")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def get_blog_detail(self, blog_id, author_name=""):
        """Get blog post content."""
        try:
            data = fetch_blog_detail(blog_id, author_name)
            return {"success": True, "blog": data}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching blog detail")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def get_user_practice_detail(self, cookie):
        """Fetch practice detail for the personal homepage."""
        cookie = (cookie or "").strip()
        if not cookie:
            return {"success": False, "error": "Cookie 不能为空"}
        try:
            detail = fetch_user_practice_detail(cookie)
            return {"success": True, "practice": detail}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching practice detail")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def get_recent_submissions(self, cookie):
        """Fetch the user's most recent submission records."""
        cookie = (cookie or "").strip()
        if not cookie:
            return {"success": False, "error": "Cookie 不能为空"}
        try:
            records = fetch_recent_submissions(cookie)
            return {"success": True, "records": records}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching recent submissions")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def get_user_statistics(self, cookie):
        """Fetch the user's submission timeline + tag distribution."""
        cookie = (cookie or "").strip()
        if not cookie:
            return {"success": False, "error": "Cookie 不能为空"}
        try:
            stats = fetch_user_statistics(cookie)
            return {"success": True, "statistics": stats}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching user statistics")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Export ---
    def export_problems(self, cookie, format="csv"):
        """Export passed problems as CSV or Markdown (writes file next to exe)."""
        result = export_passed_problems(cookie, format)
        if result.get("success"):
            return result
        return {"success": False, "error": result.get("error", "导出失败")}

    def open_export_file(self, file_path):
        """Open an exported file with the default OS application."""
        try:
            if file_path and os.path.exists(file_path):
                os.startfile(file_path)  # Windows only
                return {"success": True}
            return {"success": False, "error": "导出文件不存在"}
        except OSError as e:
            logger.error("Failed to open export file %s: %s", file_path, e)
            return {"success": False, "error": f"无法打开文件: {e}"}

    # --- Training plans (洛谷官方训练计划/学习路线) ---
    def get_trainings(self, page=1):
        """Fetch the official Luogu training plan list."""
        try:
            data = fetch_trainings(int(page or 1))
            return {"success": True, **data}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching trainings")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def get_training_detail(self, training_id):
        """Fetch the problem list of one training plan."""
        try:
            detail = fetch_training_detail(str(training_id or "").strip())
            return {"success": True, "training": detail}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching training detail")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Contest / Competition ---
    def get_contests(self, page=1):
        """Get contest list."""
        try:
            data = fetch_contests(int(page or 1))
            return {"success": True, "contests": data.get("contests", []), "total": data.get("total", 0)}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching contests")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def get_contest_detail(self, contest_id):
        """Get contest detail with problem list (uses saved cookie as viewer)."""
        try:
            data = fetch_contest_detail(str(contest_id or "").strip(),
                                        load_config().get("cookie", ""))
            return {"success": True, "contest": data}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching contest detail")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def register_contest(self, contest_id):
        """Register (报名) for a contest using the saved cookie."""
        try:
            register_contest(str(contest_id or "").strip(),
                             load_config().get("cookie", ""))
            return {"success": True, "joined": True}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error registering contest")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Drafts (unsaved code autosave) ---
    def save_draft(self, pid, code):
        problem_id = (pid or "").strip()
        code = code or ""
        if not problem_id:
            return {"success": False, "error": "缺少题号"}
        try:
            _save_draft(problem_id, code)
            return {"success": True}
        except OSError as e:
            logger.error("Failed to save draft for %s: %s", problem_id, e)
            return {"success": False, "error": f"草稿保存失败: {e}"}

    def get_draft(self, pid):
        problem_id = (pid or "").strip()
        if not problem_id:
            return {"success": False, "error": "缺少题号"}
        return {"success": True, "code": _get_draft(problem_id)}

    # --- Local submission records ---
    def save_local_record(self, pid, rid, code, lang, status, score, enable_o2):
        """Save a submission record locally."""
        _add_local_record(pid, rid, code, lang, status, score, enable_o2)
        return {"success": True}

    def get_local_records(self, pid=""):
        """Get local records for a problem (or all if pid is empty)."""
        records = _get_local_records(pid if pid else None)
        return {"success": True, "records": records}

    def get_local_stats(self):
        """Get local submission statistics."""
        stats = _get_local_stats()
        return {"success": True, "statistics": stats}

    def get_heatmap(self):
        """Get GitHub-style heatmap data from local + remote AC records."""
        try:
            return {"success": True,
                    **get_heatmap_data(load_config().get("cookie", ""))}
        except Exception as e:
            logger.exception("Unexpected error building heatmap")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def checkin(self):
        """Perform the Luogu daily check-in using the saved cookie."""
        cookie = load_config().get("cookie", "")
        if not cookie:
            return {"success": False, "error": "打卡需要登录洛谷，请填入洛谷 Cookie",
                    "no_cookie": True}
        try:
            result = luogu_checkin(cookie)
            return {"success": True, **result}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error during check-in")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def contest_reminders(self, hours=24):
        """Return contests starting within the next `hours` (reminders)."""
        try:
            result = get_upcoming_contests(load_config().get("cookie", ""), hours)
            return {"success": True, **result}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching contest reminders")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def smart_recommend(self, difficulty="", tag=""):
        """Return a recommended problem the user has not solved yet."""
        try:
            problem = smart_recommend(difficulty or "", tag or "")
            return {"success": True, "problem": problem}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error in smart recommend")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Contest standings (比赛榜单) ---
    def get_contest_standings(self, contest_id, page=1):
        """Fetch the standings of a contest."""
        try:
            data = fetch_contest_standings(contest_id, page=page or 1)
            return {"success": True, **data}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching contest standings")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Wrong book (错题本) ---
    def get_wrong_book(self):
        """Return problems whose latest local submission failed."""
        try:
            return {"success": True, "problems": get_wrong_book()}
        except Exception as e:
            logger.exception("Unexpected error building wrong book")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Code export (导出代码) ---
    def export_code(self, pid, rid):
        """Export a local submission's code to the exports folder."""
        try:
            result = export_submission_code(pid, rid)
            return {"success": True, **result}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error exporting code")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Advanced statistics (进阶统计) ---
    def get_advanced_stats(self):
        """Return richer statistics from local + remote submission records."""
        try:
            return {"success": True,
                    **get_advanced_stats(load_config().get("cookie", ""))}
        except Exception as e:
            logger.exception("Unexpected error computing advanced stats")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- AI translation (AI 翻译) ---
    def translate(self, text, target_lang="en", model=""):
        """Translate `text` into the target language using the bound AI model."""
        try:
            result = ai_translate(text or "", target_lang or "en", model or "")
            return {"success": True, "translation": result}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error translating")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def explain_failure(self, problem, code, lang, judge, thinking=False):
        """Stream an AI analysis of why a submission failed.

        Uses the same streaming infra as the assistant. Returns after the
        stream completes; tokens are pushed via window.__aiStream.
        """
        model = (load_config().get("model") or "deepseek-chat").strip() or "deepseek-chat"
        api_key, provider = self._ai_provider_key(model)
        if not api_key:
            return {"success": False, "error": f"缺少 {provider} API Key，请先在设置中配置"}

        messages = build_failure_messages(problem or {}, code or "", lang or "",
                                          judge or {})
        import json as _json

        def on_delta(kind, text):
            self._emit(
                "window.__aiStream && window.__aiStream("
                + _json.dumps(kind, ensure_ascii=False) + ","
                + _json.dumps(text, ensure_ascii=False) + ");"
            )

        try:
            stream_ai_chat(messages, api_key, model, on_delta,
                           thinking=bool(thinking))
            self._emit("window.__aiStream && window.__aiStream('done', '');")
            return {"success": True, "done": True}
        except RuntimeError as e:
            self._emit(
                "window.__aiStream && window.__aiStream('error', "
                + _json.dumps(str(e), ensure_ascii=False) + ");"
            )
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error in explain_failure")
            self._emit(
                "window.__aiStream && window.__aiStream('error', "
                + _json.dumps(f"服务器内部错误: {e}", ensure_ascii=False) + ");"
            )
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Problem collections (题单/收藏) ---
    def get_collections(self):
        """Return all problem collections."""
        try:
            data = _load_collections()
            return {"success": True, "collections": data["lists"]}
        except Exception as e:
            logger.exception("Unexpected error loading collections")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def create_collection(self, name):
        """Create a new empty collection."""
        try:
            lst = create_collection(name)
            return {"success": True, "collection": lst}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error creating collection")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def add_to_collection(self, pid, list_id, title="", difficulty=0):
        """Add a problem to a collection."""
        try:
            lst = add_to_collection(pid, list_id, title or "", difficulty or 0)
            return {"success": True, "collection": lst}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error adding to collection")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    def remove_from_collection(self, pid, list_id=""):
        """Remove a problem from a collection (all collections if list_id empty)."""
        try:
            lists = remove_from_collection(pid, list_id or None)
            return {"success": True, "collections": lists}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error removing from collection")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- Record ---
    def get_record(self, rid, cookie=""):
        cookie = cookie or ""
        try:
            result = fetch_record(int(rid), cookie=cookie)
            result["statusText"] = status_text(result.get("status", 0))
            for tc in result.get("test_cases", []):
                tc["statusText"] = status_text(tc.get("status", 0))
            return {"success": True, "record": result}
        except RuntimeError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Unexpected error fetching record")
            return {"success": False, "error": f"服务器内部错误: {e}"}

    # --- System notifications ---
    def show_system_notification(self, title="", message=""):
        """Show a Windows toast. Called exactly once per finished judge."""
        try:
            dispatched = show_system_notification(title or "洛谷", message or "")
            return {"success": True, "dispatched": dispatched}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Main entry: launch pywebview window loading the bundled index.html
# ---------------------------------------------------------------------------
def _build_index_html():
    """Read index.html and rewrite static asset paths to absolute file URIs.

    pywebview loads the HTML from a local file (file://), so Jinja's
    {{ url_for(...) }} tags won't work. We resolve static/ paths to
    absolute file:/// URIs so the WebView2 engine can load CSS/JS.
    """
    html_path = _resource_path(os.path.join("templates", "index.html"))
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    static_dir = _resource_path("static")
    def _replace_url_for(match):
        fname = match.group(1)
        abs_path = os.path.join(static_dir, fname.replace("/", os.sep))
        uri = abs_path.replace("\\", "/")
        if not uri.startswith("/"):
            uri = "/" + uri  # Windows: /C:/path/...
        return "file://" + uri

    html = re.sub(
        r"\{\{\s*url_for\(['\"]static['\"],\s*filename=['\"]([^'\"]+)['\"]\)\s*\}\}",
        _replace_url_for,
        html,
    )
    return html


def _write_temp_index(html_content):
    """Write processed HTML to a temp file next to the static dir and return
    its file:// URL.

    Loading via url=file://... (instead of html=string) gives the page a
    proper file:// origin, so WebView2 allows loading local CSS/JS without
    CORS restrictions.
    """
    static_dir = _resource_path("static")
    tmp_path = os.path.join(static_dir, "_index_runtime.html")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    uri = tmp_path.replace("\\", "/")
    if not uri.startswith("/"):
        uri = "/" + uri
    return "file://" + uri


if __name__ == "__main__":
    import webview

    # Keep the app window on its own page: any target="_blank" / window.open
    # of an external URL opens in the system default browser instead of
    # navigating the app window away (which would leave no way back).
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True

    html = _build_index_html()
    index_url = _write_temp_index(html)
    api = Api()

    # Create a portless desktop window. The page is loaded from a local
    # file:// URL so static assets (CSS/JS) resolve correctly, and JS calls
    # Python via window.pywebview.api.<method>(...).
    webview.create_window(
        title="Luogu Helper",
        url=index_url,
        js_api=api,
        width=1200,
        height=800,
        min_size=(800, 600),
    )
    # Give the Api access to the window so AI assistant chunks can be
    # streamed to the frontend via evaluate_js.
    api._window = webview.windows[0]
    webview.start(debug=not getattr(sys, "frozen", False))
