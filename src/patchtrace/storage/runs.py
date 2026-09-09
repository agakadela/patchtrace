from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from secrets import token_hex

from patchtrace.models.run import RunManifest
from patchtrace.vcs.envelope import GitSessionEnvelope


@dataclass(frozen=True)
class RunPaths:
    run_id: str
    run_dir: Path

    @property
    def manifest_path(self) -> Path:
        return self.run_dir / "run.json"

    @property
    def transcript_path(self) -> Path:
        return self.run_dir / "agent-session.txt"

    @property
    def git_before_path(self) -> Path:
        return self.run_dir / "git-before.txt"

    @property
    def git_after_path(self) -> Path:
        return self.run_dir / "git-after.txt"

    @property
    def changed_files_path(self) -> Path:
        return self.run_dir / "changed-files.txt"

    @property
    def patch_path(self) -> Path:
        return self.run_dir / "patch.diff"

    @property
    def git_session_path(self) -> Path:
        return self.run_dir / "git-session.json"

    @property
    def summary_path(self) -> Path:
        return self.run_dir / "SUMMARY.md"

    @property
    def feedback_path(self) -> Path:
        return self.run_dir / "AGENT_FEEDBACK.md"

    @property
    def verification_brief_path(self) -> Path:
        return self.run_dir / "VERIFICATION_BRIEF.md"

    def relative_artifact_path(self, artifact_path: Path) -> str:
        return artifact_path.relative_to(self.run_dir).as_posix()


def create_run_paths(repository_root: Path) -> RunPaths:
    repository_root = repository_root.resolve()
    repository_id = sha256(os.fsencode(repository_root)).hexdigest()
    configured_state = Path(os.environ.get("XDG_STATE_HOME", ""))
    state_home = (
        configured_state
        if configured_state.is_absolute()
        else Path.home() / ".local" / "state"
    )
    runs_root = (state_home / "patchtrace" / "repos" / repository_id / "runs").resolve()
    if runs_root.is_relative_to(repository_root):
        raise ValueError(
            "PatchTrace run storage must be outside the repository; "
            "set XDG_STATE_HOME to an absolute external directory."
        )
    runs_root.mkdir(mode=0o700, parents=True, exist_ok=True)

    for _ in range(10):
        run_id = _generate_run_id()
        run_dir = runs_root / run_id
        try:
            run_dir.mkdir(mode=0o700)
        except FileExistsError:
            continue
        return RunPaths(run_id=run_id, run_dir=run_dir)

    raise RuntimeError("unable to create a unique PatchTrace run folder")


def write_run_manifest(run_paths: RunPaths, manifest: RunManifest) -> None:
    # Revalidate mutable lifecycle facts and keep the last checkpoint on failure.
    validated = RunManifest.model_validate(manifest.model_dump())
    temporary = run_paths.run_dir / ".run.json.tmp"
    try:
        temporary.write_text(
            validated.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(run_paths.manifest_path)
    finally:
        temporary.unlink(missing_ok=True)


def write_git_session(run_paths: RunPaths, envelope: GitSessionEnvelope) -> None:
    run_paths.git_session_path.write_text(
        json.dumps(asdict(envelope), indent=2) + "\n", encoding="utf-8"
    )


def _generate_run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{timestamp}-{token_hex(4)}"
