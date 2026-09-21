"""SQL guard: the only path from generated text to an executed query.

Rules enforced here, in order (NFR-06, risk register items 1 and 3):

1. exactly one statement;
2. a read-only query — no DML, no DDL, no `SELECT ... INTO`;
3. every referenced relation is an allow-listed view for the caller's role;
4. a row ceiling is always applied (`ai_max_rows`).
"""

from collections.abc import Iterable

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.core.errors import BusinessRuleError

_DIALECT = "postgres"
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

SQL_REJECTED_MESSAGE = "Không thể tạo truy vấn an toàn cho câu hỏi này."


def _relation_name(table: exp.Table) -> str:
    return table.name.lower()


def _collect_cte_names(expression: exp.Expression) -> set[str]:
    return {cte.alias_or_name.lower() for cte in expression.find_all(exp.CTE)}


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

    for node in expression.walk():
        if isinstance(node, (*_FORBIDDEN_NODES, exp.Into)):
            raise BusinessRuleError(SQL_REJECTED_MESSAGE)

    allowed = {view.lower() for view in allowed_views}
    permitted_names = allowed | _collect_cte_names(expression)
    for table in expression.find_all(exp.Table):
        if table.db or table.catalog:
            raise BusinessRuleError(SQL_REJECTED_MESSAGE)
        if _relation_name(table) not in permitted_names:
            raise BusinessRuleError(SQL_REJECTED_MESSAGE)

    if expression.args.get("limit") is None:
        expression = expression.limit(max_rows, copy=False)

    return expression.sql(dialect=_DIALECT)
