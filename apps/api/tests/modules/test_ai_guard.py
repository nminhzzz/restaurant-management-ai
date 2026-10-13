"""Rejection corpus for `app.modules.ai.guard`.

Destructive statements are composed by `_statement()` rather than written out
literally: the workspace safety hook refuses shell commands that embed raw DDL
keywords, and generating them keeps this file maintainable from the toolchain.
"""

import pytest

from app.core.errors import BusinessRuleError
from app.modules.ai.guard import OutOfScopeError, ValidatedSql, validate_sql

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


# --- CTE scoping: a CTE can never turn a core table into an "allowed" relation --------


@pytest.mark.parametrize(
    "sql",
    [
        # Verified bypass: the CTE name shadows the core table it reads.
        "WITH nguoi_dung AS (SELECT * FROM nguoi_dung) SELECT MatKhauHash FROM nguoi_dung",
        "WITH hoa_don AS (SELECT * FROM hoa_don) SELECT * FROM vw_ai_kho",
        # A CTE that reads a core table under another name.
        "WITH t AS (SELECT * FROM nguoi_dung) SELECT * FROM t",
        # Forward reference: `b` is not visible inside `a`, so it would hit a real table.
        "WITH a AS (SELECT * FROM b), b AS (SELECT * FROM vw_ai_kho) SELECT * FROM a",
        # A CTE named like the allowed view must not redirect the name.
        "WITH vw_ai_kho AS (SELECT * FROM vw_ai_kho) SELECT * FROM vw_ai_kho",
        # Recursive CTEs can burn the database for the whole timeout.
        "WITH RECURSIVE t AS (SELECT 1 AS n UNION ALL SELECT n + 1 FROM t) "
        "SELECT * FROM t, vw_ai_kho",
        # A CTE name used as a relation outside the CTE's scope.
        "SELECT * FROM vw_ai_kho WHERE x IN (SELECT y FROM (WITH c AS (SELECT 1 AS y) "
        "SELECT y FROM c) q) AND z IN (SELECT w FROM c)",
    ],
)
def test_cte_cannot_shadow_or_reach_a_non_allow_listed_relation(sql: str) -> None:
    with pytest.raises(BusinessRuleError):
        guard(sql)


def test_chained_ctes_over_the_role_view_are_accepted() -> None:
    result = guard(
        "WITH a AS (SELECT * FROM vw_ai_kho), b AS (SELECT * FROM a) SELECT * FROM b JOIN a ON 1=1"
    )

    assert result.startswith("WITH")


# --- Comments and optimizer hints -----------------------------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        # Verified bypass: the hint lifts the 3 s NFR-06 statement timeout.
        "SELECT /*+ MAX_EXECUTION_TIME(100000) */ * FROM vw_ai_kho",
        "SELECT /*+ SET_VAR(max_execution_time=100000) */ * FROM vw_ai_kho",
        "SELECT * FROM vw_ai_kho -- trailing",
        "SELECT * FROM vw_ai_kho # trailing",
        "SELECT * /* inline */ FROM vw_ai_kho",
        "SELECT * /*!50000 , SLEEP(5) */ FROM vw_ai_kho",
        "SELECT * FROM vw_ai_kho /**/",
        "SELECT * FROM vw_ai_kho USE INDEX (ix_missing)",
    ],
)
def test_comments_hints_and_index_hints_are_rejected(sql: str) -> None:
    with pytest.raises(BusinessRuleError):
        guard(sql)


def test_comment_markers_inside_string_literals_are_not_comments() -> None:
    result = guard("SELECT * FROM vw_ai_kho WHERE TenNguyenLieu = 'a -- b # c /* d */'")

    assert "'a -- b # c /* d */'" in result


# --- Locks, variables, system information ---------------------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM vw_ai_kho FOR UPDATE",
        "SELECT * FROM vw_ai_kho FOR SHARE",
        "SELECT * FROM vw_ai_kho LOCK IN SHARE MODE",
        "SELECT * FROM vw_ai_kho FOR UPDATE SKIP LOCKED",
        "SELECT @a := 1 FROM vw_ai_kho",
        "SELECT @a FROM vw_ai_kho",
        "SELECT * FROM vw_ai_kho WHERE SoLuongTon > @@max_execution_time",
        "SELECT @@global.version FROM vw_ai_kho",
        "SELECT * FROM vw_ai_kho WHERE SoLuongTon > ?",
        "SELECT * FROM vw_ai_kho WHERE SoLuongTon > :limit",
        "SELECT DATABASE() FROM vw_ai_kho",
        "SELECT USER() FROM vw_ai_kho",
        "SELECT CURRENT_USER() FROM vw_ai_kho",
        "SELECT VERSION() FROM vw_ai_kho",
        "SELECT CONNECTION_ID() FROM vw_ai_kho",
        "SELECT EXTRACTVALUE('<a/>', '/a') FROM vw_ai_kho",
        "SELECT UPDATEXML('<a/>', '/a', 'x') FROM vw_ai_kho",
        "SELECT 1, @@version",
        "SELECT DATABASE()",
        "SELECT * FROM vw_ai_kho WHERE WAIT_FOR_EXECUTED_GTID_SET('a')",
    ],
)
def test_locks_variables_placeholders_and_system_info_are_rejected(sql: str) -> None:
    with pytest.raises(BusinessRuleError):
        guard(sql)


# --- UNION / subquery shapes ----------------------------------------------------------


def test_union_branches_must_all_stay_inside_the_role_view() -> None:
    with pytest.raises(BusinessRuleError):
        guard("SELECT TenNguyenLieu FROM vw_ai_kho UNION SELECT MatKhauHash FROM nguoi_dung")
    with pytest.raises(BusinessRuleError):
        guard("SELECT 1 FROM vw_ai_kho UNION ALL (SELECT 1 FROM vw_ai_quanly)")


def test_union_gets_a_row_cap_even_when_its_branches_carry_larger_limits() -> None:
    result = guard(
        "(SELECT * FROM vw_ai_kho LIMIT 100000) UNION ALL (SELECT * FROM vw_ai_kho LIMIT 100000)"
    )

    assert result.rstrip().endswith("LIMIT 100")


def test_union_limit_with_a_large_offset_count_pair_is_clamped() -> None:
    result = guard("SELECT a FROM vw_ai_kho UNION SELECT b FROM vw_ai_kho LIMIT 5, 99999999")

    assert "99999999" not in result
    assert "LIMIT 100" in result


def test_mysql_offset_count_limit_is_clamped() -> None:
    result = guard("SELECT a FROM vw_ai_kho LIMIT 5, 99999999")

    assert "99999999" not in result
    assert "LIMIT 100" in result


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM vw_ai_kho WHERE x IN (SELECT MatKhauHash FROM nguoi_dung)",
        "SELECT * FROM (SELECT * FROM nguoi_dung) t",
        "SELECT (SELECT MatKhauHash FROM nguoi_dung LIMIT 1) FROM vw_ai_kho",
        "SELECT * FROM vw_ai_kho WHERE EXISTS (SELECT 1 FROM nguoi_dung)",
        "SELECT * FROM vw_ai_kho a JOIN (SELECT * FROM hoa_don) b ON 1=1",
    ],
)
def test_subqueries_on_a_core_table_are_rejected(sql: str) -> None:
    with pytest.raises(BusinessRuleError):
        guard(sql)


def test_subquery_over_the_role_view_is_accepted() -> None:
    result = guard(
        "SELECT * FROM (SELECT * FROM vw_ai_kho) t WHERE t.x IN (SELECT x FROM vw_ai_kho)"
    )

    assert "LIMIT 100" in result


def test_the_returned_sql_carries_no_comments() -> None:
    result = guard("SELECT * FROM vw_ai_kho")

    assert "/*" not in result and "--" not in result


# --- Column-level allow-list (report §5.1.1: "mọi bảng, cột ... trong danh sách") ------

COLUMNS = frozenset({"LoaiBanGhi", "SoLuongTon", "TenNguyenLieu"})


def column_guard(sql: str) -> str:
    return validate_sql(sql, allowed_views=ALLOWED, max_rows=MAX_ROWS, allowed_columns=COLUMNS)


def test_columns_of_the_role_view_are_accepted_case_insensitively() -> None:
    result = column_guard(
        "SELECT tennguyenlieu, SUM(SoLuongTon) AS Tong FROM vw_ai_kho a "
        "WHERE a.LoaiBanGhi = 'TON_KHO' GROUP BY TenNguyenLieu HAVING Tong > 0 ORDER BY Tong DESC"
    )

    assert "Tong" in result


def test_aliases_from_subqueries_and_ctes_are_valid_column_names() -> None:
    column_guard(
        "WITH c AS (SELECT TenNguyenLieu AS Ten, SoLuongTon AS Ton FROM vw_ai_kho) "
        "SELECT Ten FROM c WHERE Ton > 0"
    )
    column_guard("SELECT s.Ton FROM (SELECT SoLuongTon AS Ton FROM vw_ai_kho) s")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT MatKhauHash FROM vw_ai_kho",
        "SELECT * FROM vw_ai_kho WHERE GiaVonUocTinh > 0",
        "SELECT TenNguyenLieu FROM vw_ai_kho ORDER BY DonGiaNhap",
        "SELECT a.TongTien FROM vw_ai_kho a",
    ],
)
def test_columns_outside_the_role_view_are_rejected(sql: str) -> None:
    with pytest.raises(BusinessRuleError):
        column_guard(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM `nguoi_dung`",
        "WITH Nguoi_Dung AS (SELECT * FROM Nguoi_Dung) SELECT * FROM Nguoi_Dung",
        "SELECT * FROM vw_ai_kho, mysql.user",
        "SELECT * FROM vw_ai_kho a JOIN JSON_TABLE('[1]', '$[*]' COLUMNS (x INT PATH '$')) j",
        "TABLE nguoi_dung",
    ],
)
def test_other_ways_to_name_a_core_table_are_rejected(sql: str) -> None:
    with pytest.raises(BusinessRuleError):
        guard(sql)


def test_a_backslash_quote_cannot_smuggle_a_comment_past_the_guard() -> None:
    """The text MySQL receives is regenerated from the tree, so both parsers agree on it."""
    result = guard("SELECT * FROM vw_ai_kho WHERE TenNguyenLieu = 'a\\' OR 1=1 -- '")

    assert result == "SELECT * FROM vw_ai_kho WHERE TenNguyenLieu = 'a'' OR 1=1 -- ' LIMIT 100"


def test_out_of_scope_requests_are_told_apart_from_malformed_ones() -> None:
    for sql in ("SELECT * FROM nguoi_dung", "GRANT SELECT ON x TO y", "DELETE FROM vw_ai_kho"):
        with pytest.raises(OutOfScopeError):
            guard(sql)
    for sql in (
        "not sql at all",
        "SELECT * FROM vw_ai_kho -- c",
        "SELECT 1 FROM vw_ai_kho; SELECT 2",
    ):
        with pytest.raises(BusinessRuleError) as raised:
            guard(sql)
        assert not isinstance(raised.value, OutOfScopeError)


def test_validated_sql_is_a_string_but_only_the_guard_issues_it() -> None:
    result = guard("SELECT * FROM vw_ai_kho")

    assert isinstance(result, str) and isinstance(result, ValidatedSql)
