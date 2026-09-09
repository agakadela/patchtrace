from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from patchtrace.analysis.analyzer import analyze_run
from patchtrace.models.report import AnalysisResult
from patchtrace.models.run import GitEvidenceManifest, RunManifest
from patchtrace.vcs.envelope import (
    GitBoundary,
    GitCommitFact,
    GitHistory,
    GitPathFact,
    GitSessionEnvelope,
    UntrackedEvidence,
)


def patch(path: str, text: str = "new") -> str:
    return f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -1 +1 @@\n-old\n+{text}\n"


def boundary(text: str | None = None) -> GitBoundary:
    return GitBoundary(
        head="a",
        dirty=text is not None,
        paths=[GitPathFact(" M", "file.txt")] if text is not None else [],
        staged_patch="",
        unstaged_patch=patch("file.txt", text) if text is not None else "",
        untracked=[],
    )


def analyze(tmp_path: Path, envelope: GitSessionEnvelope | None) -> AnalysisResult:
    now = datetime.now(UTC)
    manifest = RunManifest(
        run_id="attribution",
        command=["fake"],
        trigger_source="manual_cli",
        started_at=now,
        ended_at=now,
        wrapped_command_exit_status=0,
        outcome="completed",
        artifact_paths=[],
        git_evidence=GitEvidenceManifest(
            git_before_path="git-before.txt",
            git_after_path="git-after.txt",
            changed_files_path="changed-files.txt",
            patch_path="patch.diff",
            patch_material_present=True,
            session_envelope_path="git-session.json",
        ),
    )
    if envelope is not None:
        (tmp_path / "git-session.json").write_text(json.dumps(asdict(envelope)))
    result = analyze_run(manifest, run_dir=tmp_path)
    return AnalysisResult.model_validate_json(result.model_dump_json())


@pytest.mark.parametrize(
    ("before_text", "after_text", "expected"),
    [
        (None, "new", "session-attributed"),
        ("old work", "new", "indeterminate"),
        ("old work", "old work", "pre-existing"),
    ],
)
def test_boundary_fixture_matrix(
    tmp_path: Path, before_text: str | None, after_text: str, expected: str
) -> None:
    result = analyze(
        tmp_path,
        GitSessionEnvelope(
            "/repo",
            patch_prefixes="a/b",
            before=boundary(before_text),
            after=boundary(after_text),
            history=GitHistory("unchanged"),
            capture_status="complete",
        ),
    )
    attribution = result.git_attribution
    final = [item for item in attribution.items if item.material == "final"]
    assert [(item.path, item.attribution) for item in final] == [("file.txt", expected)]
    assert all(item.evidence_references for item in attribution.items)
    assert any("authorship" in limitation for limitation in attribution.limitations)
    if before_text is not None:
        assert attribution.items[0].attribution == "pre-existing"


def test_identical_status_with_changed_bytes_is_not_pre_existing(
    tmp_path: Path,
) -> None:
    before = boundary("old work")
    after = boundary("new work")
    assert before.paths == after.paths
    result = analyze(
        tmp_path,
        GitSessionEnvelope(
            "/repo",
            patch_prefixes="a/b",
            before=before,
            after=after,
            history=GitHistory("unchanged"),
            capture_status="complete",
        ),
    )
    assert result.git_attribution.items[-1].attribution == "indeterminate"


@pytest.mark.parametrize("dirty", [False, True])
def test_commit_material_respects_initial_dirty_paths(
    tmp_path: Path, dirty: bool
) -> None:
    result = analyze(
        tmp_path,
        GitSessionEnvelope(
            "/repo",
            patch_prefixes="a/b",
            before=boundary("old work" if dirty else None),
            after=replace(boundary(), head="b"),
            history=GitHistory("linear", [GitCommitFact("b", "a", patch("file.txt"))]),
            capture_status="complete",
        ),
    )
    commit = result.git_attribution.items[-1]
    assert commit.material == "commit"
    assert commit.commit_head == "b"
    assert commit.attribution == ("indeterminate" if dirty else "session-attributed")


@pytest.mark.parametrize("initial", [False, True])
@pytest.mark.parametrize("captured", [False, True])
def test_untracked_identity_needs_content_only_for_pre_existing(
    tmp_path: Path,
    initial: bool,
    captured: bool,
) -> None:
    untracked = replace(
        boundary(),
        dirty=True,
        paths=[GitPathFact("??", "new.txt")],
        untracked=[
            UntrackedEvidence(
                "new.txt",
                "eA==" if captured else None,
                "digest" if captured else None,
                None if captured else "Content omitted",
            )
        ],
    )
    result = analyze(
        tmp_path,
        GitSessionEnvelope(
            "/repo",
            patch_prefixes="a/b",
            before=untracked if initial else boundary(),
            after=untracked,
            history=GitHistory("unchanged"),
            capture_status="complete",
        ),
    )
    expected = "pre-existing" if captured else "indeterminate"
    assert result.git_attribution.items[-1].attribution == (
        expected if initial else "session-attributed"
    )
    if not captured:
        assert "Content omitted" in result.git_attribution.items[-1].limitations


def test_unsupported_history_is_indeterminate_even_with_clean_boundaries(
    tmp_path: Path,
) -> None:
    result = analyze(
        tmp_path,
        GitSessionEnvelope(
            "/repo",
            patch_prefixes="a/b",
            before=boundary(),
            after=replace(boundary(), head="b"),
            history=GitHistory("unsupported", limitations=["History was rewritten"]),
            capture_status="complete",
        ),
    )
    assert result.git_attribution.items[-1].attribution == "indeterminate"
    assert "History was rewritten" in result.git_attribution.limitations


@pytest.mark.parametrize("contents", [None, "{", '{"schema_version": 99}'])
def test_missing_or_invalid_envelope_never_uses_legacy_snapshot_for_attribution(
    tmp_path: Path,
    contents: str | None,
) -> None:
    if contents is not None:
        (tmp_path / "git-session.json").write_text(contents)
    (tmp_path / "changed-files.txt").write_text("file.txt\n")
    result = analyze(tmp_path, None)
    assert not any(
        item.attribution == "session-attributed"
        for item in result.git_attribution.items
    )
    assert any(
        "rerun capture" in limitation
        for limitation in result.git_attribution.limitations
    )


def test_phase4_five_unchanged_dirty_paths_are_all_pre_existing(tmp_path: Path) -> None:
    names = [f"file-{index}.txt" for index in range(5)]
    dirty = replace(
        boundary(),
        dirty=True,
        paths=[GitPathFact(" M", name) for name in names],
        unstaged_patch="".join(patch(name, "pre-existing") for name in names),
    )
    result = analyze(
        tmp_path,
        GitSessionEnvelope(
            "/repo",
            patch_prefixes="a/b",
            before=dirty,
            after=dirty,
            history=GitHistory("unchanged"),
            capture_status="complete",
        ),
    )
    assert len(result.git_attribution.items) == 10
    assert {item.attribution for item in result.git_attribution.items} == {
        "pre-existing"
    }


def test_unrelated_edits_do_not_reclassify_unchanged_initial_file(
    tmp_path: Path,
) -> None:
    before = boundary("old work")
    after = replace(
        before,
        paths=[*before.paths, GitPathFact(" M", "other.txt")],
        unstaged_patch=before.unstaged_patch + patch("other.txt"),
    )
    result = analyze(
        tmp_path,
        GitSessionEnvelope(
            "/repo",
            patch_prefixes="a/b",
            before=before,
            after=after,
            history=GitHistory("unchanged"),
            capture_status="complete",
        ),
    )
    assert {
        (item.path, item.attribution)
        for item in result.git_attribution.items
        if item.material == "final"
    } == {
        ("file.txt", "pre-existing"),
        ("other.txt", "session-attributed"),
    }


@pytest.mark.parametrize(
    "kind",
    [
        "staging",
        "untracked-bytes",
        "unsupported-patch",
        "failed-capture",
        "broken-chain",
    ],
)
def test_inseparable_or_incomplete_facts_never_gain_session_attribution(
    tmp_path: Path,
    kind: str,
) -> None:
    before = boundary("old work")
    after = before
    envelope = GitSessionEnvelope(
        "/repo",
        patch_prefixes="a/b",
        before=before,
        after=after,
        history=GitHistory("unchanged"),
        capture_status="complete",
    )
    if kind == "staging":
        envelope.after = replace(
            before,
            staged_patch=before.unstaged_patch,
            unstaged_patch="",
            paths=[GitPathFact("M ", "file.txt")],
        )
    elif kind == "untracked-bytes":
        envelope.before = replace(
            boundary(),
            dirty=True,
            paths=[GitPathFact("??", "file.txt")],
            untracked=[UntrackedEvidence("file.txt", "b2xk", "old")],
        )
        envelope.after = replace(
            envelope.before, untracked=[UntrackedEvidence("file.txt", "bmV3", "new")]
        )
    elif kind == "unsupported-patch":
        envelope.after = replace(after, unstaged_patch="diff --cc file.txt\n")
    elif kind == "failed-capture":
        envelope.capture_status = "failed"
        envelope.history = None
    elif kind == "broken-chain":
        envelope.history = GitHistory(
            "linear", [GitCommitFact("b", "wrong-parent", patch("file.txt"))]
        )
        envelope.after = replace(after, head="b")
    result = analyze(tmp_path, envelope)
    final = [item for item in result.git_attribution.items if item.material == "final"]
    assert final[0].attribution == "indeterminate"
    assert final[0].limitations
    assert not any(
        item.attribution == "session-attributed"
        for item in result.git_attribution.items
    )


@pytest.mark.parametrize("committed", [False, True])
def test_legacy_prefix_ambiguity_never_invents_session_paths(
    tmp_path: Path, committed: bool
) -> None:
    initial = boundary("old work")
    envelope = GitSessionEnvelope(
        "/repo",
        before=initial,
        after=initial,
        history=GitHistory("unchanged"),
        capture_status="complete",
    )
    if committed:
        envelope.after = replace(boundary(), head="b")
        envelope.history = GitHistory(
            "linear", [GitCommitFact("b", "a", patch("hidden/file.txt"))]
        )
    raw = asdict(envelope)
    del raw["patch_prefixes"]
    (tmp_path / "git-session.json").write_text(json.dumps(raw))
    result = analyze(tmp_path, None)
    assert not any(
        item.attribution == "session-attributed"
        for item in result.git_attribution.items
    )
    assert not any(
        item.path == "hidden/file.txt" for item in result.git_attribution.items
    )
    if not committed:
        assert (
            next(
                item
                for item in result.git_attribution.items
                if item.material == "final"
            ).attribution
            == "pre-existing"
        )
    assert any(
        "prefixes" in limitation for limitation in result.git_attribution.limitations
    )
