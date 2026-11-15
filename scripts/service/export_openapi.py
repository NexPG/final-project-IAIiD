"""CLI: export the FastAPI OpenAPI schema to docs/openapi.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from music_support_triage.api.app import app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/openapi.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schema = app.openapi()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {args.output} with {len(schema.get('paths', {}))} paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
