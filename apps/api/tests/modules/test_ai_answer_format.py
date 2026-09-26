"""Structured answers: parse the model's JSON, fall back to text, and round-trip the stored form."""

import json

from app.modules.ai.pipeline.answer_format import (
    StructuredAnswer,
    compose_answer,
    parse_model_answer,
    split_answer,
)

NOTE = "Phạm vi dữ liệu: vw_ai_thungan — đơn hàng, hóa đơn và thanh toán."


def test_valid_json_is_parsed():
    raw = json.dumps({"headline": "Doanh thu 7 ngày đạt 128.450.000 ₫.",
                      "highlights": ["CN cao nhất 22.100.000 ₫.", "T2 thấp nhất 12.400.000 ₫."],
                      "follow_ups": ["So với tuần trước?"]}, ensure_ascii=False)
    answer = parse_model_answer(raw)
    assert answer.headline == "Doanh thu 7 ngày đạt 128.450.000 ₫."
    assert answer.highlights == ["CN cao nhất 22.100.000 ₫.", "T2 thấp nhất 12.400.000 ₫."]
    assert answer.follow_ups == ["So với tuần trước?"]


def test_a_code_fence_is_stripped():
    raw = '```json\n{"headline": "Có 42 đơn.", "highlights": [], "follow_ups": []}\n```'
    assert parse_model_answer(raw).headline == "Có 42 đơn."


def test_plain_text_falls_back_to_the_headline():
    answer = parse_model_answer("Hôm qua có 42 đơn hàng.")
    assert answer == StructuredAnswer("Hôm qua có 42 đơn hàng.", [], [])


def test_wrong_shapes_are_sanitised():
    raw = json.dumps({"headline": "  Có   5 món. ", "highlights": "không phải danh sách",
                      "follow_ups": ["A?", "a?", "", 3, "B?", "C?", "D?"]})
    answer = parse_model_answer(raw)
    assert answer.headline == "Có 5 món."
    assert answer.highlights == []
    assert answer.follow_ups == ["A?", "B?", "C?"]


def test_lists_and_lengths_are_capped():
    raw = json.dumps({"headline": "x" * 500, "highlights": [f"ý {i}" for i in range(9)],
                      "follow_ups": ["y" * 400]})
    answer = parse_model_answer(raw)
    assert len(answer.headline) == 300
    assert len(answer.highlights) == 4
    assert len(answer.follow_ups[0]) == 200


def test_json_without_a_headline_falls_back_to_text():
    raw = json.dumps({"highlights": ["a"]})
    assert parse_model_answer(raw).headline == raw


def test_blank_output_gives_an_empty_headline():
    assert parse_model_answer("   ").headline == ""


def test_compose_then_split_round_trips():
    answer = StructuredAnswer("Có 42 đơn.", ["30 tại chỗ.", "12 mang về."], ["?"])
    text = compose_answer(answer, NOTE)
    assert text == "Có 42 đơn.\n- 30 tại chỗ.\n- 12 mang về.\n\n" + NOTE
    assert split_answer(text) == ("Có 42 đơn.", ["30 tại chỗ.", "12 mang về."])


def test_an_old_free_form_record_splits_into_a_headline():
    old = "Hôm qua có 42 đơn hàng, nhiều hơn hôm kia.\n\n" + NOTE
    assert split_answer(old) == ("Hôm qua có 42 đơn hàng, nhiều hơn hôm kia.", [])
