"""ChatClient usage extraction + fail-open recorder."""

from __future__ import annotations

from typing import Any

from app.foundation.llm.chat import ChatClient
from app.foundation.llm.usage import Usage, extract_usage_from_response


class _UsageObj:
    def __init__(
        self,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        total_tokens: int | None,
    ) -> None:
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens


class _Resp:
    def __init__(self, content: str, usage: object | None) -> None:
        self.usage = usage

        class _Msg:
            def __init__(self, text: str) -> None:
                self.content = text

        class _Choice:
            def __init__(self, text: str) -> None:
                self.message = _Msg(text)

        self.choices = [_Choice(content)]


class _RecordingOpenAI:
    def __init__(self, response: _Resp) -> None:
        self._response = response

        class _Completions:
            def __init__(self, outer: _RecordingOpenAI) -> None:
                self._outer = outer

            def create(self, **kwargs: object) -> object:
                return self._outer._response

        class _Chat:
            def __init__(self, outer: _RecordingOpenAI) -> None:
                self.completions = _Completions(outer)

        self.chat = _Chat(self)


class _Recorder:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.fail = False

    def record(self, **kwargs: Any) -> None:
        if self.fail:
            raise RuntimeError("store down")
        self.calls.append(kwargs)


def test_extract_usage_from_openai_shape() -> None:
    resp = _Resp(
        '{"answer":"ok"}',
        _UsageObj(prompt_tokens=100, completion_tokens=40, total_tokens=140),
    )
    usage = extract_usage_from_response(resp)
    assert usage == Usage(
        input_tokens=100, output_tokens=40, total_tokens=140, reported=True
    )


def test_extract_usage_missing_is_unreported() -> None:
    resp = _Resp('{"answer":"ok"}', None)
    usage = extract_usage_from_response(resp)
    assert usage.reported is False
    assert usage.total_tokens == 0


def test_complete_json_records_usage() -> None:
    client = _RecordingOpenAI(
        _Resp(
            '{"answer":"ok"}',
            _UsageObj(10, 5, 15),
        )
    )
    recorder = _Recorder()
    chat = ChatClient(client, model="gpt-4o-mini", recorder=recorder)  # type: ignore[arg-type]
    out = chat.complete_json(system="s", user="u", role="chat")
    assert out["answer"] == "ok"
    assert chat.last_usage.reported is True
    assert chat.last_usage.total_tokens == 15
    assert len(recorder.calls) == 1
    assert recorder.calls[0]["purpose"] == "answer"
    assert recorder.calls[0]["model"] == "gpt-4o-mini"


def test_recorder_failure_does_not_hide_answer() -> None:
    client = _RecordingOpenAI(
        _Resp(
            '{"answer":"ok"}',
            _UsageObj(1, 1, 2),
        )
    )
    recorder = _Recorder()
    recorder.fail = True
    chat = ChatClient(client, model="gpt-4o-mini", recorder=recorder)  # type: ignore[arg-type]
    out = chat.complete_json(system="s", user="u", role="composer")
    assert out["answer"] == "ok"
    assert chat.last_usage.reported is True
