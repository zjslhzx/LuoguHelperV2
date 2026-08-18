# -*- coding: utf-8 -*-
"""Diagnostic E: test JSESSlONID (lowercase L) hypothesis."""
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TOKEN = "D3F7DE4C41282F82103BAEE94F9C28EF"


def mk(cookie_name, val):
    s = requests.Session()
    s.headers.update({"User-Agent": UA,
                      "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8"})
    if val:
        s.cookies.set(cookie_name, val, domain=".vjudge.net", path="/")
    return s


def probe(label, s):
    out = []
    for url in ["https://vjudge.net/",
                "https://vjudge.net/problem/search",
                "https://vjudge.net/problem/Luogu-P1000"]:
        r = s.get(url, timeout=20)
        redir = "->login" if "login=" in r.url else ""
        out.append(f"{url.rsplit('/', 1)[-1] or '/'} {r.status_code}{redir}")
    return label + ": " + " | ".join(out)


print(probe("JSESSIONID (old)     ", mk("JSESSIONID", TOKEN)))
print(probe("JSESSlONID (new)     ", mk("JSESSlONID", TOKEN)))
print(probe("JSESSIONID+JSESSlONID", _s if (_s := None) else
            None) if False else "", end="")

# both
s = requests.Session()
s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8"})
s.cookies.set("JSESSIONID", TOKEN, domain=".vjudge.net", path="/")
s.cookies.set("JSESSlONID", TOKEN, domain=".vjudge.net", path="/")
print(probe("BOTH                ", s))
