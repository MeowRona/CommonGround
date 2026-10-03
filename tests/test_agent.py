from __future__ import annotations

import unittest

from agent import CommonGroundAgent, normalize_profile
from qloo_client import CandidateEvaluation, CandidateRef, FixtureQlooClient, ResolvedInterest


class RecordingClient:
    mode = "test"

    def __init__(self):
        self.discover_calls: list[tuple[str, int, tuple[str, ...]]] = []
        self.evaluate_calls: list[tuple[str, tuple[str, ...]]] = []

    def resolve_interests(self, names):
        return [ResolvedInterest(f"seed:{names[0]}", names[0], "urn:entity:movie")]

    def discover_candidates(self, interests, *, take, exclude_ids):
        who = interests[0].name
        self.discover_calls.append((who, take, tuple(exclude_ids)))
        rows = [
            CandidateRef("only-a", "Only A") if who == "A" else CandidateRef("only-b", "Only B"),
            CandidateRef("shared", "Shared"),
        ]
        return [row for row in rows if row.entity_id not in exclude_ids]

    def evaluate_candidates(self, interests, candidate_ids):
        who = interests[0].name
        self.evaluate_calls.append((who, tuple(candidate_ids)))
        order = ["shared", "only-a", "only-b"] if who == "A" else ["only-b", "shared", "only-a"]
        return [
            CandidateEvaluation(entity_id, entity_id, rank)
            for rank, entity_id in enumerate(order, start=1)
            if entity_id in candidate_ids
        ]


class AgentTests(unittest.TestCase):
    def test_normalize_deduplicates_and_caps_profile(self):
        self.assertEqual(normalize_profile([" Blade Runner ", "blade runner", "Aphex Twin"]), ["Blade Runner", "Aphex Twin"])
        with self.assertRaises(ValueError):
            normalize_profile(["a", "b", "c", "d"])

    def test_candidate_seen_only_in_discovery_a_is_still_evaluated_for_b(self):
        client = RecordingClient()
        CommonGroundAgent(client).run(["A"], ["B"])
        eval_b_ids = set(next(ids for who, ids in client.evaluate_calls if who == "B"))
        self.assertIn("only-a", eval_b_ids)

    def test_second_round_widens_and_preserves_veto(self):
        client = RecordingClient()
        result = CommonGroundAgent(client).run(["A"], ["B"], round_no=2, rejected_ids=["shared"])
        self.assertTrue(all(take == 25 for _, take, _ in client.discover_calls))
        self.assertTrue(all(excluded == ("shared",) for _, _, excluded in client.discover_calls))
        self.assertNotEqual(result.get("bridge", {}).get("entity_id"), "shared")

    def test_second_round_candidate_union_never_exceeds_same_pool_limit(self):
        class WideClient:
            mode = "test"

            def resolve_interests(self, names):
                return [ResolvedInterest(f"seed:{names[0]}", names[0], "urn:entity:movie")]

            def discover_candidates(self, interests, *, take, exclude_ids):
                prefix = interests[0].name
                return [CandidateRef(f"{prefix}:{i}", f"{prefix} {i}") for i in range(take)]

            def evaluate_candidates(self, interests, candidate_ids):
                if len(candidate_ids) > 50:
                    raise AssertionError("same-pool candidate list exceeded Qloo take limit")
                return [CandidateEvaluation(entity_id, entity_id, rank) for rank, entity_id in enumerate(candidate_ids, 1)]

        result = CommonGroundAgent(WideClient()).run(["A"], ["B"], round_no=2)
        self.assertEqual(result["status"], "proposal")

    def test_round_limit_is_hard(self):
        with self.assertRaises(ValueError):
            CommonGroundAgent(RecordingClient()).run(["A"], ["B"], round_no=3)

    def test_fixture_evidence_is_candidate_specific(self):
        result = CommonGroundAgent(FixtureQlooClient()).run(
            ["Blade Runner", "Aphex Twin"], ["Amelie", "Daft Punk"]
        )
        bridge = result["bridge"]
        self.assertTrue(bridge["evidence_a"])
        self.assertTrue(bridge["evidence_b"])
        self.assertLessEqual(len(bridge["evidence_a"]), 2)


if __name__ == "__main__":
    unittest.main()
