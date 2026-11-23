"""The period an answer covers, read from the date filters of the SQL that ran.

AI grading on 14/11/2026 failed 267 of 456 correct answers for not naming the period.
The period comes from the SQL rather than the question: it is what the numbers
actually cover, even when the model resolved "tuần này" differently from the reader.
"""

from datetime import date, datetime, timedelta

import sqlglot
from sqlglot import exp

_OPERATORS: dict[type[exp.Expression], str] = {
    exp.EQ: "=",
    exp.GT: ">",
    exp.GTE: ">=",
    exp.LT: "<",
    exp.LTE: "<=",
}
_FLIPPED = {"=": "=", ">": "<", ">=": "<=", "<": ">", "<=": ">="}


def _day(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def _is_date_column(node: exp.Expression) -> bool:
    if isinstance(node, (exp.Date, exp.Cast, exp.TsOrDsToDate)):
        node = node.this
    if not isinstance(node, exp.Column):
        return False
    name = node.name.lower()
    return name == "businessdate" or name.startswith("ngay") or name.startswith("thoidiem")


_UNIT_DAYS = {"DAY": 1, "WEEK": 7}


def _literal_date(node: exp.Expression, today: date) -> date | None:
    """A date literal, CURDATE(), or one of those shifted by whole days or weeks."""
    if isinstance(node, (exp.Cast, exp.TsOrDsToDate, exp.Date)):
        node = node.this
    if isinstance(node, exp.CurrentDate):
        return today
    if isinstance(node, (exp.DateSub, exp.DateAdd)):
        base = _literal_date(node.this, today)
        unit = node.args.get("unit")
        step = _UNIT_DAYS.get(unit.name.upper() if unit else "DAY")
        amount = node.expression
        if base is None or step is None or not isinstance(amount, exp.Literal):
            return None
        try:
            days = int(amount.this) * step
        except ValueError:
            return None
        return base - timedelta(days) if isinstance(node, exp.DateSub) else base + timedelta(days)
    if not isinstance(node, exp.Literal) or not node.is_string:
        return None
    try:
        return datetime.strptime(node.this[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def period_of(sql: str, today: date) -> str | None:
    """A Vietnamese phrase for the covered period, or None when it cannot be read.

    Only literal bounds are read. A filter built from functions (DATE_SUB, MONTH(...))
    returns None, and the caller asks the prose model to state the period instead.
    """
    try:
        tree = sqlglot.parse_one(sql, read="mysql")
    except sqlglot.errors.ParseError:
        return None
    lower: date | None = None
    upper: date | None = None
    for node in tree.find_all(exp.Between, *_OPERATORS):
        pairs: list[tuple[str, date]]
        if isinstance(node, exp.Between):
            if not _is_date_column(node.this):
                continue
            low = _literal_date(node.args["low"], today)
            high = _literal_date(node.args["high"], today)
            if low is None or high is None:
                return None
            pairs = [(">=", low), ("<=", high)]
        else:
            left, right = node.args["this"], node.args["expression"]
            op, column, other = _OPERATORS[type(node)], left, right
            if not _is_date_column(column):
                op, column, other = _FLIPPED[op], right, left
            if not _is_date_column(column):
                # A date column under a function (MONTH(BusinessDate) = 9) is a filter
                # this reader cannot bound; a subquery's own filters are visited anyway.
                sides = [side for side in (left, right) if not side.find(exp.Select)]
                if any(_is_date_column(c) for side in sides for c in side.find_all(exp.Column)):
                    return None
                continue
            bound = _literal_date(other, today)
            if bound is None:
                return None
            pairs = [(op, bound)]
        for op, bound in pairs:
            if op in ("=", ">=", ">"):
                start = bound + timedelta(days=1) if op == ">" else bound
                lower = start if lower is None else min(lower, start)
            if op in ("=", "<=", "<"):
                end = bound - timedelta(days=1) if op == "<" else bound
                upper = end if upper is None else max(upper, end)
    if lower is None and upper is None:
        return f"tính đến {_day(today)}"
    if lower is not None and upper is not None and lower == upper:
        return f"ngày {_day(lower)}"
    if lower is None:
        return f"đến {_day(upper)}" if upper else None
    return f"từ {_day(lower)} đến {_day(upper or today)}"
