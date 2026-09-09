from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from patchtrace.cli.app import app

runner = CliRunner()


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


def run_package(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(workspace)
    result = runner.invoke(
        app,
        ["run", "--", sys.executable, "-c", "print('Final answer: No changes.')"],
    )
    assert result.exit_code == 0, result.output
    prefix = "PatchTrace review package written to "
    location = next(
        line for line in result.output.splitlines() if line.startswith(prefix)
    )
    return Path(location.removeprefix(prefix))


@pytest.mark.parametrize("existing_ignore", [False, True])
def test_git_add_does_not_stage_any_run_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, existing_ignore: bool
) -> None:
    git(tmp_path, "init")
    if existing_ignore:
        (tmp_path / ".gitignore").write_text("user-only-pattern\n")
    original_config = (tmp_path / ".git/config").read_bytes()
    (tmp_path / "user.txt").write_text("user work\n")

    run_dir = run_package(tmp_path, monkeypatch)
    git(tmp_path, "add", ".")
    staged = git(tmp_path, "diff", "--cached", "--name-only").splitlines()
    assert staged == ([".gitignore", "user.txt"] if existing_ignore else ["user.txt"])
    assert run_dir.is_absolute()
    assert not run_dir.resolve().is_relative_to(tmp_path.resolve())
    manifest = json.loads((run_dir / "run.json").read_text())
    assert manifest["repository_root"] == str(tmp_path.resolve())
    assert manifest["run_id"] == run_dir.name
    assert len(manifest["artifact_paths"]) == 10
    assert all((run_dir / name).is_file() for name in manifest["artifact_paths"])
    assert (tmp_path / ".git/config").read_bytes() == original_config
    if existing_ignore:
        assert (tmp_path / ".gitignore").read_text() == "user-only-pattern\n"
    else:
        assert not (tmp_path / ".gitignore").exists()


def test_repository_association_is_stable_from_subdirectories_and_distinct_for_repositories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    subdir = repo / "subdir"
    subdir.mkdir(parents=True)
    git(repo, "init")
    other_repo = tmp_path / "other" / "repo"
    other_repo.mkdir(parents=True)
    git(other_repo, "init")

    first = run_package(repo, monkeypatch)
    second = run_package(subdir, monkeypatch)
    other = run_package(other_repo, monkeypatch)
    assert first != second
    assert first.parent == second.parent
    assert first.parent != other.parent
    assert json.loads((second / "run.json").read_text())["repository_root"] == str(
        repo.resolve()
    )


@pytest.mark.parametrize("symlink", [False, True])
def test_storage_inside_repository_is_rejected_before_command_or_artifacts(
    tmp_path: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
    symlink: bool,
) -> None:
    git(tmp_path, "init")
    state_home = tmp_path / "state"
    if symlink:
        link = run_storage / "link"
        link.symlink_to(state_home, target_is_directory=True)
        monkeypatch.setenv("XDG_STATE_HOME", str(link))
    else:
        monkeypatch.setenv("XDG_STATE_HOME", str(state_home))
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app, ["run", "--", sys.executable, "-c", "print('must not execute')"]
    )
    assert result.exit_code == 1
    assert "outside the repository" in result.output
    assert "must not execute" not in result.output
    assert not state_home.exists()
    assert git(tmp_path, "status", "--porcelain") == ""


def test_unwritable_storage_reports_error_without_executing_command(
    tmp_path: Path, run_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    git(tmp_path, "init")
    (run_storage / "patchtrace").write_text("not a directory")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app, ["run", "--", sys.executable, "-c", "print('must not execute')"]
    )
    assert result.exit_code == 1
    assert "Unable to create PatchTrace run storage" in result.output
    assert "must not execute" not in result.output
    assert git(tmp_path, "status", "--porcelain") == ""
