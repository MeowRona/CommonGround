# Live Qloo integration gate

The local product flow is ready. The following is intentionally blocked until the entrant receives a current hackathon API key.

## Official contract already verified

- Hackathon base URL: `https://hackathon.api.qloo.com`
- Authentication header: `X-Api-Key`
- Entity lookup: `GET /search`
- Search text parameter: `query`
- Search count parameter: `take`
- Recommendation endpoint: `GET /v2/insights`
- Required target parameter: `filter.type`
- Taste entity signal: `signal.interests.entities` as comma-separated Qloo entity IDs
- Explainability: `feature.explainability=true` so each recommendation can expose which input entities contributed
- Result count: `take` (1–50)
- Relevant target types for this MVP include `urn:entity:movie`, `urn:entity:artist`, and `urn:entity:place`.
- Do not use legacy `/recs` or `/recommendations` endpoints.

Official references:
- https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide
- https://docs.qloo.com/reference/get-search
- https://docs.qloo.com/reference/insights-api-deep-dive

## One small live smoke-test sequence

1. Set `QLOO_API_KEY` locally; never commit it.
2. Resolve 2–4 known taste names with `/search` and inspect the real JSON response shape.
3. Send one `/v2/insights` GET using the returned IDs and one supported `filter.type`.
4. Record only the fields needed for stable entity ID, display name and affinity.
5. Inspect the per-result `query.explainability` structure and map only verified contribution fields.
6. Map those verified fields in `RealQlooClient.recommend_for_profile()`.
7. Run both profiles through the same target domain and verify that the CommonGround join/rank works on live IDs.
8. Add a fixture based on the response shape with any sensitive key/header removed, then rerun unit tests.

## Stop conditions

Stop rather than guessing if:
- the key is not approved;
- a documented parameter returns 403/unsupported for the intended entity type;
- the live response lacks a stable candidate identifier or affinity needed for fair comparison;
- live API terms or contest rules change materially;
- free external hosting cannot be arranged.
