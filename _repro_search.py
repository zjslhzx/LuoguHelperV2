import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app

api = app.Api()

for q in ["CF1551A", "CF1551B1", "CF1A", "P1000", "B2001", "SP1", "AT_abc001_a", "CF", "数组"]:
    try:
        r = api.search(q)
        problems = r.get("problems") or []
        print(f"search({q!r}) -> count={r.get('count')} first={[(p['pid'], p['title']) for p in problems[:2]]} error={r.get('error')}")
    except Exception as e:
        print(f"search({q!r}) -> EXC {type(e).__name__}: {e}")
