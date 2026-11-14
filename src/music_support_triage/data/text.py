"""Text cleaning, PII masking and deduplication helpers."""

from __future__ import annotations

import html
import re
import unicodedata

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MENTION_RE = re.compile(r"@\w+")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d\s().-]{7,}\d(?!\w)")
CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
WHITESPACE_RE = re.compile(r"\s+")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")

PII_PATTERNS = {
    "email": EMAIL_RE,
    "phone": PHONE_RE,
    "card": CARD_RE,
    "url": URL_RE,
    "handle": MENTION_RE,
}


def detect_pii(text: str) -> list[str]:
    """Return PII flags found in raw text."""
    return [name for name, pattern in PII_PATTERNS.items() if pattern.search(text)]


def mask_pii(text: str) -> tuple[str, list[str]]:
    """Mask PII in raw text and return the text plus detected flags."""
    flags = detect_pii(text)
    masked = EMAIL_RE.sub(" __email__ ", text)
    masked = CARD_RE.sub(" __card__ ", masked)
    masked = PHONE_RE.sub(" __phone__ ", masked)
    masked = URL_RE.sub(" ", masked)
    masked = MENTION_RE.sub(" ", masked)
    return masked, flags


def clean_text(text: object) -> str:
    """Normalise a support message for training and inference.

    The function is deterministic and never raises on missing values.
    """
    if text is None:
        return ""
    value = unicodedata.normalize("NFKC", html.unescape(str(text)))
    value, _ = mask_pii(value)
    value = value.replace("\u2019", "'").replace("\u2018", "'")
    value = value.replace("\u201c", '"').replace("\u201d", '"')
    value = WHITESPACE_RE.sub(" ", value)
    return value.strip()


def normalize_for_dedup(text: str) -> str:
    """Return a stable Unicode-aware key used for exact-duplicate detection."""
    value = unicodedata.normalize("NFKC", text.casefold())
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return value.strip()


def has_letters(text: str) -> bool:
    """Return True when text contains at least one Latin or Cyrillic letter."""
    return any(char.isalpha() for char in text)


def is_usable(text: str, min_chars: int = 10, max_chars: int = 5000) -> bool:
    """Return True when text can be used as a model input."""
    length = len(text)
    return min_chars <= length <= max_chars and has_letters(text)
