/* =========================================================================
 * Luogu Problem Analysis Tool - Frontend Logic
 * ========================================================================= */

// --- DOM refs ---
const $ = (sel) => document.querySelector(sel);
const problemIdInput = $("#problemId");
const apiKeyInput = $("#apiKey");
const glmApiKeyInput = $("#glmApiKey");
const luoguCookieInput = $("#luoguCookie");
const modelSelect = $("#model");
const analyzeBtn = $("#analyzeBtn");
const saveApiKeyBtn = $("#saveApiKeyBtn");
const saveGlmApiKeyBtn = $("#saveGlmApiKeyBtn");
const saveCookieBtn = $("#saveCookieBtn");
const saveVjudgeCredsBtn = $("#saveVjudgeCredsBtn");
const configCollapseBtn = $("#configCollapseBtn");
const apiKeyStatus = $("#apiKeyStatus");
const glmApiKeyStatus = $("#glmApiKeyStatus");
const cookieStatus = $("#cookieStatus");
const vjudgeUsernameInput = $("#vjudgeUsername");
const vjudgePasswordInput = $("#vjudgePassword");
const vjudgeCredsStatus = $("#vjudgeCredsStatus");
const vjudgePasswordStatus = $("#vjudgePasswordStatus");
const clearVjudgeCredsBtn = $("#clearVjudgeCredsBtn");

// GLM model identifiers (must match backend GLM_MODELS in app.py)
const GLM_MODELS = new Set(["glm-4", "glm-4-flash", "glm-4.5-air"]);

function isGlmModel(model) {
    return GLM_MODELS.has((model || "").trim());
}
const statusBar = $("#statusBar");
const loadingOverlay = $("#loadingOverlay");
const loadingText = $("#loadingText");
const modeToggle = $("#modeToggle");
const themeToggle = $("#themeToggle");
const langToggle = $("#langToggle");
const inputPanel = document.querySelector(".input-panel");

// Search refs
const searchInput = $("#searchInput");
const searchBtn = $("#searchBtn");
const searchResults = $("#searchResults");
const ojSelect = $("#ojSelect");

// Current problem-library source: "luogu" or "atcoder"
function currentOj() {
    return ojSelect ? ojSelect.value : "luogu";
}

// Detect the OJ a problem ID belongs to, independent of the manual selector.
// - "AT_..." prefix (Luogu-hosted AtCoder, e.g. AT_abc138_1 / AT_abc138_a) -> atcoder
// - raw AtCoder task id (e.g. abc138_a, 1202Contest_a, dp_t) -> atcoder
// - anything else (P/CF/B/SP/UVA...) -> luogu
function detectOj(pid) {
    const p = String(pid || "").trim();
    if (/^AT_/i.test(p)) return "atcoder";
    if (/^[a-z0-9]+_[a-z0-9]+$/i.test(p)) return "atcoder";
    return "luogu";
}

// Apply the correct search placeholder for the current source + language
function updateSearchPlaceholder() {
    if (!searchInput) return;
    searchInput.placeholder = t(currentOj() === "atcoder" ? "atcoderSearchPlaceholder" : "searchPlaceholder");
}

// Tab refs
const tabs = document.querySelectorAll(".tab");

// Content refs
const problemContent = $("#problemContent");
const solutionsContent = $("#solutionsContent");
const analysisContent = $("#analysisContent");

// Submit refs
const langSelect = $("#langSelect");
const codeEditor = $("#codeEditor");
const codeHighlight = $("#codeHighlight").querySelector("code");
const submitCodeBtn = $("#submitCodeBtn");
const submitTargetPid = $("#submitTargetPid");
const submitHint = $("#submitHint");
const enableO2Checkbox = $("#enableO2");
const enableBracketCheckbox = $("#enableBracket");
const enableNotifyCheckbox = $("#enableNotify");
const tplBtn = $("#tplBtn");
const tplMenu = $("#tplMenu");
const judgeResult = $("#judgeResult");
const copyCodeBtn = $("#copyCodeBtn");
const saveDraftBtn = $("#saveDraftBtn");
const draftStatusEl = $("#draftStatus");

// Daily-feature refs (打卡 / 统计 / 比赛提醒)
const checkinBtn = $("#checkinBtn");
const statsBtn = $("#statsBtn");
const contestReminderBtn = $("#contestReminderBtn");
const standingsBtn = $("#standingsBtn");
const recommendBtn = $("#recommendBtn");
const toastContainer = $("#toastContainer");
// Stats modal removed as integrated into profile modal
const statsSummary = document.getElementById("statsSummary");
const statsHeatmap = document.getElementById("statsHeatmap");

// Online IDE refs
const ideModeBtn = $("#ideModeBtn");
const ideSplit = $("#ideSplit");
const ideMiniTabs = $("#ideMiniTabs");
const ideStdin = $("#ideStdin");
const ideRunBtn = $("#ideRunBtn");
const ideOutput = $("#ideOutput");
const ideRunMeta = $("#ideRunMeta");
const ideCaseList = $("#ideCaseList");
const ideCaseAddBtn = $("#ideCaseAddBtn");
const ideCaseRunBtn = $("#ideCaseRunBtn");
const ideCaseResult = $("#ideCaseResult");
const ideGenCode = $("#ideGenCode");
const ideBruteCode = $("#ideBruteCode");
const ideDuipaiIter = $("#ideDuipaiIter");
const ideDuipaiRunBtn = $("#ideDuipaiRunBtn");
const ideDuipaiOutput = $("#ideDuipaiOutput");
// Slots that content gets re-parented into in IDE mode
const ideSearchSlot = $("#ideSearchSlot");
const ideProblemSlot = $("#ideProblemSlot");
const ideSolutionsSlot = $("#ideSolutionsSlot");
const ideAnalysisSlot = $("#ideAnalysisSlot");
const ideEditorHeaderSlot = $("#ideEditorHeaderSlot");
const ideEditorSlot = $("#ideEditorSlot");
const ideSubmitFooterSlot = $("#ideSubmitFooterSlot");
const ideDivider = $("#ideDivider");

// Captcha modal refs
const captchaModal = $("#captchaModal");
const captchaImage = $("#captchaImage");
const captchaInput = $("#captchaInput");
const captchaError = $("#captchaError");
const refreshCaptchaBtn = $("#refreshCaptchaBtn");
const cancelCaptchaBtn = $("#cancelCaptchaBtn");
const confirmCaptchaBtn = $("#confirmCaptchaBtn");
const captchaGiveUpBox = $("#captchaGiveUpBox");
const captchaGiveUpText = $("#captchaGiveUpText");
const captchaOpenLuoguBtn = $("#captchaOpenLuoguBtn");
const manualSubmitModal = $("#manualSubmitModal");
const manualCopyCodeBtn = $("#manualCopyCodeBtn");
const manualOpenLuoguBtn = $("#manualOpenLuoguBtn");
const manualDoneBtn = $("#manualDoneBtn");
const manualCancelBtn = $("#manualCancelBtn");
const manualCopiedTip = $("#manualCopiedTip");

// User profile refs
const userProfileArea = $("#userProfileArea");
const userAvatar = $("#userAvatar");
const userName = $("#userName");
const profileModal = $("#profileModal");
const profileAvatar = $("#profileAvatar");
const profileName = $("#profileName");
const profileMeta = $("#profileMeta");
const profileLoading = $("#profileLoading");
const profileContent = $("#profileContent");
const profileTableBody = $("#profileTableBody");
const profileCloseBtn = $("#profileCloseBtn");
const profileBlogBtn = $("#profileBlogBtn");
const profileHomeLink = $("#profileHomeLink");
const profileCollectionsTitle = $("#profileCollectionsTitle");
const summaryPassed = $("#summaryPassed");
const summaryAttempted = $("#summaryAttempted");
const summaryTotal = $("#summaryTotal");
const summaryRate = $("#summaryRate");
const profileBanner = $("#profileBanner");
const profileInfo = $("#profileInfo");
const profileTypeBody = $("#profileTypeBody");
const recentBody = $("#recentBody");
const profileCollections = $("#profileCollections");
// User search modal refs
const userSearchBtn = $("#userSearchBtn");
const userSearchModal = $("#userSearchModal");
const userSearchCloseBtn = $("#userSearchCloseBtn");
const userSearchInput = $("#userSearchInput");
const userSearchGoBtn = $("#userSearchGoBtn");
const userSearchResults = $("#userSearchResults");
const collectModal = $("#collectModal");
const collectTitle = $("#collectTitle");
const collectList = $("#collectList");
const collectNewName = $("#collectNewName");
const collectCreateBtn = $("#collectCreateBtn");
const collectError = $("#collectError");
const collectCloseBtn = $("#collectCloseBtn");
const uncollectModal = $("#uncollectModal");
const uncollectTitle = $("#uncollectTitle");
const uncollectText = $("#uncollectText");
const uncollectConfirmBtn = $("#uncollectConfirmBtn");
const uncollectCancelBtn = $("#uncollectCancelBtn");
const uncollectCloseBtn = $("#uncollectCloseBtn");
let profileChart = null;
let profileTypeChart = null;
let profileTrendChart = null;
let profileWeekChart = null;
let profileTagChart = null;
let userInfoCache = null;
// When set (viewing ANOTHER user via search), the profile modal loads data
// by UID instead of the logged-in user's cookie. null = viewing yourself.
let profileViewUid = null;

// Lazy loading flags for profile sections (reset when the modal closes)
let profileStatsLoaded = false;
let profileTrendLoaded = false;
let profileTagsLoaded = false;
let profileRecentLoaded = false;
// When set, the currently open problem belongs to a contest and code is
// submitted as a contest submission (with ?contestId=...).
let currentContestId = "";
// Problem collections (题单) loaded from the backend
let collectionsCache = null;
let uncollectPid = null;
let collectTarget = null; // {pid, title, difficulty} currently being collected

// Luogu official difficulty colors (current new frontend, matching www.luogu.com.cn tags)
// Luogu restructured difficulties in 2026-06: added 提高(cyan) tier, so levels are 0-8.
const DIFFICULTY_COLORS = [
    "#BFBFBF", // 0 暂无评定
    "#FE4C61", // 1 入门
    "#F39C11", // 2 普及-
    "#FFC116", // 3 普及
    "#52C41A", // 4 普及+/提高-
    "#13C2C2", // 5 提高
    "#3498DB", // 6 提高+/省选-
    "#9D3DCF", // 7 省选/NOI-
    "#0E1D69", // 8 NOI/NOI+/CTS
];

// Pick a readable text color (dark on light badges like yellow, white elsewhere)
function diffBadgeTextColor(hex) {
    const c = hex.replace("#", "");
    const r = parseInt(c.substr(0, 2), 16);
    const g = parseInt(c.substr(2, 2), 16);
    const b = parseInt(c.substr(4, 2), 16);
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.6 ? "#333" : "#fff";
}

// Luogu problem type display names (unknown types fall back to raw key)
const TYPE_NAMES = {
    P: "Luogu", B: "Basic", CF: "Codeforces", AT: "AtCoder",
    UVA: "UVA", SP: "SPOJ", T: "Team", G: "Group",
};

// Luogu record status code -> i18n key + official Luogu verdict color.
// Status 14 ("Unaccepted") is an aggregate; the backend derives the real
// verdict (TLE/WA/RE...) from test cases for display.
const STATUS_MAP = {
    0: { key: "statusWaiting", color: "#14558F" },
    1: { key: "statusJudging", color: "#3498DB" },
    2: { key: "statusCe", color: "#FADB14" },
    3: { key: "statusOle", color: "#052242" },
    4: { key: "statusMle", color: "#052242" },
    5: { key: "statusTle", color: "#052242" },
    6: { key: "statusWa", color: "#E74C3C" },
    7: { key: "statusRe", color: "#9D3DCF" },
    8: { key: "statusAc", color: "#52C41A" },
    9: { key: "statusHack", color: "#F39C11" },
    11: { key: "statusUnaccepted", color: "#E74C3C" },
    12: { key: "statusAc", color: "#52C41A" },
    14: { key: "statusUke", color: "#8c8c8c" },
};
const STATUS_OTHER = { key: "statusOther", color: "#8c8c8c" };

// Palette for the type distribution doughnut chart
const TYPE_CHART_COLORS = [
    "#5b8ff9", "#5ad8a6", "#f6bd16", "#e8684a", "#6dc8ec",
    "#9270ca", "#ff9d4d", "#269a99", "#ff99c3", "#8378ea",
];

// --- State ---
let currentProblem = null;
let currentSolutions = null;
let lastSolutionTotal = 0;
let analysisMode = "ai"; // "ai" or "filter"
// Submission history per problem: { pid: [{ rid, code, lang, record, status }], ... }
let submissionHistory = {};
let currentRid = null; // rid of the submission currently being polled
// Multi-tab: opened problems (most recent last), cached problem data
let openTabs = []; // [{pid, title}]
let activeTabPid = null;
let problemDataCache = {}; // pid -> {problem, solutions...}
const MAX_OPEN_TABS = 12;

// Online IDE mode state
let ideMode = false;
// Maps a re-parented element -> its original parent, so exitIdeMode can restore it
const ideOriginalParents = new Map();
// Luogu language ids supported by the local compile & run backend (must match
// LANG_COMPILE_INFO in app.py): C, C++ variants, Python 3, PyPy3
const IDE_SUPPORTED_LANGS = new Set([2, 3, 4, 12, 14, 28, 7, 33]);

// Unsaved code draft state: draftPid is the problem the code editor content
// currently belongs to (avoids saving under a wrong pid after the analyze
// flow changes currentProblem without touching the editor).
let draftPid = null;
let draftTimer = null;
const DRAFT_INTERVAL_MS = 30000;

// --- Config ---
const DIFFICULTY_MAP = {
    0: "暂无评定",
    1: "入门",
    2: "普及-",
    3: "普及/提高-",
    4: "普及+/提高",
    5: "提高+/省选-",
    6: "省选/NOI-",
    7: "NOI/NOI+/CTSC",
};

function getDifficultyName(level) {
    return t("diff" + level) || t("difficultyUnknown");
}

// Configure marked
if (typeof marked !== "undefined") {
    marked.setOptions({ breaks: true, gfm: true });
}

// =========================================================================
// Tab switching
// =========================================================================
tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        const name = tab.dataset.tab;
        switchTab(name);
        if (name === "submit") {
            loadLanguages();
            updateSubmitPanel();
            renderSubmissionHistory(currentProblem ? currentProblem.pid : null);
        }
    });
});

// =========================================================================
// Mode toggle (AI 分析 / 自动筛选)
// =========================================================================
modeToggle.addEventListener("click", (e) => {
    const btn = e.target.closest(".mode-btn");
    if (!btn) return;
    setMode(btn.dataset.mode);
});

function setMode(mode) {
    analysisMode = mode;
    modeToggle.querySelectorAll(".mode-btn").forEach((b) => {
        b.classList.toggle("active", b.dataset.mode === mode);
    });
    // Dim AI-only inputs when in filter mode
    inputPanel.classList.toggle("mode-filter", mode === "filter");
    if (typeof STORAGE_KEYS !== "undefined") {
        localStorage.setItem(STORAGE_KEYS.mode, mode);
    }
}

// =========================================================================
// Theme toggle (dark / light / deepblue / lightblue)
// =========================================================================
function isDarkTheme(theme) {
    return theme === "dark" || theme === "deepblue";
}

function setTheme(theme) {
    const root = document.documentElement;
    root.setAttribute("data-theme", theme);
    // Toggle code highlight CSS (dark family: dark/deepblue, light family: light/lightblue)
    const darkLink = document.getElementById("hljsDark");
    const lightLink = document.getElementById("hljsLight");
    const darkFamily = isDarkTheme(theme);
    if (darkLink && lightLink) {
        darkLink.disabled = !darkFamily;
        lightLink.disabled = darkFamily;
    }
    localStorage.setItem(STORAGE_KEYS.theme, theme);
}

// Theme rotation order: dark -> light -> deepblue -> lightblue -> dark
const THEME_CYCLE = ["dark", "light", "deepblue", "lightblue"];

themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const idx = THEME_CYCLE.indexOf(current);
    const next = idx >= 0 ? THEME_CYCLE[(idx + 1) % THEME_CYCLE.length] : "dark";
    setTheme(next);
});

// =========================================================================
// Problem search
// =========================================================================
// Pagination state for the default problem list
const LIST_PAGE_SIZE = 20; // Luogu returns 20 problems per page
let currentListPage = 1;
let totalListPages = 1;
let listTotalCount = 0;

async function searchProblems() {
    const q = searchInput.value.trim();
    // Empty query -> show default problem list
    if (!q) {
        await loadDefaultProblems();
        return;
    }

    searchBtn.disabled = true;
    searchBtn.textContent = t("searching");
    searchResults.classList.remove("hidden");
    searchResults.innerHTML = `<div class="search-empty">${t("searchSearching", escapeHtml(q))}</div>`;

    try {
        if (currentOj() === "atcoder") {
            const data = await apiGet(`/api/atcoder-search?q=${encodeURIComponent(q)}`);
            renderSearchResults(data.count, data.problems, q, false);
        } else {
            const data = await apiGet(`/api/search?q=${encodeURIComponent(q)}`);
            searchTitleTranslations = {}; // new search -> clear AI-translated titles
            renderSearchResults(data.count, data.problems, q);
        }
    } catch (err) {
        searchResults.innerHTML = `<div class="search-empty">${escapeHtml(err.message || t("searchBtn"))}</div>`;
    } finally {
        searchBtn.disabled = false;
        searchBtn.textContent = t("searchBtn");
    }
}

async function loadDefaultProblems(page) {
    page = page || 1;
    currentListPage = page;
    searchBtn.disabled = true;
    searchBtn.textContent = t("searching");
    searchResults.classList.remove("hidden");
    searchResults.innerHTML = `<div class="search-empty">${t("defaultLoading")}</div>`;

    try {
        if (currentOj() === "atcoder") {
            const data = await apiGet(`/api/atcoder-search?q=&page=${page}`);
            listTotalCount = data.count || 0;
            totalListPages = Math.max(1, data.total_pages || 1);
            searchTitleTranslations = {};
            renderSearchResults(data.count, data.problems, "", true);
        } else {
            const data = await apiGet(`/api/default-problems?page=${page}`);
            listTotalCount = data.count || 0;
            totalListPages = Math.max(1, Math.ceil(listTotalCount / LIST_PAGE_SIZE));
            searchTitleTranslations = {}; // new page -> clear AI-translated titles
            renderSearchResults(data.count, data.problems, "", true);
        }
    } catch (err) {
        searchResults.innerHTML = `<div class="search-empty">${escapeHtml(err.message || t("searchBtn"))}</div>`;
    } finally {
        searchBtn.disabled = false;
        searchBtn.textContent = t("searchBtn");
    }
}

// Fetch user's submission status and mark each search result item:
//   green ✓  = submitted with full score (AC)
//   red ✗    = submitted but not full score
//   gray -   = never submitted
// Skipped if no cookie.
async function markProblemStatus() {
    const cookie = (luoguCookieInput.value || "").trim();
    if (!cookie) return; // no cookie -> no marks

    try {
        const data = await apiGet(`/api/practice?cookie=${encodeURIComponent(cookie)}`);
        const passedSet = new Set(data.passed || []);
        const submittedSet = new Set(data.submitted || []);
        searchResults.querySelectorAll(".search-result-status").forEach((el) => {
            const pid = el.dataset.pid;
            if (passedSet.has(pid)) {
                el.className = "search-result-status ac";
                el.textContent = "✓";
                el.title = t("passed");
            } else if (submittedSet.has(pid)) {
                el.className = "search-result-status wa";
                el.textContent = "✗";
                el.title = t("notPassed");
            } else {
                el.className = "search-result-status none";
                el.textContent = "−";
                el.title = t("notSubmitted");
            }
        });
    } catch (err) {
        console.warn("markProblemStatus failed:", err);
    }
}

// Search result filter state (client-side filtering of fetched results)
let searchFilterState = { difficulty: "", tag: "", type: "" };
let searchAllProblems = [];
let searchLastCtx = { count: 0, query: "", isDefault: false };
// pid -> AI translated title (题库标题翻译)
let searchTitleTranslations = {};

function applySearchFilters(problems) {
    let list = problems || [];
    if (searchFilterState.difficulty !== "") {
        const d = Number(searchFilterState.difficulty);
        list = list.filter((p) => Number(p.difficulty) === d);
    }
    if (searchFilterState.tag !== "") {
        list = list.filter((p) => (p.tags || []).includes(searchFilterState.tag));
    }
    if (searchFilterState.type !== "") {
        const t = String(searchFilterState.type).toLowerCase();
        list = list.filter((p) => String(p.pid || "").toLowerCase().startsWith(t));
    }
    return list;
}

function renderSearchResults(count, problems, query, isDefault) {
    const atcoder = currentOj() === "atcoder";
    if (!problems || problems.length === 0) {
        if (atcoder) {
            const hint = isDefault ? "" : `<p class="search-empty-hint">${escapeHtml(t("searchEmptyHint"))}</p>`;
            searchResults.innerHTML = `<div class="search-empty">${t("atcoderNoSearchResult", escapeHtml(query))}</div>${hint}`;
            return;
        }
        const hint = isDefault ? "" : `<p class="search-empty-hint">${escapeHtml(t("searchEmptyHint"))}</p>`;
        searchResults.innerHTML = `<div class="search-empty">${t("searchEmpty", escapeHtml(query))}</div>${hint}`;
        return;
    }
    searchAllProblems = problems;
    searchLastCtx = { count, query, isDefault };

    if (atcoder) {
        // AtCoder path: no filter bar / status marks / pagination.
        const headerText = isDefault
            ? t("atcoderDefaultHeader", count)
            : t("searchResultsHeader", count, problems.length);
        let html = `<div class="search-results-header">${headerText}</div>`;
        problems.forEach((p) => {
            const diffText = (typeof p.difficulty === "number" && isFinite(p.difficulty)) ? p.difficulty : "--";
            html += `
        <div class="search-result-item" data-pid="${escapeHtml(p.id)}" title="${escapeHtml(p.id)} - ${escapeHtml(p.title)}">
            <span class="search-result-pid">${escapeHtml(p.id)}</span>
            <span class="search-result-title">${escapeHtml(p.title)}</span>
            <div class="search-result-meta">
                <span class="search-result-diff">${escapeHtml(t("atcoderContest"))} ${escapeHtml(p.contest_id)}</span>
                <span class="search-result-stats">Diff: ${escapeHtml(String(diffText))}</span>
                <a class="search-result-link atcoder" href="https://atcoder.jp/contests/${encodeURIComponent(p.contest_id)}/tasks/${encodeURIComponent(p.id)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">${t("atcoderName")}</a>
            </div>
            ${collectBtnHtml(p.id, p.title, p.difficulty)}
        </div>`;
        });
        searchResults.innerHTML = html;

        // Collect buttons
        searchResults.querySelectorAll(".collect-btn").forEach(attachCollectBtn);
        refreshCollectButtons();

        // Click to load problem into the problemId field and display problem info only
        searchResults.querySelectorAll(".search-result-item").forEach((item) => {
            item.addEventListener("click", () => {
                const pid = item.dataset.pid;
                if (!pid) return;
                problemIdInput.value = pid;
                searchResults.classList.add("hidden");
                loadProblemOnly(pid);
            });
        });

        // Render pagination at the bottom for the default list (Luogu-style)
        if (isDefault && totalListPages > 1) {
            renderPagination(searchResults, currentListPage, totalListPages, (p) => {
                loadDefaultProblems(p);
            });
        }
        return;
    }

    const filtered = applySearchFilters(problems);
    const headerText = isDefault
        ? t("defaultResultsHeader", count, problems.length)
        : t("searchResultsHeader", count, problems.length);

    const tagOptions = [...new Set(problems.flatMap((p) => p.tags || []))].sort();
    const typeOptions = [...new Set(problems.map((p) => (String(p.pid || "").match(/^[A-Za-z]+/) || ["P"])[0]))].sort();
    const translated = Object.keys(searchTitleTranslations).length > 0;
    const filterBar = `
        <div class="search-filter-bar">
            <select id="searchFilterType" class="search-filter-select" title="${t("filterAllType")}">
                <option value="">${t("filterAllType")}</option>
                ${typeOptions.map((tp) =>
                    `<option value="${escapeHtml(tp)}" ${searchFilterState.type === tp ? "selected" : ""}>${escapeHtml(tp)}</option>`).join("")}
            </select>
            <select id="searchFilterDiff" class="search-filter-select" title="${t("filterDifficulty")}">
                <option value="">${t("filterAllDifficulty")}</option>
                ${getDifficultyNames().map((n, i) =>
                    `<option value="${i}" ${searchFilterState.difficulty === String(i) ? "selected" : ""}>${escapeHtml(n)}</option>`).join("")}
            </select>
            <select id="searchFilterTag" class="search-filter-select" title="${t("filterTag")}">
                <option value="">${t("filterAllTag")}</option>
                ${tagOptions.map((tg) =>
                    `<option value="${escapeHtml(tg)}" ${searchFilterState.tag === tg ? "selected" : ""}>${escapeHtml(tg)}</option>`).join("")}
            </select>
            <button type="button" id="searchTitleTranslateBtn" class="btn-secondary search-filter-btn" title="${t("translateTitleBtn")}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.87 15.07a10 10 0 1 1 2.2-2.2"></path><path d="M9 11h6M10 8h4M11 5h2"></path></svg>
                <span>${translated ? t("translateTitleRestore") : t("translateTitleBtn")}</span>
            </button>
            <span class="search-filter-count">${t("filterResultCount", filtered.length, problems.length)}</span>
        </div>`;

    let html = `<div class="search-results-header">${headerText}</div>${filterBar}`;
    filtered.forEach((p) => {
        const diff = getDifficultyName(p.difficulty);
        const rate = p.totalSubmit > 0 ? (p.totalAccepted / p.totalSubmit * 100).toFixed(1) + "%" : "--";
        const showTitle = (searchTitleTranslations[p.pid] || p.title);
        html += `
        <div class="search-result-item" data-pid="${escapeHtml(p.pid)}" title="${escapeHtml(p.pid)} - ${escapeHtml(showTitle)}">
            <span class="search-result-pid">${escapeHtml(p.pid)}</span>
            <span class="search-result-title">${escapeHtml(showTitle)}</span>
            <div class="search-result-meta">
                <span class="search-result-diff d${p.difficulty}">${diff}</span>
                <span class="search-result-stats">${t("submitShort")} ${formatNum(p.totalSubmit)} · ${t("acceptShort")} ${formatNum(p.totalAccepted)} · ${rate}</span>
                <a class="search-result-link" href="https://www.luogu.com.cn/problem/${escapeHtml(p.pid)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">${t("luoguLink")}</a>
                <span class="search-result-status" data-pid="${escapeHtml(p.pid)}"></span>
            </div>
            ${collectBtnHtml(p.pid, p.title, p.difficulty)}
        </div>`;
    });
    searchResults.innerHTML = html;

    // Bind filter selects (client-side, no refetch)
    const diffSel = document.getElementById("searchFilterDiff");
    const tagSel = document.getElementById("searchFilterTag");
    const typeSel = document.getElementById("searchFilterType");
    if (diffSel) {
        diffSel.addEventListener("change", (e) => {
            searchFilterState.difficulty = e.target.value;
            renderSearchResults(searchLastCtx.count, searchAllProblems, searchLastCtx.query, searchLastCtx.isDefault);
        });
    }
    if (tagSel) {
        tagSel.addEventListener("change", (e) => {
            searchFilterState.tag = e.target.value;
            renderSearchResults(searchLastCtx.count, searchAllProblems, searchLastCtx.query, searchLastCtx.isDefault);
        });
    }
    if (typeSel) {
        typeSel.addEventListener("change", (e) => {
            searchFilterState.type = e.target.value;
            renderSearchResults(searchLastCtx.count, searchAllProblems, searchLastCtx.query, searchLastCtx.isDefault);
        });
    }
    // AI translate search-result titles
    const titleTranslateBtn = document.getElementById("searchTitleTranslateBtn");
    if (titleTranslateBtn) {
        titleTranslateBtn.addEventListener("click", () => toggleSearchTitleTranslation());
    }

    // Collect buttons
    searchResults.querySelectorAll(".collect-btn").forEach(attachCollectBtn);
    refreshCollectButtons();

    // Click to load problem into the problemId field and display problem info only
    searchResults.querySelectorAll(".search-result-item").forEach((item) => {
        item.addEventListener("click", () => {
            const pid = item.dataset.pid;
            if (!pid) return;
            problemIdInput.value = pid;
            searchResults.classList.add("hidden");
            loadProblemOnly(pid);
        });
    });

    // Mark AC/WA status after rendering
    markProblemStatus();

    // Render pagination at the bottom for the default list
    if (isDefault && totalListPages > 1) {
        renderPagination(searchResults, currentListPage, totalListPages, (p) => {
            loadDefaultProblems(p);
        });
    }
}

// Translate the titles of the currently-filtered search results with the
// bound AI model. Toggle: translate once, click again to restore original.
async function toggleSearchTitleTranslation() {
    if (!searchAllProblems.length) return;
    if (Object.keys(searchTitleTranslations).length > 0) {
        // Restore original titles
        searchTitleTranslations = {};
        renderSearchResults(searchLastCtx.count, searchAllProblems, searchLastCtx.query, searchLastCtx.isDefault);
        return;
    }
    const problems = applySearchFilters(searchAllProblems);
    const target = currentLang === "zh" ? "en" : "zh";
    const items = problems
        .filter((p) => p.pid)
        .map((p) => ({ pid: p.pid, title: p.title || "" }));
    if (!items.length) return;
    const btn = document.getElementById("searchTitleTranslateBtn");
    const btnLabel = btn && btn.querySelector("span");
    if (btnLabel) btnLabel.textContent = t("translateTitlesLoading");
    try {
        // Translate each title in small batches to keep requests small.
        const translated = {};
        const BATCH = 5;
        for (let i = 0; i < items.length; i += BATCH) {
            const batch = items.slice(i, i + BATCH);
            const source = batch.map((b, j) => `${i + j + 1}. ${b.title}`).join("\n");
            const data = await apiCall("translate", source, target);
            const lines = String(data.translation || "").split("\n");
            lines.forEach((line, idx) => {
                const m = line.match(/^\s*\d+[.、:：)]?\s*(.+)$/);
                if (m && batch[idx]) translated[batch[idx].pid] = m[1].trim();
            });
        }
        searchTitleTranslations = translated;
        renderSearchResults(searchLastCtx.count, searchAllProblems, searchLastCtx.query, searchLastCtx.isDefault);
        showToast(t("translateSuccess"), "success");
    } catch (err) {
        searchTitleTranslations = {};
        renderSearchResults(searchLastCtx.count, searchAllProblems, searchLastCtx.query, searchLastCtx.isDefault);
        showToast(t("translateFailed", err.message), "error");
    }
}

// Refresh the search-results filter bar (type/difficulty/tag + AI title
// button + result count) when the UI language switches. The bar is created
// dynamically by renderSearchResults, so it needs a manual text refresh.
function refreshSearchResultsText() {
    if (searchResults.classList.contains("hidden")) return;
    if (!searchAllProblems.length) return;
    const header = searchResults.querySelector(".search-results-header");
    if (header && searchLastCtx) {
        header.textContent = searchLastCtx.isDefault
            ? t("defaultResultsHeader", searchLastCtx.count, searchAllProblems.length)
            : t("searchResultsHeader", searchLastCtx.count, searchAllProblems.length);
    }
    const typeSel = document.getElementById("searchFilterType");
    const diffSel = document.getElementById("searchFilterDiff");
    const tagSel = document.getElementById("searchFilterTag");
    const btn = document.getElementById("searchTitleTranslateBtn");
    const countSpan = searchResults.querySelector(".search-filter-count");
    if (typeSel) {
        typeSel.title = t("filterAllType");
        const first = typeSel.querySelector("option");
        if (first) first.textContent = t("filterAllType");
    }
    if (diffSel) {
        diffSel.title = t("filterDifficulty");
        const texts = [t("filterAllDifficulty")].concat(getDifficultyNames());
        diffSel.querySelectorAll("option").forEach((opt, i) => {
            if (texts[i]) opt.textContent = texts[i];
        });
    }
    if (tagSel) {
        tagSel.title = t("filterTag");
        const first = tagSel.querySelector("option");
        if (first) first.textContent = t("filterAllTag");
    }
    if (btn) {
        btn.title = t("translateTitleBtn");
        const span = btn.querySelector("span");
        if (span) {
            span.textContent = Object.keys(searchTitleTranslations).length > 0
                ? t("translateTitleRestore") : t("translateTitleBtn");
        }
    }
    if (countSpan) {
        countSpan.textContent = t("filterResultCount",
            applySearchFilters(searchAllProblems).length, searchAllProblems.length);
    }
}

// Render a row of numbered page buttons (with prev/next and ellipsis).
// `onPageClick` is called with the selected page number.
function renderPagination(container, current, total, onPageClick) {
    const pager = document.createElement("div");
    pager.className = "pagination";

    function makeBtn(label, page, opts) {
        opts = opts || {};
        const btn = document.createElement("button");
        btn.className = "page-btn";
        btn.textContent = label;
        if (page === current && !opts.jump) btn.classList.add("active");
        if (opts.disabled) {
            btn.classList.add("disabled");
            btn.disabled = true;
        } else {
            btn.addEventListener("click", () => onPageClick(page));
        }
        return btn;
    }

    // Prev
    pager.appendChild(makeBtn("‹", current - 1, { disabled: current <= 1 }));

    // Build page number list with ellipsis
    const pages = [];
    const window = 2; // pages on each side of current
    const showFirst = 1;
    const showLast = total;
    for (let i = 1; i <= total; i++) {
        if (i === showFirst || i === showLast ||
            (i >= current - window && i <= current + window)) {
            pages.push(i);
        } else if (pages[pages.length - 1] !== "...") {
            pages.push("...");
        }
    }

    pages.forEach((p) => {
        if (p === "...") {
            const span = document.createElement("span");
            span.className = "page-ellipsis";
            span.textContent = "…";
            pager.appendChild(span);
        } else {
            pager.appendChild(makeBtn(String(p), p));
        }
    });

    // Next
    pager.appendChild(makeBtn("›", current + 1, { disabled: current >= total }));

    container.appendChild(pager);
}

searchBtn.addEventListener("click", searchProblems);
searchInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") searchProblems();
});

if (ojSelect) {
    ojSelect.addEventListener("change", () => {
        updateSearchPlaceholder();
        // clear search results and reset filters when switching source
        searchFilterState = { difficulty: "", tag: "", type: "" };
        searchAllProblems = [];
        searchLastCtx = { count: 0, query: "", isDefault: false };
        if (searchResults) {
            searchResults.classList.add("hidden");
            searchResults.innerHTML = "";
        }
        updateSubmitPanel();
        updateSubmitButtonState();
    });
}
updateSearchPlaceholder();

// =========================================================================
// Problem Browser with Filters
// =========================================================================
let problemBrowserActive = false;
// Luogu-style pagination state for the problem browser
let browserPage = 1;
const BROWSER_PAGE_SIZE = 20;

function showProblemBrowser() {
    problemBrowserActive = true;
    const searchRow = document.querySelector(".search-row");
    if (!searchRow) return;

    // Add filter bar below search row if not exists
    let filterBar = document.getElementById("filterBar");
    if (!filterBar) {
        filterBar = document.createElement("div");
        filterBar.id = "filterBar";
        filterBar.className = "filter-bar";
        filterBar.innerHTML = `
            <select id="filterDifficulty" class="filter-select" multiple size="1" style="min-width:100px;" title="${t("filterDifficulty")}">
                <option value="">${t("filterAllDifficulty")}</option>
                <option value="1">${t("diff1")}</option>
                <option value="2">${t("diff2")}</option>
                <option value="3">${t("diff3")}</option>
                <option value="4">${t("diff4")}</option>
                <option value="5">${t("diff5")}</option>
                <option value="6">${t("diff6")}</option>
                <option value="7">${t("diff7")}</option>
            </select>
            <select id="filterType" class="filter-select" style="min-width:80px;" title="${t("filterAllType")}">
                <option value="">${t("filterAllType")}</option>
                <option value="P">Luogu P</option>
                <option value="CF">Codeforces</option>
                <option value="AT">AtCoder</option>
                <option value="SP">SPOJ</option>
                <option value="UVA">UVA</option>
            </select>
            <button id="applyFilterBtn" class="btn-secondary" style="padding:4px 12px;font-size:13px;">${t("applyFilter")}</button>
            <button id="clearFilterBtn" class="btn-secondary" style="padding:4px 12px;font-size:13px;">${t("clearFilter")}</button>
        `;
        searchRow.parentNode.insertBefore(filterBar, searchRow.nextSibling);

        // Event handlers
        document.getElementById("applyFilterBtn").addEventListener("click", () => {
            browserPage = 1;
            applyFilters(1);
        });
        document.getElementById("clearFilterBtn").addEventListener("click", () => {
            document.getElementById("filterDifficulty").value = "";
            document.getElementById("filterType").value = "";
            browserPage = 1;
            applyFilters(1);
        });
    }
    filterBar.classList.toggle("hidden");
}

// Refresh filter bar text when language changes (elements are created dynamically)
function refreshFilterBarText() {
    const filterBar = document.getElementById("filterBar");
    if (!filterBar) return;
    const diffSel = document.getElementById("filterDifficulty");
    const typeSel = document.getElementById("filterType");
    const applyBtn = document.getElementById("applyFilterBtn");
    const clearBtn = document.getElementById("clearFilterBtn");
    if (diffSel) {
        diffSel.title = t("filterDifficulty");
        const opts = diffSel.querySelectorAll("option");
        const texts = [t("filterAllDifficulty"), t("diff1"), t("diff2"), t("diff3"),
                       t("diff4"), t("diff5"), t("diff6"), t("diff7")];
        opts.forEach((opt, i) => { if (texts[i]) opt.textContent = texts[i]; });
    }
    if (typeSel) {
        typeSel.title = t("filterAllType");
        const opt = typeSel.querySelector("option");
        if (opt) opt.textContent = t("filterAllType");
    }
    if (applyBtn) applyBtn.textContent = t("applyFilter");
    if (clearBtn) clearBtn.textContent = t("clearFilter");
}

function applyFilters(page) {
    page = page || browserPage || 1;
    const diffSel = document.getElementById("filterDifficulty");
    const diff = diffSel && diffSel.selectedOptions
        ? Array.from(diffSel.selectedOptions).map(o => o.value).filter(v => v !== "").join(",")
        : "";
    const typeF = document.getElementById("filterType").value;
    const keyword = searchInput.value.trim();

    apiCall("get_problems_page", keyword, diff, typeF, "", page, BROWSER_PAGE_SIZE)
        .then(data => {
            if (data.success) {
                browserPage = page;
                renderFilteredResults(data.problems, data.filteredCount, data.total,
                                      data.page, data.totalPages);
            }
        })
        .catch(err => {
            showStatus("error", err.message || t("errorFilterFailed"));
        });
}

function renderFilteredResults(problems, filteredCount, total, page, totalPages) {
    const results = searchResults;
    results.classList.remove("hidden");
    if (!problems || problems.length === 0) {
        results.innerHTML = `<div class="placeholder"><p>${t("filterEmpty")}</p></div>`;
        return;
    }
    page = page || 1;
    totalPages = totalPages || 1;
    let html = `<div class="search-results-header">${t("filterResultCount", filteredCount, total)}</div>`;
    problems.forEach(p => {
        const pid = p.pid || "";
        const title = p.name || p.title || "";
        const diff = p.difficulty || 0;
        const diffColor = DIFFICULTY_COLORS[diff] || DIFFICULTY_COLORS[0];
        const diffName = getDifficultyName(diff);
        html += `<div class="search-result-item" data-pid="${escapeHtml(pid)}">
            <span class="search-result-pid">${escapeHtml(pid)}</span>
            <span class="search-result-title">${escapeHtml(title)}</span>
            <span class="diff-badge" style="background:${diffColor};color:${diffBadgeTextColor(diffColor)};padding:2px 8px;border-radius:4px;font-size:12px;">${diffName}</span>
        </div>`;
    });

    // Luogu-style pagination bar
    if (totalPages > 1) {
        html += `<div class="pagination-bar">`;
        if (page > 1) {
            html += `<button type="button" class="page-btn" data-page="1">${t("pageFirst")}</button>`;
            html += `<button type="button" class="page-btn" data-page="${page - 1}">${t("pagePrev")}</button>`;
        }
        // Show a window of page numbers around the current page
        const startPage = Math.max(1, page - 2);
        const endPage = Math.min(totalPages, page + 2);
        if (startPage > 1) {
            html += `<span class="page-ellipsis">...</span>`;
        }
        for (let p = startPage; p <= endPage; p++) {
            const active = p === page ? " active" : "";
            html += `<button type="button" class="page-btn${active}" data-page="${p}">${p}</button>`;
        }
        if (endPage < totalPages) {
            html += `<span class="page-ellipsis">...</span>`;
        }
        if (page < totalPages) {
            html += `<button type="button" class="page-btn" data-page="${page + 1}">${t("pageNext")}</button>`;
            html += `<button type="button" class="page-btn" data-page="${totalPages}">${t("pageLast")}</button>`;
        }
        html += `</div>`;
    }

    results.innerHTML = html;

    // Click handler: problem items
    results.querySelectorAll(".search-result-item").forEach(item => {
        item.addEventListener("click", () => {
            const pid = item.dataset.pid;
            if (pid) {
                problemIdInput.value = pid;
                analyzeBtn.click();
            }
        });
    });
    // Click handler: pagination buttons
    results.querySelectorAll(".page-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            applyFilters(parseInt(btn.dataset.page, 10));
        });
    });
}

// =========================================================================
// Loading & Status
// =========================================================================
function showLoading(text) {
    loadingText.textContent = text || t("loadingDefault");
    loadingOverlay.classList.remove("hidden");
}

function hideLoading() {
    loadingOverlay.classList.add("hidden");
}

function showStatus(type, message) {
    statusBar.className = `status-bar ${type}`;
    statusBar.textContent = message;
    statusBar.classList.remove("hidden");
}

function hideStatus() {
    statusBar.classList.add("hidden");
}

// =========================================================================
// Markdown rendering
// =========================================================================
// Open external links (http/https) in the system default browser instead of
// letting them navigate the pywebview window away. Once the window leaves the
// app's homepage there is no back button to return, so we keep the app window
// in place and hand the URL to the OS browser (which has tabs / back). In a
// plain browser (e.g. the test harness) this falls back to window.open.
function isExternalUrl(href) {
    return typeof href === "string" && /^https?:\/\//i.test(href);
}

function openExternalLink(url) {
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_external === "function") {
        try {
            window.pywebview.api.open_external(url);
        } catch (e) {
            // ignore - fall back to a new window if the bridge call fails
        }
        return;
    }
    try {
        window.open(url, "_blank", "noopener");
    } catch (e) {
        // ignore
    }
}

function bindExternalLinkGuard() {
    // Capture phase so we run before the app's own click handlers and before
    // any target's inline onclick (e.g. event.stopPropagation() on rows).
    document.addEventListener(
        "click",
        (event) => {
            const anchor = event.target && event.target.closest ? event.target.closest("a[href]") : null;
            if (!anchor) return;
            const href = anchor.getAttribute("href") || "";
            if (!isExternalUrl(href)) return;
            event.preventDefault();
            event.stopPropagation();
            openExternalLink(href);
        },
        true
    );
}

bindExternalLinkGuard();

// Protect LaTeX math (and fenced code blocks) from the Markdown parser.
// Marked strips backslashes and treats _ * as formatting inside math, which
// corrupts LaTeX before KaTeX can render it. Every math region is replaced by
// a placeholder token; the original LaTeX is restored afterwards as plain text
// (so special chars survive) for KaTeX's auto-render to pick up.
// Supported delimiters: $$...$$ (block), \[...\] (block), $...$ (inline),
// \(...\) (inline). Fenced code blocks are left untouched.
function protectBlockMath(content) {
    const mathBlocks = [];
    const codeRe = /```+[^\n]*\n[\s\S]*?\n```+/g;
    const blockMathRe = /\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]/g;
    // Inline $...$ must have non-space content, cannot cross lines, and must
    // not be an escaped dollar (e.g. prices like "$5 元" stay literal).
    // Note: no negative lookbehind — Electron's V8 may not support it.
    const inlineRe = /\\\([\s\S]*?\\\)|\$([^\s$]([^$\n]*[^\s$])?)\$/g;

    // Math regexes are run only on non-code segments.
    const segments = [];
    let segLast = 0;
    let cm;
    while ((cm = codeRe.exec(content)) !== null) {
        segments.push({ text: content.slice(segLast, cm.index), isCode: false });
        segments.push({ text: cm[0], isCode: true });
        segLast = cm.index + cm[0].length;
    }
    segments.push({ text: content.slice(segLast), isCode: false });

    const protect = (seg) => {
        // Temporarily mask escaped dollars (\$ = literal $) so the inline
        // matcher does not treat prices like "\$5 元" as math.
        const escaped = [];
        const masked = seg.replace(/\\\$/g, () => {
            escaped.push("\\$");
            return "@@ESC" + (escaped.length - 1) + "@@";
        });
        // First protect block math ($$...$$ / \[...\]) so an unmatched $ inside
        // a \[...\] block is not swallowed by the inline matcher.
        let out = "";
        let last = 0;
        let m;
        blockMathRe.lastIndex = 0;
        while ((m = blockMathRe.exec(masked)) !== null) {
            out += masked.slice(last, m.index);
            mathBlocks.push(m[0]);
            out += "@@MATH" + (mathBlocks.length - 1) + "@@";
            last = m.index + m[0].length;
        }
        out += masked.slice(last);
        // Then protect inline math on the remainder.
        let out2 = "";
        let last2 = 0;
        let m2;
        inlineRe.lastIndex = 0;
        while ((m2 = inlineRe.exec(out)) !== null) {
            out2 += out.slice(last2, m2.index);
            mathBlocks.push(m2[0]);
            out2 += "@@MATH" + (mathBlocks.length - 1) + "@@";
            last2 = m2.index + m2[0].length;
        }
        out2 += out.slice(last2);
        // Restore escaped dollars.
        return out2.replace(/@@ESC(\d+)@@/g, (_, i) => escaped[Number(i)] || "");
    };

    let out = "";
    for (const seg of segments) {
        out += seg.isCode ? seg.text : protect(seg.text);
    }
    return { content: out, mathBlocks };
}

// Strip the LaTeX delimiters so only the formula body reaches KaTeX.
function texFromDelimiters(raw) {
    if (raw.startsWith("$$") && raw.endsWith("$$")) return raw.slice(2, -2);
    if (raw.startsWith("\\[") && raw.endsWith("\\]")) return raw.slice(2, -2);
    if (raw.startsWith("\\(") && raw.endsWith("\\)")) return raw.slice(2, -2);
    if (raw.length > 1 && raw[0] === "$" && raw[raw.length - 1] === "$") return raw.slice(1, -1);
    return raw;
}

// `$$...$$` and `\[...\]` render as display (block) math.
function isDisplayMath(raw) {
    return raw.startsWith("$$") || raw.startsWith("\\[");
}

function renderMarkdown(content) {
    if (!content) return `<p style='color:var(--muted)'>${t("noContent")}</p>`;
    // Keep $$...$$ LaTeX intact through the Markdown parser.
    const protectedResult = protectBlockMath(content);
    const html = marked.parse(protectedResult.content);
    const wrapper = document.createElement("div");
    wrapper.innerHTML = html;
    // Restore the original LaTeX and render each formula directly with KaTeX.
    // This avoids relying on auto-render's aggressive $ matching, which would
    // turn literal prices ("价格 $5 和 $10") into math.
    if (protectedResult.mathBlocks.length) {
        const mathRe = /@@MATH(\d+)@@/g;
        const walker = document.createTreeWalker(wrapper, NodeFilter.SHOW_TEXT);
        const targets = [];
        while (walker.nextNode()) {
            if (walker.currentNode.nodeValue.indexOf("@@MATH") !== -1) {
                targets.push(walker.currentNode);
            }
        }
        targets.forEach((node) => {
            const text = node.nodeValue;
            const frag = document.createDocumentFragment();
            let last = 0;
            let m;
            mathRe.lastIndex = 0;
            while ((m = mathRe.exec(text)) !== null) {
                if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
                const raw = protectedResult.mathBlocks[Number(m[1])];
                if (raw != null && typeof katex !== "undefined") {
                    const rendered = katex.renderToString(texFromDelimiters(raw), {
                        displayMode: isDisplayMath(raw),
                        throwOnError: false,
                    });
                    const tmp = document.createElement("span");
                    tmp.innerHTML = rendered;
                    while (tmp.firstChild) frag.appendChild(tmp.firstChild);
                }
                last = m.index + m[0].length;
            }
            if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
            if (frag.firstChild) node.parentNode.replaceChild(frag, node);
        });
    }
    wrapper.querySelectorAll("pre code").forEach((block) => {
        try {
            hljs.highlightElement(block);
        } catch (e) {
            // ignore highlight errors
        }
        // Wrap each code block in a container with a copy button
        const pre = block.parentElement;
        if (pre && pre.tagName === "PRE" && !pre.parentElement.classList.contains("code-block-wrap")) {
            const wrap = document.createElement("div");
            wrap.className = "code-block-wrap";
            pre.parentNode.insertBefore(wrap, pre);
            // Build copy button
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "copy-btn code-copy-btn";
            btn.title = t("copyText");
            btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg><span class="copy-text">${t("copyText")}</span>`;
            btn.addEventListener("click", () => {
                copyToClipboard(block.textContent, btn);
            });
            wrap.appendChild(btn);
            wrap.appendChild(pre);
        }
    });
    // Math was already rendered above via katex.renderToString (no auto-render,
    // so literal $ signs like prices are never mistaken for math).
    return wrapper.innerHTML;
}

// =========================================================================
// Render: Problem Info
// =========================================================================

// Format Luogu time limit list (ms per subtask) as "1.00s" (uses the max).
function formatLimitTime(list) {
    if (!list || !list.length) return "--";
    const maxMs = Math.max(...list.map((v) => Number(v) || 0));
    if (maxMs <= 0) return "--";
    return (maxMs / 1000).toFixed(2) + "s";
}

// Format Luogu memory limit list (KB per subtask) as "125.00MB" / "2.00GB".
function formatLimitMemory(list) {
    if (!list || !list.length) return "--";
    const maxKB = Math.max(...list.map((v) => Number(v) || 0));
    if (maxKB <= 0) return "--";
    if (maxKB >= 1024 * 1024) return (maxKB / 1024 / 1024).toFixed(2) + "GB";
    return (maxKB / 1024).toFixed(2) + "MB";
}

// Format a number with thousand separators (e.g. 260189 -> "260,189").
function formatNum(n) {
    n = Number(n) || 0;
    return n.toLocaleString("en-US");
}

// Add a "copy code" button to every <pre> code block inside a rendered
// markdown container (题解/题目/分析中的代码块一键复制).
function bindCodeCopy(container) {
    if (!container) return;
    container.querySelectorAll("pre").forEach((pre) => {
        if (pre.querySelector(".code-copy-btn") || pre.closest(".code-editor-wrap")) return;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "code-copy-btn";
        btn.title = t("copyText");
        btn.innerHTML = `
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>`;
        btn.addEventListener("click", () => {
            const codeEl = pre.querySelector("code");
            copyToClipboard((codeEl || pre).textContent, btn);
        });
        pre.classList.add("has-copy");
        pre.appendChild(btn);
    });
}

// Build a Luogu-style Markdown document for a problem (used by the
// "复制 Markdown" button in the problem header).
function buildProblemMarkdown(p) {
    const url = `https://www.luogu.com.cn/problem/${encodeURIComponent(p.pid || "")}`;
    const lines = [`# [${p.pid} ${p.title}](${url})`, ""];
    if (p.background) {
        lines.push(`## ${t("background")}`, "", p.background, "");
    }
    lines.push(`## ${t("description")}`, "", p.description || "", "");
    lines.push(`## ${t("inputFormat")}`, "", p.inputFormat || "", "");
    lines.push(`## ${t("outputFormat")}`, "", p.outputFormat || "", "");
    if (p.samples && p.samples.length) {
        p.samples.forEach((s, i) => {
            lines.push(
                `## ${t("samples")} #${i + 1}`, "",
                `### ${t("sampleInput")} ${i + 1}`, "",
                "```text", s.in || "", "```", "",
                `### ${t("sampleOutput")} ${i + 1}`, "",
                "```text", s.out || "", "```", ""
            );
        });
    }
    if (p.hint) {
        lines.push(`## ${t("hint")}`, "", p.hint, "");
    }
    return lines.join("\n");
}

function renderProblem(problem) {
    const diff = getDifficultyName(problem.difficulty);
    // AtCoder problems get explicit translation-direction buttons (to Chinese / to English)
    const isAtcoder = /^AT_/i.test(String(problem.pid || ""));

    let tagsHtml = "";
    if (problem.tags && problem.tags.length > 0) {
        tagsHtml = problem.tags
            .map((t) => `<span class="tag">${escapeHtml(String(t))}</span>`)
            .join("");
    }

    let samplesHtml = "";
    if (problem.samples && problem.samples.length > 0) {
        samplesHtml = problem.samples
            .map(
                (s, i) => `
            <div class="sample-block">
                <div class="sample-label">
                    <span>${t("sampleInput")} ${i + 1}</span>
                    <button type="button" class="copy-btn sample-copy-btn" data-copy-target="sample-in-${i}" title="${t("copyInput")}">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                        <span class="copy-text">${t("copyText")}</span>
                    </button>
                </div>
                <div class="sample-content" id="sample-in-${i}">${escapeHtml(s.in || "")}</div>
                <div class="sample-label">
                    <span>${t("sampleOutput")} ${i + 1}</span>
                    <button type="button" class="copy-btn sample-copy-btn" data-copy-target="sample-out-${i}" title="${t("copyOutput")}">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                        <span class="copy-text">${t("copyText")}</span>
                    </button>
                </div>
                <div class="sample-content" id="sample-out-${i}">${escapeHtml(s.out || "")}</div>
            </div>`
            )
            .join("");
    }

    let html = `
    <div class="problem-header">
        <div class="problem-title-wrap">
            <div class="problem-title">${escapeHtml(problem.pid)} · ${escapeHtml(problem.title)}</div>
            <div class="problem-title-actions">
                <button type="button" class="copy-btn problem-translate-btn" data-target="auto" title="${t("translateBtn")}" data-translate-state="off">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.87 15.07a10 10 0 1 1 2.2-2.2"></path><path d="M9 11h6M10 8h4M11 5h2"></path><path d="m7 11-2 2-2-2M5 11v9M17 5l2 2 2-2M19 7v3"></path></svg>
                    <span class="copy-text">${t("translateBtn")}</span>
                </button>
                ${isAtcoder ? `
                <button type="button" class="copy-btn problem-translate-btn" data-target="zh" title="${t("translateToZh")}" data-translate-state="off">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.87 15.07a10 10 0 1 1 2.2-2.2"></path><path d="M9 11h6M10 8h4M11 5h2"></path><path d="m7 11-2 2-2-2M5 11v9M17 5l2 2 2-2M19 7v3"></path></svg>
                    <span class="copy-text">${t("translateToZh")}</span>
                </button>
                <button type="button" class="copy-btn problem-translate-btn" data-target="en" title="${t("translateToEn")}" data-translate-state="off">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.87 15.07a10 10 0 1 1 2.2-2.2"></path><path d="M9 11h6M10 8h4M11 5h2"></path><path d="m7 11-2 2-2-2M5 11v9M17 5l2 2 2-2M19 7v3"></path></svg>
                    <span class="copy-text">${t("translateToEn")}</span>
                </button>` : ""}
                <button type="button" class="copy-btn problem-copy-md-btn" title="${t("copyProblemMd")}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                    <span class="copy-text">${t("copyProblemMd")}</span>
                </button>
                ${collectBtnHtml(problem.pid, problem.title, problem.difficulty)}
                ${buildProblemLinksHtml(problem.pid)}
            </div>
        </div>
        <div class="problem-meta">
            <span>${t("difficulty")}: <strong>${diff}</strong></span>
            ${problem.source ? `<span>${t("source")}: <strong>${escapeHtml(problem.source)}</strong></span>` : ""}
            <span>${t("timeLimit")}: <strong>${formatLimitTime(problem.timeLimit)}</strong></span>
            <span>${t("memoryLimit")}: <strong>${formatLimitMemory(problem.memoryLimit)}</strong></span>
            ${problem.totalSubmit > 0 ? `
            <span>${t("submitCount")}: <strong>${formatNum(problem.totalSubmit)}</strong></span>
            <span>${t("acceptCount")}: <strong>${formatNum(problem.totalAccepted)}</strong></span>
            <span>${t("passRate")}: <strong>${(problem.totalAccepted / problem.totalSubmit * 100).toFixed(1)}%</strong></span>` : ""}
            ${tagsHtml}
        </div>
    </div>
    <div id="problemTranslationPanel" class="problem-translation-panel hidden"></div>
    <div class="markdown-body">`;

    if (problem.background) {
        html += `<h3>${t("background")}</h3>${renderMarkdown(problem.background)}`;
    }
    html += `<h3>${t("description")}</h3>${renderMarkdown(problem.description)}`;
    html += `<h3>${t("inputFormat")}</h3>${renderMarkdown(problem.inputFormat)}`;
    html += `<h3>${t("outputFormat")}</h3>${renderMarkdown(problem.outputFormat)}`;
    if (samplesHtml) {
        html += `<h3>${t("samples")}</h3>${samplesHtml}`;
    }
    if (problem.hint) {
        html += `<h3>${t("hint")}</h3>${renderMarkdown(problem.hint)}`;
    }
    html += `</div>`;

    // Recommended problems with similar knowledge points (Luogu's 推荐题目)
    if (problem.recommendations && problem.recommendations.length > 0) {
        html += `
        <div class="recommend-section">
            <div class="recommend-title">${t("recommendTitle")}</div>
            <div class="recommend-list">
                ${problem.recommendations.map((r) => {
                    const d = Number(r.difficulty) || 0;
                    const color = DIFFICULTY_COLORS[d] || DIFFICULTY_COLORS[0];
                    return `
                <button type="button" class="recommend-item" data-pid="${escapeHtml(r.pid)}" title="${t("recommendOpen")}">
                    <span class="diff-badge" style="background:${color};color:${diffBadgeTextColor(color)}">${escapeHtml(getDifficultyName(d))}</span>
                    <span class="recommend-pid">${escapeHtml(r.pid)}</span>
                    <span class="recommend-name">${escapeHtml(r.title || "")}</span>
                </button>`;
                }).join("")}
            </div>
        </div>`;
    }

    problemContent.innerHTML = html;
    bindCopyButtons(problemContent);
    bindCodeCopy(problemContent);

    // Copy problem Markdown button
    const copyMdBtn = problemContent.querySelector(".problem-copy-md-btn");
    if (copyMdBtn) {
        copyMdBtn.addEventListener("click", () => {
            copyToClipboard(buildProblemMarkdown(problem), copyMdBtn);
        });
    }

    // AI translate problem buttons (题库/题目翻译) - one per translation direction
    problemContent.querySelectorAll(".problem-translate-btn").forEach((translateBtn) => {
        translateBtn.addEventListener("click", () => toggleProblemTranslation(problem, translateBtn));
    });

    // Recommended problems -> open the problem in-app
    problemContent.querySelectorAll(".recommend-item").forEach((btn) => {
        btn.addEventListener("click", () => {
            const pid = btn.dataset.pid;
            if (!pid) return;
            problemIdInput.value = pid;
            searchResults.classList.add("hidden");
            loadProblemOnly(pid);
        });
    });

    // Collect button in the problem header
    const collectBtn = problemContent.querySelector(".collect-btn");
    if (collectBtn) attachCollectBtn(collectBtn);
    refreshCollectButtons();
}

// =========================================================================
// AI Translation (题库/题目翻译)
// =========================================================================
let problemTranslationCache = null; // {target, text} for the current problem

// Build a plain-text snapshot of the problem statement for translation.
function buildProblemTranslationSource(problem) {
    const sections = [];
    if (problem.background) sections.push(`## ${t("background")}\n${problem.background}`);
    sections.push(`## ${t("description")}\n${problem.description}`);
    if (problem.inputFormat) sections.push(`## ${t("inputFormat")}\n${problem.inputFormat}`);
    if (problem.outputFormat) sections.push(`## ${t("outputFormat")}\n${problem.outputFormat}`);
    if (problem.hint) sections.push(`## ${t("hint")}\n${problem.hint}`);
    return sections.join("\n\n");
}

// Default label of a translate button (based on its target direction)
function translateBtnLabel(btn) {
    const target = btn.dataset ? btn.dataset.target : "";
    if (target === "zh") return t("translateToZh");
    if (target === "en") return t("translateToEn");
    return t("translateBtn");
}

// Reset every translate button to its off (idle) label/state
function setAllTranslateButtonsOff() {
    document.querySelectorAll(".problem-translate-btn").forEach((b) => {
        b.setAttribute("data-translate-state", "off");
        const l = b.querySelector(".copy-text");
        if (l) l.textContent = translateBtnLabel(b);
    });
}

// Mark only the active button as "on" (showing translation); others idle
function setAllTranslateButtonsOn(activeBtn) {
    document.querySelectorAll(".problem-translate-btn").forEach((b) => {
        const on = b === activeBtn;
        b.setAttribute("data-translate-state", on ? "on" : "off");
        const l = b.querySelector(".copy-text");
        if (l) l.textContent = on ? t("translateShowOriginal") : translateBtnLabel(b);
    });
}

// Translate the problem statement with the bound AI model and render the
// result into a panel below the original text. Clicking again toggles.
// The target is read from the button's data-target ("zh"/"en"/"auto");
// "auto" follows the UI language (zh UI -> en, otherwise -> zh).
async function toggleProblemTranslation(problem, btn) {
    const panel = document.getElementById("problemTranslationPanel");
    if (!panel) return;
    const state = btn.getAttribute("data-translate-state") || "off";

    const explicit = btn.dataset && btn.dataset.target;
    const target = explicit && explicit !== "auto"
        ? explicit
        : (currentLang === "zh" ? "en" : "zh");

    if (state === "on") {
        // Hide the translation panel
        panel.classList.add("hidden");
        panel.innerHTML = "";
        setAllTranslateButtonsOff();
        return;
    }

    if (problemTranslationCache && problemTranslationCache.target === target) {
        renderProblemTranslationPanel(problemTranslationCache.text);
        setAllTranslateButtonsOn(btn);
        return;
    }

    const source = buildProblemTranslationSource(problem);
    if (!source.trim()) {
        showToast(t("translateNoContent"), "error");
        return;
    }
    panel.classList.remove("hidden");
    panel.innerHTML = `<div class="profile-loading" style="padding:16px 0;"><div class="spinner"></div><p>${escapeHtml(t("translateLoading"))}</p></div>`;
    const label = btn.querySelector(".copy-text");
    if (label) label.textContent = t("translateLoading");

    try {
        const data = await apiCall("translate", source, target);
        problemTranslationCache = { target, text: data.translation || "" };
        renderProblemTranslationPanel(problemTranslationCache.text);
        setAllTranslateButtonsOn(btn);
        showToast(t("translateSuccess"), "success");
    } catch (err) {
        panel.classList.add("hidden");
        setAllTranslateButtonsOff();
        showToast(t("translateFailed", err.message), "error");
    }
}

function renderProblemTranslationPanel(text) {
    const panel = document.getElementById("problemTranslationPanel");
    if (!panel) return;
    panel.classList.remove("hidden");
    panel.innerHTML = `
        <div class="problem-translation-head">
            <span class="problem-translation-tag">${escapeHtml(t("translateTitle"))}</span>
        </div>
        <div class="markdown-body">${renderMarkdown(text || "")}</div>`;
}

// =========================================================================
// Render: Solutions
// =========================================================================
function renderSolutions(solutions, total) {
    if (!solutions || solutions.length === 0) {
        solutionsContent.innerHTML = `
            <div class="placeholder">
                <p>${t("noSolutions")}</p>
                <p class="placeholder-sub">${t("noSolutionsSub")}</p>
            </div>`;
        return;
    }

    let html = `
        <div class="status-bar info" style="margin-bottom:16px;">
            ${t("solutionsSummary", total, solutions.length)}
        </div>
        <div class="solution-compare-bar" style="display:flex;gap:8px;align-items:center;margin-bottom:8px;">
            <button id="compareSolutionsBtn" class="btn-secondary" disabled style="padding:4px 12px;font-size:13px;">${t("compareBtn")}</button>
            <span id="compareHint" style="color:var(--muted);font-size:12px;">${t("compareHint")}</span>
        </div>
    `;

    solutions.forEach((sol, idx) => {
        const scoreClass = sol.score >= 30 ? "high" : sol.score >= 15 ? "mid" : "low";
        const codeBadge = sol.has_code
            ? `<span class="code-badge">${t("codeBadge", sol.code_blocks.length)}</span>`
            : `<span class="code-badge none">${t("noCodeBadge")}</span>`;

        const initial = (sol.author || "?").charAt(0).toUpperCase();
        const solContent = sol.content || "";
        const solContentAttr = escapeHtml(solContent).replace(/"/g, "&quot;");

        html += `
        <div class="solution-card">
            <div class="solution-card-header">
                <div class="solution-author">
                    <input type="checkbox" class="solution-compare-cb" data-sol-idx="${idx}" style="margin-right:8px;">
                    <div class="solution-author-avatar">${initial}</div>
                    <div>
                        <div class="solution-author-name">${escapeHtml(sol.author)}</div>
                        <div class="solution-meta">${t("solutionMeta", idx + 1, sol.score)}</div>
                    </div>
                </div>
                <div class="solution-score">
                    <span class="score-badge ${scoreClass}">${t("solutionScore", sol.score)}</span>
                    ${codeBadge}
                    <button type="button" class="copy-btn md-copy-btn" data-md-content="${solContentAttr}" title="${t("copyMd")}">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                        <span class="copy-text">${t("copyMd")}</span>
                    </button>
                </div>
            </div>
            <div class="markdown-body">${renderMarkdown(sol.content)}</div>
        </div>`;
    });

    solutionsContent.innerHTML = html;
    bindCodeCopy(solutionsContent);

    // Bind copy-markdown buttons on solution cards
    solutionsContent.querySelectorAll(".md-copy-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            copyToClipboard(btn.dataset.mdContent || "", btn);
        });
    });

    // Bind compare checkbox logic
    bindCompareCheckboxes();
}

// =========================================================================
// Solution Comparison
// =========================================================================
function bindCompareCheckboxes() {
    const cbs = solutionsContent.querySelectorAll(".solution-compare-cb");
    const btn = document.getElementById("compareSolutionsBtn");
    const hint = document.getElementById("compareHint");
    if (!btn || !hint) return;

    function updateCompareState() {
        const checked = solutionsContent.querySelectorAll(".solution-compare-cb:checked");
        if (checked.length === 2) {
            btn.disabled = false;
            hint.textContent = t("compareHint");
        } else {
            btn.disabled = true;
            hint.textContent = t("compareHint");
        }
    }

    cbs.forEach((cb) => {
        cb.addEventListener("change", () => {
            const checked = solutionsContent.querySelectorAll(".solution-compare-cb:checked");
            if (checked.length > 2) {
                cb.checked = false;
                hint.textContent = t("compareNeedTwo");
                setTimeout(() => updateCompareState(), 1200);
                return;
            }
            updateCompareState();
        });
    });

    btn.addEventListener("click", () => {
        const checked = solutionsContent.querySelectorAll(".solution-compare-cb:checked");
        if (checked.length !== 2) return;
        const idx1 = parseInt(checked[0].dataset.solIdx, 10);
        const idx2 = parseInt(checked[1].dataset.solIdx, 10);
        const sol1 = currentSolutions && currentSolutions[idx1];
        const sol2 = currentSolutions && currentSolutions[idx2];
        if (sol1 && sol2) {
            openCompare(sol1, sol2);
        }
    });
}

function createCompareModal() {
    if (document.getElementById("compareModal")) return;
    const modal = document.createElement("div");
    modal.id = "compareModal";
    modal.className = "training-modal hidden";
    modal.innerHTML = `
        <div class="training-dialog" style="max-width:90vw;width:1200px;">
            <div class="training-header">
                <div>
                    <h3>${t("compareTitle")}</h3>
                    <p class="training-subtitle">${t("compareSubtitle")}</p>
                </div>
                <button type="button" class="modal-close-btn" id="compareCloseBtn" title="×">&times;</button>
            </div>
            <div id="compareBody" class="training-body" style="display:flex;gap:16px;max-height:70vh;overflow:hidden;">
                <div id="compareLeft" class="compare-col" style="flex:1;overflow-y:auto;padding:8px;border:1px solid var(--border);border-radius:8px;"></div>
                <div id="compareRight" class="compare-col" style="flex:1;overflow-y:auto;padding:8px;border:1px solid var(--border);border-radius:8px;"></div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    document.getElementById("compareCloseBtn").addEventListener("click", () => modal.classList.add("hidden"));
    modal.addEventListener("click", (e) => {
        if (e.target === modal) modal.classList.add("hidden");
    });
}

function openCompare(sol1, sol2) {
    createCompareModal();
    const modal = document.getElementById("compareModal");
    const left = document.getElementById("compareLeft");
    const right = document.getElementById("compareRight");

    left.innerHTML = `<div class="solution-card" style="border:none;padding:0;">${renderMarkdown(sol1.content || "")}</div>`;
    right.innerHTML = `<div class="solution-card" style="border:none;padding:0;">${renderMarkdown(sol2.content || "")}</div>`;

    // Apply syntax highlighting for code blocks that renderMarkdown may have missed
    left.querySelectorAll("pre code").forEach((block) => {
        try { hljs.highlightElement(block); } catch (e) {}
    });
    right.querySelectorAll("pre code").forEach((block) => {
        try { hljs.highlightElement(block); } catch (e) {}
    });

    modal.classList.remove("hidden");
}

// =========================================================================
// Render: AI Analysis
// =========================================================================
function renderAnalysis(analysis, modelName) {
    let html = `
        <div class="status-bar success" style="margin-bottom:16px;">
            ${t("analysisComplete", escapeHtml(modelName))}
        </div>`;

    const analysisAttr = escapeHtml(analysis || "").replace(/"/g, "&quot;");
    html += `
        <div class="analysis-section">
            <div class="analysis-section-title">
                ${t("analysisSectionTitle")}
                <button type="button" class="copy-btn md-copy-btn" data-md-content="${analysisAttr}" title="${t("copyMd")}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                    <span class="copy-text">${t("copyMd")}</span>
                </button>
            </div>
            <div class="markdown-body">${renderMarkdown(analysis)}</div>
        </div>`;
    analysisContent.innerHTML = html;
    bindCodeCopy(analysisContent);

    // Bind copy-markdown button on analysis section
    analysisContent.querySelectorAll(".md-copy-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            copyToClipboard(btn.dataset.mdContent || "", btn);
        });
    });
}

function renderAnalysisPlaceholder(message, subMessage) {
    analysisContent.innerHTML = `
        <div class="placeholder">
            <p>${escapeHtml(message)}</p>
            ${subMessage ? `<p class="placeholder-sub">${escapeHtml(subMessage)}</p>` : ""}
        </div>`;
}

// =========================================================================
// API calls via pywebview JS-Python bridge (no HTTP server needed)
// =========================================================================
// pywebview exposes window.pywebview.api.<method>(args...) which returns a
// Promise resolving to the Python dict. We wrap it to enforce the same
// { success, error, ... } contract the old fetch-based helpers used.

function pyApi() {
    // window.pywebview.api is injected by pywebview after the window loads.
    // During early init it may be undefined; callers handle the rejection.
    if (!window.pywebview || !window.pywebview.api) {
        return Promise.reject(new Error("pywebview API not ready"));
    }
    return window.pywebview.api;
}

async function apiCall(method, ...args) {
    const api = await pyApi();
    const fn = api[method];
    if (typeof fn !== "function") {
        throw new Error(`Unknown API method: ${method}`);
    }
    const data = await fn(...args);
    if (!data || !data.success) {
        const err = new Error((data && data.error) || t("requestFailed", "?"));
        // Carry the backend's "captcha required" flag so the caller can show
        // the captcha modal instead of relying on error-string matching.
        if (data && data.captchaRequired) err.captchaRequired = true;
        throw err;
    }
    return data;
}

// Convenience wrappers preserving the old apiGet/apiPost call sites
async function apiGet(url) {
    // Map URL paths to pywebview API methods
    if (url.startsWith("/api/config")) {
        return apiCall("get_config");
    }
    if (url.startsWith("/api/languages")) {
        return apiCall("get_languages");
    }
    if (url.startsWith("/api/default-problems")) {
        let pm = url.match(/[?&]page=(\d+)/);
        return apiCall("get_default_problems", pm ? parseInt(pm[1], 10) : 1);
    }
    let m = url.match(/^\/api\/problem\/(.+)$/);
    if (m) return apiCall("get_problem", decodeURIComponent(m[1]));
    m = url.match(/^\/api\/search\?q=(.+)$/);
    if (m) return apiCall("search", decodeURIComponent(m[1]));
    m = url.match(/^\/api\/practice\?cookie=(.+)$/);
    if (m) return apiCall("get_practice", decodeURIComponent(m[1]));
    m = url.match(/^\/api\/solutions\/([^?]+)(?:\?cookie=(.+))?$/);
    if (m) return apiCall("get_solutions", decodeURIComponent(m[1]), m[2] ? decodeURIComponent(m[2]) : "");
    m = url.match(/^\/api\/record\/(\d+)\?cookie=(.+)$/);
    if (m) return apiCall("get_record", parseInt(m[1], 10), decodeURIComponent(m[2]));
    m = url.match(/^\/api\/atcoder-search\?q=(.*?)(?:&page=(\d+))?$/);
    if (m) return apiCall("atcoder_search", decodeURIComponent(m[1]), m[2] ? parseInt(m[2], 10) : 1);
    m = url.match(/^\/api\/atcoder-problem\/(.+)$/);
    if (m) return apiCall("get_atcoder_problem", decodeURIComponent(m[1]));
    throw new Error("Unknown GET API: " + url);
}

async function apiPost(url, body) {
    if (url === "/api/captcha") {
        return apiCall("get_captcha", body.pid, body.cookie, body.contestId || "");
    }
    if (url === "/api/submit") {
        return apiCall("submit", body.pid, body.code, body.lang, body.cookie,
            body.enableO2, body.verify, body.sessionCookies, body.csrfToken,
            body.contestId || "", body.captchaId || "");
    }
    if (url === "/api/analyze") {
        return apiCall("analyze", body.api_key, body.model, body.problem, body.solutions);
    }
    throw new Error("Unknown POST API: " + url);
}

// =========================================================================
// Unsaved code draft (autosave) helpers
// =========================================================================
function setDraftStatus(text) {
    if (draftStatusEl) draftStatusEl.textContent = text || "";
}

// Persist a code draft to the backend; empty code removes the draft.
async function persistDraft(pid, code) {
    if (!pid) return false;
    try {
        return await apiCall("save_draft", pid, code);
    } catch (err) {
        console.warn("Failed to save draft:", err);
        return false;
    }
}

// Fetch the saved draft for a problem (empty string if none).
async function fetchDraft(pid) {
    if (!pid) return "";
    try {
        const data = await apiCall("get_draft", pid);
        return data.code || "";
    } catch (err) {
        console.warn("Failed to load draft:", err);
        return "";
    }
}

// The problem the code editor content currently belongs to.
function draftTargetPid() {
    if (draftPid) return draftPid;
    return currentProblem ? currentProblem.pid : "";
}

// Save the current editor content as a draft. Shared by the manual save
// button, the 30s timer and the switch-problem flow.
async function saveCurrentDraft(showFeedback) {
    const pid = draftTargetPid();
    const code = codeEditor.value;
    if (!pid || !code.trim()) return false;
    const ok = await persistDraft(pid, code);
    if (ok) draftPid = pid;
    if (showFeedback) {
        setDraftStatus(ok ? t("draftSaved", new Date().toLocaleTimeString()) : t("draftSaveFailed"));
    }
    return ok;
}

// =========================================================================
// User profile (avatar + name + practice detail)
// =========================================================================
function getDifficultyNames() {
    return [t("diff0"), t("diff1"), t("diff2"), t("diff3"),
            t("diff4"), t("diff5"), t("diff6"), t("diff7"), t("diff8")];
}

// Fetch user info from backend and update header avatar/name.
async function syncUserProfile() {
    const cookie = (luoguCookieInput.value || "").trim();
    if (!cookie) {
        userProfileArea.classList.add("hidden");
        userInfoCache = null;
        return;
    }
    try {
        const data = await apiCall("get_user_info", cookie);
        const user = data.user;
        if (!user || !user.name) return;
        userInfoCache = user;
        // Avatar may be a relative path; prepend Luogu CDN if needed
        let avatarUrl = user.avatar || "";
        if (avatarUrl && !avatarUrl.startsWith("http")) {
            avatarUrl = "https://cdn.luogu.com.cn" + (avatarUrl.startsWith("/") ? "" : "/") + avatarUrl;
        }
        userAvatar.src = avatarUrl;
        userName.textContent = user.name;
        userProfileArea.classList.remove("hidden");
    } catch (err) {
        console.warn("syncUserProfile failed:", err);
        // Fallback: keep 个人中心 accessible even when the info fetch is
        // temporarily blocked (e.g. Luogu 403/限流) by showing the uid
        // parsed from the cookie. The modal can still load practice data.
        const m = cookie.match(/_uid=(\d+)/);
        if (m) {
            userInfoCache = { uid: m[1], name: `UID ${m[1]}`, avatar: "" };
            userAvatar.src = "";
            userName.textContent = `UID ${m[1]}`;
            userProfileArea.classList.remove("hidden");
        } else {
            userProfileArea.classList.add("hidden");
            userInfoCache = null;
        }
    }
}

// Hide the per-section loading spinner inside a container (chart wrap, list...)
function hideSectionSpinner(container) {
    if (!container) return;
    const sp = container.querySelector(".section-spinner");
    if (sp) sp.classList.add("hidden");
}

// Reset all profile section spinners when the modal opens (re-show loading)
function resetProfileSectionSpinners() {
    // Clear leftover retry-error overlays and reset every section to its
    // spinner state before the next load.
    document.querySelectorAll(".section-error").forEach((el) => el.remove());
    document.querySelectorAll(".profile-chart-wrap").forEach((el) => {
        el.style.display = "";
    });
    document.querySelectorAll(".section-spinner").forEach((el) => el.classList.remove("hidden"));
    if (recentBody) {
        recentBody.innerHTML = `<tr><td colspan="6"><div class="section-spinner"><div class="spinner"></div></div></td></tr>`;
    }
}

// Switch the active profile category tab and resize any visible charts
function switchProfileTab(name) {
    document.querySelectorAll(".profile-tab").forEach((tb) => {
        tb.classList.toggle("active", tb.dataset.profileTab === name);
    });
    document.querySelectorAll(".profile-tab-panel").forEach((p) => {
        p.classList.toggle("active", p.dataset.profilePanel === name);
    });
    
    // Load data for the active tab (lazy loading: each section fetches only
    // when first opened, and stays cached in memory for the session).
    if (name === "stats" && !profileStatsLoaded) {
        loadProfileHeatmap();
        profileStatsLoaded = true;
    } else if (name === "wrongbook" && !profileStatsLoaded) {
        loadProfileWrongBook();
        profileStatsLoaded = true;
    } else if (name === "trends" && !profileTrendLoaded) {
        loadProfileTrends();
        profileTrendLoaded = true;
    } else if (name === "tags" && !profileTagsLoaded) {
        loadProfileTags();
        profileTagsLoaded = true;
    } else if (name === "recent" && !profileRecentLoaded) {
        loadProfileRecent();
        profileRecentLoaded = true;
    }
    
    resizeProfileCharts();
}

// Load stats data when switching to stats tab
let heatmapCache = null;
async function loadProfileHeatmap(forceRefresh) {
    const statsSummary = document.getElementById("statsSummary");
    const statsHeatmap = document.getElementById("statsHeatmap");
    if (!statsSummary || !statsHeatmap) return;
    
    if (!forceRefresh && heatmapCache) {
        renderHeatmap(heatmapCache);
        return;
    }
    statsSummary.textContent = "...";
    statsHeatmap.innerHTML = "";
    
    try {
        const data = await apiCall("get_heatmap");
        heatmapCache = data;
        renderHeatmap(data);
    } catch (err) {
        statsSummary.textContent = "";
        statsHeatmap.innerHTML = `<div class="stats-empty">${escapeHtml(err.message || t("requestFailed", "?"))}</div>`;
    }
}

// Load wrong book data when switching to wrongbook tab
async function loadProfileWrongBook() {
    const wrongBookBody = document.getElementById("wrongBookBody");
    if (!wrongBookBody) return;
    
    wrongBookBody.innerHTML = `<div class="placeholder"><p>${escapeHtml(t("wrongBookLoading"))}</p></div>`;
    
    try {
        const data = await apiCall("get_wrong_book");
        const problems = data.problems || [];
        if (!problems.length) {
            wrongBookBody.innerHTML = `<div class="stats-empty">${escapeHtml(t("wrongBookEmpty"))}</div>`;
            return;
        }
        let html = `<div class="stats-summary">${escapeHtml(t("wrongBookCount", String(problems.length)))}</div>`;
        problems.forEach((p) => {
            const timeStr = p.lastTime ? new Date(p.lastTime * 1000).toLocaleString() : "";
            html += `
                <div class="wrong-book-item" data-pid="${escapeHtml(p.pid)}">
                    <span class="wrong-book-pid">${escapeHtml(p.pid)}</span>
                    <div class="wrong-book-info">
                        <div class="wrong-book-meta">${escapeHtml(t("wrongBookSubmissions", String(p.count)))} · ${escapeHtml(timeStr)}</div>
                        <div><span class="wrong-book-status">${escapeHtml(t("wrongBookLastStatus", p.lastStatusText || String(p.lastStatus)))}</span></div>
                    </div>
                    <div class="wrong-book-actions">
                        <button type="button" class="btn-secondary" data-action="open" style="padding:4px 10px;font-size:12px;">${escapeHtml(t("wrongBookOpen"))}</button>
                        <button type="button" class="btn-primary" data-action="explain" style="padding:4px 10px;font-size:12px;">${escapeHtml(t("wrongBookAnalyze"))}</button>
                    </div>
                </div>`;
        });
        wrongBookBody.innerHTML = html;
        wrongBookBody.querySelectorAll(".wrong-book-item").forEach((item) => {
            const pid = item.dataset.pid;
            item.querySelector('[data-action="open"]').addEventListener("click", () => {
                closeProfileModal();
                loadProblemOnly(pid);
            });
            item.querySelector('[data-action="explain"]').addEventListener("click", () => {
                explainWrongBookProblem(pid);
            });
        });
    } catch (err) {
        wrongBookBody.innerHTML = `<div class="stats-empty">${escapeHtml(t("wrongBookFailed", err.message))}</div>`;
    }
}

// Charts created while their panel is hidden render at zero size; resize on switch
function resizeProfileCharts() {
    [profileChart, profileTypeChart, profileTrendChart, profileWeekChart, profileTagChart]
        .forEach((c) => { if (c && typeof c.resize === "function") c.resize(); });
}

function openProfileModal() {
    if (!userInfoCache) return;
    profileViewUid = null;
    profileAvatar.src = userAvatar.src;
    profileName.textContent = userInfoCache.name;
    profileMeta.textContent = `UID: ${userInfoCache.uid}`;
    if (userInfoCache.ranking) {
        profileMeta.textContent += ` · ${t("profileRanking")}: #${userInfoCache.ranking}`;
    }
    if (userInfoCache.rating) {
        profileMeta.textContent += ` · ${t("profileRating")}: ${userInfoCache.rating}`;
    }
    renderProfileBanner(userInfoCache);
    renderProfileInfo(userInfoCache);
    profileHomeLink.classList.add("hidden");
    if (profileCollectionsTitle) profileCollectionsTitle.classList.remove("hidden");
    profileModal.classList.remove("hidden");
    profileLoading.classList.remove("hidden");
    profileContent.classList.add("hidden");
    switchProfileTab("overview");
    resetProfileSectionSpinners();
    loadPracticeDetail();
    renderProfileCollections();
}

// Open the profile modal showing ANOTHER user's homepage (from user search).
// Loads their info by UID and hides self-only sections (collections/export).
async function openUserHomepage(uid, name) {
    if (!uid) return;
    profileViewUid = uid;
    userSearchModal.classList.add("hidden");
    profileAvatar.src = "";
    profileName.textContent = name || `UID ${uid}`;
    profileMeta.textContent = `UID: ${uid}`;
    profileBanner.classList.add("hidden");
    profileInfo.innerHTML = "";
    profileHomeLink.href = `https://www.luogu.com.cn/user/${uid}`;
    profileHomeLink.classList.remove("hidden");
    if (profileCollectionsTitle) profileCollectionsTitle.classList.add("hidden");
    if (profileCollections) profileCollections.innerHTML = "";
    profileModal.classList.remove("hidden");
    profileLoading.classList.remove("hidden");
    profileContent.classList.add("hidden");
    switchProfileTab("overview");
    resetProfileSectionSpinners();
    try {
        const data = await apiCall("get_user_info_by_uid", uid);
        const user = data.user;
        if (!user) throw new Error(t("profileLoadFailed"));
        // Avatar may be a relative path; prepend Luogu CDN if needed
        let avatarUrl = user.avatar || "";
        if (avatarUrl && !avatarUrl.startsWith("http")) {
            avatarUrl = "https://cdn.luogu.com.cn" + (avatarUrl.startsWith("/") ? "" : "/") + avatarUrl;
        }
        profileAvatar.src = avatarUrl;
        profileName.textContent = user.name || name || `UID ${uid}`;
        let meta = `UID: ${uid}`;
        if (user.ranking) meta += ` · ${t("profileRanking")}: #${user.ranking}`;
        if (user.rating) meta += ` · ${t("profileRating")}: ${user.rating}`;
        profileMeta.textContent = meta;
        renderProfileBanner(user);
        renderProfileInfo(user);
    } catch (err) {
        // Still load the public sections even if the info fetch failed
        profileInfo.innerHTML = `<div class="profile-info-item wide"><span class="info-val">${escapeHtml(err && err.message || t("profileLoadFailed"))}</span></div>`;
    }
    loadPracticeDetail();
}

function closeProfileModal() {
    profileModal.classList.add("hidden");
    profileViewUid = null;
    resetLazyLoadingFlags();
    if (profileHomeLink) profileHomeLink.classList.add("hidden");
    if (profileCollectionsTitle) profileCollectionsTitle.classList.remove("hidden");
    if (profileChart) {
        profileChart.destroy();
        profileChart = null;
    }
    if (profileTypeChart) {
        profileTypeChart.destroy();
        profileTypeChart = null;
    }
    if (profileTrendChart) {
        profileTrendChart.destroy();
        profileTrendChart = null;
    }
    if (profileWeekChart) {
        profileWeekChart.destroy();
        profileWeekChart = null;
    }
    if (profileTagChart) {
        profileTagChart.destroy();
        profileTagChart = null;
    }
}

// Show the user's homepage background as a banner at the top of the profile modal
function renderProfileBanner(user) {
    if (user.background) {
        profileBanner.style.backgroundImage = `url("${user.background}")`;
        profileBanner.classList.remove("hidden");
    } else {
        profileBanner.style.backgroundImage = "";
        profileBanner.classList.add("hidden");
    }
}

function fmtTime(unixTs) {
    if (!unixTs) return "--";
    const d = new Date(unixTs * 1000);
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// Fill the profile info grid (slogan, levels, social counts, register time...)
function renderProfileInfo(user) {
    const items = [];
    if (user.slogan) items.push({ key: t("profileSlogan"), val: user.slogan, wide: true });
    if (user.ccfLevel) items.push({ key: t("profileCcfLevel"), val: `${user.ccfLevel}${t("profileLevelUnit")}` });
    if (user.xcpcLevel) items.push({ key: t("profileXcpcLevel"), val: `${user.xcpcLevel}${t("profileLevelUnit")}` });
    items.push({ key: t("profileVerified"), val: user.verified ? t("profileVerifiedYes") : t("profileVerifiedNo") });
    items.push({ key: t("profileFollowers"), val: String(user.followerCount || 0) });
    items.push({ key: t("profileFollowing"), val: String(user.followingCount || 0) });
    if (user.registerTime) {
        const days = Math.max(0, Math.floor((Date.now() / 1000 - user.registerTime) / 86400));
        items.push({ key: t("profileRegisterTime"), val: `${fmtTime(user.registerTime)} · ${t("profileRegDays", days)}` });
    }
    if (user.blogAddress) {
        const blog = user.blogAddress.startsWith("http") ? user.blogAddress : "https://www.luogu.com.cn" + user.blogAddress;
        items.push({ key: t("profileBlog"), val: blog, link: blog });
    }
    // 综合分 (gu) breakdown + contest prizes (public homepage data)
    const gu = user.guScore || {};
    if (gu && typeof gu === "object" && (gu.rating || gu.basic || gu.contest || gu.practice || gu.social || gu.prize)) {
        const parts = [];
        if (gu.rating) parts.push(`${t("profileGuRating")} ${gu.rating}`);
        if (gu.basic) parts.push(`${t("profileGuBasic")} ${gu.basic}`);
        if (gu.contest) parts.push(`${t("profileGuContest")} ${gu.contest}`);
        if (gu.practice) parts.push(`${t("profileGuPractice")} ${gu.practice}`);
        if (gu.prize) parts.push(`${t("profileGuPrize")} ${gu.prize}`);
        if (gu.social) parts.push(`${t("profileGuSocial")} ${gu.social}`);
        items.push({ key: t("profileGuScore"), val: parts.join(" · "), wide: true });
    }
    if (Array.isArray(user.prizes) && user.prizes.length) {
        const ps = user.prizes.map((p) =>
            [p.year, p.contest, p.event, p.prize].filter(Boolean).join(" ")).join(" · ");
        items.push({ key: t("profilePrizes"), val: ps, wide: true });
    }
    if (user.introduction) items.push({ key: t("profileIntroduction"), val: user.introduction, wide: true, markdown: true });
    if (!items.length) {
        profileInfo.innerHTML = "";
    } else {
        profileInfo.innerHTML = items.map((it) => {
            // Introduction is Markdown (may contain LaTeX) - render it like problem content
            const valHtml = it.markdown
                ? renderMarkdown(it.val)
                : it.link
                    ? `<a href="${escapeHtml(it.link)}" target="_blank" rel="noopener">${escapeHtml(it.val)}</a>`
                    : escapeHtml(it.val);
            const valTag = it.markdown ? "div" : "span";
            return `
                <div class="profile-info-item${it.wide ? " wide" : ""}">
                    <span class="info-key">${escapeHtml(it.key)}</span>
                    <${valTag} class="info-val${it.markdown ? " markdown-body" : ""}">${valHtml}</${valTag}>
                </div>`;
        }).join("");
    }
}

async function loadPracticeDetail() {
    const cookie = (luoguCookieInput.value || "").trim();
    const isOther = profileViewUid !== null;
    let revealed = false;
    // Reveal the content as soon as the first section finishes loading, so
    // slow sections (e.g. statistics) don't block the rest.
    const reveal = () => {
        if (revealed) return;
        revealed = true;
        profileLoading.classList.add("hidden");
        profileContent.classList.remove("hidden");
    };

    // 1) Practice detail: summary cards + difficulty table/chart + type stats
    const practiceReq = isOther
        ? apiCall("get_user_practice_by_uid", profileViewUid)
        : apiCall("get_user_practice_detail", cookie);
    practiceReq
        .then((practiceData) => {
            const p = practiceData.practice;
            // Summary cards
            summaryPassed.textContent = p.totalPassed;
            summaryAttempted.textContent = p.totalAttempted;
            summaryTotal.textContent = p.totalSubmitted;
            summaryRate.textContent = p.totalSubmitted > 0
                ? Math.round(p.totalPassed / p.totalSubmitted * 100) + "%"
                : "--";

            // Difficulty table
            const stats = p.difficultyStats;
            profileTableBody.innerHTML = "";
            for (let i = 0; i < 9; i++) {
                const s = stats[i] || { passed: 0, submitted: 0 };
                const attempted = s.submitted - s.passed;
                const rate = s.submitted > 0 ? Math.round(s.passed / s.submitted * 100) : 0;
                profileTableBody.insertAdjacentHTML("beforeend", `
                    <tr>
                        <td><span class="diff-badge" style="background:${DIFFICULTY_COLORS[i]};color:${diffBadgeTextColor(DIFFICULTY_COLORS[i])}">${getDifficultyNames()[i]}</span></td>
                        <td>${s.passed}</td>
                        <td>${attempted}</td>
                        <td>${rate}%</td>
                    </tr>`);
            }

            // Difficulty chart + type distribution table/doughnut chart
            renderProfileChart(stats);
            renderProfileType(p.typeStats || {});
            reveal();
            // Export is only meaningful for the user's own data
            if (!isOther) addExportButtons();
        })
        .catch((err) => {
            // Reveal the content with a visible error instead of hanging on
            // the loading spinner when Luogu is blocked (e.g. 403/限流).
            summaryPassed.textContent = "--";
            summaryAttempted.textContent = "--";
            summaryTotal.textContent = "--";
            summaryRate.textContent = "--";
            profileTableBody.innerHTML = `<tr><td colspan="4"><div class="profile-empty">${escapeHtml((err && err.message) || t("profileLoadFailed"))}</div></td></tr>`;
            reveal();
        });

    // 2) & 3) Recent submissions + statistics (trend/week/tags) are NOT
    // loaded here anymore: they are fetched lazily the first time the user
    // opens the 提交记录 / 做题趋势 / 标签分布 tabs (see switchProfileTab),
    // so the 做题概览 tab renders as fast as possible.
}

// Show a "private / not public" notice in the recent-submissions table
function renderRecentSubmissionsPrivate(msg) {
    if (!recentBody) return;
    recentBody.innerHTML = `<tr><td colspan="6"><div class="profile-empty">${escapeHtml(msg)}</div></td></tr>`;
}

// Load the three statistics sections (trend / week / tags). On failure they
// show a retryable error overlay instead of the misleading "no data" state.
// Results are cached in memory (`profileStatsCache`) so the 做题趋势 and
// 标签分布 lazy tabs never fetch the same data twice.
let profileStatsCache = null;

function loadProfileStats(cookie, onDone, only) {
    const done = () => { if (onDone) onDone(); };
    if (profileStatsCache) {
        renderProfileStatsData(profileStatsCache, only);
        done();
        return;
    }
    const statsReq = profileViewUid !== null
        ? apiCall("get_user_statistics_by_uid", profileViewUid)
        : apiCall("get_user_statistics", cookie);
    statsReq
        .then((statData) => {
            const st = (statData && statData.statistics) || null;
            if (st) {
                profileStatsCache = st;
                renderProfileStatsData(st, only);
            } else {
                renderProfileStatsError(t("profileStatsError"));
            }
            done();
        })
        .catch((err) => {
            renderProfileStatsError((err && err.message) || t("profileStatsError"));
            done();
        });
}

// Render a slice of the cached statistics payload. `only` is "trend" (180-day
// trend + 7-day activity) or "tags" (tag distribution); omitted = everything.
function renderProfileStatsData(st, only) {
    if (!only || only === "trend") {
        renderProfileTrend(st.trend || []);
        renderProfileWeek(st.week || []);
    }
    if (!only || only === "tags") {
        renderProfileTags(st.tags || []);
    }
}

function renderProfileStatsError(msg) {
    const text = escapeHtml(msg || t("profileStatsError"));
    const retryLabel = escapeHtml(t("profileStatsRetry"));
    const overlay = `<div class="section-error"><span>${text}</span><button type="button" class="btn-secondary profile-retry-btn">${retryLabel}</button></div>`;
    const wrapOf = (id) => {
        const el = document.querySelector(id);
        return el ? el.closest(".profile-chart-wrap") : null;
    };
    const wraps = [wrapOf("#profileTrendChart"), wrapOf("#profileWeekChart"), wrapOf("#profileTagChart")];
    wraps.forEach((wrap) => {
        if (!wrap) return;
        wrap.querySelectorAll(".section-error").forEach((el) => el.remove());
        const sp = wrap.querySelector(".section-spinner");
        if (sp) sp.classList.add("hidden");
        wrap.insertAdjacentHTML("beforeend", overlay);
        const btn = wrap.querySelector(".profile-retry-btn");
        if (btn) btn.addEventListener("click", retryProfileStats);
    });
    const tagBody = document.querySelector("#profileTagBody");
    if (tagBody) {
        tagBody.innerHTML = `<p class="profile-empty">${text} <button type="button" class="btn-secondary profile-retry-btn">${retryLabel}</button></p>`;
        const btn = tagBody.querySelector(".profile-retry-btn");
        if (btn) btn.addEventListener("click", retryProfileStats);
    }
}

function retryProfileStats() {
    // Remove error overlays and put every statistics section back to spinners.
    ["#profileTrendChart", "#profileWeekChart", "#profileTagChart"].forEach((sel) => {
        const canvas = document.querySelector(sel);
        const wrap = canvas && canvas.closest(".profile-chart-wrap");
        if (!wrap) return;
        wrap.querySelectorAll(".section-error").forEach((el) => el.remove());
        const sp = wrap.querySelector(".section-spinner");
        if (sp) sp.classList.remove("hidden");
    });
    const tagBody = document.querySelector("#profileTagBody");
    if (tagBody) {
        tagBody.innerHTML = `<div class="section-spinner"><div class="spinner"></div></div>`;
    }
    profileStatsCache = null;
    loadProfileStats((luoguCookieInput.value || "").trim(), null);
}

// Add export buttons to profile
function addExportButtons() {
    const summary = document.querySelector(".profile-summary");
    if (!summary) return;
    // Check if already added
    if (document.getElementById("exportButtons")) return;

    const exportDiv = document.createElement("div");
    exportDiv.id = "exportButtons";
    exportDiv.style.cssText = "display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;";
    exportDiv.innerHTML = `
        <button id="exportCsvBtn" class="btn-secondary" style="padding:6px 16px;font-size:13px;">${t("exportCsv")}</button>
        <button id="exportMdBtn" class="btn-secondary" style="padding:6px 16px;font-size:13px;">${t("exportMd")}</button>
    `;
    summary.parentNode.insertBefore(exportDiv, summary.nextSibling);

    document.getElementById("exportCsvBtn").addEventListener("click", () => doExport("csv"));
    document.getElementById("exportMdBtn").addEventListener("click", () => doExport("markdown"));
}

function doExport(format) {
    const cookie = document.getElementById("luoguCookie").value;
    if (!cookie) {
        showStatus("error", t("exportNeedCookie") || "需要洛谷 Cookie 才能导出");
        return;
    }
    showLoading(t("exporting") || "正在导出...");
    apiCall("export_problems", cookie, format)
        .then(data => {
            hideLoading();
            if (data.success && data.content) {
                // WebView2 file:// 下浏览器式下载无效：文件已由后端写入 exports/，
                // 直接调用后端用系统默认程序打开。
                showStatus("success", t("exportSuccess", data.count || 0));
                if (data.file_path) {
                    apiCall("open_export_file", data.file_path).catch(() => {});
                }
            } else {
                showStatus("error", data.error || t("exportFailed", "?"));
            }
        })
        .catch(err => {
            hideLoading();
            showStatus("error", err.message || t("exportFailed", "?"));
        });
}

// Render the type distribution table and doughnut chart
function renderProfileType(typeStats) {
    const entries = Object.entries(typeStats || {});
    profileTypeBody.innerHTML = "";
    if (!entries.length) {
        profileTypeBody.insertAdjacentHTML("beforeend",
            `<tr><td colspan="2" class="profile-empty">${escapeHtml(t("profileRecentEmpty"))}</td></tr>`);
    }
    for (const [type, s] of entries) {
        profileTypeBody.insertAdjacentHTML("beforeend", `
            <tr>
                <td>${escapeHtml(typeName(type))}</td>
                <td>${s.submitted}</td>
            </tr>`);
    }
    renderProfileTypeChart(entries);
}

function typeName(type) {
    return TYPE_NAMES[type] || type || "?";
}

function renderProfileTypeChart(entries) {
    if (profileTypeChart) {
        profileTypeChart.destroy();
        profileTypeChart = null;
    }
    if (!entries.length) return;
    const isDark = isDarkTheme(document.documentElement.getAttribute("data-theme"));
    const textColor = isDark ? "#ccc" : "#333";
    profileTypeChart = new Chart($("#profileTypeChart"), {
        type: "doughnut",
        data: {
            labels: entries.map(([type]) => typeName(type)),
            datasets: [{
                data: entries.map(([, s]) => s.submitted),
                backgroundColor: entries.map((_, i) => TYPE_CHART_COLORS[i % TYPE_CHART_COLORS.length]),
                borderWidth: 1,
                hoverOffset: 6,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "nearest",
                intersect: true,
            },
            hover: {
                mode: "nearest",
                intersect: true,
            },
            plugins: {
                legend: {
                    position: "right",
                    labels: { color: textColor },
                },
                tooltip: {
                    backgroundColor: isDark ? "rgba(30,30,30,0.92)" : "rgba(255,255,255,0.96)",
                    titleColor: textColor,
                    bodyColor: textColor,
                    borderColor: isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)",
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                        label: (ctx) => {
                            const s = entries[ctx.dataIndex] ? entries[ctx.dataIndex][1] : { submitted: 0 };
                            return ` ${s.submitted} ${t("profileTypeCount")}`;
                        },
                    },
                },
            },
        },
    });
}

// Chart theme helper: pick colors based on current dark/light theme
function profileChartTheme() {
    const isDark = isDarkTheme(document.documentElement.getAttribute("data-theme"));
    return {
        isDark,
        textColor: isDark ? "#ccc" : "#333",
        gridColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)",
        tooltipBg: isDark ? "rgba(30,30,30,0.92)" : "rgba(255,255,255,0.96)",
    };
}

// Render the 180-day submission trend line chart
function renderProfileTrend(trend) {
    if (profileTrendChart) {
        profileTrendChart.destroy();
        profileTrendChart = null;
    }
    const canvas = $("#profileTrendChart");
    if (!canvas) return;
    hideSectionSpinner(canvas.closest(".profile-chart-wrap"));
    if (!trend.length) {
        canvas.closest(".profile-chart-wrap").innerHTML = `<p class="profile-empty">${escapeHtml(t("profileStatsEmpty"))}</p>`;
        return;
    }
    const th = profileChartTheme();
    profileTrendChart = new Chart(canvas, {
        type: "line",
        data: {
            labels: trend.map((d) => d.date),
            datasets: [{
                label: t("profileTrendLabel"),
                data: trend.map((d) => d.count),
                borderColor: "#3498DB",
                backgroundColor: "rgba(52,152,219,0.12)",
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                pointHoverRadius: 4,
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false,
            },
            hover: {
                mode: "index",
                intersect: false,
            },
            scales: {
                x: {
                    ticks: {
                        color: th.textColor,
                        maxTicksLimit: 12,
                        maxRotation: 0,
                    },
                    grid: { color: th.gridColor },
                },
                y: {
                    beginAtZero: true,
                    ticks: { color: th.textColor, precision: 0 },
                    grid: { color: th.gridColor },
                },
            },
            plugins: {
                legend: { labels: { color: th.textColor } },
                tooltip: {
                    enabled: true,
                    backgroundColor: th.tooltipBg,
                    titleColor: th.textColor,
                    bodyColor: th.textColor,
                    borderColor: th.isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)",
                    borderWidth: 1,
                    callbacks: {
                        title: (items) => {
                            const d = items[0] ? trend[items[0].dataIndex] : null;
                            return d ? `${d.date}（${t("profileTrendLabel")}）` : "";
                        },
                        label: (ctx) => ` ${ctx.parsed.y} ${t("profileSubmissionCount")}`,
                    },
                },
            },
        },
    });
}

// Render the 7-day activity bar chart
function renderProfileWeek(week) {
    if (profileWeekChart) {
        profileWeekChart.destroy();
        profileWeekChart = null;
    }
    const canvas = $("#profileWeekChart");
    if (!canvas) return;
    hideSectionSpinner(canvas.closest(".profile-chart-wrap"));
    if (!week.length) {
        canvas.closest(".profile-chart-wrap").innerHTML = `<p class="profile-empty">${escapeHtml(t("profileStatsEmpty"))}</p>`;
        return;
    }
    const th = profileChartTheme();
    profileWeekChart = new Chart(canvas, {
        type: "bar",
        data: {
            labels: week.map((d) => d.date.slice(5)),
            datasets: [{
                label: t("profileWeekLabel"),
                data: week.map((d) => d.count),
                backgroundColor: week.map((d) => (d.count > 0 ? "#52C41A" : th.gridColor)),
                borderRadius: 4,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false,
            },
            hover: {
                mode: "index",
                intersect: false,
            },
            scales: {
                x: {
                    ticks: { color: th.textColor },
                    grid: { color: th.gridColor },
                },
                y: {
                    beginAtZero: true,
                    ticks: { color: th.textColor, precision: 0 },
                    grid: { color: th.gridColor },
                },
            },
            plugins: {
                legend: { labels: { color: th.textColor } },
                tooltip: {
                    backgroundColor: th.tooltipBg,
                    titleColor: th.textColor,
                    bodyColor: th.textColor,
                    borderColor: th.isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)",
                    borderWidth: 1,
                    callbacks: {
                        label: (ctx) => ` ${ctx.parsed.y} ${t("profileSubmissionCount")}`,
                    },
                },
            },
        },
    });
}

// Render tag statistics: top tags as chips + horizontal bar chart
function renderProfileTags(tags) {
    if (profileTagChart) {
        profileTagChart.destroy();
        profileTagChart = null;
    }
    const listEl = $("#profileTagBody");
    const canvas = $("#profileTagChart");
    if (!listEl || !canvas) return;
    hideSectionSpinner(listEl);
    hideSectionSpinner(canvas.closest(".profile-chart-wrap"));
    if (!tags || !tags.length) {
        listEl.innerHTML = `<p class="profile-empty">${escapeHtml(t("profileTagsEmpty"))}</p>`;
        if (canvas.closest(".profile-chart-wrap")) canvas.closest(".profile-chart-wrap").style.display = "none";
        return;
    }
    if (canvas.closest(".profile-chart-wrap")) canvas.closest(".profile-chart-wrap").style.display = "";
    listEl.innerHTML = tags.map((tg) => `
        <span class="tag-chip">${escapeHtml(tg.name)}<em>${tg.count}</em></span>`).join("");
    const th = profileChartTheme();
    const top = tags.slice(0, 10).reverse(); // horizontal bars: top at the top
    profileTagChart = new Chart(canvas, {
        type: "bar",
        data: {
            labels: top.map((tg) => tg.name),
            datasets: [{
                label: t("profileTagLabel"),
                data: top.map((tg) => tg.count),
                backgroundColor: top.map((_, i) => TYPE_CHART_COLORS[i % TYPE_CHART_COLORS.length]),
                borderRadius: 3,
            }],
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "nearest",
                intersect: true,
            },
            hover: {
                mode: "nearest",
                intersect: true,
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { color: th.textColor, precision: 0 },
                    grid: { color: th.gridColor },
                },
                y: {
                    ticks: { color: th.textColor },
                    grid: { display: false },
                },
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: th.tooltipBg,
                    titleColor: th.textColor,
                    bodyColor: th.textColor,
                    borderColor: th.isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)",
                    borderWidth: 1,
                    callbacks: {
                        label: (ctx) => ` ${ctx.parsed.x} ${t("profileTagCount")}`,
                    },
                },
            },
        },
    });
}

// Render the recent submissions table
function renderRecentSubmissions(records) {
    recentBody.innerHTML = "";
    if (!records || !records.length) {
        recentBody.insertAdjacentHTML("beforeend",
            `<tr><td colspan="6" class="profile-empty">${escapeHtml(t("profileRecentEmpty"))}</td></tr>`);
        return;
    }
    for (const rec of records) {
        const st = STATUS_MAP[rec.status] || STATUS_OTHER;
        const stText = diffBadgeTextColor(st.color);
        const scoreText = (rec.score != null && rec.score !== undefined) ? String(rec.score) : "--";
        recentBody.insertAdjacentHTML("beforeend", `
            <tr>
                <td><span class="status-badge" style="background:${st.color};color:${stText}">${escapeHtml(t(st.key))}</span></td>
                <td class="recent-title">
                    <a href="https://www.luogu.com.cn/problem/${encodeURIComponent(rec.pid)}" target="_blank" rel="noopener">${escapeHtml(rec.pid)}</a>
                    <span class="recent-title-name">${escapeHtml(rec.title || "")}</span>
                </td>
                <td>${escapeHtml(scoreText)}</td>
                <td>${rec.timeMs ? (rec.timeMs / 1000).toFixed(2) + "s" : "--"}</td>
                <td>${rec.memoryKB ? (rec.memoryKB / 1024).toFixed(1) + "MB" : "--"}</td>
                <td>${fmtTime(rec.submitTime)}</td>
            </tr>`);
    }
}

// =========================================================================
// Blog Reading
// =========================================================================
function createBlogModal() {
    if (document.getElementById("blogModal")) return;
    const modal = document.createElement("div");
    modal.id = "blogModal";
    modal.className = "training-modal hidden";
    modal.innerHTML = `
        <div class="training-dialog" style="max-width:800px;">
            <div class="training-header">
                <div>
                    <h3 id="blogTitle">博客</h3>
                    <p id="blogSubtitle" class="training-subtitle">用户博客文章</p>
                </div>
                <button type="button" class="modal-close-btn" id="blogCloseBtn" title="×">&times;</button>
            </div>
            <div id="blogBody" class="training-body">
                <div id="blogLoading" class="profile-loading">
                    <div class="spinner"></div>
                    <p>加载博客列表...</p>
                </div>
                <div id="blogList" class="training-list hidden"></div>
                <div id="blogContent" class="training-detail hidden"></div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    document.getElementById("blogCloseBtn").addEventListener("click", () => modal.classList.add("hidden"));
    modal.addEventListener("click", (e) => {
        if (e.target === modal) modal.classList.add("hidden");
    });
}

function showBlog(uid) {
    createBlogModal();
    const modal = document.getElementById("blogModal");
    modal.classList.remove("hidden");
    document.getElementById("blogLoading").classList.remove("hidden");
    document.getElementById("blogList").classList.add("hidden");
    document.getElementById("blogContent").classList.add("hidden");
    document.getElementById("blogTitle").textContent = t("blogTitle");
    document.getElementById("blogSubtitle").textContent = t("blogSubtitle");

    apiCall("get_user_blog", uid, 1)
        .then(data => {
            document.getElementById("blogLoading").classList.add("hidden");
            const posts = data.posts || [];
            const list = document.getElementById("blogList");
            if (!posts.length) {
                list.innerHTML = '<div class="placeholder"><p>' + escapeHtml(t("blogEmpty")) + '</p></div>';
                list.classList.remove("hidden");
                return;
            }
            let html = "";
            posts.forEach(p => {
                const time = p.time ? new Date(p.time * 1000).toLocaleString("zh-CN") : "";
                html += '<div class="training-card" data-bid="' + p.id + '" data-author="' + escapeHtml(p.author || "") + '">' +
                    '<div class="training-card-name">' + escapeHtml(p.title || t("unknown")) + '</div>' +
                    '<div class="training-card-meta">' + time + ' · 👍 ' + (p.likeCount || 0) + ' · 💬 ' + (p.commentCount || 0) + '</div>' +
                    '</div>';
            });
            list.innerHTML = html;
            list.classList.remove("hidden");

            list.querySelectorAll(".training-card").forEach(card => {
                card.addEventListener("click", () => {
                    const bid = card.dataset.bid;
                    const author = card.dataset.author || "";
                    showBlogDetail(bid, author);
                });
            });
        })
        .catch(err => {
            document.getElementById("blogLoading").innerHTML = '<p class="error-message">' + escapeHtml(err.message || t("blogLoadFailed")) + '</p>';
        });
}

function showBlogDetail(bid, author) {
    createBlogModal();
    document.getElementById("blogList").classList.add("hidden");
    document.getElementById("blogContent").classList.remove("hidden");
    document.getElementById("blogLoading").classList.remove("hidden");
    document.getElementById("blogLoading").innerHTML = '<div class="spinner"></div><p>' + escapeHtml(t("blogLoading")) + '</p>';

    apiCall("get_blog_detail", bid, author || "")
        .then(data => {
            document.getElementById("blogLoading").classList.add("hidden");
            const blog = data.blog || {};
            document.getElementById("blogTitle").textContent = escapeHtml(blog.title || t("unknown"));
            document.getElementById("blogSubtitle").textContent = blog.time ? new Date(blog.time * 1000).toLocaleString("zh-CN") : "";

            const content = document.getElementById("blogContent");
            content.innerHTML = '<div class="markdown-body">' + renderMarkdown(blog.content || "") + '</div>';

            // Apply syntax highlighting
            content.querySelectorAll("pre code").forEach(block => {
                try { hljs.highlightElement(block); } catch(e) {}
            });
        })
        .catch(err => {
            document.getElementById("blogLoading").innerHTML = '<p class="error-message">' + escapeHtml(err.message || t("blogLoadFailed")) + '</p>';
        });
}

// =========================================================================
// Training plans (洛谷官方训练计划/学习路线)
// =========================================================================
const trainingModal = $("#trainingModal");
const trainingLoading = $("#trainingLoading");
const trainingListEl = $("#trainingList");
const trainingDetailEl = $("#trainingDetail");
const trainingCloseBtn = $("#trainingCloseBtn");
const trainingBtn = $("#trainingBtn");

function openTrainingModal() {
    if (!trainingModal) return;
    trainingModal.classList.remove("hidden");
    loadTrainingList();
}

function closeTrainingModal() {
    if (trainingModal) trainingModal.classList.add("hidden");
}

async function loadTrainingList() {
    trainingLoading.classList.remove("hidden");
    trainingListEl.classList.add("hidden");
    trainingDetailEl.classList.add("hidden");
    try {
        const data = await apiCall("get_trainings", 1);
        if (!data.success) throw new Error(data.error || "failed");
        const list = data.trainings || [];
        trainingListEl.innerHTML = "";
        if (!list.length) {
            trainingListEl.innerHTML = `<p class="profile-empty">${escapeHtml(t("trainingEmpty"))}</p>`;
        } else {
            let html = "";
            list.forEach((tr) => {
                html += `
                    <div class="training-card" data-id="${escapeHtml(String(tr.id))}">
                        <div class="training-card-name">${escapeHtml(tr.name)}</div>
                        <div class="training-card-meta">${t("trainingProblemCount", tr.problemCount)}${tr.provider ? ` · ${escapeHtml(tr.provider)}` : ""}</div>
                    </div>`;
            });
            trainingListEl.innerHTML = html;
            trainingListEl.querySelectorAll(".training-card").forEach((card) => {
                card.addEventListener("click", () => loadTrainingDetail(card.dataset.id));
            });
        }
        trainingLoading.classList.add("hidden");
        trainingListEl.classList.remove("hidden");
    } catch (err) {
        trainingLoading.classList.add("hidden");
        trainingListEl.classList.remove("hidden");
        trainingListEl.innerHTML = `<p class="profile-empty">${escapeHtml(err.message || t("trainingLoadFailed"))}</p>`;
    }
}

async function loadTrainingDetail(id) {
    trainingDetailEl.classList.remove("hidden");
    trainingDetailEl.innerHTML = `<div class="profile-loading"><div class="spinner"></div><p>${escapeHtml(t("trainingLoadingDetail"))}</p></div>`;
    trainingListEl.classList.add("hidden");
    try {
        const data = await apiCall("get_training_detail", id);
        if (!data.success) throw new Error(data.error || "failed");
        const tr = data.training || {};
        let html = `
            <div class="training-detail-head">
                <button type="button" class="btn-link training-back-btn">← ${t("trainingBack")}</button>
                <h4>${escapeHtml(tr.name)}</h4>
                ${tr.description ? `<p class="training-detail-desc">${escapeHtml(tr.description)}</p>` : ""}
            </div>
            <div class="training-problem-list">`;
        (tr.problems || []).forEach((p) => {
            const diffColor = DIFFICULTY_COLORS[p.difficulty] || DIFFICULTY_COLORS[0];
            const stats = p.totalSubmit > 0
                ? ` · ${t("submitShort")} ${formatNum(p.totalSubmit)} · ${t("acceptShort")} ${formatNum(p.totalAccepted)}`
                : "";
            html += `
                <div class="training-problem-item" data-pid="${escapeHtml(p.pid)}">
                    <span class="diff-badge" style="background:${diffColor};color:${diffBadgeTextColor(diffColor)}">${getDifficultyNames()[p.difficulty]}</span>
                    <span class="training-problem-pid">${escapeHtml(p.pid)}</span>
                    <span class="training-problem-name">${escapeHtml(p.name)}</span>
                    <span class="training-problem-stats">${stats}</span>
                    <span class="training-problem-tags">${(p.tags || []).map(escapeHtml).join(" · ")}</span>
                </div>`;
        });
        html += `</div>`;
        trainingDetailEl.innerHTML = html;
        trainingDetailEl.querySelectorAll(".training-problem-item").forEach((item) => {
            item.addEventListener("click", () => {
                problemIdInput.value = item.dataset.pid;
                closeTrainingModal();
                analyze();
            });
        });
        const backBtn = trainingDetailEl.querySelector(".training-back-btn");
        if (backBtn) backBtn.addEventListener("click", loadTrainingList);
    } catch (err) {
        trainingDetailEl.innerHTML = `<p class="profile-empty">${escapeHtml(err.message || t("trainingLoadFailed"))}</p>`;
    }
}

if (trainingBtn) trainingBtn.addEventListener("click", openTrainingModal);
if (trainingCloseBtn) trainingCloseBtn.addEventListener("click", closeTrainingModal);

// Add "题库浏览" button to the action button grid
const headerActions = document.querySelector(".header-actions") || document.querySelector(".header-right");
if (headerActions) {
    if (!document.getElementById("browseBtn")) {
        const browseBtn = document.createElement("button");
        browseBtn.type = "button";
        browseBtn.id = "browseBtn";
        browseBtn.className = "btn-secondary header-btn";
        browseBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"></rect><rect x="14" y="3" width="7" height="7" rx="1"></rect><rect x="3" y="14" width="7" height="7" rx="1"></rect><rect x="14" y="14" width="7" height="7" rx="1"></rect></svg><span data-i18n="browseBtn">题库浏览</span>';
        browseBtn.setAttribute("aria-label", t("browseBtn"));
        const trainingBtnEl = document.getElementById("trainingBtn");
        if (trainingBtnEl && trainingBtnEl.parentNode === headerActions) {
            headerActions.insertBefore(browseBtn, trainingBtnEl);
        } else {
            headerActions.appendChild(browseBtn);
        }
        browseBtn.addEventListener("click", showProblemBrowser);
    }
}

// =========================================================================
// Contest / Competition
// =========================================================================
const contestModal = document.createElement("div");
contestModal.id = "contestModal";
contestModal.className = "training-modal hidden";
contestModal.innerHTML = `
    <div class="training-dialog">
        <div class="training-header">
            <div>
                <h3 id="contestTitle">比赛列表</h3>
                <p id="contestSubtitle" class="training-subtitle">查看洛谷进行中/即将开始的比赛</p>
            </div>
            <button type="button" class="modal-close-btn" id="contestCloseBtn" title="×">&times;</button>
        </div>
        <div id="contestBody" class="training-body">
            <div id="contestLoading" class="profile-loading">
                <div class="spinner"></div>
                <p>正在加载比赛列表...</p>
            </div>
            <div id="contestList" class="training-list hidden"></div>
            <div id="contestDetail" class="training-detail hidden"></div>
        </div>
    </div>
`;
document.body.appendChild(contestModal);

const contestLoading = document.getElementById("contestLoading");
const contestListEl = document.getElementById("contestList");
const contestDetailEl = document.getElementById("contestDetail");
const contestCloseBtn = document.getElementById("contestCloseBtn");

// Insert into the action button grid (idempotent: skip if already present)
const headerActionsEl = document.querySelector(".header-actions") || document.querySelector(".header-right");
const trainingBtnEl = document.getElementById("trainingBtn");
if (headerActionsEl && !document.getElementById("contestBtn")) {
    const contestBtn = document.createElement("button");
    contestBtn.type = "button";
    contestBtn.id = "contestBtn";
    contestBtn.className = "btn-secondary header-btn";
    contestBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><path d="M4 22v-7"></path></svg><span data-i18n="contestBtn">比赛</span>';
    contestBtn.setAttribute("aria-label", t("contestBtn"));
    if (trainingBtnEl && trainingBtnEl.parentNode === headerActionsEl) {
        headerActionsEl.insertBefore(contestBtn, trainingBtnEl);
    } else {
        headerActionsEl.appendChild(contestBtn);
    }
    contestBtn.addEventListener("click", showContests);
}

// Contest status badge: 0 = upcoming, 1 = ongoing, 2 = ended
function contestStatusBadge(status) {
    const info = {
        0: { cls: "cs-upcoming", key: "contestStatusUpcoming" },
        1: { cls: "cs-ongoing", key: "contestStatusOngoing" },
        2: { cls: "cs-ended", key: "contestStatusEnded" },
    }[status] || { cls: "cs-ended", key: "contestStatusEnded" };
    return `<span class="contest-status-badge ${info.cls}">${escapeHtml(t(info.key))}</span>`;
}

function showContests() {
    contestModal.classList.remove("hidden");
    contestLoading.classList.remove("hidden");
    contestListEl.classList.add("hidden");
    contestDetailEl.classList.add("hidden");
    document.getElementById("contestTitle").textContent = t("contestListTitle");
    document.getElementById("contestSubtitle").textContent = t("contestListSubtitle");

    apiCall("get_contests", 1)
        .then(data => {
            contestLoading.classList.add("hidden");
            const contests = data.contests || [];
            if (!contests.length) {
                contestListEl.innerHTML = `<div class="placeholder"><p>${escapeHtml(t("contestEmpty"))}</p></div>`;
                contestListEl.classList.remove("hidden");
                return;
            }
            let html = "";
            contests.forEach(c => {
                const start = c.startTime ? new Date(c.startTime * 1000).toLocaleString("zh-CN") : t("contestTimeUnknown");
                const dur = c.duration ? Math.round(c.duration / 60) + " " + t("contestDurationUnit") : t("contestTimeUnknown");
                html += `<div class="training-card" data-cid="${c.id}">
                    <div class="training-card-name">${contestStatusBadge(c.status)}${escapeHtml(c.name)}</div>
                    <div class="training-card-meta">${t("contestStartAt", start)} · ${t("contestDurationAt", dur)} · ${t("contestParticipantsAt", c.participantCount || 0)}</div>
                </div>`;
            });
            contestListEl.innerHTML = html;
            contestListEl.classList.remove("hidden");

            contestListEl.querySelectorAll(".training-card").forEach(card => {
                card.addEventListener("click", () => {
                    const cid = card.dataset.cid;
                    showContestDetail(cid);
                });
            });
        })
        .catch(err => {
            contestLoading.innerHTML = `<p class="error-message">${escapeHtml(err.message || t("contestLoadFailed"))}</p>`;
        });
}

function showContestDetail(cid) {
    contestListEl.classList.add("hidden");
    contestDetailEl.classList.remove("hidden");
    contestLoading.classList.remove("hidden");
    contestLoading.innerHTML = '<div class="spinner"></div><p>' + escapeHtml(t("contestDetailLoading")) + '</p>';

    apiCall("get_contest_detail", cid)
        .then(data => {
            contestLoading.classList.add("hidden");
            const contest = data.contest || {};
            document.getElementById("contestTitle").textContent = escapeHtml(contest.name || t("contestDetail"));
            document.getElementById("contestSubtitle").innerHTML =
                (contest.problemCount ? contest.problemCount + " " + t("contestProblemCount") : "") +
                (contest.participantCount ? " · " + contest.participantCount + " " + t("contestParticipants") : "") +
                " " + contestStatusBadge(contest.status);

            const start = contest.startTime ? new Date(contest.startTime * 1000).toLocaleString() : "";
            const end = contest.endTime ? new Date(contest.endTime * 1000).toLocaleString() : "";
            let html = '';
            if (contest.host) {
                html += `<div class="contest-meta">${escapeHtml(t("contestHost"))}: ${escapeHtml(contest.host)}</div>`;
            }
            if (start || end) {
                html += `<div class="contest-meta">${start} ~ ${end}</div>`;
            }
            // Register area — only for contests that are not over yet
            if (contest.status !== 2) {
                if (contest.joined) {
                    html += `<div class="contest-register-wrap"><span class="contest-joined-badge">${escapeHtml(t("contestRegistered"))}</span></div>`;
                } else {
                    html += `<div class="contest-register-wrap"><button type="button" class="contest-register-btn" id="contestRegisterBtn">${escapeHtml(t("contestRegisterBtn"))}</button></div>`;
                }
            }
            if (contest.description) {
                html += `<div class="training-detail-desc markdown-body" style="margin-top:10px;">${renderMarkdown(contest.description)}</div>`;
            }
            const problems = contest.problems || [];
            if (problems.length) {
                html += `<div class="training-detail-head" style="margin-top:14px;"><h4>${escapeHtml(t("contestProblems"))}</h4></div>`;
                problems.forEach(p => {
                    const diffColor = ["#bfbfbf","#fe4c61","#f39c11","#ffc116","#52c41a","#3498db","#9d3dcf","#0e1d69"][p.difficulty] || "#bfbfbf";
                    const diffName = ["暂无评定","入门","普及-","普及/提高-","普及+/提高","提高+/省选-","省选/NOI-","NOI/NOI+/CTSC"][p.difficulty] || "未知";
                    const label = p.no ? `${escapeHtml(p.no)} · ${escapeHtml(p.pid)}` : escapeHtml(p.pid);
                    html += `<div class="training-problem" data-pid="${p.pid}">
                        <span class="training-problem-pid" style="font-weight:600;">${label}</span>
                        <span class="training-problem-name">${escapeHtml(p.name || "")}</span>
                        <span class="diff-badge" style="background:${diffColor};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;margin-left:auto;">${diffName}</span>
                    </div>`;
                });
            } else if (contest.problemCount > 0) {
                html += `<div class="training-detail-head" style="margin-top:14px;"><h4>${escapeHtml(t("contestProblems"))}</h4></div>
                    <p class="profile-empty">${escapeHtml(t("contestProblemsLocked"))}</p>`;
            }
            contestDetailEl.innerHTML = html;

            // Render markdown in description
            contestDetailEl.querySelectorAll("pre code").forEach(block => {
                try { hljs.highlightElement(block); } catch(e) {}
            });

            // Register button — join the contest, then refresh the detail view
            const regBtn = contestDetailEl.querySelector("#contestRegisterBtn");
            if (regBtn) {
                regBtn.addEventListener("click", async () => {
                    regBtn.disabled = true;
                    regBtn.textContent = t("contestRegistering");
                    try {
                        await apiCall("register_contest", cid);
                        showContestDetail(cid);
                    } catch (err) {
                        regBtn.disabled = false;
                        regBtn.textContent = t("contestRegisterBtn");
                        let errBox = contestDetailEl.querySelector(".contest-register-error");
                        if (!errBox) {
                            errBox = document.createElement("p");
                            errBox.className = "error-message contest-register-error";
                            contestDetailEl.insertBefore(errBox, contestDetailEl.firstChild);
                        }
                        errBox.textContent = err.message || t("contestRegisterFailed");
                    }
                });
            }

            contestDetailEl.querySelectorAll(".training-problem").forEach(item => {
                item.addEventListener("click", () => {
                    const pid = item.dataset.pid;
                    if (pid) {
                        document.getElementById("problemId").value = pid;
                        contestModal.classList.add("hidden");
                        // Load the problem with the contest context so code is
                        // submitted as a contest submission.
                        loadProblemOnly(pid, { contestId: String(cid) });
                    }
                });
            });
        })
        .catch(err => {
            contestLoading.innerHTML = `<p class="error-message">${escapeHtml(err.message || t("contestDetailFailed"))}</p>`;
        });
}

contestCloseBtn.addEventListener("click", () => contestModal.classList.add("hidden"));
// Close on backdrop click
contestModal.addEventListener("click", (e) => {
    if (e.target === contestModal) contestModal.classList.add("hidden");
});

// =========================================================================
// Problem collections (题单/收藏)
// =========================================================================
async function getCollections() {
    if (collectionsCache) return collectionsCache;
    const data = await apiCall("get_collections");
    collectionsCache = data.collections || [];
    return collectionsCache;
}

async function refreshCollections() {
    collectionsCache = null;
    return getCollections();
}

function isCollectedIn(pid, lists) {
    return (lists || []).some((l) => (l.problems || []).some((p) => p.pid === pid));
}

// HTML for a collect button (collected state filled later by refreshCollectButtons)
function collectBtnHtml(pid, title, difficulty) {
    return `<button type="button" class="collect-btn" data-pid="${escapeHtml(pid)}" data-title="${escapeHtml(title || "")}" data-difficulty="${difficulty || 0}">${t("collect")}</button>`;
}

// External links shown in the problem header's top-right corner:
//   Luogu   -> https://www.luogu.com.cn/problem/<pid>
//   Vjudge  -> https://vjudge.net/problem/洛谷-<pid> (Luogu) / AtCoder-<id> (AtCoder)
//   AtCoder -> https://atcoder.jp/contests/<contest>/tasks/<id>
// Kept pure (no DOM globals) so it can be unit-tested in isolation.
function buildProblemLinksHtml(pid) {
    const safePid = encodeURIComponent(String(pid || ""));
    const luoguUrl = "https://www.luogu.com.cn/problem/" + safePid;
    const isAt = /^at_/i.test(String(pid || ""));
    const atId = String(pid || "").slice(3);                       // "AT_abc138_a" -> "abc138_a"
    // Vjudge remote-OJ naming: 洛谷-<pid> for Luogu problems,
    // AtCoder-<atcoder_id> for AtCoder problems (e.g. "AT_dp_t" -> "AtCoder-dp_t").
    const vjudgeUrl = isAt
        ? "https://vjudge.net/problem/" + encodeURIComponent("AtCoder-" + atId)
        : "https://vjudge.net/problem/" + encodeURIComponent("洛谷") + "-" + safePid;
    const atContest = atId.replace(/_[A-Za-z0-9]+$/, "");          // -> "abc138"
    const atcoderUrl = isAt ? "https://atcoder.jp/contests/" + encodeURIComponent(atContest) + "/tasks/" + encodeURIComponent(atId) : "";
    const extIcon =
        '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17 17 7"></path><path d="M7 7h10v10"></path></svg>';
    return `
        <a class="problem-link luogu" href="${luoguUrl}" target="_blank" rel="noopener" title="${t("openLuogu")}">${extIcon}<span>${t("luoguName")}</span></a>
        <a class="problem-link vjudge" href="${vjudgeUrl}" target="_blank" rel="noopener" title="${t("openVjudge")}">${extIcon}<span>${t("vjudgeName")}</span></a>
        ${isAt ? `<a class="problem-link atcoder" href="${atcoderUrl}" target="_blank" rel="noopener" title="${t("openAtcoder")}">${extIcon}<span>${t("atcoderName")}</span></a>` : ""}`;
}

function attachCollectBtn(btn) {
    btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const pid = btn.dataset.pid;
        const title = btn.dataset.title || "";
        const difficulty = Number(btn.dataset.difficulty || 0);
        if (!pid) return;
        try {
            const lists = await getCollections();
            if (isCollectedIn(pid, lists)) {
                openUncollectModal(pid, title);
            } else {
                openCollectModal(pid, title, difficulty);
            }
        } catch (err) {
            console.warn("collect state check failed:", err);
        }
    });
}

// Refresh every visible collect button (collected -> yellow "已收藏")
async function refreshCollectButtons() {
    try {
        const lists = await getCollections();
        document.querySelectorAll(".collect-btn").forEach((btn) => {
            const collected = isCollectedIn(btn.dataset.pid, lists);
            btn.classList.toggle("collected", collected);
            btn.textContent = collected ? t("collected") : t("collect");
            btn.title = collected ? t("collectCancel") : t("collect");
        });
    } catch (err) {
        console.warn("refreshCollectButtons failed:", err);
    }
}

function showCollectError(msg) {
    collectError.textContent = msg || "";
    collectError.classList.remove("hidden");
}

function closeCollectModal() {
    collectModal.classList.add("hidden");
}

// Dialog: pick an existing collection or create a new one
async function openCollectModal(pid, title, difficulty) {
    collectTarget = { pid, title, difficulty };
    collectTitle.textContent = t("collectDialogTitle", `${pid} · ${title}`);
    collectError.classList.add("hidden");
    collectNewName.value = "";
    collectList.innerHTML = "";
    let lists = [];
    try {
        lists = await getCollections();
    } catch (err) {
        showCollectError(err.message);
    }
    if (!lists.length) {
        collectList.innerHTML = `<div class="profile-empty">${escapeHtml(t("emptyCollections"))}</div>`;
    } else {
        lists.forEach((lst) => {
            const item = document.createElement("button");
            item.type = "button";
            item.className = "collect-list-item";
            item.textContent = `${lst.name} (${(lst.problems || []).length})`;
            item.title = t("collectTo");
            item.addEventListener("click", async () => {
                try {
                    await apiCall("add_to_collection", pid, lst.id, title, difficulty);
                    await refreshCollections();
                    await refreshCollectButtons();
                    if (!profileModal.classList.contains("hidden")) renderProfileCollections();
                    closeCollectModal();
                } catch (err) {
                    showCollectError(err.message);
                }
            });
            collectList.appendChild(item);
        });
    }
    collectModal.classList.remove("hidden");
}

// Create a new collection, then add the current target problem into it
async function createCollectAndAdd() {
    const name = collectNewName.value.trim();
    if (!name) {
        showCollectError(t("collectNameEmpty"));
        return;
    }
    if (!collectTarget) return;
    try {
        const data = await apiCall("create_collection", name);
        await apiCall("add_to_collection", collectTarget.pid, data.collection.id,
            collectTarget.title, collectTarget.difficulty);
        await refreshCollections();
        await refreshCollectButtons();
        if (!profileModal.classList.contains("hidden")) renderProfileCollections();
        closeCollectModal();
    } catch (err) {
        showCollectError(err.message);
    }
}

function openUncollectModal(pid, title) {
    uncollectPid = pid;
    uncollectTitle.textContent = t("uncollectTitle");
    uncollectText.textContent = t("uncollectText", `${pid} · ${title}`);
    uncollectModal.classList.remove("hidden");
}

function closeUncollectModal() {
    uncollectModal.classList.add("hidden");
    uncollectPid = null;
}

async function confirmUncollect() {
    if (!uncollectPid) return;
    try {
        await apiCall("remove_from_collection", uncollectPid);
        await refreshCollections();
        await refreshCollectButtons();
        if (!profileModal.classList.contains("hidden")) renderProfileCollections();
        closeUncollectModal();
    } catch (err) {
        uncollectText.textContent = err.message || t("requestFailed", "?");
    }
}

// Render the user's 题单 in the profile modal; clicking a problem opens it
async function renderProfileCollections() {
    let lists = [];
    try {
        lists = await getCollections();
    } catch (err) {
        profileCollections.innerHTML = `<div class="profile-empty">${escapeHtml(err.message || t("profileLoadFailed"))}</div>`;
        return;
    }
    if (!lists.length) {
        profileCollections.innerHTML = `<div class="profile-empty">${escapeHtml(t("emptyCollections"))}</div>`;
        return;
    }
    profileCollections.innerHTML = lists.map((lst) => {
        const probs = lst.problems || [];
        return `
        <div class="collection-block">
            <div class="collection-block-header">
                <span class="collection-name">${escapeHtml(lst.name)}</span>
                <span class="collection-count">${probs.length} ${escapeHtml(t("profileTypeCount"))}</span>
            </div>
            <div class="collection-problems">
                ${probs.length
                    ? probs.map((p) => `
                        <button type="button" class="collection-problem" data-pid="${escapeHtml(p.pid)}" data-title="${escapeHtml(p.title || "")}">
                            <span class="collection-problem-pid">${escapeHtml(p.pid)}</span>
                            <span class="collection-problem-title">${escapeHtml(p.title || "")}</span>
                        </button>`).join("")
                    : `<span class="profile-empty">${escapeHtml(t("emptyCollectionsProblems"))}</span>`}
            </div>
        </div>`;
    }).join("");
    profileCollections.querySelectorAll(".collection-problem").forEach((btn) => {
        btn.addEventListener("click", () => {
            const pid = btn.dataset.pid;
            if (!pid) return;
            closeProfileModal();
            problemIdInput.value = pid;
            searchResults.classList.add("hidden");
            loadProblemOnly(pid);
        });
    });
}

function renderProfileChart(stats) {
    if (profileChart) {
        profileChart.destroy();
        profileChart = null;
    }
    const labels = getDifficultyNames();
    const passedData = [];
    const attemptedData = [];
    for (let i = 0; i < 9; i++) {
        const s = stats[i] || { passed: 0, submitted: 0 };
        passedData.push(s.passed);
        attemptedData.push(s.submitted - s.passed);
    }
    const isDark = isDarkTheme(document.documentElement.getAttribute("data-theme"));
    const gridColor = isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)";
    const textColor = isDark ? "#ccc" : "#333";

    profileChart = new Chart($("#profileChart"), {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: t("profilePassed"),
                    data: passedData,
                    borderColor: "#52c41a",
                    backgroundColor: "rgba(82,196,26,0.15)",
                    tension: 0.3,
                    fill: true,
                },
                {
                    label: t("profileAttempted"),
                    data: attemptedData,
                    borderColor: "#faad14",
                    backgroundColor: "rgba(250,173,20,0.15)",
                    tension: 0.3,
                    fill: true,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            // Hovering any point on a difficulty shows both series for that difficulty
            interaction: {
                mode: "index",
                intersect: false,
            },
            plugins: {
                legend: { labels: { color: textColor } },
                tooltip: {
                    backgroundColor: isDark ? "rgba(30,30,30,0.92)" : "rgba(255,255,255,0.96)",
                    titleColor: textColor,
                    bodyColor: textColor,
                    borderColor: gridColor,
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                        // Show the hovered difficulty's submission info
                        label: (ctx) => {
                            const s = stats[ctx.dataIndex] || { passed: 0, submitted: 0 };
                            if (ctx.datasetIndex === 0) {
                                return ` ${t("profilePassed")}: ${s.passed}   ${t("profileTotalSubmit")}: ${s.submitted}`;
                            }
                            return ` ${t("profileAttempted")}: ${Math.max(0, s.submitted - s.passed)}`;
                        },
                        footer: (items) => {
                            if (!items.length) return [];
                            const s = stats[items[0].dataIndex] || { passed: 0, submitted: 0 };
                            const rate = s.submitted > 0 ? ((s.passed / s.submitted) * 100).toFixed(1) + "%" : "--";
                            return [`${t("profileRate")}: ${rate}`];
                        },
                    },
                },
            },
            scales: {
                x: { ticks: { color: textColor }, grid: { color: gridColor } },
                y: {
                    ticks: { color: textColor, precision: 0 },
                    grid: { color: gridColor },
                    beginAtZero: true,
                },
            },
        },
    });
}

// =========================================================================
// Opened problem tabs (multi-tab)
// =========================================================================
function renderOpenTabs() {
    const bar = document.getElementById("openTabs");
    if (!bar) return;
    if (!openTabs.length) {
        bar.classList.add("hidden");
        bar.innerHTML = "";
        return;
    }
    bar.classList.remove("hidden");
    bar.innerHTML = openTabs.map((tab) => `
        <div class="open-tab${tab.pid === activeTabPid ? " active" : ""}" data-pid="${escapeHtml(tab.pid)}" title="${escapeHtml(tab.title || tab.pid)}">
            <span class="open-tab-pid">${escapeHtml(tab.pid)}</span>
            <span class="open-tab-close" data-pid="${escapeHtml(tab.pid)}" title="${t("tabClose")}">×</span>
        </div>`).join("");
    bar.querySelectorAll(".open-tab").forEach((el) => {
        el.addEventListener("click", (e) => {
            if (e.target.classList.contains("open-tab-close")) return;
            switchProblemTab(el.dataset.pid);
        });
    });
    bar.querySelectorAll(".open-tab-close").forEach((el) => {
        el.addEventListener("click", (e) => {
            e.stopPropagation();
            closeProblemTab(el.dataset.pid);
        });
    });
}

function activateProblemTab(pid, title) {
    if (!pid) return;
    const existing = openTabs.find((tab) => tab.pid === pid);
    if (existing) {
        // Already open: keep its position, just refresh title
        if (title) existing.title = title;
    } else {
        openTabs.push({ pid, title: title || pid });
        if (openTabs.length > MAX_OPEN_TABS) openTabs.shift();
    }
    activeTabPid = pid;
    renderOpenTabs();
}

function closeProblemTab(pid) {
    openTabs = openTabs.filter((tab) => tab.pid !== pid);
    delete problemDataCache[pid];
    renderOpenTabs();
    if (activeTabPid === pid) {
        activeTabPid = null;
        if (openTabs.length) {
            switchProblemTab(openTabs[openTabs.length - 1].pid);
        }
    }
}

function switchProblemTab(pid) {
    if (!pid || (pid === activeTabPid && currentProblem && currentProblem.pid === pid)) return;
    problemIdInput.value = pid;
    activeTabPid = pid;
    renderOpenTabs();
    loadProblemOnly(pid);
}

// =========================================================================
// Main analyze flow
// =========================================================================
async function loadProblemOnly(problemId, opts) {
    if (!problemId) return;
    // Reset cached AI translation when switching problems
    problemTranslationCache = null;
    // opts.contestId keeps contest submission context active (contest problem);
    // otherwise clear it so a normal problem never submits into a stale contest.
    currentContestId = (opts && opts.contestId) ? String(opts.contestId) : "";
    hideStatus();
    try {
        // 切换题目前，先自动保存旧题的未提交代码草稿
        const oldPid = draftPid || (currentProblem ? currentProblem.pid : null);
        const oldCode = codeEditor.value;
        if (oldPid && oldPid !== problemId && oldCode.trim()) {
            await persistDraft(oldPid, oldCode);
        }
        showLoading(t("loadingProblem"));
        let problemData = problemDataCache[problemId];
        if (!problemData) {
            problemData = detectOj(problemId) === "atcoder"
                ? await apiGet(`/api/atcoder-problem/${encodeURIComponent(problemId)}`)
                : await apiGet(`/api/problem/${encodeURIComponent(problemId)}`);
            problemDataCache[problemId] = problemData;
        }
        currentProblem = problemData.problem;
        renderProblem(currentProblem);
        updateSubmitPanel();
        refreshAssistantContext();
        currentRid = null;
        // Load this problem's saved draft (if any); otherwise start empty
        const draft = await fetchDraft(currentProblem.pid);
        codeEditor.value = draft;
        draftPid = currentProblem.pid;
        syncCodeHighlight();
        updateSubmitButtonState();
        setDraftStatus(draft ? t("draftLoaded") : "");
        // Clear current judge result (history is rendered separately)
        judgeResult.innerHTML = "";
        judgeResult.classList.add("hidden");
        // Render submission history for this problem (if any)
        renderSubmissionHistory(currentProblem.pid);
        // Reset solutions & analysis panes to placeholders
        currentSolutions = [];
        solutionsContent.innerHTML = `
            <div class="placeholder">
                <p>${t("placeholderClickAnalyze")}</p>
                <p class="placeholder-sub">${t("placeholderClickAnalyzeSub")}</p>
            </div>`;
        renderAnalysisPlaceholder(t("placeholderClickAnalysis"), t("placeholderClickAnalysisSub"));
        switchView("problem");
        activateProblemTab(currentProblem.pid, currentProblem.title || currentProblem.pid);
    } catch (err) {
        showStatus("error", err.message || t("errorGetProblem"));
    } finally {
        hideLoading();
    }
}

async function analyze() {
    const problemId = problemIdInput.value.trim();
    const luoguCookie = luoguCookieInput.value.trim();
    const model = modelSelect.value;
    // Pick the API key matching the selected model's provider:
    // GLM models use the GLM key, everything else uses the DeepSeek key.
    const glm = isGlmModel(model);
    const apiKeyInputEl = glm ? glmApiKeyInput : apiKeyInput;
    const apiKey = apiKeyInputEl.value.trim();
    const providerName = glm ? "GLM" : "DeepSeek";

    if (!problemId) {
        showStatus("error", t("errorEnterProblemId"));
        problemIdInput.focus();
        return;
    }

    // In AI mode, warn if no API key for the selected provider
    if (analysisMode === "ai" && !apiKey) {
        showStatus("error", t("errorNeedApiKey", providerName));
        apiKeyInputEl.focus();
        return;
    }

    // Reset
    hideStatus();
    analyzeBtn.disabled = true;
    // Normal (non-contest) problem flows clear any contest submission context.
    currentContestId = "";
    currentProblem = null;
    currentSolutions = [];

    // Stop any pending judge poll and clear submit panel state
    if (submitPollTimer) {
        clearTimeout(submitPollTimer);
        submitPollTimer = null;
    }
    currentRid = null;

    let solutionsFailed = false;
    let solutionsError = null;

    try {
        // Step 1: Start both fetches in parallel
        showLoading(t("loadingProblem"));

        // Show loading state in solutions tab while fetching
        solutionsContent.innerHTML = `
            <div class="placeholder">
                <p>${t("loadingSolutions")}</p>
            </div>`;

        // Start both promises concurrently
        const problemPromise = (async () => {
            let problemData = problemDataCache[problemId];
            if (!problemData) {
                problemData = detectOj(problemId) === "atcoder"
                    ? await apiGet(`/api/atcoder-problem/${encodeURIComponent(problemId)}`)
                    : await apiGet(`/api/problem/${problemId}`);
                problemDataCache[problemId] = problemData;
            }
            return problemData;
        })();

        const solutionsPromise = (async () => {
            try {
                const cookieParam = luoguCookie ? `?cookie=${encodeURIComponent(luoguCookie)}` : "";
                return await apiGet(`/api/solutions/${problemId}${cookieParam}`);
            } catch (err) {
                solutionsFailed = true;
                solutionsError = err;
                return null;
            }
        })();

        // Process problem as soon as it arrives
        const problemData = await problemPromise;
        currentProblem = problemData.problem;
        renderProblem(currentProblem);
        updateSubmitPanel();
        refreshAssistantContext();
        // Clear code editor and judge result for the new problem
        codeEditor.value = "";
        syncCodeHighlight();
        updateSubmitButtonState();
        judgeResult.innerHTML = "";
        judgeResult.classList.add("hidden");
        renderSubmissionHistory(currentProblem.pid);
        activateProblemTab(currentProblem.pid, currentProblem.title || currentProblem.pid);

        // Process solutions when ready (AtCoder solutions are fetched from
        // the AtCoder editorial page via /api/solutions/<raw_id>)
        const solutionsData = await solutionsPromise;
        if (solutionsData) {
            currentSolutions = solutionsData.solutions;
            lastSolutionTotal = solutionsData.total_solutions;
            renderSolutions(currentSolutions, lastSolutionTotal);
        } else {
            currentSolutions = [];
            solutionsContent.innerHTML = `
                <div class="placeholder">
                    <p>${escapeHtml(solutionsError ? solutionsError.message : t("errorGetSolutions"))}</p>
                    <p class="placeholder-sub">${t("errorGetSolutionsSub")}</p>
                </div>`;
        }

        // Switch to problem tab
        switchView("problem");

        // Step 3: AI analysis (only in AI mode with API key)
        if (analysisMode === "ai" && apiKey) {
            const loadingMsg = solutionsFailed
                ? t("loadingAnalysisNoSol", providerName)
                : t("loadingAnalysis", providerName);
            showLoading(loadingMsg);
            const analysisData = await apiPost("/api/analyze", {
                api_key: apiKey,
                model: model,
                problem: currentProblem,
                solutions: currentSolutions,
            });
            renderAnalysis(analysisData.analysis, analysisData.model);
            if (solutionsFailed) {
                showStatus("success", t("successAnalyzeNoSol"));
            } else {
                showStatus("success", t("successAnalyze", model));
            }
            switchView("analysis");
        } else {
            // Filter mode: only show filtered solutions, no AI analysis
            const filterError = solutionsError && solutionsError.message
                ? solutionsError.message
                : t("errorFilterFailed");
            renderAnalysisPlaceholder(
                t("placeholderFilterMode"),
                solutionsFailed ? filterError : t("placeholderFilterModeSub")
            );
            if (solutionsFailed) {
                showStatus("error", filterError);
            } else {
                showStatus("info", t("infoFilterMode"));
                switchView("solutions");
            }
        }
    } catch (err) {
        console.error("Analyze error:", err);
        showStatus("error", err.message || t("errorAnalyze"));
        if (currentProblem) {
            switchView("problem");
        }
    } finally {
        hideLoading();
        analyzeBtn.disabled = false;
    }
}

// =========================================================================
// AI Assistant (streaming chat panel, right of the analysis window)
// =========================================================================
let assistantHistory = [];       // [{role, content}] sent to the backend
let assistantStreaming = false;  // a reply is currently streaming
let assistantBubble = null;      // current assistant DOM bubble
let assistantThinkingEl = null;  // collapsible reasoning block in the bubble
let assistantBubbleDone = false; // current bubble has been finalized (done/error)

function assistantRenderMarkdown(text) {
    // Reuse the project-wide renderMarkdown (marked + hljs + KaTeX).
    const tmp = document.createElement("div");
    tmp.innerHTML = renderMarkdown(text);
    return tmp.innerHTML;
}

function assistantScrollToBottom() {
    const box = document.getElementById("assistantMessages");
    if (box) box.scrollTop = box.scrollHeight;
}

function assistantUpdateContext() {
    const el = document.getElementById("assistantContext");
    if (!el) return;
    if (currentProblem && currentProblem.pid) {
        el.innerHTML = `<span class="assistant-context-active" data-i18n="assistantContextProblem">当前题目：</span>` +
            `<span class="assistant-context-pid">${escapeHtml(currentProblem.pid)}</span>` +
            ` <span class="assistant-context-name">${escapeHtml(currentProblem.title || "")}</span>`;
    } else {
        el.innerHTML = `<span data-i18n="assistantNoContext">可自由提问，或针对当前题目提问</span>`;
    }
    // Re-apply i18n for the injected static label.
    const ctxLabel = el.querySelector("[data-i18n]");
    if (ctxLabel && typeof t === "function") ctxLabel.textContent = t("assistantContextProblem");
}

function assistantAddUserMessage(text) {
    const box = document.getElementById("assistantMessages");
    const row = document.createElement("div");
    row.className = "assistant-msg assistant-msg-user";
    row.innerHTML = `<div class="assistant-msg-bubble">${escapeHtml(text)}</div>`;
    box.appendChild(row);
    assistantScrollToBottom();
}

function assistantStartBubble() {
    const box = document.getElementById("assistantMessages");
    const row = document.createElement("div");
    row.className = "assistant-msg assistant-msg-ai";
    row.innerHTML = `
        <div class="assistant-thinking" style="display:none;"><div class="assistant-thinking-head">${escapeHtml(t("assistantThinkingBlock"))}</div><div class="assistant-thinking-body markdown-body"></div></div>
        <div class="assistant-msg-bubble markdown-body assistant-ai-body"></div>
        <div class="assistant-typing">${escapeHtml(t("assistantTyping"))}</div>`;
    box.appendChild(row);
    assistantThinkingEl = row.querySelector(".assistant-thinking");
    assistantBubble = row.querySelector(".assistant-ai-body");
    assistantBubbleDone = false;
    return row;
}

function assistantAppend(kind, text) {
    if (!assistantBubble) return;
    if (kind === "reasoning") {
        if (assistantThinkingEl) {
            assistantThinkingEl.style.display = "block";
            const body = assistantThinkingEl.querySelector(".assistant-thinking-body");
            body.innerHTML = assistantRenderMarkdown(body.textContent + text);
            // Re-render for correct markdown (textContent round-trip).
        }
    } else if (kind === "content") {
        // Append raw text, then re-render the full accumulated markdown.
        assistantBubble.dataset.raw = (assistantBubble.dataset.raw || "") + text;
        assistantBubble.innerHTML = assistantRenderMarkdown(assistantBubble.dataset.raw);
    }
    assistantScrollToBottom();
}

function assistantFinish(ok, errorText) {
    if (assistantBubbleDone) return; // ignore duplicate done/error signals
    assistantBubbleDone = true;
    const row = document.querySelector("#assistantMessages .assistant-msg-ai:last-child");
    if (row) {
        const typing = row.querySelector(".assistant-typing");
        if (typing) typing.remove();
    }
    const raw = assistantBubble ? (assistantBubble.dataset.raw || "") : "";
    if (!raw && !errorText) {
        if (row) {
            const body = row.querySelector(".assistant-ai-body");
            if (body) body.innerHTML = `<span style="color:var(--muted)">${escapeHtml(t("assistantEmpty"))}</span>`;
        }
    } else if (errorText) {
        // Show an inline error bubble on failure.
        const box = document.getElementById("assistantMessages");
        const err = document.createElement("div");
        err.className = "assistant-msg assistant-msg-error";
        err.textContent = errorText;
        box.appendChild(err);
    }
    if (raw) {
        assistantHistory.push({ role: "assistant", content: raw });
    }
    assistantBubble = null;
    assistantThinkingEl = null;
    assistantStreaming = false;
    assistantScrollToBottom();
}

async function assistantSend() {
    const input = document.getElementById("assistantInput");
    const text = (input.value || "").trim();
    if (!text || assistantStreaming) return;
    if (!currentProblem && !confirm(t("assistantNoProblemConfirm"))) {
        return;
    }
    input.value = "";
    input.style.height = "auto";
    assistantAddUserMessage(text);
    assistantHistory.push({ role: "user", content: text });

    assistantStartBubble();
    assistantStreaming = true;
    const thinking = document.getElementById("assistantThinking").checked;

    const problemCtx = currentProblem
        ? {
            pid: currentProblem.pid,
            title: currentProblem.title,
            description: currentProblem.description,
            inputFormat: currentProblem.inputFormat,
            outputFormat: currentProblem.outputFormat,
          }
        : {};

    try {
        const res = await apiCall("assistant_chat", assistantHistory, problemCtx, thinking);
        // 'done' / 'error' are delivered via __aiStream, which finalizes the
        // bubble. res only carries the final status; do NOT call
        // assistantFinish() again here or the bubble would be overwritten.
        if (res && res.success === false && res.error) {
            assistantFinish(false, res.error);
        }
    } catch (err) {
        assistantFinish(false, err.message || t("assistantFailed"));
    }
}

// Streaming entry point invoked by the backend via evaluate_js.
window.__aiStream = function (kind, text) {
    if (kind === "done") {
        if (assistantStreaming) assistantFinish(true, "");
        return;
    }
    if (kind === "error") {
        if (assistantStreaming) assistantFinish(false, text);
        return;
    }
    if (assistantStreaming) assistantAppend(kind, text);
};

function assistantInit() {
    const sendBtn = document.getElementById("assistantSendBtn");
    const input = document.getElementById("assistantInput");
    const clearBtn = document.getElementById("assistantClearBtn");
    const thinking = document.getElementById("assistantThinking");

    if (sendBtn) sendBtn.addEventListener("click", assistantSend);
    if (input) {
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                assistantSend();
            }
        });
        // Auto-grow the input up to a few lines.
        input.addEventListener("input", () => {
            input.style.height = "auto";
            input.style.height = Math.min(input.scrollHeight, 120) + "px";
        });
    }
    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            assistantHistory = [];
            const box = document.getElementById("assistantMessages");
            if (box) box.innerHTML = "";
        });
    }
    if (thinking) thinking.checked = false;

    assistantUpdateContext();
    window.addEventListener("assistantContextRefresh", assistantUpdateContext);
}

// Refresh the assistant's current-problem context when a problem loads.
function refreshAssistantContext() {
    window.dispatchEvent(new Event("assistantContextRefresh"));
}

// =========================================================================
// Daily features: toast / 打卡 / 统计热力图 / 比赛提醒 / 错因讲题
// =========================================================================
function showToast(message, type = "info", duration = 3500) {
    if (!toastContainer) return;
    const el = document.createElement("div");
    el.className = `toast toast-${type}`;
    el.textContent = message;
    toastContainer.appendChild(el);
    requestAnimationFrame(() => el.classList.add("show"));
    setTimeout(() => {
        el.classList.remove("show");
        setTimeout(() => el.remove(), 300);
    }, duration);
}

async function doCheckin() {
    try {
        const data = await apiCall("checkin");
        if (data.already) {
            showToast(t("checkinAlready"), "info");
        } else {
            showToast(t("checkinSuccess"), "success");
        }
        return data;
    } catch (err) {
        const msg = err.message || "";
        // Only show the "need cookie" prompt when no cookie is actually
        // saved; otherwise surface the real failure reason (e.g. expired
        // cookie, network error) instead of a misleading message.
        showToast(err.no_cookie ? t("checkinNeedCookie") : t("checkinFail", msg), "error");
        return null;
    }
}

// Hue per Luogu difficulty (difficulty decides hue).
// 0/unknown has no hue -> falls back to the theme's gray border color.
const HEATMAP_DIFF_HUES = {
    1: 345,   // 入门 - 粉红
    2: 30,    // 普及- - 橙黄→橙
    3: 48,    // 普及 - 黄
    4: 120,   // 普及+/提高- - 绿
    5: 185,   // 提高 - 青
    6: 210,   // 提高+/省选- - 浅蓝
    7: 255,   // 省选/NOI- - 蓝紫 (扩展)
    8: 285,   // NOI/NOI+/CTS - 深紫 (扩展)
};

function heatmapColor(count, difficulty) {
    // Empty / zero-AC day: keep the default border (gray) color.
    if (!count || count <= 0) return "";
    const hue = HEATMAP_DIFF_HUES[difficulty];
    if (hue === undefined) return "";  // unknown difficulty -> gray
    // Depth tiers by submission count (count decides depth).
    // Luogu tiers: 0=灰, ≤3=最浅, ≤5=较浅, ≤8=中等, >8=最深.
    let sat, light;
    if (count <= 3) { sat = 60; light = 75; }
    else if (count <= 5) { sat = 75; light = 62; }
    else if (count <= 8) { sat = 85; light = 50; }
    else { sat = 90; light = 35; }
    return `hsl(${hue} ${sat}% ${light}%)`;
}

// Official legend only shows the green (difficulty 4) depth scale.
function renderHeatmapLegend() {
    const legend = document.getElementById("heatmapLegend");
    if (!legend) return;
    const green = HEATMAP_DIFF_HUES[4];
    const tiers = [["", "0"], [`hsl(${green} 60% 75%)`, "≤3"],
                   [`hsl(${green} 75% 62%)`, "≤5"],
                   [`hsl(${green} 85% 50%)`, "≤8"],
                   [`hsl(${green} 90% 35%)`, ">8"]];
    legend.innerHTML = tiers.map(([bg]) =>
        `<span class="hm-legend-swatch" style="background:${bg || "var(--border)"}"></span>`
    ).join("");
}

function renderHeatmap(data) {
    if (!statsHeatmap) return;
    const total = data.total || 0;
    const streak = data.streak || { current: 0, longest: 0 };
    // Summary line: total + current/longest streak (with a 🔥 for a live streak)
    const streakBits = [];
    if (streak.current > 0) streakBits.push(t("heatmapStreak", String(streak.current)));
    if (streak.longest > 1) streakBits.push(t("heatmapStreakLongest", String(streak.longest)));
    statsSummary.innerHTML = streak.current > 0
        ? `${escapeHtml(t("heatmapTotal", String(total)))} · <span class="hm-streak">🔥 ${escapeHtml(streakBits.join(" · "))}</span>`
        : escapeHtml(t("heatmapTotal", String(total)));
    if (total === 0) {
        statsHeatmap.innerHTML = `<div class="stats-empty">${escapeHtml(t("heatmapEmpty"))}</div>`;
        return;
    }
    const weeks = data.weeks || [];
    let html = '<div class="hm-grid">';
    weeks.forEach((week) => {
        week.forEach((cell) => {
            const count = cell.count || 0;
            const difficulty = cell.difficulty || 0;
            const difficultyNames = ['', '入门', '普及-', '普及', '普及+/提高-', '提高', '提高+/省选-', '省选/NOI-', 'NOI/NOI+/CTS'];
            const difficultyText = difficulty ? difficultyNames[difficulty] || '暂无评定' : '暂无评定';
            const title = `${cell.date}: ${count}题 (${difficultyText}难度)`;
            const bg = heatmapColor(count, difficulty);
            const style = bg ? ` style="background:${bg}"` : "";
            html += `<div class="hm-cell" data-hm-date="${escapeHtml(cell.date)}" data-hm-count="${count}" data-hm-difficulty="${difficulty}" title="${escapeHtml(title)}"${style}></div>`;
        });
    });
    html += "</div>";
    statsHeatmap.innerHTML = html;
    renderHeatmapLegend();
    bindHeatmapTooltip();
}

// Custom hover tooltip for the heatmap (native title is unreliable in WebView)
function bindHeatmapTooltip() {
    const wrap = statsHeatmap;
    if (!wrap) return;
    let tip = document.getElementById("hmTooltip");
    if (!tip) {
        tip = document.createElement("div");
        tip.id = "hmTooltip";
        tip.className = "hm-tooltip";
        tip.style.display = "none";
        document.body.appendChild(tip);
    }
    wrap.addEventListener("mouseover", (e) => {
        const cell = e.target.closest(".hm-cell");
        if (!cell) { tip.style.display = "none"; return; }
        const date = cell.dataset.hmDate || "";
        const count = cell.dataset.hmCount || "0";
        const difficulty = cell.dataset.hmDifficulty || "1";
const difficultyNames = ['', '入门', '普及-', '普及', '普及+/提高-', '提高', '提高+/省选-', '省选/NOI-', 'NOI/NOI+/CTS'];
const difficultyText = difficultyNames[parseInt(difficulty)] || '暂无评定';
tip.textContent = `${date} · ${count}题 · ${difficultyText}难度`;
        tip.style.display = "block";
    });
    wrap.addEventListener("mousemove", (e) => {
        if (tip.style.display === "none") return;
        const pad = 10;
        tip.style.left = (e.clientX + pad) + "px";
        tip.style.top = (e.clientY + pad) + "px";
    });
    wrap.addEventListener("mouseleave", () => {
        tip.style.display = "none";
    });
}

// openStats function removed as stats modal is integrated into profile modal
// async function openStats() {
//     if (!statsModal) return;
//     statsSummary.textContent = "...";
//     statsHeatmap.innerHTML = "";
//     statsModal.classList.remove("hidden");
//     switchStatsTab("heatmap");
//     try {
//         const data = await apiCall("get_heatmap");
//         renderHeatmap(data);
//     } catch (err) {
//         statsSummary.textContent = "";
//         statsHeatmap.innerHTML = `<div class="stats-empty">${escapeHtml(err.message || t("requestFailed", "?"))}</div>`;
//     }
// }

// Stats tab switching for personal center integration
function switchStatsTab(tab) {
    const heatView = document.getElementById("statsHeatmapView");
    const advView = document.getElementById("statsAdvancedView");
    const tabs = document.querySelectorAll(".stats-tab");
    if (heatView && advView) {
        heatView.classList.toggle("hidden", tab !== "heatmap");
        advView.classList.toggle("hidden", tab !== "advanced");
    }
    tabs.forEach((tb) => tb.classList.toggle("active", tb.dataset.statsTab === tab));
    if (tab === "advanced") {
        renderAdvancedStats();
    }
}

// Language id -> readable name for advanced stats charts
function advLangName(langId) {
    if (langSelect) {
        const opt = Array.from(langSelect.options).find((o) => String(o.value) === String(langId));
        if (opt) return opt.text;
    }
    const map = { 1: "Pascal", 2: "C", 3: "C++98", 4: "C++11", 7: "Python 3",
                  8: "Java 8", 9: "Node.js", 11: "C++14", 12: "C++17", 13: "Ruby",
                  14: "Go", 15: "Rust", 16: "PHP", 17: "C#", 19: "Haskell",
                  21: "Kotlin", 25: "PyPy 3", 27: "C++20", 28: "C++14 (GCC 9)",
                  33: "Java 21" };
    return map[langId] || "Lang " + langId;
}

function advStatusName(code) {
    const st = STATUS_MAP[code];
    return st ? t(st.key) : ("#" + code);
}

async function renderAdvancedStats() {
    const summaryEl = document.getElementById("advStatsSummary");
    if (!summaryEl) return;
    summaryEl.textContent = t("advStatsEmpty");
    // Destroy previously created charts so re-renders don't stack canvases.
    if (window.advCharts && Array.isArray(window.advCharts)) {
        window.advCharts.forEach((c) => { try { c.destroy(); } catch (e) {} });
    }
    window.advCharts = [];
    window.advStatusFilter = null;
    const registerChart = (ctx, chart) => { if (chart) window.advCharts.push(chart); };
    try {
        const data = window.advStatsCache || await apiCall("get_advanced_stats");
        window.advStatsCache = data;
        summaryEl.textContent = t("advStatsSummary",
            String(data.totalSubmissions || 0),
            String(data.totalAC || 0),
            String(data.acRate || 0),
            String(data.totalProblems || 0));

        // Status distribution (doughnut)
        const statusKeys = Object.keys(data.statusCounts || {});
        const statusLabels = statusKeys.map((k) => advStatusName(parseInt(k, 10)));
        const statusValues = Object.values(data.statusCounts || {});
        const statusTotal = statusValues.reduce((a, b) => a + b, 0);
        const statusColors = statusKeys.map((k) => {
            const st = STATUS_MAP[parseInt(k, 10)];
            return st ? st.color : "#8c8c8c";
        });
        const statusCtx = document.getElementById("advStatusChart");
        if (statusCtx && window.Chart) {
            registerChart(statusCtx, new Chart(statusCtx, {
                type: "doughnut",
                data: { labels: statusLabels, datasets: [{ data: statusValues, backgroundColor: statusColors }] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: "nearest", intersect: true },
                    hover: { mode: "nearest", intersect: true },
                    plugins: {
                        legend: { position: "bottom", labels: { color: "var(--muted)", font: { size: 11 } } },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => {
                                    const v = ctx.parsed || 0;
                                    const pct = statusTotal ? (v / statusTotal * 100).toFixed(1) : "0";
                                    return `${ctx.label}: ${v} (${pct}%)`;
                                },
                            },
                        },
                    },
                    // Click a status slice to filter the problem ranking list below.
                    onClick: (evt, items) => {
                        if (!items || !items.length) return;
                        const idx = items[0].index;
                        const statusCode = parseInt(statusKeys[idx], 10);
                        filterAdvProblemList(data, statusCode, statusKeys, statusValues);
                    },
                },
            }));
        }

        // Language distribution (bar)
        const langLabels = Object.keys(data.langCounts || {}).map((k) => advLangName(parseInt(k, 10)));
        const langValues = Object.values(data.langCounts || {});
        const langCtx = document.getElementById("advLangChart");
        if (langCtx && window.Chart) {
            registerChart(langCtx, new Chart(langCtx, {
                type: "bar",
                data: { labels: langLabels, datasets: [{ label: t("submitShort"), data: langValues, backgroundColor: "#5b8ff9", borderRadius: 4 }] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: "nearest", intersect: true },
                    hover: { mode: "nearest", intersect: true },
                    plugins: {
                        legend: { display: false },
                        tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y}` } },
                    },
                    scales: { 
                        x: { 
                            ticks: { color: "var(--muted)" },
                            maxTicksLimit: 8 
                        }, 
                        y: { 
                            ticks: { color: "var(--muted)" }, 
                            beginAtZero: true,
                            max: Math.max(...langValues, 10),
                            suggestedMax: Math.max(...langValues, 10)
                        } 
                    },
                },
            }));
        }

        // Daily trend (last 30 days line)
        const days = (data.days || []).slice(-30);
        const dayCtx = document.getElementById("advDayChart");
        if (dayCtx && window.Chart) {
            registerChart(dayCtx, new Chart(dayCtx, {
                type: "line",
                data: {
                    labels: days.map((d) => d.date.slice(5)),
                    datasets: [{ label: t("submitShort"), data: days.map((d) => d.count), borderColor: "#13c2c2", backgroundColor: "rgba(19,194,194,0.15)", fill: true, tension: 0.3, pointRadius: 2 }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: "nearest", intersect: true },
                    hover: { mode: "nearest", intersect: true },
                    plugins: {
                        legend: { display: false },
                        tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y}` } },
                    },
                    scales: { 
                        x: { 
                            ticks: { color: "var(--muted)", maxTicksLimit: 10 }
                        }, 
                        y: { 
                            ticks: { color: "var(--muted)" }, 
                            beginAtZero: true,
                            max: Math.max(...days.map((d) => d.count), 10),
                            suggestedMax: Math.max(...days.map((d) => d.count), 10)
                        } 
                    },
                },
            }));
        }

        // Problem ranking list
        renderAdvProblemList((data.perProblem || []).slice(0, 12));
    } catch (err) {
        summaryEl.textContent = err.message || t("requestFailed", "?");
    }
}

// Render the "题目排名" list; `filterStatus` (optional) restricts the rows to
// problems whose latest/best status matches, used by the status chart click.
function renderAdvProblemList(problems, filterStatus) {
    const listEl = document.getElementById("advProblemList");
    if (!listEl) return;
    let rows = problems || [];
    if (filterStatus !== undefined && filterStatus !== null) {
        rows = rows.filter((p) => (p.statusCounts || {})[filterStatus]);
    }
    if (!rows.length) {
        listEl.innerHTML = `<div class="adv-stats-no-data">${escapeHtml(t("advStatsNoData"))}</div>`;
        return;
    }
    const max = Math.max(...rows.map((p) => p.submissions), 1);
    listEl.innerHTML = rows.map((p) => `
        <div class="adv-problem-item" data-pid="${escapeHtml(p.pid)}" title="${escapeHtml(t("submitShort"))}: ${p.submissions}">
            <span class="adv-problem-pid">${escapeHtml(p.pid)}</span>
            <div class="adv-problem-bar-wrap"><div class="adv-problem-bar" style="width:${(p.submissions / max * 100).toFixed(1)}%"></div></div>
            <span class="adv-problem-num">${p.submissions}${p.ac ? " ✓" : ""}</span>
        </div>`).join("");
    listEl.querySelectorAll(".adv-problem-item").forEach((item) => {
        item.addEventListener("click", () => {
            closeProfileModal();
            loadProblemOnly(item.dataset.pid);
        });
    });
}

// Click handler for the status doughnut: re-render the problem list filtered
// to submissions whose per-problem statusCounts contain the clicked status.
// Clicking the same slice again (or clicking the chart background) resets.
function filterAdvProblemList(data, statusCode, statusKeys, statusValues) {
    if (window.advStatusFilter === statusCode) {
        window.advStatusFilter = null;
        renderAdvProblemList((data.perProblem || []).slice(0, 12));
        showToast(t("advStatsFilterCleared"), "info");
        return;
    }
    window.advStatusFilter = statusCode;
    const problems = (data.perProblem || []).filter((p) => (p.statusCounts || {})[statusCode]);
    if (!problems.length) {
        showToast(t("advStatsNoMatch"), "info");
        return;
    }
    renderAdvProblemList(problems.slice(0, 12));
    showToast(t("advStatsFiltered", advStatusName(statusCode)), "info");
}

function difficultyText(diff) {
    const key = "diff" + String(diff);
    const txt = t(key);
    return txt && txt !== key ? txt : t("difficultyUnknown");
}

async function checkContestReminders(openModal = false, silent = false) {
    try {
        const data = await apiCall("contest_reminders", 24);
        const upcoming = data.upcoming || [];
        if (upcoming.length === 0) {
            if (!silent) showToast(t("contestReminderNone"), "info");
            return;
        }
        upcoming.forEach((c) => {
            showToast(t("contestReminderMsg", c.name || String(c.id), String(c.minutesUntilStart)), "info", 6000);
        });
    } catch (err) {
        if (!silent) showToast(t("contestReminderFail", err.message), "error");
    }
}

async function explainSubmissionFailure(record) {
    if (!currentProblem) {
        showToast(t("explainFailureNoRecord"), "error");
        return;
    }
    const pid = currentProblem.pid;
    const list = submissionHistory[pid] || [];
    let code = "", lang = 0;
    const sub = list.find((s) => String(s.rid) === String(record.rid));
    if (sub) {
        code = sub.code || "";
        lang = sub.lang || 0;
    }
    if (!code && codeEditor.value.trim()) {
        code = codeEditor.value;
        lang = parseInt(langSelect.value, 10) || 0;
    }
    if (!code) {
        showToast(t("explainFailureNoRecord"), "error");
        return;
    }
    // Show the analysis in the AI assistant panel.
    switchTab("analysis");
    assistantAddUserMessage(`${pid} ${currentProblem.title || ""} — ${t("explainFailureStart")}`);
    assistantStartBubble();
    assistantStreaming = true;
    try {
        await apiCall("explain_failure", currentProblem, code, lang, record, false);
    } catch (err) {
        showToast(t("explainFailureFail", err.message), "error");
        if (assistantStreaming) assistantFinish(false, err.message);
    }
}

function initDailyFeatures() {
    if (checkinBtn) checkinBtn.addEventListener("click", doCheckin);
    if (contestReminderBtn) contestReminderBtn.addEventListener("click", checkContestReminders);
    // Profile modal tabs (个人中心分类)
    document.querySelectorAll(".profile-tab").forEach((tb) => {
        tb.addEventListener("click", () => switchProfileTab(tb.dataset.profileTab));
    });
    // Stats modal tabs (热力图 / 进阶统计)
    document.querySelectorAll(".stats-tab").forEach((tb) => {
        tb.addEventListener("click", () => switchStatsTab(tb.dataset.statsTab));
    });
}

// =========================================================================
// Contest standings (比赛榜单)
// =========================================================================
const standingsModal = $("#standingsModal");
const standingsCloseBtn = $("#standingsCloseBtn");
const standingsInput = $("#standingsInput");
const standingsGoBtn = $("#standingsGoBtn");
const standingsContent = $("#standingsContent");

function openStandingsModal() {
    if (!standingsModal) return;
    standingsModal.classList.remove("hidden");
    if (currentContestId && standingsInput) {
        standingsInput.value = currentContestId;
    }
    if (standingsContent) {
        standingsContent.innerHTML = `<div class="placeholder"><p>${escapeHtml(t("standingsHint"))}</p></div>`;
    }
}

function closeStandingsModal() {
    if (standingsModal) standingsModal.classList.add("hidden");
}

async function loadStandings() {
    const cid = (standingsInput.value || "").trim();
    if (!cid) {
        showToast(t("standingsHint"), "info");
        return;
    }
    if (!standingsContent) return;
    standingsContent.innerHTML = `<div class="profile-loading"><div class="spinner"></div><p>${escapeHtml(t("standingsLoading"))}</p></div>`;
    try {
        const data = await apiCall("get_contest_standings", cid, 1);
        const players = data.players || [];
        if (!players.length) {
            standingsContent.innerHTML = `<div class="stats-empty">${escapeHtml(t("standingsEmpty"))}</div>`;
            return;
        }
        let html = `<div class="stats-summary">${escapeHtml(t("standingsName", data.contest.name || cid))} · ${escapeHtml(t("standingsTotal", String(data.total)))}</div>`;
        html += `<table class="standings-table"><thead><tr>
            <th>${escapeHtml(t("standingsRank"))}</th>
            <th>${escapeHtml(t("standingsUser"))}</th>
            <th>${escapeHtml(t("standingsScore"))}</th>
            <th>${escapeHtml(t("standingsTime"))}</th>
            <th></th>
        </tr></thead><tbody>`;
        players.forEach((p) => {
            const rankCls = p.rank <= 3 ? " standings-rank-top" : "";
            html += `<tr>
                <td class="${rankCls}">${escapeHtml(String(p.rank))}</td>
                <td><a class="standings-user-link" href="https://www.luogu.com.cn/user/${escapeHtml(String(p.uid))}" target="_blank" rel="noopener">${escapeHtml(p.name || p.uid)}</a></td>
                <td>${escapeHtml(String(p.score))}</td>
                <td>${escapeHtml(String(p.time))}</td>
                <td><a class="btn-link" href="https://www.luogu.com.cn/contest/${escapeHtml(cid)}/standings" target="_blank" rel="noopener">${escapeHtml(t("standingsOpenInLuogu"))}</a></td>
            </tr>`;
        });
        html += `</tbody></table>`;
        standingsContent.innerHTML = html;
    } catch (err) {
        standingsContent.innerHTML = `<div class="stats-empty">${escapeHtml(t("standingsFailed", err.message))}</div>`;
    }
}

// =========================================================================
// Wrong book (错题本)
// =========================================================================
const wrongBookModal = $("#wrongBookModal");
const wrongBookBtn = $("#wrongBookBtn");
const wrongBookCloseBtn = $("#wrongBookCloseBtn");
const wrongBookBody = $("#wrongBookBody");

async function openWrongBook() {
    if (!wrongBookModal) return;
    wrongBookModal.classList.remove("hidden");
    if (wrongBookBody) wrongBookBody.innerHTML = `<div class="placeholder"><p>${escapeHtml(t("wrongBookLoading"))}</p></div>`;
    try {
        const data = await apiCall("get_wrong_book");
        const problems = data.problems || [];
        if (!problems.length) {
            wrongBookBody.innerHTML = `<div class="stats-empty">${escapeHtml(t("wrongBookEmpty"))}</div>`;
            return;
        }
        let html = `<div class="stats-summary">${escapeHtml(t("wrongBookCount", String(problems.length)))}</div>`;
        problems.forEach((p) => {
            const timeStr = p.lastTime ? new Date(p.lastTime * 1000).toLocaleString() : "";
            html += `
                <div class="wrong-book-item" data-pid="${escapeHtml(p.pid)}">
                    <span class="wrong-book-pid">${escapeHtml(p.pid)}</span>
                    <div class="wrong-book-info">
                        <div class="wrong-book-meta">${escapeHtml(t("wrongBookSubmissions", String(p.count)))} · ${escapeHtml(timeStr)}</div>
                        <div><span class="wrong-book-status">${escapeHtml(t("wrongBookLastStatus", p.lastStatusText || String(p.lastStatus)))}</span></div>
                    </div>
                    <div class="wrong-book-actions">
                        <button type="button" class="btn-secondary" data-action="open" style="padding:4px 10px;font-size:12px;">${escapeHtml(t("wrongBookOpen"))}</button>
                        <button type="button" class="btn-primary" data-action="explain" style="padding:4px 10px;font-size:12px;">${escapeHtml(t("wrongBookAnalyze"))}</button>
                    </div>
                </div>`;
        });
        wrongBookBody.innerHTML = html;
        wrongBookBody.querySelectorAll(".wrong-book-item").forEach((item) => {
            const pid = item.dataset.pid;
            item.querySelector('[data-action="open"]').addEventListener("click", () => {
                closeWrongBook();
                loadProblemOnly(pid);
            });
            item.querySelector('[data-action="explain"]').addEventListener("click", () => {
                explainWrongBookProblem(pid);
            });
        });
    } catch (err) {
        wrongBookBody.innerHTML = `<div class="stats-empty">${escapeHtml(t("wrongBookFailed", err.message))}</div>`;
    }
}

function closeWrongBook() {
    if (wrongBookModal) wrongBookModal.classList.add("hidden");
}

async function explainWrongBookProblem(pid) {
    closeWrongBook();
    try {
        await loadProblemOnly(pid);
        const data = await apiCall("get_local_records", pid);
        const records = data.records || [];
        const failed = records.find((r) => r.status !== 12 && r.code);
        if (!failed) {
            showToast(t("explainFailureNoRecord"), "error");
            return;
        }
        const problem = currentProblem || { pid };
        switchTab("analysis");
        assistantAddUserMessage(`${pid} ${problem.title || ""} — ${t("explainFailureStart")}`);
        assistantStartBubble();
        assistantStreaming = true;
        try {
            await apiCall("explain_failure", problem, failed.code, failed.lang, {
                rid: failed.rid, status: failed.status, score: failed.score,
            }, false);
        } catch (err) {
            showToast(t("explainFailureFail", err.message), "error");
            if (assistantStreaming) assistantFinish(false, err.message);
        }
    } catch (err) {
        showToast(t("wrongBookFailed", err.message), "error");
    }
}

// =========================================================================
// Smart recommend (智能推荐)
// =========================================================================
const recommendModal = $("#recommendModal");
const recommendCloseBtn = $("#recommendCloseBtn");
const recommendBody = $("#recommendBody");
const recommendRefreshBtn = $("#recommendRefreshBtn");
const recommendGoBtn = $("#recommendGoBtn");
let recommendProblem = null;

async function openRecommend() {
    if (!recommendModal) return;
    recommendModal.classList.remove("hidden");
    await refreshRecommend();
}

function closeRecommend() {
    if (recommendModal) recommendModal.classList.add("hidden");
}

async function refreshRecommend() {
    if (recommendBody) recommendBody.innerHTML = `<div class="placeholder"><p>${escapeHtml(t("recommendLoading"))}</p></div>`;
    try {
        const data = await apiCall("smart_recommend");
        const p = data.problem || {};
        recommendProblem = p;
        if (!p.pid) {
            recommendBody.innerHTML = `<div class="stats-empty">${escapeHtml(t("recommendEmpty"))}</div>`;
            return;
        }
        const tags = Array.isArray(p.tags) ? p.tags : [];
        const tagsHtml = tags.length
            ? `<div class="daily-problem-tags">${tags.map(tg => `<span class="daily-problem-tag">${escapeHtml(tg)}</span>`).join("")}</div>`
            : "";
        recommendBody.innerHTML = `
            <div class="recommend-card">
                <div class="recommend-pid">${escapeHtml(p.pid)}</div>
                <div class="recommend-title">${escapeHtml(p.title || "")}</div>
                <div class="recommend-meta">${escapeHtml(t("difficulty"))}：${escapeHtml(difficultyText(p.difficulty))}</div>
                ${tagsHtml}
            </div>`;
    } catch (err) {
        recommendBody.innerHTML = `<div class="stats-empty">${escapeHtml(t("recommendFailed", err.message))}</div>`;
        recommendProblem = null;
    }
}

// =========================================================================
// Version diff (版本对比) + code export
// =========================================================================
const diffModal = $("#diffModal");
const diffCloseBtn = $("#diffCloseBtn");
const diffSubtitleEl = $("#diffSubtitle");
const diffContent = $("#diffContent");
const submissionExportBtn = $("#submissionExportBtn");
let lastViewedSubmission = null; // {pid, rid, code, lang}

function setSubmissionExportTarget(submission) {
    lastViewedSubmission = submission || null;
    if (submissionExportBtn) {
        submissionExportBtn.classList.toggle("hidden", !submission);
    }
}

async function exportCurrentSubmission() {
    if (!lastViewedSubmission || !currentProblem) return;
    try {
        const data = await apiCall("export_code", currentProblem.pid, String(lastViewedSubmission.rid));
        showToast(t("diffExported", data.path || data.filename), "success", 5000);
    } catch (err) {
        showToast(t("diffExportFailed", err.message), "error");
    }
}

// Simple LCS-based line diff. Returns [{type: "add"|"del"|"ctx", text}].
function diffLines(a, b) {
    const linesA = String(a || "").split("\n");
    const linesB = String(b || "").split("\n");
    const n = linesA.length, m = linesB.length;
    const dp = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
    for (let i = n - 1; i >= 0; i--) {
        for (let j = m - 1; j >= 0; j--) {
            dp[i][j] = linesA[i] === linesB[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
        }
    }
    const out = [];
    let i = 0, j = 0;
    while (i < n && j < m) {
        if (linesA[i] === linesB[j]) {
            out.push({ type: "ctx", text: linesA[i] });
            i++; j++;
        } else if (dp[i + 1][j] >= dp[i][j + 1]) {
            out.push({ type: "del", text: linesA[i] });
            i++;
        } else {
            out.push({ type: "add", text: linesB[j] });
            j++;
        }
    }
    while (i < n) { out.push({ type: "del", text: linesA[i] }); i++; }
    while (j < m) { out.push({ type: "add", text: linesB[j] }); j++; }
    return out;
}

async function showVersionDiff(pid, oldRec, newRec) {
    if (!diffModal) return;
    if (diffSubtitleEl) {
        diffSubtitleEl.textContent = t("diffSubtitle", `#${oldRec.rid}`, `#${newRec.rid}`);
    }
    const lines = diffLines(oldRec.code, newRec.code);
    const html = lines.map((l) => {
        const marker = l.type === "del" ? "−" : (l.type === "add" ? "+" : " ");
        return `<span class="diff-line ${l.type}"><span class="diff-marker">${marker}</span>${escapeHtml(l.text)}</span>`;
    }).join("");
    if (diffContent) diffContent.innerHTML = html;
    diffModal.classList.remove("hidden");
}

function closeDiffModal() {
    if (diffModal) diffModal.classList.add("hidden");
}

// Version compare inside local records list: keep two selected checkboxes.
let compareSelection = []; // selected rids

function bindCompareControls(container, records) {
    const compareBar = container.querySelector(".local-records-compare-bar");
    const compareBtnEl = container.querySelector(".local-records-compare-btn");
    if (compareBtnEl) {
        compareBtnEl.addEventListener("click", () => {
            const pid = currentProblem ? currentProblem.pid : "";
            if (compareSelection.length !== 2) {
                showToast(t("diffNeedRecords"), "info");
                return;
            }
            const recs = compareSelection.map((rid) => records.find((r) => String(r.rid) === String(rid)));
            if (!recs[0] || !recs[1]) {
                showToast(t("diffNeedRecords"), "info");
                return;
            }
            recs.sort((x, y) => (x.timestamp || 0) - (y.timestamp || 0));
            showVersionDiff(pid, recs[0], recs[1]);
        });
    }
    container.querySelectorAll(".compare-check").forEach((cb) => {
        cb.addEventListener("click", (e) => {
            e.stopPropagation();
            const rid = cb.dataset.rid;
            const itemEl = cb.closest(".local-records-item");
            if (cb.checked) {
                if (compareSelection.length >= 2) {
                    cb.checked = false;
                    showToast(t("diffNeedRecords"), "info");
                    return;
                }
                compareSelection.push(rid);
                if (itemEl) itemEl.classList.add("compare-selected");
            } else {
                compareSelection = compareSelection.filter((r) => r !== rid);
                if (itemEl) itemEl.classList.remove("compare-selected");
            }
            if (compareBar) {
                compareBar.style.display = compareSelection.length ? "" : "none";
            }
        });
    });
}

function initNewFeatures() {
    if (standingsBtn) standingsBtn.addEventListener("click", openStandingsModal);
    if (standingsCloseBtn) standingsCloseBtn.addEventListener("click", closeStandingsModal);
    if (standingsModal) standingsModal.addEventListener("click", (e) => { if (e.target === standingsModal) closeStandingsModal(); });
    if (standingsGoBtn) standingsGoBtn.addEventListener("click", loadStandings);
    if (standingsInput) standingsInput.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); loadStandings(); } });

    if (wrongBookBtn) wrongBookBtn.addEventListener("click", openWrongBook);
    if (wrongBookCloseBtn) wrongBookCloseBtn.addEventListener("click", closeWrongBook);
    if (wrongBookModal) wrongBookModal.addEventListener("click", (e) => { if (e.target === wrongBookModal) closeWrongBook(); });

    if (recommendBtn) recommendBtn.addEventListener("click", openRecommend);
    if (recommendCloseBtn) recommendCloseBtn.addEventListener("click", closeRecommend);
    if (recommendModal) recommendModal.addEventListener("click", (e) => { if (e.target === recommendModal) closeRecommend(); });
    if (recommendRefreshBtn) recommendRefreshBtn.addEventListener("click", refreshRecommend);
    if (recommendGoBtn) recommendGoBtn.addEventListener("click", () => {
        if (recommendProblem && recommendProblem.pid) {
            closeRecommend();
            loadProblemOnly(recommendProblem.pid);
        }
    });

    if (diffCloseBtn) diffCloseBtn.addEventListener("click", closeDiffModal);
    if (diffModal) diffModal.addEventListener("click", (e) => { if (e.target === diffModal) closeDiffModal(); });
    if (submissionExportBtn) submissionExportBtn.addEventListener("click", exportCurrentSubmission);
}

// =========================================================================
// Helpers
// =========================================================================
function switchTab(tabName) {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));
    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add("active");
    document.getElementById(`tab-${tabName}`).classList.add("active");
}

// View switching that is IDE-aware: in IDE mode the top tabs are hidden, so
// "switching to problem/solutions/analysis" means switching the left mini-tab
// instead. `target` uses the same names as the top tabs (problem/solutions/
// analysis); "search" is IDE-only.
function switchView(target) {
    if (ideMode) {
        switchIdeTab(target);
    } else {
        switchTab(target);
    }
}

// =========================================================================
// Online IDE mode
// =========================================================================
// In IDE mode the existing content elements (search row, problem/solutions/
// analysis content, code editor, submit header & footer) are re-parented into
// the #ideSplit slots. Their render functions still write by element id, so
// moving the DOM nodes does not break updates. On exit, every moved node is
// restored to its original parent recorded in ideOriginalParents.

function switchIdeTab(name) {
    ideMiniTabs.querySelectorAll(".ide-mini-tab").forEach((b) => {
        b.classList.toggle("active", b.dataset.ideTab === name);
    });
    const slotMap = {
        search: ideSearchSlot,
        problem: ideProblemSlot,
        solutions: ideSolutionsSlot,
        analysis: ideAnalysisSlot,
    };
    Object.values(slotMap).forEach((slot) => slot.classList.remove("active"));
    const slot = slotMap[name];
    if (slot) slot.classList.add("active");
}

// Move an element into a slot, remembering its original parent + next sibling
// so it can be restored exactly where it came from.
function ideReparent(el, slot) {
    if (!el || !slot || el.parentElement === slot) return;
    ideOriginalParents.set(el, {
        parent: el.parentElement,
        nextSibling: el.nextElementSibling,
    });
    slot.appendChild(el);
}

function ideRestore(el) {
    if (!el) return;
    const rec = ideOriginalParents.get(el);
    if (!rec) return;
    if (rec.nextSibling && rec.nextSibling.parentElement === rec.parent) {
        rec.parent.insertBefore(el, rec.nextSibling);
    } else {
        rec.parent.appendChild(el);
    }
    ideOriginalParents.delete(el);
}

function enterIdeMode() {
    if (ideMode) return;
    // IDE layout lives inside the submit tab; make sure it is the active pane.
    switchTab("submit");
    // Populate the language dropdown (normally done on tab click, which we
    // skip here). The test feature requires a concrete language selection.
    loadLanguages();

    // Re-parent content into the IDE slots.
    ideReparent(document.querySelector(".search-row"), ideSearchSlot);
    ideReparent(searchResults, ideSearchSlot);
    ideReparent(problemContent, ideProblemSlot);
    ideReparent(solutionsContent, ideSolutionsSlot);
    ideReparent(analysisContent, ideAnalysisSlot);
    ideReparent(document.querySelector(".submit-header"), ideEditorHeaderSlot);
    ideReparent(document.querySelector(".code-editor-wrap"), ideEditorSlot);
    ideReparent(document.querySelector(".submit-footer"), ideSubmitFooterSlot);

    // Reset pane widths to defaults (clear any inline styles from prior drag)
    ideSplit.querySelector(".ide-left").style.flex = "";
    ideSplit.querySelector(".ide-right").style.flex = "";

    ideMode = true;
    document.querySelector(".app").classList.add("ide-mode");
    ideSplit.classList.remove("hidden");
    updateIdeModeBtnText();

    // Default to the problem pane (or search if no problem loaded yet)
    switchIdeTab(currentProblem ? "problem" : "search");

    // The editor changed size; re-sync the highlight overlay after layout settles.
    requestAnimationFrame(() => {
        syncCodeScroll();
        syncCodeHighlight();
    });
}

function exitIdeMode() {
    if (!ideMode) return;
    // Restore every re-parented element to its original location.
    ideRestore(document.querySelector(".submit-footer"));
    ideRestore(document.querySelector(".code-editor-wrap"));
    ideRestore(document.querySelector(".submit-header"));
    ideRestore(analysisContent);
    ideRestore(solutionsContent);
    ideRestore(problemContent);
    ideRestore(searchResults);
    ideRestore(document.querySelector(".search-row"));

    ideMode = false;
    document.querySelector(".app").classList.remove("ide-mode");
    ideSplit.classList.add("hidden");
    updateIdeModeBtnText();
    ideOutput.textContent = "";
    ideOutput.className = "ide-output";
    ideRunMeta.textContent = "";

    switchTab("submit");
    requestAnimationFrame(() => {
        syncCodeScroll();
        syncCodeHighlight();
    });
}

function updateIdeModeBtnText() {
    if (!ideModeBtn) return;
    ideModeBtn.textContent = ideMode ? t("ideModeExit") : t("ideModeBtn");
}

// Compile & run the current editor code locally with the user-provided stdin.
async function runLocalTest() {
    const code = codeEditor.value;
    const langId = parseInt(langSelect.value, 10);
    const stdin = ideStdin.value;
    const enableO2 = enableO2Checkbox.checked;

    if (!code.trim()) {
        ideOutput.textContent = t("ideNoCode");
        ideOutput.className = "ide-output ide-output-warn";
        ideRunMeta.textContent = "";
        return;
    }
    if (!langId || !IDE_SUPPORTED_LANGS.has(langId)) {
        ideOutput.textContent = t("ideUnsupportedLang");
        ideOutput.className = "ide-output ide-output-warn";
        ideRunMeta.textContent = "";
        return;
    }

    ideRunBtn.disabled = true;
    const originalBtnText = ideRunBtn.textContent;
    ideRunBtn.textContent = t("ideRunRunning");
    ideOutput.textContent = t("ideRunRunning");
    ideOutput.className = "ide-output ide-output-running";
    ideRunMeta.textContent = "";

    try {
        const api = await pyApi();
        const data = await api.compile_and_run(code, langId, stdin, enableO2);
        renderIdeOutput(data);
    } catch (err) {
        ideOutput.textContent = t("networkError") + (err.message || "");
        ideOutput.className = "ide-output ide-output-error";
        ideRunMeta.textContent = "";
    } finally {
        ideRunBtn.disabled = false;
        ideRunBtn.textContent = originalBtnText;
    }
}

function renderIdeOutput(data) {
    if (!data) {
        ideOutput.textContent = t("networkError");
        ideOutput.className = "ide-output ide-output-error";
        return;
    }
    if (data.success === false) {
        // Backend refused (unsupported language / missing compiler / etc.)
        ideOutput.textContent = data.error || t("ideUnsupportedLang");
        ideOutput.className = "ide-output ide-output-error";
        ideRunMeta.textContent = "";
        return;
    }
    if (data.compile_failed) {
        ideOutput.textContent = (data.compile_output || "").trim() || t("ideCompileError");
        ideOutput.className = "ide-output ide-output-error";
        ideRunMeta.textContent = t("ideCompileError");
        return;
    }
    if (data.timeout) {
        const out = (data.stdout || "") + (data.stderr ? "\n" + data.stderr : "");
        ideOutput.textContent = (out.trim() ? out + "\n" : "") + t("ideRunTimeout");
        ideOutput.className = "ide-output ide-output-warn";
        ideRunMeta.textContent = t("ideRunTimeout");
        return;
    }
    // Normal run result
    const parts = [];
    if (data.stdout) parts.push(t("ideStdout") + "\n" + data.stdout);
    if (data.stderr) parts.push(t("ideStderr") + "\n" + data.stderr);
    if (data.compile_output) parts.push(t("ideCompileError") + "\n" + data.compile_output);
    ideOutput.textContent = parts.join("\n\n") || t("ideNoOutput");
    ideOutput.className = "ide-output";
    ideRunMeta.textContent = t("ideExitCode", data.exit_code, data.time_ms);
}

// --- IDE test panel sub-tabs (single / cases / duipai) ---
function initIdeTestTabs() {
    const panel = document.querySelector(".ide-test-panel");
    if (!panel) return;
    panel.querySelectorAll(".ide-test-tab").forEach((tab) => {
        tab.addEventListener("click", () => {
            panel.querySelectorAll(".ide-test-tab").forEach((x) => x.classList.remove("active"));
            panel.querySelectorAll(".ide-test-pane").forEach((x) => x.classList.remove("active"));
            tab.classList.add("active");
            const pane = panel.querySelector(`.ide-test-pane[data-ide-test-pane="${tab.dataset.ideTest}"]`);
            if (pane) pane.classList.add("active");
        });
    });
}

// --- Multi test cases ---
let ideCaseCount = 0;
function addIdeCase(input, expected) {
    ideCaseCount += 1;
    const row = document.createElement("div");
    row.className = "ide-case-row";
    row.dataset.idx = String(ideCaseCount);
    row.innerHTML = `
        <div class="ide-case-row-head">
            <span class="ide-case-index">${t("ideCaseNum", ideCaseCount)}</span>
            <button type="button" class="btn-link ide-case-del" data-i18n="ideCaseDel">${t("ideCaseDel")}</button>
        </div>
        <div class="ide-case-cols">
            <textarea class="ide-case-input" placeholder="${escapeHtml(t("ideCaseInputPlaceholder"))}" spellcheck="false" wrap="off">${escapeHtml(input || "")}</textarea>
            <textarea class="ide-case-expected" placeholder="${escapeHtml(t("ideCaseExpectedPlaceholder"))}" spellcheck="false" wrap="off">${escapeHtml(expected || "")}</textarea>
        </div>`;
    ideCaseList.appendChild(row);
    const delBtn = row.querySelector(".ide-case-del");
    delBtn.addEventListener("click", () => {
        row.remove();
    });
}

function collectIdeCases() {
    const cases = [];
    ideCaseList.querySelectorAll(".ide-case-row").forEach((row) => {
        const input = row.querySelector(".ide-case-input").value;
        const expected = row.querySelector(".ide-case-expected").value;
        if (input.trim() || expected.trim()) {
            cases.push({ input, expected });
        }
    });
    return cases;
}

async function runAllIdeCases() {
    const code = codeEditor.value;
    const langId = parseInt(langSelect.value, 10);
    const enableO2 = enableO2Checkbox.checked;
    const cases = collectIdeCases();
    if (!code.trim()) {
        ideCaseResult.innerHTML = `<div class="ide-case-result-item warn">${escapeHtml(t("ideNoCode"))}</div>`;
        return;
    }
    if (!langId || !IDE_SUPPORTED_LANGS.has(langId)) {
        ideCaseResult.innerHTML = `<div class="ide-case-result-item warn">${escapeHtml(t("ideUnsupportedLang"))}</div>`;
        return;
    }
    if (!cases.length) {
        ideCaseResult.innerHTML = `<div class="ide-case-result-item warn">${escapeHtml(t("ideCasesEmpty"))}</div>`;
        return;
    }
    ideCaseRunBtn.disabled = true;
    const originalText = ideCaseRunBtn.textContent;
    ideCaseRunBtn.textContent = t("ideCaseRunning");
    ideCaseResult.innerHTML = `<div class="ide-case-result-item running">${escapeHtml(t("ideCaseRunning"))}</div>`;
    try {
        const api = await pyApi();
        const data = await api.run_local_cases(code, langId, cases, enableO2);
        renderIdeCaseResult(data);
    } catch (err) {
        ideCaseResult.innerHTML = `<div class="ide-case-result-item error">${escapeHtml(t("networkError") + (err.message || ""))}</div>`;
    } finally {
        ideCaseRunBtn.disabled = false;
        ideCaseRunBtn.textContent = originalText;
    }
}

function renderIdeCaseResult(data) {
    if (!data || data.success === false) {
        ideCaseResult.innerHTML = `<div class="ide-case-result-item error">${escapeHtml((data && data.error) || t("networkError"))}</div>`;
        return;
    }
    const results = data.results || [];
    const passedCount = results.filter((r) => r.passed).length;
    let html = `<div class="ide-case-summary ${passedCount === results.length && results.length ? "pass" : "fail"}">${t("ideCaseSummary", passedCount, results.length)}</div>`;
    results.forEach((r) => {
        if (r.error) {
            html += `<div class="ide-case-result-item error">${t("ideCaseNum", r.index + 1)} ${escapeHtml(r.error)}</div>`;
        } else if (r.compile_failed) {
            html += `<div class="ide-case-result-item error">${t("ideCaseNum", r.index + 1)} ${escapeHtml(t("ideCompileError"))}\n<pre>${escapeHtml((r.compile_output || "").slice(0, 800))}</pre></div>`;
        } else if (r.timeout) {
            html += `<div class="ide-case-result-item warn">${t("ideCaseNum", r.index + 1)} ${escapeHtml(t("ideRunTimeout"))}</div>`;
        } else if (r.passed) {
            html += `<div class="ide-case-result-item pass">${t("ideCaseNum", r.index + 1)} ✓ ${t("ideCasePassed")} · ${r.time_ms} ms</div>`;
        } else {
            html += `
                <div class="ide-case-result-item fail">
                    <div>${t("ideCaseNum", r.index + 1)} ✗ ${t("ideCaseFailed")} · ${r.time_ms} ms</div>
                    <div class="ide-case-diff">
                        <div><b>${escapeHtml(t("ideCaseExpected"))}</b><pre>${escapeHtml(r.expected)}</pre></div>
                        <div><b>${escapeHtml(t("ideCaseActual"))}</b><pre>${escapeHtml(r.actual)}</pre></div>
                    </div>
                </div>`;
        }
    });
    ideCaseResult.innerHTML = html;
}

// --- 对拍 (duipai) ---
async function runDuipai() {
    const code = codeEditor.value;
    const langId = parseInt(langSelect.value, 10);
    const enableO2 = enableO2Checkbox.checked;
    const genCode = ideGenCode.value;
    const bruteCode = ideBruteCode.value;
    const iterations = parseInt(ideDuipaiIter.value, 10) || 20;
    if (!code.trim()) {
        ideDuipaiOutput.textContent = t("ideNoCode");
        ideDuipaiOutput.className = "ide-output ide-output-warn";
        return;
    }
    if (!langId || !IDE_SUPPORTED_LANGS.has(langId)) {
        ideDuipaiOutput.textContent = t("ideUnsupportedLang");
        ideDuipaiOutput.className = "ide-output ide-output-warn";
        return;
    }
    if (!genCode.trim() || !bruteCode.trim()) {
        ideDuipaiOutput.textContent = t("ideDuipaiNeedCode");
        ideDuipaiOutput.className = "ide-output ide-output-warn";
        return;
    }
    ideDuipaiRunBtn.disabled = true;
    const originalText = ideDuipaiRunBtn.textContent;
    ideDuipaiRunBtn.textContent = t("ideDuipaiRunning");
    ideDuipaiOutput.textContent = t("ideDuipaiRunning");
    ideDuipaiOutput.className = "ide-output ide-output-running";
    try {
        const api = await pyApi();
        const data = await api.run_duipai(code, langId, bruteCode, langId, genCode, langId, iterations, enableO2);
        renderDuipaiOutput(data);
    } catch (err) {
        ideDuipaiOutput.textContent = t("networkError") + (err.message || "");
        ideDuipaiOutput.className = "ide-output ide-output-error";
    } finally {
        ideDuipaiRunBtn.disabled = false;
        ideDuipaiRunBtn.textContent = originalText;
    }
}

function renderDuipaiOutput(data) {
    if (!data || data.success === false) {
        ideDuipaiOutput.textContent = (data && data.error) || t("networkError");
        ideDuipaiOutput.className = "ide-output ide-output-error";
        return;
    }
    const lines = [];
    if (data.matched) {
        lines.push(t("ideDuipaiOk", data.iterations));
        ideDuipaiOutput.className = "ide-output ide-output-ok";
    } else if (data.mismatch) {
        const m = data.mismatch;
        lines.push(t("ideDuipaiMismatch", m.iteration));
        lines.push(`--- ${t("ideDuipaiInput")} ---\n${m.input}`);
        lines.push(`--- ${t("ideDuipaiUserOut")} ---\n${m.userOutput}`);
        lines.push(`--- ${t("ideDuipaiBruteOut")} ---\n${m.bruteOutput}`);
        ideDuipaiOutput.className = "ide-output ide-output-error";
    } else {
        lines.push(t("ideDuipaiNoCompare", data.iterations));
        ideDuipaiOutput.className = "ide-output ide-output-warn";
    }
    (data.errors || []).forEach((e) => lines.push("[!] " + e));
    ideDuipaiOutput.textContent = lines.join("\n\n");
}

if (ideCaseAddBtn) ideCaseAddBtn.addEventListener("click", () => addIdeCase());
if (ideCaseRunBtn) ideCaseRunBtn.addEventListener("click", runAllIdeCases);
if (ideDuipaiRunBtn) ideDuipaiRunBtn.addEventListener("click", runDuipai);
initIdeTestTabs();

// --- Draggable divider: resize left/right panes ---
// The divider sits between .ide-left and .ide-right inside #ideSplit.
// Dragging adjusts the flex-basis of both panes as a percentage of the split width.
function initIdeDivider() {
    let dragging = false;

    ideDivider.addEventListener("mousedown", (e) => {
        e.preventDefault();
        dragging = true;
        ideDivider.classList.add("dragging");
        document.body.classList.add("ide-resizing");
    });

    document.addEventListener("mousemove", (e) => {
        if (!dragging) return;
        const rect = ideSplit.getBoundingClientRect();
        // Percentage of the cursor position within the split container
        let pct = ((e.clientX - rect.left) / rect.width) * 100;
        // Clamp to reasonable bounds so neither pane collapses
        pct = Math.max(20, Math.min(80, pct));
        const left = ideSplit.querySelector(".ide-left");
        const right = ideSplit.querySelector(".ide-right");
        left.style.flex = `0 0 ${pct}%`;
        right.style.flex = `1 1 ${100 - pct}%`;
    });

    document.addEventListener("mouseup", () => {
        if (!dragging) return;
        dragging = false;
        ideDivider.classList.remove("dragging");
        document.body.classList.remove("ide-resizing");
        // Editor changed size — re-sync highlight overlay
        syncCodeScroll();
        syncCodeHighlight();
    });
}

// --- Draggable divider: resize AI report / AI assistant panes ---
// The divider sits between #analysisContent and #assistantPanel inside
// .analysis-split. Dragging adjusts the assistant panel width; the report
// pane flex-fills the remainder.
function initAnalysisDivider() {
    const divider = document.getElementById("analysisDivider");
    const split = divider ? divider.parentElement : null;
    const panel = document.getElementById("assistantPanel");
    if (!divider || !split || !panel) return;

    const COLLAPSE = 40;   // width (px) below which the assistant fully closes
    let lastWidth = 380;   // remembered width so the panel can be re-opened
    let dragging = false;
    let startX = 0;
    let startW = 0;

    divider.addEventListener("mousedown", (e) => {
        e.preventDefault();
        dragging = true;
        startX = e.clientX;
        // When collapsed the panel is display:none (offsetWidth 0), so fall
        // back to the remembered width to reopen it smoothly.
        startW = panel.offsetWidth || lastWidth;
        divider.classList.add("dragging");
        document.body.classList.add("ide-resizing");
    });

    document.addEventListener("mousemove", (e) => {
        if (!dragging) return;
        const rect = split.getBoundingClientRect();
        // The assistant panel is anchored to the right, so dragging right
        // narrows it (the divider follows the cursor); dragging left widens it.
        let w = startW - (e.clientX - startX);
        const maxW = rect.width * 0.65;         // never crowd out the report
        w = Math.max(0, Math.min(maxW, w));
        if (w <= COLLAPSE) {
            // Dragged all the way shut: hide the assistant completely.
            panel.style.display = "none";
            panel.style.width = "0px";
        } else {
            panel.style.display = "flex";
            panel.style.width = w + "px";
            lastWidth = w;
        }
    });

    document.addEventListener("mouseup", () => {
        if (!dragging) return;
        dragging = false;
        divider.classList.remove("dragging");
        document.body.classList.remove("ide-resizing");
    });
}
initAnalysisDivider();

function escapeHtml(text) {
    if (text === null || text === undefined) return "";
    const div = document.createElement("div");
    div.textContent = String(text);
    return div.innerHTML;
}

// Copy text to clipboard and show feedback on the button. Resolves to a
// boolean indicating whether the copy succeeded.
async function copyToClipboard(text, btn) {
    if (!text) return false;
    try {
        await navigator.clipboard.writeText(text);
    } catch (e) {
        // Fallback for non-secure contexts
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        let copied = false;
        try {
            copied = document.execCommand("copy");
        } catch (e2) {
            // give up
        }
        document.body.removeChild(ta);
        if (!copied) return false;
    }
    if (btn) {
        const label = btn.querySelector(".copy-text");
        const orig = label ? label.textContent : "";
        if (label) label.textContent = t("copiedText");
        btn.classList.add("copied");
        setTimeout(() => {
            if (label) label.textContent = orig || t("copyText");
            btn.classList.remove("copied");
        }, 1500);
    }
    return true;
}

// Bind copy buttons inside a container (sample blocks, etc.)
function bindCopyButtons(container) {
    container.querySelectorAll(".sample-copy-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const targetId = btn.dataset.copyTarget;
            const el = document.getElementById(targetId);
            if (el) copyToClipboard(el.textContent, btn);
        });
    });
}

// =========================================================================
// Code editor: syntax highlight overlay + auto-indent
// =========================================================================
const CODE_INDENT = "    "; // 4 spaces

// Map selected language to hljs language name
function getHljsLangName(langId) {
    const map = {
        0: null,       // auto
        1: "delphi",   // Pascal
        2: "c",
        3: "cpp",      // C++98
        4: "cpp",      // C++11
        7: "python",   // Python 3
        8: "java",     // Java 8
        9: "javascript", // Node.js
        11: "cpp",     // C++14
        12: "cpp",     // C++17
        13: "ruby",
        14: "go",
        15: "rust",
        16: "php",
        17: "csharp",
        19: "haskell",
        21: "kotlin",
        25: "python",  // PyPy 3
        27: "cpp",     // C++20
        28: "cpp",     // C++14 (GCC 9)
        33: "java",    // Java 21
    };
    return map[langId] || null;
}

function syncCodeHighlight() {
    const code = codeEditor.value;
    const langName = getHljsLangName(parseInt(langSelect.value, 10) || 0);
    // Reset className and apply hljs + optional language
    codeHighlight.className = langName ? `hljs language-${langName}` : "hljs";
    // Remove data-highlighted so hljs can re-highlight (highlightElement sets it)
    codeHighlight.removeAttribute("data-highlighted");
    try {
        if (langName && hljs.getLanguage(langName)) {
            // Use specific language highlighting
            codeHighlight.innerHTML = hljs.highlight(code + "\n", { language: langName }).value;
        } else {
            // Auto-detect language via highlightAuto (not highlightElement,
            // which marks the element with data-highlighted and refuses to
            // re-run on subsequent keystrokes, causing all-black output).
            const result = hljs.highlightAuto(code + "\n");
            codeHighlight.innerHTML = result.value;
            if (result.language) {
                codeHighlight.className = `hljs language-${result.language}`;
            }
        }
    } catch (e) {
        // Fallback: plain text (still visible via .hljs base color)
        codeHighlight.textContent = code + "\n";
    }
    syncCodeScroll();
}

function syncCodeScroll() {
    const highlight = document.getElementById("codeHighlight");
    const codeEl = highlight.querySelector("code");
    // Sync vertical scroll position from textarea to pre
    highlight.scrollTop = codeEditor.scrollTop;
    // Sync horizontal scroll: pre has overflow:hidden so scrollLeft won't
    // work. Translate the inner <code> element (not the pre, to avoid
    // shifting the background) to match the textarea's horizontal scroll.
    const sx = codeEditor.scrollLeft;
    if (codeEl) {
        if (sx > 0) {
            codeEl.style.transform = `translateX(${-sx}px)`;
        } else {
            codeEl.style.transform = "";
        }
    }
    // Compensate for textarea scrollbar width: when the textarea shows a
    // vertical scrollbar, its content area is narrower than the pre's.
    // Add matching right padding to the pre so text aligns perfectly.
    const hasVScroll = codeEditor.scrollHeight > codeEditor.clientHeight;
    if (hasVScroll) {
        const sbWidth = codeEditor.offsetWidth - codeEditor.clientWidth;
        if (sbWidth > 0) {
            highlight.style.paddingRight = `calc(18px + ${sbWidth}px)`;
        } else {
            highlight.style.paddingRight = "";
        }
    } else {
        highlight.style.paddingRight = "";
    }
}

// Bracket pairs supported by auto-completion: (), [], {}
const BRACKET_PAIRS = [
    ["(", ")"],
    ["[", "]"],
    ["{", "}"],
];

// Bracket auto-completion (only active when the "括号补全" checkbox is on):
// - typing an opening bracket inserts the matching closing bracket and places
//   the cursor in between; with a selection it wraps the selected text.
// - typing a closing bracket that already follows the cursor skips over it
//   instead of inserting a duplicate.
function handleBracketAutoComplete(e) {
    const ch = e.key;
    const start = codeEditor.selectionStart;
    const end = codeEditor.selectionEnd;
    const value = codeEditor.value;

    const openPair = BRACKET_PAIRS.find((p) => p[0] === ch);
    if (openPair) {
        e.preventDefault();
        const close = openPair[1];
        const next = value.substring(end, end + 1);
        if (start === end && next === close) {
            // Closing bracket already present right after the cursor: just move past it
            codeEditor.selectionStart = codeEditor.selectionEnd = end + 1;
        } else {
            const insert = ch + close;
            codeEditor.value = value.substring(0, start) + insert + value.substring(end);
            codeEditor.selectionStart = codeEditor.selectionEnd = start + 1;
        }
        syncCodeHighlight();
        updateSubmitButtonState();
        return true;
    }

    const closePair = BRACKET_PAIRS.find((p) => p[1] === ch);
    if (closePair && start === end && value.substring(end, end + 1) === ch) {
        e.preventDefault();
        codeEditor.selectionStart = codeEditor.selectionEnd = end + 1;
        syncCodeHighlight();
        updateSubmitButtonState();
        return true;
    }
    return false;
}

// Auto-indent: Tab inserts spaces, Enter auto-indents based on context
function handleCodeKeydown(e) {
    // Bracket auto-completion for printable characters (skips Tab/Enter/etc.)
    if (enableBracketCheckbox.checked && !e.isComposing && !e.ctrlKey && !e.metaKey && !e.altKey && e.key.length === 1) {
        if (handleBracketAutoComplete(e)) return;
    }
    if (e.key === "Tab") {
        e.preventDefault();
        const start = codeEditor.selectionStart;
        const end = codeEditor.selectionEnd;
        if (e.shiftKey) {
            // Shift+Tab: dedent (remove up to 4 leading spaces on current line)
            const before = codeEditor.value.substring(0, start);
            const lineStart = before.lastIndexOf("\n") + 1;
            const linePrefix = codeEditor.value.substring(lineStart, start);
            const stripCount = Math.min(CODE_INDENT.length, linePrefix.match(/^ */) ? linePrefix.match(/^ */)[0].length : 0);
            if (stripCount > 0) {
                codeEditor.value = codeEditor.value.substring(0, lineStart) + linePrefix.substring(stripCount) + codeEditor.value.substring(start);
                codeEditor.selectionStart = codeEditor.selectionEnd = start - stripCount;
            }
        } else {
            // Tab: insert 4 spaces
            codeEditor.value = codeEditor.value.substring(0, start) + CODE_INDENT + codeEditor.value.substring(end);
            codeEditor.selectionStart = codeEditor.selectionEnd = start + CODE_INDENT.length;
        }
        syncCodeHighlight();
        updateSubmitButtonState();
    } else if (e.key === "Enter") {
        // Auto-indent: match previous line's indentation, add extra indent if line ends with {
        const start = codeEditor.selectionStart;
        const before = codeEditor.value.substring(0, start);
        const lineStart = before.lastIndexOf("\n") + 1;
        const currentLine = codeEditor.value.substring(lineStart, start);
        const indentMatch = currentLine.match(/^(\s*)/);
        let indent = indentMatch ? indentMatch[1] : "";
        // 行尾（去除尾部空白后）以 { 结尾
        const trimmedEnd = currentLine.replace(/\s+$/, "");
        // 光标后紧跟自动补全的 } 时，把 } 换到下一行并与 { 对齐，光标留在中间缩进行
        const rest = codeEditor.value.substring(codeEditor.selectionEnd);
        if (trimmedEnd.endsWith("{") && rest.startsWith("}")) {
            e.preventDefault();
            const insert = "\n" + indent + CODE_INDENT + "\n" + indent;
            codeEditor.value = codeEditor.value.substring(0, start) + insert + rest;
            // 光标停在中间缩进行末尾（第一段 "\n" + 缩进 + 一级缩进 之后）
            codeEditor.selectionStart = codeEditor.selectionEnd = start + 1 + indent.length + CODE_INDENT.length;
            syncCodeHighlight();
            updateSubmitButtonState();
        } else {
            // 普通自动缩进：匹配上一行缩进，行尾以 { 结尾时额外增加一级缩进
            if (trimmedEnd.endsWith("{")) {
                indent += CODE_INDENT;
            }
            if (indent.length > 0) {
                e.preventDefault();
                const insert = "\n" + indent;
                codeEditor.value = codeEditor.value.substring(0, start) + insert + codeEditor.value.substring(codeEditor.selectionEnd);
                codeEditor.selectionStart = codeEditor.selectionEnd = start + insert.length;
                syncCodeHighlight();
                updateSubmitButtonState();
            }
            // If no indent needed, let the default Enter behavior happen,
            // but still sync highlight after
            setTimeout(syncCodeHighlight, 0);
        }
    } else if (e.key === "}") {
        // Auto-dedent: if current line is only whitespace and we type }, dedent
        const start = codeEditor.selectionStart;
        const before = codeEditor.value.substring(0, start);
        const lineStart = before.lastIndexOf("\n") + 1;
        const linePrefix = codeEditor.value.substring(lineStart, start);
        // If the line consists only of spaces and has at least one indent worth
        if (/^ +$/.test(linePrefix) && linePrefix.length >= CODE_INDENT.length) {
            // Remove one indent level, then insert }
            e.preventDefault();
            const dedented = linePrefix.substring(0, linePrefix.length - CODE_INDENT.length);
            codeEditor.value = codeEditor.value.substring(0, lineStart) + dedented + "}" + codeEditor.value.substring(codeEditor.selectionEnd);
            codeEditor.selectionStart = codeEditor.selectionEnd = lineStart + dedented.length + 1;
            syncCodeHighlight();
            updateSubmitButtonState();
        }
    }
}

// =========================================================================
// localStorage save/load
// =========================================================================
const STORAGE_KEYS = {
    mode: "luogu_analyzer_mode",
    theme: "luogu_analyzer_theme",
    lang: "luogu_analyzer_lang",
    bracket: "luogu_analyzer_bracket",
    notify: "luogu_analyzer_notify",
    disclaimer: "luogu_analyzer_disclaimer_accepted",
    };

// =========================================================================
// Global keyboard shortcuts
// =========================================================================
document.addEventListener("keydown", (e) => {
    if (!e.ctrlKey) return;
    const active = document.activeElement;
    if (e.key === "k" || e.key === "K") {
        // Ctrl+K: focus the search box
        e.preventDefault();
        searchInput.focus();
        searchInput.select();
        return;
    }
    if (e.key === "s" || e.key === "S") {
        // Ctrl+S: save the current draft (blocks the browser save dialog)
        e.preventDefault();
        const pid = draftTargetPid();
        if (pid && codeEditor.value.trim()) {
            persistDraft(pid, codeEditor.value);
        } else {
            setDraftStatus(t("draftEmpty"));
        }
        return;
    }
    if (e.key === "Enter") {
        if (active === codeEditor) {
            // Ctrl+Enter: run in IDE mode, otherwise submit to Luogu
            e.preventDefault();
            if (ideMode) {
                runLocalTest();
            } else {
                submitCode();
            }
        } else if (active === problemIdInput || active === searchInput) {
            e.preventDefault();
            if (active === searchInput) searchProblems();
            else analyze();
        }
        return;
    }
    if (e.shiftKey && (e.key === "t" || e.key === "T")) {
        // Ctrl+Shift+T: insert a code template for the current language
        e.preventDefault();
        closeTplMenu();
        const cur = parseInt(langSelect.value, 10);
        const langId = CODE_TEMPLATES[cur] ? cur : 14;
        insertTemplate(langId);
        return;
    }
});

async function loadSavedConfig() {
    // Load UI prefs from localStorage (theme, mode, lang are client-only)
    const savedMode = localStorage.getItem(STORAGE_KEYS.mode);
    const savedTheme = localStorage.getItem(STORAGE_KEYS.theme);

    if (savedMode === "ai" || savedMode === "filter") {
        setMode(savedMode);
    } else {
        setMode("ai");
    }
    const initialTheme = savedTheme || document.documentElement.getAttribute("data-theme") || "dark";
    setTheme(initialTheme);

    // Restore bracket auto-completion preference (default: on)
    const savedBracket = localStorage.getItem(STORAGE_KEYS.bracket);
    if (savedBracket !== null) {
        enableBracketCheckbox.checked = savedBracket === "1";
    }

    // Restore system notification preference (default: on)
    const savedNotify = localStorage.getItem(STORAGE_KEYS.notify);
    if (savedNotify !== null) {
        enableNotifyCheckbox.checked = savedNotify === "1";
    }

    // Load API key / cookie / model from server config.json
    try {
        const data = await apiGet("/api/config");
        if (data.api_key) {
            apiKeyInput.value = data.api_key;
            apiKeyStatus.className = "save-status saved";
            apiKeyStatus.textContent = t("savedStatus");
        }
        if (data.glm_api_key) {
            glmApiKeyInput.value = data.glm_api_key;
            glmApiKeyStatus.className = "save-status saved";
            glmApiKeyStatus.textContent = t("savedStatus");
        }
        if (data.cookie) {
            luoguCookieInput.value = data.cookie;
            cookieStatus.className = "save-status saved";
            cookieStatus.textContent = t("savedStatus");
        }
        if (data.vjudge_username) {
            vjudgeUsernameInput.value = data.vjudge_username;
        }
        if (data.vjudge_has_password) {
            vjudgePasswordInput.value = "********";
            vjudgePasswordStatus.className = "save-status saved";
            vjudgePasswordStatus.textContent = t("vjudgePasswordSaved");
        }
        if (data.model) {
            modelSelect.value = data.model;
        }
        // Sync user profile if cookie was loaded
        if (data.cookie) {
            syncUserProfile();
        }
    } catch (err) {
        console.warn("Failed to load server config:", err);
    }
}

// =========================================================================
// Validate & save API key (DeepSeek / GLM)
// =========================================================================
// Each save button validates its own key against its own provider, regardless
// of which model is currently selected in the dropdown. This keeps the two
// keys independent: validating the DeepSeek key never touches the GLM key and
// vice versa. The backend validate_apikey() routes to the correct endpoint
// based on the model name and persists the key to the matching field.
async function validateAndSaveApiKey() {
    const apiKey = apiKeyInput.value.trim();

    if (!apiKey) {
        apiKeyStatus.className = "save-status error";
        apiKeyStatus.textContent = t("errorEnterApiKey");
        return;
    }

    saveApiKeyBtn.disabled = true;
    apiKeyStatus.className = "save-status loading";
    apiKeyStatus.textContent = t("validating");

    try {
        const api = await pyApi();
        // Always validate against a DeepSeek model so the DeepSeek key is
        // tested against the DeepSeek endpoint and saved to api_key.
        const data = await api.validate_apikey(apiKey, "deepseek-chat");

        if (data.success) {
            apiKeyStatus.className = "save-status success";
            apiKeyStatus.textContent = data.message || t("validateSuccess");
            setTimeout(() => {
                apiKeyStatus.className = "save-status saved";
                apiKeyStatus.textContent = t("savedStatus");
            }, 2000);
        } else {
            apiKeyStatus.className = "save-status error";
            apiKeyStatus.textContent = data.error || t("validateFailed");
        }
    } catch (err) {
        apiKeyStatus.className = "save-status error";
        apiKeyStatus.textContent = t("networkError") + err.message;
    } finally {
        saveApiKeyBtn.disabled = false;
    }
}

async function validateAndSaveGlmApiKey() {
    const apiKey = glmApiKeyInput.value.trim();

    if (!apiKey) {
        glmApiKeyStatus.className = "save-status error";
        glmApiKeyStatus.textContent = t("errorEnterApiKey");
        return;
    }

    saveGlmApiKeyBtn.disabled = true;
    glmApiKeyStatus.className = "save-status loading";
    glmApiKeyStatus.textContent = t("validating");

    try {
        const api = await pyApi();
        // Always validate against a GLM model so the GLM key is tested
        // against the GLM endpoint and saved to glm_api_key.
        const data = await api.validate_apikey(apiKey, "glm-4");

        if (data.success) {
            glmApiKeyStatus.className = "save-status success";
            glmApiKeyStatus.textContent = data.message || t("validateSuccess");
            setTimeout(() => {
                glmApiKeyStatus.className = "save-status saved";
                glmApiKeyStatus.textContent = t("savedStatus");
            }, 2000);
        } else {
            glmApiKeyStatus.className = "save-status error";
            glmApiKeyStatus.textContent = data.error || t("validateFailed");
        }
    } catch (err) {
        glmApiKeyStatus.className = "save-status error";
        glmApiKeyStatus.textContent = t("networkError") + err.message;
    } finally {
        saveGlmApiKeyBtn.disabled = false;
    }
}

// =========================================================================
// Validate & save cookie
// =========================================================================
async function validateAndSaveCookie() {
    const cookie = luoguCookieInput.value.trim();

    if (!cookie) {
        cookieStatus.className = "save-status error";
        cookieStatus.textContent = t("errorEnterCookie");
        return;
    }

    saveCookieBtn.disabled = true;
    cookieStatus.className = "save-status loading";
    cookieStatus.textContent = t("validating");

    try {
        const api = await pyApi();
        const data = await api.validate_cookie(cookie);

        if (data.success) {
            cookieStatus.className = "save-status success";
            cookieStatus.textContent = data.message || t("validateSuccess");
            setTimeout(() => {
                cookieStatus.className = "save-status saved";
                cookieStatus.textContent = t("savedStatus");
            }, 3000);
            // Sync user profile (avatar + name) after cookie is validated
            syncUserProfile();
        } else {
            cookieStatus.className = "save-status error";
            cookieStatus.textContent = data.error || t("validateFailed");
        }
    } catch (err) {
        cookieStatus.className = "save-status error";
        cookieStatus.textContent = t("networkError") + err.message;
    } finally {
        saveCookieBtn.disabled = false;
    }
}

// The password input shows "********" when a stored password exists; treat
// that sentinel as "use the stored password" (empty) so it is never sent.
function vjudgePasswordValue() {
    const v = vjudgePasswordInput.value;
    return v && v !== "********" ? v : "";
}

// Validate & save the Vjudge account credentials. This is the stable auth
// method: the app auto-logs-in on every submission, so the JSESSlONID cookie
// never needs to be re-copied.
async function validateAndSaveVjudgeCreds() {
    const username = vjudgeUsernameInput.value.trim();
    const password = vjudgePasswordValue();

    if (!username || !password) {
        vjudgeCredsStatus.className = "save-status error";
        vjudgeCredsStatus.textContent = t("vjudgeCredsError");
        return;
    }

    saveVjudgeCredsBtn.disabled = true;
    vjudgeCredsStatus.className = "save-status loading";
    vjudgeCredsStatus.textContent = t("vjudgeCredsValidating");

    try {
        const api = await pyApi();
        const data = await api.save_vjudge_credentials(username, password);

        if (data.success) {
            vjudgeCredsStatus.className = "save-status success";
            vjudgeCredsStatus.textContent = data.message || t("vjudgeCredsValidateSuccess");
            vjudgePasswordStatus.className = "save-status saved";
            vjudgePasswordStatus.textContent = t("vjudgePasswordSaved");
            setTimeout(() => {
                vjudgeCredsStatus.className = "save-status saved";
                vjudgeCredsStatus.textContent = t("savedStatus");
            }, 3000);
        } else {
            vjudgeCredsStatus.className = "save-status error";
            vjudgeCredsStatus.textContent = data.error || t("vjudgeCredsValidateFailed");
        }
    } catch (err) {
        vjudgeCredsStatus.className = "save-status error";
        vjudgeCredsStatus.textContent = t("networkError") + err.message;
    } finally {
        saveVjudgeCredsBtn.disabled = false;
        updateSubmitButtonState();
    }
}

// Clear the saved Vjudge account credentials (e.g. wrong password). The
// saved username/password fields are reset and the submit button re-evaluated.
async function clearVjudgeCreds() {
    try {
        const api = await pyApi();
        const data = await api.clear_vjudge_credentials();
        vjudgeUsernameInput.value = "";
        vjudgePasswordInput.value = "";
        vjudgeCredsStatus.className = data.success ? "save-status success" : "save-status error";
        vjudgeCredsStatus.textContent = data.message || data.error || t("vjudgeCredsCleared");
        vjudgePasswordStatus.className = "";
        vjudgePasswordStatus.textContent = "";
        updateSubmitButtonState();
    } catch (err) {
        vjudgeCredsStatus.className = "save-status error";
        vjudgeCredsStatus.textContent = t("networkError") + err.message;
    }
}

// =========================================================================
// Submit code
// =========================================================================
let languagesLoaded = false;
let submitPollTimer = null;
// Current submission target: "luogu" | "vjudge"
let submitOj = "luogu";

async function loadLanguages() {
    if (languagesLoaded) return;
    try {
        const data = await apiGet("/api/languages");
        const langs = data.languages || [];
        langsCache = langs;
        langSelect.innerHTML = "";
        langs.forEach((l) => {
            const opt = document.createElement("option");
            opt.value = l.id;
            opt.textContent = l.name;
            langSelect.appendChild(opt);
        });
        languagesLoaded = true;
    } catch (err) {
        // Keep default option on failure
        console.warn("Failed to load languages:", err);
    }
}

// =========================================================================
// Code templates (per Luogu language id) + template picker dropdown
// =========================================================================
let langsCache = [];

// Insertion marker: after inserting, the caret jumps right after the first
// "TODO" occurrence so the user can start typing immediately.
const CODE_TEMPLATES = {
    12: { // C++17
        nameKey: "tplCpp",
        code: `#include <bits/stdc++.h>
using namespace std;
using ll = long long;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    // TODO

    return 0;
}
`,
    },
    2: { // C
        nameKey: "tplC",
        code: `#include <stdio.h>

int main() {
    // TODO

    return 0;
}
`,
    },
    7: { // Python 3
        nameKey: "tplPy",
        code: `import sys

def main():
    input = sys.stdin.readline
    # TODO

if __name__ == "__main__":
    main()
`,
    },
    8: { // Java (Java 8)
        nameKey: "tplJava",
        code: `import java.util.*;
import java.io.*;

public class Main {
    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        // TODO
    }
}
`,
    },
    14: { // Go
        nameKey: "tplGo",
        code: `package main

import (
    "bufio"
    "fmt"
    "os"
)

func main() {
    in := bufio.NewReader(os.Stdin)
    // TODO
    _ = in
    fmt.Println()
}
`,
    },
    15: { // Rust
        nameKey: "tplRust",
        code: `use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    // TODO
    for line in stdin.lock().lines() {
        if let Ok(line) = line {
            println!("{}", line);
        }
    }
}
`,
    },
    9: { // Node.js
        nameKey: "tplJs",
        code: `const readline = require("readline");

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

rl.on("line", (line) => {
    // TODO
    console.log(line);
});
`,
    },
};

function langNameById(id) {
    const found = langsCache.find((l) => String(l.id) === String(id));
    return found ? found.name : "";
}

function buildTplMenu() {
    if (!tplMenu) return;
    tplMenu.innerHTML = "";
    Object.keys(CODE_TEMPLATES).forEach((id) => {
        const tpl = CODE_TEMPLATES[id];
        const item = document.createElement("button");
        item.type = "button";
        item.className = "tpl-item";
        item.dataset.lang = id;
        item.setAttribute("role", "menuitem");
        item.innerHTML =
            `<span class="tpl-item-lang">${escapeHtml(langNameById(id))}</span>` +
            `<span class="tpl-item-name">${escapeHtml(t(tpl.nameKey))}</span>`;
        item.addEventListener("click", () => {
            insertTemplate(parseInt(id, 10));
            closeTplMenu();
        });
        tplMenu.appendChild(item);
    });
}

function openTplMenu() {
    if (!tplMenu) return;
    if (tplMenu.classList.contains("hidden")) {
        buildTplMenu();
        tplMenu.classList.remove("hidden");
    } else {
        closeTplMenu();
    }
}

function closeTplMenu() {
    if (tplMenu) tplMenu.classList.add("hidden");
}

function insertTemplate(langId) {
    const tpl = CODE_TEMPLATES[langId];
    if (!tpl) return;
    // If the user left language on "auto", switch to the template's language
    if (!langSelect.value || langSelect.value === "0") {
        langSelect.value = String(langId);
    }
    const textarea = codeEditor;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const val = textarea.value;
    textarea.value = val.slice(0, start) + tpl.code + val.slice(end);
    const todoIdx = tpl.code.indexOf("TODO");
    const caret = todoIdx >= 0 ? start + todoIdx + 4 : start + tpl.code.length;
    textarea.focus();
    textarea.setSelectionRange(caret, caret);
    syncCodeHighlight();
    updateSubmitButtonState();
    showStatus("success", t("tplInserted", langNameById(langId) || t(tpl.nameKey)));
}

if (tplBtn) {
    tplBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        openTplMenu();
    });
}
document.addEventListener("click", (e) => {
    if (e.target.closest(".tpl-wrap")) return;
    closeTplMenu();
});

function updateSubmitPanel() {
    const pid = currentProblem ? currentProblem.pid : "";
    if (pid) {
        submitTargetPid.textContent = pid;
        submitHint.textContent = currentOj() === "atcoder" ? t("atcoderSubmitDisabled") : t("submitReady");
    } else {
        submitTargetPid.textContent = t("submitTargetEmpty");
        submitHint.textContent = t("submitHint");
    }
    updateSubmitButtonState();
}

function updateSubmitButtonState() {
    if (currentOj() === "atcoder") {
        submitCodeBtn.disabled = true;
        return;
    }
    let authOk;
    if (submitOj === "vjudge") {
        // Vjudge: account credentials (auto-login) are the only auth method.
        authOk = vjudgeUsernameInput.value.trim() && vjudgePasswordValue();
    } else {
        authOk = luoguCookieInput.value.trim();
    }
    const ready =
        currentProblem &&
        currentProblem.pid &&
        codeEditor.value.trim() &&
        authOk;
    submitCodeBtn.disabled = !ready;
}

// Pending submission state (held while user solves captcha)
let pendingSubmitData = null;
let captchaSession = null; // {sessionCookies, csrfToken}
// Bounded retry counter for captcha attempts. Resets whenever a fresh captcha
// modal opens. Guards against the "never-ending captcha" loop: after MAX_CAPTCHA_ATTEMPTS
// failed attempts we stop auto-refreshing and offer a manual browser fallback.
let captchaAttempts = 0;
const MAX_CAPTCHA_ATTEMPTS = 2;
// Code held for the manual in-browser submission guide (re-copy support).
let manualGuideCode = "";

async function submitCode() {
    const pid = currentProblem ? currentProblem.pid : "";
    const code = codeEditor.value;
    const lang = parseInt(langSelect.value, 10) || 0;
    const cookie = luoguCookieInput.value.trim();
    const enableO2 = enableO2Checkbox.checked;

    // If the captcha modal or the manual-submit guide is already open (e.g. a
    // second submit trigger from a double click / shortcut), do not re-open —
    // that would swap the session under the pending captcha and make it
    // impossible to submit ("验证码错误" loop).
    if (!captchaModal.classList.contains("hidden") || !manualSubmitModal.classList.contains("hidden")) return;

    if (!pid) {
        showStatus("error", t("errorSelectPid"));
        return;
    }
    if (!code.trim()) {
        showStatus("error", t("errorEmptyCode"));
        return;
    }

    // Vjudge: submit directly without captcha (uses saved account credentials)
    if (submitOj === "vjudge") {
        hideStatus();
        if (submitPollTimer) {
            clearTimeout(submitPollTimer);
            submitPollTimer = null;
        }
        showStatus("info", t("submittingToVjudge"));
        submitCodeBtn.disabled = true;
        try {
            const data = await apiCall("submit_vjudge", pid, code, lang, "");
            if (data.url) {
                window.open(data.url, "_blank");
            }
            showStatus("success", t("vjudgeSubmitSuccess"));
            // Clear draft for this problem
            await persistDraft(pid, "");
            draftPid = null;
            setDraftStatus("");
        } catch (err) {
            showStatus("error", err.message || t("errorSubmitFailed"));
        } finally {
            submitCodeBtn.disabled = false;
        }
        return;
    }

    // Luogu: direct submit first. Luogu currently accepts submissions without
    // a captcha for trusted sessions (verified live). Only when the server
    // explicitly requires a captcha (risk-triggered, incl. interactive ones)
    // do we fall back to a manual in-browser submission guide.
    if (!cookie) {
        showStatus("error", t("errorNeedCookie"));
        return;
    }

    hideStatus();
    if (submitPollTimer) {
        clearTimeout(submitPollTimer);
        submitPollTimer = null;
    }

    const contestId = currentContestId || "";
    submitCodeBtn.disabled = true;
    try {
        // Direct submit: no verify / sessionCookies / csrfToken / captchaId.
        // The backend rebuilds a session from the cookie and self-fetches CSRF.
        const data = await apiCall("submit", pid, code, lang, cookie, enableO2, "", "", "", contestId, "");
        handleSubmitSuccess(data.rid, pid, code, lang, enableO2, cookie);
    } catch (err) {
        if (err.captchaRequired) {
            // Luogu asks for a (possibly interactive) captcha that a text
            // input cannot solve -> try the embedded Luogu submit window first
            // (auto-copies the code). On failure, fall back to the manual
            // in-browser submission guide. Never auto-fetch a captcha.
            pendingSubmitData = { pid, code, lang, cookie, enableO2, contestId };
            await openLuoguSubmitWindow(pid, contestId, code);
        } else {
            showStatus("error", err.message || t("errorSubmitFailed"));
        }
    } finally {
        submitCodeBtn.disabled = false;
    }
}

// Shared success handling for both direct submit and captcha-fallback submit.
async function handleSubmitSuccess(rid, pid, code, lang, enableO2, cookie) {
    hideCaptchaModal();
    // Submit succeeded: clear this problem's unsaved-code draft.
    await persistDraft(pid, "");
    draftPid = null;
    setDraftStatus("");
    // Store submission in history (newest first)
    if (!submissionHistory[pid]) {
        submissionHistory[pid] = [];
    }
    submissionHistory[pid].unshift({
        rid: rid,
        code: code,
        lang: lang,
        enableO2: enableO2,
        record: null,
        status: "pending",
    });
    currentRid = rid;
    renderSubmissionHistory(pid);
    judgeResult.classList.remove("hidden");
    renderJudgeResultPlaceholder(rid);
    showStatus("info", t("judgeSubmitSuccess", rid));
    pollRecord(rid, cookie);
}

async function fetchAndShowCaptcha(pid, cookie, contestId) {
    // A fresh modal opens: reset the bounded retry counter and any give-up box.
    captchaAttempts = 0;
    captchaGiveUpBox.classList.add("hidden");
    captchaInput.disabled = false;
    refreshCaptchaBtn.disabled = false;
    captchaImage.src = "";
    captchaInput.value = "";
    captchaError.classList.add("hidden");
    captchaError.textContent = "";
    captchaModal.classList.remove("hidden");
    confirmCaptchaBtn.disabled = true;
    confirmCaptchaBtn.textContent = t("captchaLoading");

    try {
        const data = await apiPost("/api/captcha", { pid, cookie, contestId: contestId || "" });
        captchaImage.src = data.image;
        captchaSession = { captchaId: data.captchaId || "", sessionCookies: data.sessionCookies, csrfToken: data.csrfToken };
        confirmCaptchaBtn.disabled = false;
        confirmCaptchaBtn.textContent = t("captchaConfirm");
        captchaInput.focus();
    } catch (err) {
        captchaError.textContent = err.message || t("captchaFetchFailed");
        captchaError.classList.remove("hidden");
        confirmCaptchaBtn.textContent = t("captchaConfirm");
    }
}

function hideCaptchaModal() {
    captchaModal.classList.add("hidden");
    captchaInput.value = "";
    captchaError.classList.add("hidden");
    captchaGiveUpBox.classList.add("hidden");
    captchaSession = null;
    pendingSubmitData = null;
    captchaAttempts = 0;
    updateSubmitButtonState();
}

// Luogu now uses an interactive click captcha (NetEase Yidun) that cannot be
// auto-filled. Show a guide: copy the code and submit manually in a browser.
function showManualSubmitGuide(pid, contestId, code) {
    manualSubmitModal.classList.remove("hidden");
    manualCopiedTip.classList.add("hidden");
    manualGuideCode = code || "";
    // Auto-copy the code so the user can paste it into Luogu's editor.
    copyToClipboard(manualGuideCode).then((ok) => {
        if (ok) {
            manualCopiedTip.classList.remove("hidden");
        }
    });
    manualOpenLuoguBtn.onclick = () => {
        const cid = contestId || "";
        // Open the problem page scrolled to the submit form (#submit) so the
        // user can paste the copied code and solve the interactive captcha
        // right away (the hash must come after the query string).
        const url = cid
            ? "https://www.luogu.com.cn/problem/" + encodeURIComponent(pid) + "?contest=" + encodeURIComponent(cid) + "#submit"
            : "https://www.luogu.com.cn/problem/" + encodeURIComponent(pid) + "#submit";
        window.open(url, "_blank");
    };
    manualDoneBtn.onclick = () => {
        hideManualSubmitGuide();
        showStatus("info", t("judgeTimeout"));
    };
    manualCancelBtn.onclick = hideManualSubmitGuide;
}

function hideManualSubmitGuide() {
    manualSubmitModal.classList.add("hidden");
    manualCopiedTip.classList.add("hidden");
}

// Try to open an embedded Luogu submit window (WebView2) for interactive
// captcha handling. Auto-fills the code / language / O2 inside the window and
// clicks 提交评测, leaving only the captcha for the user. Also auto-copies the
// code to the clipboard. Falls back to the manual browser guide on failure.
async function openLuoguSubmitWindow(pid, contestId, code) {
    // Auto-copy the code so the user can paste it into Luogu's editor in the
    // embedded window if the auto-fill ever fails.
    copyToClipboard(code || "");
    const p = pendingSubmitData || {};
    try {
        const data = await apiCall(
            "open_luogu_submit_window",
            pid,
            contestId || "",
            p.cookie || "",
            p.code || code || "",
            p.lang || "",
            !!p.enableO2
        );
        if (data && data.success) {
            showStatus("info", t("submitWindowAutoFilled"));
            return true;
        }
        // fall through to manual guide on failure
    } catch (err) {
        // fall through to manual guide
    }
    showManualSubmitGuide(pid, contestId, code);
    return false;
}

async function refreshCaptcha() {
    if (!pendingSubmitData) return;
    captchaGiveUpBox.classList.add("hidden");
    captchaImage.src = "";
    captchaInput.value = "";
    captchaError.classList.add("hidden");
    confirmCaptchaBtn.disabled = true;
    confirmCaptchaBtn.textContent = t("captchaLoading");
    try {
        const data = await apiPost("/api/captcha", { pid: pendingSubmitData.pid, cookie: pendingSubmitData.cookie, contestId: pendingSubmitData.contestId || "" });
        captchaImage.src = data.image;
        captchaSession = { captchaId: data.captchaId || "", sessionCookies: data.sessionCookies, csrfToken: data.csrfToken };
        confirmCaptchaBtn.disabled = false;
        confirmCaptchaBtn.textContent = t("captchaConfirm");
        captchaInput.focus();
    } catch (err) {
        captchaError.textContent = err.message || t("captchaRefreshFailed");
        captchaError.classList.remove("hidden");
        confirmCaptchaBtn.textContent = t("captchaConfirm");
    }
}

// Show the "give up" fallback: stop auto-refreshing (never loop) and offer a
// manual browser submission, which is the only way to satisfy Luogu's new
// interactive (slider/puzzle) captchas that a text input cannot solve.
function showCaptchaGiveUp() {
    captchaGiveUpText.textContent = t("captchaGiveUp");
    captchaGiveUpBox.classList.remove("hidden");
    captchaInput.disabled = true;
    confirmCaptchaBtn.disabled = true;
    refreshCaptchaBtn.disabled = true;
}

async function confirmSubmitWithCaptcha() {
    if (!pendingSubmitData || !captchaSession) return;

    const verify = captchaInput.value.trim();
    if (!verify) {
        captchaError.textContent = t("captchaEmpty");
        captchaError.classList.remove("hidden");
        captchaInput.focus();
        return;
    }

    const { pid, code, lang, cookie, enableO2, contestId } = pendingSubmitData;

    confirmCaptchaBtn.disabled = true;
    confirmCaptchaBtn.textContent = t("captchaSubmitting");
    captchaError.classList.add("hidden");

    try {
        const data = await apiPost("/api/submit", {
            pid: pid,
            code: code,
            lang: lang,
            cookie: cookie,
            enableO2: enableO2,
            verify: verify,
            sessionCookies: captchaSession.sessionCookies,
            csrfToken: captchaSession.csrfToken,
            contestId: contestId || "",
            captchaId: captchaSession.captchaId || "",
        });
        const rid = data.rid;
        hideCaptchaModal();
        await handleSubmitSuccess(rid, pid, code, lang, enableO2, cookie);
    } catch (err) {
        const msg = err.message || t("errorSubmitFailed");
        const isCaptchaIssue = err.captchaRequired ||
            msg.includes("验证码") ||
            msg.toLowerCase().includes("captcha") ||
            msg.toLowerCase().includes("verify") ||
            msg.includes("过期");
        // Close the (dead) text-captcha modal in every case.
        hideCaptchaModal();
        if (!isCaptchaIssue) {
            // Other error - show status
            showStatus("error", msg);
            return;
        }
        // Captcha issue: never auto-fetch a fresh captcha. Luogu now uses an
        // interactive click captcha (NetEase Yidun) that a text input cannot
        // solve, so fall back to the manual in-browser submission guide.
        showManualSubmitGuide(pid, contestId, code);
    }
}

function renderJudgeResultPlaceholder(rid) {
    judgeResult.classList.remove("hidden");
    judgeResult.innerHTML = `
        <div class="judge-pending" id="judgePendingBox">
            <div class="spinner small"></div>
            <div>
                <div class="judge-rid">${t("judgePending", escapeHtml(String(rid)))}</div>
                <div class="judge-waiting" id="judgeWaitingText">${t("judgeWaiting")}</div>
            </div>
        </div>`;
}

function updateJudgePendingText(text) {
    const el = document.getElementById("judgeWaitingText");
    if (el) el.textContent = text;
}

function pollRecord(rid, cookie) {
    // Progressive polling: start fast, slow down over time.
    // Total budget ~4 minutes, which covers even slow judges.
    const MAX_ATTEMPTS = 120;
    const MAX_CONSEC_ERR = 12;      // more tolerant of transient errors

    // Interval schedule (ms) based on attempt number:
    //   1-5:    500ms   (fast initial polls)
    //   6-15:   1000ms
    //   16-40:  1500ms
    //   41+:    3000ms  (slow steady polls)
    function getInterval(attempt) {
        if (attempt <= 5) return 500;
        if (attempt <= 15) return 1000;
        if (attempt <= 40) return 1500;
        return 3000;
    }

    let attempts = 0;
    let consecErrors = 0;
    let lastErrMsg = "";

    if (submitPollTimer) clearTimeout(submitPollTimer);

    const tick = async () => {
        if (attempts >= MAX_ATTEMPTS) {
            submitPollTimer = null;
            updateSubmissionHistoryStatus(rid, "timeout");
            renderJudgeTimeout(rid, cookie, true);
            showStatus("error", t("judgeTimeoutStatus", rid));
            return;
        }
        attempts++;
        try {
            const url = `/api/record/${rid}?cookie=${encodeURIComponent(cookie)}`;
            const data = await apiGet(url);
            const record = data.record;
            const status = record.status;
            consecErrors = 0;  // reset on successful fetch

            // 0 = Waiting, 1 = Judging => non-final, keep polling
            if (status === 0 || status === 1) {
                const waitMsg = status === 0
                    ? t("judgeWaiting")
                    : t("judgeJudging", attempts);
                updateJudgePendingText(waitMsg);
                scheduleNext();
                return;
            }
            // Final result
            submitPollTimer = null;
            updateSubmissionHistoryRecord(record);
            renderJudgeResult(record);
            // Save local record after judge result is received
            if (currentProblem) {
                const savePid = currentProblem.pid;
                const saveList = submissionHistory[savePid] || [];
                const saveSub = saveList.find((s) => String(s.rid) === String(record.rid));
                if (saveSub) {
                    apiCall("save_local_record", savePid, record.rid, saveSub.code, saveSub.lang, record.status, record.score, saveSub.enableO2).catch(() => {});
                }
            }
            const statusText = record.statusText || t("unknown");
            if (status === 8 || status === 12) {
                showStatus("success", t("judgeComplete", statusText, record.score));
            } else {
                showStatus("info", t("judgeComplete", statusText, record.score));
            }
            // Fire a Windows system notification once per finished judge
            if (enableNotifyCheckbox && enableNotifyCheckbox.checked && window.pywebview && window.pywebview.api) {
                const isAc = status === 8 || status === 12;
                const verdict = isAc ? "AC" : statusText;
                const nTitle = `${isAc ? "✅" : "📋"} ${verdict} · ${record.pid || ""}`.trim();
                const nMsg = `${record.title || ""} — ${statusText} · ${record.score} 分`.trim();
                window.pywebview.api.show_system_notification(nTitle, nMsg).catch(() => {});
            }
        } catch (err) {
            consecErrors++;
            lastErrMsg = err.message || "";
            console.warn(`Poll attempt ${attempts} failed (${consecErrors}/${MAX_CONSEC_ERR}):`, lastErrMsg);
            if (consecErrors >= MAX_CONSEC_ERR) {
                submitPollTimer = null;
                updateSubmissionHistoryStatus(rid, "timeout");
                renderJudgeTimeout(rid, cookie, false, lastErrMsg);
                showStatus("error", t("judgeTimeoutStatus", rid));
                return;
            }
            // Show transient error count in the waiting text
            updateJudgePendingText(t("judgeRetryInfo", consecErrors, lastErrMsg));
            scheduleNext();
        }
    };

    const scheduleNext = () => {
        const delay = getInterval(attempts);
        submitPollTimer = setTimeout(tick, delay);
    };

    scheduleNext();  // first poll immediately (getInterval(0) = 500ms)
}

function renderJudgeTimeout(rid, cookie, isMaxAttempts, errMsg) {
    judgeResult.classList.remove("hidden");
    const errDetail = errMsg ? `<div class="judge-err-detail">${escapeHtml(errMsg)}</div>` : "";
    judgeResult.innerHTML = `
        <div class="judge-error">
            <div class="judge-rid">${t("judgePending", escapeHtml(String(rid)))}</div>
            <div>${t("judgeTimeout")}</div>
            ${errDetail}
            <div class="judge-timeout-actions">
                <button type="button" class="btn-secondary judge-retry-btn">${t("judgeContinueWaiting")}</button>
                <a class="btn-link" href="https://www.luogu.com.cn/record/${escapeHtml(String(rid))}" target="_blank" rel="noopener">${t("judgeViewRecord")}</a>
            </div>
        </div>`;
    // Bind "continue waiting" button to restart polling
    const retryBtn = judgeResult.querySelector(".judge-retry-btn");
    if (retryBtn) {
        retryBtn.addEventListener("click", () => {
            if (cookie) {
                renderJudgeResultPlaceholder(rid);
                pollRecord(rid, cookie);
            }
        });
    }
}

// =========================================================================
// Submission history: persists multiple submissions per problem
// =========================================================================
function renderSubmissionHistory(pid) {
    const container = document.getElementById("submissionHistory");
    if (!container) return;
    const submissions = submissionHistory[pid] || [];
    if (submissions.length === 0) {
        container.innerHTML = "";
        container.classList.add("hidden");
        return;
    }
    container.classList.remove("hidden");
    let html = `<div class="history-title">${t("submissionHistoryTitle", submissions.length)}</div><div class="history-list">`;
    submissions.forEach((item) => {
        let badgeText, badgeClass;
        if (item.status === "pending") {
            badgeText = t("judgeWaiting");
            badgeClass = "pending";
        } else if (item.status === "timeout") {
            badgeText = t("judgeTimeout");
            badgeClass = "other";
        } else if (item.record) {
            badgeText = item.record.statusText || t("unknown");
            badgeClass = judgeStatusClass(item.record.status);
        } else {
            badgeText = t("unknown");
            badgeClass = "other";
        }
        const scoreText = item.record ? t("judgeScore", escapeHtml(String(item.record.score))) : "";
        const isActive = String(item.rid) === String(currentRid) ? " active" : "";
        html += `
            <div class="history-item ${badgeClass}${isActive}" data-rid="${escapeHtml(String(item.rid))}" title="${t("viewSubmissionCode")}">
                <span class="history-rid">#${escapeHtml(String(item.rid))}</span>
                <span class="history-status">${escapeHtml(badgeText)}</span>
                <span class="history-score">${scoreText}</span>
            </div>`;
    });
    html += `</div>`;
    container.innerHTML = html;
    // Bind click: show submitted code in modal
    container.querySelectorAll(".history-item").forEach((el) => {
        el.addEventListener("click", () => {
            const rid = el.dataset.rid;
            const sub = submissions.find((s) => String(s.rid) === String(rid));
            if (sub) showSubmissionCode(sub);
        });
    });
}

function updateSubmissionHistoryRecord(record) {
    if (!currentProblem) return;
    const pid = currentProblem.pid;
    const list = submissionHistory[pid];
    if (!list) return;
    const idx = list.findIndex((s) => String(s.rid) === String(record.rid));
    if (idx !== -1) {
        list[idx].record = record;
        list[idx].status = "done";
    }
    renderSubmissionHistory(pid);
}

function updateSubmissionHistoryStatus(rid, status) {
    if (!currentProblem) return;
    const pid = currentProblem.pid;
    const list = submissionHistory[pid];
    if (!list) return;
    const idx = list.findIndex((s) => String(s.rid) === String(rid));
    if (idx !== -1) {
        list[idx].status = status;
    }
    renderSubmissionHistory(pid);
}

function judgeStatusText(status) {
    const st = STATUS_MAP[status] || STATUS_OTHER;
    return t(st.key);
}

function showSubmissionCode(submission) {
    const modal = document.getElementById("submissionCodeModal");
    const codeEl = document.getElementById("submissionCode");
    const titleEl = document.getElementById("submissionCodeTitle");
    const metaEl = document.getElementById("submissionCodeMeta");
    const tcContainer = document.getElementById("submissionTestCases");
    if (!modal || !codeEl || !titleEl) return;
    titleEl.textContent = t("submissionCodeTitle", submission.rid);
    // Show language and O2 info
    let metaText = "";
    const langName = getHljsLangName(submission.lang);
    if (langName) {
        metaText += t("langLabel") + ": " + langName;
    }
    if (submission.enableO2) {
        metaText += (metaText ? " · " : "") + t("judgeO2On");
    }
    if (metaEl) metaEl.textContent = metaText;
    // Render per-test-case details from the stored judge record
    const record = submission.record || null;
    if (tcContainer) {
        const cases = (record && record.test_cases) || [];
        if (cases.length > 0) {
            let html = `<div class="judge-cases-title">${t("judgeCasesTitle", cases.length)}</div><div class="judge-cases-grid">`;
            cases.forEach((tc) => {
                const cls = judgeStatusClass(tc.status);
                const tcMem = tc.memory >= 1024 ? `${(tc.memory / 1024).toFixed(2)} MB` : `${tc.memory} KB`;
                const detail = `${tc.time} ms / ${tcMem}`;
                const msg = tc.message ? `<div class="case-msg">${escapeHtml(tc.message)}</div>` : "";
                html += `
                    <div class="case-item ${cls}">
                        <div class="case-num">${t("judgeCaseNum", tc.case)}</div>
                        <div class="case-status">${escapeHtml(judgeStatusText(tc.status))}</div>
                        <div class="case-detail">${detail}</div>
                        ${msg}
                    </div>`;
            });
            html += `</div>`;
            tcContainer.innerHTML = html;
            tcContainer.classList.remove("hidden");
        } else {
            tcContainer.innerHTML = "";
            tcContainer.classList.add("hidden");
        }
    }
    // Set code and apply syntax highlighting
    codeEl.textContent = submission.code || "";
    codeEl.className = "hljs";
    try {
        if (langName && hljs.getLanguage(langName)) {
            codeEl.innerHTML = hljs.highlight(submission.code || "", { language: langName }).value;
            codeEl.className = `hljs language-${langName}`;
        } else {
            const result = hljs.highlightAuto(submission.code || "");
            codeEl.innerHTML = result.value;
            if (result.language) {
                codeEl.className = `hljs language-${result.language}`;
            }
        }
    } catch (e) {
        codeEl.textContent = submission.code || "";
    }
    // Track current submission so "导出代码" knows which record to export.
    if (typeof setSubmissionExportTarget === "function") {
        setSubmissionExportTarget({ rid: submission.rid, code: submission.code || "", lang: submission.lang });
    }
    modal.classList.remove("hidden");
}

function hideSubmissionCodeModal() {
    const modal = document.getElementById("submissionCodeModal");
    if (modal) modal.classList.add("hidden");
}

function renderJudgeResult(record) {
    const statusText = record.statusText || t("unknown");
    const statusClass = judgeStatusClass(record.status);
    const memKb = record.memory || 0;
    const memText = memKb >= 1024 ? `${(memKb / 1024).toFixed(2)} MB` : `${memKb} KB`;
    const timeText = `${record.time || 0} ms`;

    let casesHtml = "";
    if (record.test_cases && record.test_cases.length > 0) {
        casesHtml = `
            <div class="judge-cases">
                <div class="judge-cases-title">${t("judgeCasesTitle", record.test_cases.length)}</div>
                <div class="judge-cases-grid">`;
        record.test_cases.forEach((tc) => {
            const tcStatusClass = judgeStatusClass(tc.status);
            const tcMem = tc.memory >= 1024 ? `${(tc.memory / 1024).toFixed(2)} MB` : `${tc.memory} KB`;
            casesHtml += `
                <div class="case-item ${tcStatusClass}">
                    <div class="case-num">${t("judgeCaseNum", tc.case)}</div>
                    <div class="case-status">${escapeHtml(tc.statusText || t("unknown"))}</div>
                    <div class="case-detail">${tc.time} ms / ${tcMem}</div>
                </div>`;
        });
        casesHtml += `</div></div>`;
    }

    judgeResult.classList.remove("hidden");
    judgeResult.innerHTML = `
        <div class="judge-summary ${statusClass}">
            <div class="judge-summary-left">
                <span class="judge-status-badge">${escapeHtml(statusText)}</span>
                <span class="judge-score">${t("judgeScore", escapeHtml(String(record.score)))}</span>
            </div>
            <div class="judge-summary-right">
                <span class="judge-metric">${t("judgeTime", timeText)}</span>
                <span class="judge-metric">${t("judgeMemory", memText)}</span>
                ${record.language_name ? `<span class="judge-metric">${escapeHtml(record.language_name)}</span>` : ""}
                ${record.enable_o2 ? `<span class="judge-metric">${t("judgeO2On")}</span>` : ""}
            </div>
        </div>
        ${casesHtml}
        <div class="judge-footer">
            ${(record.status !== 8 && record.status !== 12) ? `<button type="button" class="judge-explain-btn" id="judgeExplainBtn">${t("explainFailureBtn")}</button>` : ""}
            <button type="button" class="btn-link judge-view-code-btn" data-rid="${escapeHtml(String(record.rid))}">${t("viewSubmissionCode")}</button>
            <a class="btn-link" href="https://www.luogu.com.cn/record/${escapeHtml(String(record.rid))}" target="_blank" rel="noopener">${t("judgeViewFullRecord")}</a>
        </div>`;
    // Bind "explain failure" button
    const explainBtn = judgeResult.querySelector("#judgeExplainBtn");
    if (explainBtn) {
        explainBtn.addEventListener("click", () => explainSubmissionFailure(record));
    }
    // Bind "view code" button
    const viewCodeBtn = judgeResult.querySelector(".judge-view-code-btn");
    if (viewCodeBtn) {
        viewCodeBtn.addEventListener("click", () => {
            const rid = viewCodeBtn.dataset.rid;
            if (!currentProblem) return;
            const list = submissionHistory[currentProblem.pid] || [];
            const sub = list.find((s) => String(s.rid) === String(rid));
            if (sub) showSubmissionCode(sub);
        });
    }
}

function judgeStatusClass(status) {
    switch (status) {
        case 8:
        case 12:
            return "ac";
        case 6:
            return "wa";
        case 5:
            return "tle";
        case 4:
            return "mle";
        case 7:
            return "re";
        case 2:
            return "ce";
        default:
            return "other";
    }
}

// =========================================================================
// Local submission records (persistent, per-problem history)
// =========================================================================
let localRecordsVisible = false;
let localRecordsContainer = null;

function createLocalRecordsUI() {
    if (localRecordsContainer) return;
    // Create container after submissionHistory
    const historyEl = document.getElementById("submissionHistory");
    if (!historyEl) return;
    const container = document.createElement("div");
    container.id = "localRecords";
    container.className = "local-records hidden";
    container.style.cssText = "margin-top:12px;border-top:1px solid var(--border);padding-top:12px;";
    container.innerHTML = `<div class="local-records-title">${t("localRecordsTitle")}</div><div class="local-records-list"></div>`;
    historyEl.parentNode.insertBefore(container, historyEl.nextSibling);
    localRecordsContainer = container;
}

function renderLocalRecords() {
    const pid = currentProblem ? currentProblem.pid : "";
    if (!pid || !localRecordsContainer) {
        if (localRecordsContainer) localRecordsContainer.classList.add("hidden");
        return;
    }
    apiCall("get_local_records", pid).then((data) => {
        const records = data.records || [];
        const listEl = localRecordsContainer.querySelector(".local-records-list");
        if (!listEl) return;
        if (records.length === 0) {
            listEl.innerHTML = `<div class="local-records-empty">${t("localRecordsEmpty")}</div>`;
            localRecordsContainer.classList.remove("hidden");
            return;
        }
        // Reset version-compare selection whenever the list re-renders.
        compareSelection = [];
        let html = `
            <div class="local-records-compare-bar" style="display:none;">
                <span>${escapeHtml(t("diffTitle"))}</span>
                <button type="button" class="btn-secondary local-records-compare-btn" style="padding:2px 10px;font-size:12px;">${escapeHtml(t("diffTitle"))}</button>
            </div>`;
        records.forEach((rec) => {
            const statusClass = judgeStatusClass(rec.status);
            const statusText = judgeStatusText(rec.status);
            const timeStr = rec.timestamp ? new Date(rec.timestamp * 1000).toLocaleString() : "";
            const langName = (rec.lang && langSelect) ? Array.from(langSelect.options).find(o => String(o.value) === String(rec.lang))?.text || rec.lang : rec.lang;
            const o2Tag = rec.enable_o2 ? ` <span class="local-records-o2">O2</span>` : "";
            html += `
                <div class="local-records-item ${statusClass}" data-rid="${escapeHtml(String(rec.rid))}">
                    <input type="checkbox" class="compare-check" data-rid="${escapeHtml(String(rec.rid))}" title="${escapeHtml(t("diffTitle"))}">
                    <span class="local-records-status">${escapeHtml(statusText)}</span>
                    <span class="local-records-score">${escapeHtml(String(rec.score))}</span>
                    <span class="local-records-lang">${escapeHtml(langName)}${o2Tag}</span>
                    <span class="local-records-time">${escapeHtml(timeStr)}</span>
                </div>`;
        });
        listEl.innerHTML = html;
        localRecordsContainer.classList.remove("hidden");
        // Bind compare checkboxes + compare button
        if (typeof bindCompareControls === "function") {
            bindCompareControls(localRecordsContainer, records);
        }
        // Bind click (ignore clicks on the checkbox itself): show submitted code
        listEl.querySelectorAll(".local-records-item").forEach((el) => {
            el.addEventListener("click", (e) => {
                if (e.target.classList && e.target.classList.contains("compare-check")) return;
                const rid = el.dataset.rid;
                const rec = records.find((r) => String(r.rid) === String(rid));
                if (rec) {
                    showSubmissionCode({
                        rid: rec.rid,
                        code: rec.code || "",
                        lang: rec.lang,
                        enableO2: rec.enable_o2,
                        record: null,
                        status: "done",
                    });
                }
            });
        });
    }).catch(() => {
        if (localRecordsContainer) localRecordsContainer.classList.add("hidden");
    });
}

function toggleLocalRecords() {
    localRecordsVisible = !localRecordsVisible;
    const btn = document.getElementById("toggleLocalRecordsBtn");
    if (btn) btn.classList.toggle("active", localRecordsVisible);
    if (localRecordsVisible) {
        createLocalRecordsUI();
        renderLocalRecords();
    } else if (localRecordsContainer) {
        localRecordsContainer.classList.add("hidden");
    }
}

// =========================================================================
// Embedded Luogu submit window callbacks
//
// Invoked by the backend (via window.evaluate_js) when the user finishes
// interacting with the embedded Luogu submit window.
// =========================================================================
// The user submitted successfully in the embedded window -> handle it.
window.__onEmbeddedSubmit = (rid) => {
    const p = pendingSubmitData;
    if (!p) return;
    if (submitPollTimer) { clearTimeout(submitPollTimer); submitPollTimer = null; }
    handleSubmitSuccess(rid, p.pid, p.code, p.lang, p.enableO2, p.cookie);
};

// The user closed the embedded window without submitting.
window.__onEmbeddedClose = () => {
    showStatus("info", t("embeddedCancel"));
};

// =========================================================================
// Event bindings
// =========================================================================
analyzeBtn.addEventListener("click", analyze);

problemIdInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") analyze();
});

apiKeyInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") analyze();
});

glmApiKeyInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") analyze();
});

luoguCookieInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") analyze();
});

saveApiKeyBtn.addEventListener("click", validateAndSaveApiKey);
saveGlmApiKeyBtn.addEventListener("click", validateAndSaveGlmApiKey);
saveCookieBtn.addEventListener("click", validateAndSaveCookie);
saveVjudgeCredsBtn.addEventListener("click", validateAndSaveVjudgeCreds);
clearVjudgeCredsBtn.addEventListener("click", clearVjudgeCreds);

// Submission target toggle: switch between Luogu and Vjudge
document.querySelectorAll(".submit-oj-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        submitOj = btn.dataset.oj === "vjudge" ? "vjudge" : "luogu";
        document.querySelectorAll(".submit-oj-btn").forEach((b) => {
            b.classList.toggle("active", b === btn);
        });
        updateSubmitButtonState();
    });
});

// Online IDE mode bindings
ideModeBtn.addEventListener("click", () => {
    if (ideMode) exitIdeMode();
    else enterIdeMode();
});
ideMiniTabs.addEventListener("click", (e) => {
    const btn = e.target.closest(".ide-mini-tab");
    if (!btn) return;
    switchIdeTab(btn.dataset.ideTab);
});
ideRunBtn.addEventListener("click", runLocalTest);
initIdeDivider();

// Toggle collapse/expand for the API key + Cookie config row
configCollapseBtn.addEventListener("click", () => {
    const configRow = configCollapseBtn.closest(".input-row");
    const hint = document.querySelector(".input-hint");
    const collapsed = configRow.classList.toggle("collapsed");
    configCollapseBtn.classList.toggle("collapsed", collapsed);
    if (hint) hint.classList.toggle("collapsed", collapsed);
    configCollapseBtn.title = collapsed ? "展开配置" : "收起配置";
});

// Input example popups: show full fill-in example below the field on focus,
// hide on blur.
document.querySelectorAll("[data-example-key]").forEach((ex) => {
    const input = ex.closest(".input-group").querySelector("input");
    if (!input) return;
    input.addEventListener("focus", () => {
        ex.textContent = t(ex.dataset.exampleKey);
        ex.classList.remove("hidden");
    });
    input.addEventListener("blur", () => ex.classList.add("hidden"));
});

submitCodeBtn.addEventListener("click", submitCode);
codeEditor.addEventListener("input", () => {
    updateSubmitButtonState();
    syncCodeHighlight();
});
codeEditor.addEventListener("scroll", syncCodeScroll);
codeEditor.addEventListener("keydown", handleCodeKeydown);
langSelect.addEventListener("change", syncCodeHighlight);
luoguCookieInput.addEventListener("input", updateSubmitButtonState);
enableBracketCheckbox.addEventListener("change", () => {
    localStorage.setItem(STORAGE_KEYS.bracket, enableBracketCheckbox.checked ? "1" : "0");
});
enableNotifyCheckbox.addEventListener("change", () => {
    localStorage.setItem(STORAGE_KEYS.notify, enableNotifyCheckbox.checked ? "1" : "0");
});

// =========================================================================
// Drag-and-drop file upload for code editor
// =========================================================================
const EXT_TO_LANG = {
    ".cpp": 14,  // C++17
    ".cxx": 14,
    ".cc": 14,
    ".c": 2,     // C
    ".py": 7,    // Python 3
    ".java": 11, // Java
    ".go": 31,   // Go
    ".rs": 27,   // Rust
    ".js": 20,   // Node.js
    ".ts": 20,
    ".pas": 1,   // Pascal
    ".cs": 19,   // C#
};

// Language name to option value mapping for the select dropdown
const EXT_TO_LANG_NAME = {
    ".cpp": "C++17",
    ".cxx": "C++17",
    ".cc": "C++17",
    ".c": "C",
    ".py": "Python 3",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".js": "Node.js",
    ".ts": "Node.js",
    ".pas": "Pascal",
    ".cs": "C#",
};

function setupDragDrop(editor, isStdin) {
    if (!editor) return;

    editor.addEventListener("dragover", (e) => {
        e.preventDefault();
        e.stopPropagation();
        editor.style.outline = "2px solid var(--primary)";
        editor.style.outlineOffset = "-2px";
    });

    editor.addEventListener("dragleave", (e) => {
        e.preventDefault();
        e.stopPropagation();
        editor.style.outline = "";
        editor.style.outlineOffset = "";
    });

    editor.addEventListener("drop", (e) => {
        e.preventDefault();
        e.stopPropagation();
        editor.style.outline = "";
        editor.style.outlineOffset = "";

        const files = e.dataTransfer.files;
        if (!files || files.length === 0) return;

        const file = files[0];
        const reader = new FileReader();
        reader.onload = (ev) => {
            const content = ev.target.result;
            if (isStdin) {
                // For IDE stdin, just set the value
                editor.value = content;
            } else {
                // For code editor, set the code and try to auto-detect language
                editor.value = content;
                // Trigger syntax highlighting update
                if (typeof syncCodeHighlight === "function") {
                    syncCodeHighlight();
                }
                // Try to auto-select language
                const ext = "." + file.name.split(".").pop().toLowerCase();
                const langName = EXT_TO_LANG_NAME[ext];
                if (langName && langSelect) {
                    // Find the option by text
                    for (const opt of langSelect.options) {
                        if (opt.text.includes(langName) || opt.text.toLowerCase().includes(langName.toLowerCase())) {
                            langSelect.value = opt.value;
                            break;
                        }
                    }
                }
            }
        };
        reader.readAsText(file);
    });
}

// Apply to code editor
setupDragDrop(codeEditor, false);

// Apply to IDE stdin
setupDragDrop(ideStdin, true);

copyCodeBtn.addEventListener("click", () => {
    copyToClipboard(codeEditor.value, copyCodeBtn);
});

// Manual draft save button
saveDraftBtn.addEventListener("click", async () => {
    const pid = draftTargetPid();
    if (!pid) {
        showStatus("error", t("errorSelectPid"));
        return;
    }
    if (!codeEditor.value.trim()) {
        setDraftStatus(t("draftEmpty"));
        return;
    }
    await saveCurrentDraft(true);
});

// Local records toggle button
(function initLocalRecordsBtn() {
    const btn = document.createElement("button");
    btn.id = "toggleLocalRecordsBtn";
    btn.type = "button";
    btn.className = "btn-secondary";
    btn.textContent = t("localRecordsBtn");
    btn.style.marginRight = "auto";
    // Insert before saveDraftBtn
    const parent = saveDraftBtn.parentNode;
    if (parent) parent.insertBefore(btn, saveDraftBtn);
    btn.addEventListener("click", toggleLocalRecords);
})();

refreshCaptchaBtn.addEventListener("click", refreshCaptcha);
cancelCaptchaBtn.addEventListener("click", hideCaptchaModal);
confirmCaptchaBtn.addEventListener("click", confirmSubmitWithCaptcha);
captchaInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !confirmCaptchaBtn.disabled) {
        confirmSubmitWithCaptcha();
    }
});
// Manual fallback: open the problem on Luogu in a new tab so the user can
// complete the (possibly interactive) captcha and submit in the browser.
captchaOpenLuoguBtn.addEventListener("click", () => {
    if (pendingSubmitData && pendingSubmitData.pid) {
        window.open("https://www.luogu.com.cn/problem/" + encodeURIComponent(pendingSubmitData.pid), "_blank");
    }
    hideCaptchaModal();
});

// Manual submit guide: close on backdrop click
if (manualSubmitModal) {
    manualSubmitModal.addEventListener("click", (e) => {
        if (e.target === manualSubmitModal) hideManualSubmitGuide();
    });
}
// Manual submit guide: re-copy the code on demand
if (manualCopyCodeBtn) {
    manualCopyCodeBtn.addEventListener("click", () => {
        copyToClipboard(manualGuideCode).then((ok) => {
            if (ok) {
                manualCopiedTip.classList.remove("hidden");
            }
        });
    });
}

// Submission code modal: close on button click or backdrop click
const submissionCodeCloseBtn = $("#submissionCodeCloseBtn");
if (submissionCodeCloseBtn) {
    submissionCodeCloseBtn.addEventListener("click", hideSubmissionCodeModal);
}
const submissionCodeModalEl = $("#submissionCodeModal");
if (submissionCodeModalEl) {
    submissionCodeModalEl.addEventListener("click", (e) => {
        if (e.target === submissionCodeModalEl) hideSubmissionCodeModal();
    });
}

// User profile: click to open, close on button/backdrop
userProfileArea.addEventListener("click", openProfileModal);
profileCloseBtn.addEventListener("click", closeProfileModal);
profileModal.addEventListener("click", (e) => {
    if (e.target === profileModal) closeProfileModal();
});
// Blog button: open blog modal with the current profile's uid
if (profileBlogBtn) {
    profileBlogBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        const uid = profileViewUid || (userInfoCache && userInfoCache.uid);
        if (uid) {
            showBlog(uid);
        }
    });
}

// User search modal bindings
if (userSearchBtn) {
    userSearchBtn.addEventListener("click", () => {
        userSearchModal.classList.remove("hidden");
        userSearchInput.focus();
        userSearchInput.select();
    });
}
if (userSearchCloseBtn) {
    userSearchCloseBtn.addEventListener("click", () => {
        userSearchModal.classList.add("hidden");
    });
}
if (userSearchModal) {
    userSearchModal.addEventListener("click", (e) => {
        if (e.target === userSearchModal) userSearchModal.classList.add("hidden");
    });
}
if (userSearchGoBtn) {
    userSearchGoBtn.addEventListener("click", searchLuoguUsers);
}
if (userSearchInput) {
    userSearchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") searchLuoguUsers();
    });
}

async function searchLuoguUsers() {
    const keyword = (userSearchInput.value || "").trim();
    if (!keyword) return;
    userSearchResults.innerHTML = `<div class="user-search-empty"><div class="spinner" style="margin:0 auto 10px;"></div>${escapeHtml(t("userSearching"))}</div>`;
    try {
        const data = await apiCall("search_users", keyword);
        const users = (data && data.users) || [];
        if (!users.length) {
            userSearchResults.innerHTML = `<div class="user-search-empty">${escapeHtml(t("userSearchEmpty"))}</div>`;
            return;
        }
        userSearchResults.innerHTML = users.map((u) => {
            let avatarUrl = u.avatar || "";
            if (avatarUrl && !avatarUrl.startsWith("http")) {
                avatarUrl = "https://cdn.luogu.com.cn" + (avatarUrl.startsWith("/") ? "" : "/") + avatarUrl;
            }
            let metaBits = [];
            if (u.ccfLevel) metaBits.push(`${t("profileCcfLevel")}: ${u.ccfLevel}`);
            if (u.xcpcLevel) metaBits.push(`${t("profileXcpcLevel")}: ${u.xcpcLevel}`);
            if (u.slogan) metaBits.push(u.slogan);
            if (u.isBanned) metaBits.push(t("profileVerifiedNo"));
            return `
                <div class="user-search-item" data-uid="${escapeHtml(u.uid)}" data-name="${escapeHtml(u.name)}">
                    <img class="user-search-avatar" alt="" src="${escapeHtml(avatarUrl)}">
                    <div class="user-search-item-body">
                        <div class="user-search-item-name">${escapeHtml(u.name)} <span style="color:var(--muted);font-weight:400;">#${escapeHtml(u.uid)}</span></div>
                        <div class="user-search-item-meta">${escapeHtml(metaBits.join(" · ") || `UID: ${u.uid}`)}</div>
                    </div>
                    <span class="btn-secondary" style="padding:3px 10px;font-size:12px;">${escapeHtml(t("userOpenHome"))}</span>
                </div>`;
        }).join("");
        userSearchResults.querySelectorAll(".user-search-item").forEach((item) => {
            item.addEventListener("click", () => {
                openUserHomepage(item.dataset.uid, item.dataset.name);
            });
        });
    } catch (err) {
        userSearchResults.innerHTML = `<div class="user-search-empty">${escapeHtml((err && err.message) || t("userSearchFailed"))}</div>`;
    }
}

// Collection (题单) modal bindings
collectCloseBtn.addEventListener("click", closeCollectModal);
collectModal.addEventListener("click", (e) => {
    if (e.target === collectModal) closeCollectModal();
});
collectCreateBtn.addEventListener("click", createCollectAndAdd);
collectNewName.addEventListener("keypress", (e) => {
    if (e.key === "Enter") createCollectAndAdd();
});
uncollectCloseBtn.addEventListener("click", closeUncollectModal);
uncollectCancelBtn.addEventListener("click", closeUncollectModal);
uncollectConfirmBtn.addEventListener("click", confirmUncollect);
uncollectModal.addEventListener("click", (e) => {
    if (e.target === uncollectModal) closeUncollectModal();
});

// =========================================================================
// Disclaimer modal (免责声明, only shown on the very first launch)
// =========================================================================
const disclaimerModal = document.getElementById("disclaimerModal");
const disclaimerBody = document.getElementById("disclaimerBody");
const disclaimerCheck = document.getElementById("disclaimerCheck");
const disclaimerConfirmBtn = document.getElementById("disclaimerConfirmBtn");

function showDisclaimerModal() {
    if (!disclaimerModal) return;
    // 未勾选时确认按钮始终不可用
    if (disclaimerCheck) disclaimerCheck.checked = false;
    if (disclaimerConfirmBtn) disclaimerConfirmBtn.disabled = true;
    disclaimerModal.classList.remove("hidden");
}

// 初次启动展示完整免责声明；同意后写入 localStorage，后续不再弹出。
async function showDisclaimerIfFirstRun() {
    if (!disclaimerModal || !disclaimerBody) return;
    if (localStorage.getItem(STORAGE_KEYS.disclaimer) === "1") return;
    let content = "";
    try {
        const data = await apiCall("get_disclaimer");
        if (data && data.success && data.content) content = data.content;
    } catch (err) {
        console.warn("get_disclaimer failed:", err);
    }
    // 加载失败时兜底展示页脚简版声明，保证首次启动一定有内容可读。
    if (!content) content = t("footerDisclaimer");
    if (window.marked && window.marked.parse) {
        disclaimerBody.innerHTML = window.marked.parse(content);
    } else {
        disclaimerBody.textContent = content;
    }
    showDisclaimerModal();
}

if (disclaimerCheck) {
    disclaimerCheck.addEventListener("change", () => {
        if (disclaimerConfirmBtn) {
            disclaimerConfirmBtn.disabled = !disclaimerCheck.checked;
        }
    });
}

if (disclaimerConfirmBtn) {
    disclaimerConfirmBtn.addEventListener("click", () => {
        // 未勾选则不能确认
        if (!disclaimerCheck || !disclaimerCheck.checked) return;
        localStorage.setItem(STORAGE_KEYS.disclaimer, "1");
        if (disclaimerModal) disclaimerModal.classList.add("hidden");
    });
}

// =========================================================================
// Language toggle (zh / en)
// =========================================================================
function loadSavedLang() {
    const savedLang = localStorage.getItem(STORAGE_KEYS.lang);
    if (savedLang === "zh" || savedLang === "en") {
        setLang(savedLang);
    } else {
        // Default to browser language
        const browserLang = (navigator.language || navigator.userLanguage || "zh").toLowerCase();
        setLang(browserLang.startsWith("zh") ? "zh" : "en");
    }
}

if (langToggle) {
    langToggle.addEventListener("click", () => {
        setLang(currentLang === "zh" ? "en" : "zh");
        updateSearchPlaceholder();
    });
}

// Load saved config and language on page load
// pywebview injects window.pywebview.api AFTER the 'pywebviewready' event,
// so we must defer server-config loading until then. UI-only prefs (theme,
// lang, mode) can run immediately since they only touch localStorage.
loadSavedLang();

async function initAfterPywebviewReady() {
    // Load config FIRST so the cookie input is populated before
    // markProblemStatus() runs inside loadDefaultProblems().
    try {
        await loadSavedConfig();
    } catch (err) {
        console.warn("loadSavedConfig failed:", err);
    }
    // Load default problem list on startup (cookie is now available)
    loadDefaultProblems().catch((err) => {
        console.warn("loadDefaultProblems failed:", err);
    });
    // Start the 30s autosave timer for unsaved code drafts
    draftTimer = setInterval(() => {
        const pid = draftTargetPid();
        if (pid && codeEditor.value.trim()) {
            persistDraft(pid, codeEditor.value);
        }
    }, DRAFT_INTERVAL_MS);
    // Initialize the AI assistant chat panel
    assistantInit();
    // Initialize daily-feature buttons (打卡 / 统计 / 比赛提醒)
    initDailyFeatures();
    // Initialize new features (比赛榜单 / 错题本 / 智能推荐 / 版本对比)
    initNewFeatures();
    // Show disclaimer modal on first launch (blocks UI until confirmed)
    showDisclaimerIfFirstRun().catch((err) => {
        console.warn("showDisclaimerIfFirstRun failed:", err);
    });
    // On startup: auto check-in (backend skips if already done) + contest reminders
    setTimeout(() => { doCheckin().catch(() => {}); }, 800);
    setTimeout(() => { checkContestReminders(false, true).catch(() => {}); }, 1600);
}

if (window.pywebview && window.pywebview.api) {
    // API already available (e.g. when reloaded after initial load)
    initAfterPywebviewReady();
} else {
    // Wait for pywebview to inject the API bridge
    window.addEventListener("pywebviewready", initAfterPywebviewReady);
}

// =========================================================================
// Lazy loading helpers for profile sections (做题趋势 / 标签分布 / 提交记录)
// =========================================================================

// 做题趋势 tab: 180-day trend + 7-day activity (uses the shared stats cache)
function loadProfileTrends() {
    const trendChart = document.getElementById("profileTrendChart");
    const weekChart = document.getElementById("profileWeekChart");
    if (!trendChart || !weekChart) return;
    loadProfileStats((luoguCookieInput.value || "").trim(), null, "trend");
}

// 标签分布 tab: tag distribution (uses the shared stats cache)
function loadProfileTags() {
    const tagBody = document.getElementById("profileTagBody");
    if (!tagBody) return;
    tagBody.innerHTML = `<div class="section-spinner"><div class="spinner"></div></div>`;
    loadProfileStats((luoguCookieInput.value || "").trim(), null, "tags");
}

// 提交记录 tab: recent submissions (public; private for other users)
function loadProfileRecent() {
    const recentBody = document.getElementById("recentBody");
    if (!recentBody) return;
    recentBody.innerHTML = `<tr><td colspan="6"><div class="section-spinner"><div class="spinner"></div></div></td></tr>`;
    const cookie = (luoguCookieInput.value || "").trim();
    const recentReq = profileViewUid !== null
        ? apiCall("get_recent_submissions_by_uid", profileViewUid)
        : apiCall("get_recent_submissions", cookie);
    recentReq
        .then((recentData) => {
            renderRecentSubmissions((recentData && recentData.records) || []);
        })
        .catch((err) => {
            // Other users' submission lists are often private
            if (profileViewUid !== null) {
                renderRecentSubmissionsPrivate((err && err.message) || t("userSearchFailed"));
            } else {
                renderRecentSubmissions([]);
            }
        });
}

// Reset lazy loading flags when the profile modal is closed
function resetLazyLoadingFlags() {
    profileStatsLoaded = false;
    profileTrendLoaded = false;
    profileTagsLoaded = false;
    profileRecentLoaded = false;
    profileStatsCache = null;
}
