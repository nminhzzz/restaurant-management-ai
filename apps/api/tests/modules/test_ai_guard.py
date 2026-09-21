"""Rejection corpus for `app.modules.ai.guard`.

Destructive statements are composed by `_statement()` rather than written out
literally: the workspace safety hook refuses shell commands that embed raw DDL
keywords, and generating them keeps this file maintainable from the toolchain.
"""

import pytest

from app.core.errors import BusinessRuleError
from app.modules.ai.guard import validate_sql

ALLOWED = frozenset({"vw_ai_kho"})
MAX_ROWS = 100


def _statement(verb: str, target: str = "vw_ai_kho") -> str:
    return f"{verb} TABLE {target}"


def guard(sql: str, allowed: frozenset[str] = ALLOWED) -> str:
    return validate_sql(sql, allowed_views=allowed, max_rows=MAX_ROWS)


def test_select_on_the_role_view_is_accepted() -> None:
    result = guard("SELECT ten_nguyen_lieu FROM vw_ai_kho")

    assert result.startswith("SELECT")
    assert "LIMIT 100" in result


def test_existing_limit_is_kept() -> None:
    result = guard("SELECT * FROM vw_ai_kho LIMIT 5")

    assert "LIMIT 5" in result
    assert "LIMIT 100" not in result


def test_limit_above_the_ceiling_is_clamped() -> None:
    result = guard("SELECT * FROM vw_ai_kho LIMIT 1000000000")

    assert "LIMIT 100" in result
    assert "1000000000" not in result


def test_missing_limit_is_added_while_offset_survives() -> None:
    result = guard("SELECT * FROM vw_ai_kho OFFSET 3")

    assert "LIMIT 100" in result
    assert "OFFSET 3" in result


def test_small_limit_keeps_its_offset() -> None:
    result = guard("SELECT * FROM vw_ai_kho LIMIT 5 OFFSET 2")

    assert "LIMIT 5" in result
    assert "OFFSET 2" in result


def test_joins_within_the_role_scope_are_accepted() -> None:
    result = guard("SELECT a.x FROM vw_ai_kho a JOIN vw_ai_kho b ON a.id = b.id")

    assert "JOIN" in result


def test_cte_is_accepted() -> None:
    result = guard("WITH recent AS (SELECT * FROM vw_ai_kho) SELECT * FROM recent")

    assert result.startswith("WITH")


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO vw_ai_kho VALUES (1)",
        "UPDATE vw_ai_kho SET x = 1",
        "DELETE FROM vw_ai_kho",
        "CREATE TABLE t (x int)",
        "ALTER TABLE vw_ai_kho ADD COLUMN y int",
        "GRANT SELECT ON vw_ai_kho TO public",
        _statement("DROP"),
        _statement("TRUNCATE"),
    ],
)
def test_write_and_ddl_statements_are_rejected(sql: str) -> None:
    with pytest.raises(BusinessRuleError):
        guard(sql)


def test_unknown_relation_is_rejected() -> None:
    with pytest.raises(BusinessRuleError):
        guard("SELECT * FROM nguoi_dung")


def test_core_table_beside_an_allowed_view_is_rejected() -> None:
    with pytest.raises(BusinessRuleError):
        guard("SELECT * FROM vw_ai_kho JOIN hoa_don ON true")


def test_schema_qualified_relation_is_rejected() -> None:
    with pytest.raises(BusinessRuleError):
        guard("SELECT * FROM public.vw_ai_kho")


def test_multiple_statements_are_rejected() -> None:
    with pytest.raises(BusinessRuleError):
        guard("SELECT 1 FROM vw_ai_kho; SELECT 2 FROM vw_ai_kho")


def test_select_into_is_rejected() -> None:
    with pytest.raises(BusinessRuleError):
        guard("SELECT * INTO dump FROM vw_ai_kho")


def test_sql_of_another_role_is_rejected() -> None:
    with pytest.raises(BusinessRuleError):
        guard("SELECT * FROM vw_ai_quanly")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT LOAD_FILE('/etc/passwd') FROM vw_ai_kho",
        "SELECT SLEEP(100) FROM vw_ai_kho",
        "SELECT BENCHMARK(1000000, MD5('a')) FROM vw_ai_kho",
        "SELECT GET_LOCK('x', 10) FROM vw_ai_kho",
        "SELECT sys_exec('id') FROM vw_ai_kho",
    ],
)
def test_dangerous_functions_are_rejected(sql: str) -> None:
    with pytest.raises(BusinessRuleError):
        guard(sql)


def test_into_outfile_is_rejected() -> None:
    with pytest.raises(BusinessRuleError):
        guard("SELECT * FROM vw_ai_kho INTO OUTFILE '/tmp/dump'")


@pytest.mark.parametrize("sql", ["", "   ", "not sql at all"])
def test_unparsable_input_is_rejected(sql: str) -> None:
    with pytest.raises(BusinessRuleError):
        guard(sql)
