# CommonGround â€” Qloo Agentic Hackathon MVP

CommonGround is a deliberately focused decision agent for the Qloo Agentic Hackathon.

Two people enter a few taste signals and choose a target domain. The agent grounds the two profiles independently, compares their candidate sets, checks whether the shared options are genuinely balanced, and widens retrieval once when the first bridge is weak. It then ranks the overlap with a **fairness-first** rule: a recommendation is strong only when its weaker-person affinity is still strong.

## Current state

- Local UI and API work with clearly labelled deterministic demo affinity data.
- The adaptive agent workflow and group-ranking logic are real and tested.
- The agent exposes its decision trace: interpret -> ground -> stress-test overlap -> adapt if weak -> decide.
- The live Qloo transport is isolated and reads `QLOO_API_KEY` from the environment only.
- The endpoint-specific live Insights mapping is intentionally not guessed. It must be completed after the entrant obtains a hackathon key and the current official response schema is smoke-tested.
- Nothing is hosted or published yet.

## Run

Requires Python 3.11+ and no third-party Python packages.

```powershell
python app.py
```

Open the `http://127.0.0.1:<port>/` address printed by the server. By default the OS selects a free local port. `PORT` is supported for hosted environments; `COMMON_GROUND_PORT` remains available locally.

Run tests:

```powershell
python -m unittest discover -s tests -v
```

Current validation: **15 unit tests pass**, plus a real local HTTP smoke test of `/`, `/health`, and `/api/recommend`. The HTML response also carries CSP, `nosniff`, referrer and permissions headers.

## Why this is not just an LLM wrapper

The core output is an adaptive decision workflow over per-person cultural affinity data, not a chat wrapper. No LLM is required. The agent observes overlap quality and can change its retrieval plan once when the first candidate window is weak. In the intended live version, Qloo materially supplies entity resolution, profile-specific affinity ranking, and explainability; CommonGround supplies the group-fairness objective and decision policy.

## Modes

- `COMMON_GROUND_MODE=demo` â€” default; deterministic fake affinities, clearly labelled in the UI.
- `COMMON_GROUND_MODE=live` â€” reserved for the real Qloo adapter. It intentionally fails closed until the entrant key is available and response-field mapping has been verified.

## Live Qloo integration gate

Do not claim the current demo is Qloo-powered yet. Before that claim is made:

1. entrant requests/receives the official hackathon API key;
2. current official `/v2/insights` request and response schema is checked with a tiny smoke test;
3. `RealQlooClient.recommend_for_profile()` is mapped to those verified fields;
4. live results are compared with the demo mode and documented.

The key must never be committed. The base transport uses `X-Api-Key` and the documented hackathon host only.

See `DEPLOYMENT.md` for the publication-ready runtime contract and `JUDGING_READINESS.md` for the exact contest gaps that still remain.

