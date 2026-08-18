# -*- coding: utf-8 -*-
"""Temporary diagnostic: inspect how the Vjudge problem page submits code."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"

vj_pid = app._build_vj_pid(PID)
s = app._build_vjudge_session(COOKIE)
r = s.get(f"{app.VJUDGE_BASE}/problem/{vj_pid}", timeout=20)
html = r.text

# 1) All forms
print("=== <form ...> tags ===")
for m in re.finditer(r'<form[^>]*>', html):
    print(" ", m.group(0)[:300])

# 2) References to submit endpoints / APIs
print("=== 'submit' endpoint refs ===")
for m in re.finditer(r'[^"\'\s]*(?:submit|Submit)[^"\'\s]*', html):
    t = m.group(0)
    if len(t) < 200:
        print(" ", t[:160])
