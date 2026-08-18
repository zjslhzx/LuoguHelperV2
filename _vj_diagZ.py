# -*- coding: utf-8 -*-
"""Temporary diagnostic: locate Vjudge OJ registry (languages per OJ)."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"

s = app._build_vjudge_session(COOKIE)
page = s.get(f"{app.VJUDGE_BASE}/problem/{app._build_vj_pid(PID)}", timeout=20).text
srcs = [u for u in re.findall(r'<script[^>]*src="([^"]+)"', page) if u.startswith("/static/bundle/")]

# Try common OJ registry endpoints
for url in ["/ojs", "/ojs?type=json", "/oj/list", "/user/ojs"]:
    try:
        r = s.get(f"{app.VJUDGE_BASE}{url}", timeout=15)
        print("\nGET", url, "->", r.status_code, r.headers.get("Content-Type", ""))
        print("   ", r.text[:300].replace("\n", " "))
    except Exception as e:
        print("\nGET", url, "EXC", e)

# Search bundles for 'getOjs' / '/ojs'
for u in srcs:
    js = s.get(f"{app.VJUDGE_BASE}{u}", timeout=20).text
    for kw in ["getOjs", "'/ojs'", '"/ojs"', "ojs?"]:
        if kw in js:
            idx = js.find(kw)
            print(f"\n[{u}] '{kw}' ctx:", js[max(0, idx-200):idx+300].replace("\n", " ")[:500])
            break
