# Devpost update after CommonGround v2 redesign

## Elevator pitch

An adaptive Qloo-powered agent that finds one movie two different tastes can reach for different reasons — and lets either person veto the compromise.

## Replace the old core-description paragraphs with

CommonGround treats a shared recommendation as a two-person decision problem, not one averaged profile.

Each person searches for and selects 1–3 Qloo-recognized films or artists. The app keeps the selected entity ID/type so ambiguous names are not silently guessed. CommonGround then discovers movie candidates independently for both people. CommonGround unions the candidate sets, then asks Qloo to evaluate that same movie pool separately for A and B.

Candidates are ranked by the worse of the two positions first, then by the sum of both positions. Missing evaluation is unknown, not zero.

The app proposes one movie and shows two different evidence routes. Both people respond with Want to try, Already know it, or Not for me. A veto or already-known result is excluded and triggers one wider second round. After two rounds, CommonGround stops rather than forcing a compromise.

The public GitHub Pages build is currently a clearly labelled fixture preview generated from the Python decision policy while the hackathon API key is pending. It does not claim to show live Qloo output.

## Built with

Python, JavaScript, HTML, CSS, Qloo API, REST API, Docker

## Public links

Demo preview: https://meowrona.github.io/CommonGround/
Public repo: https://github.com/MeowRona/CommonGround

## Media to replace

Old screenshots show the removed percentage-score UI. Replace them after opening the current public preview:
1. top screen with “One movie. Two different reasons.” and scenario selector;
2. bridge result showing one movie, A/B rank routes, evidence chips and bilateral feedback buttons;
3. optional second-round screen after a veto.

Do not final-submit until the live Qloo key smoke test and live backend deployment are complete.

## Live deployment path

The repo includes ender.yaml for a Render Free Docker web service. After the Qloo key passes live_smoke.py, connect the repo to Render, store QLOO_API_KEY only as a secret environment variable, deploy, then run submission_preflight.py with LIVE_DEMO_URL set to the HTTPS service URL.

