from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "docs" / "runtime_config.json"


def normalize_api_base(value: str) -> str:
    value = value.strip().rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in {"", "/"}:
        raise ValueError("API base must be an HTTPS origin such as https://commonground.onrender.com")
    return f"https://{parsed.netloc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Point the GitHub Pages frontend at the live CommonGround API")
    parser.add_argument("api_base", nargs="?", default="", help="HTTPS API origin; omit with --fixture")
    parser.add_argument("--fixture", action="store_true", help="restore fixture-only Pages mode")
    args = parser.parse_args()

    api_base = "" if args.fixture else normalize_api_base(args.api_base)
    CONFIG.parent.mkdir(exist_ok=True)
    CONFIG.write_text(json.dumps({"api_base": api_base}, indent=2) + "\n", encoding="utf-8")
    print(f"Pages runtime config: {'fixture mode' if not api_base else api_base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
