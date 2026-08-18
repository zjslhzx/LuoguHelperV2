# -*- coding: utf-8 -*-
"""Temporary diagnostic: extract 洛谷 languages from Vjudge OJ registry."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
s = app._build_vjudge_session(COOKIE)

# From diagAB: bundle 1ab4f2a25ddef0442d12.js calls T.getOjs().
# getOjs() likely defined in the same bundle or a shared bundle.
for u in [
    "/static/bundle/1ab4f2a25ddef0442d12.js",
    "/static/bundle/bb189e7f309a17b4ef0e.js",
    "/static/bundle/2c09ce8bf02f69bc0aed.js",
]:
    try:
        js = s.get(f"{app.VJUDGE_BASE}{u}", timeout=20).text
    except Exception as e:
        print(u, "EXC", e)
        continue
    print(f"\n### {u}  len={len(js)}")
    # find getOjs definition
    for m in re.finditer(r'getOjs\s*[:=(]', js):
        i = m.start()
        print("  getOjs ctx:", js[max(0, i-80):i+200].replace("\n", " ")[:300])
    # find 洛谷 literal
    idx = js.find("洛谷")
    while idx >= 0:
        print("  洛谷 ctx:", js[max(0, idx-150):idx+450].replace("\n", " ")[:600])
        idx = js.find("洛谷", idx + 1)
        if idx > 3000000:
            break
