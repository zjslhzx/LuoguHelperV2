# -*- coding: utf-8 -*-
"""Temporary diagnostic: inspect the Vjudge submit POST response in detail."""
import re
import base64
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"

vj_pid = app._build_vj_pid(PID)
s = app._build_vjudge_session(COOKIE)
r = s.get(f"{app.VJUDGE_BASE}/problem/{vj_pid}", timeout=20)
print("problem page:", r.status_code, "url:", r.url)
html = r.text

num_id = None
for pat in [r'id="problemId"[^>]*value="(\d+)"',
            r'name="problemId"[^>]*value="(\d+)"',
            r'"problemId"\s*:\s*(\d+)',
            r'data-problem-id="(\d+)"']:
    m = re.search(pat, html)
    if m:
        num_id = m.group(1)
        break
csrf_val = None
for pat in [r'name="csrf-token"[^>]*content="([^"]+)"',
            r'"csrfToken"\s*:\s*"([^"]+)"',
            r'name="X-CSRF-Token"[^>]*content="([^"]+)"']:
    m = re.search(pat, html)
    if m:
        csrf_val = m.group(1)
        break
print("num_id =", num_id, " csrf_val =", csrf_val)
print("has _csrf in page:", bool(re.search(r'_csrf|csrf', html, re.I)))

code = "#include <iostream>\nint main(){ long long a,b; std::cin>>a>>b; std::cout<<a+b; return 0; }\n"
source_b64 = base64.b64encode(code.encode("utf-8")).decode("ascii")

submit_data = {
    "problemId": str(num_id),
    "language": "0",
    "source": source_b64,
}
submit_headers = {
    "Referer": f"{app.VJUDGE_BASE}/problem/{vj_pid}",
    "Content-Type": "application/x-www-form-urlencoded",
}
if csrf_val:
    submit_headers["X-CSRF-Token"] = csrf_val

try:
    resp = s.post(f"{app.VJUDGE_BASE}/problem/submit",
                  data=submit_data, headers=submit_headers, timeout=30,
                  allow_redirects=False)
    print("submit POST ->", resp.status_code)
    print("  headers:", dict(resp.headers))
    print("  body[:600]:", resp.text[:600].replace("\n", " "))
except Exception as e:
    print("submit exception:", e)

# Also try without custom headers (fresh session) to compare.
s2 = app._build_vjudge_session(COOKIE)
try:
    resp2 = s2.post(f"{app.VJUDGE_BASE}/problem/submit",
                    data=submit_data, timeout=30, allow_redirects=False)
    print("plain POST ->", resp2.status_code)
    print("  body[:600]:", resp2.text[:600].replace("\n", " "))
except Exception as e:
    print("plain submit exception:", e)
