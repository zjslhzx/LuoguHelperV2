import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app

api = app.Api()

tests = [
    # (label, method, pid)
    ("atcoder endpoint with luogu pid", "get_atcoder_problem", "P1000"),
    ("luogu endpoint with atcoder raw pid", "get_problem", "abc138_a"),
    ("atcoder endpoint with atcoder pid", "get_atcoder_problem", "abc138_a"),
    ("luogu endpoint with luogu pid", "get_problem", "P1000"),
]

for label, method, pid in tests:
    try:
        fn = getattr(api, method)
        r = fn(pid)
        print(f"[{label}] pid={pid!r} -> success={r.get('success')} error={r.get('error')}")
    except Exception as e:
        print(f"[{label}] pid={pid!r} -> EXC {type(e).__name__}: {e}")

print("---")
# Also test get_problems_page with OJ mismatch? not relevant to analyze
