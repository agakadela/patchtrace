from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from patchtrace.cli.app import app

runner = CliRunner()


def test_run_inside_git_repo_writes_git_evidence_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    change_command = (
        "from pathlib import Path; "
        "Path('tracked.txt').write_text('after\\n', encoding='utf-8'); "
        "print('changed tracked.txt')"
    )
    result = runner.invoke(app, ["run", "--", sys.executable, "-c", change_command])

    assert result.exit_code == 0

    run_dir = next((Path(".patchtrace") / "runs").iterdir())
    manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    summary = (run_dir / "SUMMARY.md").read_text(encoding="utf-8")
    feedback = (run_dir / "AGENT_FEEDBACK.md").read_text(encoding="utf-8")
    verification_brief = (run_dir / "VERIFICATION_BRIEF.md").read_text(encoding="utf-8")

    assert (run_dir / "git-before.txt").exists()
    assert (run_dir / "git-after.txt").exists()
    assert (run_dir / "changed-files.txt").exists()
    assert (run_dir / "patch.diff").exists()
    assert (run_dir / "AGENT_FEEDBACK.md").exists()
    assert (run_dir / "VERIFICATION_BRIEF.md").exists()

    assert manifest["artifact_paths"] == [
        "run.json",
        "agent-session.txt",
        "git-before.txt",
        "git-after.txt",
        "changed-files.txt",
        "patch.diff",
        "SUMMARY.md",
        "AGENT_FEEDBACK.md",
        "VERIFICATION_BRIEF.md",
    ]
    assert manifest["git_evidence"] == {
        "git_before_path": "git-before.txt",
        "git_after_path": "git-after.txt",
        "changed_files_path": "changed-files.txt",
        "patch_path": "patch.diff",
        "patch_material_present": True,
    }

    assert (run_dir / "git-before.txt").read_text(encoding="utf-8") == ""
    assert " M tracked.txt" in (run_dir / "git-after.txt").read_text(encoding="utf-8")
    assert (run_dir / "changed-files.txt").read_text(encoding="utf-8") == (
        "tracked.txt\n"
    )

    patch = (run_dir / "patch.diff").read_text(encoding="utf-8")
    assert "-before" in patch
    assert "+after" in patch

    assert "## Local Evidence" in summary
    assert "- Diff material: `present`" in summary
    assert "- `tracked.txt`" in summary
    assert "# PatchTrace Agent Feedback" in feedback
    assert "- Diff material: `present`" in feedback
    assert "- `tracked.txt`" in feedback
    assert "# PatchTrace Verification Brief" in verification_brief
    assert "- Diff material: `present`" in verification_brief
    assert "Review `tracked.txt` first." in verification_brief


def test_run_outside_git_repo_exits_without_writing_run_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["run", "--", sys.executable, "-c", "print('should not run')"],
    )

    assert result.exit_code == 1
    assert "PatchTrace run requires a Git work tree" in result.output
    assert "should not run" not in result.output
    assert not (tmp_path / ".patchtrace").exists()


def _init_git_repo(path: Path) -> None:
    _git(path, "init")
    _git(path, "config", "user.name", "PatchTrace Test")
    _git(path, "config", "user.email", "patchtrace-test@example.com")
    (path / "tracked.txt").write_text("before\n", encoding="utf-8")
    _git(path, "add", "tracked.txt")
    _git(path, "commit", "-m", "initial")


def _git(path: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
