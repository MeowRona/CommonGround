from __future__ import annotations

import argparse
import json
import os
import threading
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
        self._lock = threading.Lock()

    def get_json(self, path: str, params: dict | None = None) -> dict:
        payload = self.transport.get_json(path, params)
        with self._lock:
            self.calls.append({"path": path, "params": params or {}, "response": payload})
        return payload

    def snapshot(self) -> list[dict]:
        with self._lock:
            return list(self.calls)


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


def validate_round_contract(
    calls: list[dict], *, expected_discovery_take: int, rejected_id: str | None = None
) -> dict:
    insights = [call for call in calls if call.get("path") == "/v2/insights"]
    discovery = [call for call in insights if "filter.results.entities" not in call.get("params", {})]
    evaluation = [call for call in insights if "filter.results.entities" in call.get("params", {})]

    if len(discovery) != 2 or len(evaluation) != 2:
        raise RuntimeError(
            f"Expected 2 discovery + 2 same-pool Insights calls, got {len(discovery)} + {len(evaluation)}"
        )
    if any(call["params"].get("take") != expected_discovery_take for call in discovery):
        raise RuntimeError("Discovery take does not match the agent round contract")

    pools = {call["params"].get("filter.results.entities", "") for call in evaluation}
    if len(pools) != 1 or not next(iter(pools), ""):
        raise RuntimeError("A and B were not evaluated against one identical non-empty movie pool")
    pool_ids = [value for value in next(iter(pools)).split(",") if value]
    if len(pool_ids) > 50:
        raise RuntimeError("Same-pool evaluation exceeded the Qloo 50-result request limit")

    if rejected_id:
        if rejected_id in pool_ids:
            raise RuntimeError("Rejected movie leaked back into the second-round evaluation pool")
        for call in discovery:
            excluded = str(call["params"].get("filter.exclude.entities", "")).split(",")
            if rejected_id not in excluded:
                raise RuntimeError("Second-round discovery did not send filter.exclude.entities")

    return {
        "discovery_calls": len(discovery),
        "evaluation_calls": len(evaluation),
        "same_pool_size": len(pool_ids),
    }


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

        round1_start = len(recorder.snapshot())
        bridge = CommonGroundAgent(client).run_resolved(a, b)
        if not bridge.get("bridge"):
            raise RuntimeError("No bridge survived complete evaluation")
        round1_calls = recorder.snapshot()[round1_start:]
        round1_contract = validate_round_contract(
            round1_calls, expected_discovery_take=20
        )
        print("round1_contract:", round1_contract)
        print("round1_diagnostics:", bridge.get("diagnostics", {}))

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

        round2_start = len(recorder.snapshot())
        second = CommonGroundAgent(client).run_resolved(
            a,
            b,
            round_no=2,
            rejected_ids=[first["entity_id"]],
        )
        round2_calls = recorder.snapshot()[round2_start:]
        round2_contract = validate_round_contract(
            round2_calls,
            expected_discovery_take=25,
            rejected_id=first["entity_id"],
        )
        print("round2_contract:", round2_contract)
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
                        "calls": recorder.snapshot(),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(f"fixture: wrote {output.name} ({len(recorder.snapshot())} call(s))")

        print("PASS: live Qloo bridge flow completed without exposing the API key.")
        return 0
    except (ValueError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
