from __future__ import annotations

import unittest

from live_smoke import validate_round_contract


def insight(params: dict) -> dict:
    return {"path": "/v2/insights", "params": params, "response": {}}


class LiveSmokeTests(unittest.TestCase):
    def test_round_contract_accepts_two_discovery_and_identical_pool_evaluations(self):
        calls = [
            insight({"take": 20, "signal.interests.entities": "a"}),
            insight({"take": 20, "signal.interests.entities": "b"}),
            insight({"take": 3, "signal.interests.entities": "a", "filter.results.entities": "m1,m2,m3"}),
            insight({"take": 3, "signal.interests.entities": "b", "filter.results.entities": "m1,m2,m3"}),
        ]
        summary = validate_round_contract(calls, expected_discovery_take=20)
        self.assertEqual(summary["same_pool_size"], 3)

    def test_round_contract_rejects_different_evaluation_pools(self):
        calls = [
            insight({"take": 20}),
            insight({"take": 20}),
            insight({"take": 2, "filter.results.entities": "m1,m2"}),
            insight({"take": 2, "filter.results.entities": "m2,m3"}),
        ]
        with self.assertRaises(RuntimeError):
            validate_round_contract(calls, expected_discovery_take=20)

    def test_round2_contract_requires_exclusion_and_keeps_veto_out_of_pool(self):
        calls = [
            insight({"take": 25, "filter.exclude.entities": "m0"}),
            insight({"take": 25, "filter.exclude.entities": "m0"}),
            insight({"take": 2, "filter.results.entities": "m1,m2"}),
            insight({"take": 2, "filter.results.entities": "m1,m2"}),
        ]
        summary = validate_round_contract(
            calls, expected_discovery_take=25, required_excluded_ids=["m0"]
        )
        self.assertEqual(summary["same_pool_size"], 2)

    def test_round_contract_requires_seed_movie_exclusions(self):
        calls = [
            insight({"take": 20, "filter.exclude.entities": "seed-a,seed-b"}),
            insight({"take": 20, "filter.exclude.entities": "seed-a,seed-b"}),
            insight({"take": 2, "filter.results.entities": "m1,m2"}),
            insight({"take": 2, "filter.results.entities": "m1,m2"}),
        ]
        summary = validate_round_contract(
            calls,
            expected_discovery_take=20,
            required_excluded_ids=["seed-a", "seed-b"],
        )
        self.assertEqual(summary["same_pool_size"], 2)

    def test_round_contract_rejects_missing_required_exclusion(self):
        calls = [
            insight({"take": 20, "filter.exclude.entities": "seed-a"}),
            insight({"take": 20, "filter.exclude.entities": "seed-a"}),
            insight({"take": 2, "filter.results.entities": "m1,m2"}),
            insight({"take": 2, "filter.results.entities": "m1,m2"}),
        ]
        with self.assertRaises(RuntimeError):
            validate_round_contract(
                calls,
                expected_discovery_take=20,
                required_excluded_ids=["seed-a", "seed-b"],
            )


if __name__ == "__main__":
    unittest.main()
