from __future__ import annotations

import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from qloo_client import (
    CandidateAffinity,
    MockQlooClient,
    QlooTransport,
    build_insights_params,
    build_search_params,
)
from ranking import rank_common_ground


def row(entity_id: str, affinity: float) -> CandidateAffinity:
    return CandidateAffinity(entity_id, entity_id, affinity, "movie")


class RankingTests(unittest.TestCase):
    def test_fair_option_beats_high_average_with_weak_person(self):
        a = [row("polarizing", 0.99), row("bridge", 0.80)]
        b = [row("polarizing", 0.35), row("bridge", 0.78)]
        ranked = rank_common_ground(a, b)
        self.assertEqual(ranked[0].entity_id, "bridge")
        self.assertAlmostEqual(ranked[0].floor, 0.78)

    def test_only_shared_entities_are_ranked(self):
        a = [row("a-only", 0.90), row("shared", 0.70)]
        b = [row("b-only", 0.95), row("shared", 0.75)]
        ranked = rank_common_ground(a, b)
        self.assertEqual([r.entity_id for r in ranked], ["shared"])

    def test_demo_client_is_deterministic(self):
        client = MockQlooClient()
        first = client.recommend_for_profile(["Blade Runner", "Aphex Twin"], "movie")
        second = client.recommend_for_profile(["Blade Runner", "Aphex Twin"], "movie")
        self.assertEqual(first, second)
        self.assertTrue(all(0.0 <= r.affinity <= 1.0 for r in first))

    def test_transport_rejects_missing_key(self):
        import os
        prior = os.environ.pop("QLOO_API_KEY", None)
        try:
            with self.assertRaises(RuntimeError):
                QlooTransport(api_key="")
        finally:
            if prior is not None:
                os.environ["QLOO_API_KEY"] = prior

    def test_official_search_request_shape(self):
        self.assertEqual(build_search_params("Blade Runner", 3), {"query": "Blade Runner", "take": 3})

    def test_official_insights_request_shape(self):
        params = build_insights_params(["id-a", "id-b"], "movie", 8)
        self.assertEqual(params["filter.type"], "urn:entity:movie")
        self.assertEqual(params["signal.interests.entities"], "id-a,id-b")
        self.assertEqual(params["feature.explainability"], "true")
        self.assertEqual(params["take"], 8)

    def test_transport_wraps_http_error_without_leaking_key(self):
        transport = QlooTransport(api_key="super-secret-test-key")
        error = HTTPError("https://example.invalid", 401, "Unauthorized", {}, None)
        with patch("qloo_client.urlopen", side_effect=error):
            with self.assertRaises(RuntimeError) as ctx:
                transport.get_json("/search", {"query": "test"})
        message = str(ctx.exception)
        self.assertIn("HTTP 401", message)
        self.assertNotIn("super-secret-test-key", message)


if __name__ == "__main__":
    unittest.main()
