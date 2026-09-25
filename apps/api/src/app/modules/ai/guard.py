"""SQL guard: the only path from generated text to an executed query.

Rules enforced here, in order (NFR-06, risk register items 1 and 3):

1. exactly one statement;
2. a read-only query — no DML, no DDL, no `SELECT ... INTO`;
3. every referenced relation is an allow-listed view for the caller's role;
4. no file/locking/DoS function (`LOAD_FILE`, `SLEEP`, `BENCHMARK`, `GET_LOCK`, `sys_exec`, …);
5. the result is capped at `ai_max_rows` — a smaller LIMIT is honoured, a larger or
   non-literal LIMIT is clamped, and a missing LIMIT is added.

The row ceiling here is a guard-level ceiling only: `ai_sql_timeout_seconds` (statement
timeout in the executor) and the role's read-only database account remain the outer layers.
"""

from collections.abc import Iterable

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.core.errors import BusinessRuleError

_DIALECT = "mysql"
_FORBIDDEN_NODES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.Command,
    exp.Merge,
    exp.TruncateTable,
)
# MySQL functions that reach outside the read-only data plane: file access, deliberate
# stalls, user-level locking and the `sys` UDF bridge. `SELECT ... INTO OUTFILE` is not
# in this list because the parser already rejects it as unparsable, and is caught earlier.
_FORBIDDEN_FUNCTIONS = frozenset(
    {
        "load_file",
        "sleep",
        "benchmark",
        "get_lock",
        "release_lock",
        "is_free_lock",
        "is_used_lock",
        "sys_exec",
        "sys_eval",
    }
)
_FORBIDDEN_FUNCTION_PREFIX = "sys_"

SQL_REJECTED_MESSAGE = "Không thể tạo truy vấn an toàn cho câu hỏi này."


def _relation_name(table: exp.Table) -> str:
    return table.name.lower()


def _collect_cte_names(expression: exp.Expression) -> set[str]:
    return {cte.alias_or_name.lower() for cte in expression.find_all(exp.CTE)}


def _function_name(node: exp.Expr) -> str | None:
    """Return the lower-cased callee name, or None when the node is not a call."""
    if isinstance(node, exp.Anonymous):
        return str(node.this).lower()
    if isinstance(node, exp.Func):
        return str(node.sql_name()).lower()
    return None


def _apply_row_ceiling(expression: exp.Query, max_rows: int) -> exp.Query:
    """Force the result set down to `max_rows`, preserving a smaller LIMIT/OFFSET."""
    limit = expression.args.get("limit")
    if limit is None:
        return expression.limit(max_rows, copy=False)

    value = limit.expression
    if isinstance(value, exp.Literal) and value.is_int and int(value.this) <= max_rows:
        return expression

    # A larger, non-literal or unparsable limit is replaced, keeping any OFFSET intact.
    limit.set("expression", exp.Literal.number(max_rows))
    return expression


def validate_sql(
    sql: str,
    *,
    allowed_views: Iterable[str],
    max_rows: int,
) -> str:
    """Return a normalised, row-capped SQL string, or raise BusinessRuleError."""
    if not sql or not sql.strip():
        raise BusinessRuleError(SQL_REJECTED_MESSAGE)

    try:
        statements = sqlglot.parse(sql, read=_DIALECT)
    except ParseError as exc:
        raise BusinessRuleError(SQL_REJECTED_MESSAGE) from exc
    if len(statements) != 1 or statements[0] is None:
        raise BusinessRuleError(SQL_REJECTED_MESSAGE)

    expression = statements[0]
    if not isinstance(expression, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        raise BusinessRuleError(SQL_REJECTED_MESSAGE)

    # Block SELECT without FROM (e.g. SELECT database()) unless allow-listed explicitly
    has_table = False
    for _ in expression.find_all(exp.Table):
        has_table = True
        break
    if not has_table:
        # Allow CTE-only or trivial? No - require at least one allowed view
        raise BusinessRuleError(SQL_REJECTED_MESSAGE)
    for node in expression.walk():
        if isinstance(node, exp.Parameter):
            raise BusinessRuleError(SQL_REJECTED_MESSAGE)
        # Variables like @a are Parameter(Var), already caught; plain Var inside Parameter handled above
        if isinstance(node, (*_FORBIDDEN_NODES, exp.Into)):
            raise BusinessRuleError(SQL_REJECTED_MESSAGE)
        callee = _function_name(node)
        if callee is not None and (
            callee.startswith(_FORBIDDEN_FUNCTION_PREFIX) or callee in _FORBIDDEN_FUNCTIONS
        ):
            raise BusinessRuleError(SQL_REJECTED_MESSAGE)

    allowed = {view.lower() for view in allowed_views}
    permitted_names = allowed | _collect_cte_names(expression)
    for table in expression.find_all(exp.Table):
        if table.db or table.catalog:
            raise BusinessRuleError(SQL_REJECTED_MESSAGE)
        if _relation_name(table) not in permitted_names:
            raise BusinessRuleError(SQL_REJECTED_MESSAGE)

    return _apply_row_ceiling(expression, max_rows).sql(dialect=_DIALECT)
