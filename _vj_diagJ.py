# -*- coding: utf-8 -*-
"""Temporary diagnostic: extract Vjudge's JS submit endpoint & payload."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"

vj_pid = app._build_vj_pid(PID)
s = app._build_vjudge_session(COOKIE)
r = s.get(f"{app.VJUDGE_BASE}/problem/{vj_pid}", timeout=20)
html = r.text

# Find all <script> blocks and any JS source urls that could hold submit logic.
print("=== script srcs ===")
for m in re.finditer(r'<script[^>]*src="([^"]+)"', html):
    print(" ", m.group(1))

print("=== ajax / post / fetch refs ===")
for pat in [r'\$\.post\s*\([^)]{0,200}', r'\$\.ajax\s*\([^)]{0,200}',
            r'axios\.\w+\s*\([^)]{0,200}', r'fetch\s*\(\s*["\'][^"\']{0,80}',
            r'url\s*:\s*["\'][^"\']{0,80}', r'action\s*:\s*["\'][^"\']{0,80}']:
    for m in re.finditer(pat, html):
        print(" ", m.group(0)[:180])
