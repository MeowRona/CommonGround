# Deployment contract

The contest requires a fully published, freely accessible working demo. Publication is intentionally deferred until live Qloo validation and entrant approval.

## Runtime

- Python 3.11+
- no pip dependencies
- start command: `python app.py`
- bind address: set `HOST=0.0.0.0` on a host
- port: the app reads the standard `PORT` environment variable
- production data mode: `COMMON_GROUND_MODE=live`
- secret: `QLOO_API_KEY`, stored only in the hosting provider's secret/environment settings
- health endpoint: `GET /health`

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

