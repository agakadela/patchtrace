from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict, cast

from patchtrace.analysis.analyzer import analyze_run
from patchtrace.models.report import ClaimSupport
from patchtrace.models.run import GitEvidenceManifest, RunManifest
from patchtrace.reports.feedback import build_agent_feedback_report
from patchtrace.reports.summary import build_summary_report
from patchtrace.reports.verification_brief import build_verification_brief_report

FIXTURE = Path(__file__).parents[1] / "fixtures" / "phase4_claim_matrix.json"
EXPECTED_SCENARIOS = {
    "supported",
    "partially_supported",
    "unsupported",
    "contradicted",
    "cannot_assess",
    "missing_material",
    "non_zero_exit",
}


class FixtureCase(TypedDict):
    name: str
    transcript: str | None
    changed_files: str | None
    patch: str | None
    patch_material_present: bool
    exit_status: int
    expected_supports: list[str]
    expected_claim_material_status: str
    expected_transcript_status: str
    expected_diff_material_status: str
    expected_verdict: str


def test_phase4_sanitized_fixture_matrix_drives_one_shared_analysis_result(
    tmp_path: Path,
) -> None:
    cases = cast(list[FixtureCase], json.loads(FIXTURE.read_text(encoding="utf-8")))

    assert {case["name"] for case in cases} == EXPECTED_SCENARIOS

    for case in cases:
        run_dir = tmp_path / case["name"]
        run_dir.mkdir()
        _write_if_present(run_dir / "agent-session.txt", case["transcript"])
        _write_if_present(run_dir / "changed-files.txt", case["changed_files"])
        _write_if_present(run_dir / "patch.diff", case["patch"])
        manifest = _manifest(case)

        analysis_result = analyze_run(manifest, run_dir=run_dir)
        summary = build_summary_report(
            manifest,
            analysis_result=analysis_result,
        )
        feedback = build_agent_feedback_report(
            manifest,
            analysis_result=analysis_result,
        )
        verification_brief = build_verification_brief_report(
            manifest,
            analysis_result=analysis_result,
        )

        assert [
            assessment.support for assessment in analysis_result.claim_assessments
        ] == [ClaimSupport(value) for value in case["expected_supports"]]
        assert (
            analysis_result.claim_material_status
            == case["expected_claim_material_status"]
        )
        assert analysis_result.transcript_status == case["expected_transcript_status"]
        assert (
            analysis_result.diff_material_status
            == case["expected_diff_material_status"]
        )
        assert analysis_result.verdict == case["expected_verdict"]
        assert summary.verdict == feedback.verdict == analysis_result.verdict
        assert summary.most_important_gap == feedback.most_important_gap
        assert summary.next_action == feedback.next_action
        assert verification_brief.claim_assessments == (
            analysis_result.claim_assessments
        )


def _manifest(case: FixtureCase) -> RunManifest:
    exit_status = case["exit_status"]
    git_evidence = None
    if case["changed_files"] is not None or case["patch"] is not None:
        git_evidence = GitEvidenceManifest(
            git_before_path="git-before.txt",
            git_after_path="git-after.txt",
            changed_files_path="changed-files.txt",
            patch_path="patch.diff",
            patch_material_present=case["patch_material_present"],
        )
    return RunManifest(
        run_id=f"fixture-{case['name']}",
        command=["codex"],
        trigger_source="manual_cli",
        started_at=datetime(2026, 7, 12, 12, 0, tzinfo=UTC),
        ended_at=datetime(2026, 7, 12, 12, 1, tzinfo=UTC),
        artifact_paths=[
            "run.json",
            "agent-session.txt",
            "changed-files.txt",
            "patch.diff",
            "SUMMARY.md",
            "AGENT_FEEDBACK.md",
            "VERIFICATION_BRIEF.md",
        ],
        wrapped_command_exit_status=exit_status,
        outcome="completed" if exit_status == 0 else "wrapped_command_failed",
        git_evidence=git_evidence,
    )


def _write_if_present(path: Path, content: str | None) -> None:
    if content is not None:
        path.write_text(content, encoding="utf-8")
