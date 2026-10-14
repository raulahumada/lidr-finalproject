"""Provider-reported chat token usage (ledger + HTTP payloads).

Never invent tokens from tiktoken or character counts — only copy what the
provider returned (or mark ``reported=false``).

|| Uso de tokens reportado por el proveedor (ledger + payloads HTTP).
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Literal, Protocol

UsagePurpose = Literal["answer", "grounded_composer", "prompt_specialist"]

PURPOSE_BY_ROLE: dict[str, UsagePurpose] = {
    "chat": "answer",
    "composer": "grounded_composer",
    "prompt_specialist": "prompt_specialist",
}


@dataclass(frozen=True)
class Usage:
    """Token counts for one chat completion."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    reported: bool = False

    @classmethod
    def unreported(cls) -> Usage:
        return cls()

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "reported": self.reported,
        }


class UsageRecorder(Protocol):
    """Persist one ledger row. Failures are handled by the caller (fail-open)."""

    def record(
        self,
        *,
        purpose: str,
        model: str,
        usage: Usage,
        session_id: str | None = None,
        thread_id: str | None = None,
        owner_id: str | None = None,
    ) -> None: ...


@dataclass
class UsageRunContext:
    """Per-request / per-background-thread metadata for ledger rows."""

    session_id: str | None = None
    thread_id: str | None = None
    owner_id: str | None = None
    activity_log: Any | None = None  # GraphActivityLog; avoid circular import


_run_ctx: ContextVar[UsageRunContext | None] = ContextVar(
    "llm_usage_run_ctx", default=None
)
_last_usage: ContextVar[Usage] = ContextVar(
    "llm_usage_last", default=Usage.unreported()
)


def bind_usage_run(
    *,
    session_id: str | None = None,
    thread_id: str | None = None,
    owner_id: str | None = None,
    activity_log: Any | None = None,
) -> Any:
    """Set run context and reset last usage. Returns a token for ``reset_usage_run``."""
    _last_usage.set(Usage.unreported())
    return _run_ctx.set(
        UsageRunContext(
            session_id=session_id,
            thread_id=thread_id,
            owner_id=owner_id,
            activity_log=activity_log,
        )
    )


def reset_usage_run(token: Any) -> None:
    _run_ctx.reset(token)


def get_last_usage() -> Usage:
    return _last_usage.get()


def set_last_usage(usage: Usage) -> None:
    _last_usage.set(usage)
    ctx = _run_ctx.get()
    if ctx is None:
        return
    log = ctx.activity_log
    tid = ctx.thread_id
    if log is not None and tid and hasattr(log, "set_usage"):
        log.set_usage(tid, usage.to_dict())


def current_run_context() -> UsageRunContext | None:
    return _run_ctx.get()


def extract_usage_from_response(response: Any) -> Usage:
    """Copy OpenAI-compatible usage fields; never invent counts."""
    raw = getattr(response, "usage", None)
    if raw is None:
        return Usage.unreported()
    try:
        prompt = getattr(raw, "prompt_tokens", None)
        completion = getattr(raw, "completion_tokens", None)
        total = getattr(raw, "total_tokens", None)
        if prompt is None or completion is None:
            return Usage.unreported()
        input_tokens = int(prompt)
        output_tokens = int(completion)
        if total is None:
            total_tokens = input_tokens + output_tokens
        else:
            total_tokens = int(total)
    except (TypeError, ValueError):
        return Usage.unreported()
    return Usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        reported=True,
    )


def purpose_for_role(role: str) -> str:
    return PURPOSE_BY_ROLE.get(role, role)
