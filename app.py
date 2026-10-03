from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from agent import CommonGroundAgent
from qloo_client import FixtureQlooClient, RealQlooClient, ResolvedInterest, SUPPORTED_INPUT_TYPES


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
    agent = CommonGroundAgent(get_client())
    round_no = int(payload.get("round", 1))
    rejected_ids = payload.get("rejected_ids", [])
    if "profile_a_entities" in payload or "profile_b_entities" in payload:
        a = _parse_resolved_entities(payload.get("profile_a_entities"), "profile_a_entities")
        b = _parse_resolved_entities(payload.get("profile_b_entities"), "profile_b_entities")
        return agent.run_resolved(a, b, round_no=round_no, rejected_ids=rejected_ids)
    return agent.run(
        payload.get("profile_a", []),
        payload.get("profile_b", []),
        round_no=round_no,
        rejected_ids=rejected_ids,
    )


def _parse_resolved_entities(value: object, field: str) -> list[ResolvedInterest]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    rows: list[ResolvedInterest] = []
    seen: set[str] = set()
    for raw in value:
        if not isinstance(raw, dict):
            raise ValueError(f"{field} entries must be objects")
        entity_id = raw.get("entity_id")
        name = raw.get("name")
        entity_type = raw.get("entity_type")
        if not all(isinstance(x, str) and x.strip() for x in (entity_id, name, entity_type)):
            raise ValueError(f"{field} entries require entity_id, name and entity_type")
        if entity_type not in SUPPORTED_INPUT_TYPES:
            raise ValueError(f"unsupported input entity type: {entity_type}")
        if entity_id not in seen:
            seen.add(entity_id)
            rows.append(ResolvedInterest(entity_id.strip(), name.strip(), entity_type.strip()))
    if not 1 <= len(rows) <= 3:
        raise ValueError(f"{field} must contain 1 to 3 unique entities")
    return rows


def search_interests(query: str) -> dict:
    query = " ".join(query.strip().split())
    if len(query) < 2:
        raise ValueError("search query must contain at least 2 characters")
    rows = get_client().search_interests(query, 5)
    return {
        "query": query,
        "results": [
            {
                "entity_id": row.entity_id,
                "name": row.name,
                "entity_type": row.entity_type,
                "kind": "movie" if row.entity_type == "urn:entity:movie" else "artist",
            }
            for row in rows
        ],
    }


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
        parsed = urlsplit(self.path)
        request_path = parsed.path
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
        if request_path == "/api/search":
            try:
                query = parse_qs(parsed.query).get("q", [""])[0]
                self._send_json(HTTPStatus.OK, search_interests(query))
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except RuntimeError as exc:
                self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(exc)})
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
