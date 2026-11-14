from music_support_triage.services.routing import route, top_k


def test_high_confidence_routes_to_topic_queue() -> None:
    decision = route([0.9, 0.02, 0.02, 0.02, 0.02, 0.01, 0.01])
    assert decision.label == "payment"
    assert decision.queue == "billing"
    assert decision.needs_human_review is False


def test_low_confidence_goes_to_manual_review() -> None:
    decision = route([0.4, 0.3, 0.1, 0.1, 0.05, 0.05, 0.0])
    assert decision.queue == "manual_review"
    assert decision.needs_human_review is True


def test_small_margin_goes_to_manual_review() -> None:
    decision = route([0.75, 0.70, 0.02, 0.01, 0.01, 0.005, 0.005])
    assert decision.queue == "manual_review"


def test_high_confidence_other_routes_to_general_support() -> None:
    decision = route([0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.94])
    assert decision.queue == "general_support"


def test_top_k_is_sorted() -> None:
    items = top_k([0.1, 0.6, 0.2, 0.05, 0.02, 0.02, 0.01], k=3)
    assert [item["label"] for item in items] == ["subscription", "account", "payment"]
