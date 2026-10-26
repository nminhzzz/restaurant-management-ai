"""Request-local provider accounting, including failed and fallback attempts."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderAttempt:
    model: str
    input_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    output_tokens: int = 0
    usage_reported: bool = False
    succeeded: bool = False


@dataclass
class Usage:
    input_price: float
    output_price: float
    cache_write_price: float = 0.0
    cache_read_price: float = 0.0
    attempts: list[ProviderAttempt] = field(default_factory=list)

    @property
    def call_count(self) -> int:
        return len(self.attempts)

    @property
    def input_tokens(self) -> int:
        """The whole prompt, cached or not, so totals stay comparable across runs."""
        return sum(
            item.input_tokens + item.cache_write_tokens + item.cache_read_tokens
            for item in self.attempts
        )

    @property
    def output_tokens(self) -> int:
        return sum(item.output_tokens for item in self.attempts)

    @property
    def models(self) -> list[str]:
        return list(dict.fromkeys(item.model for item in self.attempts))

    @property
    def cost_complete(self) -> bool:
        return all(item.usage_reported for item in self.attempts)

    @property
    def cost_usd(self) -> float:
        return sum(
            (
                item.input_tokens * self.input_price
                + item.cache_write_tokens * self.cache_write_price
                + item.cache_read_tokens * self.cache_read_price
                + item.output_tokens * self.output_price
            )
            / 1e6
            for item in self.attempts
        )


_current: ContextVar[Usage | None] = ContextVar("ai_usage", default=None)
_active_attempt: ContextVar[ProviderAttempt | None] = ContextVar("ai_active_attempt", default=None)


@contextmanager
def collect_usage(
    *,
    input_price: float,
    output_price: float,
    cache_write_price: float = 0.0,
    cache_read_price: float = 0.0,
) -> Iterator[Usage]:
    usage = Usage(input_price, output_price, cache_write_price, cache_read_price)
    token = _current.set(usage)
    try:
        yield usage
    finally:
        _current.reset(token)


def current_usage() -> Usage | None:
    return _current.get()


@contextmanager
def attempt_context(model: str) -> Iterator[ProviderAttempt]:
    attempt = ProviderAttempt(model)
    usage = _current.get()
    if usage is not None:
        usage.attempts.append(attempt)
    token = _active_attempt.set(attempt)
    try:
        yield attempt
    finally:
        _active_attempt.reset(token)


def start_attempt(model: str) -> ProviderAttempt:
    active = _active_attempt.get()
    if active is not None:
        return active
    attempt = ProviderAttempt(model)
    usage = _current.get()
    if usage is not None:
        usage.attempts.append(attempt)
    return attempt


def finish_attempt(attempt: ProviderAttempt, payload: dict[str, Any]) -> None:
    attempt.model = str(payload.get("model") or attempt.model)
    usage = payload.get("usage", {})
    if isinstance(usage, dict):
        attempt.usage_reported = "input_tokens" in usage and "output_tokens" in usage
        # input_tokens is only the uncached remainder of the prompt.
        attempt.input_tokens = max(0, int(usage.get("input_tokens") or 0))
        attempt.cache_write_tokens = max(0, int(usage.get("cache_creation_input_tokens") or 0))
        attempt.cache_read_tokens = max(0, int(usage.get("cache_read_input_tokens") or 0))
        # output_tokens already includes thinking tokens; never double-count them.
        attempt.output_tokens = max(0, int(usage.get("output_tokens") or 0))
    attempt.succeeded = True
