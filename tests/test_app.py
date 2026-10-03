from __future__ import annotations

import os
import unittest

from app import build_bridge


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


if __name__ == "__main__":
    unittest.main()
