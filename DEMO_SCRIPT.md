# CommonGround — 60–90 second judging demo

Use this after the live Qloo deployment is verified. Do not record the fixture Pages build as if it were live.

## 0–10 s — the problem

Show the landing screen.

Narration idea:

> Two people can both get “good recommendations” and still have no good shared choice. CommonGround does not merge them into one average profile.

## 10–25 s — select two genuinely different profiles

Person A searches and selects:

- `Blade Runner`
- `Aphex Twin`

Person B searches and selects:

- `Amelie`
- `Daft Punk`

Briefly show that each item is a recognized Qloo **movie/artist entity**, not raw free text.

Narration idea:

> Qloo resolves each taste signal and searches cross-domain from movies and artists into one target domain: movies.

## 25–45 s — the key technical moment

Click **Find a bridge**.

Show the proposed bridge card with:

- one movie in the center;
- A's rank route;
- B's rank route;
- Qloo-supported evidence chips when explainability is available.
- the diagnostic line showing that the naive top-3 intersection can be empty while same-pool evaluation still recovers a bridge.
- the `input movies excluded` diagnostic, showing that the proposed bridge must be a third object rather than simply echoing one person's seed movie.

Narration idea:

> The two searches are not merely intersected. CommonGround unions both candidate sets and asks Qloo to evaluate the exact same movie pool for A and B. It minimizes the worse rank, so a proposal cannot win just by being excellent for one person.

## 45–65 s — prove that the agent is adaptive

Choose **Not for me** for one person on the first proposal.

Show the second result appear.

Narration idea:

> A veto changes the next action. The first movie is excluded, the search widens, and the shared pool is evaluated again. There are only two rounds — if both people still do not accept, CommonGround stops instead of inventing a compromise.

## 65–80 s — success condition

Choose **Want to try** for both people on the second proposal.

Show the confirmed-common-ground message.

Narration idea:

> Common ground is confirmed only by both people. Qloo supplies cultural affinity and explainability; CommonGround supplies the transparent two-person decision policy and feedback loop.

## What not to say

- Do not call Qloo affinity a probability that a person will enjoy the movie.
- Do not claim CommonGround can read emotion or detect whether somebody is “pretending”.
- Do not say the rank policy is a novel recommendation algorithm; describe it as a transparent least-misery-style decision heuristic.
- Do not claim the Pages fixture preview is live Qloo.
- Do not show the API key, Render environment page, terminal environment variables, or raw request headers.

## Media checklist after live deploy

Capture three final images for Devpost:

1. entity-selection screen with Qloo-recognized films/artists;
2. first live bridge showing A/B ranks and real explainability evidence;
3. second-round result after a veto.
