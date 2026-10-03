from __future__ import annotations

import json
import os
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def check(label: str, ok: bool, detail: str) -> bool:
    print(f"{'PASS' if ok else 'BLOCK'} {label}: {detail}")
    return ok


def fetch_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "CommonGround-preflight/1"})
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("unexpected JSON response")
    return payload


def main() -> int:
    results: list[bool] = []

    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
        capture_output=True,
        text=True,
    )
    results.append(check("unit tests", tests.returncode == 0, "suite passes" if tests.returncode == 0 else tests.stderr.strip()))

    git = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    results.append(check("git state", git.returncode == 0 and not git.stdout.strip(), "clean working tree" if not git.stdout.strip() else "uncommitted changes remain"))

    results.append(check("Qloo key", bool(os.environ.get("QLOO_API_KEY")), "present in environment" if os.environ.get("QLOO_API_KEY") else "QLOO_API_KEY missing"))

    live_url = os.environ.get("LIVE_DEMO_URL", "").strip().rstrip("/")
    results.append(check("live demo URL", bool(live_url), live_url or "LIVE_DEMO_URL missing"))
    if live_url:
        try:
            health = fetch_json(f"{live_url}/health")
            live_ok = health.get("ok") is True and health.get("mode") == "live" and health.get("qloo_key_present") is True
            results.append(check("live health", live_ok, json.dumps(health, ensure_ascii=False)))
        except (HTTPError, URLError, RuntimeError, json.JSONDecodeError) as exc:
            results.append(check("live health", False, str(exc)))

    repo_url = "https://github.com/MeowRona/CommonGround"
    try:
        with urlopen(Request(repo_url, headers={"User-Agent": "CommonGround-preflight/1"}), timeout=20) as response:
            results.append(check("public repo", response.status == 200, f"HTTP {response.status}"))
    except (HTTPError, URLError) as exc:
        results.append(check("public repo", False, str(exc)))

    if all(results):
        print("READY: automated preflight passed. Human Devpost review is still required.")
        return 0
    print("NOT READY: resolve BLOCK items before final submission.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
