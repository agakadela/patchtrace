from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pexpect  # type: ignore[import-untyped]

FIXTURE = Path(__file__).parents[1] / "fixtures" / "fake_interactive_agent.py"
REPO_ROOT = Path(__file__).parents[2]
SRC_ROOT = REPO_ROOT / "src"


def test_interactive_run_captures_prompt_response_and_exit_status(
    tmp_path: Path,
) -> None:
    _init_git_repo(tmp_path)

    child = pexpect.spawn(
        sys.executable,
        ["-m", "patchtrace", "run", "--", sys.executable, str(FIXTURE)],
        cwd=str(tmp_path),
        env=_pythonpath_env(),
        encoding="utf-8",
        codec_errors="replace",
        timeout=10,
    )
    try:
        child.expect("fake interactive prompt:")
        child.sendline("Aga typed proof")
        child.expect("fake interactive response: Aga typed proof")
        child.expect("PatchTrace review package written to")
        child.expect("Review the package before deciding next steps.")
        child.expect(pexpect.EOF)
        child.close()
    finally:
        if child.isalive():
            child.terminate(force=True)

    assert child.exitstatus == 0

    run_dir = next((tmp_path / ".patchtrace" / "runs").iterdir())
    manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    transcript = (run_dir / "agent-session.txt").read_text(encoding="utf-8")

    assert manifest["wrapped_command_exit_status"] == 0
    assert manifest["outcome"] == "completed"
    assert "fake interactive prompt:" in transcript
    assert "Aga typed proof" in transcript
    assert "fake interactive response: Aga typed proof" in transcript
    assert "[patchtrace] wrapped command exited with status 0" in transcript


def _pythonpath_env() -> dict[str, str]:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{SRC_ROOT}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else str(SRC_ROOT)
    )
    return env


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
