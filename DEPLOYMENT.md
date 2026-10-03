# Deployment contract

The contest requires a fully published, freely accessible working demo. The repository now includes `render.yaml` for a Render Free web service. The live deployment remains deferred until the Qloo key passes `live_smoke.py`.

## Runtime

- Python 3.11+
- no pip dependencies
- start command: `python app.py`
- bind address: set `HOST=0.0.0.0` on a host
- port: the app reads the standard `PORT` environment variable
- production data mode: `COMMON_GROUND_MODE=live`
- secret: `QLOO_API_KEY`, stored only in the hosting provider's secret/environment settings
- health endpoint: `GET /health`

## Prepared free backend path: Render

`render.yaml` declares one Docker web service using Render's Free plan. The service:

- binds to `0.0.0.0`;
- uses the platform-provided `PORT`;
- runs `COMMON_GROUND_MODE=live`;
- checks `/health`;
- requires `QLOO_API_KEY` as a secret value (`sync: false`), so it is never committed.
- has automatic deploys disabled; deployment stays an explicit contest-demo action.

After the key is verified locally:

1. click the Deploy to Render button in the README (or create a Blueprint from the public repository);
2. create/sign in to a Render account;
3. choose the declared Free service;
4. enter `QLOO_API_KEY` only in Render's secret/environment UI;
5. deploy;
6. set `LIVE_DEMO_URL` locally to the resulting HTTPS URL;
7. run `python submission_preflight.py`.

## Free-host requirement

Use a host only if all of these are true at publication time:

1. no payment method or paid subscription is required for the contest demo;
2. the service can run a small Python HTTP process and inject environment secrets;
3. the public URL remains usable through the judging period;
4. sleeping/cold-start behavior does not make judging impractical;
5. its terms allow a public hackathon demo.

If no genuinely free suitable host is available, stop instead of buying a service under this test.

## Pre-publication smoke test

1. `GET /health` reports `mode: live` and `qloo_key_present: true` without exposing the key.
2. A real A/B request returns at least one Qloo-grounded shared candidate.
3. The UI visibly identifies live mode.
4. Browser console has no application errors.
5. Repository contains no key, `.env`, personal data, temporary docs snapshots, or generated cache files.
6. Public README contains the final demo URL and exact run instructions.

`submission_preflight.py` automates the test suite, clean-Git check, key presence, public repository reachability, and live `/health` verification. It deliberately does not submit anything to Devpost.
