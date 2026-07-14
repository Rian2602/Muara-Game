"""Tests for ending text integrity — validates all ENDING_TEXTS keys and headers."""

from muara.engine.ending import ENDING_TEXTS, determine_ending


EXPECTED_KEYS = frozenset({
    "pembebasan",
    "kehancuran",
    "dipercaya",
    "dicurigai",
    "terlupakan",
    "sekutu",
})


class TestEndingTexts:
    """Validate ENDING_TEXTS structure and content."""

    def test_all_expected_keys_exist(self):
        assert set(ENDING_TEXTS.keys()) == EXPECTED_KEYS

    def test_total_key_count(self):
        assert len(ENDING_TEXTS) == 6

    def test_no_empty_text(self):
        for key, text in ENDING_TEXTS.items():
            assert text, f"ENDING_TEXTS[{key!r}] is empty"

    def test_each_key_appears_in_header(self):
        for key, text in ENDING_TEXTS.items():
            expected_header = key.upper()
            assert expected_header in text, (
                f"ENDING_TEXTS[{key!r}] header should contain "
                f"{expected_header!r}, but got: {text[:80]}"
            )

    def test_all_endings_have_bold_header(self):
        for key, text in ENDING_TEXTS.items():
            assert "[bold]" in text, (
                f"ENDING_TEXTS[{key!r}] missing [bold] markup in header"
            )
            assert "TAMAT:" in text, (
                f"ENDING_TEXTS[{key!r}] missing 'TAMAT:' in header"
            )
