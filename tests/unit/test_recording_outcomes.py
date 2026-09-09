from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from patchtrace.session.recorder import RecordingError, record_command


@pytest.mark.parametrize("failure", [OSError("PTY unavailable"), KeyboardInterrupt()])
def test_failed_capture_closes_child_without_inventing_its_exit_status(
    tmp_path: Path,
    failure: BaseException,
) -> None:
    child = Mock(exitstatus=None, signalstatus=None)
    child.expect.side_effect = failure
    with (
        patch("patchtrace.session.recorder.pexpect.spawn", return_value=child),
        patch(
            "patchtrace.session.recorder._stdio_supports_passthrough",
            return_value=False,
        ),
        pytest.raises(RecordingError) as caught,
    ):
        record_command(
            command=["fake"], transcript_path=tmp_path / "session.txt", cwd=tmp_path
        )
    assert caught.value.process_outcome == "unknown"
    assert caught.value.exit_status is None
    assert caught.value.stage == "session_capture"
    child.close.assert_called_once_with(force=True)


def test_footer_write_failure_retains_observed_success(tmp_path: Path) -> None:
    class FailedTranscript(StringIO):
        def write(self, text: str) -> int:
            raise OSError("transcript disk full")

    child = Mock(exitstatus=0, signalstatus=None)
    with (
        patch("patchtrace.session.recorder.pexpect.spawn", return_value=child),
        patch(
            "patchtrace.session.recorder._stdio_supports_passthrough",
            return_value=False,
        ),
        patch.object(Path, "open", return_value=FailedTranscript()),
        pytest.raises(RecordingError) as caught,
    ):
        record_command(
            command=["fake"], transcript_path=tmp_path / "session.txt", cwd=tmp_path
        )
    assert caught.value.process_outcome == "completed"
    assert caught.value.exit_status == 0
    assert caught.value.stage == "transcript_write"


def test_missing_exit_status_is_unknown_instead_of_guessed_failure(
    tmp_path: Path,
) -> None:
    child = Mock(exitstatus=None, signalstatus=None)
    with (
        patch("patchtrace.session.recorder.pexpect.spawn", return_value=child),
        patch(
            "patchtrace.session.recorder._stdio_supports_passthrough",
            return_value=False,
        ),
        pytest.raises(RecordingError) as caught,
    ):
        record_command(
            command=["fake"], transcript_path=tmp_path / "session.txt", cwd=tmp_path
        )
    assert caught.value.process_outcome == "unknown"
    assert caught.value.exit_status is None


def test_signal_exit_is_normalized_to_shell_status(tmp_path: Path) -> None:
    child = Mock(exitstatus=None, signalstatus=15)
    with (
        patch("patchtrace.session.recorder.pexpect.spawn", return_value=child),
        patch(
            "patchtrace.session.recorder._stdio_supports_passthrough",
            return_value=False,
        ),
    ):
        result = record_command(
            command=["fake"], transcript_path=tmp_path / "session.txt", cwd=tmp_path
        )
    assert result.exit_status == 143


@pytest.mark.parametrize(
    "exit_status, signal_status, expected",
    [(0, None, 0), (7, None, 7), (None, 15, 143)],
)
def test_terminal_restore_failure_retains_already_observed_exit(
    tmp_path: Path,
    exit_status: int | None,
    signal_status: int | None,
    expected: int,
) -> None:
    child = Mock(exitstatus=exit_status, signalstatus=signal_status)
    child.interact.side_effect = OSError("terminal restoration failed")
    with (
        patch("patchtrace.session.recorder.pexpect.spawn", return_value=child),
        patch(
            "patchtrace.session.recorder._stdio_supports_passthrough", return_value=True
        ),
        pytest.raises(RecordingError) as caught,
    ):
        record_command(
            command=["fake"], transcript_path=tmp_path / "session.txt", cwd=tmp_path
        )
    assert caught.value.exit_status == expected
    assert caught.value.process_outcome == ("completed" if expected == 0 else "failed")
    assert caught.value.stage == "session_capture"
    child.close.assert_called_once_with(force=True)
