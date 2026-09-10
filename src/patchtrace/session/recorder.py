from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO, cast

import pexpect  # type: ignore[import-untyped]

from patchtrace.models.run import ProcessOutcome


class RecordingError(Exception):
    def __init__(
        self,
        stage: str,
        message: str,
        process_outcome: ProcessOutcome,
        exit_status: int | None,
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.process_outcome = process_outcome
        self.exit_status = exit_status


class _TranscriptWriteError(OSError):
    pass


@dataclass(frozen=True)
class RecordedSession:
    transcript_path: Path
    exit_status: int


def record_command(
    *,
    command: Sequence[str],
    transcript_path: Path,
    cwd: Path,
    on_started: Callable[[], None] | None = None,
) -> RecordedSession:
    if not command:
        raise ValueError("command must contain at least one argument")

    stage = "transcript_write"
    process_outcome: ProcessOutcome = "not_started"
    exit_status = None
    try:
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        with transcript_path.open("w", encoding="utf-8") as transcript_file:
            stage = "process_start"
            child = pexpect.spawn(
                command[0],
                list(command[1:]),
                cwd=str(cwd),
                encoding="utf-8",
                codec_errors="replace",
                echo=False,
                timeout=None,
            )
            process_outcome = "unknown"
            stage = "session_capture"
            try:
                if on_started is not None:
                    stage = "process_checkpoint_write"
                    on_started()
                    stage = "session_capture"
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
                if exit_status is None:
                    raise RuntimeError("Wrapped command exit status is unavailable")
                process_outcome = "completed" if exit_status == 0 else "failed"
            finally:
                # interact() can observe an exit and then fail while restoring
                # the terminal. Retain that result before cleanup can alter it.
                if exit_status is None:
                    exit_status = _normalize_exit_status(
                        cast("int | None", child.exitstatus),
                        cast("int | None", child.signalstatus),
                    )
                    if exit_status is not None:
                        process_outcome = "completed" if exit_status == 0 else "failed"
                # Pexpect close(force=True) also terminates a live child. Never
                # report that cleanup termination as the command's own result.
                child.close(force=True)
            stage = "transcript_write"
            transcript_file.write(
                f"\n[patchtrace] wrapped command exited with status {exit_status}\n"
            )
    except (Exception, KeyboardInterrupt) as error:
        if isinstance(error, _TranscriptWriteError):
            stage = "transcript_write"
        raise RecordingError(
            stage, str(error) or type(error).__name__, process_outcome, exit_status
        ) from error

    return RecordedSession(transcript_path=transcript_path, exit_status=exit_status)


class _TranscriptLog:
    def __init__(self, transcript_file: TextIO) -> None:
        self._transcript_file = transcript_file

    def write(self, data: bytes | str) -> int:
        text = (
            data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
        )
        try:
            return self._transcript_file.write(text)
        except OSError as error:
            raise _TranscriptWriteError(str(error)) from error

    def flush(self) -> None:
        try:
            self._transcript_file.flush()
        except OSError as error:
            raise _TranscriptWriteError(str(error)) from error


def _stdio_supports_passthrough() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _normalize_exit_status(
    exit_status: int | None, signal_status: int | None
) -> int | None:
    if exit_status is not None:
        return exit_status
    if signal_status is not None:
        return 128 + signal_status
    return None
