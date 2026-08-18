# -*- coding: utf-8 -*-
"""Temporary diagnostic: find remoteOJs / setCfg call sites in all bundles."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
s = app._build_vjudge_session(COOKIE)
page = s.get(f"{app.VJUDGE_BASE}/problem/{app._build_vj_pid('P1001')}", timeout=20).text
srcs = sorted(set(re.findall(r'<script[^>]*src="(/static/bundle/[^"]+)"', page)))

for u in srcs:
    try:
        js = s.get(f"{app.VJUDGE_BASE}{u}", timeout=25).text
    except Exception:
        continue
    for kw in ["remoteOJs", "setCfg", "getCfg", "remote_oj", "remoteOj"]:
        for m in re.finditer(re.escape(kw), js):
            i = m.start()
            print(f"### {u} '{kw}':", js[max(0, i-200):i+200].replace("\n", " ")[:420])
