# -*- coding: utf-8 -*-
"""Temporary diagnostic: find setCfg source (config endpoint)."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
s = app._build_vjudge_session(COOKIE)

for u in [
    "/static/bundle/bb189e7f309a17b4ef0e.js",
    "/static/bundle/044edcc7261708529ee7.js",
    "/static/bundle/d1e25565f07107bfb007.js",
    "/static/bundle/cf4aeaee22c19337768b.js",
]:
    try:
        js = s.get(f"{app.VJUDGE_BASE}{u}", timeout=20).text
    except Exception as e:
        print(u, "EXC", e)
        continue
    for m in re.finditer(r'setCfg\(', js):
        i = m.start()
        print(f"\n### {u} setCfg ctx:")
        print("   ", js[max(0, i-300):i+200].replace("\n", " ")[:500])
