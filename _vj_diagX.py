# -*- coding: utf-8 -*-
"""Temporary diagnostic: inspect problem dataJson language fields + find lang API."""
import re
import json
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"

s = app._build_vjudge_session(COOKIE)
page = s.get(f"{app.VJUDGE_BASE}/problem/{app._build_vj_pid(PID)}", timeout=20).text

m = re.search(r'name="dataJson"[^>]*>\s*([^<]+)', page) or \
    re.search(r'name="dataJson"\s+value="([^"]*)"', page)
raw = m.group(1).replace("\\u0022", '"').replace("\\u0027", "'").replace("\\/", "/")
data = json.loads(raw)
print("dataJson keys:", list(data.keys()))
for k in ["languages", "language", "submitMethods"]:
    v = data.get(k)
    if v is not None:
        print(f"\n{k} =", json.dumps(v, ensure_ascii=False)[:1500])

# Try known Vjudge language-list APIs
for url in [f"{app.VJUDGE_BASE}/problem/{app._build_vj_pid(PID)}/languages",
            f"{app.VJUDGE_BASE}/problem/languages?oj=洛谷",
            f"{app.VJUDGE_BASE}/user/languages?oj=洛谷"]:
    try:
        r = s.get(url, timeout=15)
        print("\nGET", url, "->", r.status_code,
              (r.text[:300].replace("\n", " ") if r.status_code == 200 else ""))
    except Exception as e:
        print("\nGET", url, "EXC", e)
