# -*- coding: utf-8 -*-
"""Diagnostic: find correct Vjudge Luogu problem URL / submission flow."""
import sys
import re
import requests

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
COOKIE = "D3F7DE4C41282F82103BAEE94F9C28EF"


def mk(cookie):
    s = requests.Session()
    s.headers.update({"User-Agent": UA,
                      "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8"})
    if cookie:
        s.cookies.set("JSESSIONID", cookie, domain=".vjudge.net", path="/")
    return s


s = mk(COOKIE)

# 1) Try the problem search page (GET) to find how the API is invoked
print("=== GET /problem/search (page) ===")
r = s.get("https://vjudge.net/problem/search", timeout=20)
print("status:", r.status_code, "url:", r.url, "len:", len(r.text))
# find ajax url used by the page
for m in re.finditer(r'(url|ajax)\s*[:=]\s*["\']([^"\']+)["\']', r.text):
    print("  ref:", m.group(2))
for m in re.finditer(r'(/problem/[a-zA-Z0-9_/.-]+)', r.text):
    pass

# 2) Try common search API variants
print("=== search API variants ===")
variants = [
    ("post", "https://vjudge.net/problem/search",
     {"action": "search", "draw": 1, "start": 0, "length": 20,
      "OJId": "Luogu", "probNum": "P1000"}),
    ("get", "https://vjudge.net/problem/search",
     {"action": "search", "draw": 1, "start": 0, "length": 20,
      "OJId": "Luogu", "probNum": "P1000"}),
    ("post", "https://vjudge.net/problem/search",
     {"action": "search", "draw": 1, "start": 0, "length": 20,
      "OJId": "Luogu", "probNum": "P1000", "title": "", "source": ""}),
]
for method, url, data in variants:
    try:
        rr = s.request(method, url, data=data, timeout=15,
                       headers={"X-Requested-With": "XMLHttpRequest",
                                "Referer": "https://vjudge.net/problem/search"})
        ct = rr.headers.get("Content-Type", "")
        snippet = rr.text[:300].replace("\n", " ")
        print(f"{method.upper()} {rr.status_code} ct={ct} :: {snippet}")
    except Exception as e:
        print(f"{method.upper()} ERR {e}")
