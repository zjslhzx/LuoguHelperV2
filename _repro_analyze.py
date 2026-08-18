import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app

api = app.Api()

# Simulate what analyze() does for an AtCoder problem
for pid in ["abc138_a", "abc241_f", "dp_t", "P1000"]:
    print("=" * 60)
    print("PROBLEM:", pid)
    try:
        if pid.upper().startswith("P") or pid.upper().startswith("B") or pid.upper().startswith("CF"):
            r = api.get_problem(pid)
        else:
            r = api.get_atcoder_problem(pid)
        print("  get problem -> success:", r.get("success"), "error:", r.get("error"))
        if r.get("success"):
            print("  problem pid:", r["problem"].get("pid"), "title:", r["problem"].get("title"))
    except Exception as e:
        print("  get problem EXC:", repr(e))
    try:
        r2 = api.get_solutions(pid, cookie="")
        print("  get solutions -> success:", r2.get("success"), "error:", r2.get("error"))
        if r2.get("success"):
            print("  solutions count:", r2.get("total_solutions"))
    except Exception as e:
        print("  get solutions EXC:", repr(e))
