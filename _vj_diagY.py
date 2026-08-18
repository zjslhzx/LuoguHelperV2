# -*- coding: utf-8 -*-
"""Temporary diagnostic: find how submit bundle loads language list."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
BUNDLE = "/static/bundle/1ab4f2a25ddef0442d12.js"

s = app._build_vjudge_session(COOKIE)
js = s.get(f"{app.VJUDGE_BASE}{BUNDLE}", timeout=20).text

for kw in ["languages", "languageList", "getLanguages", "lang", "ojLangs"]:
    print(f"\n=== '{kw}' ===")
    seen = 0
    for m in re.finditer(re.escape(kw), js):
        if seen >= 3:
            break
        a = max(0, m.start() - 150)
        b = min(len(js), m.end() + 250)
        print("   ...", js[a:b].replace("\n", " ")[:400])
        seen += 1
