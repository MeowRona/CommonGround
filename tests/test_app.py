from __future__ import annotations

import unittest

from app import build_recommendation


class AppTests(unittest.TestCase):
    def test_valid_payload_returns_three_demo_results(self):
        result = build_recommendation({
            "profile_a": ["Blade Runner", "Aphex Twin"],
            "profile_b": ["Amélie", "Daft Punk"],
            "target_domain": "movie",
        })
        self.assertEqual(result["mode"], "demo")
        self.assertEqual(len(result["results"]), 3)
        self.assertIn("affinity_a", result["results"][0])
        self.assertIn("affinity_b", result["results"][0])
        self.assertIn("trace", result["agent"])

    def test_both_profiles_are_required(self):
        with self.assertRaises(ValueError):
            build_recommendation({"profile_a": ["x"], "profile_b": [], "target_domain": "movie"})

    def test_unknown_demo_domain_is_rejected(self):
        with self.assertRaises(ValueError):
            build_recommendation({"profile_a": ["x"], "profile_b": ["y"], "target_domain": "spaceships"})

    def test_non_object_payload_is_rejected(self):
        with self.assertRaises(ValueError):
            build_recommendation(["not", "an", "object"])


if __name__ == "__main__":
    unittest.main()
