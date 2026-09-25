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
