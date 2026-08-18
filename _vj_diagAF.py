# -*- coding: utf-8 -*-
"""Temporary diagnostic: find cfg endpoint + try direct config URLs."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"
s = app._build_vjudge_session(COOKIE)
page = s.get(f"{app.VJUDGE_BASE}/problem/{app._build_vj_pid(PID)}", timeout=20).text
srcs = sorted(set(re.findall(r'<script[^>]*src="([^"]+)"', page) if u.startswith("/") else "" for u in []))

# gather all bundle urls
srcs = sorted(set(re.findall(r'<script[^>]*src="(/static/bundle/[^"]+)"', page)))
print("bundles:", len(srcs))

# search each bundle for config-fetching patterns
for u in srcs:
    try:
        js = s.get(f"{app.VJUDGE_BASE}{u}", timeout=25).text
    except Exception:
        continue
    for kw in ["setCfg", "/config", "getCfg()", ".cfg=", "cfg,", "getOjs"]:
        idx = js.find(kw)
        if idx >= 0:
            # only print interesting fetch contexts
            if kw in ("/config", "setCfg"):
                print(f"\n### {u} '{kw}' ctx:", js[max(0, idx-250):idx+250].replace("\n", " ")[:500])

# try likely config endpoints
print("\n=== config endpoint probes ===")
for url in ["/config", "/api/config", "/user/config", "/ojs", "/user/ojs",
            "/problem/ojs", "/oj?OJId=%E6%B4%9B%E8%B0%B7",
            "/problem/ojconfig/%E6%B4%9B%E8%B0%B7"]:
    try:
        r = s.get(f"{app.VJUDGE_BASE}{url}", timeout=15)
        print(f"GET {url} -> {r.status_code} {r.headers.get('Content-Type','')}")
        if r.status_code == 200:
            txt = r.text
            if "洛谷" in txt or "GNU C++" in txt or "languages" in txt:
                print("   CONTAINS languages/luogu:", txt[:300].replace("\n", " "))
    except Exception as e:
        print(f"GET {url} EXC {e}")
