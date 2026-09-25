"""Chart selection for the assistant's answers (FR-AI-07).

Pure rules, no model call: the shape of the result decides the chart, so the same data
always produces the same picture and nothing here can be talked out of its choice.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

DATE_HINTS = ("date", "ngay", "thang", "thoidiem", "hour", "gio", "time", "week", "tuan")
SHARE_HINTS = ("tytrong", "tỷ trọng", "tile", "phamtram", "percent", "share")


@dataclass(frozen=True)
class ChartSpec:
    type: str
    x: str
    y: list[str]


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _looks_like_date(column: str) -> bool:
    lowered = column.lower().replace("_", "")
    return any(hint in lowered for hint in DATE_HINTS)


def _looks_like_share(column: str) -> bool:
    lowered = column.lower().replace("_", "")
    return any(hint in lowered for hint in SHARE_HINTS)


def choose_chart(columns: list[str], rows: list[dict[str, Any]]) -> ChartSpec | None:
    """A line, bar or doughnut spec when the data has a chart shape, else `None`."""
    if len(columns) < 2 or not rows:
        return None

    numeric = [
        column for column in columns if all(_number(row.get(column)) is not None for row in rows)
    ]
    categorical = [column for column in columns if column not in numeric]
    if not numeric or not categorical:
        return None

    x = categorical[0]
    y = [numeric[-1]] if _looks_like_share(numeric[-1]) else [numeric[0]]

    if _looks_like_date(x):
        return ChartSpec(type="line", x=x, y=y)

    values = [_number(row.get(y[0])) or 0.0 for row in rows]
    if _looks_like_share(y[0]) and 0 < sum(values) <= 101:
        return ChartSpec(type="doughnut", x=x, y=y)

    if len(rows) >= 2:
        return ChartSpec(type="bar", x=x, y=y)
    return None
