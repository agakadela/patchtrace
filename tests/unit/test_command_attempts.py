from datetime import UTC, datetime
from pathlib import Path

import pytest

from patchtrace.analysis.analyzer import analyze_run
from patchtrace.analysis.test_evidence import collect_command_evidence
from patchtrace.models.report import ClaimSupport
from patchtrace.models.run import RunManifest


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("3 passed, 0 failed", "passed"),
        ("3 passed, 1 failed", "failed"),
        ("0 passed, 1 failed", "failed"),
        ("0 passed, 0 failed", "unknown"),
        ("Found 0 errors\nSuccess: no issues found", "passed"),
        ("Found 1 error", "failed"),
        ("3 passed, 0 failed, 1 error", "failed"),
        ("FAILED tests/test_example.py::test_example", "failed"),
        ("3 passed\nKeyboardInterrupt", "unknown"),
    ],
)
def test_command_result_semantics(output: str, expected: str) -> None:
    attempts = collect_command_evidence(
        f"$ pytest\n{output}\nFinal answer:\nTests passed: `pytest`.\n",
        artifact_path="agent-session.txt",
    )
    assert len(attempts) == 1
    assert attempts[0].result == expected


@pytest.mark.parametrize(
    ("first", "last", "support"),
    [
        ("3 passed", "1 failed", ClaimSupport.CONTRADICTED),
        ("1 failed", "3 passed", ClaimSupport.SUPPORTED),
        ("3 passed", "", ClaimSupport.PARTIALLY_SUPPORTED),
        ("3 passed", "Interrupted", ClaimSupport.PARTIALLY_SUPPORTED),
        ("3 passed", "3 passed", ClaimSupport.SUPPORTED),
    ],
)
def test_latest_attempt_assesses_claim_and_preserves_history(
    tmp_path: Path, first: str, last: str, support: ClaimSupport
) -> None:
    transcript = (
        f"$ pytest\n{first}\n$ pytest\n{last}\n"
        "Final answer:\nTests passed: `pytest`.\n$ pytest\n99 passed\n"
    )
    attempts = collect_command_evidence(transcript, artifact_path="agent-session.txt")
    assert len(attempts) == 2
    assert [a.command_reference.locator for a in attempts] == [
        "normalized transcript line 1",
        "normalized transcript line 3",
    ]
    assert attempts[0].result == ("passed" if first == "3 passed" else "failed")
    (tmp_path / "agent-session.txt").write_text(transcript)
    result = analyze_run(_manifest(), run_dir=tmp_path)
    assessment = result.claim_assessments[0]
    assert assessment.support is support
    assert assessment.evidence_references[0].locator == "normalized transcript line 3"
    if support is ClaimSupport.PARTIALLY_SUPPORTED:
        assert assessment.evidence_gap and "latest" in assessment.evidence_gap
    assert any("freshness" in gap for gap in result.evidence_gaps)


@pytest.mark.parametrize("claim", ["Tests failed: `pytest`.", "Checks: `pytest`."])
def test_truthful_failed_verification_still_requires_failure_action(
    tmp_path: Path, claim: str
) -> None:
    (tmp_path / "agent-session.txt").write_text(
        f"$ pytest\n1 failed\nFinal answer:\n{claim}\n"
    )
    result = analyze_run(_manifest(), run_dir=tmp_path)
    assert result.claim_assessments[0].support is ClaimSupport.SUPPORTED
    assert "verification" in result.verdict and "failed" in result.verdict
    assert "pytest" in result.next_action and "failure" in result.next_action


def test_different_command_does_not_supply_missing_result(tmp_path: Path) -> None:
    transcript = (
        "$ pytest\n$ echo result\n3 passed\n"
        "$ pytest tests/unit\n4 passed\n"
        "Final answer:\nTests passed: `pytest`.\n"
    )
    (tmp_path / "agent-session.txt").write_text(transcript)
    result = analyze_run(_manifest(), run_dir=tmp_path)
    assert result.claim_assessments[0].support is ClaimSupport.PARTIALLY_SUPPORTED


def _manifest() -> RunManifest:
    return RunManifest(
        run_id="command-attempts",
        command=["codex"],
        trigger_source="manual_cli",
        started_at=datetime(2026, 9, 8, tzinfo=UTC),
        ended_at=datetime(2026, 9, 8, tzinfo=UTC),
        artifact_paths=["agent-session.txt"],
        wrapped_command_exit_status=0,
        process_outcome="completed",
        analysis_outcome="not_run",
        package_outcome="partial",
    )
