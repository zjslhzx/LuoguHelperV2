import app

cfg = app.load_config()
cookie = cfg.get("cookie", "")
for pid in ["AT_dp_t", "AT_dp_20", "AT_abc138_a", "AT_abc001_1"]:
    try:
        r = app.fetch_problem(pid, cookie)
        print(pid, "-> OK", r.get("title"))
    except RuntimeError as e:
        print(pid, "-> RuntimeError:", e)
