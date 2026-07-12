from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from patchtrace.analysis.analyzer import analyze_run
from patchtrace.cli.app import app

runner = CliRunner()
FIXTURE = Path(__file__).parents[1] / "fixtures" / "fake_agent.py"
REQUIRED_ARTIFACTS = [
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


def test_fake_run_creates_run_folder_manifest_and_transcript(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with patch("patchtrace.cli.app.analyze_run", wraps=analyze_run) as analyze_mock:
        result = runner.invoke(app, ["run", "--", sys.executable, str(FIXTURE)])

    assert result.exit_code == 0
    assert analyze_mock.call_count == 1

    run_dirs = list((Path(".patchtrace") / "runs").iterdir())
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]

    manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    transcript = (run_dir / "agent-session.txt").read_text(encoding="utf-8")
    summary = (run_dir / "SUMMARY.md").read_text(encoding="utf-8")
    feedback = (run_dir / "AGENT_FEEDBACK.md").read_text(encoding="utf-8")
    verification_brief = (run_dir / "VERIFICATION_BRIEF.md").read_text(encoding="utf-8")

    assert f"PatchTrace review package written to {run_dir}" in result.output
    assert "Review the package before deciding next steps." in result.output
    assert "accepted" not in result.output.lower()
    assert "correct" not in result.output.lower()
    assert "safe" not in result.output.lower()
    assert "production verified" not in result.output.lower()
    assert manifest["run_id"] == run_dir.name
    assert manifest["command"] == [sys.executable, str(FIXTURE)]
    assert manifest["trigger_source"] == "manual_cli"
    assert manifest["wrapped_command_exit_status"] == 0
    assert manifest["outcome"] == "completed"
    assert manifest["artifact_paths"] == REQUIRED_ARTIFACTS
    _assert_required_artifacts_exist(run_dir)
    assert manifest["git_evidence"]["patch_material_present"] is False
    assert "started_at" in manifest
    assert "ended_at" in manifest
    assert "fake agent says hello" in transcript
    assert f"- Run ID: `{run_dir.name}`" in summary
    assert "- Exit status: `0`" in summary
    assert "- `SUMMARY.md`" in summary
    assert summary.index("## Quick Decision") < summary.index("## Run")
    assert "- Verdict: No captured file changes require review." in summary
    assert (
        "- Most important gap: PatchTrace cannot determine whether the absence "
        "of changes was intended."
    ) in summary
    assert (
        "- Recommended next action: Confirm that no change was intended; otherwise "
        "capture the missing change."
    ) in summary
    assert "# PatchTrace Agent Feedback" in feedback
    assert "Paste this back to the agent:" in feedback
    assert "- Verdict: No captured file changes require review." in feedback
    assert (
        "- Highest-priority gap: PatchTrace cannot determine whether the absence "
        "of changes was intended." in feedback
    )
    assert (
        "- Recommended next action: Confirm that no change was intended; otherwise "
        "capture the missing change." in feedback
    )
    assert "- None beyond the recommended next action above." in feedback
    assert "- Exit status: `0`" in feedback
    assert "- Diff material: `empty`" in feedback
    assert "No obvious command or test signals were detected." in feedback
    assert "Confirm that no change was intended" in feedback
    assert "- `AGENT_FEEDBACK.md`" in feedback
    assert "success" not in feedback.lower()
    assert "# PatchTrace Verification Brief" in verification_brief
    assert f"- Run ID: `{run_dir.name}`" in verification_brief
    assert "- Exit status: `0`" in verification_brief
    assert "- Diff material: `empty`" in verification_brief
    assert "- Command/test signals: `missing`" in verification_brief
    assert "- `VERIFICATION_BRIEF.md`" in verification_brief
    assert "No bounded explicit final claims were extracted." in verification_brief
    assert "- Claim material: `ambiguous`." in verification_brief
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

    assert f"PatchTrace review package written to {run_dir}" in result.output
    assert "Review the package before deciding next steps." in result.output
    assert manifest["wrapped_command_exit_status"] == 7
    assert manifest["outcome"] == "wrapped_command_failed"
    assert manifest["artifact_paths"] == REQUIRED_ARTIFACTS
    _assert_required_artifacts_exist(run_dir)
    assert "success" not in manifest
    assert "fake agent exiting with 7" in transcript
    assert "- Exit status: `7`" in summary
    assert "- Verdict: Review required: the wrapped command failed." in summary
    assert "- Most important gap: Wrapped command exited with status 7." in summary
    assert (
        "- Recommended next action: Address the wrapped command failure, rerun it, "
        "and review the new evidence."
    ) in summary
    assert "success" not in summary.lower()
    assert "- Exit status: `7`" in feedback
    assert "Wrapped command exited with status 7." in feedback
    assert "Address the wrapped command failure, rerun it" in feedback
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


def _assert_required_artifacts_exist(run_dir: Path) -> None:
    for artifact_path in REQUIRED_ARTIFACTS:
        assert (run_dir / artifact_path).is_file()


def _git(path: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
