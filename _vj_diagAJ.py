# -*- coding: utf-8 -*-
"""Temporary diagnostic: submit P1001 with correct Luogu-origin language id."""
import json
import base64
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"

vj_pid = app._build_vj_pid(PID)
s = app._build_vjudge_session(COOKIE)

# 1) bindingId for 洛谷
rj = s.get(f"{app.VJUDGE_BASE}/user/remoteAccounts/list",
           params={"oj": "洛谷"}, timeout=20).json()
bindings = ((rj.get("groups") or {}).get("洛谷") or {}).get("bindings") or []
ready = [b for b in bindings if b.get("runtimeStatus") == "READY"]
print("ready bindings:", [(b.get("id"), b.get("accountId")) for b in ready])
binding_id = ready[0]["id"] if ready else None

code = "#include <iostream>\nint main(){ long long a,b; std::cin>>a>>b; std::cout<<a+b; return 0; }\n"
base_headers = {
    "Referer": f"{app.VJUDGE_BASE}/problem/{vj_pid}",
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Requested-With": "XMLHttpRequest",
}
endpoint = f"{app.VJUDGE_BASE}/problem/submit/{vj_pid}"

# Try method=1 with C++17 language id 12, and variants
for name, payload in [
    ("method1 lang12", {"method": "1", "language": "12", "open": "0",
                        "source": code, "token": "", "bindingId": str(binding_id)}),
    ("method1 lang12-o2", {"method": "1", "language": "12-o2", "open": "0",
                           "source": code, "token": "", "bindingId": str(binding_id)}),
    ("method2 lang12", {"method": "2", "language": "12", "open": "0",
                        "source": code, "token": ""}),
]:
    try:
        r = s.post(endpoint, data=payload, headers=base_headers,
                   timeout=30, allow_redirects=False)
        print(f"\n--- {name}: HTTP {r.status_code} ct={r.headers.get('Content-Type','')} ---")
        print("  headers:", dict(list(r.headers.items())[:4]))
        print("  body[:400]:", r.text[:400].replace("\n", " "))
        try:
            j = r.json()
            print("  json:", json.dumps(j, ensure_ascii=False)[:400])
        except Exception:
            pass
    except Exception as e:
        print(f"\n--- {name}: EXC {e} ---")
