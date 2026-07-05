from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from patchtrace.vcs.git import git_output


@dataclass(frozen=True)
class GitEvidenceSnapshot:
    after_status: str
    changed_files: list[str]
    patch: str
    patch_material_present: bool


def capture_git_status(cwd: Path) -> str:
    status = git_output(cwd, "status", "--porcelain=v1")
    return _without_internal_artifacts(status)


def capture_git_evidence(cwd: Path) -> GitEvidenceSnapshot:
    after_status = capture_git_status(cwd)
    patch = _combined_patch(cwd)
    return GitEvidenceSnapshot(
        after_status=after_status,
        changed_files=_changed_files_from_status(after_status),
        patch=patch,
        patch_material_present=bool(patch.strip()),
    )


def _combined_patch(cwd: Path) -> str:
    unstaged = git_output(cwd, "diff", "--binary")
    staged = git_output(cwd, "diff", "--cached", "--binary")
    return "\n".join(part.rstrip("\n") for part in (staged, unstaged) if part)


def _without_internal_artifacts(status: str) -> str:
    kept_lines = [
        line for line in status.splitlines() if not _is_internal_artifact(line[3:])
    ]
    return "\n".join(kept_lines) + ("\n" if kept_lines else "")


def _changed_files_from_status(status: str) -> list[str]:
    changed_files: list[str] = []
    for line in status.splitlines():
        path = line[3:]
        if " -> " in path:
            path = path.rsplit(" -> ", maxsplit=1)[1]
        if not _is_internal_artifact(path):
            changed_files.append(path)
    return changed_files


def _is_internal_artifact(path: str) -> bool:
    return path == ".patchtrace" or path.startswith(".patchtrace/")
