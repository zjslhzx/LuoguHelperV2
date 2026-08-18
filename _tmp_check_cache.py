import json

with open("cache/atcoder_problems.json", encoding="utf-8") as f:
    d = json.load(f)
data = d["_payload"]
print("total problems:", len(data))
if isinstance(data, list):
    sample = [p.get("id") for p in data[:5]]
    print("sample ids:", sample)
    abc = [p.get("id") for p in data if str(p.get("id", "")).startswith("abc001")]
    print("abc001 ids:", abc[:12])
