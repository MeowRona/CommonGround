# Devpost submission draft — not final

## Project name

CommonGround

## Elevator pitch

An adaptive Qloo-powered agent that finds one movie two different tastes can reach for different reasons — and lets either person veto the compromise.

## Inspiration

Recommendation systems are good at answering “what might this person like?” but a shared decision is different. A high score for one person can hide a poor option for the other, and simply intersecting two short recommendation lists can miss strong candidates that sit just outside one person's initial window.

CommonGround treats the problem as a two-person decision process rather than one averaged profile.

The concrete use case is simple: two friends, roommates, or partners want to pick one movie together, but their taste signals come from different cultural corners. One person may describe themselves through a film, the other through an artist. CommonGround tries to find the third cultural object they can both plausibly approach — without letting one person's stronger match erase the other's weak one.

## What it does

Two people provide a few films or artists they like. CommonGround uses Qloo to resolve those cultural entities and discover movie candidates independently for each person.

Instead of ranking only the intersection, it unions both candidate sets and asks Qloo to evaluate that **same movie pool** separately for A and B.

CommonGround then minimizes the worse of the two ranks and proposes one bridge movie.

Each person responds:

- **Want to try**
- **Already know it**
- **Not for me**

Any veto or already-known result is excluded. The agent widens the search once (from 20 to 25 candidates per side, so the union remains at most 50 and can be evaluated as one identical pool) and tries again. After two rounds it stops rather than forcing a compromise.

## How Qloo is used

The intended live flow is:

`taste names -> /search -> profile A/B entity IDs -> /v2/insights discovery -> union candidate IDs -> /v2/insights with filter.results.entities for A -> same pool for B -> fairness rank -> feedback -> optional second search`

Live requests use `feature.explainability=true`. The UI shows only evidence that can be tied back to Qloo's explainability payload; otherwise it says no explanation is available.

Qloo is not a replaceable lookup layer here. It supplies the cross-domain entity graph, movie discovery from mixed movie/artist tastes, affinity-ordered evaluation of a controlled candidate pool, and per-result explainability metadata. Without that cultural graph, CommonGround would have no grounded way to move from heterogeneous tastes to a shared movie pool; replacing Qloo with an LLM prompt would turn the core bridge step back into generated guesswork.

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

## Challenges I ran into

The hardest part was defining what “common ground” should mean without pretending an affinity score is a probability of human enjoyment.

The first prototype intersected short recommendation lists and used synthetic percentage-like scores. That was easy to demo but conceptually weak: a useful bridge can sit just outside one person's short list, and two separate affinity queries are not automatically calibrated as personal satisfaction percentages.

The final design therefore changed the problem. It unions candidates discovered from both profiles, evaluates the **same candidate pool** for each person with Qloo, then ranks by the worse of the two positions. Missing evaluation stays unknown instead of becoming a negative preference.

A second challenge was making the workflow genuinely agentic without adding an LLM just for appearance. Feedback now changes the next API action: a rejected/known movie is excluded, retrieval widens once, and the agent has a hard stop after round two.

## Accomplishments that I am proud of

- The main fixture demonstrates a concrete failure of naive intersection: A's top 3 and B's top 3 have **zero overlap**, while same-pool evaluation still recovers a bridge (`Arrival`, A #3 / B #4 in the fixture).
- The public demo never invents a recommendation for arbitrary text while Qloo is unavailable.
- Selected tastes are stable Qloo entity IDs, not ambiguous free-text labels.
- Qloo explainability is surfaced only when the input entity ID is actually present in the response metadata.
- A veto is persistent and changes the second-round query rather than merely changing presentation.
- The repository has a deterministic fixture preview, a live Qloo path, deployment configuration, abuse protection and an automated release preflight.

## What I learned

Multi-user recommendation is partly a decision-policy problem. “Good for the average profile” and “acceptable to both people” are different objectives.

I also learned to treat API scores according to their documented semantics instead of turning them into more intuitive-looking but unsupported percentages. Qloo provides the cultural relationship and ranking signal; CommonGround deliberately keeps its own decision policy simple and inspectable.

## Potential impact

The initial audience is deliberately narrow: pairs of people making repeated shared entertainment choices where “just average our profiles” is a poor social rule. The same interaction pattern can support couples, friends or roommates choosing a movie without making one person's taste the default.

The project does not claim that the current rank heuristic is universally fair or that it improves satisfaction without user testing. What it demonstrates is a concrete product behavior that can be evaluated: both people see the same proposed object, both retain veto power, and the system can return “no confirmed bridge” instead of forcing a recommendation.

## What's next

Before final submission:

1. validate the competition API key against `/search` and `/v2/insights`;
2. verify the exact live explainability response structure;
3. deploy the prepared Render backend with the key server-side;
4. point the existing GitHub Pages frontend at that live API;
5. run the end-to-end preflight and replace fixture screenshots with live screenshots.

Beyond the hackathon, the same two-person bridge loop could be tested with other Qloo-supported cultural domains, but the submission intentionally keeps the output domain to movies so the core behavior stays easy to verify.

## Public preview

- Preview: https://meowrona.github.io/CommonGround/
- Source: https://github.com/MeowRona/CommonGround

The current public Pages build is a clearly labelled fixture preview generated from the Python decision engine. It is intentionally not described as live Qloo output while the hackathon API key is pending.

## Before final submission

- validate real competition-key responses;
- verify exact explainability structure;
- deploy the live Python backend for free;
- point the existing Pages frontend at the live backend and update screenshots;
- re-check rules and final statements against the shipped build.
