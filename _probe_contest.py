# -*- coding: utf-8 -*-
"""Temp probe: contestProblems item shape."""
import re
import json
import requests

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.luogu.com.cn/",
})
s.get("https://www.luogu.com.cn/", timeout=15)

for cid in [304154, 252716]:
    r = s.get(f"https://www.luogu.com.cn/contest/{cid}", timeout=15)
    m = re.search(r'<script[^>]*>(\{"instance".*?)</script>', r.text, re.DOTALL)
    d = json.loads(m.group(1))
    dd = d.get("data", {})
    print("== cid", cid, "| joined:", dd.get("joined"),
          "| canClarify:", dd.get("canClarify"), "| canViewScoreboard:", dd.get("canViewScoreboard"))
    cp = dd.get("contestProblems") or []
    print("  contestProblems len:", len(cp))
    if cp:
        item = cp[0]
        print("  item keys:", sorted(item.keys()))
        prob = item.get("problem") or {}
        print("  problem keys:", sorted(prob.keys()) if isinstance(prob, dict) else prob)
        print("  sample:", json.dumps(item, ensure_ascii=False)[:400])
