from __future__ import annotations

import base64
import subprocess
from pathlib import Path

import pytest

from patchtrace.vcs.envelope import capture_boundary, capture_history


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.name", "PatchTrace Test")
    git(tmp_path, "config", "user.email", "patchtrace-test@example.com")
    (tmp_path / "tracked.txt").write_text("before\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "initial")
    return tmp_path


def test_clean_to_modified_preserves_boundary_facts(repo: Path) -> None:
    before = capture_boundary(repo)
    (repo / "tracked.txt").write_text("after\n")
    after = capture_boundary(repo)
    assert before.head == after.head == git(repo, "rev-parse", "HEAD")
    assert before.dirty is False
    assert before.paths == []
    assert after.dirty is True
    assert [(p.status, p.path) for p in after.paths] == [(" M", "tracked.txt")]
    assert "-before" in after.unstaged_patch
    assert "+after" in after.unstaged_patch
    assert after.staged_patch == ""


def test_pre_existing_dirty_and_untracked_facts_are_preserved(repo: Path) -> None:
    (repo / "tracked.txt").write_text("staged\n")
    git(repo, "add", "tracked.txt")
    (repo / "tracked.txt").write_text("unstaged\n")
    (repo / "old.txt").write_bytes(b"old\x00bytes")
    before = capture_boundary(repo)
    after = capture_boundary(repo)
    assert before == after
    assert before.dirty
    assert "+staged" in before.staged_patch
    assert "+unstaged" in before.unstaged_patch
    assert {p.path for p in before.paths} == {"tracked.txt", "old.txt"}


def test_new_untracked_bytes_and_unusual_paths_are_preserved(repo: Path) -> None:
    before = capture_boundary(repo)
    name = 'new directory/quote" arrow -> tab\t carriage\r newline\n.txt'
    path = repo / name
    path.parent.mkdir()
    path.write_bytes(b"new\x00\xff\r\n")
    after = capture_boundary(repo)
    assert before.paths == []
    assert [(p.status, p.path) for p in after.paths] == [("??", name)]
    evidence = after.untracked[0]
    assert evidence.path == name
    assert evidence.content_base64 is not None
    assert base64.b64decode(evidence.content_base64) == path.read_bytes()


def test_linear_commits_preserve_patches_even_when_final_tree_is_unchanged(
    repo: Path,
) -> None:
    before = capture_boundary(repo)
    (repo / "tracked.txt").write_text("committed\n")
    git(repo, "commit", "-am", "change")
    first = git(repo, "rev-parse", "HEAD")
    (repo / "tracked.txt").write_text("before\n")
    git(repo, "commit", "-am", "undo")
    after = capture_boundary(repo)
    history = capture_history(repo, before, after)
    assert history.kind == "linear"
    assert [c.head for c in history.commits] == [first, after.head]
    assert history.commits[0].parent == before.head
    assert "+committed" in history.commits[0].patch
    assert "-committed" in history.commits[1].patch
    assert after.dirty is False
    assert after.unstaged_patch == after.staged_patch == ""


def test_capture_does_not_mutate_index_refs_or_worktree(repo: Path) -> None:
    # Touch content after commit so ordinary status would refresh the index.
    (repo / "tracked.txt").write_text("before\n")
    index = (repo / ".git/index").read_bytes()
    refs = git(repo, "show-ref", "--head")
    head = (repo / ".git/HEAD").read_bytes()
    files = {
        p.relative_to(repo): p.read_bytes()
        for p in repo.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(repo).parts
    }
    before = capture_boundary(repo)
    capture_history(repo, before, capture_boundary(repo))
    assert (repo / ".git/index").read_bytes() == index
    assert git(repo, "show-ref", "--head") == refs
    assert (repo / ".git/HEAD").read_bytes() == head
    assert {
        p.relative_to(repo): p.read_bytes()
        for p in repo.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(repo).parts
    } == files


def test_internal_artifacts_are_excluded_from_all_material(repo: Path) -> None:
    internal = repo / ".patchtrace"
    internal.mkdir()
    (internal / "tracked.txt").write_text("internal before\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "legacy internal artifact")
    before = capture_boundary(repo)
    (internal / "tracked.txt").write_text("internal after\n")
    (internal / "new.txt").write_text("internal untracked\n")
    after = capture_boundary(repo)
    assert not after.dirty
    assert after.paths == []
    assert after.untracked == []
    assert after.staged_patch == after.unstaged_patch == ""
    git(repo, "add", ".")
    git(repo, "commit", "-m", "internal changes")
    history = capture_history(repo, before, capture_boundary(repo))
    assert history.commits[0].patch == ""


def test_rewritten_history_is_explicitly_unsupported(repo: Path) -> None:
    before = capture_boundary(repo)
    git(repo, "commit", "--amend", "-m", "replacement")
    history = capture_history(repo, before, capture_boundary(repo))
    assert history.kind == "unsupported"
    assert history.commits == []
    assert history.limitations


def test_unborn_repository_retains_facts_with_history_limitation(
    tmp_path: Path,
) -> None:
    git(tmp_path, "init")
    before = capture_boundary(tmp_path)
    assert before.head is None
    assert before.dirty is False
    assert capture_history(tmp_path, before, before).kind == "unsupported"


@pytest.mark.parametrize("stage", ["before", "after", "history"])
def test_cli_preserves_capture_failure_and_partial_material(
    repo: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
) -> None:
    import json
    import sys

    from typer.testing import CliRunner

    from patchtrace.cli.app import app
    from patchtrace.vcs.git import GitCommandError

    calls = 0

    def fail_boundary(root: Path) -> object:
        nonlocal calls
        calls += 1
        if calls == (1 if stage == "before" else 2):
            raise GitCommandError(["git", "status"], "injected unreadable index")
        return capture_boundary(root)

    def fail_history(*args: object) -> object:
        raise GitCommandError(["git", "rev-list"], "injected missing object")

    if stage == "history":
        monkeypatch.setattr("patchtrace.cli.app.capture_history", fail_history)
    else:
        monkeypatch.setattr("patchtrace.cli.app.capture_boundary", fail_boundary)
    monkeypatch.chdir(repo)
    result = CliRunner().invoke(
        app, ["run", "--", sys.executable, "-c", "print('captured transcript')"]
    )
    assert result.exit_code == 1
    path = next(run_storage.rglob("git-session.json"))
    envelope = json.loads(path.read_text())
    assert envelope["capture_status"] == "failed"
    assert envelope["failed_stage"] == stage
    assert "injected" in envelope["error"]
    assert "rerun capture" in envelope["recovery"]
    assert str(path.parent) in result.output
    assert "review package written" not in result.output
    assert not (path.parent / "run.json").exists()
    if stage == "before":
        assert not (path.parent / "agent-session.txt").exists()
    else:
        assert envelope["before"]["head"]
        assert "captured transcript" in (path.parent / "agent-session.txt").read_text()
    if stage == "history":
        assert envelope["after"]["head"]


def test_untracked_symlink_and_large_file_have_explicit_limitations(repo: Path) -> None:
    from patchtrace.vcs.envelope import MAX_UNTRACKED_BYTES

    (repo / "link").symlink_to(repo / "tracked.txt")
    (repo / "large").write_bytes(b"x" * (MAX_UNTRACKED_BYTES + 1))
    after = capture_boundary(repo)
    assert len(after.untracked) == 2
    assert all(e.content_base64 is None and e.limitation for e in after.untracked)


def test_merge_history_is_not_presented_as_linear(repo: Path) -> None:
    before = capture_boundary(repo)
    branch = git(repo, "branch", "--show-current")
    git(repo, "checkout", "-b", "side")
    (repo / "side.txt").write_text("side\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "side change")
    git(repo, "checkout", branch)
    git(repo, "merge", "--no-ff", "side", "-m", "merge side")
    history = capture_history(repo, before, capture_boundary(repo))
    assert history.kind == "unsupported"
    assert history.commits == []
    assert "merges" in history.limitations[0]


def test_diff_never_executes_configured_helpers(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    helper = repo / "helper.sh"
    helper.write_text("#!/bin/sh\ntouch helper-was-run\n")
    helper.chmod(0o700)
    monkeypatch.setenv("GIT_EXTERNAL_DIFF", str(helper))
    (repo / ".gitattributes").write_text("tracked.txt diff=test\n")
    git(repo, "config", "diff.test.textconv", str(helper))
    git(repo, "config", "core.fsmonitor", str(helper))
    git(repo, "config", "color.ui", "always")
    (repo / "tracked.txt").write_text("after\n")
    after = capture_boundary(repo)
    assert "+after" in after.unstaged_patch
    assert "\x1b" not in after.unstaged_patch
    assert not (repo / "helper-was-run").exists()


def test_active_content_filter_fails_before_executing_helper(repo: Path) -> None:
    from patchtrace.vcs.git import GitCommandError

    (repo / ".gitattributes").write_text("tracked.txt filter=test\n")
    git(repo, "config", "filter.test.clean", "touch filter-was-run; cat")
    (repo / "tracked.txt").write_text("after\n")
    with pytest.raises(GitCommandError, match="Active clean/process filters"):
        capture_boundary(repo)
    assert not (repo / "filter-was-run").exists()


def test_cli_from_subdirectory_preserves_commits_and_new_file_bytes(
    repo: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import json
    import sys

    from typer.testing import CliRunner

    from patchtrace.cli.app import app

    (repo / "pre-existing.txt").write_text("old dirty work\n")
    subdir = repo / "subdir"
    subdir.mkdir()
    monkeypatch.chdir(subdir)
    script = (
        "from pathlib import Path; import subprocess; "
        "Path('../tracked.txt').write_text('committed change\\n'); "
        "subprocess.run(['git', 'commit', '-am', 'session change'], check=True); "
        "Path('new.bin').write_bytes(b'new\\x00bytes')"
    )
    result = CliRunner().invoke(app, ["run", "--", sys.executable, "-c", script])
    assert result.exit_code == 0, result.output
    path = next(run_storage.rglob("git-session.json"))
    envelope = json.loads(path.read_text())
    assert envelope["repository_root"] == str(repo)
    assert envelope["before"]["paths"] == [{"status": "??", "path": "pre-existing.txt"}]
    assert envelope["history"]["kind"] == "linear"
    assert "+committed change" in envelope["history"]["commits"][0]["patch"]
    content = {
        e["path"]: base64.b64decode(e["content_base64"])
        for e in envelope["after"]["untracked"]
    }
    assert content == {
        "pre-existing.txt": b"old dirty work\n",
        "subdir/new.bin": b"new\x00bytes",
    }
    assert "subdir/new.bin" in (path.parent / "changed-files.txt").read_text()
