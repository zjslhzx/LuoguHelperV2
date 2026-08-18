# -*- coding: utf-8 -*-
"""Live diagnostic: what does the CURRENT Luogu submit endpoint require?

Checks (using the real cookie from config.json, never printed):
  1. Direct POST /fe/api/problem/submit/{pid} with valid CSRF and NO verify field.
  2. Same POST but with a dummy 'verify' value.
  3. GET /api/verify/captcha -> content-type/size.
  4. Whether the response mentions interactive/slider/click captcha wording.
"""
import json
import os
import re
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import app
except Exception as e:  # noqa
    print("FAIL import app:", e)
    sys.exit(1)

BASE = app.LUOGU_BASE


def mask_cookie(c):
    if not c:
        return "<empty>"
    return c[:18] + "..." if len(c) > 21 else c


def main():
    cfg = app.load_config()
    cookie = cfg.get("cookie", "").strip()
    print("cookie:", mask_cookie(cookie), "len=", len(cookie))

    if not cookie:
        print("NO COOKIE - cannot test live")
        sys.exit(2)

    pid = "P1000"
    code = '#include<bits/stdc++.h>\nusing namespace std;int main(){return 0;}'
    lang = 12  # C++17

    session = app.build_luogu_session(cookie)

    # --- 1. fetch CSRF from problem page ---
    page = session.get(f"{BASE}/problem/{pid}", timeout=15)
    csrf = None
    for c in session.cookies:
        if c.name == "csrf-token":
            csrf = c.value
            break
    if not csrf:
        m = re.search(r'<meta name="csrf-token" content="([^"]+)"', page.text)
        if m:
            csrf = m.group(1)
    print("problem page HTTP", page.status_code, "csrf:", ("yes" if csrf else "NO"))

    headers = {
        "x-csrf-token": csrf or "",
        "Content-Type": "application/json",
        "Referer": f"{BASE}/problem/{pid}",
        "Origin": BASE,
    }

    # --- 2. DIRECT submit (no verify) ---
    body = {"code": code, "lang": lang, "enableO2": 0, "verify": ""}
    try:
        r = session.post(f"{BASE}/fe/api/problem/submit/{pid}", json=body,
                         headers=headers, timeout=30)
    except requests.RequestException as e:
        print("direct submit EXC:", e)
        r = None
    if r is not None:
        print("DIRECT submit HTTP", r.status_code)
        try:
            data = r.json()
            print("DIRECT submit body:", json.dumps(data, ensure_ascii=False)[:400])
        except Exception:
            print("DIRECT submit raw:", r.text[:400])

    # --- 3. submit with dummy verify ---
    body2 = dict(body)
    body2["verify"] = "xxxx"
    try:
        r2 = session.post(f"{BASE}/fe/api/problem/submit/{pid}", json=body2,
                          headers=headers, timeout=30)
        print("DUMMYVERIFY submit HTTP", r2.status_code)
        try:
            print("DUMMYVERIFY body:", json.dumps(r2.json(), ensure_ascii=False)[:400])
        except Exception:
            print("DUMMYVERIFY raw:", r2.text[:400])
    except requests.RequestException as e:
        print("DUMMYVERIFY submit EXC:", e)

    # --- 4. captcha endpoint ---
    cap = session.get(f"{BASE}/api/verify/captcha", timeout=15)
    print("captcha HTTP", cap.status_code, "content-type:", cap.headers.get("Content-Type"),
          "bytes:", len(cap.content), "b64 head:", cap.content[:16].hex())


if __name__ == "__main__":
    main()
