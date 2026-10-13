"""Minimal OpenAI chat wrapper for grounded answers."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import OpenAI

from app.foundation.llm.runtime_config import ChatRole, RuntimeModelConfig

log = logging.getLogger(__name__)

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


class ChatClient:
    def __init__(
        self,
        client: OpenAI,
        *,
        model: str,
        runtime: RuntimeModelConfig | None = None,
    ) -> None:
        self._client = client
        self._default_model = model
        self._runtime = runtime

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
        content = (response.choices[0].message.content or "").strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = _JSON_BLOCK.search(content)
            if not match:
                raise
            return json.loads(match.group(0))
