from __future__ import annotations

import os
import unittest
from http import HTTPStatus
from unittest.mock import patch

import app
from app import FixtureQlooClient, allow_request, build_bridge, health_state, search_interests


class AppTests(unittest.TestCase):
    def setUp(self):
        self.previous = os.environ.get("COMMON_GROUND_MODE")
        os.environ["COMMON_GROUND_MODE"] = "fixture"

    def tearDown(self):
        if self.previous is None:
            os.environ.pop("COMMON_GROUND_MODE", None)
        else:
            os.environ["COMMON_GROUND_MODE"] = self.previous

    def test_fixture_bridge_returns_one_primary_proposal(self):
        result = build_bridge({
            "profile_a": ["Blade Runner", "Aphex Twin"],
            "profile_b": ["Amelie", "Daft Punk"],
        })
        self.assertEqual(result["status"], "proposal")
        self.assertIsNotNone(result["bridge"])
        self.assertIn("rank_a", result["bridge"])
        self.assertIn("rank_b", result["bridge"])

    def test_feedback_round_excludes_previous_bridge(self):
        first = build_bridge({
            "profile_a": ["Blade Runner", "Aphex Twin"],
            "profile_b": ["Amelie", "Daft Punk"],
        })
        second = build_bridge({
            "profile_a": ["Blade Runner", "Aphex Twin"],
            "profile_b": ["Amelie", "Daft Punk"],
            "round": 2,
            "rejected_ids": [first["bridge"]["entity_id"]],
        })
        self.assertNotEqual(first["bridge"]["entity_id"], second["bridge"]["entity_id"])

    def test_random_input_fails_instead_of_fake_success(self):
        with self.assertRaises(ValueError):
            build_bridge({"profile_a": ["qwertyuiop"], "profile_b": ["asdfghjkl"]})

    def test_non_object_payload_is_rejected(self):
        with self.assertRaises(ValueError):
            build_bridge(["not", "an", "object"])

    def test_fixture_search_returns_canonical_entity(self):
        result = search_interests("blade")
        self.assertEqual(result["results"][0]["name"], "Blade Runner")
        self.assertEqual(result["results"][0]["kind"], "movie")

    def test_short_search_is_rejected(self):
        with self.assertRaises(ValueError):
            search_interests("x")

    def test_overlong_search_is_rejected(self):
        with self.assertRaises(ValueError):
            search_interests("x" * 121)

    def test_search_results_are_cached(self):
        import app

        app._search_cache.clear()
        with patch.object(FixtureQlooClient, "search_interests", wraps=FixtureQlooClient().search_interests) as mocked:
            first = search_interests("blade")
            second = search_interests("blade")
        self.assertEqual(first, second)
        self.assertEqual(mocked.call_count, 1)

    def test_overlong_selected_entity_is_rejected(self):
        with self.assertRaises(ValueError):
            build_bridge({
                "profile_a_entities": [{"entity_id": "x" * 201, "name": "X", "entity_type": "urn:entity:movie"}],
                "profile_b_entities": [{"entity_id": "y", "name": "Y", "entity_type": "urn:entity:movie"}],
            })

    def test_bridge_accepts_explicit_resolved_entities(self):
        result = build_bridge({
            "profile_a_entities": [
                {"entity_id": "seed:blade-runner", "name": "Blade Runner", "entity_type": "urn:entity:movie"},
                {"entity_id": "seed:aphex-twin", "name": "Aphex Twin", "entity_type": "urn:entity:artist"},
            ],
            "profile_b_entities": [
                {"entity_id": "seed:amelie", "name": "Amelie", "entity_type": "urn:entity:movie"},
                {"entity_id": "seed:daft-punk", "name": "Daft Punk", "entity_type": "urn:entity:artist"},
            ],
        })
        self.assertEqual(result["bridge"]["name"], "Arrival")

    def test_explicit_entity_type_is_validated(self):
        with self.assertRaises(ValueError):
            build_bridge({
                "profile_a_entities": [{"entity_id": "x", "name": "X", "entity_type": "urn:entity:place"}],
                "profile_b_entities": [{"entity_id": "y", "name": "Y", "entity_type": "urn:entity:movie"}],
            })

    def test_fixture_health_is_ready_without_key(self):
        os.environ["COMMON_GROUND_MODE"] = "fixture"
        os.environ.pop("QLOO_API_KEY", None)
        status, body = health_state()
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(body["ok"])

    def test_live_health_fails_closed_without_key(self):
        os.environ["COMMON_GROUND_MODE"] = "live"
        os.environ.pop("QLOO_API_KEY", None)
        status, body = health_state()
        self.assertEqual(status, HTTPStatus.SERVICE_UNAVAILABLE)
        self.assertFalse(body["ok"])

    def test_rate_limit_blocks_after_limit_and_recovers_after_window(self):
        key = "unit-test-client-rate-limit"
        self.assertTrue(allow_request(key, "test", 2, now=100.0))
        self.assertTrue(allow_request(key, "test", 2, now=101.0))
        self.assertFalse(allow_request(key, "test", 2, now=102.0))
        self.assertTrue(allow_request(key, "test", 2, now=161.1))

    def test_rate_limit_client_map_is_bounded(self):
        previous_max = app.RATE_KEY_MAX_ITEMS
        with app._rate_lock:
            app._rate_events.clear()
        app.RATE_KEY_MAX_ITEMS = 3
        try:
            for index in range(6):
                self.assertTrue(allow_request(f"client-{index}", "search", 2, now=100.0 + index))
            with app._rate_lock:
                self.assertLessEqual(len(app._rate_events), 3)
        finally:
            app.RATE_KEY_MAX_ITEMS = previous_max
            with app._rate_lock:
                app._rate_events.clear()

    def test_configured_cors_origin_is_exact(self):
        prior = app.FRONTEND_ORIGIN
        app.FRONTEND_ORIGIN = "https://meowrona.github.io"
        try:
            handler = object.__new__(app.Handler)
            handler.headers = {"Origin": "https://meowrona.github.io"}
            self.assertEqual(handler._cors_origin(), "https://meowrona.github.io")
            handler.headers = {"Origin": "https://evil.example"}
            self.assertEqual(handler._cors_origin(), "")
        finally:
            app.FRONTEND_ORIGIN = prior


if __name__ == "__main__":
    unittest.main()
