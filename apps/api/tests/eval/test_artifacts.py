"""Evaluation artifacts must distinguish captured evidence from human grades."""

import pytest

from app.core.errors import BusinessRuleError


def test_grades_require_a_named_reviewer_and_never_turn_wrong_sql_into_correct_answer():
    from data.eval.artifacts import apply_grades

    result = {
        "detail": {
            "B": {
                "outcomes": [
                    {
                        "question_id": "Q001",
                        "run_index": 1,
                        "status": "sai",
                        "answer_correct": None,
                    }
                ]
            }
        }
    }
    with pytest.raises(ValueError, match="reviewer"):
        apply_grades(
            result, [{"config": "B", "question_id": "Q001", "run_index": 1, "answer_correct": True}]
        )
    graded = apply_grades(
        result,
        [
            {
                "config": "B",
                "question_id": "Q001",
                "run_index": 1,
                "answer_correct": True,
                "reviewer": "Reviewer 1",
            }
        ],
    )
    assert graded["detail"]["B"]["outcomes"][0]["answer_correct"] is False


def test_snapshot_refuses_to_freeze_a_query_outside_the_roles_views():
    from data.eval.artifacts import validated_reference

    with pytest.raises(BusinessRuleError):
        validated_reference({"role": "WAREHOUSE", "sql": "SELECT * FROM HOA_DON"})
