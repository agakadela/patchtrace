from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from patchtrace.cli.app import app

runner = CliRunner()
FIXTURE = Path(__file__).parents[1] / "fixtures" / "fake_agent.py"


def test_fake_run_creates_run_folder_manifest_and_transcript(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["run", "--", sys.executable, str(FIXTURE)])

    assert result.exit_code == 0

    run_dirs = list((Path(".patchtrace") / "runs").iterdir())
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]

    manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    transcript = (run_dir / "agent-session.txt").read_text(encoding="utf-8")

    assert manifest["run_id"] == run_dir.name
    assert manifest["command"] == [sys.executable, str(FIXTURE)]
    assert manifest["trigger_source"] == "manual_cli"
    assert manifest["wrapped_command_exit_status"] == 0
    assert manifest["outcome"] == "completed"
    assert manifest["artifact_paths"] == [
        "run.json",
        "agent-session.txt",
        "git-before.txt",
        "git-after.txt",
        "changed-files.txt",
        "patch.diff",
    ]
    assert manifest["git_evidence"]["patch_material_present"] is False
    assert "started_at" in manifest
    assert "ended_at" in manifest
    assert "fake agent says hello" in transcript


def test_nonzero_fake_run_records_exit_without_claiming_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["run", "--", sys.executable, str(FIXTURE), "--exit-code", "7"],
    )

    assert result.exit_code == 7

    run_dir = next((Path(".patchtrace") / "runs").iterdir())
    manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    transcript = (run_dir / "agent-session.txt").read_text(encoding="utf-8")

    assert manifest["wrapped_command_exit_status"] == 7
    assert manifest["outcome"] == "wrapped_command_failed"
    assert "success" not in manifest
    assert "fake agent exiting with 7" in transcript


def _init_git_repo(path: Path) -> None:
    _git(path, "init")
    _git(path, "config", "user.name", "PatchTrace Test")
    _git(path, "config", "user.email", "patchtrace-test@example.com")
    (path / "tracked.txt").write_text("baseline\n", encoding="utf-8")
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
