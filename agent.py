from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from qloo_client import CandidateEvaluation, CandidateRef, ResolvedInterest
from ranking import rank_bridges


MAX_ROUNDS = 2


class BridgeClient(Protocol):
    mode: str

    def resolve_interests(self, names: list[str]) -> list[ResolvedInterest]: ...

    def discover_candidates(
        self,
        interests: list[ResolvedInterest],
        *,
        take: int,
        exclude_ids: list[str],
    ) -> list[CandidateRef]: ...

    def evaluate_candidates(
        self,
        interests: list[ResolvedInterest],
        candidate_ids: list[str],
    ) -> list[CandidateEvaluation]: ...


@dataclass(frozen=True)
class AgentStep:
    name: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "detail": self.detail}


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
    if not 1 <= len(out) <= 3:
        raise ValueError("Each person must provide 1 to 3 taste signals")
    return out


def _stable_union(a: list[CandidateRef], b: list[CandidateRef]) -> list[CandidateRef]:
    seen: set[str] = set()
    rows: list[CandidateRef] = []
    for row in a + b:
        if row.entity_id not in seen:
            seen.add(row.entity_id)
            rows.append(row)
    return rows


class CommonGroundAgent:
    """Two-round bridge finder with explicit veto and same-pool evaluation."""

    def __init__(self, client: BridgeClient):
        self.client = client

    def run(
        self,
        profile_a: object,
        profile_b: object,
        *,
        round_no: int = 1,
        rejected_ids: object = None,
    ) -> dict:
        a_names = normalize_profile(profile_a)
        b_names = normalize_profile(profile_b)
        a_interests = self.client.resolve_interests(a_names)
        b_interests = self.client.resolve_interests(b_names)
        return self.run_resolved(
            a_interests,
            b_interests,
            round_no=round_no,
            rejected_ids=rejected_ids,
        )

    def run_resolved(
        self,
        a_interests: list[ResolvedInterest],
        b_interests: list[ResolvedInterest],
        *,
        round_no: int = 1,
        rejected_ids: object = None,
    ) -> dict:
        if round_no < 1 or round_no > MAX_ROUNDS:
            raise ValueError(f"round_no must be between 1 and {MAX_ROUNDS}")
        if not 1 <= len(a_interests) <= 3 or not 1 <= len(b_interests) <= 3:
            raise ValueError("Each person must provide 1 to 3 resolved interests")
        rejected = [] if rejected_ids is None else rejected_ids
        if not isinstance(rejected, list) or not all(isinstance(x, str) for x in rejected):
            raise ValueError("rejected_ids must be a list of entity IDs")
        rejected = list(dict.fromkeys(x for x in rejected if x))

        trace: list[AgentStep] = [
            AgentStep(
                "Resolve real taste entities",
                f"Resolved {len(a_interests)} interest(s) for A and {len(b_interests)} for B.",
            )
        ]

        take = 20 if round_no == 1 else 40
        candidates_a = self.client.discover_candidates(
            a_interests, take=take, exclude_ids=rejected
        )
        candidates_b = self.client.discover_candidates(
            b_interests, take=take, exclude_ids=rejected
        )
        pool = _stable_union(candidates_a, candidates_b)
        trace.append(
            AgentStep(
                "Build a shared candidate pool",
                f"Round {round_no}: unioned {len(pool)} movie candidate(s) from both searches"
                + (f" after excluding {len(rejected)} vetoed/known item(s)." if rejected else "."),
            )
        )

        candidate_ids = [row.entity_id for row in pool]
        eval_a = self.client.evaluate_candidates(a_interests, candidate_ids)
        eval_b = self.client.evaluate_candidates(b_interests, candidate_ids)
        trace.append(
            AgentStep(
                "Evaluate the same movies for both people",
                f"Measured {len(eval_a)} candidate(s) for A and {len(eval_b)} for B on the identical pool.",
            )
        )

        bridges = rank_bridges(eval_a, eval_b, limit=3)
        if not bridges:
            return {
                "mode": self.client.mode,
                "status": "no_bridge",
                "round": round_no,
                "max_rounds": MAX_ROUNDS,
                "profiles": {
                    "a": [x.__dict__ for x in a_interests],
                    "b": [x.__dict__ for x in b_interests],
                },
                "bridge": None,
                "alternatives": [],
                "policy": "minimize worse rank, then total rank; missing evaluation stays unknown",
                "trace": [step.as_dict() for step in trace],
            }

        trace.append(
            AgentStep(
                "Propose one cultural bridge",
                "Selected the movie with the best worst-side rank; ties use the sum of both ranks.",
            )
        )
        return {
            "mode": self.client.mode,
            "status": "proposal",
            "round": round_no,
            "max_rounds": MAX_ROUNDS,
            "profiles": {
                "a": [x.__dict__ for x in a_interests],
                "b": [x.__dict__ for x in b_interests],
            },
            "bridge": bridges[0].as_dict(),
            "alternatives": [row.as_dict() for row in bridges[1:]],
            "policy": "minimize worse rank, then total rank; missing evaluation stays unknown",
            "trace": [step.as_dict() for step in trace],
        }
