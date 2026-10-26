"""The cross-check worksheet must not leak the gold answer, and the draft minutes must
only call a question agreed when every member's rows match the gold rows."""

from collections import Counter

import pytest
from tests.eval.conftest import load_questions


def test_the_selection_covers_every_difficulty_and_role():
    from data.eval.crosscheck import selected

    picked = selected(load_questions())

    assert len(picked) == 20
    assert Counter(q["difficulty"] for q in picked) == {"easy": 6, "medium": 7, "hard": 7}
    assert {q["role"] for q in picked} == {"MANAGER", "CASHIER", "WAREHOUSE"}


def test_the_worksheet_never_shows_the_gold_sql():
    from data.eval.crosscheck import answer_template, selected, worksheet

    picked = selected(load_questions())
    sheet = worksheet(picked)

    for question in picked:
        assert question["question"] in sheet
        assert question["sql"] not in sheet
    assert answer_template(picked)["answers"] == {q["id"]: "" for q in picked}


def test_an_unknown_question_id_is_refused():
    from data.eval.crosscheck import selected

    with pytest.raises(ValueError, match="Q999"):
        selected(load_questions(), ("Q001", "Q999"))


def test_a_question_is_agreed_only_when_every_member_matches():
    from data.eval.crosscheck import (
        AGREED,
        BLANK,
        DISCUSS,
        MATCH,
        MATCH_EXTRA,
        MISMATCH,
        MemberResult,
        verdict,
    )

    assert verdict([MemberResult("A", MATCH), MemberResult("B", MATCH_EXTRA)]) == AGREED
    assert verdict([MemberResult("A", MATCH), MemberResult("B", MISMATCH)]) == DISCUSS
    assert verdict([MemberResult("A", MATCH), MemberResult("B", BLANK)]) == DISCUSS
    assert verdict([]) == DISCUSS


QUESTION = {
    "id": "Q900",
    "question": "Kho hiện có bao nhiêu nguyên liệu?",
    "role": "WAREHOUSE",
    "sql": "SELECT 1",
    "reference_time": "2026-10-23T12:00:00",
    "expected_result": [{"SoNguyenLieu": 12}],
}


@pytest.mark.anyio
async def test_member_rows_are_compared_with_the_frozen_gold(monkeypatch):
    from data.eval import crosscheck

    from app.modules.ai.pipeline import executor

    replies = {
        "same": [{"SoLuong": 12}],
        "extra": [{"SoLuong": 12, "DonVi": "loại"}],
        "other": [{"SoLuong": 11}],
    }

    async def fake_execute(sql, *, role, timeout_seconds):
        return next(rows for key, rows in replies.items() if f"'{key}'" in sql)

    monkeypatch.setattr(executor, "execute", fake_execute)
    sheets = [
        {"member": name, "answers": {"Q900": f"SELECT '{key}' FROM vw_ai_kho_ton"}}
        for name, key in (("An", "same"), ("Bình", "extra"), ("Chi", "other"))
    ]

    [(_, results, _)] = await crosscheck.check([QUESTION], sheets)

    assert [r.status for r in results] == [
        crosscheck.MATCH,
        crosscheck.MATCH_EXTRA,
        crosscheck.MISMATCH,
    ]
    assert "Q900 | khớp | khớp (thừa cột) | lệch | Cần thảo luận" in crosscheck.minutes(
        [(QUESTION, results, QUESTION["expected_result"])]
    )


@pytest.mark.anyio
async def test_sql_outside_the_roles_views_is_an_error_not_a_crash():
    from data.eval.crosscheck import BLANK, judge

    status, _ = await judge("SELECT * FROM HOA_DON", QUESTION, QUESTION["expected_result"])
    assert status.startswith("lỗi")
    assert (await judge("  ", QUESTION, QUESTION["expected_result"]))[0] == BLANK
