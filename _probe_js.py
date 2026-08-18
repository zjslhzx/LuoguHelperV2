# -*- coding: utf-8 -*-
"""Temporary probe: why do test_frontend_manual_guide_elements checks fail?"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
js_path = os.path.join(ROOT, "static", "app.js")
js = open(js_path, encoding="utf-8").read()
print("js size:", len(js))
for el in ["manualSubmitModal", "manualCopyCodeBtn", "manualOpenLuoguBtn",
           "manualDoneBtn", "manualCancelBtn", "manualCopiedTip"]:
    c1 = '"%s"' % el in js
    c2 = "$%s" % el in js
    c3 = "$%s," % el in js
    print(el, "qmatch=", c1, "dolmatch=", c2, "dolcm=", c3, "=>", c1 or c2 or c3)
    idx = js.find(el)
    if idx >= 0:
        print("   ctx:", repr(js[max(0, idx-15):idx+25]))
