# Judging readiness

This file maps the current build to the four equally weighted Qloo judging dimensions from the reviewed contest rules. It is an evidence checklist, not a score prediction.

## Technological Implementation

Ready locally:
- explicit Qloo hackathon transport and documented request builders;
- separate profile retrieval and stable-ID intersection architecture;
- fairness-first reconciliation algorithm;
- adaptive second retrieval pass when overlap is weak;
- Qloo explainability requested in the live Insights call;
- 15 unit tests plus current local HTTP smoke test;
- no runtime third-party dependencies or hidden paid model requirement.

Remaining proof:
- real `/search` and `/v2/insights` responses after API-key approval;
- verified live response parser and sanitized fixture;
- public preview deployed and reachable over HTTPS.

## Design

Ready locally:
- responsive single-page flow with clear A/B profiles and target domain;
- visible weaker-person affinity rather than opaque aggregate score;
- visible agent decision trace;
- clear demo/live-state labeling;
- escaped dynamic values and basic browser security headers.

Remaining proof:
- final review using live Qloo entity names/explainability;
- final public URL QA after switching from static demo data to the live Qloo backend.

## Potential Impact

Concrete use case: repeated two-person choice problems where a recommendation optimized for only one profile or a simple average can hide a bad experience for one participant. The MVP demonstrates the decision policy directly rather than making an unsupported market-size claim.

## Quality of the Idea

The distinctive mechanism is the max-min-style fairness objective plus adaptive retrieval: Qloo supplies individual cultural affinity; CommonGround decides when the overlap is good enough and optimizes for a bridge that remains acceptable to both people.

## Hard blockers before submission

1. entrant obtains the hackathon API key;
2. live adapter is validated instead of guessed;
3. entrant approves public repository and free hosting;
4. final rules/terms are rechecked before submission;
5. Devpost submission is manually reviewed and sent by the entrant.

