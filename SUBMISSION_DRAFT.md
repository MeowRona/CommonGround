# Devpost submission draft — do not submit yet

## Project name

CommonGround

## Tagline

An adaptive taste agent that protects the less enthusiastic person.

## Short description

CommonGround helps two people find a cultural choice they can both genuinely enjoy. Instead of merging their tastes into one average profile, the agent grounds each person independently with Qloo, inspects the overlap, and finds shared candidates whose **weaker-person affinity** is still strongest.

That changes both the optimization target and the agent behavior. A recommendation with a very high score for one person and a poor score for the other is not treated as a good compromise just because its average looks respectable. If the first candidate window produces no useful bridge, the agent widens retrieval once without changing either person's stated tastes. The interface keeps both affinities and the decision trace visible.

The intended Qloo flow is:

`taste names -> /search entity IDs -> /v2/insights per profile -> compare overlap -> adapt retrieval if weak -> fairness-first rank -> visible explanation`

The local MVP currently uses deterministic demo affinities so the ranking, UI, error handling, and product interaction can be tested before an entrant API key exists. It must **not** be submitted or described as Qloo-powered until the live smoke test and mapping are complete.

## Key features

- two independent taste profiles;
- cross-domain target selection;
- visible per-person affinities instead of an opaque combined score;
- fairness-first rank based primarily on the weaker affinity;
- adaptive retrieval when the first overlap is weak;
- inspectable agent trace rather than hidden chain-of-thought;
- Qloo explainability requested in live mode so influential taste entities can be surfaced when available;
- no account/profile database or personal identifiers required by the MVP;
- no paid LLM dependency;
- lightweight Python standard-library backend and vanilla browser UI.

## Why Qloo is essential

CommonGround needs structured cross-domain cultural affinity, not generic text generation. Qloo is intended to supply entity resolution, profile-specific affinity ranking, and recommendation explainability. The application layer then solves a different problem: decide whether two Qloo-grounded result sets contain adequate common ground, adapt retrieval when they do not, and rank the final bridge fairly.

## Before this text becomes final

- replace all demo data with verified live Qloo results;
- document the exact live entity types/domains used;
- add one concrete live A/B example showing that different profiles change Qloo rankings;
- confirm the hosted demo and public repository URLs;
- remove this warning and verify every statement against the shipped build.

## Public links

- Demo preview: https://meowrona.github.io/CommonGround/
- Public source: https://github.com/MeowRona/CommonGround

The current public preview is intentionally labelled demo-data mode. Do not final-submit until the live Qloo adapter is validated with the hackathon API key.
