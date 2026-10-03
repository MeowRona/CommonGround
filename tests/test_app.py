from __future__ import annotations

import os
import unittest

from app import build_bridge, search_interests


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


if __name__ == "__main__":
    unittest.main()
