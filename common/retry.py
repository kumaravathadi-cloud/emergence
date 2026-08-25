"""Generic retry-with-backoff wrapper for external calls (HTTP, LLM).

No business logic lives here — callers decide what a failure means for their
candidate/stage; this module only decides when to retry.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class RetryExhausted(Exception):
    """Raised when all retry attempts fail. Wraps the last exception."""

    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"gave up after {attempts} attempt(s): {last_error!r}")


def call_with_retry(
    fn: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 20.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call `fn` with exponential backoff + jitter, up to `max_attempts` tries.

    Raises RetryExhausted (wrapping the last exception) once attempts run out.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except exceptions as exc:  # noqa: PERF203 - retry loop, not a hot path
            last_error = exc
            if attempt == max_attempts:
                break
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            delay += random.uniform(0, delay * 0.1)
            sleep(delay)

    assert last_error is not None
    raise RetryExhausted(max_attempts, last_error)
