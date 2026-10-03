from __future__ import annotations

from dataclasses import dataclass

from qloo_client import CandidateEvaluation


@dataclass(frozen=True)
class BridgeResult:
    entity_id: str
    name: str
    rank_a: int
    rank_b: int
    worst_rank: int
    rank_sum: int
    evidence_a: tuple[str, ...] = ()
    evidence_b: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "rank_a": self.rank_a,
            "rank_b": self.rank_b,
            "worst_rank": self.worst_rank,
            "rank_sum": self.rank_sum,
            "evidence_a": list(self.evidence_a),
            "evidence_b": list(self.evidence_b),
            "explanation": (
                f"Same candidate evaluated for both profiles: A ranks it #{self.rank_a}, "
                f"B ranks it #{self.rank_b}."
            ),
        }


def rank_bridges(
    evaluations_a: list[CandidateEvaluation],
    evaluations_b: list[CandidateEvaluation],
    *,
    limit: int = 3,
) -> list[BridgeResult]:
    """Minimize the worse rank first, then the total rank.

    Missing evaluation on either side means unknown, not zero, so the candidate
    is not ranked as confirmed common ground.
    """
    a_by_id = {row.entity_id: row for row in evaluations_a}
    b_by_id = {row.entity_id: row for row in evaluations_b}
    rows: list[BridgeResult] = []
    for entity_id in a_by_id.keys() & b_by_id.keys():
        a = a_by_id[entity_id]
        b = b_by_id[entity_id]
        rows.append(
            BridgeResult(
                entity_id=entity_id,
                name=a.name,
                rank_a=a.rank,
                rank_b=b.rank,
                worst_rank=max(a.rank, b.rank),
                rank_sum=a.rank + b.rank,
                evidence_a=a.evidence,
                evidence_b=b.evidence,
            )
        )
    rows.sort(
        key=lambda row: (
            row.worst_rank,
            row.rank_sum,
            row.name.casefold(),
            row.entity_id,
        )
    )
    return rows[:limit]
