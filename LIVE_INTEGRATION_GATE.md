# Live Qloo integration gate

Official references used for the request contract:

- https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide
- https://docs.qloo.com/reference/get-search
- https://docs.qloo.com/reference/insights-api-deep-dive

## Official request contract verified on 2026-10-03

- Hackathon base URL: `https://hackathon.api.qloo.com`
- Header: `X-Api-Key`
- Search: `GET /search`
- Search params: `query`, optional `types`, `take`
- Insights: `GET /v2/insights`
- Movie output: `filter.type=urn:entity:movie`
- Profile interests: `signal.interests.entities`
- Candidate re-scoring: `filter.results.entities`
- Exclusions: `filter.exclude.entities`
- Explainability: `feature.explainability=true`
- Result count: `take`, max 50

The current official docs describe per-result `query.explainability` as showing which input entities contributed to the recommendation, with normalized contribution scores. They also state that explainability may be unavailable and return a warning; that case must not generate a fabricated explanation.

## Smoke test once the key arrives

1. Resolve `Blade Runner`, `Aphex Twin`, `Amelie`, `Daft Punk` via `/search`.
2. Confirm stable IDs, names and supported entity types.
3. Discover 20 movies for each profile separately.
4. Build the union.
5. Evaluate the identical union for A using `filter.results.entities`.
6. Evaluate the identical union for B.
7. Inspect exact entity ID/name fields, ordering, `query.affinity` and `query.explainability` shape.
8. Run one exclusion with `filter.exclude.entities` and confirm the rejected movie cannot return.
9. Save a sanitized fixture with no API key or sensitive headers.
10. Run the entire automated suite plus HTTP smoke test in `COMMON_GROUND_MODE=live`.

## Stop conditions

Do not claim a live Qloo demo if:
- the key is unavailable;
- search ambiguity cannot be safely resolved;
- same-pool filtering does not behave as documented;
- result identity/order cannot be parsed reliably;
- explainability fields differ materially from assumptions;
- no genuinely free backend can keep the secret server-side.
