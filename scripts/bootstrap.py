"""Bootstrap the project from primary sources: download, prepare, train.

Requires Kaggle API credentials for TWCS:
    KAGGLE_USERNAME, KAGGLE_KEY

Usage:
    python scripts/bootstrap.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

STEPS = [
    [PY, "scripts/data/download_data.py", "--fetch-bitext"],
    [PY, "scripts/data/download_data.py", "--fetch-twcs"],
    [PY, "scripts/data/prepare_twcs.py"],
    [PY, "scripts/data/build_dataset.py", "--config", "configs/data.yaml"],
    [PY, "scripts/data/validate_data_ge.py"],
    [PY, "scripts/train/train_final.py"],
]


def main() -> int:
    for command in STEPS:
        print("$", " ".join(command), flush=True)
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode != 0:
            print(f"Step failed: {' '.join(command)}", file=sys.stderr)
            return result.returncode
    print("Done. Model: artifacts/model.joblib")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
