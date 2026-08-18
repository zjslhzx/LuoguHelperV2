# -*- coding: utf-8 -*-
"""Temporary verification: confirm P1001 submits to Vjudge using 洛谷 OJ id."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"

# 1) Problem page fetch via the real code paths.
vj_pid = app._build_vj_pid(PID)
print("vj_pid =", vj_pid)
s = app._build_vjudge_session(COOKIE)
print("authenticated =", app._vjudge_session_is_authenticated(s))
r = s.get(f"{app.VJUDGE_BASE}/problem/{vj_pid}", timeout=20)
m = re.search(r'"problemId"\s*:\s*(\d+)', r.text)
print("problem page:", r.status_code, "problemId =", m.group(1) if m else None)

# 2) End-to-end submit via Api (A+B program for P1001).
api = app.Api()
code = (
    "#include <iostream>\n"
    "int main(){ long long a,b; std::cin>>a>>b; std::cout<<a+b; return 0; }\n"
)
res = api.submit_vjudge(PID, code, 14, COOKIE)
print("submit result:", res)
