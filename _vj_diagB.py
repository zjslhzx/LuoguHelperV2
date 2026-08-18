# -*- coding: utf-8 -*-
"""Diagnostic B: resolve auth confusion + Luogu origin existence."""
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


# --- Inspect homepage user markers with valid cookie ---
print("=== homepage user JS markers (valid cookie) ===")
s = mk(COOKIE)
r = s.get("https://vjudge.net/", timeout=20)
txt = r.text
for pat in [r"window\.user\s*=\s*([^;]+);", r"user\s*=\s*(\{.*?\})\s*;",
            r"var\s+\w*[Uu]ser\w*\s*=\s*([^;]+);"]:
    for m in re.finditer(pat, txt, re.S):
        seg = m.group(1).strip()
        print("PAT", pat, "=>", seg[:200].replace("\n", " "))
# find any JSON-ish assignments around 'username'
for m in re.finditer(r'"(username|userName|nickname|nickName)"\s*:\s*"([^"]+)"', txt):
    print("field:", m.group(1), "=", m.group(2))
# user dropdown area
for m in re.finditer(r'(top-nav-user-item.{0,400}?)</li>', txt, re.S):
    print("USERITEM:", m.group(1)[:300].replace("\n", " "))

# --- /problem/search redirect behavior across sessions ---
print("=== /problem/search redirect behavior ===")
for name, ck in [("anon", None), ("bad", "0"*32), ("valid", COOKIE)]:
    ss = mk(ck)
    rr = ss.get("https://vjudge.net/problem/search", timeout=20,
                allow_redirects=True)
    print(name, "->", rr.status_code, rr.url)

# --- Try to find a working Luogu problem URL ---
print("=== probe Luogu problem URLs (valid cookie) ===")
for url in ["https://vjudge.net/problem/Luogu-P1000",
            "https://vjudge.net/problem/Luogu-1000",
            "https://vjudge.net/problem/Luogu-P1000/description",
            "https://vjudge.net/problem/Luogu-P1425"]:
    rr = mk(COOKIE).get(url, timeout=15)
    print(url, "->", rr.status_code, rr.url)

# --- Vjudge origin list page ---
print("=== origin list ===")
rr = mk(COOKIE).get("https://vjudge.net/origin", timeout=15)
print("origin page:", rr.status_code, rr.url)
for m in re.finditer(r'value="(\w+)"[^>]*>([^<]{1,40})</option>', rr.text):
    print("  origin:", m.group(1), "=", m.group(2).strip())
