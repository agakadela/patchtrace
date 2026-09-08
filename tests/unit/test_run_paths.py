from pathlib import Path

import pytest

from patchtrace.storage.runs import create_run_paths


@pytest.mark.parametrize("state_value", [None, "", "relative/state"])
def test_default_state_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, state_value: str | None
) -> None:
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    if state_value is None:
        monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    else:
        monkeypatch.setenv("XDG_STATE_HOME", state_value)

    paths = create_run_paths(tmp_path / "repo")
    assert paths.run_dir.is_relative_to(home / ".local/state/patchtrace/repos")
    assert paths.run_dir.stat().st_mode & 0o777 == 0o700


def test_repository_path_alias_uses_same_storage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(repo, target_is_directory=True)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))

    first = create_run_paths(repo)
    second = create_run_paths(alias)
    assert first.run_dir.parent == second.run_dir.parent
    assert first.run_id != second.run_id
