"""CLI: verify local external datasets and print their checksums.

Raw datasets are intentionally not committed. TWCS requires accepting the
Kaggle terms and downloading manually; Bitext and Audio Retailer can be fetched
from Hugging Face when ``--fetch-bitext`` is passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

from music_support_triage.core.config import load_data_config

BITEXT_URL = (
    "https://huggingface.co/datasets/bitext/"
    "Bitext-customer-support-llm-chatbot-training-dataset/resolve/main/"
    "Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/data.yaml"))
    parser.add_argument("--fetch-bitext", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_data_config(args.config)
    paths = config["paths"]

    bitext = paths.get("bitext")
    if args.fetch_bitext and bitext is not None and not bitext.exists():
        bitext.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading Bitext to {bitext}")
        urllib.request.urlretrieve(BITEXT_URL, bitext)

    inventory: dict[str, dict[str, object]] = {}
    for name in ("twcs_dev", "twcs_pseudo", "bitext", "synthetic", "human"):
        path = paths.get(name)
        if path is None:
            continue
        inventory[name] = {
            "path": str(path),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else 0,
            "sha256": sha256_file(path) if path.exists() else None,
        }
    print(json.dumps(inventory, indent=2))
    return 0 if all(item["exists"] for item in inventory.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
