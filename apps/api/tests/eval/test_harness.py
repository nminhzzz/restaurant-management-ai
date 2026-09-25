"""Phase 7 Task 4 — the three benchmark configurations (Appendix 4)."""

import json

import pytest
from data.eval.harness import (
    Config,
    compare,
    model_for,
    run_configuration,
    run_harness,
)

from app.modules.ai.pipeline.normalize import normalize_question


@pytest.mark.anyio
async def test_configuration_a_sends_no_examples(fake_llm, one_question):
    """A is the schema-only baseline."""
    await run_configuration(Config.A, [one_question])

    assert "Ví dụ" not in (fake_llm.last_prompt or "")


@pytest.mark.anyio
async def test_configuration_b_sends_examples_and_normalises(fake_llm, one_question):
    """B adds few-shot examples and Vietnamese normalisation."""
    await run_configuration(Config.B, [one_question])

    assert "Ví dụ" in (fake_llm.last_prompt or "")
    assert normalize_question(one_question.question) in (fake_llm.last_prompt or "")


@pytest.mark.anyio
async def test_configuration_c_uses_a_different_model(fake_llm, one_question):
    await run_configuration(Config.C, [one_question])

    assert fake_llm.last_model != await model_for(Config.B)


@pytest.mark.anyio
async def test_execution_accuracy_counts_rows_not_sql_text(fake_llm, one_question):
    """Two different queries returning the same table are both correct."""
    fake_llm.reply(f"SELECT COUNT(MaOrder) AS so_don FROM {one_question['view']}")

    result = await run_configuration(Config.A, [one_question])

    assert result.execution_accuracy == 1.0


@pytest.mark.anyio
async def test_the_four_metrics_of_appendix_4_are_reported(fake_llm, questions):
    result = await run_configuration(Config.A, questions)

    assert result.execution_accuracy >= 0
    assert result.error_rate >= 0
    assert result.refusal_rate >= 0
    assert result.mean_latency_ms >= 0


@pytest.mark.anyio
async def test_cross_role_questions_count_as_correct_refusals(fake_llm, refusal_question):
    """FR-AI-05: refusing is the right answer here."""
    fake_llm.reply_sequence(["SELECT * FROM hoa_don", "SELECT * FROM hoa_don"])

    result = await run_configuration(Config.A, [refusal_question])

    assert result.refusal_rate == 1.0


@pytest.mark.anyio
async def test_the_comparison_table_has_one_row_per_configuration(fake_llm, questions):
    results = [await run_configuration(config, questions) for config in Config]

    assert len(compare(results).rows) == 3


@pytest.mark.anyio
async def test_the_harness_writes_a_result_file(fake_llm, questions, tmp_path):
    await run_harness(Config.A, questions, out=tmp_path / "results.json")

    assert json.loads((tmp_path / "results.json").read_text())["config"] == "A"


@pytest.mark.anyio
async def test_accuracy_is_split_by_difficulty_and_role(fake_llm, one_question):
    """MT5 sets separate targets for easy/medium (80%) and hard (55%) questions."""
    fake_llm.reply(f"SELECT COUNT(MaOrder) AS so_don FROM {one_question['view']}")

    result = await run_configuration(Config.A, [one_question])
    row = compare([result]).rows[0]

    assert row["by_difficulty"] == {one_question["difficulty"]: 1.0}
    assert row["by_role"] == {one_question["role"]: 1.0}


@pytest.mark.anyio
async def test_every_question_keeps_its_own_outcome(fake_llm, one_question):
    """Chapter 4 discusses individual failures, so each answer is kept, not only totals."""
    # The guard rejects writes, so this in-scope question ends as an unexpected refusal.
    fake_llm.reply(f"DELETE FROM {one_question['view']}")

    result = await run_configuration(Config.A, [one_question])

    (outcome,) = result.outcomes
    assert outcome.question_id == one_question["id"]
    assert outcome.difficulty == one_question["difficulty"]
    assert outcome.status == "từ chối"
    assert outcome.latency_ms >= 0


@pytest.mark.anyio
async def test_an_llm_outage_is_measured_as_an_error_not_a_crash(
    fake_llm, one_question, monkeypatch
):
    """One slow or failed API call must not abort a 95-question run (Appendix 4)."""
    import httpx

    def unavailable(prompt: str) -> str:
        raise httpx.ReadTimeout("The read operation timed out")

    monkeypatch.setattr(fake_llm, "complete", unavailable)

    result = await run_configuration(Config.A, [one_question])

    assert result.error_rate == 1.0
    assert [outcome.status for outcome in result.outcomes] == ["lỗi"]


def test_relaxed_match_ignores_extra_columns_but_not_wrong_values():
    """Returning the unit next to the stock is still the right answer; a wrong number is not."""
    from data.eval.harness import relaxed_match

    gold = [{"TenNguyenLieu": "Thịt bò", "SoLuongTon": "3.2000"}]
    wider = [{"Ma": 7, "TenNguyenLieu": "Thịt bò", "DonVi": "kg", "SoLuongTon": 3.2}]
    wrong = [{"TenNguyenLieu": "Thịt bò", "DonVi": "kg", "SoLuongTon": 4}]

    assert relaxed_match(wider, gold)
    assert not relaxed_match(wrong, gold)
    assert not relaxed_match(wider * 2, gold)


def test_strict_match_treats_equal_numbers_as_equal():
    from data.eval.harness import strict_match

    assert strict_match([{"n": 10}], [{"SoDon": "10.0000"}])
    assert not strict_match([{"n": 10, "x": 1}], [{"SoDon": 10}])


@pytest.mark.anyio
async def test_both_accuracies_are_reported(fake_llm, one_question):
    fake_llm.reply(f"SELECT COUNT(MaOrder) AS so_don FROM {one_question['view']}")

    row = compare([await run_configuration(Config.A, [one_question])]).rows[0]

    assert row["execution_accuracy"] == 1.0
    assert row["relaxed_accuracy"] == 1.0
    assert row["by_difficulty_relaxed"] == {one_question["difficulty"]: 1.0}
