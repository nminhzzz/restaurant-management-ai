"""Step 3 — SQL generation through the configured LLM.

Every candidate goes straight through `guard.validate_for_role`. A malformed candidate
costs one of the `ai_max_sql_attempts` (two) generations and running out raises; a
candidate that reaches beyond the caller's permission (`OutOfScopeError`) ends the turn
at once with no regeneration. The attempt budget is shared with the orchestrator, which
spends one more generation when the database rejects a validated query. The cache
key includes the role, because the same words asked by another role must never reuse
an answer produced under a different scope (FR-AI-05).

The quota is reserved and persisted by the orchestration service before this module runs.
The SQL cache remains process-local and role-scoped.
"""

import asyncio
import re
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date
from time import monotonic

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import BusinessRuleError
from app.modules.ai import guard, llm
from app.modules.ai.errors import ClarificationNeeded
from app.modules.ai.guard import OutOfScopeError, ValidatedSql
from app.modules.ai.pipeline.normalize import normalize_question
from app.modules.ai.pipeline.prompt import ROLE_SCOPE_NOTE, build_prompt
from app.modules.ai.scope import views_for
from app.shared.roles import Role

CLARIFY_PREFIX = "CLARIFY:"
SQL_CACHE_TTL_SECONDS = 30.0
SQL_CACHE_MAX_ENTRIES = 256

_TEMPORAL_PATTERN = re.compile(
    r"\b(?:hôm nay|hôm qua|hôm kia|tuần này|tuần trước|tuần qua|tháng này|"
    r"tháng trước|tháng qua|năm nay|năm trước|(?:\d+)\s*(?:ngày|tuần|tháng|năm)\s+"
    r"(?:qua|gần đây)|(?:ngày|tháng|năm)\s+\d{1,4}(?:[/\-]\d{1,2}){0,2})\b"
)
_VOLATILE_QUESTION = re.compile(
    r"\b(?:tồn kho|tồn|nguyên liệu|giữ chỗ|giữ món|đang giữ|còn phục vụ|"
    r"phục vụ được|số suất|suất còn|công suất)\b",
    re.IGNORECASE,
)
_CacheKey = tuple[object, ...]
_cache: OrderedDict[_CacheKey, tuple[str, float]] = OrderedDict()


@dataclass
class AttemptBudget:
    """SQL generations still available to one question (NFR-06: at most two)."""

    remaining: int

    def take(self) -> bool:
        if self.remaining <= 0:
            return False
        self.remaining -= 1
        return True


def reset_state() -> None:
    """Clear the process-local SQL cache (used between tests)."""
    _cache.clear()


def temporal_parameters(question: str) -> tuple[str, ...]:
    """Capture explicit date and relative-period phrases in a normalized question."""
    normalized = normalize_question(question).casefold()
    return tuple(_TEMPORAL_PATTERN.findall(normalized))


def is_volatile_question(question: str) -> bool:
    """Questions about live stock, holds, or service capacity must bypass caches."""
    return _VOLATILE_QUESTION.search(normalize_question(question)) is not None


def permission_fingerprint(
    role: Role, allowed_views: frozenset[str] | None = None
) -> tuple[tuple[str, ...], str]:
    """Version the cache by the live view allow-list and role scope description."""
    views = allowed_views if allowed_views is not None else views_for(role)
    return tuple(sorted(views)), ROLE_SCOPE_NOTE[role]


def cache_context_key(
    user_id: int,
    question: str,
    role: Role,
    effective_business_date: date,
    *,
    allowed_views: frozenset[str] | None = None,
) -> _CacheKey:
    """Shared isolation context for SQL and interpretation entries."""
    normalized = normalize_question(question)
    return (
        user_id,
        role.value,
        permission_fingerprint(role, allowed_views),
        normalized,
        temporal_parameters(normalized),
        effective_business_date,
    )


def _cached_sql(key: _CacheKey, *, role: Role, max_rows: int) -> ValidatedSql | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    sql, expires_at = entry
    if expires_at <= monotonic():
        del _cache[key]
        return None
    try:
        validated = guard.validate_for_role(sql, role, max_rows=max_rows)
    except BusinessRuleError:
        del _cache[key]
        return None
    _cache.move_to_end(key)
    return validated


def _store_sql(key: _CacheKey, sql: str) -> None:
    if SQL_CACHE_TTL_SECONDS <= 0 or SQL_CACHE_MAX_ENTRIES <= 0:
        return
    now = monotonic()
    for expired_key, (_, expires_at) in list(_cache.items()):
        if expires_at <= now:
            del _cache[expired_key]
    _cache[key] = (sql, now + SQL_CACHE_TTL_SECONDS)
    _cache.move_to_end(key)
    while len(_cache) > SQL_CACHE_MAX_ENTRIES:
        _cache.popitem(last=False)


def invalidate_sql(user_id: int, question: str, role: Role, effective_business_date: date) -> None:
    """Drop a cached query the database rejected, so a retry cannot reuse it."""
    key = cache_context_key(
        user_id, question, role, effective_business_date, allowed_views=views_for(role)
    )
    _cache.pop(key, None)


async def generate_sql(
    session: AsyncSession,
    question: str,
    role: Role,
    user_id: int,
    effective_business_date: date,
    *,
    budget: AttemptBudget | None = None,
    feedback: str | None = None,
) -> ValidatedSql:
    """Validated SQL for this question, or a raised signal for the orchestrator.

    `feedback` is the database's complaint about the previous query; it bypasses the
    cache and is passed to the model on the next generation.
    """
    settings = get_settings()
    normalized = normalize_question(question)
    allowed = views_for(role)
    attempts = budget if budget is not None else AttemptBudget(settings.ai_max_sql_attempts)
    cache_key = cache_context_key(
        user_id,
        normalized,
        role,
        effective_business_date,
        allowed_views=allowed,
    )
    volatile = is_volatile_question(normalized)
    cached = (
        None
        if volatile or feedback is not None
        else _cached_sql(cache_key, role=role, max_rows=settings.ai_max_rows)
    )
    if cached is not None:
        return cached

    client = llm.get_client()
    last_error: BusinessRuleError | None = None

    while attempts.take():
        prompt = await build_prompt(
            session, normalized, role, effective_business_date=effective_business_date
        )
        if feedback is not None:
            prompt += f"\n\nLần trước câu SQL bị cơ sở dữ liệu từ chối: {feedback}. Hãy sửa lại."
            feedback = None
        elif last_error is not None:
            prompt += f"\n\nLần trước câu SQL chưa hợp lệ: {last_error}. Hãy sửa lại."
        raw = await asyncio.to_thread(client.complete, prompt) or ""
        text = raw.strip()

        if text.upper().startswith(CLARIFY_PREFIX):
            raise ClarificationNeeded(text[len(CLARIFY_PREFIX) :].strip())

        try:
            sql = guard.validate_for_role(text, role, max_rows=settings.ai_max_rows)
        except OutOfScopeError:
            # A request beyond the caller's permission is final: no second generation.
            raise
        except BusinessRuleError as exc:
            last_error = exc
            continue

        if not volatile:
            _store_sql(cache_key, sql)
        return sql

    raise BusinessRuleError(guard.SQL_REJECTED_MESSAGE)
