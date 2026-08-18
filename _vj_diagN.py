# -*- coding: utf-8 -*-
"""Temporary diagnostic: extract submit modal form fields from bundle."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"
BUNDLE = "/static/bundle/1ab4f2a25ddef0442d12.js"

s = app._build_vjudge_session(COOKIE)
js = s.get(f"{app.VJUDGE_BASE}{BUNDLE}", timeout=20).text

# Find the modal template containing name="method" etc.
for kw in ['name="method"', 'name="open"', 'name="source"', 'name="language"',
           'token:', 'M.token', 'M=', 'const M', 'let M', 'turnstile']:
    idx = js.find(kw)
    print(f"\n=== first '{kw}' at {idx} ===")
    if idx >= 0:
        a = max(0, idx - 500)
        b = min(len(js), idx + 500)
        print(js[a:b])
