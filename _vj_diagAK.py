# -*- coding: utf-8 -*-
"""Temporary diagnostic: verify status page URL format for a runId."""
import re
import app

COOKIE = "71D4CBE67CE4E68DD3E6FA2EAA00DA0D"
s = app._build_vjudge_session(COOKIE)

for u in ["/status/71963425", "/solution/71963425", "/status/71963425#"]:
    try:
        r = s.get(f"{app.VJUDGE_BASE}{u}", timeout=20)
        m = re.search(r'<title>(.*?)</title>', r.text, re.S)
        t = (m.group(1).strip()[:40] if m else "")
        print(f"GET {u} -> {r.status_code} title={t!r}")
    except Exception as e:
        print(f"GET {u} EXC {e}")
