"""CLI: small HTTP load test for the triage API."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

import httpx

TEXTS = [
    "I was charged twice for my subscription",
    "I cannot log in to my account",
    "The app crashes when I play a song",
    "Please bring back this album",
    "I want better recommendations",
    "Thank you for the support",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--rps", type=float, default=20.0)
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path("artifacts/load_test.json"))
    return parser.parse_args()


async def one_request(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    url: str,
    index: int,
) -> tuple[int, float]:
    async with semaphore:
        started = time.perf_counter()
        try:
            response = await client.post(
                url,
                json={"text": TEXTS[index % len(TEXTS)], "channel": "app", "locale": "en"},
            )
            return response.status_code, (time.perf_counter() - started) * 1000.0
        except Exception:
            return 0, (time.perf_counter() - started) * 1000.0


async def run(args: argparse.Namespace) -> dict[str, object]:
    total = max(1, int(args.rps * args.duration))
    semaphore = asyncio.Semaphore(args.concurrency)
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks: list[asyncio.Task[tuple[int, float]]] = []
        started = time.perf_counter()
        for index in range(total):
            target = started + index / args.rps
            delay = target - time.perf_counter()
            if delay > 0:
                await asyncio.sleep(delay)
            tasks.append(
                asyncio.create_task(one_request(client, semaphore, f"{args.base_url}/v1/classify", index))
            )
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - started

    latencies = sorted(latency for _, latency in results)
    errors = sum(1 for status, _ in results if status != 200)
    p50 = latencies[int(len(latencies) * 0.50)] if latencies else 0.0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
    p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0.0
    return {
        "base_url": args.base_url,
        "target_rps": args.rps,
        "duration_seconds": round(elapsed, 2),
        "concurrency": args.concurrency,
        "requests": total,
        "errors": errors,
        "error_rate": round(errors / total, 4),
        "actual_rps": round(total / elapsed, 2) if elapsed else 0.0,
        "latency_ms": {
            "p50": round(p50, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
            "max": round(latencies[-1], 2) if latencies else 0.0,
        },
    }


def main() -> int:
    args = parse_args()
    report = asyncio.run(run(args))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["error_rate"] <= 0.01 and report["latency_ms"]["p95"] <= 500 else 1


if __name__ == "__main__":
    raise SystemExit(main())
