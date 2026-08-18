# -*- coding: utf-8 -*-
"""Temporary diagnostic: extract exact submit endpoint & payload from bundle."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"
BUNDLE = "/static/bundle/1ab4f2a25ddef0442d12.js"

s = app._build_vjudge_session(COOKIE)
js = s.get(f"{app.VJUDGE_BASE}{BUNDLE}", timeout=20).text
print("bundle size:", len(js))

# Print contexts around "problem/submit" occurrences
for m in re.finditer(r'problem/submit', js):
    a = max(0, m.start() - 400)
    b = min(len(js), m.end() + 400)
    print("\n===== context @", m.start(), "=====")
    print(js[a:b])
