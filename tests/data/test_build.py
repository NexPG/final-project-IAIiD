import pandas as pd

from music_support_triage.data.build import (
    assign_stratified_split,
    deduplicate_combined,
)


def make_frame(size: int = 100) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [f"id-{index}" for index in range(size)],
            "text": [f"support message number {index}" for index in range(size)],
            "label": ["other" if index % 5 else "payment" for index in range(size)],
            "source": ["weak_twcs" if index % 2 else "bitext" for index in range(size)],
            "label_quality": ["weak"] * size,
            "split": ["train"] * size,
            "conversation_id": [f"c-{index}" for index in range(size)],
        }
    )


def test_stratified_split_preserves_source_and_label() -> None:
    frame = assign_stratified_split(make_frame(200), test_fraction=0.2, seed=42)
    assert set(frame["split"]) == {"train", "test"}
    assert frame.groupby("conversation_id")["split"].nunique().max() == 1
    for source in ("weak_twcs", "bitext"):
        for label in ("payment", "other"):
            subset = frame[(frame["source"] == source) & (frame["label"] == label)]
            assert (subset["split"] == "test").any()
            assert (subset["split"] == "train").any()


def test_stratified_split_is_about_twenty_percent() -> None:
    frame = assign_stratified_split(make_frame(200), test_fraction=0.2, seed=42)
    share = (frame["split"] == "test").mean()
    assert 0.15 <= share <= 0.25


def test_deduplicate_prefers_twcs_over_bitext() -> None:
    frame = pd.DataFrame(
        {
            "id": ["twcs-1", "bitext-1"],
            "text": ["the same message", "the same message"],
            "label": ["payment", "payment"],
            "source": ["weak_twcs", "bitext"],
            "label_quality": ["weak", "weak"],
            "split": ["train", "train"],
            "conversation_id": ["c-1", "c-2"],
        }
    )
    result = deduplicate_combined(frame)
    assert len(result) == 1
    assert result.iloc[0]["source"] == "weak_twcs"
