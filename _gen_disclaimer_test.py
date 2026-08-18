# -*- coding: utf-8 -*-
"""Temporary helper: build index.html + stub pywebview bridge for browser QA."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app  # noqa: E402

if __name__ == "__main__":
    html = app._build_index_html()
    # Rewrite absolute file:// asset URIs to server-relative paths so the
    # page works over http:// (browser tools block file:// navigation).
    root = os.path.dirname(os.path.abspath(__file__))
    root_uri = "file:///" + root.replace("\\", "/") + "/"
    html = html.replace(root_uri, "/")
    content = app._load_disclaimer()
    stub = (
        "<script>\n"
        "(function(){\n"
        "  var disclaimerContent = " + json.dumps(content, ensure_ascii=False) + ";\n"
        "  var noop = function(){ return Promise.resolve({success:false}); };\n"
        "  var api = {};\n"
        "  api.get_disclaimer = function(){ return Promise.resolve({success:true, content: disclaimerContent}); };\n"
        "  window.pywebview = { api: api };\n"
        "})();\n"
        "</script>\n"
    )
    # Inject the stub right before the first <script src=...i18n.js> tag.
    marker = '<script src="'
    idx = html.find(marker)
    if idx == -1:
        raise SystemExit("marker not found")
    html = html[:idx] + stub + html[idx:]
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_disclaimer_test.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("WROTE", out)
