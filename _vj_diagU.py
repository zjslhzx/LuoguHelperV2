# -*- coding: utf-8 -*-
"""Temporary diagnostic: check /user/remoteAccounts/list JSON for 洛谷."""
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"

s = app._build_vjudge_session(COOKIE)
r = s.get(f"{app.VJUDGE_BASE}/user/remoteAccounts/list",
          params={"oj": "洛谷"}, timeout=20)
print("status:", r.status_code, "ct:", r.headers.get("Content-Type", ""))
try:
    j = r.json()
    print("keys:", list(j.keys()) if isinstance(j, dict) else type(j))
    print("bindings:", j.get("bindings") if isinstance(j, dict) else None)
except Exception as e:
    print("json err:", e, "body[:300]:", r.text[:300])
