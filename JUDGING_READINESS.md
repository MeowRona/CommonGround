# Judging readiness

Current Devpost judging criteria are equally weighted: Technological Implementation, Design, Potential Impact, and Quality of the Idea. The rules also note that judges are not required to run the project and may judge from the submitted description/media, so the final screenshots and text must make the Qloo-specific behavior visible without relying on a code walkthrough.

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
- public HTTP/CORS/runtime-config tests and a live preflight that exercises search, bridge and veto end to end.

Still required:
- real hackathon-key smoke test;
- exact live response/explainability verification;
- live Render API deployment and Pages runtime configuration.

## Design

Current interaction focuses on one bridge movie and two visible routes instead of three generic recommendation cards.

The mathematical policy and trace are secondary details; the main user action is bilateral feedback.

The final Pages frontend loads immediately even when the free API is asleep, shows the backend wake state, and unlocks live controls automatically after health succeeds.

## Potential impact

The demonstrated use case is repeated two-person movie choice for friends, roommates, or partners where an average-profile recommender can hide a weak option for one participant. The project does not claim a market-size, satisfaction lift, or superiority result without user testing.

## Quality of idea

The distinctive part is the combination of:
- cross-domain Qloo interests;
- same-pool evaluation for both people;
- worse-side rank protection;
- feedback-driven exclusion and one adaptive second round;
- explicit willingness to return “no confirmed bridge”.

The public diagnostic makes the non-obvious part inspectable: the deterministic main fixture has zero overlap between A's and B's naive top-3 lists, yet the shared-pool process still recovers a bridge. The final live media should capture the equivalent Qloo-backed state.

## Hard blockers before final submission

1. Qloo API key.
2. Live schema smoke test.
3. Deploy the prepared Render Free API.
4. Point the existing Pages frontend at the verified live API and pass `submission_preflight.py`.
5. Final live screenshots, human review and Devpost submission.
