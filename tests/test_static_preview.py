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

    def test_live_ui_renders_before_background_health_check(self):
        html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("showInteractiveSetup();refreshBackendStatus();", html)
        self.assertIn("function refreshBackendStatus(", html)

    def test_live_backend_wake_retries_and_unlocks_controls(self):
        html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("setInteractiveEnabled(true)", html)
        self.assertIn("attempt<47", html)
        self.assertIn("2500", html)
        self.assertIn("did not become ready within two minutes", html)

    def test_feedback_retry_is_single_flight(self):
        html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("feedbackBusy=true", html)
        self.assertIn("if(feedbackBusy)return", html)
        self.assertIn("querySelectorAll('.choice').forEach(x=>x.disabled=true)", html)

    def test_no_bridge_clears_previous_result_state(self):
        html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("$('rankA').textContent=''", html)
        self.assertIn("$('evidenceA').innerHTML=''", html)
        self.assertIn("No confirmed bridge. Try a different pair of taste signals.", html)


if __name__ == "__main__":
    unittest.main()
