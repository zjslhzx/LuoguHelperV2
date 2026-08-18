# -*- coding: utf-8 -*-
"""Live diagnostic: does the app's requests-based direct submit work right now?"""
import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app

cfg = app.load_config()
cookie = cfg.get("cookie", "")
print("cookie present:", bool(cookie), "len:", len(cookie))

# Simulate exactly what submit_code does for a direct submit (no captcha).
try:
    rid = app.submit_code(
        "P1000",
        "#include <cstdio>\nint main(){return 0;}",
        12,
        cookie,
        enable_o2=False,
        verify="",
        session_cookies="",
        csrf_token="",
        session=None,
        contest_id="",
    )
    print("DIRECT SUBMIT SUCCESS rid =", rid)
except app.CaptchaRequiredError as e:
    print("CaptchaRequiredError:", e)
except Exception as e:
    print("Other error:", type(e).__name__, e)
