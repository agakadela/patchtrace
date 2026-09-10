import json
import os
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from unittest.mock import Mock, patch

import pexpect  # type: ignore[import-untyped]
import pytest
from typer.testing import CliRunner

from patchtrace.cli.app import app
from patchtrace.models.run import RunManifest
from patchtrace.storage.runs import RunPaths


def _init_git_repo(path: Path) -> None:
    for args in (
        ["init"],
        ["config", "user.name", "PatchTrace Test"],
        ["config", "user.email", "patchtrace-test@example.com"],
        ["commit", "--allow-empty", "-m", "initial"],
    ):
        subprocess.run(["git", *args], cwd=path, check=True, capture_output=True)


def fake_codex(path: Path) -> Path:
    executable = path / "codex"
    executable.write_text(
        f"#!{sys.executable}\n"
        "import sys, json, os\nfrom pathlib import Path\n"
        "Path('invocation.json').write_text(json.dumps({'args': sys.argv[1:], 'tty': os.isatty(0)}))\n"
        "if os.environ.get('PATCHTRACE_TEST_INTERACTIVE'):\n"
        "    print('interactive response: ' + input('interactive prompt: '))\n"
        "print('Final answer:\\nNo files changed.')\n"
    )
    executable.chmod(0o755)
    return executable


def test_codex_delivery_binds_saved_task_to_observed_argv(
    tmp_path: Path, run_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    raw = b"\xef\xbb\xbf## Outcome\r\nKeep `echo no` $(touch nope) \xc5\xbc  \r\n## Requirements\r\n1. Reply only.  "
    (tmp_path / "task.md").write_bytes(raw)
    executable = fake_codex(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--codex",
            "--task-file",
            "task.md",
            "--",
            str(executable),
            "--no-alt-screen",
        ],
    )
    assert result.exit_code == 0, result.output
    manifest_path = next(run_storage.rglob("run.json"))
    manifest = RunManifest.model_validate_json(manifest_path.read_text())
    observed = json.loads((tmp_path / "invocation.json").read_text())
    assert observed == {
        "args": ["--no-alt-screen", "--", raw.decode("utf-8")],
        "tty": True,
    }
    assert manifest.task_delivery is not None
    assert manifest.task_delivery.confirmation == "process_started"
    assert manifest.task_delivery.attempted
    assert manifest.task_delivery.prompt_sha256 == sha256(raw).hexdigest()
    assert (manifest_path.parent / "task.md").read_bytes() == raw
    assert not (tmp_path / "nope").exists()
    for name in ("SUMMARY.md", "AGENT_FEEDBACK.md", "VERIFICATION_BRIEF.md"):
        report = (manifest_path.parent / name).read_text()
        assert "process_started" in report
        assert "receipt and understanding are unobservable" in report


@pytest.mark.parametrize("failure", ["start", "prepare"])
def test_delivery_failures_are_preserved_before_analysis(
    tmp_path: Path, run_storage: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "task.md").write_text(
        "## Outcome\nReply.\n## Requirements\n1. Reply only.\n"
    )
    command = (
        [str(tmp_path / "missing-codex")]
        if failure == "start"
        else [str(fake_codex(tmp_path)), "exec"]
    )
    result = CliRunner().invoke(
        app, ["run", "--codex", "--task-file", "task.md", "--", *command]
    )
    assert result.exit_code == 1, result.output
    manifest = RunManifest.model_validate_json(
        next(run_storage.rglob("run.json")).read_text()
    )
    assert manifest.task_delivery is not None
    assert manifest.task_delivery.confirmation == "failed"
    assert manifest.task_delivery.attempted == (failure == "start")
    assert manifest.process_outcome == "not_started"
    assert manifest.analysis_outcome == "not_run"
    assert manifest.failures[0].stage == (
        "task_delivery_start" if failure == "start" else "task_delivery_prepare"
    )
    assert manifest.package_outcome == "partial"


def test_generic_command_never_receives_task_or_codex_interpretation(
    tmp_path: Path, run_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "task.md").write_text(
        "## Outcome\nReply.\n## Requirements\n1. Reply only.\n"
    )
    executable = fake_codex(tmp_path)
    result = CliRunner().invoke(
        app, ["run", "--task-file", "task.md", "--", str(executable)]
    )
    assert result.exit_code == 0, result.output
    manifest = RunManifest.model_validate_json(
        next(run_storage.rglob("run.json")).read_text()
    )
    assert json.loads((tmp_path / "invocation.json").read_text())["args"] == []
    assert manifest.task_delivery is not None
    assert manifest.task_delivery.mode == "retained_only"
    assert manifest.task_delivery.confirmation == "unverified"
    assert manifest.analysis_outcome == "degraded"


def test_started_checkpoint_failure_closes_child_and_preserves_launch(
    tmp_path: Path, run_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from patchtrace.storage.runs import write_run_manifest

    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "task.md").write_text(
        "## Outcome\nReply.\n## Requirements\n1. Reply only.\n"
    )
    child = Mock(exitstatus=None, signalstatus=None)
    failed = False

    def write(paths: RunPaths, manifest: RunManifest) -> None:
        nonlocal failed
        if (
            manifest.task_delivery
            and manifest.task_delivery.confirmation == "process_started"
            and not failed
        ):
            failed = True
            raise OSError("checkpoint disk failure")
        write_run_manifest(paths, manifest)

    with (
        patch("patchtrace.session.recorder.pexpect.spawn", return_value=child),
        patch("patchtrace.cli.app.write_run_manifest", side_effect=write),
    ):
        result = CliRunner().invoke(
            app, ["run", "--codex", "--task-file", "task.md", "--", "codex"]
        )
    assert result.exit_code == 1
    child.close.assert_called_once_with(force=True)
    manifest = RunManifest.model_validate_json(
        next(run_storage.rglob("run.json")).read_text()
    )
    assert manifest.process_outcome == "unknown"
    assert (
        manifest.task_delivery
        and manifest.task_delivery.confirmation == "process_started"
    )
    assert manifest.failures[0].stage == "process_checkpoint_write"
    assert manifest.package_outcome == "failed"


def test_transcript_open_failure_records_no_delivery_attempt(
    tmp_path: Path, run_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from typing import IO, Any

    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "task.md").write_text(
        "## Outcome\nReply.\n## Requirements\n1. Reply only.\n"
    )
    original = Path.open

    def open_file(path: Path, mode: str = "r", *args: Any, **kwargs: Any) -> IO[Any]:
        if path.name == "agent-session.txt" and mode == "w":
            raise OSError("transcript unavailable")
        return original(path, mode, *args, **kwargs)

    with patch.object(Path, "open", open_file):
        result = CliRunner().invoke(
            app, ["run", "--codex", "--task-file", "task.md", "--", "codex"]
        )
    assert result.exit_code == 1
    manifest = RunManifest.model_validate_json(
        next(run_storage.rglob("run.json")).read_text()
    )
    assert manifest.task_delivery and not manifest.task_delivery.attempted
    assert manifest.task_delivery.confirmation == "failed"
    assert manifest.process_outcome == "not_started"


def test_task_delivery_keeps_stdin_available_for_interactive_followup(
    tmp_path: Path, run_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_git_repo(tmp_path)
    executable = fake_codex(tmp_path)
    raw = b"## Outcome\nReply.\n## Requirements\n1. Keep interactive input.\n"
    (tmp_path / "task.md").write_bytes(raw)
    monkeypatch.setenv("PATCHTRACE_TEST_INTERACTIVE", "1")
    monkeypatch.setenv("PYTHONPATH", str(Path(__file__).parents[2] / "src"))
    child = pexpect.spawn(
        sys.executable,
        [
            "-m",
            "patchtrace",
            "run",
            "--codex",
            "--task-file",
            "task.md",
            "--",
            str(executable),
        ],
        cwd=str(tmp_path),
        env=os.environ.copy(),
        encoding="utf-8",
        timeout=15,
    )
    try:
        child.expect("interactive prompt:")
        child.sendline("Aga followup")
        child.expect("interactive response: Aga followup")
        child.expect("PatchTrace review package written to")
        child.expect(pexpect.EOF)
        child.close()
    finally:
        child.close(force=True)
    assert child.exitstatus == 0
    observed = json.loads((tmp_path / "invocation.json").read_text())
    assert observed["args"] == ["--", raw.decode()]
    manifest_path = next(run_storage.rglob("run.json"))
    assert "Aga followup" in (manifest_path.parent / "agent-session.txt").read_text()
