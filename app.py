from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from agent import CommonGroundAgent
from qloo_client import FixtureQlooClient, RealQlooClient


ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "static" / "index.html"
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", os.environ.get("COMMON_GROUND_PORT", "0")))


def get_client():
    mode = os.environ.get("COMMON_GROUND_MODE", "fixture").strip().lower()
    if mode in {"fixture", "demo"}:
        return FixtureQlooClient()
    if mode == "live":
        return RealQlooClient()
    raise RuntimeError("COMMON_GROUND_MODE must be 'fixture' or 'live'")


def build_bridge(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object")
    return CommonGroundAgent(get_client()).run(
        payload.get("profile_a", []),
        payload.get("profile_b", []),
        round_no=int(payload.get("round", 1)),
        rejected_ids=payload.get("rejected_ids", []),
    )


class Handler(BaseHTTPRequestHandler):
    server_version = "CommonGround/0.3"

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, status: int, body: dict) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(raw)

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'",
        )

    def do_GET(self) -> None:
        request_path = urlsplit(self.path).path
        if request_path == "/":
            raw = INDEX.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self._security_headers()
            self.end_headers()
            self.wfile.write(raw)
            return
        if request_path == "/health":
            mode = os.environ.get("COMMON_GROUND_MODE", "fixture").strip().lower()
            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "mode": mode,
                    "qloo_key_present": bool(os.environ.get("QLOO_API_KEY")),
                },
            )
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/api/bridge":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            if "application/json" not in self.headers.get("Content-Type", "").lower():
                raise ValueError("Content-Type must be application/json")
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 64_000:
                raise ValueError("invalid request size")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = build_bridge(payload)
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except RuntimeError as exc:
            self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(exc)})
            return
        self._send_json(HTTPStatus.OK, result)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"CommonGround: http://{HOST}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
