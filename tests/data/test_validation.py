import pandas as pd

from music_support_triage.data.validation import validate_dataset

LABELS = ["payment", "subscription", "account", "app"]


def make_frame() -> pd.DataFrame:
    rows = []
    for index, label in enumerate(LABELS):
        rows.append(
            {
                "id": f"train-{index}",
                "text": f"this is a training message about {label}",
                "label": label,
                "label_quality": "human_verified",
                "source": "human",
                "split": "train",
                "conversation_id": f"c-{index}",
                "channel": "social",
                "locale": "en",
            }
        )
    for index, label in enumerate(LABELS):
        rows.append(
            {
                "id": f"val-{index}",
                "text": f"this is a validation message about {label}",
                "label": label,
                "label_quality": "human_verified",
                "source": "human",
                "split": "validation",
                "conversation_id": f"v-{index}",
                "channel": "social",
                "locale": "en",
            }
        )
    return pd.DataFrame(rows)


def test_clean_dataset_is_valid() -> None:
    report = validate_dataset(make_frame(), {"splits": {"allow_weak_eval": False}})
    assert report["ok"] is True


def test_cross_split_duplicate_is_error() -> None:
    frame = make_frame()
    frame.loc[0, "text"] = frame.loc[4, "text"]
    report = validate_dataset(frame, {"splits": {"allow_weak_eval": False}})
    assert report["ok"] is False
    assert any(item["code"] == "cross_split_duplicates" for item in report["errors"])


def test_conversation_leak_is_error() -> None:
    frame = make_frame()
    frame.loc[4, "conversation_id"] = frame.loc[0, "conversation_id"]
    report = validate_dataset(frame, {"splits": {"allow_weak_eval": False}})
    assert any(item["code"] == "conversation_leak" for item in report["errors"])


def test_weak_eval_is_error_when_not_allowed() -> None:
    frame = make_frame()
    frame.loc[4, "label_quality"] = "weak"
    report = validate_dataset(frame, {"splits": {"allow_weak_eval": False}})
    assert any(item["code"] == "weak_eval" for item in report["errors"])
