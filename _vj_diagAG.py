# -*- coding: utf-8 -*-
"""Temporary diagnostic: dump inline scripts from problem page."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"
s = app._build_vjudge_session(COOKIE)
page = s.get(f"{app.VJUDGE_BASE}/problem/{app._build_vj_pid(PID)}", timeout=20).text
print("page len:", len(page))

# All inline <script> blocks (no src)
for i, m in enumerate(re.finditer(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', page, re.S)):
    body = m.group(1).strip()
    if not body:
        continue
    interesting = any(k in body for k in ["cfg", "Oj", "OJ", "language", "window.", "= {", "JSON"])
    print(f"\n--- inline script #{i} len={len(body)} interesting={interesting} ---")
    print(body[:1500].replace("\n", " "))
