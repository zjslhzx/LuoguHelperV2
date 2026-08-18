# -*- coding: utf-8 -*-
"""Validate UI-thread WebView2 CookieManager injection via pythonnet.

Opens a blank pywebview window, injects cookies on the UI thread, then reads
them back and prints the result. Auto-closes after a few seconds.
"""
import sys
import time
import threading
import json


def _find_webview2_control(win):
    try:
        native = win.native
        if native is None:
            return None
        for c in native.Controls:
            if type(c).__name__ == "WebView2":
                return c
    except Exception as e:
        print("find_control err:", e)
        return None
    return None


def main():
    import webview

    api = {"done": threading.Event()}

    win = webview.create_window(
        title="cookie test", url=None, js_api=api, width=400, height=300
    )

    result = {}

    def worker():
        try:
            time.sleep(2.0)
            native = win.native
            print("native:", native)
            control = None
            deadline = time.time() + 10
            while time.time() < deadline:
                control = _find_webview2_control(win)
                if control is not None:
                    break
                time.sleep(0.2)
            print("control:", control)
            if control is None:
                result["error"] = "control not found"
                return
            print("InvokeRequired:", control.InvokeRequired)
            from System import Action

            ok = {"v": False}

            def _do():
                try:
                    if control.CoreWebView2 is None:
                        control.EnsureCoreWebView2Async(None)
                    d = time.time() + 10
                    while time.time() < d and control.CoreWebView2 is None:
                        time.sleep(0.05)
                    print("CoreWebView2:", control.CoreWebView2)
                    cm = control.CoreWebView2.CookieManager
                    cookie = cm.CreateCookie("testcookie", "hello", "www.luogu.com.cn", "/")
                    cm.AddOrUpdateCookie(cookie)
                    ok["v"] = True
                except Exception as e:
                    print("inject err:", e)
                    ok["v"] = False

            if control.InvokeRequired:
                control.Invoke(Action(_do))
            else:
                _do()
            result["injected"] = ok["v"]

            # read back via JS after a short delay
            time.sleep(1.0)
            val = win.evaluate_js("document.cookie")
            result["js_cookie"] = val
            print("RESULT:", json.dumps(result, ensure_ascii=False))
        except Exception as e:
            print("worker err:", e)
        finally:
            try:
                win.destroy()
            except Exception:
                pass

    threading.Thread(target=worker, daemon=True).start()

    # Auto-exit after 12s in case the worker fails silently.
    def watchdog():
        time.sleep(12)
        try:
            win.destroy()
        except Exception:
            pass

    threading.Thread(target=watchdog, daemon=True).start()

    webview.start(debug=False)


if __name__ == "__main__":
    main()
