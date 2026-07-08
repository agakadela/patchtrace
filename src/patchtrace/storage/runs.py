from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from secrets import token_hex

from patchtrace.models.run import RunManifest

RUNS_ROOT = Path(".patchtrace") / "runs"


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
    def summary_path(self) -> Path:
        return self.run_dir / "SUMMARY.md"

    @property
    def feedback_path(self) -> Path:
        return self.run_dir / "AGENT_FEEDBACK.md"

    def relative_artifact_path(self, artifact_path: Path) -> str:
        return artifact_path.relative_to(self.run_dir).as_posix()


def create_run_paths(workspace: Path) -> RunPaths:
    runs_root = workspace / RUNS_ROOT
    runs_root.mkdir(parents=True, exist_ok=True)

    for _ in range(10):
        run_id = _generate_run_id()
        run_dir = runs_root / run_id
        try:
            run_dir.mkdir()
        except FileExistsError:
            continue
        return RunPaths(run_id=run_id, run_dir=run_dir)

    raise RuntimeError("unable to create a unique PatchTrace run folder")


def write_run_manifest(run_paths: RunPaths, manifest: RunManifest) -> None:
    run_paths.manifest_path.write_text(
        manifest.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )


def _generate_run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{timestamp}-{token_hex(4)}"
