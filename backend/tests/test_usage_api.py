"""GET /api/v1/usage/summary."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.dependencies import get_usage_store
from app.foundation.llm.usage import Usage
from app.foundation.persistence.usage import UsageByModel, UsageStore, UsageTotals
from app.main import create_app


class FakeUsageStore(UsageStore):
    def __init__(self) -> None:
        super().__init__(session_factory=None)
        self.rows: list[dict] = []

    def record(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self.rows.append(kwargs)

    def summarize(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        session_id: str | None = None,
        purpose: str | None = None,
    ) -> UsageTotals:
        rows = list(self.rows)
        if session_id is not None:
            rows = [r for r in rows if r.get("session_id") == session_id]
        if purpose is not None:
            rows = [r for r in rows if r.get("purpose") == purpose]
        if not rows:
            return UsageTotals(
                total_calls=0,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                by_model=[],
            )
        by_model: dict[str, UsageByModel] = {}
        for row in rows:
            usage: Usage = row["usage"]
            model = str(row["model"])
            prev = by_model.get(model)
            if prev is None:
                by_model[model] = UsageByModel(
                    model=model,
                    calls=1,
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    total_tokens=usage.total_tokens,
                )
            else:
                by_model[model] = UsageByModel(
                    model=model,
                    calls=prev.calls + 1,
                    input_tokens=prev.input_tokens + usage.input_tokens,
                    output_tokens=prev.output_tokens + usage.output_tokens,
                    total_tokens=prev.total_tokens + usage.total_tokens,
                )
        models = sorted(by_model.values(), key=lambda m: m.model)
        return UsageTotals(
            total_calls=sum(m.calls for m in models),
            input_tokens=sum(m.input_tokens for m in models),
            output_tokens=sum(m.output_tokens for m in models),
            total_tokens=sum(m.total_tokens for m in models),
            by_model=models,
        )


def test_usage_summary_empty_and_seeded() -> None:
    store = FakeUsageStore()
    app = create_app()
    app.dependency_overrides[get_usage_store] = lambda: store
    client = TestClient(app)

    empty = client.get("/api/v1/usage/summary")
    assert empty.status_code == 200
    body = empty.json()
    assert body["total_calls"] == 0
    assert body["by_model"] == []

    store.record(
        purpose="answer",
        model="gpt-4o-mini",
        usage=Usage(100, 40, 140, True),
        session_id=None,
        thread_id=None,
        owner_id=None,
    )
    store.record(
        purpose="answer",
        model="gpt-4o-mini",
        usage=Usage(100, 40, 140, True),
        session_id=None,
        thread_id=None,
        owner_id=None,
    )
    filled = client.get("/api/v1/usage/summary")
    assert filled.status_code == 200
    data = filled.json()
    assert data["total_calls"] == 2
    assert data["input_tokens"] == 200
    assert data["output_tokens"] == 80
    assert data["total_tokens"] == 280
    assert len(data["by_model"]) == 1
    assert data["by_model"][0]["model"] == "gpt-4o-mini"
    app.dependency_overrides.clear()


def test_usage_summary_inverted_range_422() -> None:
    store = FakeUsageStore()
    app = create_app()
    app.dependency_overrides[get_usage_store] = lambda: store
    client = TestClient(app)
    later = datetime(2026, 10, 14, tzinfo=timezone.utc).isoformat()
    earlier = datetime(2026, 10, 1, tzinfo=timezone.utc).isoformat()
    resp = client.get(f"/api/v1/usage/summary?from={later}&to={earlier}")
    assert resp.status_code == 422
    app.dependency_overrides.clear()
