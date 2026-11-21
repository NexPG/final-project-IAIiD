"""CLI: download/verify external datasets and print their checksums.

Raw datasets are intentionally not committed. TWCS is downloaded through the
official Kaggle API (credentials required) and then converted with
``prepare_twcs.py``. Bitext is fetched from Hugging Face.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import urllib.request
import zipfile
from pathlib import Path

from music_support_triage.core.config import load_data_config

BITEXT_URL = (
    "https://huggingface.co/datasets/bitext/"
    "Bitext-customer-support-llm-chatbot-training-dataset/resolve/main/"
    "Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv"
)
KAGGLE_TWCS_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "thoughtvector/customer-support-on-twitter"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_bitext(path: Path) -> None:
    """Download the public Bitext CSV from Hugging Face."""
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading Bitext to {path}")
    urllib.request.urlretrieve(BITEXT_URL, path)


def download_twcs(raw_path: Path) -> None:
    """Download the official Kaggle TWCS archive and extract ``twcs.csv``."""
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")
    if not username or not key:
        raise RuntimeError(
            "Set KAGGLE_USERNAME and KAGGLE_KEY (Kaggle Account -> Create New API Token), "
            f"then rerun, or download manually from {KAGGLE_TWCS_URL}"
        )
    token = base64.b64encode(f"{username}:{key}".encode()).decode()
    request = urllib.request.Request(
        KAGGLE_TWCS_URL,
        headers={"Authorization": f"Basic {token}", "User-Agent": "music-support-triage"},
    )
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    archive = raw_path.parent / "twcs.zip"
    print(f"Downloading TWCS from Kaggle to {archive}")
    with urllib.request.urlopen(request) as response, archive.open("wb") as target:
        while chunk := response.read(1024 * 1024):
            target.write(chunk)
    with zipfile.ZipFile(archive) as bundle:
        member = next((name for name in bundle.namelist() if name.endswith("twcs.csv")), None)
        if member is None:
            raise RuntimeError(f"twcs.csv not found in {archive}")
        with bundle.open(member) as source, raw_path.open("wb") as target:
            while chunk := source.read(1024 * 1024):
                target.write(chunk)
    archive.unlink(missing_ok=True)
    print(f"Extracted raw dataset to {raw_path}")
    print("Next: python scripts/data/prepare_twcs.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/data.yaml"))
    parser.add_argument("--fetch-bitext", action="store_true")
    parser.add_argument("--fetch-twcs", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_data_config(args.config)
    paths = config["paths"]

    bitext = paths.get("bitext")
    if args.fetch_bitext and bitext is not None and not bitext.exists():
        download_bitext(bitext)
    if args.fetch_twcs:
        raw_path = paths.get("twcs_raw", Path("data/external/twcs/raw/twcs.csv"))
        if raw_path.exists():
            print(f"TWCS raw already exists: {raw_path}")
        else:
            try:
                download_twcs(raw_path)
            except (RuntimeError, OSError) as exc:
                print(str(exc))
                return 2

    inventory: dict[str, dict[str, object]] = {}
    for name in ("twcs_raw", "twcs_dev", "twcs_pseudo", "bitext", "synthetic", "human"):
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
    if args.fetch_bitext or args.fetch_twcs:
        # A fetch only prepares one stage; prepare_twcs.py and build_dataset.py follow.
        return 0
    return 0 if all(item["exists"] for item in inventory.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
