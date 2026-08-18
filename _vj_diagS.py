# -*- coding: utf-8 -*-
"""Temporary diagnostic: test old submit endpoint with various params."""
import base64
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"

vj_pid = app._build_vj_pid(PID)
s = app._build_vjudge_session(COOKIE)
code = "#include <iostream>\nint main(){ long long a,b; std::cin>>a>>b; std::cout<<a+b; return 0; }\n"
src_b64 = base64.b64encode(code.encode()).decode()

# Try old endpoint with AJAX header
r = s.post(
    f"{app.VJUDGE_BASE}/problem/submit",
    data={"problemId": "4026406", "language": "0", "source": src_b64},
    headers={"X-Requested-With": "XMLHttpRequest", "Content-Type": "application/x-www-form-urlencoded",
             "Referer": f"{app.VJUDGE_BASE}/problem/{vj_pid}"},
    timeout=30, allow_redirects=False
)
print("old endpoint AJAX:", r.status_code, r.text[:300].replace("\n"," "))

# Try old endpoint without AJAX header
r2 = s.post(
    f"{app.VJUDGE_BASE}/problem/submit",
    data={"problemId": "4026406", "language": "0", "source": src_b64},
    allow_redirects=False, timeout=30
)
print("old endpoint plain:", r2.status_code, r2.headers.get("Location",""))

# Try new endpoint with old payload
r3 = s.post(
    f"{app.VJUDGE_BASE}/problem/submit/{vj_pid}",
    data={"problemId": "4026406", "language": "0", "source": src_b64},
    headers={"X-Requested-With": "XMLHttpRequest", "Content-Type": "application/x-www-form-urlencoded",
             "Referer": f"{app.VJUDGE_BASE}/problem/{vj_pid}"},
    timeout=30, allow_redirects=False
)
print("new endpoint old payload:", r3.status_code, r3.text[:300].replace("\n"," "))