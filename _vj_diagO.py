# -*- coding: utf-8 -*-
"""Temporary diagnostic: find M.token source + U data + submit_methods."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"
BUNDLE = "/static/bundle/1ab4f2a25ddef0442d12.js"

s = app._build_vjudge_session(COOKIE)
page = s.get(f"{app.VJUDGE_BASE}/problem/{app._build_vj_pid(PID)}", timeout=20).text

print("=== problem page: token refs ===")
for m in re.finditer(r'[^"\'\s]*token[^"\'\s]{0,60}', page, re.I):
    t = m.group(0)
    if len(t) < 200:
        print(" ", t[:120])

print("\n=== problem page: data-oj / data-num / data-... attrs ===")
for m in re.finditer(r'data-(?:oj|num|problem-id|method|prob-num|oj-name)="[^"]*"', page, re.I):
    print(" ", m.group(0)[:150])

print("\n=== problem page: submit button element ===")
for m in re.finditer(r'<[^>]*id="btn-submit"[^>]*>', page):
    print(" ", m.group(0)[:300])

print("\n=== bundle: M.token assignments ===")
js = s.get(f"{app.VJUDGE_BASE}{BUNDLE}", timeout=20).text
for m in re.finditer(r'M\.token\s*=|\.token\s*=\s*[^;,]{0,80}', js):
    print(" ", m.group(0)[:120])
for m in re.finditer(r'submit_methods', js):
    a = max(0, m.start() - 300)
    b = min(len(js), m.end() + 500)
    print("\n--- submit_methods ctx @", m.start(), "---")
    print(js[a:b][:800])
