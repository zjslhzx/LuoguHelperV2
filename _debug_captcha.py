# -*- coding: utf-8 -*-
"""Temporary diagnostic for Luogu captcha behavior (NOT part of the project)."""
import json
import re
import sys
import requests

LUOGU_BASE = "https://www.luogu.com.cn"
COOKIE = "__client_id=ykzm5xibcyegpy6vaksno7yi6cp5ak6pazlfu77s5wkhobhb;_uid=1076915"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def build_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    for part in COOKIE.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            k, v = part.split("=", 1)
            s.cookies.set(k, v, domain=".luogu.com.cn", path="/")
    return s


def main():
    s = build_session()
    # 1) Visit problem page, get csrf
    r = s.get(f"{LUOGU_BASE}/problem/P1000", timeout=20)
    print("== problem page ==", r.status_code, "len", len(r.text))
    csrf = None
    for c in s.cookies:
        if c.name == "csrf-token":
            csrf = c.value
    if not csrf:
        m = re.search(r'<meta name="csrf-token" content="([^"]+)"', r.text)
        if m:
            csrf = m.group(1)
    print("csrf (cookie):", csrf)

    # 2) Fetch captcha endpoint - inspect raw response
    r2 = s.get(f"{LUOGU_BASE}/api/verify/captcha", timeout=20)
    print("\n== captcha ==", r2.status_code, "CT:", r2.headers.get("Content-Type"),
          "len:", len(r2.content))
    print("head bytes:", r2.content[:300])
    try:
        j = r2.json()
        print("JSON body keys:", list(j.keys()) if isinstance(j, dict) else type(j))
        print("JSON body:", json.dumps(j, ensure_ascii=False)[:600])
    except Exception as e:
        print("not json:", e)

    # 3) Direct submit WITHOUT verify
    headers = {
        "x-csrf-token": csrf or "",
        "Content-Type": "application/json",
        "Referer": f"{LUOGU_BASE}/problem/P1000",
        "Origin": LUOGU_BASE,
    }
    body = {"code": "print(1)", "lang": 7, "enableO2": 0, "verify": ""}
    r3 = s.post(f"{LUOGU_BASE}/fe/api/problem/submit/P1000", json=body,
                headers=headers, timeout=30)
    print("\n== direct submit (no verify) ==", r3.status_code)
    print("body:", r3.text[:600])

    # 4) Submit WITH a bogus verify, reusing same session
    body["verify"] = "0000"
    r4 = s.post(f"{LUOGU_BASE}/fe/api/problem/submit/P1000", json=body,
                headers=headers, timeout=30)
    print("\n== submit with verify=0000 (same session) ==", r4.status_code)
    print("body:", r4.text[:600])


if __name__ == "__main__":
    main()
