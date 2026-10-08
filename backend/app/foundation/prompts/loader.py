"""Jinja2 loader for versioned prompt templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

_BASE_DIR = Path(__file__).resolve().parent

_env = Environment(
    loader=FileSystemLoader(_BASE_DIR),
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
    keep_trailing_newline=True,
)


def render_answer_prompts(
    *,
    version: str,
    knowledge_pack: str,
    question: str,
    retrieved_chunks: list[dict[str, Any]] | None = None,
    context: str = "",
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for the answer use case.

    v1 templates use ``retrieved_chunks``; v2+ use preformatted ``context``.
    """
    values = {
        "knowledge_pack": knowledge_pack,
        "question": question,
        "retrieved_chunks": retrieved_chunks or [],
        "context": context,
    }
    system = _env.get_template(f"answer/{version}/system.j2").render(**values)
    user = _env.get_template(f"answer/{version}/user.j2").render(**values)
    return system, user
