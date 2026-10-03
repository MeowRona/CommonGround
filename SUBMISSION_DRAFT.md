# Devpost submission draft — not final

## Project name

CommonGround

## Elevator pitch

An adaptive Qloo-powered agent that finds one movie two different tastes can reach for different reasons — and lets either person veto the compromise.

## Inspiration

Recommendation systems are good at answering “what might this person like?” but a shared decision is different. A high score for one person can hide a poor option for the other, and simply intersecting two short recommendation lists can miss strong candidates that sit just outside one person's initial window.

CommonGround treats the problem as a two-person decision process rather than one averaged profile.

## What it does

Two people provide a few films or artists they like. CommonGround uses Qloo to resolve those cultural entities and discover movie candidates independently for each person.

Instead of ranking only the intersection, it unions both candidate sets and asks Qloo to evaluate that **same movie pool** separately for A and B.

CommonGround then minimizes the worse of the two ranks and proposes one bridge movie.

Each person responds:

- **Want to try**
- **Already know it**
- **Not for me**

Any veto or already-known result is excluded. The agent widens the search once and tries again. After two rounds it stops rather than forcing a compromise.

## How Qloo is used

The intended live flow is:

`taste names -> /search -> profile A/B entity IDs -> /v2/insights discovery -> union candidate IDs -> /v2/insights with filter.results.entities for A -> same pool for B -> fairness rank -> feedback -> optional second search`

Live requests use `feature.explainability=true`. The UI shows only evidence that can be tied back to Qloo's explainability payload; otherwise it says no explanation is available.

## Ranking

CommonGround does not treat Qloo affinity as “probability this person will like the movie”. The decision policy uses result order within each query context.

For candidates measured on both sides:

1. minimize the worse rank;
2. break ties with the sum of both ranks.

Missing evaluation is treated as unknown, not zero.

## Agent behavior

The agent makes concrete decisions:

- which candidate pool to construct;
- whether a movie has complete evidence on both sides;
- which bridge to propose;
- whether user feedback requires an exclusion;
- whether to widen retrieval for the second and final round;
- when to stop with no confirmed compromise.

## Public preview

- Preview: https://meowrona.github.io/CommonGround/
- Source: https://github.com/MeowRona/CommonGround

The current public Pages build is a clearly labelled fixture preview generated from the Python decision engine. It is intentionally not described as live Qloo output while the hackathon API key is pending.

## Before final submission

- validate real competition-key responses;
- verify exact explainability structure;
- deploy the live Python backend for free;
- update screenshots and public demo URL;
- re-check rules and final statements against the shipped build.

