from __future__ import annotations

import json
import shutil
from pathlib import Path

from agent import CommonGroundAgent
from qloo_client import FixtureQlooClient


ROOT = Path(__file__).resolve().parent

SCENARIOS = [
    {
        "id": "future-meets-romance",
        "label": "Blade Runner + Aphex Twin  ×  Amelie + Daft Punk",
        "profile_a": ["Blade Runner", "Aphex Twin"],
        "profile_b": ["Amelie", "Daft Punk"],
    },
    {
        "id": "rhythm-meets-intimacy",
        "label": "Whiplash + Radiohead  ×  Her + Daft Punk",
        "profile_a": ["Whiplash", "Radiohead"],
        "profile_b": ["Her", "Daft Punk"],
    },
]


def build() -> None:
    agent = CommonGroundAgent(FixtureQlooClient())
    payload = []
    for scenario in SCENARIOS:
        first = agent.run(scenario["profile_a"], scenario["profile_b"])
        rejected = [first["bridge"]["entity_id"]] if first.get("bridge") else []
        second = agent.run(
            scenario["profile_a"],
            scenario["profile_b"],
            round_no=2,
            rejected_ids=rejected,
        )
        payload.append({**scenario, "rounds": [first, second]})

    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "demo_scenarios.json").write_text(
        json.dumps({"scenarios": payload}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    shutil.copyfile(ROOT / "static" / "index.html", docs / "index.html")
    (docs / ".nojekyll").touch()


if __name__ == "__main__":
    build()
