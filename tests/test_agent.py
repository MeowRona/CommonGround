from __future__ import annotations

import unittest

from agent import CommonGroundAgent, normalize_profile
from qloo_client import CandidateAffinity, MockQlooClient


def row(entity_id: str, affinity: float) -> CandidateAffinity:
    return CandidateAffinity(entity_id, entity_id, affinity, "movie")


class AdaptiveStub:
    mode = "test"

    def __init__(self):
        self.calls: list[int] = []

    def recommend_for_profile(self, seeds, target_domain, limit=8):
        self.calls.append(limit)
        person = seeds[0]
        if limit == 8:
            return [row(f"{person}-only", 0.9)]
        return [row("shared", 0.8 if person == "A" else 0.77)]


class AgentTests(unittest.TestCase):
    def test_normalize_deduplicates_and_preserves_order(self):
        self.assertEqual(
            normalize_profile(["  Blade   Runner ", "blade runner", "Her"]),
            ["Blade Runner", "Her"],
        )

    def test_too_many_signals_are_rejected(self):
        with self.assertRaises(ValueError):
            normalize_profile([str(i) for i in range(9)])

    def test_agent_adapts_when_first_pass_has_no_overlap(self):
        client = AdaptiveStub()
        result = CommonGroundAgent(client).run(["A"], ["B"], "movie")
        self.assertTrue(result["agent"]["expanded_search"])
        self.assertEqual(result["results"][0]["entity_id"], "shared")
        self.assertEqual(client.calls, [8, 8, 20, 20])

    def test_demo_agent_returns_trace(self):
        result = CommonGroundAgent(MockQlooClient()).run(["Blade Runner"], ["Amelie"], "movie")
        self.assertGreaterEqual(len(result["agent"]["trace"]), 4)
        self.assertIn(
            result["agent"]["bridge_band"],
            {"strong bridge", "workable bridge", "exploratory bridge"},
        )


if __name__ == "__main__":
    unittest.main()
