"""Temporary browser-test harness: serves the app's static UI in a plain
browser and proxies every pywebview API call to the real Python backend
(no pywebview window needed). For visual/browser QA only; not part of the
shipped app."""
import os
import re
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(BASE, "templates", "index.html")
STATIC = os.path.join(BASE, "static")

MOCK = """<script>
(function () {
  var api = new Proxy({}, {
    get: function (_, method) {
      // Returning a function for ANY property turns the Proxy into a
      // "thenable" (the get trap answers proxy.then), so `await pyApi()`
      // hangs forever in the real app flow. Only answer string method
      // names; return undefined for 'then'/symbols so await resolves.
      if (typeof method !== 'string' || method === 'then' || method === 'toJSON') {
        return undefined;
      }
      return function () {
        var args = Array.prototype.slice.call(arguments);
        return fetch('/api/rpc', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ method: method, args: args })
        }).then(function (r) { return r.json(); });
      };
    }
  });
  window.pywebview = { api: api };
})();
</script>
"""


def build_html():
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        html = f.read()
    html = re.sub(
        r"\{\{\s*url_for\(['\"]static['\"],\s*filename=['\"]([^'\"]+)['\"]\)\s*\}\}",
        r"/static/\1",
        html,
    )
    # Inject the pywebview mock right before the i18n.js/app.js script tags.
    html = html.replace('<script src="/static/i18n.js">', MOCK + '<script src="/static/i18n.js">')
    return html


HTML = build_html()


_LOG = os.path.join(BASE, "_rpc_log.jsonl")


def _log_call(method, args, result):
    try:
        entry = {
            "method": method,
            "args": args,
            "result": result,
        }
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def rpc(body):
    import app
    try:
        payload = json.loads(body)
        method = payload.get("method")
        args = payload.get("args") or []
        fn = getattr(app.Api(), method, None)
        if fn is None:
            return {"success": False, "error": f"Unknown API method: {method}"}
        result = fn(*args)
        if not isinstance(result, dict):
            result = {"success": True, "result": result}
        _log_call(method, args, result)
        return result
    except Exception as e:  # noqa: BLE001
        _log_call(method, args, {"error": repr(e)})
        return {"success": False, "error": f"服务器内部错误: {e}"}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE, **kwargs)

    def end_headers(self):
        # Never cache static files, so browser QA always picks up the latest code.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html", ""):
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/rpc":
            length = int(self.headers.get("Content-Length", 0))
            self._json(200, rpc(self.rfile.read(length)))
            return
        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
