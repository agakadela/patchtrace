from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from patchtrace.models.run import GitEvidenceManifest, RunManifest, RunOutcome
from patchtrace.reports.feedback import (
    build_agent_feedback_report,
    render_agent_feedback_markdown,
)


def test_agent_feedback_references_local_evidence_and_followups(
    tmp_path: Path,
) -> None:
    (tmp_path / "agent-session.txt").write_text(
        "agent note\nuv run pytest tests/unit/test_agent_feedback_report.py\ndone\n",
        encoding="utf-8",
    )
    (tmp_path / "changed-files.txt").write_text(
        "src/patchtrace/reports/feedback.py\n",
        encoding="utf-8",
    )
    (tmp_path / "patch.diff").write_text(
        "diff --git a/src/patchtrace/reports/feedback.py "
        "b/src/patchtrace/reports/feedback.py\n",
        encoding="utf-8",
    )
    manifest = _manifest(
        artifact_paths=[
            "run.json",
            "agent-session.txt",
            "git-before.txt",
            "git-after.txt",
            "changed-files.txt",
            "patch.diff",
            "SUMMARY.md",
            "AGENT_FEEDBACK.md",
        ],
        exit_status=7,
        patch_material_present=True,
    )

    report = build_agent_feedback_report(manifest, run_dir=tmp_path)
    markdown = render_agent_feedback_markdown(report)

    assert "# PatchTrace Agent Feedback" in markdown
    assert "Paste this back to the agent:" in markdown
    assert "- Exit status: `7`" in markdown
    assert "- Outcome: `wrapped_command_failed`" in markdown
    assert "- `src/patchtrace/reports/feedback.py`" in markdown
    assert "- Diff material: `present`" in markdown
    assert "- `uv run pytest tests/unit/test_agent_feedback_report.py`" in markdown
    assert "Wrapped command exited with status 7." in markdown
    assert "Address the wrapped command failure and rerun it." in markdown
    assert "- `AGENT_FEEDBACK.md`" in markdown
    assert "patch succeeded" not in markdown.lower()
    assert "patch is correct" not in markdown.lower()
    assert "patch is safe" not in markdown.lower()
    assert "production verified" not in markdown.lower()


def test_agent_feedback_asks_for_missing_test_and_patch_evidence(
    tmp_path: Path,
) -> None:
    (tmp_path / "agent-session.txt").write_text(
        "fake agent says hello\n",
        encoding="utf-8",
    )
    (tmp_path / "changed-files.txt").write_text("", encoding="utf-8")
    (tmp_path / "patch.diff").write_text("", encoding="utf-8")
    manifest = _manifest(
        artifact_paths=[
            "run.json",
            "agent-session.txt",
            "git-before.txt",
            "git-after.txt",
            "changed-files.txt",
            "patch.diff",
            "SUMMARY.md",
            "AGENT_FEEDBACK.md",
        ],
        exit_status=0,
        patch_material_present=False,
    )

    report = build_agent_feedback_report(manifest, run_dir=tmp_path)
    markdown = render_agent_feedback_markdown(report)

    assert "- None captured." in markdown
    assert "- Diff material: `empty`" in markdown
    assert "No obvious command or test signals were detected." in markdown
    assert "Run the relevant tests and paste the exact command output." in markdown
    assert (
        "Explain why no file changes were expected, or make the intended change."
        in markdown
    )
    assert (
        "Explain why no diff material was expected, or rerun after producing the patch."
        in markdown
    )
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
