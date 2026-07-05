from __future__ import annotations

from datetime import UTC, datetime

from patchtrace.models.run import GitEvidenceManifest, RunManifest, RunOutcome
from patchtrace.reports.summary import build_summary_report, render_summary_markdown


def test_summary_report_includes_run_material_and_conservative_gaps() -> None:
    manifest = _manifest(
        artifact_paths=[
            "run.json",
            "agent-session.txt",
            "git-before.txt",
            "git-after.txt",
            "changed-files.txt",
            "patch.diff",
            "SUMMARY.md",
        ],
        exit_status=0,
        patch_material_present=False,
    )

    report = build_summary_report(manifest)
    markdown = render_summary_markdown(report)

    assert "# PatchTrace Summary" in markdown
    assert "- Run ID: `run-123`" in markdown
    assert "- Command: `python tests/fixtures/fake_agent.py`" in markdown
    assert "- Exit status: `0`" in markdown
    assert "- Outcome: `completed`" in markdown
    assert "- `SUMMARY.md`" in markdown
    assert "No git patch material was captured for this run." in markdown
    assert (
        "PatchTrace has not verified correctness, safety, or production readiness."
        in markdown
    )
    assert "No claim extraction or final verdict has run in this phase." in markdown
    assert "patch is correct" not in markdown
    assert "patch is safe" not in markdown
    assert "production verified" not in markdown


def test_summary_report_notes_nonzero_wrapped_command_exit() -> None:
    manifest = _manifest(
        artifact_paths=[
            "run.json",
            "agent-session.txt",
            "git-before.txt",
            "git-after.txt",
            "changed-files.txt",
            "patch.diff",
            "SUMMARY.md",
        ],
        exit_status=7,
        patch_material_present=True,
    )

    report = build_summary_report(manifest)
    markdown = render_summary_markdown(report)

    assert "- Exit status: `7`" in markdown
    assert "- Outcome: `wrapped_command_failed`" in markdown
    assert "Wrapped command exited with status 7." in markdown
    assert "No git patch material was captured for this run." not in markdown
    assert "success" not in markdown.lower()


def _manifest(
    *,
    artifact_paths: list[str],
    exit_status: int,
    patch_material_present: bool,
) -> RunManifest:
    outcome: RunOutcome = "completed" if exit_status == 0 else "wrapped_command_failed"
    return RunManifest(
        run_id="run-123",
        command=["python", "tests/fixtures/fake_agent.py"],
        trigger_source="manual_cli",
        started_at=datetime(2026, 7, 5, 12, 0, tzinfo=UTC),
        ended_at=datetime(2026, 7, 5, 12, 1, tzinfo=UTC),
        artifact_paths=artifact_paths,
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
