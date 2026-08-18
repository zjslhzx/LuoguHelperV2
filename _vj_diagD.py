# -*- coding: utf-8 -*-
"""Diagnostic D: understand current Vjudge auth mechanism."""
import sys
import re
import requests

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
COOKIE = "D3F7DE4C41282F82103BAEE94F9C28EF"

# 1) Login page: what cookies are used? any hidden fields?
print("=== /login page ===")
s = requests.Session()
s.headers.update({"User-Agent": UA})
r = s.get("https://vjudge.net/login", timeout=20)
print("status:", r.status_code, "url:", r.url)
print("cookies in jar:", dict(s.cookies))
for m in re.finditer(r'<input[^>]*name="([^"]+)"[^>]*>', r.text):
    print("  input name:", m.group(1))
for m in re.finditer(r'(csrf|token|action)[^>]{0,120}', r.text, re.I):
    pass

# 2) Try /user/check or current user endpoints
print("=== current-user endpoints ===")
for url in ["https://vjudge.net/user/info",
            "https://vjudge.net/api/user",
            "https://vjudge.net/user/checkLogin",
            "https://vjudge.net/user/login/state",
            "https://vjudge.net/session"]:
    try:
        rr = s.get(url, timeout=10)
        print(url, "->", rr.status_code, rr.url, "len:", len(rr.text),
              "ct:", rr.headers.get("Content-Type", ""))
    except Exception as e:
        print(url, "-> ERR", e)

# 3) Check what Vjudge sets in Set-Cookie on a normal GET (homepage)
print("=== Set-Cookie on homepage ===")
r = requests.get("https://vjudge.net/", timeout=20, headers={"User-Agent": UA})
for h in r.raw.headers.items():
    if h[0].lower() == "set-cookie":
        print("  set-cookie:", h[1])

# 4) Look at how frontend renders user dropdown (find JS template vars)
print("=== user dropdown template markers in homepage ===")
txt = requests.get("https://vjudge.net/", timeout=20,
                   headers={"User-Agent": UA}).text
for kw in ["currentUser", "window.user", "userInfo", "top.nav.logout",
           "isLogin", "loggedIn", "user={", "avatarUrl"]:
    print(f"  has '{kw}':", kw in txt)
# find the script that fills nav user area
for m in re.finditer(r'(user\w*\s*[:=]\s*\{[^}]{0,200}\})', txt):
    print("  found:", m.group(1)[:200].replace("\n", " "))
