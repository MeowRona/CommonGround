from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


HACKATHON_BASE_URL = "https://hackathon.api.qloo.com"
TARGET_TYPE = "urn:entity:movie"
SUPPORTED_INPUT_TYPES = {"urn:entity:movie", "urn:entity:artist"}
SEARCH_INPUT_TYPES = ("urn:entity:movie", "urn:entity:artist")


@dataclass(frozen=True)
class ResolvedInterest:
    entity_id: str
    name: str
    entity_type: str


@dataclass(frozen=True)
class CandidateRef:
    entity_id: str
    name: str
    domain: str = "movie"


@dataclass(frozen=True)
class CandidateEvaluation:
    entity_id: str
    name: str
    rank: int
    domain: str = "movie"
    affinity: float | None = None
    evidence: tuple[str, ...] = ()


def build_search_params(query: str, take: int = 5) -> dict[str, str | int]:
    query = query.strip()
    if not query:
        raise ValueError("search query cannot be empty")
    if not 1 <= take <= 50:
        raise ValueError("take must be between 1 and 50")
    return {
        "query": query,
        "types": ",".join(SEARCH_INPUT_TYPES),
        "take": take,
    }


def build_insights_params(
    interest_ids: Iterable[str],
    take: int = 20,
    *,
    result_ids: Iterable[str] = (),
    exclude_ids: Iterable[str] = (),
) -> dict[str, str | int]:
    interests = [x.strip() for x in interest_ids if x.strip()]
    if not interests:
        raise ValueError("at least one Qloo interest entity ID is required")
    if not 1 <= take <= 50:
        raise ValueError("take must be between 1 and 50")

    params: dict[str, str | int] = {
        "filter.type": TARGET_TYPE,
        "signal.interests.entities": ",".join(interests),
        "feature.explainability": "true",
        "sort_by": "affinity",
        "take": take,
    }
    results = [x.strip() for x in result_ids if x.strip()]
    excludes = [x.strip() for x in exclude_ids if x.strip()]
    if results:
        params["filter.results.entities"] = ",".join(results)
    if excludes:
        params["filter.exclude.entities"] = ",".join(excludes)
    return params


class QlooTransport:
    def __init__(self, api_key: str | None = None, base_url: str = HACKATHON_BASE_URL):
        self.api_key = api_key or os.environ.get("QLOO_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        if not self.api_key:
            raise RuntimeError("QLOO_API_KEY is not set")

    def get_json(self, path: str, params: dict[str, str | int | float] | None = None) -> dict:
        if not path.startswith("/"):
            raise ValueError("path must start with /")
        query = urlencode(params or {})
        url = f"{self.base_url}{path}" + (f"?{query}" if query else "")
        request = Request(url, headers={"X-Api-Key": self.api_key, "Accept": "application/json"})
        raw = b""
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                with urlopen(request, timeout=15) as response:
                    raw = response.read(8_000_001)
                last_error = None
                break
            except HTTPError as exc:
                last_error = exc
                if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                    raise RuntimeError(f"Qloo API returned HTTP {exc.code} for {path}") from exc
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                try:
                    delay = min(2.0, max(0.0, float(retry_after))) if retry_after else 0.35 * (attempt + 1)
                except ValueError:
                    delay = 0.35 * (attempt + 1)
                time.sleep(delay)
            except URLError as exc:
                last_error = exc
                if attempt == 2:
                    raise RuntimeError(f"Qloo API is unreachable for {path}") from exc
                time.sleep(0.25 * (attempt + 1))

        if last_error is not None:
            raise RuntimeError(f"Qloo API request failed for {path}") from last_error

        if len(raw) > 8_000_000:
            raise RuntimeError("Qloo API response exceeded the 8 MB safety limit")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Qloo API returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("Qloo API returned an unexpected top-level JSON value")
        return payload


def _entity_id(row: dict) -> str:
    for key in ("entity_id", "id"):
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _entity_name(row: dict) -> str:
    value = row.get("name")
    return value.strip() if isinstance(value, str) else ""


def _entity_types(row: dict) -> tuple[str, ...]:
    raw = row.get("types", row.get("type", ()))
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, list):
        return tuple(x for x in raw if isinstance(x, str))
    return ()


def _search_rows(payload: dict) -> list[dict]:
    rows = payload.get("results", [])
    if not isinstance(rows, list):
        raise RuntimeError("Unexpected Qloo /search response shape")
    return [row for row in rows if isinstance(row, dict)]


def _insight_rows(payload: dict) -> list[dict]:
    results = payload.get("results", {})
    if not isinstance(results, dict) or not isinstance(results.get("entities"), list):
        raise RuntimeError("Unexpected Qloo /v2/insights response shape")
    return [row for row in results["entities"] if isinstance(row, dict)]


def _affinity(row: dict) -> float | None:
    query = row.get("query")
    if isinstance(query, dict):
        value = query.get("affinity")
        if isinstance(value, (int, float)):
            return float(value)
    value = row.get("affinity")
    return float(value) if isinstance(value, (int, float)) else None


def _explainability_evidence(row: dict, interests: list[ResolvedInterest]) -> tuple[str, ...]:
    """Surface only input IDs that occur as exact strings in explainability metadata."""
    query = row.get("query")
    if not isinstance(query, dict) or "explainability" not in query:
        return ()

    strings: set[str] = set()

    def collect(value) -> None:
        if isinstance(value, str):
            strings.add(value)
        elif isinstance(value, dict):
            for key, child in value.items():
                if isinstance(key, str):
                    strings.add(key)
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(query.get("explainability"))
    names = [interest.name for interest in interests if interest.entity_id in strings]
    return tuple(names)


class RealQlooClient:
    mode = "live"

    def __init__(self, transport: QlooTransport | None = None):
        self.transport = transport or QlooTransport()

    def search_interests(self, query: str, take: int = 5) -> list[ResolvedInterest]:
        payload = self.transport.get_json("/search", build_search_params(query, take))
        candidates: list[ResolvedInterest] = []
        seen: set[str] = set()
        for row in _search_rows(payload):
            entity_id = _entity_id(row)
            entity_name = _entity_name(row)
            types = _entity_types(row)
            entity_type = next((t for t in types if t in SUPPORTED_INPUT_TYPES), "")
            if entity_id and entity_name and entity_type and entity_id not in seen:
                seen.add(entity_id)
                candidates.append(ResolvedInterest(entity_id, entity_name, entity_type))
        return candidates

    def resolve_interests(self, names: Iterable[str]) -> list[ResolvedInterest]:
        resolved: list[ResolvedInterest] = []
        for raw_name in names:
            name = raw_name.strip()
            candidates = self.search_interests(name, 5)

            exact = [x for x in candidates if x.name.casefold() == name.casefold()]
            if len(exact) == 1:
                resolved.append(exact[0])
            elif len(candidates) == 1:
                resolved.append(candidates[0])
            elif not candidates:
                raise ValueError(f"Qloo could not resolve interest: {name}")
            else:
                choices = ", ".join(x.name for x in candidates[:3])
                raise ValueError(f"Ambiguous interest '{name}'. Qloo matches: {choices}")
        return resolved

    def discover_candidates(
        self,
        interests: list[ResolvedInterest],
        *,
        take: int,
        exclude_ids: Iterable[str] = (),
    ) -> list[CandidateRef]:
        params = build_insights_params(
            [x.entity_id for x in interests], take, exclude_ids=exclude_ids
        )
        payload = self.transport.get_json("/v2/insights", params)
        rows: list[CandidateRef] = []
        for row in _insight_rows(payload):
            entity_id = _entity_id(row)
            name = _entity_name(row)
            if entity_id and name:
                rows.append(CandidateRef(entity_id, name))
        return rows

    def evaluate_candidates(
        self,
        interests: list[ResolvedInterest],
        candidate_ids: list[str],
    ) -> list[CandidateEvaluation]:
        if not candidate_ids:
            return []
        params = build_insights_params(
            [x.entity_id for x in interests],
            take=min(50, len(candidate_ids)),
            result_ids=candidate_ids,
        )
        payload = self.transport.get_json("/v2/insights", params)
        rows: list[CandidateEvaluation] = []
        for rank, row in enumerate(_insight_rows(payload), start=1):
            entity_id = _entity_id(row)
            name = _entity_name(row)
            if entity_id and name and entity_id in candidate_ids:
                rows.append(
                    CandidateEvaluation(
                        entity_id=entity_id,
                        name=name,
                        rank=rank,
                        affinity=_affinity(row),
                        evidence=_explainability_evidence(row, interests),
                    )
                )
        return rows


# Public preview / unit-test fixtures. Unknown text is rejected instead of receiving
# meaningless hash-based scores.
FIXTURE_ENTITY_IDS = {
    "Blade Runner": ("seed:blade-runner", "urn:entity:movie"),
    "Aphex Twin": ("seed:aphex-twin", "urn:entity:artist"),
    "Amelie": ("seed:amelie", "urn:entity:movie"),
    "Daft Punk": ("seed:daft-punk", "urn:entity:artist"),
    "Whiplash": ("seed:whiplash", "urn:entity:movie"),
    "Radiohead": ("seed:radiohead", "urn:entity:artist"),
    "Her": ("seed:her", "urn:entity:movie"),
}

FIXTURE_PROFILES: dict[tuple[str, ...], list[tuple[str, str, tuple[str, ...]]]] = {
    tuple(sorted(("Blade Runner", "Aphex Twin"))): [
        ("movie:blade-runner-2049", "Blade Runner 2049", ("Blade Runner",)),
        ("movie:ex-machina", "Ex Machina", ("Blade Runner",)),
        ("movie:arrival", "Arrival", ("Blade Runner",)),
        ("movie:drive", "Drive", ("Aphex Twin",)),
        ("movie:her", "Her", ("Aphex Twin",)),
        ("movie:social-network", "The Social Network", ("Aphex Twin",)),
        ("movie:whiplash", "Whiplash", ("Aphex Twin",)),
        ("movie:grand-budapest", "The Grand Budapest Hotel", ("Blade Runner",)),
    ],
    tuple(sorted(("Amelie", "Daft Punk"))): [
        ("movie:grand-budapest", "The Grand Budapest Hotel", ("Amelie",)),
        ("movie:her", "Her", ("Amelie", "Daft Punk")),
        ("movie:social-network", "The Social Network", ("Daft Punk",)),
        ("movie:arrival", "Arrival", ("Daft Punk",)),
        ("movie:drive", "Drive", ("Daft Punk",)),
        ("movie:blade-runner-2049", "Blade Runner 2049", ("Daft Punk",)),
        ("movie:ex-machina", "Ex Machina", ("Daft Punk",)),
        ("movie:whiplash", "Whiplash", ("Daft Punk",)),
    ],
    tuple(sorted(("Whiplash", "Radiohead"))): [
        ("movie:whiplash", "Whiplash", ("Whiplash",)),
        ("movie:social-network", "The Social Network", ("Radiohead",)),
        ("movie:arrival", "Arrival", ("Radiohead",)),
        ("movie:her", "Her", ("Radiohead",)),
        ("movie:ex-machina", "Ex Machina", ("Radiohead",)),
        ("movie:drive", "Drive", ("Radiohead",)),
        ("movie:grand-budapest", "The Grand Budapest Hotel", ("Whiplash",)),
        ("movie:blade-runner-2049", "Blade Runner 2049", ("Radiohead",)),
    ],
    tuple(sorted(("Her", "Daft Punk"))): [
        ("movie:her", "Her", ("Her",)),
        ("movie:arrival", "Arrival", ("Her",)),
        ("movie:ex-machina", "Ex Machina", ("Her", "Daft Punk")),
        ("movie:social-network", "The Social Network", ("Daft Punk",)),
        ("movie:drive", "Drive", ("Daft Punk",)),
        ("movie:blade-runner-2049", "Blade Runner 2049", ("Daft Punk",)),
        ("movie:grand-budapest", "The Grand Budapest Hotel", ("Her",)),
        ("movie:whiplash", "Whiplash", ("Daft Punk",)),
    ],
}


class FixtureQlooClient:
    mode = "fixture"

    def search_interests(self, query: str, take: int = 5) -> list[ResolvedInterest]:
        needle = query.strip().casefold()
        if not needle:
            return []
        rows: list[ResolvedInterest] = []
        for name, (entity_id, entity_type) in FIXTURE_ENTITY_IDS.items():
            if needle in name.casefold():
                rows.append(ResolvedInterest(entity_id, name, entity_type))
        return rows[:take]

    def resolve_interests(self, names: Iterable[str]) -> list[ResolvedInterest]:
        resolved: list[ResolvedInterest] = []
        for raw in names:
            name = raw.strip()
            canonical = next((k for k in FIXTURE_ENTITY_IDS if k.casefold() == name.casefold()), None)
            if canonical is None:
                raise ValueError(
                    f"'{name}' is not in the public preview fixture. Live Qloo search requires the hackathon API key."
                )
            entity_id, entity_type = FIXTURE_ENTITY_IDS[canonical]
            resolved.append(ResolvedInterest(entity_id, canonical, entity_type))
        return resolved

    @staticmethod
    def _rows(interests: list[ResolvedInterest]) -> list[tuple[str, str, tuple[str, ...]]]:
        key = tuple(sorted(x.name for x in interests))
        if key not in FIXTURE_PROFILES:
            raise ValueError("That taste combination is not available in the public preview fixture")
        return FIXTURE_PROFILES[key]

    def discover_candidates(
        self,
        interests: list[ResolvedInterest],
        *,
        take: int,
        exclude_ids: Iterable[str] = (),
    ) -> list[CandidateRef]:
        excluded = set(exclude_ids)
        return [
            CandidateRef(entity_id, name)
            for entity_id, name, _ in self._rows(interests)
            if entity_id not in excluded
        ][:take]

    def evaluate_candidates(
        self,
        interests: list[ResolvedInterest],
        candidate_ids: list[str],
    ) -> list[CandidateEvaluation]:
        wanted = set(candidate_ids)
        rows: list[CandidateEvaluation] = []
        for rank, (entity_id, name, evidence) in enumerate(self._rows(interests), start=1):
            if entity_id in wanted:
                rows.append(CandidateEvaluation(entity_id, name, rank, evidence=evidence))
        return rows
