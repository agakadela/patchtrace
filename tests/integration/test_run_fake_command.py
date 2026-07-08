from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from patchtrace.cli.app import app

runner = CliRunner()
FIXTURE = Path(__file__).parents[1] / "fixtures" / "fake_agent.py"


def test_fake_run_creates_run_folder_manifest_and_transcript(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["run", "--", sys.executable, str(FIXTURE)])

    assert result.exit_code == 0

    run_dirs = list((Path(".patchtrace") / "runs").iterdir())
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]

    manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    transcript = (run_dir / "agent-session.txt").read_text(encoding="utf-8")
    summary = (run_dir / "SUMMARY.md").read_text(encoding="utf-8")
    feedback = (run_dir / "AGENT_FEEDBACK.md").read_text(encoding="utf-8")
    verification_brief = (run_dir / "VERIFICATION_BRIEF.md").read_text(encoding="utf-8")

    assert manifest["run_id"] == run_dir.name
    assert manifest["command"] == [sys.executable, str(FIXTURE)]
    assert manifest["trigger_source"] == "manual_cli"
    assert manifest["wrapped_command_exit_status"] == 0
    assert manifest["outcome"] == "completed"
    assert manifest["artifact_paths"] == [
        "run.json",
        "agent-session.txt",
        "git-before.txt",
        "git-after.txt",
        "changed-files.txt",
        "patch.diff",
        "SUMMARY.md",
        "AGENT_FEEDBACK.md",
        "VERIFICATION_BRIEF.md",
    ]
    assert manifest["git_evidence"]["patch_material_present"] is False
    assert "started_at" in manifest
    assert "ended_at" in manifest
    assert "fake agent says hello" in transcript
    assert f"- Run ID: `{run_dir.name}`" in summary
    assert "- Exit status: `0`" in summary
    assert "- `SUMMARY.md`" in summary
    assert "- Diff material: `empty`" in summary
    assert "No obvious command or test signals were detected." in summary
    assert "PatchTrace has not verified correctness" in summary
    assert "# PatchTrace Agent Feedback" in feedback
    assert "Paste this back to the agent:" in feedback
    assert "- Exit status: `0`" in feedback
    assert "- Diff material: `empty`" in feedback
    assert "No obvious command or test signals were detected." in feedback
    assert "Run the relevant tests and paste the exact command output." in feedback
    assert "- `AGENT_FEEDBACK.md`" in feedback
    assert "success" not in feedback.lower()
    assert "# PatchTrace Verification Brief" in verification_brief
    assert f"- Run ID: `{run_dir.name}`" in verification_brief
    assert "- Exit status: `0`" in verification_brief
    assert "- Diff material: `empty`" in verification_brief
    assert "- Command/test signals: `missing`" in verification_brief
    assert "- `VERIFICATION_BRIEF.md`" in verification_brief
    assert (
        "Phase 3 does not perform full claim-vs-diff matching or prove correctness."
        in verification_brief
    )
    assert "success" not in verification_brief.lower()


def test_nonzero_fake_run_records_exit_without_claiming_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["run", "--", sys.executable, str(FIXTURE), "--exit-code", "7"],
    )

    assert result.exit_code == 7

    run_dir = next((Path(".patchtrace") / "runs").iterdir())
    manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    transcript = (run_dir / "agent-session.txt").read_text(encoding="utf-8")
    summary = (run_dir / "SUMMARY.md").read_text(encoding="utf-8")
    feedback = (run_dir / "AGENT_FEEDBACK.md").read_text(encoding="utf-8")
    verification_brief = (run_dir / "VERIFICATION_BRIEF.md").read_text(encoding="utf-8")

    assert manifest["wrapped_command_exit_status"] == 7
    assert manifest["outcome"] == "wrapped_command_failed"
    assert "SUMMARY.md" in manifest["artifact_paths"]
    assert "AGENT_FEEDBACK.md" in manifest["artifact_paths"]
    assert "VERIFICATION_BRIEF.md" in manifest["artifact_paths"]
    assert "success" not in manifest
    assert "fake agent exiting with 7" in transcript
    assert "- Exit status: `7`" in summary
    assert "success" not in summary.lower()
    assert "- Exit status: `7`" in feedback
    assert "Wrapped command exited with status 7." in feedback
    assert "Address the wrapped command failure and rerun it." in feedback
    assert "success" not in feedback.lower()
    assert "- Exit status: `7`" in verification_brief
    assert "- Wrapped command: `non-zero exit 7`" in verification_brief
    assert "Wrapped command exited with status 7." in verification_brief
    assert "success" not in verification_brief.lower()


def _init_git_repo(path: Path) -> None:
    _git(path, "init")
    _git(path, "config", "user.name", "PatchTrace Test")
    _git(path, "config", "user.email", "patchtrace-test@example.com")
    (path / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    _git(path, "add", "tracked.txt")
    _git(path, "commit", "-m", "initial")


def _git(path: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
