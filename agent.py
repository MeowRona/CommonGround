from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from qloo_client import CandidateAffinity
from ranking import rank_common_ground


class RecommendationClient(Protocol):
    mode: str

    def recommend_for_profile(
        self, seeds: list[str], target_domain: str, limit: int = 8
    ) -> list[CandidateAffinity]: ...


@dataclass(frozen=True)
class AgentStep:
    name: str
    detail: str
    status: str = "done"

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "detail": self.detail, "status": self.status}


def normalize_profile(values: object) -> list[str]:
    if not isinstance(values, list):
        raise ValueError("Each profile must be a list of taste signals")

    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        if not isinstance(raw, str):
            raise ValueError("Taste signals must be text")
        value = " ".join(raw.strip().split())
        if not value:
            continue
        if len(value) > 100:
            raise ValueError("Each taste signal must be at most 100 characters")
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            out.append(value)

    if not out:
        raise ValueError("Each profile needs at least one taste signal")
    if len(out) > 8:
        raise ValueError("Use at most 8 taste signals per person")
    return out


class CommonGroundAgent:
    """Adaptive decision workflow built around a Qloo-compatible client."""

    def __init__(self, client: RecommendationClient):
        self.client = client

    def run(
        self,
        profile_a: object,
        profile_b: object,
        target_domain: str,
        result_limit: int = 3,
    ) -> dict:
        a = normalize_profile(profile_a)
        b = normalize_profile(profile_b)
        domain = target_domain.strip().lower()
        if result_limit < 1 or result_limit > 10:
            raise ValueError("result_limit must be between 1 and 10")

        trace: list[AgentStep] = [
            AgentStep(
                "Interpret profiles",
                f"Kept {len(a)} unique signal(s) for A and {len(b)} for B.",
            )
        ]

        first_take = 8
        a_results = self.client.recommend_for_profile(a, domain, limit=first_take)
        b_results = self.client.recommend_for_profile(b, domain, limit=first_take)
        trace.append(
            AgentStep(
                "Ground each profile independently",
                f"Retrieved {len(a_results)} candidates for A and {len(b_results)} for B.",
            )
        )

        ranked = rank_common_ground(a_results, b_results, limit=result_limit)
        initial_floor = ranked[0].floor if ranked else 0.0
        shared_count = len({r.entity_id for r in a_results} & {r.entity_id for r in b_results})
        trace.append(
            AgentStep(
                "Stress-test the overlap",
                f"Found {shared_count} shared candidate(s); best weaker-person affinity is {initial_floor:.0%}.",
            )
        )

        expanded = False
        if not ranked or initial_floor < 0.58:
            expanded = True
            second_take = 20
            a_results = self.client.recommend_for_profile(a, domain, limit=second_take)
            b_results = self.client.recommend_for_profile(b, domain, limit=second_take)
            ranked = rank_common_ground(a_results, b_results, limit=result_limit)
            trace.append(
                AgentStep(
                    "Adapt retrieval",
                    "The first pass was weak, so the agent widened retrieval once without changing either profile.",
                )
            )

        top_floor = ranked[0].floor if ranked else 0.0
        if top_floor >= 0.75:
            band = "strong bridge"
        elif top_floor >= 0.60:
            band = "workable bridge"
        elif ranked:
            band = "exploratory bridge"
        else:
            band = "no shared candidate"

        trace.append(
            AgentStep(
                "Choose common ground",
                (
                    f"Ranked {len(ranked)} result(s) fairness-first; outcome is {band}."
                    if ranked
                    else "No shared candidate survived the current retrieval window."
                ),
            )
        )

        return {
            "mode": self.client.mode,
            "target_domain": domain,
            "profiles": {"a": a, "b": b},
            "results": [r.as_dict() for r in ranked],
            "agent": {
                "workflow": "observe -> retrieve -> compare -> adapt if weak -> decide",
                "expanded_search": expanded,
                "bridge_band": band,
                "trace": [step.as_dict() for step in trace],
            },
            "method": "72% weaker-person affinity + 20% mean + 8% balance",
        }

