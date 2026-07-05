from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path


class GitCommandError(RuntimeError):
    def __init__(self, command: Sequence[str], stderr: str) -> None:
        self.command = list(command)
        self.stderr = stderr.strip()
        command_text = " ".join(self.command)
        message = f"{command_text} failed"
        if self.stderr:
            message = f"{message}: {self.stderr}"
        super().__init__(message)


def is_inside_work_tree(cwd: Path) -> bool:
    command = ["git", "rev-parse", "--is-inside-work-tree"]
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise GitCommandError(command, "git executable was not found") from error

    return result.returncode == 0 and result.stdout.strip() == "true"


def git_output(cwd: Path, *args: str) -> str:
    command = ["git", *args]
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise GitCommandError(command, "git executable was not found") from error

    if result.returncode != 0:
        raise GitCommandError(command, result.stderr)

    return result.stdout
