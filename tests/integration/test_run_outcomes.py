import json
import subprocess
import sys
from pathlib import Path
from typing import IO, Any
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from patchtrace.analysis.analyzer import analyze_run
from patchtrace.cli.app import app
from patchtrace.models.run import RunManifest

REPORTS = ("SUMMARY.md", "AGENT_FEEDBACK.md", "VERIFICATION_BRIEF.md")


@pytest.mark.parametrize("exit_status", [0, 7])
@pytest.mark.parametrize(
    "final_output",
    [
        "Final answer:\nDone.",
        "unmarked output",
        "Final answer:\nOne\nFinal answer:\nTwo",
    ],
)
def test_command_and_analysis_outcomes_are_independent(
    tmp_path: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
    exit_status: int,
    final_output: str,
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--",
            sys.executable,
            "-c",
            f"print({final_output!r}); raise SystemExit({exit_status})",
        ],
    )
    assert result.exit_code == exit_status
    path = next(run_storage.rglob("run.json"))
    manifest = RunManifest.model_validate_json(path.read_text())
    assert manifest.process_outcome == ("completed" if exit_status == 0 else "failed")
    analysis = "completed" if final_output == "Final answer:\nDone." else "degraded"
    assert manifest.analysis_outcome == analysis
    assert manifest.package_outcome == "complete"
    for name in REPORTS:
        report = (path.parent / name).read_text()
        assert f"- Process outcome: `{manifest.process_outcome}`" in report
        assert f"- Analysis outcome: `{analysis}`" in report
        assert "- Package outcome: see `run.json`" in report
        assert "- Outcome:" not in report


@pytest.mark.parametrize("missing", [False, True])
def test_analysis_exception_or_missing_transcript_preserves_process_result(
    tmp_path: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
    missing: bool,
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def analyze(manifest: RunManifest, *, run_dir: Path) -> object:
        if missing:
            (run_dir / "agent-session.txt").unlink()
            return analyze_run(manifest, run_dir=run_dir)
        raise ValueError("injected analysis failure")

    with patch("patchtrace.cli.app.analyze_run", side_effect=analyze):
        result = CliRunner().invoke(
            app, ["run", "--", sys.executable, "-c", "print('Final answer:\\nDone.')"]
        )
    path = next(run_storage.rglob("run.json"))
    manifest = RunManifest.model_validate_json(path.read_text())
    assert manifest.process_outcome == "completed"
    assert manifest.wrapped_command_exit_status == 0
    assert manifest.analysis_outcome == ("degraded" if missing else "failed")
    assert manifest.package_outcome != "complete"
    assert result.exit_code == 1
    assert "review package written" not in result.output
    assert str(path.parent) in result.output


@pytest.mark.parametrize(
    "artifact",
    [
        "git-before.txt",
        "agent-session.txt",
        "git-after.txt",
        "changed-files.txt",
        "patch.diff",
        "git-session.json",
        *REPORTS,
        "run.json",
    ],
)
def test_injected_artifact_write_failure_never_claims_complete_package(
    tmp_path: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
    artifact: str,
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    original_open = Path.open

    def fail_open(
        path: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]:
        # The manifest is written to a sibling temporary file before replacement.
        if (
            path.name in (artifact, f".{artifact}.tmp")
            and "w" in mode
            and path.is_relative_to(run_storage)
        ):
            raise OSError(f"injected write failure: {artifact}")
        return original_open(path, mode, buffering, encoding, errors, newline)

    with patch.object(Path, "open", fail_open):
        result = CliRunner().invoke(
            app, ["run", "--", sys.executable, "-c", "print('Final answer:\\nDone.')"]
        )
    assert result.exit_code == 1
    assert "review package written" not in result.output
    assert "injected write failure" in result.output
    paths = list(run_storage.rglob("run.json"))
    if artifact == "run.json":
        assert not paths
        assert "Unable to preserve run manifest" in result.output
    else:
        manifest = RunManifest.model_validate_json(paths[0].read_text())
        assert manifest.package_outcome == "failed"
        assert manifest.failures
        for name in REPORTS:
            report = paths[0].parent / name
            if report.exists():
                assert "Package outcome: `complete`" not in report.read_text()


def test_missing_executable_preserves_not_started_outcome(
    tmp_path: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app, ["run", "--", "/patchtrace-test-no-such-executable"]
    )
    assert result.exit_code == 1
    manifest = json.loads(next(run_storage.rglob("run.json")).read_text())
    assert manifest["process_outcome"] == "not_started"
    assert manifest["wrapped_command_exit_status"] is None
    assert manifest["analysis_outcome"] == "not_run"
    assert manifest["package_outcome"] == "partial"


def _init_git_repo(path: Path) -> None:
    for args in (
        ["init"],
        ["config", "user.name", "PatchTrace Test"],
        ["config", "user.email", "patchtrace-test@example.com"],
        ["commit", "--allow-empty", "-m", "initial"],
    ):
        subprocess.run(["git", *args], cwd=path, check=True, capture_output=True)


@pytest.mark.parametrize("persistent", [False, True])
def test_final_manifest_replace_failure_keeps_an_incomplete_checkpoint(
    tmp_path: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
    persistent: bool,
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    original_replace = Path.replace
    failed = False

    def fail_replace(path: Path, target: Path) -> Path:
        nonlocal failed
        if path.name == ".run.json.tmp":
            candidate = json.loads(path.read_text())
            if candidate["package_outcome"] == "complete" or (failed and persistent):
                failed = True
                raise OSError("injected manifest replacement failure")
        return original_replace(path, target)

    with patch.object(Path, "replace", fail_replace):
        result = CliRunner().invoke(
            app, ["run", "--", sys.executable, "-c", "print('Final answer:\\nDone.')"]
        )
    assert failed
    assert result.exit_code == 1
    assert "review package written" not in result.output
    path = next(run_storage.rglob("run.json"))
    manifest = RunManifest.model_validate_json(path.read_text())
    assert manifest.process_outcome == "completed"
    assert manifest.analysis_outcome == "completed"
    assert manifest.package_outcome == ("partial" if persistent else "failed")
    assert not (path.parent / ".run.json.tmp").exists()
    assert ("Unable to preserve run manifest" in result.output) == persistent
    assert all((path.parent / name).is_file() for name in REPORTS)


@pytest.mark.parametrize("exit_status", [0, 7])
def test_analysis_failure_takes_cli_precedence_without_losing_child_status(
    tmp_path: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
    exit_status: int,
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    with patch(
        "patchtrace.cli.app.analyze_run", side_effect=RuntimeError("analyzer failed")
    ):
        result = CliRunner().invoke(
            app, ["run", "--", sys.executable, "-c", f"raise SystemExit({exit_status})"]
        )
    manifest = RunManifest.model_validate_json(
        next(run_storage.rglob("run.json")).read_text()
    )
    assert result.exit_code == 1
    assert manifest.wrapped_command_exit_status == exit_status
    assert manifest.process_outcome == ("completed" if exit_status == 0 else "failed")
    assert manifest.analysis_outcome == "failed"
    assert manifest.package_outcome == "partial"
    assert manifest.failures[0].stage == "analysis"


def test_prelaunch_checkpoint_failure_records_that_command_never_started(
    tmp_path: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    original_replace = Path.replace

    def fail_prelaunch(path: Path, target: Path) -> Path:
        if path.name == ".run.json.tmp":
            candidate = json.loads(path.read_text())
            if candidate["process_outcome"] == "unknown":
                raise OSError("prelaunch checkpoint failed")
        return original_replace(path, target)

    with patch.object(Path, "replace", fail_prelaunch):
        result = CliRunner().invoke(
            app,
            [
                "run",
                "--",
                sys.executable,
                "-c",
                "from pathlib import Path; Path('command-ran').touch()",
            ],
        )
    manifest = RunManifest.model_validate_json(
        next(run_storage.rglob("run.json")).read_text()
    )
    assert result.exit_code == 1
    assert not (tmp_path / "command-ran").exists()
    assert manifest.process_outcome == "not_started"
    assert manifest.wrapped_command_exit_status is None
    assert manifest.package_outcome == "failed"


def test_initial_status_read_failure_is_capture_failure_not_write_failure(
    tmp_path: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from patchtrace.vcs.git import GitCommandError

    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    with patch(
        "patchtrace.cli.app.capture_git_status",
        side_effect=GitCommandError(["git", "status"], "index unreadable"),
    ):
        result = CliRunner().invoke(
            app, ["run", "--", sys.executable, "-c", "print('not started')"]
        )
    path = next(run_storage.rglob("run.json"))
    manifest = RunManifest.model_validate_json(path.read_text())
    assert result.exit_code == 1
    assert manifest.process_outcome == "not_started"
    assert manifest.analysis_outcome == "not_run"
    assert manifest.package_outcome == "partial"
    assert manifest.failures[0].stage == "capture_before"
    envelope = json.loads((path.parent / "git-session.json").read_text())
    assert envelope["failed_stage"] == "before"
    assert envelope["before"] is not None
