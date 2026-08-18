# -*- coding: utf-8 -*-
"""Temporary diagnostic: probe new Vjudge submit endpoint behavior."""
import re
import json
import base64
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"

vj_pid = app._build_vj_pid(PID)
s = app._build_vjudge_session(COOKIE)
page = s.get(f"{app.VJUDGE_BASE}/problem/{vj_pid}", timeout=20).text

# Extract dataJson (hidden field with problem config)
m = re.search(r'name="dataJson"[^>]*>\s*([^<]+)', page) or \
    re.search(r'name="dataJson"\s+value="([^"]*)"', page)
data = None
if m:
    raw = m.group(1).replace("\\u0022", '"').replace("\\u0027", "'").replace("\\/", "/")
    try:
        data = json.loads(raw)
    except Exception as e:
        print("dataJson parse failed:", e, "raw[:200]=", raw[:200])
print("dataJson oj/prob/problemId/submitMethods:",
      (data or {}).get("oj"), (data or {}).get("prob"),
      (data or {}).get("problemId"), (data or {}).get("submitMethods"))

code = "#include <iostream>\nint main(){ long long a,b; std::cin>>a>>b; std::cout<<a+b; return 0; }\n"
src_b64 = base64.b64encode(code.encode()).decode()
base_headers = {
    "Referer": f"{app.VJUDGE_BASE}/problem/{vj_pid}",
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Requested-With": "XMLHttpRequest",
}
endpoint = f"{app.VJUDGE_BASE}/problem/submit/{vj_pid}"

variants = [
    ("old-style b64", {"problemId": "4026406", "language": "0", "source": src_b64}),
    ("new method0 raw", {"method": "0", "language": "0", "open": "0",
                         "source": code, "token": ""}),
    ("new method1 raw", {"method": "1", "language": "0", "open": "0",
                         "source": code, "token": ""}),
]

for name, payload in variants:
    try:
        r = s.post(endpoint, data=payload, headers=base_headers,
                   timeout=30, allow_redirects=False)
        body = r.text
        print(f"\n--- {name}: HTTP {r.status_code} ---")
        print("  headers:", dict(list(r.headers.items())[:4]))
        print("  body[:400]:", body[:400].replace("\n", " "))
    except Exception as e:
        print(f"\n--- {name}: EXC {e} ---")

# Check user's remote accounts for 洛谷
print("\n=== remoteAccounts?oj=洛谷 ===")
try:
    ra = s.get(f"{app.VJUDGE_BASE}/user/remoteAccounts?oj={app._build_vj_pid('') or ''}", timeout=20)
    print("  status:", ra.status_code)
    m2 = re.search(r'name="dataJson"[^>]*>\s*([^<]+)', ra.text) or \
         re.search(r'name="dataJson"\s+value="([^"]*)"', ra.text)
    if m2:
        print("  dataJson[:500]:", m2.group(1)[:500])
    else:
        for kw in ["binding", "account", "洛谷"]:
            idx = ra.text.find(kw)
            if idx >= 0:
                print(f"  '{kw}' ctx:", ra.text[max(0, idx-100):idx+150].replace("\n", " "))
except Exception as e:
    print("  EXC:", e)
