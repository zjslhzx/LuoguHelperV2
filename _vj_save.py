# -*- coding: utf-8 -*-
"""Temporary diagnostic: save page + config bundle for local inspection."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
s = app._build_vjudge_session(COOKIE)
page = s.get(f"{app.VJUDGE_BASE}/problem/{app._build_vj_pid('P1001')}", timeout=20).text
open("_vj_page.html", "w", encoding="utf-8").write(page)

for u in ["/static/bundle/bb189e7f309a17b4ef0e.js",
          "/static/bundle/1ab4f2a25ddef0442d12.js"]:
    js = s.get(f"{app.VJUDGE_BASE}{u}", timeout=25).text
    fn = "_vj_" + u.rsplit("/", 1)[1]
    open(fn, "w", encoding="utf-8").write(js)
    print("saved", fn, len(js))
print("page saved", len(page))
