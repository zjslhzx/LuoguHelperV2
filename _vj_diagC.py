# -*- coding: utf-8 -*-
"""Diagnostic C: compare navbar valid vs anon; find real auth endpoints."""
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


def navbar(txt):
    # capture the <nav> ... </nav> block
    m = re.search(r'<nav[^>]*>.*?</nav>', txt, re.S)
    if not m:
        return "(no nav found)"
    seg = m.group(0)
    return re.sub(r'\s+', ' ', seg)


v = navbar(mk(COOKIE).get("https://vjudge.net/", timeout=20).text)
a = navbar(requests.get("https://vjudge.net/", timeout=20,
                        headers={"User-Agent": UA}).text)
print("=== VALID nav (len %d) ===" % len(v))
print(v[:1200])
print("=== ANON nav (len %d) ===" % len(a))
print(a[:1200])

print()
print("=== ajax/auth endpoints referenced in valid homepage ===")
txt = mk(COOKIE).get("https://vjudge.net/", timeout=20).text
for m in re.finditer(r'["\'](/[a-zA-Z0-9_/.-]+)["\']', txt):
    u = m.group(1)
    if any(k in u.lower() for k in ["user", "auth", "login", "logout", "info"]):
        print("  ref:", u)
