# Judging readiness

## Technological implementation

Implemented:
- explicit Qloo entity search/selection for ambiguous names;
- Qloo `/search` request path and entity resolution;
- independent `/v2/insights` movie discovery for two profiles;
- candidate union rather than short-list intersection;
- `filter.results.entities` same-pool evaluation for both people;
- `filter.exclude.entities` feedback loop;
- `feature.explainability=true`;
- rank-based two-person decision policy;
- maximum two-round agent loop;
- fail-closed parsing and unknown-data handling;
- fixture-generated public preview;
- automated tests for the decision and request contracts.

Still required:
- real hackathon-key smoke test;
- exact live response/explainability verification;
- live Render API deployment and Pages runtime configuration.

## Design

Current interaction focuses on one bridge movie and two visible routes instead of three generic recommendation cards.

The mathematical policy and trace are secondary details; the main user action is bilateral feedback.

## Potential impact

The demonstrated use case is repeated two-person choice where an average-profile recommender can hide a bad experience for one participant. The project does not claim a market-size or superiority result without user testing.

## Quality of idea

The distinctive part is the combination of:
- cross-domain Qloo interests;
- same-pool evaluation for both people;
- worse-side rank protection;
- feedback-driven exclusion and one adaptive second round;
- explicit willingness to return “no confirmed bridge”.

## Hard blockers before final submission

1. Qloo API key.
2. Live schema smoke test.
3. Deploy the prepared Render Free API.
4. Point the existing Pages frontend at the verified live API and pass `submission_preflight.py`.
5. Final live screenshots, human review and Devpost submission.
