from datetime import UTC, datetime
from pathlib import Path

import pytest

from patchtrace.analysis.analyzer import analyze_run
from patchtrace.models.report import ClaimSupport
from patchtrace.models.run import GitEvidenceManifest, RunManifest

COMMENT_PATCH = (
    "diff --git a/auth.py b/auth.py\n"
    "index 1111111..2222222 100644\n"
    "--- a/auth.py\n+++ b/auth.py\n@@ -1 +1 @@\n"
    "-# old comment\n+# new comment\n"
)
DELETION_PATCH = (
    "diff --git a/auth.py b/auth.py\n"
    "deleted file mode 100644\n"
    "--- a/auth.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-# comment\n"
)


@pytest.mark.parametrize(
    ("claim", "patch", "expected"),
    [
        (
            "Fixed authentication in `auth.py`.",
            COMMENT_PATCH,
            ClaimSupport.CANNOT_DETERMINE,
        ),
        ("Implemented `auth.py`.", COMMENT_PATCH, ClaimSupport.CANNOT_DETERMINE),
        ("Deleted `auth.py`.", COMMENT_PATCH, ClaimSupport.CANNOT_DETERMINE),
        ("Modified `auth.py`.", DELETION_PATCH, ClaimSupport.CANNOT_DETERMINE),
        (
            "Changed `auth.py` and `other.py`.",
            COMMENT_PATCH,
            ClaimSupport.PARTIALLY_SUPPORTED,
        ),
        (
            "Changed `other.py` and `auth.py`.",
            COMMENT_PATCH,
            ClaimSupport.PARTIALLY_SUPPORTED,
        ),
        (
            "Fixed `auth.py` and `other.py`.",
            COMMENT_PATCH,
            ClaimSupport.CANNOT_DETERMINE,
        ),
        ("Modified `auth.py`.", COMMENT_PATCH, ClaimSupport.SUPPORTED),
        ("Deleted `auth.py`.", DELETION_PATCH, ClaimSupport.SUPPORTED),
        (
            "Changed `auth.py` to fix authentication.",
            COMMENT_PATCH,
            ClaimSupport.CANNOT_DETERMINE,
        ),
        (
            "Changed `auth.py` and other.py.",
            COMMENT_PATCH,
            ClaimSupport.CANNOT_DETERMINE,
        ),
        (
            "Completed deterministic claim assessment.",
            COMMENT_PATCH,
            ClaimSupport.CANNOT_DETERMINE,
        ),
    ],
)
def test_file_claim_does_not_exceed_captured_facts(
    tmp_path: Path, claim: str, patch: str, expected: ClaimSupport
) -> None:
    (tmp_path / "agent-session.txt").write_text(f"• Final answer:\n{claim}\n")
    (tmp_path / "changed-files.txt").write_text("auth.py\n")
    (tmp_path / "patch.diff").write_text(patch)

    assessment = analyze_run(_manifest(), run_dir=tmp_path).claim_assessments[0]

    assert assessment.support is expected
    if "`auth.py`" in claim:
        assert any(
            "auth.py" in ref.description for ref in assessment.evidence_references
        )
    if expected is not ClaimSupport.SUPPORTED:
        assert assessment.evidence_gap
        assert assessment.next_action
    if "other.py" in claim:
        assert assessment.evidence_gap and "other.py" in assessment.evidence_gap


@pytest.mark.parametrize("patch", ["", "diff --git a/auth.py b/auth.py\n"])
def test_path_alone_does_not_establish_modification_type(
    tmp_path: Path, patch: str
) -> None:
    (tmp_path / "agent-session.txt").write_text(
        "• Final answer:\nModified `auth.py`.\n"
    )
    (tmp_path / "changed-files.txt").write_text("auth.py\n")
    (tmp_path / "patch.diff").write_text(patch)

    assessment = analyze_run(_manifest(), run_dir=tmp_path).claim_assessments[0]

    assert assessment.support is ClaimSupport.CANNOT_DETERMINE


@pytest.mark.parametrize(
    ("claim", "changed_files", "patch", "expected"),
    [
        (
            "Changed ` auth.py`.",
            "auth.py\n",
            COMMENT_PATCH,
            ClaimSupport.UNSUPPORTED,
        ),
        (
            "Changed `auth.py`.",
            " auth.py\n",
            "",
            ClaimSupport.UNSUPPORTED,
        ),
        (
            "Updated `auth.py`.",
            "auth.py\n",
            DELETION_PATCH,
            ClaimSupport.CANNOT_DETERMINE,
        ),
        (
            "Changed `auth.py` and `LICENSE`.",
            "auth.py\n",
            COMMENT_PATCH,
            ClaimSupport.PARTIALLY_SUPPORTED,
        ),
        (
            "Changed `auth.py`, `other.py`, and `LICENSE`.",
            "auth.py\nother.py\nLICENSE\n",
            "",
            ClaimSupport.SUPPORTED,
        ),
        ("Changed `auth.py` and `auth.py`.", "auth.py\n", "", ClaimSupport.SUPPORTED),
        (
            "Modified `auth.py` and `other.py`.",
            "auth.py\nother.py\n",
            COMMENT_PATCH,
            ClaimSupport.PARTIALLY_SUPPORTED,
        ),
        ("Added `auth.py`.", "auth.py\n", COMMENT_PATCH, ClaimSupport.CANNOT_DETERMINE),
        (
            "Deleted `auth.py`.",
            "auth.py\n",
            DELETION_PATCH + COMMENT_PATCH,
            ClaimSupport.CANNOT_DETERMINE,
        ),
        (
            "Modified `auth.py`.",
            "auth.py\n",
            COMMENT_PATCH + DELETION_PATCH,
            ClaimSupport.CANNOT_DETERMINE,
        ),
        ("Changed `a/auth.py`.", "auth.py\n", COMMENT_PATCH, ClaimSupport.UNSUPPORTED),
        ("Changed `auth.py`.", "a/auth.py\n", "", ClaimSupport.UNSUPPORTED),
        ("Changed `./auth.py`.", "auth.py\n", "", ClaimSupport.SUPPORTED),
        (
            "Changed `auth.py` or `other.py`.",
            "auth.py\n",
            COMMENT_PATCH,
            ClaimSupport.CANNOT_DETERMINE,
        ),
    ],
)
def test_all_targets_and_operation_evidence_are_considered(
    tmp_path: Path, claim: str, changed_files: str, patch: str, expected: ClaimSupport
) -> None:
    (tmp_path / "agent-session.txt").write_text(f"• Final answer:\n{claim}\n")
    (tmp_path / "changed-files.txt").write_text(changed_files)
    (tmp_path / "patch.diff").write_text(patch)

    assessment = analyze_run(_manifest(), run_dir=tmp_path).claim_assessments[0]

    assert assessment.support is expected
    if expected is ClaimSupport.PARTIALLY_SUPPORTED:
        assert assessment.evidence_gap
        assert "auth.py" in assessment.evidence_gap
        assert "only" in assessment.evidence_gap


@pytest.mark.parametrize("claim", ["Changed `auth.py`.", "Fixed `auth.py`."])
def test_missing_file_evidence_cannot_establish_a_claim(
    tmp_path: Path, claim: str
) -> None:
    (tmp_path / "agent-session.txt").write_text(f"• Final answer:\n{claim}\n")

    assessment = analyze_run(_manifest(), run_dir=tmp_path).claim_assessments[0]

    assert assessment.support is ClaimSupport.CANNOT_DETERMINE
    assert assessment.evidence_references == []


@pytest.mark.parametrize("verb", ["Added", "Created"])
def test_file_creation_requires_an_observed_addition(tmp_path: Path, verb: str) -> None:
    (tmp_path / "agent-session.txt").write_text(f"• Final answer:\n{verb} `auth.py`.\n")
    # A captured empty-file addition has no hunk or file-content headers.
    (tmp_path / "patch.diff").write_text(
        "diff --git a/auth.py b/auth.py\nnew file mode 100644\nindex 0000000..e69de29\n"
    )

    assessment = analyze_run(_manifest(), run_dir=tmp_path).claim_assessments[0]

    assert assessment.support is ClaimSupport.SUPPORTED
    assert assessment.evidence_references[0].artifact_path == "patch.diff"
    assert "change type: added" in assessment.evidence_references[0].description


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
        process_outcome="completed",
        analysis_outcome="not_run",
        package_outcome="partial",
        git_evidence=GitEvidenceManifest(
            git_before_path="git-before.txt",
            git_after_path="git-after.txt",
            changed_files_path="changed-files.txt",
            patch_path="patch.diff",
            patch_material_present=True,
        ),
    )


def test_ambiguous_diff_path_does_not_invent_a_matching_target(tmp_path: Path) -> None:
    (tmp_path / "agent-session.txt").write_text("• Final answer:\nChanged `auth.py`.\n")
    (tmp_path / "changed-files.txt").write_text("auth b/auth.py\n")
    (tmp_path / "patch.diff").write_text(
        "diff --git a/auth b/auth.py b/auth b/auth.py\n"
        "--- a/auth b/auth.py\t\n+++ b/auth b/auth.py\t\n@@ -1 +1 @@\n-old\n+new\n"
    )

    assessment = analyze_run(_manifest(), run_dir=tmp_path).claim_assessments[0]

    assert assessment.support is ClaimSupport.UNSUPPORTED


def test_unparsed_nonempty_diff_does_not_prove_no_changes(tmp_path: Path) -> None:
    (tmp_path / "agent-session.txt").write_text("• Final answer:\nNo files changed.\n")
    (tmp_path / "changed-files.txt").write_text("")
    (tmp_path / "patch.diff").write_text(
        'diff --git "a/quoted\\tfile.py" "b/quoted\\tfile.py"\n'
    )

    assessment = analyze_run(_manifest(), run_dir=tmp_path).claim_assessments[0]

    assert assessment.support is ClaimSupport.CANNOT_DETERMINE


def test_unparsed_header_cannot_supply_another_files_operation(tmp_path: Path) -> None:
    (tmp_path / "agent-session.txt").write_text("• Final answer:\nDeleted `auth.py`.\n")
    (tmp_path / "changed-files.txt").write_text("auth.py\n")
    (tmp_path / "patch.diff").write_text(
        "diff --git a/auth.py b/auth.py\n"
        'diff --git "a/quoted\\tfile.py" "b/quoted\\tfile.py"\n'
        "deleted file mode 100644\n"
    )

    assessment = analyze_run(_manifest(), run_dir=tmp_path).claim_assessments[0]

    assert assessment.support is ClaimSupport.CANNOT_DETERMINE
