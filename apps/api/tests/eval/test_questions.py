"""Phase 7 Task 3 — the Vietnamese Text-to-SQL benchmark set (Appendix 4)."""

import unicodedata
from collections import Counter

import sqlglot

from app.modules.ai import guard
from app.modules.ai.scope import ROLE_VIEWS, views_for
from app.shared.roles import Role


def test_the_set_has_between_fifty_and_one_hundred_questions(questions):
    assert 50 <= len(questions) <= 100


def test_every_difficulty_tier_is_represented(questions):
    """Appendix 4: three tiers."""
    tiers = Counter(question["difficulty"] for question in questions)

    assert set(tiers) == {"easy", "medium", "hard"}
    assert all(count >= 10 for count in tiers.values())


def test_every_role_has_questions(questions):
    roles = Counter(question["role"] for question in questions)

    assert set(roles) == {"MANAGER", "CASHIER", "WAREHOUSE"}


def test_each_question_names_the_view_its_sql_must_use(questions):
    for question in questions:
        assert question["view"] == ROLE_VIEWS[Role(question["role"])]


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

        assert tables <= set(ROLE_VIEWS.values())


def test_the_set_includes_cross_role_cases_expected_to_be_refused(questions):
    """FR-AI-05: the set also proves the assistant stays in its lane."""
    refused = [q for q in questions if q["notes"] and "vượt quyền" in q["notes"]]

    assert len(refused) >= 5


def test_questions_are_unique_and_numbered(questions):
    ids = [question["id"] for question in questions]

    assert len(set(ids)) == len(ids)
    assert ids == [f"Q{index:03d}" for index in range(1, len(ids) + 1)]


def test_vietnamese_diacritics_are_kept_intact(questions):
    """A normaliser that strips diacritics would lose meaning on food names."""
    for question in questions:
        assert question["question"] == unicodedata.normalize("NFC", question["question"])
