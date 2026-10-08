"""Minimal OpenAI chat wrapper for grounded answers."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import OpenAI

log = logging.getLogger(__name__)

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


class ChatClient:
    def __init__(self, client: OpenAI, *, model: str) -> None:
        self._client = client
        self.model = model

    def complete_json(self, *, system: str, user: str) -> dict[str, Any]:
        response = self._client.chat.completions.create(
            model=self.model,
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
