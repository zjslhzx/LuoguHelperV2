# -*- coding: utf-8 -*-
"""Temporary diagnostic: dump problem page inline JS data (U config + token)."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"
BUNDLE = "/static/bundle/1ab4f2a25ddef0442d12.js"

s = app._build_vjudge_session(COOKIE)
page = s.get(f"{app.VJUDGE_BASE}/problem/{app._build_vj_pid(PID)}", timeout=20).text

for kw in ["submitMethods", "probNum", "problemId", "csrf", "csrf-token",
           "oj:", '"oj"', "token", "data-oj", "data-num", "M.token",
           "openModal", "showSubmit"]:
    hits = [m.start() for m in re.finditer(re.escape(kw), page)]
    print(f"\n=== '{kw}' -> {len(hits)} hits ===")
    for h in hits[:3]:
        a = max(0, h - 200)
        b = min(len(page), h + 300)
        print("   ...", page[a:b].replace("\n", " ")[:500])
