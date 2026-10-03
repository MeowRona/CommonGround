from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict

from agent import CommonGroundAgent
from qloo_client import RealQlooClient


PROFILE_A = ["Blade Runner", "Aphex Twin"]
PROFILE_B = ["Amelie", "Daft Punk"]


def main() -> int:
    if not os.environ.get("QLOO_API_KEY"):
        print("BLOCKED: QLOO_API_KEY is not set.")
        return 2

    client = RealQlooClient()

    try:
        a = client.resolve_interests(PROFILE_A)
        b = client.resolve_interests(PROFILE_B)
        print("resolve:A", [(x.name, x.entity_type) for x in a])
        print("resolve:B", [(x.name, x.entity_type) for x in b])

        candidates_a = client.discover_candidates(a, take=20, exclude_ids=[])
        candidates_b = client.discover_candidates(b, take=20, exclude_ids=[])
        union_ids = list(dict.fromkeys([x.entity_id for x in candidates_a + candidates_b]))
        print(
            "discover:",
            {"A": len(candidates_a), "B": len(candidates_b), "union": len(union_ids)},
        )
        if not union_ids:
            raise RuntimeError("Qloo returned no movie candidates")

        eval_a = client.evaluate_candidates(a, union_ids)
        eval_b = client.evaluate_candidates(b, union_ids)
        print("same_pool:", {"A": len(eval_a), "B": len(eval_b)})
        if not eval_a or not eval_b:
            raise RuntimeError("Same-pool evaluation returned no rows for one profile")

        bridge = CommonGroundAgent(client).run_resolved(a, b)
        if not bridge.get("bridge"):
            raise RuntimeError("No bridge survived complete evaluation")

        first = bridge["bridge"]
        print(
            "bridge:",
            json.dumps(
                {
                    "name": first["name"],
                    "rank_a": first["rank_a"],
                    "rank_b": first["rank_b"],
                    "evidence_a": first["evidence_a"],
                    "evidence_b": first["evidence_b"],
                },
                ensure_ascii=False,
            ),
        )

        second = CommonGroundAgent(client).run_resolved(
            a,
            b,
            round_no=2,
            rejected_ids=[first["entity_id"]],
        )
        if second.get("bridge") and second["bridge"]["entity_id"] == first["entity_id"]:
            raise RuntimeError("filter.exclude.entities did not preserve the veto")
        print(
            "veto:",
            {
                "excluded": first["name"],
                "next": second.get("bridge", {}).get("name", "NO_BRIDGE"),
            },
        )

        evidence_count = len(first["evidence_a"]) + len(first["evidence_b"])
        if evidence_count:
            print("explainability: evidence mapped for the proposed bridge")
        else:
            print("explainability: WARNING — no per-result input evidence mapped")

        print("PASS: live Qloo bridge flow completed without exposing the API key.")
        return 0
    except (ValueError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
