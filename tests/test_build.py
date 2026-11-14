import pandas as pd

from music_support_triage.data.build import (
    assign_group_splits,
    cap_other_share,
    deduplicate_across_splits,
)


def make_frame(size: int = 30) -> pd.DataFrame:
    other_count = max(1, int(size * 0.7))
    return pd.DataFrame(
        {
            "id": [f"id-{index}" for index in range(size)],
            "text": [f"support message number {index}" for index in range(size)],
            "label": ["other"] * other_count + ["payment"] * (size - other_count),
            "source": ["weak_twcs"] * size,
            "label_quality": ["weak"] * size,
            "split": ["train"] * size,
            "conversation_id": [f"c-{index}" for index in range(size)],
        }
    )


def test_group_split_keeps_conversations_whole() -> None:
    frame = assign_group_splits(make_frame(), validation_size=5, test_size=5, seed=42)
    assert set(frame["split"]) == {"train", "validation", "test"}
    assert frame.groupby("conversation_id")["split"].nunique().max() == 1


def test_cap_other_share_limits_majority() -> None:
    frame = make_frame(100)
    capped = cap_other_share(frame, max_share=0.35, seed=42)
    share = (capped["label"] == "other").mean()
    assert share <= 0.36


def test_deduplicate_prefers_test_row() -> None:
    frame = pd.DataFrame(
        {
            "id": ["train-1", "test-1"],
            "text": ["the same message", "the same message"],
            "label": ["other", "payment"],
            "source": ["weak_twcs", "human"],
            "label_quality": ["weak", "human_verified"],
            "split": ["train", "test"],
            "conversation_id": ["c-1", "c-2"],
        }
    )
    result = deduplicate_across_splits(frame)
    assert len(result) == 1
    assert result.iloc[0]["split"] == "test"
