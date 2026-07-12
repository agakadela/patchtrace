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
