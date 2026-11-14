"""Label mapping from source taxonomies to the project's seven classes."""

from __future__ import annotations

import re

TWCS_INTENT_TO_LABEL: dict[str, str] = {
    "billing_payment": "payment",
    "subscription_plan": "subscription",
    "account_access": "account",
    "account_data_privacy": "account",
    "playback_technical": "app",
    "content_availability": "content",
    "feature_request_feedback": "recommendations",
    "ads_free_tier_complaint": "other",
    "general_complaint_dissatisfaction": "other",
    "other": "other",
}

REFUND_RE = re.compile(
    r"\b(refund|refunded|chargeback|money back|charged|charge|receipt|invoice|billing|paid|payment)\b",
    re.IGNORECASE,
)
CANCEL_RE = re.compile(
    r"\b(cancel|cancelled|canceled|cancellation|end|stop|renew|renewal|subscription|plan)\b",
    re.IGNORECASE,
)

BITEXT_CATEGORY_TO_LABEL: dict[str, str] = {
    "ACCOUNT": "account",
    "CONTACT": "account",
    "PAYMENT": "payment",
    "INVOICE": "payment",
    "REFUND": "payment",
    "CANCEL": "payment",
    "SUBSCRIPTION": "subscription",
    "FEEDBACK": "recommendations",
    "DELIVERY": "other",
    "SHIPPING": "other",
}

BITEXT_ORDER_INTENTS: frozenset[str] = frozenset({"cancel_order", "change_order"})
PLAN_RE = re.compile(r"\b(plan|subscription|membership|premium|billing)\b", re.IGNORECASE)


def map_twcs_intent(intent: str, text: str) -> str:
    """Map a TWCS weak intent to one of the seven project classes."""
    if intent == "cancellation_refund":
        if REFUND_RE.search(text):
            return "payment"
        if CANCEL_RE.search(text):
            return "subscription"
        return "other"
    return TWCS_INTENT_TO_LABEL.get(intent, "other")


def map_bitext(category: str, intent: str, text: str) -> str:
    """Map a Bitext category/intent pair to a project class."""
    if category == "ORDER":
        if intent in BITEXT_ORDER_INTENTS and PLAN_RE.search(text):
            return "subscription"
        return "other"
    return BITEXT_CATEGORY_TO_LABEL.get(category, "other")
