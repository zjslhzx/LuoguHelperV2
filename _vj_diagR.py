# -*- coding: utf-8 -*-
"""Temporary diagnostic: inspect /user/remoteAccounts page binding list."""
import re
import json
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"

s = app._build_vjudge_session(COOKIE)
ra = s.get(f"{app.VJUDGE_BASE}/user/remoteAccounts", timeout=20)
html = ra.text
print("status:", ra.status_code, "len:", len(html))

# Find dataJson-like hidden fields
for m in re.finditer(r'<textarea[^>]*name="dataJson"[^>]*>(.*?)</textarea>', html, re.S):
    print("\ndataJson textarea:", m.group(1)[:800])
for m in re.finditer(r'<input[^>]*name="dataJson"[^>]*>', html):
    print("\ndataJson input:", m.group(0)[:300])

# Look for bindings / accounts keywords
for kw in ["bindingId", "bindings", "remoteAccounts", "洛谷", "isBinding", "accountId", "id:"]:
    hits = [h for h in [m.start() for m in re.finditer(re.escape(kw), html)]]
    print(f"\n=== '{kw}' -> {len(hits)} hits ===")
    for h in hits[:2]:
        print("   ...", html[max(0, h-120):h+220].replace("\n", " ")[:340])
