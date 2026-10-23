"""Phase 7 Task 3 — the Vietnamese Text-to-SQL benchmark set (Appendix 4)."""

import unicodedata
from collections import Counter

import sqlglot

from app.modules.ai import guard
from app.modules.ai.scope import ROLE_VIEWS, views_for
from app.shared.roles import Role


def test_the_official_set_has_eighty_questions_in_the_planned_strata(questions):
    """Appendix 4: 30 easy, 30 medium, 20 hard; 60 Manager, 10 Cashier, 10 Warehouse."""
    assert len(questions) == 80
    tiers = Counter(question["difficulty"] for question in questions)
    assert tiers == {"easy": 30, "medium": 30, "hard": 20}

    role_tiers = Counter((question["role"], question["difficulty"]) for question in questions)
    assert role_tiers == {
        ("MANAGER", "easy"): 20,
        ("MANAGER", "medium"): 20,
        ("MANAGER", "hard"): 20,
        ("CASHIER", "easy"): 5,
        ("CASHIER", "medium"): 5,
        ("WAREHOUSE", "easy"): 5,
        ("WAREHOUSE", "medium"): 5,
    }


def test_the_development_set_has_thirty_questions(dev_questions):
    """Appendix 4 keeps the prompt-building sample separate from the locked set."""
    assert len(dev_questions) == 30
    assert [question["id"] for question in dev_questions] == [
        f"D{index:03d}" for index in range(1, 31)
    ]


def test_every_role_has_questions(questions):
    roles = Counter(question["role"] for question in questions)

    assert set(roles) == {"MANAGER", "CASHIER", "WAREHOUSE"}


def test_each_question_names_the_view_its_sql_must_use(questions):
    for question in questions:
        allowed = views_for(Role(question["role"]))
        assert question["view"] in allowed
        assert set(question["views"]) <= allowed


def test_every_reference_sql_passes_the_guard(questions):
    """If the reference SQL cannot run, it is not a valid reference."""
    for question in questions:
        guard.validate_sql(
            question["sql"],
            allowed_views=views_for(Role(question["role"])),
            max_rows=500,
        )


def test_no_reference_sql_touches_a_core_table(questions):
    """String matching would be fooled by a column named after a table; parse instead."""
    for question in questions:
        tables = {
            table.name for table in sqlglot.parse_one(question["sql"]).find_all(sqlglot.exp.Table)
        }

        assert tables <= views_for(Role(question["role"]))
        assert tables == set(question["views"])


def test_the_set_includes_cross_role_cases_expected_to_be_refused(safety_questions):
    """FR-AI-05: safety cases prove the assistant stays in its lane."""
    assert len(safety_questions) == 30
    assert all(question["expect"] == "refusal" for question in safety_questions)


def test_the_safety_set_has_thirty_refusal_cases(safety_questions):
    """Appendix 4 keeps the safety cases outside the 80-question business sample."""
    assert len(safety_questions) == 30
    assert all(question["expect"] == "refusal" for question in safety_questions)


def test_safety_questions_are_numbered_and_cover_every_role(safety_questions):
    assert [question["id"] for question in safety_questions] == [
        f"S{index:03d}" for index in range(1, 31)
    ]
    assert {question["role"] for question in safety_questions} == {
        "MANAGER",
        "CASHIER",
        "WAREHOUSE",
    }
    for question in safety_questions:
        assert question["view"] == ROLE_VIEWS[Role(question["role"])]
        assert "kỳ vọng trợ lý từ chối" in question["notes"]


def test_questions_are_unique_and_numbered(questions):
    ids = [question["id"] for question in questions]

    assert len(set(ids)) == len(ids)
    assert ids == [f"Q{index:03d}" for index in range(1, len(ids) + 1)]


def test_vietnamese_diacritics_are_kept_intact(questions):
    """A normaliser that strips diacritics would lose meaning on food names."""
    for question in questions:
        assert question["question"] == unicodedata.normalize("NFC", question["question"])
