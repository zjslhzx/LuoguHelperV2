# -*- coding: utf-8 -*-
"""Verify: does fetching captcha CONSUME the CSRF token, requiring a re-fetch?

Hypothesis: the captcha endpoint /api/verify/captcha invalidates the current
csrf-token cookie. After fetching the captcha, we need to visit the problem
page AGAIN to get a fresh CSRF token before submitting.
"""
import json
import os
import re
import sys
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
        print("NO COOKIE"); sys.exit(2)

    pid = "P1000"
    session = app.build_luogu_session(cookie)

    # 1. Visit problem page -> get CSRF
    page = session.get(f"{BASE}/problem/{pid}", timeout=15)
    check("problem page 200", page.status_code == 200)

    csrf1 = None
    for c in session.cookies:
        if c.name == "csrf-token":
            csrf1 = c.value
            break
    check("csrf after page visit", bool(csrf1), str(csrf1)[:30])

    # 2. Fetch captcha
    cap = session.get(f"{BASE}/api/verify/captcha", timeout=15)
    check("captcha 200", cap.status_code == 200)

    # Check csrf-token cookie after captcha
    csrf2 = None
    for c in session.cookies:
        if c.name == "csrf-token":
            csrf2 = c.value
            break
    check("csrf after captcha", csrf2 is not None,
          f"csrf2={'None' if csrf2 is None else str(csrf2)[:30]}")
    if csrf2 is None:
        print("  *** CSRF CONSUMED by captcha fetch! ***")

    # 3. Visit problem page AGAIN -> get fresh CSRF
    page2 = session.get(f"{BASE}/problem/{pid}", timeout=15)
    check("page2 200", page2.status_code == 200)

    csrf3 = None
    for c in session.cookies:
        if c.name == "csrf-token":
            csrf3 = c.value
            break
    check("csrf after re-visit", bool(csrf3), str(csrf3)[:30] if csrf3 else "None")
    check("csrf3 same as csrf1", csrf3 == csrf1,
          f"csrf1={str(csrf1)[:30] if csrf1 else 'None'} csrf3={str(csrf3)[:30] if csrf3 else 'None'}")

    # 4. Visit problem page first, then captcha, then page again, then submit
    session2 = app.build_luogu_session(cookie)
    page_a = session2.get(f"{BASE}/problem/{pid}", timeout=15)
    cap_a = session2.get(f"{BASE}/api/verify/captcha", timeout=15)
    page_b = session2.get(f"{BASE}/problem/{pid}", timeout=15)

    csrf_final = None
    for c in session2.cookies:
        if c.name == "csrf-token":
            csrf_final = c.value
            break
    if not csrf_final:
        m = re.search(r'<meta name="csrf-token" content="([^"]+)"', page_b.text)
        if m:
            csrf_final = m.group(1)
    check("csrf after page->captcha->page", bool(csrf_final), str(csrf_final)[:30] if csrf_final else "None")

    # Submit with this CSRF and a WRONG verify (should get captcha error, not CSRF error)
    code = '#include<bits/stdc++.h>\nint main(){return 0;}'
    headers = {
        "x-csrf-token": csrf_final or "",
        "Content-Type": "application/json",
        "Referer": f"{BASE}/problem/{pid}",
        "Origin": BASE,
    }
    body = {"code": code, "lang": 12, "enableO2": 0, "verify": "WRONG"}
    r = session2.post(f"{BASE}/fe/api/problem/submit/{pid}", json=body,
                      headers=headers, timeout=30)
    try:
        rdata = r.json()
        err_type = rdata.get("errorType", "")
        print(f"  submit (page->captcha->page) HTTP {r.status_code}, errType={err_type}")
        is_captcha_err = "InvalidCaptcha" in err_type
        is_csrf_err = "InvalidCSRF" in err_type
        check("captcha error (not CSRF error)", is_captcha_err,
              f"got {err_type}")
    except Exception:
        print(f"  submit raw: {r.text[:300]}")

    # 5. Alternative: fetch CSRF from meta tag AFTER captcha (not from cookie)
    session3 = app.build_luogu_session(cookie)
    page3a = session3.get(f"{BASE}/problem/{pid}", timeout=15)
    cap3 = session3.get(f"{BASE}/api/verify/captcha", timeout=15)
    # Get CSRF from meta tag only (not cookie)
    csrf_meta = None
    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', page3a.text)
    if m:
        csrf_meta = m.group(1)
    check("csrf from meta tag", bool(csrf_meta))

    # Check if current page session has a fresh csrf cookie
    # Actually, after captcha, cookie is gone. But we have the page3a response.
    # The meta tag is from before captcha fetch. Let's visit page again.
    page3b = session3.get(f"{BASE}/problem/{pid}", timeout=15)
    csrf_after = None
    for c in session3.cookies:
        if c.name == "csrf-token":
            csrf_after = c.value
            break
    if not csrf_after:
        m2 = re.search(r'<meta name="csrf-token" content="([^"]+)"', page3b.text)
        if m2:
            csrf_after = m2.group(1)
    check("csrf after re-visit (test 5)", bool(csrf_after))

    print(f"\n{'=' * 40}")
    print(f"PASS: {PASS}  FAIL: {FAIL}")


if __name__ == "__main__":
    main()