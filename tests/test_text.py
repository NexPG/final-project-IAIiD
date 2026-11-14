from music_support_triage.data.text import (
    clean_text,
    detect_pii,
    is_usable,
    normalize_for_dedup,
)


def test_clean_text_masks_pii_and_mentions() -> None:
    raw = "Hi @SpotifyCares, mail me at user@example.com or +1 (555) 123-4567 https://t.co/x"
    cleaned = clean_text(raw)
    assert "@SpotifyCares" not in cleaned
    assert "user@example.com" not in cleaned
    assert "https://t.co" not in cleaned
    assert "__email__" in cleaned
    assert "__phone__" in cleaned


def test_detect_pii_flags() -> None:
    flags = detect_pii("mail user@example.com from https://t.co/x @spotify")
    assert "email" in flags
    assert "url" in flags
    assert "handle" in flags


def test_normalize_for_dedup_is_stable() -> None:
    assert normalize_for_dedup("Hello, WORLD!") == normalize_for_dedup("hello world")


def test_is_usable_rejects_short_or_symbol_only() -> None:
    assert not is_usable("ok")
    assert not is_usable("!!!!!!!!!!")
    assert is_usable("my payment failed twice")
