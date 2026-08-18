# -*- coding: utf-8 -*-
"""Diagnostic #2: save captcha image + extract Luogu frontend JS (NOT part of the project)."""
import json
import re
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
    # Save captcha image
    r = s.get(f"{LUOGU_BASE}/api/verify/captcha", timeout=20)
    with open("captcha_sample.png", "wb") as f:
        f.write(r.content)
    print("saved captcha_sample.png", r.headers.get("Content-Type"), len(r.content))

    # Fetch problem page and collect script URLs
    rp = s.get(f"{LUOGU_BASE}/problem/P1000", timeout=20)
    srcs = re.findall(r'<script[^>]+src="([^"]+)"', rp.text)
    print("\nscript srcs:")
    for u in srcs:
        print("  ", u)
    # collect likely app bundle urls
    js_urls = []
    for u in srcs:
        if u.startswith("/"):
            u = LUOGU_BASE + u
        if ".js" in u:
            js_urls.append(u)

    # Download a couple of the main app bundles and grep for captcha/verify
    keywords = ["verify", "captcha", "验证码", "click", "点击"]
    for u in js_urls[:6]:
        try:
            jr = s.get(u, timeout=25)
        except Exception as e:
            print("  fetch fail", u, e)
            continue
        txt = jr.text
        hits = [k for k in keywords if k in txt]
        if hits:
            print(f"\n=== {u} len={len(txt)} hits={hits} ===")
            # print surrounding context of 'verify' occurrences
            for m in list(re.finditer(r"verify", txt))[:8]:
                st = max(0, m.start() - 160)
                en = min(len(txt), m.end() + 200)
                snippet = txt[st:en].replace("\n", " ")
                print("   ...", snippet)
                print("   ---")


if __name__ == "__main__":
    main()
