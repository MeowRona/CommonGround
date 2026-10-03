# Qloo hackathon API key request — ready answers

Official form: https://forms.gle/zz12orkLHTAneLGz6

The current official form asks for:

- **First Name** — required; enter your real first name.
- **Last Name** — required; enter your real last name.
- **Devpost Username** — required; copy it exactly from your Devpost profile.
- **GitHub Username** — optional; `MeowRona`.
- **Location Country** — required; `Poland`.
- **Project Idea** — required; use the text below.
- **Agreement** — required; read the linked hackathon/API rules yourself and tick both boxes only if you agree.

## Project Idea — concise version

CommonGround is an adaptive two-person cultural bridge finder. Each person selects a few Qloo-recognized films or artists. Qloo discovers movie candidates independently for both profiles, then CommonGround evaluates the same candidate pool for both sides, proposes one bridge movie, and adapts once after a veto. Qloo explainability is surfaced only when present in the API response.

## Project Idea — shorter fallback

CommonGround uses Qloo to find one movie that bridges two different cultural taste profiles, then adapts once if either person rejects the proposal.

## What happens after submission

The Qloo developer guide says hackathon keys are typically issued by email within a few business days. Check spam/junk if it does not appear.

Once the key arrives, do **not** paste it into Devpost, GitHub, screenshots, or chat logs. Set it locally as `QLOO_API_KEY`, run `python live_smoke.py --write-fixture`, then put it only into the Render secret/environment field during live deployment.

