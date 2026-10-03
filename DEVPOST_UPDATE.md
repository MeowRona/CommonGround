# Devpost update after CommonGround v2 redesign

## Elevator pitch

An adaptive Qloo-powered agent that finds one movie two different tastes can reach for different reasons — and lets either person veto the compromise.

## Replace the old core-description paragraphs with

CommonGround treats a shared recommendation as a two-person decision problem, not one averaged profile.

It is built for pairs — friends, roommates, or partners — who need one shared movie even when their cultural tastes come from different places.

Each person searches for and selects 1–3 Qloo-recognized films or artists. The app keeps the selected entity ID/type so ambiguous names are not silently guessed. CommonGround then discovers movie candidates independently for both people. CommonGround unions the candidate sets, then asks Qloo to evaluate that same movie pool separately for A and B.

Candidates are ranked by the worse of the two positions first, then by the sum of both positions. Missing evaluation is unknown, not zero.

The app proposes one movie and shows two different evidence routes. Both people respond with Want to try, Already know it, or Not for me. A veto or already-known result is excluded and triggers one wider second round. After two rounds, CommonGround stops rather than forcing a compromise.

The public GitHub Pages build is currently a clearly labelled fixture preview generated from the Python decision policy while the hackathon API key is pending. It does not claim to show live Qloo output.

### Why Qloo is essential

The bridge step depends on Qloo's cultural graph: it resolves stable movie/artist entities, discovers movies from mixed-domain taste signals, evaluates an identical candidate pool for two different profiles, and provides explainability metadata tied to each result. A generic LLM could generate a plausible movie title, but it would not provide the same grounded two-profile cultural measurement that the decision policy operates on.

The demo makes this visible instead of hiding it. Its diagnostics show the naive top-3 overlap, input movies excluded from candidacy, and the larger same-pool evaluation. In the deterministic fixture, the two top-3 lists have zero overlap, yet same-pool evaluation recovers a third-object bridge. The final live screenshots will show the same diagnostics using real Qloo responses.

### Impact and limits

CommonGround focuses on a specific recurring problem: choosing one thing together without letting the person with the stronger recommendation dominate the result. Both users keep explicit veto power, and the system can stop with no confirmed bridge. It does not claim proven satisfaction gains or universal fairness without user testing.

## Built with

Python, JavaScript, HTML, CSS, Qloo API, REST API, Docker

## Testing instructions for judges

1. Open `https://meowrona.github.io/CommonGround/`. The static interface appears immediately; if the free backend was asleep, its status will switch from `live backend warming` to `live Qloo` when ready.
2. For Person A, search and select `Blade Runner` and `Aphex Twin`.
3. For Person B, search and select `Amelie` and `Daft Punk`.
4. Click **Find a bridge**. Inspect the naive top-3 overlap, shared-pool size, A/B ranks and any Qloo explainability evidence shown.
5. Choose **Not for me** for either person. The rejected movie is excluded and CommonGround runs its wider second and final round.
6. Choose **Want to try** for both people on a proposal to confirm common ground.

The API key is server-side and no login is required.

## Public links

Demo preview: https://meowrona.github.io/CommonGround/
Public repo: https://github.com/MeowRona/CommonGround

For the final submission, keep the GitHub Pages URL as the demo URL after `docs/runtime_config.json` has been switched to the verified live Render API. The page loads immediately and wakes the free backend in the background.

## Media to replace

Old screenshots show the removed percentage-score UI. Replace them after opening the current public preview:
1. top screen with “One movie. Two different reasons.” and scenario selector;
2. bridge result showing one movie, A/B rank routes, evidence chips and bilateral feedback buttons;
3. optional second-round screen after a veto.

Suggested captions after the live deployment:

1. **CommonGround — two people select Qloo-recognized films and artists before the bridge search begins.**
2. **Same-pool evaluation recovers a movie bridge even when the two naive top-3 lists have no overlap.**
3. **A veto changes the plan: the rejected movie is excluded and CommonGround runs one wider final round.**

Do not final-submit until the live Qloo key smoke test and live backend deployment are complete.

## Live deployment path

The repo includes render.yaml for a Render Free Docker web service. After the Qloo key passes live_smoke.py, connect the repo to Render, store QLOO_API_KEY only as a secret environment variable, deploy, point Pages at it with configure_live_frontend.py, then run submission_preflight.py with LIVE_API_URL set to the Render HTTPS origin.
