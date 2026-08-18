# -*- coding: utf-8 -*-
"""Temporary diagnostic: extract remoteOJs (OJ registry) from problem page."""
import re
import json
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"

vj_pid = app._build_vj_pid(PID)
s = app._build_vjudge_session(COOKIE)
page = s.get(f"{app.VJUDGE_BASE}/problem/{vj_pid}", timeout=20).text

# Search for remoteOJs in page
idx = page.find("remoteOJs")
print("remoteOJs found at:", idx)
if idx >= 0:
    seg = page[max(0, idx-400):idx+2000]
    print(seg[:2400].replace("\n", " "))
