"""CLI: smoke-check a running triage API."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def request_json(method: str, url: str, payload: dict[str, object] | None = None) -> tuple[int, object]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            if not body:
                return response.status, None
            try:
                return response.status, json.loads(body)
            except json.JSONDecodeError:
                return response.status, body
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base = args.base_url.rstrip("/")
    checks: list[tuple[str, bool, object]] = []

    status, body = request_json("GET", f"{base}/healthcheck")
    checks.append(("healthcheck", status == 200, body))

    status, body = request_json("GET", f"{base}/model-info")
    checks.append(("model-info", status == 200, body))

    status, body = request_json(
        "POST",
        f"{base}/v1/classify",
        {"text": "I was charged twice for my premium subscription", "channel": "app"},
    )
    checks.append(("classify", status == 200, body))

    status, body = request_json(
        "POST",
        f"{base}/v1/classify/batch",
        {
            "items": [
                {"text": "I cannot log in to my account"},
                {"text": "The app crashes when I play a song"},
            ]
        },
    )
    checks.append(("batch", status == 200, body))

    status, body = request_json("GET", f"{base}/metrics")
    checks.append(("metrics", status == 200, body))

    for name, ok, body in checks:
        print(f"[{'ok' if ok else 'fail'}] {name}")
        if not ok:
            print(body)
    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
