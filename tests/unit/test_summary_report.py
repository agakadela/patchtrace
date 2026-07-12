from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from patchtrace.analysis.analyzer import analyze_run
from patchtrace.models.run import GitEvidenceManifest, RunManifest, RunOutcome
from patchtrace.reports.summary import build_summary_report, render_summary_markdown


def test_summary_leads_with_shared_analysis_decision_before_run_metadata(
    tmp_path: Path,
) -> None:
    _write_run_material(
        tmp_path,
        transcript="\n".join(
            (
                "• Final answer:",
                "Updated `src/patchtrace/reports/summary.py`.",
                "Tests passed: `uv run pytest tests/unit/test_summary_report.py`.",
            )
        ),
        changed_files="src/patchtrace/reports/summary.py\n",
        patch=(
            "diff --git a/src/patchtrace/reports/summary.py "
            "b/src/patchtrace/reports/summary.py\n"
        ),
    )
    manifest = _manifest()
    analysis_result = analyze_run(manifest, run_dir=tmp_path)

    report = build_summary_report(manifest, analysis_result=analysis_result)
    markdown = render_summary_markdown(report)

    assert markdown.index("## Quick Decision") < markdown.index("## Run")
    assert "- Verdict: Review required:" in markdown
    assert "- Most important gap:" in markdown
    assert "- Recommended next action:" in markdown
    assert "No captured command matches" in markdown
    assert "Run `uv run pytest tests/unit/test_summary_report.py`" in markdown
    assert "- Run ID: `run-123`" in markdown
    assert "- Command: `codex`" in markdown
    assert "the patch is correct" not in markdown.lower()
    assert "the patch is safe" not in markdown.lower()
    assert "the work is accepted" not in markdown.lower()


def test_summary_decision_is_useful_when_no_changes_were_captured(
    tmp_path: Path,
) -> None:
    _write_run_material(
        tmp_path,
        transcript="• Final answer:\nDone.\n",
        changed_files="",
        patch="",
    )
    manifest = _manifest(patch_material_present=False)
    analysis_result = analyze_run(manifest, run_dir=tmp_path)

    report = build_summary_report(manifest, analysis_result=analysis_result)

    assert report.verdict == "No captured file changes require review."
    assert report.most_important_gap == (
        "PatchTrace cannot determine whether the absence of changes was intended."
    )
    assert report.next_action == (
        "Confirm that no change was intended; otherwise capture the missing change."
    )


def test_summary_decision_is_useful_when_transcript_is_missing(tmp_path: Path) -> None:
    (tmp_path / "changed-files.txt").write_text(
        "src/patchtrace/reports/summary.py\n",
        encoding="utf-8",
    )
    (tmp_path / "patch.diff").write_text(
        "diff --git a/src/patchtrace/reports/summary.py "
        "b/src/patchtrace/reports/summary.py\n",
        encoding="utf-8",
    )
    manifest = _manifest()
    analysis_result = analyze_run(manifest, run_dir=tmp_path)

    report = build_summary_report(manifest, analysis_result=analysis_result)

    assert report.verdict == "Review blocked: agent claims could not be assessed."
    assert report.most_important_gap == "Transcript evidence is missing for this run."
    assert report.next_action == (
        "Capture the agent transcript and rerun PatchTrace before relying on its claims."
    )


def test_summary_decision_prioritizes_failed_wrapped_command(tmp_path: Path) -> None:
    _write_run_material(
        tmp_path,
        transcript="• Final answer:\nDone.\n",
        changed_files="",
        patch="",
    )
    manifest = _manifest(exit_status=7, patch_material_present=False)
    analysis_result = analyze_run(manifest, run_dir=tmp_path)

    report = build_summary_report(manifest, analysis_result=analysis_result)

    assert report.verdict == "Review required: the wrapped command failed."
    assert report.most_important_gap == "Wrapped command exited with status 7."
    assert report.next_action == (
        "Address the wrapped command failure, rerun it, and review the new evidence."
    )


def test_summary_decision_prioritizes_conflicting_evidence_in_mixed_claims(
    tmp_path: Path,
) -> None:
    _write_run_material(
        tmp_path,
        transcript="\n".join(
            (
                "• Ran uv run mypy src tests",
                "Found 1 error in 1 file (checked 20 source files)",
                "• Final answer:",
                "Updated `src/patchtrace/reports/summary.py`.",
                "Verification passed: `uv run mypy src tests`.",
            )
        ),
        changed_files="src/patchtrace/reports/summary.py\n",
        patch=(
            "diff --git a/src/patchtrace/reports/summary.py "
            "b/src/patchtrace/reports/summary.py\n"
        ),
    )
    manifest = _manifest()
    analysis_result = analyze_run(manifest, run_dir=tmp_path)

    report = build_summary_report(manifest, analysis_result=analysis_result)

    assert report.verdict == (
        "Review required: available evidence conflicts with an assessed claim."
    )
    assert report.most_important_gap == (
        "Captured output reports that the claimed verification command failed."
    )
    assert report.next_action == (
        "Address the captured failure, rerun the same command, and capture its output."
    )


def test_summary_does_not_turn_supported_evidence_into_acceptance(
    tmp_path: Path,
) -> None:
    _write_run_material(
        tmp_path,
        transcript=("• Final answer:\nUpdated `src/patchtrace/reports/summary.py`.\n"),
        changed_files="src/patchtrace/reports/summary.py\n",
        patch=(
            "diff --git a/src/patchtrace/reports/summary.py "
            "b/src/patchtrace/reports/summary.py\n"
        ),
    )
    manifest = _manifest()
    analysis_result = analyze_run(manifest, run_dir=tmp_path)

    report = build_summary_report(manifest, analysis_result=analysis_result)

    assert report.verdict == (
        "Available evidence supports the assessed claims; human review is still required."
    )
    assert report.most_important_gap == (
        "Evidence support does not establish correctness, safety, or acceptance."
    )
    assert report.next_action == (
        "Review the referenced changes before deciding whether to accept them."
    )


def _write_run_material(
    path: Path,
    *,
    transcript: str,
    changed_files: str,
    patch: str,
) -> None:
    (path / "agent-session.txt").write_text(transcript, encoding="utf-8")
    (path / "changed-files.txt").write_text(changed_files, encoding="utf-8")
    (path / "patch.diff").write_text(patch, encoding="utf-8")


def _manifest(
    *,
    exit_status: int = 0,
    patch_material_present: bool = True,
) -> RunManifest:
    outcome: RunOutcome = "completed" if exit_status == 0 else "wrapped_command_failed"
    return RunManifest(
        run_id="run-123",
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
        ],
        wrapped_command_exit_status=exit_status,
        outcome=outcome,
        git_evidence=GitEvidenceManifest(
            git_before_path="git-before.txt",
            git_after_path="git-after.txt",
            changed_files_path="changed-files.txt",
            patch_path="patch.diff",
            patch_material_present=patch_material_present,
        ),
    )
