# CommonGround — submission concept

## Concrete idea

When two people choose a movie, restaurant, music-related place, or activity, recommendation systems usually optimize for one profile or an average profile. CommonGround instead asks: **what is the strongest cultural bridge that neither person has to sacrifice for?**

Each participant provides a few real taste signals. Qloo supplies candidate affinities for each profile. CommonGround joins matching candidates and ranks them primarily by the lower of the two affinities, then uses mean affinity and balance as tie-break information. If the initial overlap is absent or weak, the agent autonomously widens retrieval once instead of silently returning a poor compromise.

## Advantage

The Qloo graph is not decoration. It provides the cross-domain cultural relationships that make a bridge possible even when the two seed lists do not overlap directly. Qloo explainability can also expose which input interests influenced a live recommendation. The visible A/B affinities and the agent trace make the compromise inspectable instead of hiding it behind an LLM sentence.

## Minimum contest scope

1. Two taste profiles.
2. One selectable target domain.
3. Real Qloo Insights results for each profile.
4. Join candidates by stable entity identity.
5. Fairness-first ranking with visible per-person affinity.
6. Adaptive second retrieval pass when the first common-ground window is weak.
7. Three recommendations plus an inspectable agent decision trace.
8. Public, free hosted demo plus public repository and instructions.

No accounts, database, payments, chat system, vector database, image generation, or paid LLM are needed.

## Required submission materials

- working hosted application;
- public GitHub/GitLab/Bitbucket repository;
- all source/assets/run instructions;
- visible open-source license;
- English project description;
- final Devpost form fields/declarations.

## Expected cost

- software/dependencies: €0;
- Qloo hackathon API: expected €0 for the competition key;
- local MVP: €0;
- hosting: must use a genuinely free option or the project is dropped under this test's constraints.

## Human involvement

- request the Qloo hackathon key and accept any account/contest terms personally;
- approve public repository/hosting before publication;
- review final description and legal declarations;
- submit manually.

Estimated active human work after the technical package is ready: well under 1 hour if account/key access is straightforward, excluding waiting time for a key.
