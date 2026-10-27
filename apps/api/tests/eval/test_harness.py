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
async def test_configuration_c_uses_the_same_model_with_thinking(fake_llm, one_question):
    await run_configuration(Config.C, [one_question])

    assert fake_llm.last_model == await model_for(Config.B)


@pytest.mark.anyio
async def test_harness_keeps_interpretation_and_usage_for_manual_grading(
    fake_llm, one_question, fake_engine_factory
):
    # Two cells, so the interpretation still goes through the model.
    fake_engine_factory.columns = ["n", "m"]
    fake_engine_factory.rows = [(1, 2)]
    fake_llm.reply(f"SELECT COUNT(MaOrder) AS so_don FROM {one_question['view']}")
    result = await run_configuration(Config.B, [one_question])
    outcome = result.outcomes[0]
    assert outcome.answer
    assert outcome.call_count >= 2
    assert outcome.answer_correct is None
    assert outcome.reference_rows is not None
    assert outcome.produced_rows is not None
    assert compare([result]).rows[0]["answer_accuracy"] is None


def test_reference_clock_replaces_relative_mysql_dates_without_changing_literals():
    from data.eval.harness import bind_reference_sql

    question = {
        "reference_time": "2026-10-23T12:00:00+07:00",
        "reference_business_date": "2026-10-23",
    }
    sql = (
        "SELECT DATE(CURDATE() - INTERVAL 6 HOUR) AS BusinessDate, "
        "CURDATE() AS Ngay, 'CURDATE()' AS Literal"
    )
    result = bind_reference_sql(sql, question)
    assert "CURDATE()" in result  # The quoted data remains literal.
    assert "2026-10-23" in result
    assert "INTERVAL" not in result


@pytest.mark.parametrize(
    "anchor",
    ["DATE(CURRENT_DATE - INTERVAL '6' HOUR)", "DATE(CURDATE() - INTERVAL 6 HOUR)"],
)
def test_the_gold_business_date_anchor_becomes_the_reference_day(anchor):
    """Regression: binding CURRENT_DATE alone left DATE('2026-10-23' - 6h) = 22/10, so
    every 'hôm nay' reference query counted the previous business day."""
    from data.eval.harness import bind_reference_sql

    question = {
        "reference_time": "2026-10-23T12:00:00+07:00",
        "reference_business_date": "2026-10-23",
    }
    sql = f"SELECT COUNT(*) AS SoDon FROM vw_ai_quanly_order WHERE BusinessDate = {anchor}"

    result = bind_reference_sql(sql, question)

    assert "HOUR" not in result
    assert "'2026-10-23'" in result


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
    assert result.p95_latency_ms >= 0


@pytest.mark.anyio
async def test_repeated_runs_report_a_p95_and_the_run_count(fake_llm, one_question):
    """R27: the evaluation method asks for repeated runs, not one pass."""
    fake_llm.reply(f"SELECT COUNT(MaOrder) AS so_don FROM {one_question['view']}")

    result = await run_configuration(Config.A, [one_question], runs=3)

    assert result.runs == 3
    assert result.execution_accuracy == 1.0
    assert len(result.outcomes) == 3
    assert result.p95_latency_ms >= 0


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

    assert json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))["config"] == "A"


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


def test_numbers_are_compared_at_two_decimal_places():
    """An unrounded average is the same answer as the gold's ROUND(..., 2)."""
    from data.eval.harness import relaxed_match, strict_match

    assert strict_match([{"avg": "32091166.66666667"}], [{"TrungBinh": "32091166.67"}])
    assert relaxed_match(
        [{"Thang": "2026-01", "avg": "66.9032", "SoNgay": 31}],
        [{"Thang": "2026-01", "TrungBinh": "66.90"}],
    )
    assert not strict_match([{"avg": "66.91"}], [{"TrungBinh": "66.90"}])
    assert strict_match([{"n": 2074}], [{"SoDon": "2074.0000"}])


@pytest.mark.anyio
async def test_both_accuracies_are_reported(fake_llm, one_question):
    fake_llm.reply(f"SELECT COUNT(MaOrder) AS so_don FROM {one_question['view']}")

    row = compare([await run_configuration(Config.A, [one_question])]).rows[0]

    assert row["execution_accuracy"] == 1.0
    assert row["relaxed_accuracy"] == 1.0
    assert row["by_difficulty_relaxed"] == {one_question["difficulty"]: 1.0}


@pytest.mark.anyio
async def test_a_provider_connection_error_is_an_llm_error_tried_once(
    fake_llm, one_question, monkeypatch
):
    """A dropped connection is not a SQL execution error and must not spend a 2nd attempt."""
    import anthropic
    import httpx

    def drop(prompt: str) -> str:
        fake_llm.calls += 1
        raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.test"))

    monkeypatch.setattr(fake_llm, "complete", drop)

    result = await run_configuration(Config.A, [one_question])

    assert result.outcomes[0].status == "lỗi"
    assert result.failures[0].reason.startswith("Lỗi gọi LLM")
    assert fake_llm.calls == 1
