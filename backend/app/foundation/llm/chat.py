"""Minimal OpenAI chat wrapper for grounded answers."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import OpenAI

from app.foundation.llm.runtime_config import ChatRole, RuntimeModelConfig
from app.foundation.llm.usage import (
    Usage,
    UsageRecorder,
    current_run_context,
    extract_usage_from_response,
    purpose_for_role,
    set_last_usage,
)

log = logging.getLogger(__name__)

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


class ChatClient:
    def __init__(
        self,
        client: OpenAI,
        *,
        model: str,
        runtime: RuntimeModelConfig | None = None,
        recorder: UsageRecorder | None = None,
    ) -> None:
        self._client = client
        self._default_model = model
        self._runtime = runtime
        self._recorder = recorder
        self.last_usage: Usage = Usage.unreported()

    @property
    def model(self) -> str:
        """Effective model for the default ``chat`` role (used by CAG keys)."""
        return self.effective_model("chat")

    def effective_model(self, role: ChatRole = "chat") -> str:
        if self._runtime is not None:
            return self._runtime.effective(role)
        return self._default_model

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        role: ChatRole = "chat",
    ) -> dict[str, Any]:
        model = self.effective_model(role)
        response = self._client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
        )
        usage = extract_usage_from_response(response)
        if not usage.reported:
            log.warning("llm_usage_missing model=%s role=%s", model, role)
        self.last_usage = usage
        set_last_usage(usage)
        self._maybe_record(purpose=purpose_for_role(role), model=model, usage=usage)

        content = (response.choices[0].message.content or "").strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = _JSON_BLOCK.search(content)
            if not match:
                raise
            return json.loads(match.group(0))

    def _maybe_record(self, *, purpose: str, model: str, usage: Usage) -> None:
        if self._recorder is None:
            return
        ctx = current_run_context()
        try:
            self._recorder.record(
                purpose=purpose,
                model=model,
                usage=usage,
                session_id=ctx.session_id if ctx else None,
                thread_id=ctx.thread_id if ctx else None,
                owner_id=ctx.owner_id if ctx else None,
            )
        except Exception:  # noqa: BLE001
            log.exception(
                "llm_usage_record_failed purpose=%s model=%s",
                purpose,
                model,
            )
