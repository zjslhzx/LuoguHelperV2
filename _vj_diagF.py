# -*- coding: utf-8 -*-
"""Diagnostic F: cookie delivery variations + login page fields."""
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TOKEN = "D3F7DE4C41282F82103BAEE94F9C28EF"
TARGET = "https://vjudge.net/problem/Luogu-P1000"


def base():
    s = requests.Session()
    s.headers.update({"User-Agent": UA,
                      "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8"})
    return s


def probe(label, s):
    r = s.get(TARGET, timeout=20)
    tag = "->login" if "login=" in r.url else ""
    print(f"{label:42s} {r.status_code} {r.url.rsplit('/', 1)[-1]}{tag}")


# header injection variants
for name in ["JSESSIONID", "JSESSlONID"]:
    s = base()
    s.headers["Cookie"] = f"{name}={TOKEN}"
    probe(f"Header Cookie {name}", s)

# cookie jar domain variants (no leading dot)
for d in ["vjudge.net", ".vjudge.net"]:
    for name in ["JSESSIONID", "JSESSlONID"]:
        s = base()
        s.cookies.set(name, TOKEN, domain=d, path="/")
        probe(f"jar {name} domain={d}", s)

# full browser-like cookie line: both names
s = base()
s.headers["Cookie"] = f"JSESSIONID={TOKEN}; JSESSlONID={TOKEN}"
probe("Header both", s)

# check /login page structure (current form fields)
print("=== login page ===")
s = base()
r = s.get("https://vjudge.net/login", timeout=20)
print("status:", r.status_code, "url:", r.url)
