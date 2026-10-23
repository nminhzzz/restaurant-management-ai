"""Generate guarded SQL with shared, durable cache and daily reservations.

Quota counts logical SQL-generation calls (`client.complete`), including guard
retries. Transport fallback inside the adapter and result interpretation are not
additional SQL generations. Each reservation commits before invoking the model.
"""

import hashlib
import json
from collections.abc import Awaitable, Callable
from datetime import UTC
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import BusinessRuleError
from app.modules.ai import guard, llm, runtime
from app.modules.ai.errors import ClarificationNeeded
from app.modules.ai.pipeline.normalize import normalize_question
from app.modules.ai.pipeline.prompt import build_prompt
from app.modules.ai.scope import views_for
from app.shared import business_date
from app.shared.roles import Role

CLARIFY_PREFIX = "CLARIFY:"
# Guard implementation changes invalidate previously accepted candidates too.
_GUARD_FINGERPRINT = hashlib.sha256(Path(guard.__file__).read_bytes()).hexdigest()


async def generate_sql(
    session: AsyncSession,
    question: str,
    role: Role,
    user_id: int | None = None,
    history: list[tuple[str, str | None, str | None]] | None = None,
    validate_execution: Callable[[str], Awaitable[None]] | None = None,
) -> str:
    """Return SQL only after validation, including when it came from shared cache."""
    settings = get_settings()
    normalized = normalize_question(question)
    allowed = views_for(role)
    quota = settings.ai_daily_question_quota
    try:
        # The manager's configured per-user daily limit wins over the env default.
        from app.modules.settings.service import get_config

        quota = (await get_config(session)).ai_daily_question_quota
    except Exception:
        pass
    # Schema reflection uses the caller's connection and never locks runtime tables.
    # Include the full prompt: view columns, examples and prompt policy all matter.
    base_prompt = await build_prompt(session, normalized, role, history=history)
    now = business_date.now()
    day = business_date.business_date_of(now)
    cache_context = {
        "role": role.value,
        "day": day.isoformat(),
        "prompt": base_prompt,
        "provider": settings.ai_provider,
        "endpoint": settings.llm_base_url,
        "ollama_endpoint": settings.ai_ollama_base_url,
        "model": settings.llm_model,
        "client_model": getattr(llm.get_client(), "model", None),
        "fallback_model": settings.llm_fallback_model or settings.ai_config_c_model,
        "reasoning_effort": settings.llm_reasoning_effort,
        "guard": _GUARD_FINGERPRINT,
        "views": sorted(allowed),
        "max_rows": settings.ai_max_rows,
        "timeout": settings.ai_sql_timeout_seconds,
        "attempts": settings.ai_max_sql_attempts,
        "ttl": settings.ai_sql_cache_ttl_seconds,
    }
    cache_key = hashlib.sha256(
        json.dumps(cache_context, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    store = runtime.get_runtime_store()
    # Store naive UTC in MySQL DATETIME; BusinessDate itself uses restaurant time.
    cache_now = now.astimezone(UTC).replace(tzinfo=None)
    # NFR-16 counts questions, not provider calls: a cache hit is still a question
    # answered, and a retry inside one question must not burn a second slot.
    call_day = business_date.business_date_of(business_date.now())
    await store.reserve_call(call_day, quota, user_id or 0)
    cached = await store.get_sql(cache_key, cache_now)
    if cached is not None:
        try:
            sql = guard.validate_sql(cached, allowed_views=allowed, max_rows=settings.ai_max_rows)
            if validate_execution is not None:
                await validate_execution(sql)
            return sql
        except Exception:
            # Corrupt/outdated SQL or changed schema must never bypass guard/execution.
            pass

    client = llm.get_client()
    last_error: BusinessRuleError | None = None
    for _ in range(settings.ai_max_sql_attempts):
        prompt = base_prompt
        if last_error is not None:
            prompt += f"\n\nLần trước câu SQL chưa hợp lệ: {last_error}. Hãy sửa lại."
        raw = await llm.complete_async(client, prompt) or ""
        text = raw.strip()

        if text.upper().startswith(CLARIFY_PREFIX):
            raise ClarificationNeeded(text[len(CLARIFY_PREFIX) :].strip())

        try:
            sql = guard.validate_sql(text, allowed_views=allowed, max_rows=settings.ai_max_rows)
        except BusinessRuleError as exc:
            last_error = exc
            continue

        if validate_execution is not None:
            try:
                await validate_execution(sql)
            except TimeoutError:
                raise
            except Exception:
                last_error = BusinessRuleError(
                    "Truy vấn chưa thực thi được; hãy kiểm tra lại tên cột "
                    "và kiểu dữ liệu theo schema."
                )
                continue
        await store.put_sql(cache_key, sql, cache_now, settings.ai_sql_cache_ttl_seconds)
        return sql

    raise BusinessRuleError(guard.SQL_REJECTED_MESSAGE)
