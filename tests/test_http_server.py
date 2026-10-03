from __future__ import annotations

import json
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app


class HttpServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_mode = os.environ.get("COMMON_GROUND_MODE")
        cls.previous_origin = app.FRONTEND_ORIGIN
        os.environ["COMMON_GROUND_MODE"] = "fixture"
        os.environ.pop("QLOO_API_KEY", None)
        app.FRONTEND_ORIGIN = "https://meowrona.github.io"
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        app.FRONTEND_ORIGIN = cls.previous_origin
        if cls.previous_mode is None:
            os.environ.pop("COMMON_GROUND_MODE", None)
        else:
            os.environ["COMMON_GROUND_MODE"] = cls.previous_mode

    def get_json(self, path: str, *, origin: str | None = None):
        headers = {}
        if origin:
            headers["Origin"] = origin
        with urlopen(Request(f"{self.base}{path}", headers=headers), timeout=3) as response:
            return response, json.loads(response.read().decode("utf-8"))

    def test_health_endpoint_and_allowed_cors(self):
        response, body = self.get_json("/health", origin="https://meowrona.github.io")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "https://meowrona.github.io")
        self.assertTrue(body["ok"])
        self.assertEqual(body["mode"], "fixture")

    def test_search_endpoint_returns_fixture_entity(self):
        response, body = self.get_json("/api/search?q=blade")
        self.assertEqual(response.status, 200)
        self.assertEqual(body["results"][0]["name"], "Blade Runner")

    def test_demo_scenarios_are_served_for_local_fixture_ui(self):
        response, body = self.get_json("/demo_scenarios.json")
        self.assertEqual(response.status, 200)
        self.assertGreaterEqual(len(body["scenarios"]), 2)
        self.assertIn("rounds", body["scenarios"][0])

    def test_options_allows_pages_and_rejects_foreign_origin(self):
        allowed = Request(
            f"{self.base}/api/bridge",
            method="OPTIONS",
            headers={
                "Origin": "https://meowrona.github.io",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        with urlopen(allowed, timeout=3) as response:
            self.assertEqual(response.status, 204)
            self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "https://meowrona.github.io")

        denied = Request(
            f"{self.base}/api/bridge",
            method="OPTIONS",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(denied, timeout=3)
        self.assertEqual(ctx.exception.code, 403)

    def test_bridge_post_with_resolved_entities(self):
        payload = {
            "profile_a_entities": [
                {"entity_id": "seed:blade-runner", "name": "Blade Runner", "entity_type": "urn:entity:movie"},
                {"entity_id": "seed:aphex-twin", "name": "Aphex Twin", "entity_type": "urn:entity:artist"},
            ],
            "profile_b_entities": [
                {"entity_id": "seed:amelie", "name": "Amelie", "entity_type": "urn:entity:movie"},
                {"entity_id": "seed:daft-punk", "name": "Daft Punk", "entity_type": "urn:entity:artist"},
            ],
        }
        request = Request(
            f"{self.base}/api/bridge",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Origin": "https://meowrona.github.io"},
            method="POST",
        )
        with urlopen(request, timeout=3) as response:
            body = json.loads(response.read().decode("utf-8"))
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "https://meowrona.github.io")
        self.assertEqual(body["bridge"]["name"], "Arrival")
        self.assertEqual(body["diagnostics"]["top3_overlap"], 0)

    def test_bridge_rejects_wrong_content_type(self):
        request = Request(
            f"{self.base}/api/bridge",
            data=b"{}",
            headers={"Content-Type": "text/plain"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request, timeout=3)
        self.assertEqual(ctx.exception.code, 400)

    def test_bridge_rejects_jsonp_content_type(self):
        request = Request(
            f"{self.base}/api/bridge",
            data=b"{}",
            headers={"Content-Type": "application/jsonp"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request, timeout=3)
        self.assertEqual(ctx.exception.code, 400)

    def test_bridge_accepts_json_content_type_with_charset(self):
        payload = {
            "profile_a": ["Blade Runner", "Aphex Twin"],
            "profile_b": ["Amelie", "Daft Punk"],
        }
        request = Request(
            f"{self.base}/api/bridge",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urlopen(request, timeout=3) as response:
            self.assertEqual(response.status, 200)

    def test_bridge_rejects_invalid_utf8_with_400(self):
        request = Request(
            f"{self.base}/api/bridge",
            data=b'\xff\xfe{"x":1}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request, timeout=3)
        self.assertEqual(ctx.exception.code, 400)

    def test_bridge_rejects_invalid_round_type_with_400(self):
        payload = {
            "profile_a": ["Blade Runner", "Aphex Twin"],
            "profile_b": ["Amelie", "Daft Punk"],
            "round": None,
        }
        request = Request(
            f"{self.base}/api/bridge",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request, timeout=3)
        self.assertEqual(ctx.exception.code, 400)
        body = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertIn("round must be an integer", body["error"])


if __name__ == "__main__":
    unittest.main()
