from __future__ import annotations

import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from qloo_client import (
    CandidateEvaluation,
    FixtureQlooClient,
    QlooTransport,
    RealQlooClient,
    build_insights_params,
    build_search_params,
)
from ranking import rank_bridges


def row(entity_id: str, rank: int, name: str | None = None) -> CandidateEvaluation:
    return CandidateEvaluation(entity_id, name or entity_id, rank)


class RankingTests(unittest.TestCase):
    def test_worst_rank_beats_better_average_rank(self):
        # Average rank prefers 1/9 (5.0) over 6/6 (6.0), while max-min fairness
        # protects the worse-off person and correctly prefers 6/6.
        a = [row("polarizing", 1), row("bridge", 6)]
        b = [row("polarizing", 9), row("bridge", 6)]
        ranked = rank_bridges(a, b)
        self.assertEqual(ranked[0].entity_id, "bridge")
        self.assertEqual(ranked[0].worst_rank, 6)

    def test_missing_evaluation_is_unknown_not_zero(self):
        a = [row("a-only", 1), row("shared", 2)]
        b = [row("shared", 4)]
        ranked = rank_bridges(a, b)
        self.assertEqual([x.entity_id for x in ranked], ["shared"])

    def test_fixture_rejects_random_text(self):
        with self.assertRaises(ValueError):
            FixtureQlooClient().resolve_interests(["qwertyuiop"])

    def test_search_request_shape(self):
        self.assertEqual(build_search_params("Blade Runner", 3), {"query": "Blade Runner", "take": 3})

    def test_insights_same_pool_request_shape(self):
        params = build_insights_params(
            ["seed-a", "seed-b"],
            12,
            result_ids=["movie-a", "movie-b"],
            exclude_ids=["movie-x"],
        )
        self.assertEqual(params["filter.type"], "urn:entity:movie")
        self.assertEqual(params["signal.interests.entities"], "seed-a,seed-b")
        self.assertEqual(params["filter.results.entities"], "movie-a,movie-b")
        self.assertEqual(params["filter.exclude.entities"], "movie-x")
        self.assertEqual(params["feature.explainability"], "true")

    def test_transport_wraps_http_error_without_leaking_key(self):
        transport = QlooTransport(api_key="super-secret-test-key")
        error = HTTPError("https://example.invalid", 401, "Unauthorized", {}, None)
        with patch("qloo_client.urlopen", side_effect=error):
            with self.assertRaises(RuntimeError) as ctx:
                transport.get_json("/search", {"query": "test"})
        self.assertIn("HTTP 401", str(ctx.exception))
        self.assertNotIn("super-secret-test-key", str(ctx.exception))

    def test_real_client_resolves_exact_supported_entity(self):
        class FakeTransport:
            def get_json(self, path, params):
                self.path = path
                self.params = params
                return {
                    "results": [
                        {"entity_id": "seed:blade", "name": "Blade Runner", "types": ["urn:entity:movie"]},
                        {"entity_id": "seed:other", "name": "Blade Runner Cafe", "types": ["urn:entity:place"]},
                    ]
                }

        client = RealQlooClient(FakeTransport())
        result = client.resolve_interests(["Blade Runner"])
        self.assertEqual(result[0].entity_id, "seed:blade")
        self.assertEqual(result[0].entity_type, "urn:entity:movie")

    def test_real_client_parses_same_pool_rank_and_literal_explainability(self):
        class FakeTransport:
            def get_json(self, path, params):
                return {
                    "results": {
                        "entities": [
                            {
                                "entity_id": "movie:arrival",
                                "name": "Arrival",
                                "query": {
                                    "affinity": 0.81,
                                    "explainability": {"contributors": [{"entity_id": "seed:blade", "score": 0.4}]},
                                },
                            },
                            {"entity_id": "movie:her", "name": "Her", "query": {"affinity": 0.78}},
                        ]
                    }
                }

        client = RealQlooClient(FakeTransport())
        interests = [type("I", (), {"entity_id": "seed:blade", "name": "Blade Runner", "entity_type": "urn:entity:movie"})()]
        rows = client.evaluate_candidates(interests, ["movie:arrival", "movie:her"])
        self.assertEqual([x.rank for x in rows], [1, 2])
        self.assertEqual(rows[0].evidence, ("Blade Runner",))
        self.assertEqual(rows[1].evidence, ())


if __name__ == "__main__":
    unittest.main()
