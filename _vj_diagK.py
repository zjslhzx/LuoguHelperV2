# -*- coding: utf-8 -*-
"""Temporary diagnostic: find the Vjudge JS submit endpoint in bundles."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"

vj_pid = app._build_vj_pid(PID)
s = app._build_vjudge_session(COOKIE)
r = s.get(f"{app.VJUDGE_BASE}/problem/{vj_pid}", timeout=20)
html = r.text

srcs = re.findall(r'<script[^>]*src="([^"]+)"', html)
srcs = [u for u in srcs if u.startswith("/static/bundle/")]
print("bundles:", len(srcs))

keywords = ["submit", "problemId", "judgeServer", "/problem/"]
for u in srcs:
    url = f"{app.VJUDGE_BASE}{u}"
    try:
        js = s.get(url, timeout=20).text
    except Exception as e:
        print("  ERR", u, e)
        continue
    hits = set()
    for kw in ["problem/submit", "/submit", "problemId", "csrf", "CSRF"]:
        if kw.lower() in js.lower():
            hits.add(kw)
    if hits:
        print("  ", u, "->", sorted(hits))
        # print short context around 'submit' endpoint strings
        for m in re.finditer(r'["\'](/problem/submit[^"\']*)["\']', js):
            print("     endpoint:", m.group(1))
