from __future__ import annotations

from dataclasses import dataclass

from qloo_client import CandidateAffinity


@dataclass(frozen=True)
class CommonGroundResult:
    entity_id: str
    name: str
    domain: str
    affinity_a: float
    affinity_b: float
    floor: float
    mean: float
    balance: float
    score: float
    evidence_a: tuple[str, ...] = ()
    evidence_b: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "domain": self.domain,
            "affinity_a": round(self.affinity_a, 4),
            "affinity_b": round(self.affinity_b, 4),
            "floor": round(self.floor, 4),
            "mean": round(self.mean, 4),
            "balance": round(self.balance, 4),
            "score": round(self.score, 4),
            "evidence_a": list(self.evidence_a),
            "evidence_b": list(self.evidence_b),
            "explanation": (
                f"Both profiles stay above {self.floor:.0%} affinity; "
                f"A is {self.affinity_a:.0%}, B is {self.affinity_b:.0%}."
            ),
        }


def rank_common_ground(
    results_a: list[CandidateAffinity],
    results_b: list[CandidateAffinity],
    limit: int = 3,
) -> list[CommonGroundResult]:
    """Rank shared candidates with the weaker profile as the primary signal."""
    a_by_id = {r.entity_id: r for r in results_a}
    b_by_id = {r.entity_id: r for r in results_b}

    joined: list[CommonGroundResult] = []
    for entity_id in a_by_id.keys() & b_by_id.keys():
        a = a_by_id[entity_id]
        b = b_by_id[entity_id]
        floor = min(a.affinity, b.affinity)
        mean = (a.affinity + b.affinity) / 2.0
        balance = 1.0 - abs(a.affinity - b.affinity)

        # Fairness first: the minimum affinity dominates. Mean and balance only refine ties.
        score = 0.72 * floor + 0.20 * mean + 0.08 * balance
        joined.append(
            CommonGroundResult(
                entity_id=entity_id,
                name=a.name,
                domain=a.domain,
                affinity_a=a.affinity,
                affinity_b=b.affinity,
                floor=floor,
                mean=mean,
                balance=balance,
                score=score,
                evidence_a=a.evidence,
                evidence_b=b.evidence,
            )
        )

    joined.sort(key=lambda r: (r.score, r.floor, r.mean, r.name), reverse=True)
    return joined[:limit]
