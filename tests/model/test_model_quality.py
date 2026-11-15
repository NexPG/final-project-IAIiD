from __future__ import annotations

import numpy as np
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline

from music_support_triage.data.schema import LABELS
from music_support_triage.data.text import clean_text, is_usable
from music_support_triage.services.routing import route

TRAIN = {
    "payment": [
        "charged twice for my subscription",
        "refund my payment please",
        "receipt for the last charge",
        "card declined but money taken",
        "duplicate billing on my account",
        "invoice shows the wrong amount",
        "payment failed but i was charged",
        "need a refund for premium",
        "billing error on my card",
        "money back for duplicate charge",
    ],
    "subscription": [
        "cancel my premium plan",
        "stop the automatic renewal",
        "upgrade my subscription plan",
        "family plan is not working",
        "change my subscription tier",
        "renewal date is wrong",
        "i want to end my membership",
        "premium plan benefits",
        "switch to student subscription",
        "promo subscription expired",
    ],
    "account": [
        "cannot log in to my account",
        "reset my password please",
        "my account was hacked",
        "two factor code not arriving",
        "change my profile email",
        "delete my account data",
        "account locked after login",
        "password reset link broken",
        "someone accessed my profile",
        "verify my account email",
    ],
    "app": [
        "the app crashes when i play a song",
        "player freezes on my phone",
        "offline mode is broken",
        "audio stops after ten seconds",
        "app will not install on android",
        "desktop player keeps buffering",
        "playback is lagging badly",
        "app logs me out constantly",
        "shuffle button does not work",
        "song stops when screen locks",
    ],
    "recommendations": [
        "recommendations are terrible",
        "improve my playlist suggestions",
        "feature request for better mixes",
        "why do you recommend this artist",
        "i want more control over discover weekly",
        "suggestions do not match my taste",
        "add a feature to block artists",
        "recommendation algorithm is repetitive",
        "personalized mixes are boring",
        "feedback on recommended playlists",
    ],
    "content": [
        "the album disappeared from the catalog",
        "song is not available in my country",
        "missing track from my playlist",
        "bring back this album please",
        "artist page has wrong metadata",
        "catalog is missing this release",
        "track removed due to licensing",
        "album cover is wrong",
        "cannot find this song anymore",
        "content unavailable in my region",
    ],
    "other": [
        "partnership proposal for your team",
        "press inquiry about your company",
        "job application for a designer",
        "thanks for the great service",
        "spam offer for marketing",
        "general feedback about the brand",
        "question about your office",
        "request for a sponsorship",
        "hello i have a business idea",
        "unsubscribe from your newsletter",
    ],
}


def make_dataset() -> tuple[list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []
    for label, examples in TRAIN.items():
        texts.extend(clean_text(value) for value in examples)
        labels.extend([label] * len(examples))
    return texts, labels


@pytest.fixture(scope="module")
def model() -> Pipeline:
    texts, labels = make_dataset()
    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            ("clf", LogisticRegression(C=4.0, max_iter=1000, class_weight="balanced")),
        ]
    )
    pipeline.fit(texts, labels)
    return pipeline


def test_model_has_all_labels(model: Pipeline) -> None:
    assert set(model.classes_) == set(LABELS)


def test_overall_macro_f1(model: Pipeline) -> None:
    texts, labels = make_dataset()
    predictions = model.predict(texts)
    score = f1_score(labels, predictions, average="macro")
    assert score >= 0.90


def test_per_class_recall(model: Pipeline) -> None:
    texts, labels = make_dataset()
    predictions = model.predict(texts)
    for label in LABELS:
        indices = [index for index, value in enumerate(labels) if value == label]
        recall = float(np.mean([predictions[index] == label for index in indices]))
        assert recall >= 0.70, f"low recall for {label}: {recall:.2f}"


def test_robustness_to_case_and_spacing(model: Pipeline) -> None:
    base = "charged twice for my subscription"
    assert model.predict([base])[0] == model.predict(["  CHARGED   twice for my subscription!!! "])[0]


def test_edge_cases_are_rejected_by_preprocessing() -> None:
    assert not is_usable("")
    assert not is_usable("     ")
    assert not is_usable("!!!!!")
    assert clean_text(None) == ""


def test_behavior_negation_is_correct_or_manual(model: Pipeline) -> None:
    text = "I don't want to cancel my subscription, I need a receipt"
    probabilities = model.predict_proba([text])[0]
    decision = route(
        probabilities,
        list(model.classes_),
        threshold=0.7,
        margin_threshold=0.1,
    )
    assert decision.label == "payment" or decision.needs_human_review


def test_adversarial_typo_keeps_topic(model: Pipeline) -> None:
    clean_prediction = model.predict(["reset my password please"])[0]
    typo_prediction = model.predict(["resset my passwrd please"])[0]
    assert clean_prediction == typo_prediction == "account"


def test_subgroup_length_does_not_crash(model: Pipeline) -> None:
    short = "app crashes"
    long = "the app crashes when i play a song on my phone and it keeps buffering"
    assert model.predict([short])[0] == "app"
    assert model.predict([long])[0] == "app"
