# -*- coding: utf-8 -*-
"""Diagnostic G: definitive auth-state signals on same-run comparison."""
import sys
import re
import requests

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TOKEN = "D3F7DE4C41282F82103BAEE94F9C28EF"


def mk(cookie):
    s = requests.Session()
    s.headers.update({"User-Agent": UA,
                      "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8"})
    if cookie:
        for name in ("JSESSIONID", "JSESSlONID"):
            s.cookies.set(name, cookie, domain=".vjudge.net", path="/")
    return s


for label, ck in [("ANON  ", None), ("BAD   ", "0"*32), ("USER  ", TOKEN)]:
    s = mk(ck)
    print(f"--- {label} ---")
    for url in ["https://vjudge.net/user/profile",
                "https://vjudge.net/problem/Luogu-P1000"]:
        r = s.get(url, timeout=20)
        redir = "->login" if "login=" in r.url else ""
        txt = r.text
        # extract page title + any login/logout/username markers
        title = re.search(r"<title>(.*?)</title>", txt, re.S)
        print(f"  {url.rsplit('/', 1)[-1]}: {r.status_code}{redir} "
              f"len={len(txt)} title={title.group(1).strip() if title else ''}")
        for kw in ["login", "logout", "Login", "Logout", "Sign in"]:
            if kw in txt:
                idx = txt.find(kw)
                print(f"     [{kw}] ...{re.sub(chr(92)+'s+', ' ', txt[max(0,idx-60):idx+60])}...")
                break
