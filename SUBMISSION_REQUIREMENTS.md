# Qloo submission requirements — current readiness

Official sources:

- https://qloo.devpost.com/
- https://qloo.devpost.com/rules

Deadline: **October 30, 2026 at 11:45 PM EDT**.

## Eligibility / project baseline

| Requirement | State | Evidence / action |
|---|---|---|
| Working software application using Qloo API | BLOCKED externally | Live client and full flow are implemented; competition API key is still required for real verification. |
| Agentic tool / workflow | READY in code | Two-round policy chooses a pool, evaluates both profiles, proposes one bridge, preserves veto and decides whether to retry or stop. |
| Project created/updated during submission period | READY | CommonGround work began during this hackathon period. |

## Submission materials

| Requirement | State | Evidence / action |
|---|---|---|
| Functional demo URL | PARTIAL | `https://meowrona.github.io/CommonGround/` is public now in fixture mode. Final config must point it at the verified Render/Qloo backend. |
| Fully published external hosting | BLOCKED externally | Render Free deployment path is prepared in `render.yaml`; deploy after the Qloo key passes smoke testing. |
| Public code repository | READY | `https://github.com/MeowRona/CommonGround` |
| All source/assets/instructions | READY | Source, Dockerfile, Render Blueprint, architecture, run/test/deploy instructions are public. |
| Open-source license visible | READY | MIT `LICENSE`; GitHub currently detects it as MIT. |
| Text description | READY as draft | `SUBMISSION_DRAFT.md` + `DEVPOST_UPDATE.md` |
| English submission materials | READY | Public UI, README, submission draft and testing instructions are in English. |
| Demo video | NOT REQUIRED | Current hackathon overview explicitly requires a live app instead of a demo video. A short recording remains optional media only. |

## Final technical release sequence

1. Submit the official Qloo API key request form and receive the key.
2. Set the key locally and run `python live_smoke.py --write-fixture`.
3. If the smoke test passes, deploy the repo to Render Free and store `QLOO_API_KEY` only as a Render secret.
4. Run `python configure_live_frontend.py https://<service>.onrender.com`.
5. Commit/push `docs/runtime_config.json`; wait for GitHub Pages to rebuild.
6. Set `LIVE_API_URL` and run `python submission_preflight.py`.
7. Replace Devpost screenshots with the live entity-selector / bridge / veto screens.
8. Update Devpost text from `DEVPOST_UPDATE.md`.
9. Human reviews all public claims and submits before the deadline.

## Final release gate

Do **not** submit while any of these is true:

- Pages is still in fixture mode;
- `/health` does not report `mode=live` and key present;
- live search cannot resolve the four smoke-test entities;
- the same-pool bridge request fails;
- a vetoed result can return in round 2;
- any public explanation lacks backing Qloo explainability evidence;
- repository is not clean/public or GitHub no longer detects the MIT license.

