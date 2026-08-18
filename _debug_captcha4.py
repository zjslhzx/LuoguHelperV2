# -*- coding: utf-8 -*-
"""Deep diagnostic: test the EXACT captcha flow used by the app.

Hypothesis: the captcha endpoint returns a valid captcha, but the CSRF token
extracted from the problem page is stale by the time the submit happens.
The captcha endpoint might set a new CSRF token that should be used instead.
"""
import json
import os
import re
import sys
import uuid

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import app
except Exception as e:
    print("FAIL import app:", e)
    sys.exit(1)

BASE = app.LUOGU_BASE
PASS = 0
FAIL = 0


def check(label, cond, detail=""):
    global PASS, FAIL
    if cond:
        print(f"  PASS: {label}")
        PASS += 1
    else:
        print(f"  FAIL: {label}  {detail}")
        FAIL += 1


def main():
    cfg = app.load_config()
    cookie = cfg.get("cookie", "").strip()
    print(f"cookie len={len(cookie)}")

    if not cookie:
        print("NO COOKIE")
        sys.exit(2)

    pid = "P1000"
    code = '#include<bits/stdc++.h>\nusing namespace std;int main(){return 0;}'
    lang = 12

    # --- Test 1: CSRF from problem page vs after captcha fetch ---
    session = app.build_luogu_session(cookie)
    page = session.get(f"{BASE}/problem/{pid}", timeout=15)
    check("problem page 200", page.status_code == 200, str(page.status_code))

    csrf_from_page = None
    for c in session.cookies:
        if c.name == "csrf-token":
            csrf_from_page = c.value
            break
    if not csrf_from_page:
        m = re.search(r'<meta name="csrf-token" content="([^"]+)"', page.text)
        if m:
            csrf_from_page = m.group(1)
    check("csrf from page exists", bool(csrf_from_page))

    # Fetch captcha with the same session
    cap = session.get(f"{BASE}/api/verify/captcha", timeout=15)
    check("captcha 200", cap.status_code == 200, str(cap.status_code))
    check("captcha is jpeg", "image" in (cap.headers.get("Content-Type", "") or ""),
          cap.headers.get("Content-Type", ""))

    # Check if CSRF token changed after captcha fetch
    csrf_after_captcha = None
    for c in session.cookies:
        if c.name == "csrf-token":
            csrf_after_captcha = c.value
            break
    csrf_same = csrf_from_page == csrf_after_captcha
    check("csrf unchanged after captcha fetch", csrf_same,
          f"before={csrf_from_page} after={csrf_after_captcha}")

    # --- Test 2: Submit with the REAL captcha session ---
    # The captcha is an image; we can't read it. But we can test the submission
    # with a WRONG verify value to see if the endpoint is reachable and the
    # session is correct.
    check("csrf_to_use", bool(csrf_from_page))

    # Simulate the exact flow: fetch_captcha -> Api.get_captcha -> submit
    body = {"code": code, "lang": lang, "enableO2": 0, "verify": "WRONG"}
    headers = {
        "x-csrf-token": csrf_from_page or "",
        "Content-Type": "application/json",
        "Referer": f"{BASE}/problem/{pid}",
        "Origin": BASE,
    }
    r = session.post(f"{BASE}/fe/api/problem/submit/{pid}", json=body,
                     headers=headers, timeout=30)
    check("captcha-session submit reachable", r.status_code in (200, 403),
          f"HTTP {r.status_code}")
    try:
        rdata = r.json()
        print(f"  submit response: {json.dumps(rdata, ensure_ascii=False)[:300]}")
    except Exception:
        print(f"  submit raw: {r.text[:300]}")

    # --- Test 3: Check if the captcha endpoint sets a new CSRF cookie ---
    session2 = app.build_luogu_session(cookie)
    page2 = session2.get(f"{BASE}/problem/{pid}", timeout=15)
    csrf2_before = None
    for c in session2.cookies:
        if c.name == "csrf-token":
            csrf2_before = c.value
            break
    cap2 = session2.get(f"{BASE}/api/verify/captcha", timeout=15)
    csrf2_after = None
    for c in session2.cookies:
        if c.name == "csrf-token":
            csrf2_after = c.value
            break
    check("csrf cookies before/after captcha (2nd test)",
          csrf2_before == csrf2_after,
          f"before={csrf2_before} after={csrf2_after}")

    # --- Test 4: Can we submit with csrf token from AFTER captcha fetch? ---
    headers2 = dict(headers)
    headers2["x-csrf-token"] = csrf2_after or ""
    body2 = dict(body)
    body2["verify"] = "WRONG2"
    r2 = session2.post(f"{BASE}/fe/api/problem/submit/{pid}", json=body2,
                       headers=headers2, timeout=30)
    check("submit with after-captcha csrf", r2.status_code in (200, 403),
          f"HTTP {r2.status_code}")
    try:
        r2data = r2.json()
        print(f"  submit2 response: {json.dumps(r2data, ensure_ascii=False)[:300]}")
    except Exception:
        print(f"  submit2 raw: {r2.text[:300]}")

    # --- Summary ---
    print(f"\n{'=' * 40}")
    print(f"PASS: {PASS}  FAIL: {FAIL}")

    # Key insight: check the response type
    if r.status_code == 403:
        err_type = r.json().get("errorType", "")
        if "InvalidCaptchaException" in err_type:
            print("\nCONCLUSION: Backend sends captcha, submission fails with 'captcha error'")
            print("The captcha IS being sent and validated, but the value is wrong.")
            print("This is EXPECTED since we used a wrong verify value.")
        elif "InvalidCSRFTokenException" in err_type:
            print("\nCONCLUSION: CSRF token is the issue!")
        else:
            print(f"\nCONCLUSION: Unknown error type: {err_type}")


if __name__ == "__main__":
    main()