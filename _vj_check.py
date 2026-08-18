# -*- coding: utf-8 -*-
"""Compare Luogu problem access: cookie vs no cookie, English vs Chinese OJ id."""
import re
import requests

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
BASE = "https://vjudge.net/problem/"

names = [
    "Luogu-P1001",
    "%E6%B4%9B%E8%B0%B7-P1001",  # 洛谷-P1001 (URL-encoded Chinese)
    "Luogu-P1000",
    "%E6%B4%9B%E8%B0%B7-P1000",
]


def probe(cookie=True):
    s = requests.Session()
    s.headers.update({"User-Agent": ua})
    if cookie:
        s.cookies.set("JSESSIONID", COOKIE, domain=".vjudge.net", path="/")
        s.cookies.set("JSESSlONID", COOKIE, domain=".vjudge.net", path="/")
    tag = "cookie" if cookie else "anon  "
    for name in names:
        r = s.get(BASE + name, timeout=20)
        m = re.search(r'"problemId"\s*:\s*(\d+)', r.text)
        m2 = re.search(r'"oj"\s*:\s*"([^"]+)"', r.text)
        title = re.search(r'<title>(.*?)</title>', r.text, re.S)
        t = (title.group(1).strip()[:30] if title else "")
        print(f"[{tag}] {name:26s} -> {r.status_code} problemId={m.group(1) if m else None} oj={m2.group(1) if m2 else None} title={t!r}")


print("=== WITH cookie ===")
probe(True)
print()
print("=== WITHOUT cookie ===")
probe(False)
