"""Live harness: golden set → POST /answer/agentic → score → report.

Run from ``backend/`` (spends OpenAI tokens; not part of ordinary pytest):

    python -m eval.run_eval --base-url http://localhost:8000
    python -m eval.run_eval --limit 1
    python -m eval.run_eval --case cobranzas-handoff-tenela --auto-approve
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from eval.scoring import score_case

EVAL_DIR = Path(__file__).resolve().parent
DEFAULT_GOLDEN = EVAL_DIR / "golden_set.json"
DEFAULT_REPORTS = EVAL_DIR / "reports"


def load_golden(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise SystemExit(f"Golden set empty or invalid: {path}")
    ids = [str(c.get("id") or "") for c in data]
    if len(ids) != len(set(ids)) or any(not i for i in ids):
        raise SystemExit("Golden set requires unique non-empty id per case")
    for case in data:
        if not str(case.get("question") or "").strip():
            raise SystemExit(f"Case {case.get('id')!r} missing question")
    return data


def select_cases(
    cases: list[dict[str, Any]],
    *,
    case_id: str | None,
    limit: int | None,
) -> list[dict[str, Any]]:
    selected = cases
    if case_id:
        selected = [c for c in cases if c["id"] == case_id]
        if not selected:
            raise SystemExit(f"Unknown case id: {case_id}")
    if limit is not None:
        selected = selected[: max(0, limit)]
    if not selected:
        raise SystemExit("No cases selected")
    return selected


def _api_prefix(base_url: str) -> str:
    return base_url.rstrip("/") + "/api/v1"


def post_agentic(
    client: httpx.Client,
    base: str,
    case: dict[str, Any],
) -> dict[str, Any]:
    body: dict[str, Any] = {"question": case["question"]}
    domain = case.get("domain")
    if domain:
        body["domain"] = domain
    res = client.post(f"{base}/answer/agentic", json=body)
    if res.status_code not in (200, 202):
        raise RuntimeError(
            f"agentic HTTP {res.status_code}: {res.text[:500]}"
        )
    return res.json()


def resume_approve(
    client: httpx.Client,
    base: str,
    thread_id: str,
) -> dict[str, Any]:
    res = client.post(
        f"{base}/answer/agentic/{thread_id}/resume",
        json={"decision": "approve"},
    )
    if res.status_code not in (200, 202):
        raise RuntimeError(
            f"resume HTTP {res.status_code}: {res.text[:500]}"
        )
    return res.json()


def run_case(
    client: httpx.Client,
    base: str,
    case: dict[str, Any],
    *,
    auto_approve: bool,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    initial = post_agentic(client, base, case)
    pause_status = str(initial.get("status") or "")
    payload = initial
    resumed = False
    if (
        auto_approve
        and pause_status == "awaiting_human_review"
        and initial.get("thread_id")
    ):
        payload = resume_approve(client, base, str(initial["thread_id"]))
        resumed = True
    scored = score_case(case, payload, pause_status=pause_status)
    scored["latency_s"] = round(time.perf_counter() - t0, 3)
    scored["resumed"] = resumed
    scored["question"] = case["question"]
    return scored


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Metropol agentic eval harness")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="API origin (default http://localhost:8000)",
    )
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--case", default=None, help="Run a single case id")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Resume approve when status is awaiting_human_review",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=180.0,
        help="HTTP timeout seconds per request",
    )
    args = parser.parse_args(argv)

    cases = select_cases(
        load_golden(args.golden),
        case_id=args.case,
        limit=args.limit,
    )
    base = _api_prefix(args.base_url)
    results: list[dict[str, Any]] = []

    with httpx.Client(timeout=args.timeout) as client:
        for case in cases:
            cid = case["id"]
            print(f"→ {cid} …", flush=True)
            try:
                row = run_case(
                    client,
                    base,
                    case,
                    auto_approve=args.auto_approve,
                )
            except Exception as exc:  # noqa: BLE001
                row = {
                    "case_id": cid,
                    "passed": False,
                    "reasons": [f"harness error: {exc}"],
                    "question": case["question"],
                }
            results.append(row)
            mark = "PASS" if row["passed"] else "FAIL"
            print(f"  {mark} {cid}: {row.get('reasons') or 'ok'}", flush=True)

    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "auto_approve": args.auto_approve,
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "results": results,
    }
    DEFAULT_REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = DEFAULT_REPORTS / f"report-{stamp}.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\n{passed}/{len(results)} passed — report {out}", flush=True)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
