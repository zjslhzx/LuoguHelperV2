# -*- coding: utf-8 -*-
"""Temporary diagnostic: find how Vjudge loads language options for a problem."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"

vj_pid = app._build_vj_pid(PID)
s = app._build_vjudge_session(COOKIE)
base = f"{app.VJUDGE_BASE}/problem/{vj_pid}"
page = s.get(base, timeout=20).text

# 1) Find JS bundles
srcs = [u for u in re.findall(r'<script[^>]*src="([^"]+)"', page) if u.startswith("/static/bundle/")]
print("bundles:", srcs)

# 2) Try likely language-list API endpoints
for url in [
    "/problem/language?OJId=%E6%B4%9B%E8%B0%B7&probNum=P1001",
    "/problem/languages/%E6%B4%9B%E8%B0%B7-P1001",
    "/problem/languages?OJId=%E6%B4%9B%E8%B0%B7&probNum=P1001",
    "/problem/lang/%E6%B4%9B%E8%B0%B7-P1001",
    "/problem/getLanguage/%E6%B4%9B%E8%B0%B7-P1001",
    "/problem/getLanguages/%E6%B4%9B%E8%B0%B7-P1001",
    "/oj/language/%E6%B4%9B%E8%B0%B7",
]:
    try:
        r = s.get(f"{app.VJUDGE_BASE}{url}", timeout=15)
        ct = r.headers.get("Content-Type", "")
        body = r.text[:200].replace("\n", " ")
        print(f"\nGET {url}\n  -> {r.status_code} {ct}\n  {body}")
    except Exception as e:
        print(f"\nGET {url} EXC {e}")

# 3) Search bundles for language-fetching code
for u in srcs:
    try:
        js = s.get(f"{app.VJUDGE_BASE}{u}", timeout=20).text
    except Exception:
        continue
    hits = []
    for kw in ["getLanguages", "getLanguage", "loadLanguage", "languages", "getOJ", "language/"]:
        idx = 0
        while True:
            idx = js.find(kw, idx)
            if idx < 0:
                break
            hits.append((kw, idx))
            idx += 1
    if hits:
        print(f"\n=== {u}: {len(hits)} language-related hits ===")
        for kw, idx in hits[:3]:
            print(f"  '{kw}':", js[max(0, idx-120):idx+220].replace("\n", " ")[:340])
