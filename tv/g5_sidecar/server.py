#!/usr/bin/env python3
"""
G5 Grok Eyes — SIDECAR (subscription CLI prove)
================================================
Uses local `grok -p` + SuperGrok login. NEVER uses XAI_API_KEY / api.x.ai.

  # be logged in:  grok login   (once)
  python3 tv/g5_sidecar/server.py
  curl -s http://127.0.0.1:8765/health
  curl -s -X POST http://127.0.0.1:8765/read -H 'content-type: application/json' \
    -d '{"path":"/abs/frame.jpg"}'
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
TV = os.path.dirname(HERE)
if TV not in sys.path:
    sys.path.insert(0, TV)

try:
    import g5_grok_eyes as g5
except Exception as e:
    print("FATAL: cannot import g5_grok_eyes:", e, file=sys.stderr)
    sys.exit(1)

HOST = os.environ.get("G5_SIDECAR_HOST", "127.0.0.1")
PORT = int(os.environ.get("G5_SIDECAR_PORT", "8765"))


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[g5-sidecar] " + (fmt % args) + "\n")

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/health", "/status"):
            st = g5.status()
            st["sidecar"] = {"host": HOST, "port": PORT, "force": True, "lane": "subscription-cli"}
            st["ok"] = True
            st["ready"] = bool(st.get("hasSubscription"))
            self._json(200, st)
            return
        self._json(404, {"ok": False, "msg": "not found"})

    def do_POST(self):
        if self.path.split("?")[0] != "/read":
            self._json(404, {"ok": False, "msg": "POST /read only"})
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b"{}"
            body = json.loads(raw.decode("utf-8") or "{}")
        except Exception as e:
            self._json(400, {"ok": False, "msg": "bad json: " + str(e)[:120]})
            return
        path = str(body.get("path") or body.get("image") or "").strip()
        if not path:
            self._json(400, {"ok": False, "msg": "need path (absolute image file)"})
            return
        if not os.path.isfile(path):
            self._json(404, {"ok": False, "msg": "file missing: " + path[:200]})
            return
        if not g5.has_subscription():
            self._json(503, {
                "ok": False,
                "msg": "grok CLI not logged in — run: grok login  (SuperGrok subscription, NO API keys)",
            })
            return
        result = g5.g5_vision_read(path, prompt=body.get("prompt"), force=True)
        if result is None:
            self._json(502, {
                "ok": False,
                "msg": "g5_vision_read returned None (subscription CLI)",
                "stats": g5.status().get("stats"),
                "last_error": (g5.status().get("stats") or {}).get("last_error"),
            })
            return
        self._json(200, {"ok": True, "lane": "g5-subscription-cli", "read": result})


def main():
    httpd = ThreadingHTTPServer((HOST, PORT), H)
    print(f"G5 sidecar (subscription CLI) on http://{HOST}:{PORT}", flush=True)
    print("  power: grok -p + SuperGrok login — NO api.x.ai / NO XAI_API_KEY", flush=True)
    print("  logged in:", g5.has_subscription(), " bin:", g5._grok_bin(), flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbye", flush=True)


if __name__ == "__main__":
    main()
