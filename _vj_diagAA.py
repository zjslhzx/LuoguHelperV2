# -*- coding: utf-8 -*-
"""Temporary diagnostic: extract real Vjudge language options for 洛谷 origin."""
import re
import json
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
PID = "P1001"

vj_pid = app._build_vj_pid(PID)
s = app._build_vjudge_session(COOKIE)
page = s.get(f"{app.VJUDGE_BASE}/problem/{vj_pid}", timeout=20).text

# 1) Find <select name="language"> options
sel = re.search(r'<select[^>]*name="language"[^>]*>(.*?)</select>', page, re.S)
if sel:
    print("=== <select name=language> options ===")
    for m in re.finditer(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>', sel.group(1)):
        print(f"  value={m.group(1)!r:10s} label={m.group(2).strip()!r}")
else:
    print("no <select name=language> found")

# 2) Search for language option JSON / arrays in page & bundles
print("\n=== 'language' contexts in page ===")
for m in list(re.finditer(r'language', page))[:6]:
    i = m.start()
    print("  ...", page[max(0, i-80):i+120].replace("\n", " ")[:200])

# 3) dataJson raw
m = re.search(r'name="dataJson"[^>]*>\s*([^<]+)', page) or \
    re.search(r'name="dataJson"\s+value="([^"]*)"', page)
if m:
    raw = m.group(1).replace("\\u0022", '"').replace("\\u0027", "'").replace("\\/", "/")
    try:
        data = json.loads(raw)
        print("\n=== dataJson keys ===")
        print("  ", list(data.keys()))
        for k in ("language", "languages", "lang", "submitMethods"):
            if k in data:
                print(f"  {k} =", json.dumps(data[k], ensure_ascii=False)[:600])
    except Exception as e:
        print("dataJson parse failed:", e)
