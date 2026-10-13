"""SQL guard: the only path from generated text to an executed query.

Rules enforced here, in order (NFR-06, risk register items 1 and 3):

1. exactly one statement, written without comments or optimizer hints (a `/*+ ... */`
   hint such as `MAX_EXECUTION_TIME` would lift the statement timeout, and `/*! ... */`
   is executed by MySQL);
2. a read-only query — no DML, no DDL, no `SELECT ... INTO`, no lock clause
   (`FOR UPDATE`, `LOCK IN SHARE MODE`), no user/system variables or placeholders;
3. every referenced relation is an allow-listed view for the caller's role. CTEs are
   resolved in scope: a CTE may only be read by the statements that follow it, may not
   reuse an allow-listed name, and may not be recursive, so a CTE can never launder a
   core table into the allow-list;
4. every referenced column is a column of the role's view or an alias the query itself
   defines (optional `allowed_columns`; the product always passes it);
5. no file/locking/DoS/system-information function (`LOAD_FILE`, `SLEEP`, `BENCHMARK`,
   `GET_LOCK`, `DATABASE`, `VERSION`, `EXTRACTVALUE`, `sys_exec`, …);
6. the result is capped at `ai_max_rows` — a smaller LIMIT is honoured, a larger or
   non-literal LIMIT is clamped, and a missing LIMIT is added.

The result is a `ValidatedSql`, the only type the executor accepts, so no caller can
run text that skipped this function. The row ceiling here is a guard-level ceiling only:
`ai_sql_timeout_seconds` (statement timeout in the executor) and the role's read-only
database account remain the outer layers.
"""

from collections.abc import Iterable

import sqlglot
from sqlglot import exp
from sqlglot.dialects.dialect import Dialect
from sqlglot.errors import SqlglotError

from app.core.errors import BusinessRuleError
from app.modules.ai.scope import columns_for, foreign_columns_for, views_for
from app.shared.roles import Role

_DIALECT = "mysql"
# Statements that write or change schema: asking the assistant for one is a request
# beyond the read-only permission, so it ends the turn instead of earning a retry.
_WRITE_NODES = (
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
_FORBIDDEN_NODES = (
    exp.Into,
    exp.Hint,
    exp.Lock,
    # `@a`, `@a := 1`, `@@global.x`, `?`, `:name` — state, or a bind slot nobody fills.
    exp.Parameter,
    exp.SessionParameter,
    exp.Placeholder,
    exp.CurrentSchema,
    exp.CurrentCatalog,
    exp.CurrentVersion,
    exp.CurrentUser,
)
# Table-level modifiers that have no business on a role view (index hints steer the
# optimizer; the others address storage the views do not have).
_FORBIDDEN_TABLE_ARGS = ("hints", "partition", "version", "sample", "pivots")
# MySQL functions that reach outside the read-only data plane: file access, deliberate
# stalls, user-level locking, the `sys` UDF bridge, and server/session introspection or
# error-based exfiltration helpers. `SELECT ... INTO OUTFILE` is not in this list because
# the parser already rejects it as unparsable, and is caught earlier.
_FORBIDDEN_FUNCTIONS = frozenset(
    {
        "load_file",
        "sleep",
        "pg_sleep",
        "benchmark",
        "get_lock",
        "release_lock",
        "release_all_locks",
        "is_free_lock",
        "is_used_lock",
        "master_pos_wait",
        "source_pos_wait",
        "wait_for_executed_gtid_set",
        "wait_until_sql_thread_after_gtids",
        "sys_exec",
        "sys_eval",
        "database",
        "schema",
        "user",
        "current_user",
        "session_user",
        "system_user",
        "current_role",
        "version",
        "connection_id",
        "last_insert_id",
        "found_rows",
        "row_count",
        "extractvalue",
        "updatexml",
    }
)
_FORBIDDEN_FUNCTION_PREFIX = "sys_"

SQL_REJECTED_MESSAGE = "Không thể tạo truy vấn an toàn cho câu hỏi này."


class OutOfScopeError(BusinessRuleError):
    """The query reaches beyond the caller's permission (other relations/roles, writes).

    Unlike a malformed query this is not worth another generation: the pipeline ends the
    turn at once (report §4.1.3, NFR-06).
    """


def _reject() -> BusinessRuleError:
    return BusinessRuleError(SQL_REJECTED_MESSAGE)


def _out_of_scope() -> OutOfScopeError:
    return OutOfScopeError(SQL_REJECTED_MESSAGE)


_ISSUER = object()


class ValidatedSql(str):
    """SQL text that went through `validate_sql`.

    Only `validate_sql` holds the issuer token, and the executor accepts nothing else, so
    "every query passes the guard" is a property of the types and not of caller discipline.
    """

    __slots__ = ()

    def __new__(cls, value: str, *, issuer: object) -> "ValidatedSql":
        if issuer is not _ISSUER:
            raise TypeError("ValidatedSql can only be issued by guard.validate_sql")
        return super().__new__(cls, value)


def _function_name(node: exp.Expr) -> str | None:
    """Return the lower-cased callee name, or None when the node is not a call."""
    if isinstance(node, exp.Anonymous):
        return str(node.this).lower()
    if isinstance(node, exp.Func):
        return str(node.sql_name()).lower()
    return None


def _children(node: exp.Expr) -> Iterable[exp.Expr]:
    for value in node.args.values():
        if isinstance(value, exp.Expr):
            yield value
        elif isinstance(value, list):
            yield from (item for item in value if isinstance(item, exp.Expr))


def _check_relations(node: exp.Expr, visible: frozenset[str], allowed: frozenset[str]) -> None:
    """Resolve every table reference in scope; anything unresolved is rejected.

    `visible` holds the CTE names that the current position can legally read. A CTE
    becomes visible only after its own definition, so `WITH x AS (SELECT * FROM x)`
    reads the *real* `x` and is rejected, instead of being waved through because a CTE
    happens to carry the same name.
    """
    with_clause = next((child for child in _children(node) if isinstance(child, exp.With)), None)
    if with_clause is not None:
        if with_clause.args.get("recursive"):
            raise _reject()
        scope = visible
        for cte in with_clause.expressions:
            name = cte.alias_or_name.lower()
            if not name or name in allowed:
                raise _reject()
            _check_relations(cte.this, scope, allowed)
            scope = scope | {name}
        visible = scope

    if isinstance(node, exp.Table):
        if node.db or node.catalog or not isinstance(node.this, exp.Identifier):
            raise _out_of_scope()
        if any(node.args.get(key) for key in _FORBIDDEN_TABLE_ARGS):
            raise _reject()
        if node.name.lower() not in visible and node.name.lower() not in allowed:
            raise _out_of_scope()

    for child in _children(node):
        if child is not with_clause:
            _check_relations(child, visible, allowed)


def _defined_names(expression: exp.Expr) -> set[str]:
    """Names the query itself introduces: select aliases, CTE/derived-table aliases."""
    names: set[str] = set()
    for node in expression.walk():
        if isinstance(node, exp.Alias) and node.alias:
            names.add(node.alias.lower())
        elif isinstance(node, exp.TableAlias):
            names.add(node.name.lower())
            names.update(column.name.lower() for column in node.columns)
    return names


def _check_columns(
    expression: exp.Expr, allowed_columns: Iterable[str], restricted_columns: Iterable[str]
) -> None:
    permitted = {column.lower() for column in allowed_columns}
    restricted = {column.lower() for column in restricted_columns} - permitted
    permitted |= _defined_names(expression)
    for column in expression.find_all(exp.Column):
        if isinstance(column.this, exp.Star):
            continue
        name = column.name.lower()
        if name in permitted:
            continue
        # A column that exists in another role's view is a scope violation; one that
        # exists nowhere is just a bad query the model may correct.
        raise _out_of_scope() if name in restricted else _reject()


def _check_comments(sql: str, expression: exp.Expr) -> None:
    """Reject any comment: it can carry an optimizer hint or a MySQL executable comment."""
    for token in Dialect.get_or_raise(_DIALECT).tokenize(sql):
        if token.comments:
            raise _reject()
    if any(node.comments for node in expression.walk()):
        raise _reject()


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
    allowed_columns: Iterable[str] | None = None,
    restricted_columns: Iterable[str] = (),
) -> ValidatedSql:
    """Return normalised, row-capped, comment-free SQL, or raise BusinessRuleError."""
    if not sql or not sql.strip():
        raise _reject()

    try:
        statements = sqlglot.parse(sql, read=_DIALECT)
        if len(statements) != 1 or statements[0] is None:
            raise _reject()
        expression = statements[0]
        _check_comments(sql, expression)
    except SqlglotError as exc:
        raise _reject() from exc

    if isinstance(expression, exp.Subquery):
        # `(SELECT ...)` is still a read; it is only a shape the model should not use.
        raise _reject()
    if not isinstance(expression, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        # Any other statement (writes, DDL, GRANT, SET, SHOW...) is beyond a read-only role.
        raise _out_of_scope()
    # `SELECT DATABASE()` and friends read the server, not a view: a table is required.
    if expression.find(exp.Table) is None:
        raise _reject()

    for node in expression.walk():
        if isinstance(node, _WRITE_NODES):
            raise _out_of_scope()
        if isinstance(node, _FORBIDDEN_NODES):
            raise _reject()
        callee = _function_name(node)
        if callee is not None and (
            callee.startswith(_FORBIDDEN_FUNCTION_PREFIX) or callee in _FORBIDDEN_FUNCTIONS
        ):
            raise _reject()

    allowed = frozenset(view.lower() for view in allowed_views)
    _check_relations(expression, frozenset(), allowed)
    if allowed_columns is not None:
        _check_columns(expression, allowed_columns, restricted_columns)

    capped = _apply_row_ceiling(expression, max_rows)
    return ValidatedSql(capped.sql(dialect=_DIALECT, comments=False), issuer=_ISSUER)


def validate_for_role(sql: str, role: Role, *, max_rows: int) -> ValidatedSql:
    """`validate_sql` with the role's views and columns — the call every runtime path uses."""
    return validate_sql(
        sql,
        allowed_views=views_for(role),
        max_rows=max_rows,
        allowed_columns=columns_for(role),
        restricted_columns=foreign_columns_for(role),
    )
