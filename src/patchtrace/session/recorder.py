from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO, cast

import pexpect  # type: ignore[import-untyped]


@dataclass(frozen=True)
class RecordedSession:
    transcript_path: Path
    exit_status: int


def record_command(
    *,
    command: Sequence[str],
    transcript_path: Path,
    cwd: Path,
) -> RecordedSession:
    if not command:
        raise ValueError("command must contain at least one argument")

    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    with transcript_path.open("w", encoding="utf-8") as transcript_file:
        child = pexpect.spawn(
            command[0],
            list(command[1:]),
            cwd=str(cwd),
            encoding="utf-8",
            codec_errors="replace",
            echo=False,
            timeout=None,
        )
        child.logfile = _TranscriptLog(transcript_file)
        if _stdio_supports_passthrough():
            child.interact(escape_character=None)
        else:
            child.expect(pexpect.EOF)
        child.close()

        exit_status = _normalize_exit_status(
            cast("int | None", child.exitstatus),
            cast("int | None", child.signalstatus),
        )
        transcript_file.write(
            f"\n[patchtrace] wrapped command exited with status {exit_status}\n"
        )

    return RecordedSession(transcript_path=transcript_path, exit_status=exit_status)


class _TranscriptLog:
    def __init__(self, transcript_file: TextIO) -> None:
        self._transcript_file = transcript_file

    def write(self, data: bytes | str) -> int:
        text = (
            data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
        )
        return self._transcript_file.write(text)

    def flush(self) -> None:
        self._transcript_file.flush()


def _stdio_supports_passthrough() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _normalize_exit_status(exit_status: int | None, signal_status: int | None) -> int:
    if exit_status is not None:
        return exit_status
    if signal_status is not None:
        return 128 + signal_status
    return 1
