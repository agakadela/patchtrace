from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from patchtrace.analysis.analyzer import analyze_run
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

    analysis_result = analyze_run(manifest, run_dir=tmp_path)
    report = build_agent_feedback_report(
        manifest,
        analysis_result=analysis_result,
    )
    markdown = render_agent_feedback_markdown(report)

    assert "# PatchTrace Agent Feedback" in markdown
    assert "Paste this back to the agent:" in markdown
    assert "- Exit status: `7`" in markdown
    assert "- Outcome: `wrapped_command_failed`" in markdown
    assert "- `src/patchtrace/reports/feedback.py`" in markdown
    assert "- Diff material: `present`" in markdown
    assert "- `uv run pytest tests/unit/test_agent_feedback_report.py`" in markdown
    assert "Wrapped command exited with status 7." in markdown
    assert "Address the wrapped command failure, rerun it" in markdown
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

    analysis_result = analyze_run(manifest, run_dir=tmp_path)
    report = build_agent_feedback_report(
        manifest,
        analysis_result=analysis_result,
    )
    markdown = render_agent_feedback_markdown(report)

    assert "- None captured." in markdown
    assert "- Diff material: `empty`" in markdown
    assert "No obvious command or test signals were detected." in markdown
    assert "Confirm that no change was intended" in markdown
    assert "success" not in markdown.lower()


def test_agent_feedback_uses_shared_analysis_and_cites_unresolved_claim(
    tmp_path: Path,
) -> None:
    (tmp_path / "agent-session.txt").write_text(
        "\u2022 Final answer:\nImplemented `src/patchtrace/reports/missing.py`.\n",
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
            "changed-files.txt",
            "patch.diff",
            "SUMMARY.md",
            "AGENT_FEEDBACK.md",
            "VERIFICATION_BRIEF.md",
        ],
        exit_status=0,
        patch_material_present=True,
    )
    analysis_result = analyze_run(manifest, run_dir=tmp_path)
    (tmp_path / "agent-session.txt").unlink()
    (tmp_path / "changed-files.txt").unlink()
    (tmp_path / "patch.diff").unlink()

    report = build_agent_feedback_report(
        manifest,
        analysis_result=analysis_result,
    )
    markdown = render_agent_feedback_markdown(report)

    assert report.verdict == analysis_result.verdict
    assert report.most_important_gap == analysis_result.most_important_gap
    assert report.next_action == analysis_result.next_action
    assert "Implemented `src/patchtrace/reports/missing.py`." in markdown
    assert (
        "Confirm whether `src/patchtrace/reports/missing.py` changed and provide "
        "the matching diff."
    ) in markdown
    assert "Transcript: `present`" in markdown
    assert "Diff material: `present`" in markdown


def test_agent_feedback_requests_no_work_for_supported_claims(
    tmp_path: Path,
) -> None:
    (tmp_path / "agent-session.txt").write_text(
        "• Final answer:\nImplemented `src/patchtrace/reports/feedback.py`.\n",
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
            "changed-files.txt",
            "patch.diff",
            "SUMMARY.md",
            "AGENT_FEEDBACK.md",
            "VERIFICATION_BRIEF.md",
        ],
        exit_status=0,
        patch_material_present=True,
    )
    analysis_result = analyze_run(manifest, run_dir=tmp_path)

    report = build_agent_feedback_report(
        manifest,
        analysis_result=analysis_result,
    )
    markdown = render_agent_feedback_markdown(report)

    assert report.requested_followups == []
    assert (
        "Follow-up work requested:\n"
        "- None beyond the recommended next action above." in markdown
    )


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
