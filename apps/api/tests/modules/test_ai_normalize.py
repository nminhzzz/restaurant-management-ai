import unicodedata

from app.modules.ai.pipeline.normalize import normalize_question


def test_whitespace_is_collapsed() -> None:
    assert normalize_question("  doanh   thu\n tháng 8  ") == "doanh thu tháng 8"


def test_trailing_punctuation_is_dropped() -> None:
    assert normalize_question("Món nào bán chạy nhất?") == "Món nào bán chạy nhất"


def test_diacritics_are_preserved() -> None:
    assert normalize_question("Tồn kho nguyên liệu") == "Tồn kho nguyên liệu"


def test_output_is_nfc() -> None:
    decomposed = unicodedata.normalize("NFD", "Tồn kho")

    assert normalize_question(decomposed) == unicodedata.normalize("NFC", "Tồn kho")


def test_punctuation_only_input_is_returned_unchanged() -> None:
    assert normalize_question("???") == "???"
