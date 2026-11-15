"""CLI: validate an existing processed dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from music_support_triage.core.config import load_data_config
from music_support_triage.data.validation import validate_dataset, write_validation_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/data.yaml"))
    parser.add_argument("--data", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_data_config(args.config)
    data_path = args.data or config["paths"]["processed"]
    frame = pd.read_csv(data_path)
    report = validate_dataset(frame, config)
    write_validation_report(report, config["paths"]["validation_report"])
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
