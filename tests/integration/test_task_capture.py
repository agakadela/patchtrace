import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from patchtrace.cli.app import app
from patchtrace.models.run import RunManifest
from patchtrace.task.contract import ParsedTask

FIXTURES = Path(__file__).parents[1] / "fixtures" / "tasks"
REPORTS = ("SUMMARY.md", "AGENT_FEEDBACK.md", "VERIFICATION_BRIEF.md")


@pytest.mark.parametrize(
    "name", ["valid", "minimal", "na", "invalid", "duplicate", None]
)
def test_task_capture_binds_original_bytes_and_lifecycle(
    tmp_path: Path, run_storage: Path, monkeypatch: pytest.MonkeyPatch, name: str | None
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    args = ["run"]
    raw = b""
    if name is not None:
        # Preserve Unicode, BOM, CRLF, trailing whitespace, and no final newline.
        raw = (
            b"\xef\xbb\xbf"
            + (FIXTURES / f"{name}.md").read_bytes().replace(b"\n", b"\r\n").rstrip()
            + b"  "
        )
        (tmp_path / "task.md").write_bytes(raw)
        args += ["--task-file", "task.md"]
    child = "from pathlib import Path; Path('command-ran').touch(); print('Final answer:\\nDone.')"
    result = CliRunner().invoke(app, [*args, "--", sys.executable, "-c", child])
    manifest_path = next(run_storage.rglob("run.json"))
    manifest = RunManifest.model_validate_json(manifest_path.read_text())
    invalid = name in ("invalid", "duplicate")
    assert result.exit_code == (1 if invalid else 0), result.output
    assert manifest.process_outcome == ("not_started" if invalid else "completed")
    assert manifest.analysis_outcome == ("failed" if invalid else "completed")
    assert manifest.package_outcome == ("partial" if invalid else "complete")
    assert (tmp_path / "command-ran").exists() is not invalid
    if name is None:
        assert manifest.task is None
        for report in REPORTS:
            assert "No task was supplied" in (manifest_path.parent / report).read_text()
    else:
        assert manifest.task is not None
        assert manifest.task.sha256 == sha256(raw).hexdigest()
        assert manifest.task.raw_path in manifest.artifact_paths
        assert manifest.task.parsed_path in manifest.artifact_paths
        assert (manifest_path.parent / manifest.task.raw_path).read_bytes() == raw
        parsed = ParsedTask.model_validate_json(
            (manifest_path.parent / manifest.task.parsed_path).read_text()
        )
        assert parsed.run_id == manifest.run_id
        assert parsed.sha256 == manifest.task.sha256
        assert (
            parsed.status
            == manifest.task.parse_status
            == ("invalid" if invalid else "valid")
        )
        if invalid:
            assert manifest.failures[0].stage == "task_parse"
            assert parsed.errors[0] in manifest.failures[0].message
        else:
            for report in REPORTS:
                text = (manifest_path.parent / report).read_text()
                assert "task.md" in text and "task.json" in text
                assert "Requirement satisfaction is not evaluated" in text
                assert "Task delivery is unverified" in text


def test_task_file_help_is_discoverable() -> None:
    result = CliRunner().invoke(app, ["run", "--help"], color=False)
    assert result.exit_code == 0
    assert "--task-file" in result.output


def test_missing_task_file_preserves_read_failure(
    tmp_path: Path, run_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app, ["run", "--task-file", "missing.md", "--", "echo", "hello"]
    )
    assert result.exit_code == 1
    manifest = RunManifest.model_validate_json(
        next(run_storage.rglob("run.json")).read_text()
    )
    assert manifest.process_outcome == "not_started"
    assert manifest.analysis_outcome == "not_run"
    assert manifest.package_outcome == "partial"
    assert manifest.failures[0].stage == "task_read"
    assert "missing.md" in manifest.failures[0].message


@pytest.mark.parametrize("artifact", ["task.md", "task.json"])
def test_task_write_failure_prevents_launch(
    tmp_path: Path, run_storage: Path, monkeypatch: pytest.MonkeyPatch, artifact: str
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    original = Path.open

    # A write failure at either new artifact must use T4's package failure path.
    from typing import IO, Any

    def fail_open(path: Path, mode: str = "r", *args: Any, **kwargs: Any) -> IO[Any]:
        if path.name == artifact and "w" in mode and path.is_relative_to(run_storage):
            raise OSError("injected task write failure")
        return original(path, mode, *args, **kwargs)

    with patch.object(Path, "open", fail_open):
        result = CliRunner().invoke(
            app,
            ["run", "--task-file", str(FIXTURES / "valid.md"), "--", "echo", "hello"],
        )
    assert result.exit_code == 1
    manifest = RunManifest.model_validate_json(
        next(run_storage.rglob("run.json")).read_text()
    )
    assert manifest.process_outcome == "not_started"
    assert manifest.package_outcome == "failed"
    assert manifest.failures[0].stage == "task_artifact_write"


def _init_git_repo(path: Path) -> None:
    for args in (
        ["init"],
        ["config", "user.name", "PatchTrace Test"],
        ["config", "user.email", "patchtrace-test@example.com"],
        ["commit", "--allow-empty", "-m", "initial"],
    ):
        subprocess.run(["git", *args], cwd=path, check=True, capture_output=True)


def test_task_source_is_captured_once_before_command_changes_it(
    tmp_path: Path, run_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    original = (FIXTURES / "minimal.md").read_bytes()
    (tmp_path / "task.md").write_bytes(original)
    child = (
        "from pathlib import Path; import sys; "
        "assert sys.argv[1:] == ['--task-file', 'child-owned']; "
        "Path('task.md').write_text('changed during the run'); "
        "print('Final answer:\\nDone.')"
    )
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--task-file",
            "task.md",
            "--",
            sys.executable,
            "-c",
            child,
            "--task-file",
            "child-owned",
        ],
    )
    assert result.exit_code == 0, result.output
    manifest_path = next(run_storage.rglob("run.json"))
    manifest = RunManifest.model_validate_json(manifest_path.read_text())
    assert manifest.task is not None
    assert manifest.task.sha256 == sha256(original).hexdigest()
    assert (manifest_path.parent / manifest.task.raw_path).read_bytes() == original
    assert (tmp_path / "task.md").read_bytes() != original


def test_non_utf8_task_is_preserved_with_explicit_parse_failure(
    tmp_path: Path, run_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "binary.md").write_bytes(b"\xff\x00\r\n")
    result = CliRunner().invoke(
        app, ["run", "--task-file", "binary.md", "--", "echo", "hello"]
    )
    manifest_path = next(run_storage.rglob("run.json"))
    manifest = RunManifest.model_validate_json(manifest_path.read_text())
    assert result.exit_code == 1
    assert manifest.task is not None
    assert manifest.task.parse_status == "invalid"
    assert manifest.analysis_outcome == "failed"
    assert (manifest_path.parent / "task.md").read_bytes() == b"\xff\x00\r\n"


@pytest.mark.parametrize("kind", ["directory", "fifo"])
def test_task_input_requires_a_regular_file(
    tmp_path: Path, run_storage: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    import os

    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "task-input"
    if kind == "directory":
        source.mkdir()
    else:
        os.mkfifo(source)
    # Prove special files are rejected before opening (a FIFO would block).
    original = Path.read_bytes

    def read_bytes(path: Path) -> bytes:
        if path == source:
            pytest.fail("Special task input must not be opened")
        return original(path)

    with patch.object(Path, "read_bytes", read_bytes):
        result = CliRunner().invoke(
            app, ["run", "--task-file", str(source), "--", "echo", "hello"]
        )
    assert result.exit_code == 1
    manifest = RunManifest.model_validate_json(
        next(run_storage.rglob("run.json")).read_text()
    )
    assert manifest.failures[0].stage == "task_read"
    assert manifest.process_outcome == "not_started"
