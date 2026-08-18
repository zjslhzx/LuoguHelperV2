# -*- coding: utf-8 -*-
"""Temporary diagnostic: full end-to-end submit test with bindingId."""
import json
import base64
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"

vj_pid = app._build_vj_pid(PID)
s = app._build_vjudge_session(COOKIE)

# 1) get bindingId
rj = s.get(f"{app.VJUDGE_BASE}/user/remoteAccounts/list",
           params={"oj": "洛谷"}, timeout=20).json()
bindings = ((rj.get("groups") or {}).get("洛谷") or {}).get("bindings") or []
ready = [b for b in bindings if b.get("runtimeStatus") == "READY"]
print("ready bindings:", [(b.get("id"), b.get("accountId")) for b in ready])
binding_id = ready[0]["id"] if ready else None

code = "#include <iostream>\nint main(){ long long a,b; std::cin>>a>>b; std::cout<<a+b; return 0; } // vjtest\n"
base_headers = {
    "Referer": f"{app.VJUDGE_BASE}/problem/{vj_pid}",
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Requested-With": "XMLHttpRequest",
}
endpoint = f"{app.VJUDGE_BASE}/problem/submit/{vj_pid}"

for name, source_val in [("RAW", code)]:
    payload = {
        "method": "1",
        "language": "12",  # C++17 (matches Luogu's language id on Vjudge)
        "open": "0",
        "source": source_val,
        "token": "",
        "bindingId": str(binding_id),
    }
    try:
        r = s.post(endpoint, data=payload, headers=base_headers,
                   timeout=30, allow_redirects=False)
        print(f"\n--- {name}: HTTP {r.status_code} ct={r.headers.get('Content-Type','')} ---")
        print("  body[:400]:", r.text[:400].replace("\n", " "))
    except Exception as e:
        print(f"\n--- {name}: EXC {e} ---")
