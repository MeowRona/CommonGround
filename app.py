from __future__ import annotations

import json
import os
import threading
import time
from collections import defaultdict, deque
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
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "").strip().rstrip("/")

RATE_WINDOW_SECONDS = 60.0
SEARCH_LIMIT_PER_MINUTE = 40
BRIDGE_LIMIT_PER_MINUTE = 12
BRIDGE_CONCURRENCY = 6
RATE_KEY_MAX_ITEMS = 2048
SEARCH_CACHE_TTL_SECONDS = 300.0
SEARCH_CACHE_MAX_ITEMS = 256

_rate_lock = threading.Lock()
_rate_events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_bridge_slots = threading.BoundedSemaphore(BRIDGE_CONCURRENCY)
_search_cache_lock = threading.Lock()
_search_cache: dict[tuple[str, str], tuple[float, dict]] = {}


def _client_key(headers, client_address) -> str:
    forwarded = headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()[:80]
    return str(client_address[0])[:80]


def allow_request(client_key: str, bucket: str, limit: int, now: float | None = None) -> bool:
    timestamp = time.monotonic() if now is None else now
    cutoff = timestamp - RATE_WINDOW_SECONDS
    key = (client_key, bucket)
    with _rate_lock:
        if key not in _rate_events and len(_rate_events) >= RATE_KEY_MAX_ITEMS:
            stale_keys = [
                existing_key
                for existing_key, existing_events in _rate_events.items()
                if not existing_events or existing_events[-1] <= cutoff
            ]
            for stale_key in stale_keys:
                _rate_events.pop(stale_key, None)
                if len(_rate_events) < RATE_KEY_MAX_ITEMS:
                    break
            if len(_rate_events) >= RATE_KEY_MAX_ITEMS:
                oldest_key = min(
                    _rate_events,
                    key=lambda existing_key: (
                        _rate_events[existing_key][-1]
                        if _rate_events[existing_key]
                        else float("-inf")
                    ),
                )
                _rate_events.pop(oldest_key, None)

        events = _rate_events.setdefault(key, deque())
        while events and events[0] <= cutoff:
            events.popleft()
        if len(events) >= limit:
            return False
        events.append(timestamp)
        return True


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
        if len(entity_id) > 200 or len(name) > 200:
            raise ValueError(f"{field} contains an overlong entity ID or name")
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
    if len(query) > 120:
        raise ValueError("search query must be at most 120 characters")

    mode = os.environ.get("COMMON_GROUND_MODE", "fixture").strip().lower()
    cache_key = (mode, query.casefold())
    now = time.monotonic()
    with _search_cache_lock:
        cached = _search_cache.get(cache_key)
        if cached and now - cached[0] < SEARCH_CACHE_TTL_SECONDS:
            return cached[1]

    rows = get_client().search_interests(query, 5)
    result = {
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
    with _search_cache_lock:
        if len(_search_cache) >= SEARCH_CACHE_MAX_ITEMS:
            oldest = min(_search_cache, key=lambda key: _search_cache[key][0])
            _search_cache.pop(oldest, None)
        _search_cache[cache_key] = (now, result)
    return result


def health_state() -> tuple[int, dict]:
    mode = os.environ.get("COMMON_GROUND_MODE", "fixture").strip().lower()
    key_present = bool(os.environ.get("QLOO_API_KEY"))
    ok = mode != "live" or key_present
    return (
        HTTPStatus.OK if ok else HTTPStatus.SERVICE_UNAVAILABLE,
        {"ok": ok, "mode": mode, "qloo_key_present": key_present},
    )


class Handler(BaseHTTPRequestHandler):
    server_version = "CommonGround/0.3"

    def log_message(self, format: str, *args) -> None:
        return

    def _cors_origin(self) -> str:
        origin = self.headers.get("Origin", "").strip().rstrip("/")
        return origin if FRONTEND_ORIGIN and origin == FRONTEND_ORIGIN else ""

    def _send_json(self, status: int, body: dict) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        cors_origin = self._cors_origin()
        if cors_origin:
            self.send_header("Access-Control-Allow-Origin", cors_origin)
            self.send_header("Vary", "Origin")
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

    def _rate_limit(self, bucket: str, limit: int) -> bool:
        client = _client_key(self.headers, self.client_address)
        if allow_request(client, bucket, limit):
            return True
        self._send_json(
            HTTPStatus.TOO_MANY_REQUESTS,
            {"error": "Too many requests. Please wait a minute and try again."},
        )
        return False

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
            status, body = health_state()
            self._send_json(status, body)
            return
        if request_path == "/api/search":
            if not self._rate_limit("search", SEARCH_LIMIT_PER_MINUTE):
                return
            try:
                query = parse_qs(parsed.query).get("q", [""])[0]
                self._send_json(HTTPStatus.OK, search_interests(query))
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except RuntimeError as exc:
                self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(exc)})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_OPTIONS(self) -> None:
        request_path = urlsplit(self.path).path
        if request_path not in {"/api/search", "/api/bridge", "/health"}:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        origin = self._cors_origin()
        if not origin:
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "origin not allowed"})
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        self.end_headers()

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/api/bridge":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        if not self._rate_limit("bridge", BRIDGE_LIMIT_PER_MINUTE):
            return
        if not _bridge_slots.acquire(blocking=False):
            self._send_json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {"error": "CommonGround is busy. Please retry shortly."},
            )
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
        finally:
            _bridge_slots.release()
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
