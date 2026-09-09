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
    command = ["git", "--no-optional-locks", "rev-parse", "--is-inside-work-tree"]
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


def git_output(cwd: Path, *args: str, input_text: str | None = None) -> str:
    command = [
        "git",
        "--no-optional-locks",
        "--no-lazy-fetch",
        "--no-replace-objects",
        "-c",
        "core.fsmonitor=false",
        *args,
    ]
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            input=input_text.encode("utf-8") if input_text is not None else None,
            timeout=30,
        )
        stdout = result.stdout.decode("utf-8")
        stderr = result.stderr.decode("utf-8", errors="replace")
    except (OSError, UnicodeError, subprocess.TimeoutExpired) as error:
        raise GitCommandError(command, str(error)) from error

    if result.returncode != 0:
        raise GitCommandError(command, stderr)

    return stdout
