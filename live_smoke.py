from __future__ import annotations

import argparse
import json
import os
import unicodedata
from pathlib import Path

from agent import CommonGroundAgent
from qloo_client import QlooTransport, RealQlooClient


PROFILE_A = ["Blade Runner", "Aphex Twin"]
PROFILE_B = ["Amelie", "Daft Punk"]
PROFILE_A_TYPES = ["urn:entity:movie", "urn:entity:artist"]
PROFILE_B_TYPES = ["urn:entity:movie", "urn:entity:artist"]


class RecordingTransport:
    """Record request params + response JSON, never headers or secrets."""

    def __init__(self, transport: QlooTransport):
        self.transport = transport
        self.calls: list[dict] = []

    def get_json(self, path: str, params: dict | None = None) -> dict:
        payload = self.transport.get_json(path, params)
        self.calls.append({"path": path, "params": params or {}, "response": payload})
        return payload


def comparable_name(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    asciiish = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join("".join(ch if ch.isalnum() else " " for ch in asciiish).split())


def resolve_exact(client: RealQlooClient, names: list[str], expected_types: list[str]):
    resolved = []
    for name, expected_type in zip(names, expected_types, strict=True):
        matches = [
            row
            for row in client.search_interests(name, 5)
            if comparable_name(row.name) == comparable_name(name)
            and row.entity_type == expected_type
        ]
        if not matches:
            raise RuntimeError(
                f"Expected a Qloo match for {name!r} as {expected_type}, got none"
            )
        resolved.append(matches[0])
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Qloo live contract smoke test")
    parser.add_argument(
        "--write-fixture",
        action="store_true",
        help="write sanitized_live_fixture.json with query params and raw response JSON; no API headers/key are recorded",
    )
    args = parser.parse_args(argv)

    if not os.environ.get("QLOO_API_KEY"):
        print("BLOCKED: QLOO_API_KEY is not set.")
        return 2

    recorder = RecordingTransport(QlooTransport())
    client = RealQlooClient(recorder)

    try:
        a = resolve_exact(client, PROFILE_A, PROFILE_A_TYPES)
        b = resolve_exact(client, PROFILE_B, PROFILE_B_TYPES)
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

        if args.write_fixture:
            output = Path(__file__).resolve().parent / "sanitized_live_fixture.json"
            output.write_text(
                json.dumps(
                    {
                        "note": "Qloo smoke fixture: request query params + API response JSON only. X-Api-Key is never recorded.",
                        "calls": recorder.calls,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(f"fixture: wrote {output.name} ({len(recorder.calls)} call(s))")

        print("PASS: live Qloo bridge flow completed without exposing the API key.")
        return 0
    except (ValueError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
