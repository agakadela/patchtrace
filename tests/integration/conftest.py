from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def run_storage(
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    state_home = tmp_path_factory.mktemp("patchtrace-state")
    monkeypatch.setenv("XDG_STATE_HOME", str(state_home))
    return state_home
