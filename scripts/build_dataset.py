"""CLI: build the processed dataset and manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from music_support_triage.core.config import load_data_config
from music_support_triage.data.build import build_dataset
from music_support_triage.data.validation import validate_dataset, write_validation_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/data.yaml"))
    parser.add_argument("--skip-validation", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_data_config(args.config)
    frame, manifest = build_dataset(config)
    print(json.dumps(manifest["summary"], indent=2, ensure_ascii=False))

    if args.skip_validation:
        return 0

    report = validate_dataset(frame, config)
    report_path = config["paths"]["validation_report"]
    write_validation_report(report, report_path)
    print(json.dumps({"ok": report["ok"], "errors": report["errors"], "warnings": report["warnings"]}, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
