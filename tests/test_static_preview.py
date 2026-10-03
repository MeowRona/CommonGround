from __future__ import annotations

import json
import unittest
from pathlib import Path

from agent import CommonGroundAgent
from build_static_preview import SCENARIOS
from qloo_client import FixtureQlooClient


ROOT = Path(__file__).resolve().parents[1]


class StaticPreviewTests(unittest.TestCase):
    def test_docs_ui_matches_application_ui_source(self):
        self.assertEqual(
            (ROOT / "docs" / "index.html").read_text(encoding="utf-8"),
            (ROOT / "static" / "index.html").read_text(encoding="utf-8"),
        )

    def test_public_scenarios_match_python_policy(self):
        published = json.loads(
            (ROOT / "docs" / "demo_scenarios.json").read_text(encoding="utf-8")
        )["scenarios"]
        self.assertEqual(len(published), len(SCENARIOS))

        agent = CommonGroundAgent(FixtureQlooClient())
        for expected, actual in zip(SCENARIOS, published, strict=True):
            first = agent.run(expected["profile_a"], expected["profile_b"])
            second = agent.run(
                expected["profile_a"],
                expected["profile_b"],
                round_no=2,
                rejected_ids=[first["bridge"]["entity_id"]],
            )
            self.assertEqual(actual["rounds"], [first, second])
            self.assertNotEqual(
                actual["rounds"][0]["bridge"]["entity_id"],
                actual["rounds"][1]["bridge"]["entity_id"],
            )

    def test_runtime_config_exists_and_has_api_base_field(self):
        config = json.loads((ROOT / "docs" / "runtime_config.json").read_text(encoding="utf-8"))
        self.assertIn("api_base", config)
        self.assertIsInstance(config["api_base"], str)


if __name__ == "__main__":
    unittest.main()
