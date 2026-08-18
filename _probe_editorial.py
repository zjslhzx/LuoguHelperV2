# -*- coding: utf-8 -*-
"""Probe Luogu AtCoder solution page availability."""
import requests
import re

for pid in ["AT_abc138_2", "AT_awc0135_2"]:
    url = f"https://www.luogu.com.cn/problem/solution/{pid}"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        print("=" * 60)
        print(url, "->", r.status_code, "len", len(r.text))
        m = re.search(r"<script id=\"lentille-context\"[^>]*>(.*?)</script>", r.text, re.S)
        if m:
            print("lentille found, len", len(m.group(1)))
            print(m.group(1)[:300])
        else:
            print(r.text[:300].replace("\n", " "))
    except Exception as e:
        print("ERROR", url, e)
