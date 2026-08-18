# -*- coding: utf-8 -*-
"""Temporary diagnostic: extract the submit payload fields + token source."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"
BUNDLE = "/static/bundle/1ab4f2a25ddef0442d12.js"

s = app._build_vjudge_session(COOKIE)
js = s.get(f"{app.VJUDGE_BASE}{BUNDLE}", timeout=20).text

idx = js.find("problem/submit")
# Bigger window BEFORE the submit call to see n.data construction
a = max(0, idx - 2200)
b = min(len(js), idx + 1200)
seg = js[a:b]
print(seg)
