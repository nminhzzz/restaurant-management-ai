"""The few-shot examples embedded in the prompt must stay runnable.

A stale example teaches the model a column that does not exist, and the model then
writes the same invalid SQL for real questions. These tests keep the examples honest
against the same views the guard and the evaluator use.
"""

import json

import pytest
import sqlglot
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import REPO_ROOT
from app.modules.ai import guard
from app.modules.ai.scope import views_for
from app.shared.roles import Role

EXAMPLES_PATH = REPO_ROOT / "data" / "eval" / "questions.example.jsonl"


def load_examples() -> list[dict]:
    lines = EXAMPLES_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


@pytest.fixture(scope="module")
def examples() -> list[dict]:
    return load_examples()


def test_examples_cover_every_role(examples: list[dict]) -> None:
    assert {example["role"] for example in examples} == {role.value for role in Role}


def test_every_example_names_its_role_view(examples: list[dict]) -> None:
    for example in examples:
        assert example["view"] in views_for(Role(example["role"]))


def test_every_example_passes_the_guard(examples: list[dict]) -> None:
    for example in examples:
        guard.validate_sql(
            example["sql"],
            allowed_views=views_for(Role(example["role"])),
            max_rows=500,
        )


def test_every_example_filters_by_loaibanghi(examples: list[dict]) -> None:
    """A branch column without its discriminator mixes orders, invoices and stock."""
    for example in examples:
        assert "LoaiBanGhi" in example["sql"], example["id"]


def test_every_example_references_only_its_role_view(examples: list[dict]) -> None:
    for example in examples:
        parsed = sqlglot.parse_one(example["sql"], read="mysql")
        tables = {table.name.lower() for table in parsed.find_all(sqlglot.exp.Table)}
        assert tables <= {example["view"].lower()}, example["id"]


@pytest.mark.anyio
async def test_every_example_uses_columns_that_exist_in_its_view(
    examples: list[dict], session: AsyncSession, seed_views: None
) -> None:
    for example in examples:
        view = example["view"]
        result = await session.execute(text(f"PRAGMA table_info({view})"))
        columns = {row[1] for row in result.all()}
        parsed = sqlglot.parse_one(example["sql"], read="mysql")
        aliases = {alias.alias_or_name for alias in parsed.find_all(sqlglot.exp.Alias)}
        used = {
            column.name
            for column in parsed.find_all(sqlglot.exp.Column)
            if column.name != "*" and column.name not in aliases
        }
        assert used <= columns, f"{example['id']} uses stale columns: {used - columns}"
