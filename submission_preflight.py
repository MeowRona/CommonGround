from __future__ import annotations

import json
import os
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def check(label: str, ok: bool, detail: str) -> bool:
    print(f"{'PASS' if ok else 'BLOCK'} {label}: {detail}")
    return ok


def fetch_json(url: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"User-Agent": "CommonGround-preflight/1"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(
        url,
        data=body,
        headers=headers,
        method="POST" if body is not None else "GET",
    )
    with urlopen(request, timeout=20) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not isinstance(result, dict):
        raise RuntimeError("unexpected JSON response")
    return result


def exact_search(live_url: str, name: str, kind: str) -> dict:
    data = fetch_json(f"{live_url}/api/search?q={quote(name)}")
    matches = [
        row
        for row in data.get("results", [])
        if row.get("name", "").casefold() == name.casefold() and row.get("kind") == kind
    ]
    if not matches:
        raise RuntimeError(f"live search could not resolve {name!r} as {kind}")
    return matches[0]


def main() -> int:
    results: list[bool] = []

    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
        capture_output=True,
        text=True,
    )
    results.append(
        check(
            "unit tests",
            tests.returncode == 0,
            "suite passes" if tests.returncode == 0 else tests.stderr.strip(),
        )
    )

    git = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    results.append(
        check(
            "git state",
            git.returncode == 0 and not git.stdout.strip(),
            "clean working tree" if not git.stdout.strip() else "uncommitted changes remain",
        )
    )

    if os.environ.get("QLOO_API_KEY"):
        print("INFO local Qloo key: present (not printed)")
    else:
        print("INFO local Qloo key: not set; final readiness relies on the deployed server reporting a live key")

    live_url = os.environ.get("LIVE_API_URL", os.environ.get("LIVE_DEMO_URL", "")).strip().rstrip("/")
    results.append(check("live API URL", bool(live_url), live_url or "LIVE_API_URL missing"))

    if live_url:
        try:
            health = fetch_json(f"{live_url}/health")
            live_ok = (
                health.get("ok") is True
                and health.get("mode") == "live"
                and health.get("qloo_key_present") is True
            )
            results.append(check("live health", live_ok, json.dumps(health, ensure_ascii=False)))

            profile_a = [
                exact_search(live_url, "Blade Runner", "movie"),
                exact_search(live_url, "Aphex Twin", "artist"),
            ]
            profile_b = [
                exact_search(live_url, "Amelie", "movie"),
                exact_search(live_url, "Daft Punk", "artist"),
            ]

            bridge_payload = {
                "profile_a_entities": profile_a,
                "profile_b_entities": profile_b,
                "round": 1,
                "rejected_ids": [],
            }
            first = fetch_json(f"{live_url}/api/bridge", bridge_payload)
            bridge = first.get("bridge")
            bridge_ok = (
                first.get("status") == "proposal"
                and isinstance(bridge, dict)
                and bool(bridge.get("entity_id"))
            )
            results.append(
                check(
                    "live bridge",
                    bridge_ok,
                    bridge.get("name", "no proposal") if isinstance(bridge, dict) else "no proposal",
                )
            )

            if bridge_ok:
                bridge_payload["round"] = 2
                bridge_payload["rejected_ids"] = [bridge["entity_id"]]
                second = fetch_json(f"{live_url}/api/bridge", bridge_payload)
                next_bridge = second.get("bridge")
                veto_ok = (
                    not isinstance(next_bridge, dict)
                    or next_bridge.get("entity_id") != bridge["entity_id"]
                )
                results.append(
                    check(
                        "live veto",
                        veto_ok,
                        "rejected bridge stayed excluded" if veto_ok else "rejected bridge returned",
                    )
                )
        except (HTTPError, URLError, RuntimeError, json.JSONDecodeError) as exc:
            results.append(check("live end-to-end", False, str(exc)))

    repo_url = "https://github.com/MeowRona/CommonGround"
    try:
        with urlopen(
            Request(repo_url, headers={"User-Agent": "CommonGround-preflight/1"}),
            timeout=20,
        ) as response:
            results.append(check("public repo", response.status == 200, f"HTTP {response.status}"))
    except (HTTPError, URLError) as exc:
        results.append(check("public repo", False, str(exc)))

    pages_url = "https://meowrona.github.io/CommonGround"
    try:
        with urlopen(
            Request(f"{pages_url}/", headers={"User-Agent": "CommonGround-preflight/1"}),
            timeout=20,
        ) as response:
            results.append(check("public Pages frontend", response.status == 200, f"HTTP {response.status}"))
        config = fetch_json(f"{pages_url}/runtime_config.json")
        configured_api = str(config.get("api_base", "")).rstrip("/")
        config_ok = bool(live_url) and configured_api == live_url
        results.append(
            check(
                "Pages live API config",
                config_ok,
                configured_api or "runtime_config.json is still in fixture mode",
            )
        )
    except (HTTPError, URLError, RuntimeError, json.JSONDecodeError) as exc:
        results.append(check("public Pages frontend", False, str(exc)))

    if all(results):
        print("READY: automated preflight passed. Human Devpost review is still required.")
        return 0
    print("NOT READY: resolve BLOCK items before final submission.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
