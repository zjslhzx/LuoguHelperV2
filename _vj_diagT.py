# -*- coding: utf-8 -*-
"""Temporary diagnostic: find remote-account load + status URL in bundle."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
BUNDLE = "/static/bundle/1ab4f2a25ddef0442d12.js"

s = app._build_vjudge_session(COOKIE)
js = s.get(f"{app.VJUDGE_BASE}{BUNDLE}", timeout=20).text

for kw in ["submit-remote-account", "remoteAccounts", "bindingId",
           "showModal", "runId", "/status", "remote_accounts"]:
    print(f"\n=== '{kw}' ===")
    for m in list(re.finditer(re.escape(kw), js))[:2]:
        a = max(0, m.start() - 200)
        b = min(len(js), m.end() + 300)
        print("   ...", js[a:b].replace("\n", " ")[:520])
