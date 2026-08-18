# -*- coding: utf-8 -*-
"""Temporary diagnostic: fetch /util/cfg to get remoteOJs with language map."""
import json
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
s = app._build_vjudge_session(COOKIE)
r = s.get(f"{app.VJUDGE_BASE}/util/cfg", timeout=20)
print("status:", r.status_code)
if r.status_code == 200:
    cfg = r.json()
    ojs = cfg.get("remoteOJs", {})
    luogu = ojs.get("洛谷", {})
    print("洛谷 keys:", list(luogu.keys()))
    langs = luogu.get("languages", {})
    print("languages:", json.dumps(langs, ensure_ascii=False, indent=2))
    print("\n--- full 洛谷 entry ---")
    print(json.dumps(luogu, ensure_ascii=False, indent=2)[:2000])