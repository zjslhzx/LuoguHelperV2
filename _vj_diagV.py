# -*- coding: utf-8 -*-
"""Temporary diagnostic: dump full remoteAccounts/list JSON for 洛谷."""
import json
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"

s = app._build_vjudge_session(COOKIE)
r = s.get(f"{app.VJUDGE_BASE}/user/remoteAccounts/list",
          params={"oj": "洛谷"}, timeout=20)
j = r.json()
print(json.dumps(j, ensure_ascii=False, indent=1)[:2500])
