"""CLI: show the selected threshold/margin and its OOF/test metrics.

Threshold tuning itself is part of ``scripts/train/search_models.py``: it uses
out-of-fold probabilities on train, so test is never touched during tuning.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("artifacts/search_results.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.results.exists():
        raise SystemExit(f"Run scripts/train/search_models.py first: {args.results}")
    payload = json.loads(args.results.read_text(encoding="utf-8"))
    summary = {
        "model_version": payload.get("model_version"),
        "selected_family": payload.get("selected", {}).get("family"),
        "cv_macro_f1_mean": payload.get("selected", {}).get("cv_macro_f1_mean"),
        "cv_macro_f1_std": payload.get("selected", {}).get("cv_macro_f1_std"),
        "oof_threshold": payload.get("oof_threshold"),
        "test_routing": payload.get("test_routing"),
        "bootstrap_macro_f1": payload.get("bootstrap_macro_f1"),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
