from __future__ import annotations

import base64
import os
import stat
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Literal

from patchtrace.vcs.git import GitCommandError, git_output

# All paths are repository-root relative. Exclude legacy run storage even if tracked.
EVIDENCE_PATHS = (".", ":(top,exclude).patchtrace")
DIFF_OPTIONS = (
    "--binary",
    "--no-ext-diff",
    "--no-textconv",
    "--no-renames",
    "--no-color",
)
MAX_UNTRACKED_BYTES = 1024 * 1024
MAX_UNTRACKED_TOTAL_BYTES = 8 * MAX_UNTRACKED_BYTES
MAX_COMMITS = 100


@dataclass(frozen=True)
class GitPathFact:
    status: str
    path: str


@dataclass(frozen=True)
class UntrackedEvidence:
    path: str
    content_base64: str | None = None
    sha256: str | None = None
    limitation: str | None = None


@dataclass(frozen=True)
class GitBoundary:
    head: str | None
    dirty: bool
    paths: list[GitPathFact]
    staged_patch: str
    unstaged_patch: str
    untracked: list[UntrackedEvidence]


@dataclass(frozen=True)
class GitCommitFact:
    head: str
    parent: str
    patch: str


@dataclass(frozen=True)
class GitHistory:
    kind: Literal["unchanged", "linear", "unsupported"]
    commits: list[GitCommitFact] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass
class GitSessionEnvelope:
    repository_root: str
    schema_version: int = 1
    before: GitBoundary | None = None
    after: GitBoundary | None = None
    history: GitHistory | None = None
    capture_status: Literal["started", "complete", "failed"] = "started"
    failed_stage: str | None = None
    error: str | None = None
    recovery: str | None = None
    limitations: list[str] = field(
        default_factory=lambda: [
            "Boundary observations are sequential, not atomic; concurrent edits and "
            "changes reverted between boundaries are not observable.",
            "Facts do not prove authorship or separate pre-existing dirty bytes from "
            "session edits or partial commits on the same path.",
            "Sparse checkouts, submodules, nested repositories, ignored files and "
            "non-UTF-8 Git output are unsupported; .patchtrace/ is excluded.",
        ]
    )


def _reject_active_content_filters(repository_root: Path) -> None:
    keys = git_output(repository_root, "config", "--name-only", "--list").splitlines()
    filters = {
        key[len("filter.") :].rsplit(".", 1)[0]
        for key in keys
        if key.startswith("filter.") and key.endswith((".clean", ".process"))
    }
    if not filters:
        return
    tracked = git_output(repository_root, "ls-files", "-z", "--", *EVIDENCE_PATHS)
    attributes = git_output(
        repository_root, "check-attr", "-z", "--stdin", "filter", input_text=tracked
    ).split("\0")
    if any(value in filters for value in attributes[2::3]):
        raise GitCommandError(
            ["git", "check-attr", "filter"],
            "Active clean/process filters are unsupported: "
            "capture will not execute them. Use a checkout "
            "without external content filters for capture.",
        )


def capture_boundary(repository_root: Path) -> GitBoundary:
    _reject_active_content_filters(repository_root)
    # --default HEAD produces no result on an unborn branch, while command
    # failures still propagate instead of being mistaken for an unborn HEAD.
    head = (
        git_output(
            repository_root, "rev-parse", "--revs-only", "--default", "HEAD"
        ).strip()
        or None
    )
    status = git_output(
        repository_root,
        "status",
        "--porcelain=v1",
        "-z",
        "--no-renames",
        "--untracked-files=all",
        "--ignore-submodules=all",
        "--",
        *EVIDENCE_PATHS,
    )
    paths = parse_status(status)
    return GitBoundary(
        head=head,
        dirty=bool(paths),
        paths=paths,
        staged_patch=capture_patch(repository_root, "--cached"),
        unstaged_patch=capture_patch(repository_root),
        untracked=_capture_untracked(repository_root, paths),
    )


def parse_status(status: str) -> list[GitPathFact]:
    """Parse porcelain v1 -z with rename detection explicitly disabled."""
    return [
        GitPathFact(status=entry[:2], path=entry[3:])
        for entry in status.split("\0")
        if entry
    ]


def capture_patch(repository_root: Path, *revisions: str) -> str:
    return git_output(
        repository_root,
        "diff",
        *DIFF_OPTIONS,
        "--ignore-submodules=all",
        *revisions,
        "--",
        *EVIDENCE_PATHS,
    )


def _capture_untracked(root: Path, paths: list[GitPathFact]) -> list[UntrackedEvidence]:
    evidence: list[UntrackedEvidence] = []
    remaining = MAX_UNTRACKED_TOTAL_BYTES
    for fact in paths:
        if fact.status != "??":
            continue
        path = root / fact.path
        # Never follow an untracked symlink (or a replaced parent) outside root.
        if path.is_symlink() or path.resolve() != path:
            evidence.append(
                UntrackedEvidence(
                    fact.path, limitation="Symlink content is not captured."
                )
            )
            continue
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                evidence.append(
                    UntrackedEvidence(
                        fact.path,
                        limitation="Only regular untracked files are captured.",
                    )
                )
                continue
            data = source.read(min(MAX_UNTRACKED_BYTES, remaining) + 1)
        if len(data) > min(MAX_UNTRACKED_BYTES, remaining):
            evidence.append(
                UntrackedEvidence(
                    fact.path,
                    limitation="Content omitted: 1 MiB per-file or 8 MiB "
                    "per-boundary untracked byte limit exceeded.",
                )
            )
            continue
        remaining -= len(data)
        evidence.append(
            UntrackedEvidence(
                fact.path,
                base64.b64encode(data).decode("ascii"),
                sha256(data).hexdigest(),
            )
        )
    return evidence


def capture_history(root: Path, before: GitBoundary, after: GitBoundary) -> GitHistory:
    if before.head is None or after.head is None:
        return GitHistory(
            "unsupported",
            limitations=["An unborn HEAD prevents a before/after commit range."],
        )
    if before.head == after.head:
        return GitHistory("unchanged")
    rows = git_output(
        root,
        "rev-list",
        "--reverse",
        "--topo-order",
        "--parents",
        f"--max-count={MAX_COMMITS + 1}",
        f"{before.head}..{after.head}",
        "--",
    ).splitlines()
    parent = before.head
    chain: list[tuple[str, str]] = []
    for row in rows:
        parts = row.split()
        if len(parts) != 2 or parts[1] != parent:
            break
        chain.append((parts[0], parts[1]))
        parent = parts[0]
    if (
        not rows
        or len(rows) > MAX_COMMITS
        or len(chain) != len(rows)
        or parent != after.head
    ):
        return GitHistory(
            "unsupported",
            limitations=[
                "HEAD range is not a direct single-parent chain of at most 100 commits; "
                "merges, rewrites, backwards movement and truncated history are not reconstructed."
            ],
        )
    return GitHistory(
        "linear",
        commits=[
            GitCommitFact(head, parent, capture_patch(root, parent, head))
            for head, parent in chain
        ],
    )
