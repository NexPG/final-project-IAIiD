from music_support_triage.data.labels import map_bitext, map_twcs_intent


def test_twcs_payment_mapping() -> None:
    assert map_twcs_intent("billing_payment", "charged twice") == "payment"


def test_cancellation_refund_is_split_by_text() -> None:
    assert map_twcs_intent("cancellation_refund", "I need a refund for this charge") == "payment"
    assert map_twcs_intent("cancellation_refund", "please cancel my subscription") == "subscription"
    assert map_twcs_intent("cancellation_refund", "not sure what to do") == "other"


def test_bitext_order_mapping() -> None:
    assert map_bitext("ORDER", "cancel_order", "cancel my premium plan") == "subscription"
    assert map_bitext("ORDER", "track_order", "where is my parcel") == "other"
    assert map_bitext("FEEDBACK", "complaint", "bad service") == "recommendations"


def test_unknown_intent_falls_back_to_other() -> None:
    assert map_twcs_intent("unknown", "hello") == "other"
    assert map_bitext("UNKNOWN", "unknown", "hello") == "other"
