from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from patchtrace.analysis.analyzer import analyze_run
from patchtrace.models.report import ClaimCategory, ClaimSupport
from patchtrace.models.run import GitEvidenceManifest, RunManifest


def test_analyze_run_assesses_explicit_file_and_completed_change_claims(
    tmp_path: Path,
) -> None:
    (tmp_path / "agent-session.txt").write_text(
        "\n".join(
            (
                "• Final answer:",
                "Implemented `src/patchtrace/analysis/analyzer.py`.",
                "Completed deterministic claim assessment.",
                "Done.",
                "Fixed.",
                "Everything works.",
            )
        ),
        encoding="utf-8",
    )
    (tmp_path / "changed-files.txt").write_text(
        "src/patchtrace/analysis/analyzer.py\n",
        encoding="utf-8",
    )
    (tmp_path / "patch.diff").write_text(
        "diff --git a/src/patchtrace/analysis/analyzer.py "
        "b/src/patchtrace/analysis/analyzer.py\n",
        encoding="utf-8",
    )

    result = analyze_run(_manifest(), run_dir=tmp_path)

    assert result.run_id == "run-123"
    assert result.claim_material_status == "identified"
    assert len(result.claim_assessments) == 2

    file_assessment = result.claim_assessments[0]
    assert file_assessment.claim == (
        "Implemented `src/patchtrace/analysis/analyzer.py`."
    )
    assert file_assessment.category is ClaimCategory.FILE_CHANGE
    assert file_assessment.support is ClaimSupport.SUPPORTED
    assert file_assessment.relationship == "Evidence supports this claim"
    assert file_assessment.claim_source.artifact_path == "agent-session.txt"
    assert file_assessment.claim_source.locator == "final response line 1"
    assert file_assessment.evidence_references[0].artifact_path == "changed-files.txt"
    assert file_assessment.evidence_references[0].locator == "line 1"
    assert file_assessment.evidence_gap is None
    assert file_assessment.next_action is None

    completion_assessment = result.claim_assessments[1]
    assert completion_assessment.claim == "Completed deterministic claim assessment."
    assert completion_assessment.category is ClaimCategory.COMPLETED_CHANGE
    assert completion_assessment.support is ClaimSupport.CANNOT_DETERMINE
    assert completion_assessment.relationship == (
        "Cannot assess from available material"
    )
    assert completion_assessment.evidence_references == []
    assert completion_assessment.evidence_gap == (
        "The claim does not identify a file or other exact local evidence target."
    )
    assert completion_assessment.next_action == (
        "Name the changed file or diff location that demonstrates this change."
    )
    extracted_claims = {assessment.claim for assessment in result.claim_assessments}
    assert extracted_claims.isdisjoint({"Done.", "Fixed.", "Everything works."})


def test_analyze_run_marks_conflicting_no_change_claim(
    tmp_path: Path,
) -> None:
    (tmp_path / "agent-session.txt").write_text(
        "• Final answer:\nNo files changed.\n",
        encoding="utf-8",
    )
    (tmp_path / "changed-files.txt").write_text(
        "src/patchtrace/analysis/analyzer.py\n",
        encoding="utf-8",
    )
    (tmp_path / "patch.diff").write_text(
        "diff --git a/src/patchtrace/analysis/analyzer.py "
        "b/src/patchtrace/analysis/analyzer.py\n",
        encoding="utf-8",
    )

    result = analyze_run(_manifest(), run_dir=tmp_path)

    assessment = result.claim_assessments[0]
    assert assessment.support is ClaimSupport.CONTRADICTED
    assert assessment.relationship == "Available evidence conflicts with this claim"
    assert assessment.evidence_references[0].artifact_path == "changed-files.txt"
    assert assessment.evidence_gap == (
        "Captured git evidence lists files changed during the run."
    )
    assert assessment.next_action == (
        "Reconcile the final claim with the captured changed-file evidence."
    )


def test_analyze_run_marks_unmatched_file_claim_unsupported(
    tmp_path: Path,
) -> None:
    (tmp_path / "agent-session.txt").write_text(
        "• Final answer:\nUpdated `src/patchtrace/missing.py`.\n",
        encoding="utf-8",
    )
    (tmp_path / "changed-files.txt").write_text(
        "src/patchtrace/analysis/analyzer.py\n",
        encoding="utf-8",
    )
    (tmp_path / "patch.diff").write_text(
        "diff --git a/src/patchtrace/analysis/analyzer.py "
        "b/src/patchtrace/analysis/analyzer.py\n",
        encoding="utf-8",
    )

    result = analyze_run(_manifest(), run_dir=tmp_path)

    assessment = result.claim_assessments[0]
    assert assessment.support is ClaimSupport.UNSUPPORTED
    assert assessment.relationship == "No supporting evidence found"
    assert [
        reference.artifact_path for reference in assessment.evidence_references
    ] == ["changed-files.txt", "patch.diff"]
    assert assessment.evidence_gap == (
        "No captured changed-file or diff reference matches "
        "`src/patchtrace/missing.py`."
    )
    assert assessment.next_action == (
        "Confirm whether `src/patchtrace/missing.py` changed and provide the "
        "matching diff."
    )


def test_analyze_run_does_not_infer_claims_from_ambiguous_output(
    tmp_path: Path,
) -> None:
    (tmp_path / "agent-session.txt").write_text(
        "Implemented `src/patchtrace/analysis/analyzer.py`.\n",
        encoding="utf-8",
    )
    (tmp_path / "changed-files.txt").write_text(
        "src/patchtrace/analysis/analyzer.py\n",
        encoding="utf-8",
    )
    (tmp_path / "patch.diff").write_text("", encoding="utf-8")

    result = analyze_run(_manifest(), run_dir=tmp_path)

    assert result.claim_material_status == "ambiguous"
    assert result.claim_assessments == []


def test_analyze_run_assesses_test_and_verification_command_results(
    tmp_path: Path,
) -> None:
    (tmp_path / "agent-session.txt").write_text(
        "\n".join(
            (
                "• Ran uv run pytest tests/unit/test_claim_analysis.py",
                "4 passed in 0.05s",
                "• Ran uv run mypy src tests",
                "Found 1 error in 1 file (checked 20 source files)",
                "• Ran uv run ruff check .",
                "• Ran uv run pytest tests/unit/test_unrelated.py",
                "1 passed in 0.01s",
                "• Final answer:",
                "Tests passed: `uv run pytest tests/unit/test_claim_analysis.py`.",
                "Verification passed: `uv run mypy src tests`.",
                "Checks: `uv run ruff check .`.",
                "Tests passed: `uv run pytest tests/unit/test_missing.py`.",
            )
        ),
        encoding="utf-8",
    )
    (tmp_path / "changed-files.txt").write_text("", encoding="utf-8")
    (tmp_path / "patch.diff").write_text("", encoding="utf-8")

    result = analyze_run(_manifest(), run_dir=tmp_path)

    assert len(result.claim_assessments) == 4

    passing_test = result.claim_assessments[0]
    assert passing_test.category is ClaimCategory.TEST
    assert passing_test.support is ClaimSupport.SUPPORTED
    assert [reference.locator for reference in passing_test.evidence_references] == [
        "normalized transcript line 1",
        "normalized transcript line 2",
    ]
    assert passing_test.evidence_gap is None
    assert passing_test.next_action is None

    failing_verification = result.claim_assessments[1]
    assert failing_verification.category is ClaimCategory.VERIFICATION_COMMAND
    assert failing_verification.support is ClaimSupport.CONTRADICTED
    assert failing_verification.relationship == (
        "Available evidence conflicts with this claim"
    )
    assert [
        reference.locator for reference in failing_verification.evidence_references
    ] == ["normalized transcript line 3", "normalized transcript line 4"]
    assert failing_verification.evidence_gap == (
        "Captured output reports that the claimed verification command failed."
    )
    assert failing_verification.next_action == (
        "Address the captured failure, rerun the same command, and capture its output."
    )

    command_only = result.claim_assessments[2]
    assert command_only.category is ClaimCategory.VERIFICATION_COMMAND
    assert command_only.support is ClaimSupport.PARTIALLY_SUPPORTED
    assert [reference.locator for reference in command_only.evidence_references] == [
        "normalized transcript line 5"
    ]
    assert command_only.evidence_gap == (
        "The command is captured, but no pass or fail result is available."
    )
    assert command_only.next_action == (
        "Capture the result output for `uv run ruff check .`."
    )

    missing_command = result.claim_assessments[3]
    assert missing_command.category is ClaimCategory.TEST
    assert missing_command.support is ClaimSupport.UNSUPPORTED
    assert missing_command.evidence_references == []
    assert missing_command.evidence_gap == (
        "No captured command matches `uv run pytest tests/unit/test_missing.py`."
    )
    assert missing_command.next_action == (
        "Run `uv run pytest tests/unit/test_missing.py` and capture its result output."
    )


def _manifest() -> RunManifest:
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
            "VERIFICATION_BRIEF.md",
        ],
        wrapped_command_exit_status=0,
        outcome="completed",
        git_evidence=GitEvidenceManifest(
            git_before_path="git-before.txt",
            git_after_path="git-after.txt",
            changed_files_path="changed-files.txt",
            patch_path="patch.diff",
            patch_material_present=True,
        ),
    )
