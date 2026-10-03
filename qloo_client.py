from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


HACKATHON_BASE_URL = "https://hackathon.api.qloo.com"

DOMAIN_TO_QLOO_TYPE = {
    "movie": "urn:entity:movie",
    "music": "urn:entity:artist",
    "restaurant": "urn:entity:place",
}


def build_search_params(query: str, take: int = 5) -> dict[str, str | int]:
    query = query.strip()
    if not query:
        raise ValueError("search query cannot be empty")
    if not 1 <= take <= 50:
        raise ValueError("take must be between 1 and 50")
    return {"query": query, "take": take}


def build_insights_params(
    entity_ids: Iterable[str], target_domain: str, take: int = 8
) -> dict[str, str | int]:
    ids = [entity_id.strip() for entity_id in entity_ids if entity_id.strip()]
    if not ids:
        raise ValueError("at least one Qloo entity ID is required")
    if target_domain not in DOMAIN_TO_QLOO_TYPE:
        raise ValueError(f"unsupported target domain: {target_domain}")
    if not 1 <= take <= 50:
        raise ValueError("take must be between 1 and 50")
    return {
        "filter.type": DOMAIN_TO_QLOO_TYPE[target_domain],
        "signal.interests.entities": ",".join(ids),
        "feature.explainability": "true",
        "take": take,
    }


@dataclass(frozen=True)
class CandidateAffinity:
    entity_id: str
    name: str
    affinity: float
    domain: str
    evidence: tuple[str, ...] = ()


DOMAIN_CANDIDATES: dict[str, tuple[str, ...]] = {
    "movie": (
        "Arrival",
        "Her",
        "The Grand Budapest Hotel",
        "Blade Runner 2049",
        "Everything Everywhere All at Once",
        "Whiplash",
        "Ex Machina",
        "The Social Network",
    ),
    "restaurant": (
        "Modern Japanese",
        "Levantine small plates",
        "Korean barbecue",
        "Neapolitan pizza",
        "Modern Polish",
        "Vietnamese street food",
        "Mediterranean seafood",
        "Vegetarian tasting menu",
    ),
    "music": (
        "James Blake",
        "Fred again..",
        "FKA twigs",
        "Tame Impala",
        "Kaytranada",
        "Caroline Polachek",
        "The xx",
        "Bonobo",
    ),
}


def _stable_unit_interval(text: str) -> float:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    raw = int.from_bytes(digest[:8], "big")
    return raw / float((1 << 64) - 1)


class MockQlooClient:
    """Demo-only affinity source. It never pretends to return live Qloo data."""

    mode = "demo"

    def recommend_for_profile(
        self, seeds: Iterable[str], target_domain: str, limit: int = 8
    ) -> list[CandidateAffinity]:
        clean_seeds = tuple(s.strip() for s in seeds if s.strip())
        if not clean_seeds:
            raise ValueError("At least one taste signal is required")
        if target_domain not in DOMAIN_CANDIDATES:
            raise ValueError(f"Unsupported demo domain: {target_domain}")

        rows: list[CandidateAffinity] = []
        for name in DOMAIN_CANDIDATES[target_domain]:
            # Deterministic synthetic affinity for functional UI/ranking tests only.
            parts = [_stable_unit_interval(f"{s.lower()}|{target_domain}|{name}") for s in clean_seeds]
            affinity = 0.42 + 0.56 * (sum(parts) / len(parts))
            rows.append(
                CandidateAffinity(
                    entity_id=f"demo:{target_domain}:{name.lower().replace(' ', '-')}",
                    name=name,
                    affinity=round(min(0.99, affinity), 4),
                    domain=target_domain,
                    evidence=clean_seeds[:3],
                )
            )
        return sorted(rows, key=lambda r: r.affinity, reverse=True)[:limit]


class QlooTransport:
    """Low-level verified transport only; endpoint-specific schema is kept separate."""

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
        try:
            with urlopen(request, timeout=15) as response:
                raw = response.read(8_000_001)
        except HTTPError as exc:
            raise RuntimeError(f"Qloo API returned HTTP {exc.code} for {path}") from exc
        except URLError as exc:
            raise RuntimeError(f"Qloo API is unreachable for {path}") from exc

        if len(raw) > 8_000_000:
            raise RuntimeError("Qloo API response exceeded the 8 MB safety limit")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Qloo API returned an invalid JSON response") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("Qloo API returned an unexpected top-level JSON value")
        return payload


class RealQlooClient:
    mode = "live"

    def __init__(self, transport: QlooTransport | None = None):
        self.transport = transport or QlooTransport()

    def recommend_for_profile(
        self, seeds: Iterable[str], target_domain: str, limit: int = 8
    ) -> list[CandidateAffinity]:
        # Request construction is already locked to the current official contract.
        # Response-field mapping remains gated until a real hackathon response can
        # be inspected without guessing its exact JSON structure.
        seed_list = [s.strip() for s in seeds if s.strip()]
        if not seed_list:
            raise ValueError("At least one taste signal is required")
        build_insights_params(["SCHEMA_SMOKE_TEST_REQUIRED"], target_domain, limit)
        raise RuntimeError(
            "Live Qloo Insights mapping is intentionally gated until the current "
            "official hackathon request/response schema is smoke-tested with the entrant's key."
        )
