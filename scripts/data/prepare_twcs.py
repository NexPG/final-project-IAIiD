"""Build TWCS dev cases and weak intent labels from the raw Kaggle CSV.

The raw Kaggle dataset is not committed. This script keeps the transformation
deterministic: it filters the SpotifyCares brand, pairs each customer tweet with
the first brand reply, and assigns the same weak intent families that the project
uses for training.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

RAW_COLUMNS = (
    "tweet_id",
    "author_id",
    "inbound",
    "created_at",
    "text",
    "response_tweet_id",
    "in_response_to_tweet_id",
)
DEV_COLUMNS = (
    "case_id",
    "customer_text",
    "brand_response",
    "conversation_id",
    "created_at",
    "brand",
)
INTENT_COLUMNS = DEV_COLUMNS + ("intent", "pseudo_label_method")

INTENT_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "cancellation_refund",
        re.compile(r"\b(cancel|cancelled|canceled|refund|refunded|chargeback|money back)\b", re.I),
    ),
    (
        "billing_payment",
        re.compile(r"\b(charge|charged|receipt|invoice|billing|payment|paid|card|price)\b", re.I),
    ),
    (
        "subscription_plan",
        re.compile(r"\b(plan|subscription|renew|renewal|premium|membership|family|student)\b", re.I),
    ),
    (
        "account_access",
        re.compile(r"\b(login|log in|sign in|password|locked|two factor|2fa|verification code)\b", re.I),
    ),
    (
        "account_data_privacy",
        re.compile(r"\b(delete my data|privacy|hacked|personal data|profile|email address)\b", re.I),
    ),
    (
        "playback_technical",
        re.compile(r"\b(app|crash|crashes|player|play|audio|offline|buffer|buffering|freeze|lag|glitch)\b", re.I),
    ),
    (
        "content_availability",
        re.compile(r"\b(album|song|track|catalog|licens|unavailable|removed|missing)\b", re.I),
    ),
    (
        "feature_request_feedback",
        re.compile(r"\b(recommend|playlist|mix|discover|feature|suggest|algorithm)\b", re.I),
    ),
    (
        "ads_free_tier_complaint",
        re.compile(r"\b(ad|ads|advert|free tier|commercial)\b", re.I),
    ),
    (
        "general_complaint_dissatisfaction",
        re.compile(r"\b(worst|terrible|awful|useless|angry|complaint|poor service)\b", re.I),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw", type=Path, default=Path("data/external/twcs/raw/twcs.csv")
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data/external/twcs"))
    return parser.parse_args()


def assign_intent(text: str) -> str:
    """Assign one of the project's weak TWCS intents."""
    for intent, pattern in INTENT_RULES:
        if pattern.search(text):
            return intent
    return "other"


def normalize_id(series: pd.Series) -> pd.Series:
    """Normalize tweet ids that may be parsed as floats."""
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()


def build_frames(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pair SpotifyCares replies with customer messages."""
    raw = raw.copy()
    raw["tweet_id"] = normalize_id(raw["tweet_id"])
    raw["in_response_to_tweet_id"] = normalize_id(raw["in_response_to_tweet_id"])
    raw["text"] = raw["text"].fillna("").astype(str)
    raw["created_at"] = raw["created_at"].fillna("").astype(str)
    raw["author_id"] = raw["author_id"].fillna("").astype(str)

    brand = raw[
        raw["author_id"].str.casefold().eq("spotifycares")
        & raw["in_response_to_tweet_id"].ne("")
        & raw["text"].str.strip().ne("")
    ][["tweet_id", "in_response_to_tweet_id", "text", "created_at"]].rename(
        columns={
            "tweet_id": "conversation_id",
            "in_response_to_tweet_id": "customer_tweet_id",
            "text": "brand_response",
            "created_at": "brand_created_at",
        }
    )
    brand = brand.sort_values(["customer_tweet_id", "brand_created_at"]).drop_duplicates(
        "customer_tweet_id", keep="first"
    )

    customer_ids = set(brand["customer_tweet_id"])
    customer = raw[
        raw["tweet_id"].isin(customer_ids)
        & raw["inbound"].astype(str).str.casefold().eq("true")
    ][["tweet_id", "text", "created_at"]].rename(
        columns={
            "tweet_id": "customer_tweet_id",
            "text": "customer_text",
            "created_at": "created_at",
        }
    )

    merged = customer.merge(brand, on="customer_tweet_id", how="inner")
    merged = merged[merged["customer_text"].str.strip().ne("")]
    merged["case_id"] = "C" + merged["customer_tweet_id"]
    merged["brand"] = "SpotifyCares"
    merged = merged.drop_duplicates("case_id", keep="first")
    dev = merged[
        ["case_id", "customer_text", "brand_response", "conversation_id", "created_at", "brand"]
    ].reset_index(drop=True)

    pseudo = dev.copy()
    pseudo["intent"] = pseudo["customer_text"].map(assign_intent)
    pseudo["pseudo_label_method"] = "keyword"
    return dev, pseudo[list(INTENT_COLUMNS)]


def main() -> int:
    args = parse_args()
    if not args.raw.exists():
        raise SystemExit(
            f"Raw TWCS file not found: {args.raw}. "
            "Run `python scripts/data/download_data.py --fetch-twcs` first."
        )
    raw = pd.read_csv(
        args.raw,
        usecols=list(RAW_COLUMNS),
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    )
    dev, pseudo = build_frames(raw)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    dev_path = args.output_dir / "dev_cases.csv"
    pseudo_path = args.output_dir / "dev_cases_pseudo_labeled.csv"
    dev.to_csv(dev_path, index=False)
    pseudo.to_csv(pseudo_path, index=False)
    print(f"wrote {dev_path} ({len(dev)} rows)")
    print(f"wrote {pseudo_path} ({len(pseudo)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
