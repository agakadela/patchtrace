import subprocess
from pathlib import Path

import pytest

from patchtrace.vcs.envelope import parse_status
from patchtrace.vcs.git import GitCommandError, git_output


def test_status_preserves_spaces_newlines_quotes_and_arrow_characters() -> None:
    facts = parse_status(' M space name\0?? a -> b\0 D quote"\t\r\n\0')
    assert [(f.status, f.path) for f in facts] == [
        (" M", "space name"),
        ("??", "a -> b"),
        (" D", 'quote"\t\r\n'),
    ]


def test_git_timeout_becomes_capture_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired("git", 30)

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(GitCommandError, match="timed out"):
        git_output(Path.cwd(), "status")
