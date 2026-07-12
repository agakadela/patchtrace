from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from patchtrace.analysis.analyzer import analyze_run
from patchtrace.models.run import GitEvidenceManifest, RunManifest, RunOutcome
from patchtrace.reports.verification_brief import (
    build_verification_brief_report,
    render_verification_brief_markdown,
)


def test_verification_brief_includes_bounded_evidence_and_review_targets(
    tmp_path: Path,
) -> None:
    (tmp_path / "agent-session.txt").write_text(
        "• Ran uv run pytest tests/unit/test_verification_brief_report.py\n"
        "2 passed in 0.04s\n"
        "• Final answer:\n"
        "Implemented `src/patchtrace/reports/verification_brief.py`.\n"
        "Implemented clearer verification detail.\n"
        "Tests: `uv run pytest tests/unit/test_verification_brief_report.py`\n",
        encoding="utf-8",
    )
    (tmp_path / "changed-files.txt").write_text(
        "src/patchtrace/reports/verification_brief.py\n"
        "tests/unit/test_verification_brief_report.py\n",
        encoding="utf-8",
    )
    (tmp_path / "patch.diff").write_text(
        "diff --git a/src/patchtrace/reports/verification_brief.py "
        "b/src/patchtrace/reports/verification_brief.py\n",
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
            "VERIFICATION_BRIEF.md",
        ],
        exit_status=0,
        patch_material_present=True,
    )

    analysis_result = analyze_run(manifest, run_dir=tmp_path)
    report = build_verification_brief_report(
        manifest,
        analysis_result=analysis_result,
        run_dir=tmp_path,
    )
    markdown = render_verification_brief_markdown(report)

    assert "# PatchTrace Verification Brief" in markdown
    assert "- Run ID: `run-123`" in markdown
    assert "- Command: `python tests/fixtures/fake_agent.py`" in markdown
    assert "- Trigger source: `manual_cli`" in markdown
    assert "- Exit status: `0`" in markdown
    assert "- Transcript: `present`" in markdown
    assert "- Diff material: `present`" in markdown
    assert "- `SUMMARY.md`" in markdown
    assert "- `AGENT_FEEDBACK.md`" in markdown
    assert "- `VERIFICATION_BRIEF.md`" in markdown
    assert "- `src/patchtrace/reports/verification_brief.py`" in markdown
    assert "- `tests/unit/test_verification_brief_report.py`" in markdown
    assert "- `uv run pytest tests/unit/test_verification_brief_report.py`" in markdown
    assert "## Review First" in markdown
    assert "Review `src/patchtrace/reports/verification_brief.py` first." in markdown
    assert "## Claim Assessments" in markdown
    assert "### Claim 1: File change" in markdown
    assert (
        "- Claim: Implemented `src/patchtrace/reports/verification_brief.py`."
        in markdown
    )
    assert "- Relationship: **Evidence supports this claim**" in markdown
    assert "`changed-files.txt` (`line 1`)" in markdown
    assert "### Claim 2: Completed change" in markdown
    assert "- Relationship: **Cannot assess from available material**" in markdown
    assert (
        "- Next action: Name the changed file or diff location that demonstrates "
        "this change." in markdown
    )
    assert "### Claim 3: Test" in markdown
    assert (
        "- Claim: Tests: `uv run pytest "
        "tests/unit/test_verification_brief_report.py`" in markdown
    )
    assert "`agent-session.txt` (`normalized transcript line 1`)" in markdown
    assert "`agent-session.txt` (`normalized transcript line 2`)" in markdown
    assert "- Relationship: **Evidence supports this claim**" in markdown
    assert (
        "Claim relationships describe captured evidence only; they do not prove "
        "correctness, safety, acceptance, or production readiness." in markdown
    )
    assert "patch is correct" not in markdown.lower()
    assert "patch is safe" not in markdown.lower()
    assert "production verified" not in markdown.lower()


def test_verification_brief_labels_missing_and_failed_evidence_conservatively(
    tmp_path: Path,
) -> None:
    (tmp_path / "changed-files.txt").write_text("", encoding="utf-8")
    (tmp_path / "patch.diff").write_text("", encoding="utf-8")
    manifest = _manifest(
        artifact_paths=[
            "run.json",
            "git-before.txt",
            "git-after.txt",
            "changed-files.txt",
            "patch.diff",
            "SUMMARY.md",
            "AGENT_FEEDBACK.md",
            "VERIFICATION_BRIEF.md",
        ],
        exit_status=7,
        patch_material_present=False,
    )

    analysis_result = analyze_run(manifest, run_dir=tmp_path)
    report = build_verification_brief_report(
        manifest,
        analysis_result=analysis_result,
        run_dir=tmp_path,
    )
    markdown = render_verification_brief_markdown(report)

    assert "- Transcript: `missing`" in markdown
    assert "- Diff material: `empty`" in markdown
    assert "- Command/test signals: `missing`" in markdown
    assert "- Wrapped command: `non-zero exit 7`" in markdown
    assert "Transcript artifact is missing for this run." in markdown
    assert "No obvious command or test signals were detected." in markdown
    assert "No git patch material was captured for this run." in markdown
    assert "Wrapped command exited with status 7." in markdown
    assert (
        "No changed files were captured; inspect git evidence artifacts first."
        in markdown
    )
    assert "No bounded explicit final claims were extracted." in markdown
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
