from __future__ import annotations

import codecs
import re
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from patchtrace.models.report import (
    EvidenceReference,
    GitAttribution,
    GitAttributionClass,
    GitAttributionItem,
    GitMaterial,
)
from patchtrace.models.run import RunManifest
from patchtrace.vcs.envelope import GitBoundary, GitSessionEnvelope

_ENVELOPE = TypeAdapter(GitSessionEnvelope)
_CEILING = "Session attribution describes boundary observations, not agent or byte-level authorship."
_SAME_PATH = (
    "Initial dirty material and later work on the same path cannot be separated."
)


def load_git_attribution(manifest: RunManifest, run_dir: Path) -> GitAttribution:
    artifact = (
        manifest.git_evidence.session_envelope_path if manifest.git_evidence else None
    )
    if artifact is None:
        return GitAttribution(
            limitations=[
                _CEILING,
                "No T1 Git session envelope is linked; rerun capture to establish attribution.",
            ]
        )
    try:
        # Reuse the capture schema instead of maintaining a parallel input model.
        envelope = _ENVELOPE.validate_json(
            (run_dir / artifact).read_bytes(), strict=True
        )
        if envelope.schema_version != 1:
            raise ValueError("Unsupported Git session envelope version")
        return _attribute(envelope, artifact)
    except (OSError, ValidationError, ValueError) as error:
        return GitAttribution(
            limitations=[
                _CEILING,
                f"Git session envelope is unavailable or invalid ({type(error).__name__}); inspect {artifact} and rerun capture.",
            ]
        )


def _reference(artifact: str, locator: str) -> EvidenceReference:
    return EvidenceReference(
        artifact_path=artifact,
        locator=locator,
        description="Captured Git session facts; no authorship inference.",
    )


def _item(
    artifact: str,
    material: GitMaterial,
    path: str | None,
    attribution: GitAttributionClass,
    locators: list[str],
    limitations: list[str],
    commit_head: str | None = None,
) -> GitAttributionItem:
    return GitAttributionItem(
        material=material,
        path=path,
        attribution=attribution,
        evidence_references=[_reference(artifact, locator) for locator in locators],
        limitations=limitations,
        commit_head=commit_head,
    )


def _patches(text: str) -> dict[str, str]:
    """Read capture's no-renames patches with explicitly recorded a/b prefixes.

    Git quotes unusual paths with C escapes (including octal UTF-8 bytes).
    Source: https://git-scm.com/docs/diff-format#_generating_patch_text_with_p
    """
    headers = list(re.finditer(r"^diff --git (.+)$", text, re.MULTILINE))
    if text and (not headers or headers[0].start() != 0):
        raise ValueError("Unsupported patch format")
    patches: dict[str, str] = {}
    for index, header in enumerate(headers):
        names = header.group(1)
        # Rename detection is off: both encoded names have equal length.
        middle = len(names) // 2
        old, new = names[:middle], names[middle + 1 :]
        if names[middle : middle + 1] != " ":
            raise ValueError("Unsupported patch header")
        if old.startswith('"') and old.endswith('"'):
            old = codecs.escape_decode(old[1:-1].encode("utf-8"))[0].decode("utf-8")
        if new.startswith('"') and new.endswith('"'):
            new = codecs.escape_decode(new[1:-1].encode("utf-8"))[0].decode("utf-8")
        if not old.startswith("a/") or not new.startswith("b/") or old[2:] != new[2:]:
            raise ValueError("Unsupported patch paths")
        path = old[2:]
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        # A type change (e.g. regular file to symlink) emits two blocks.
        patches[path] = patches.get(path, "") + text[header.start() : end]
    return patches


def _path_limits(boundary: GitBoundary, path: str) -> list[str]:
    return [
        item.limitation
        for item in boundary.untracked
        if item.path == path and item.limitation is not None
    ]


def _same_untracked(before: GitBoundary, after: GitBoundary, path: str) -> bool:
    initial = next((item for item in before.untracked if item.path == path), None)
    final = next((item for item in after.untracked if item.path == path), None)
    return (
        initial is not None
        and final is not None
        and initial.content_base64 is not None
        and initial.sha256 is not None
        and initial.limitation is None
        and final.limitation is None
        and initial == final
    )


def _attribute(envelope: GitSessionEnvelope, artifact: str) -> GitAttribution:
    result = GitAttribution(
        limitations=list(dict.fromkeys([_CEILING, *envelope.limitations]))
    )
    before, after, history = envelope.before, envelope.after, envelope.history
    initial = {fact.path: fact.status for fact in before.paths} if before else {}
    for index, path in enumerate(initial):
        assert before is not None
        result.items.append(
            _item(
                artifact,
                "initial",
                path,
                "pre-existing",
                [f"/before/paths/{index}"],
                _path_limits(before, path),
            )
        )

    problem = None
    if (
        envelope.capture_status != "complete"
        or before is None
        or after is None
        or history is None
    ):
        problem = "Git capture is incomplete; inspect the preserved envelope and rerun capture."
    elif history.kind == "unsupported":
        result.limitations.extend(history.limitations)
        problem = (
            "Unsupported history cannot separate pre-existing and session material."
        )
    else:
        parent = before.head
        for commit in history.commits:
            if commit.parent != parent or commit.head == parent:
                problem = "Captured history does not link the session boundaries."
            parent = commit.head
        if (
            parent != after.head
            or before.head is None
            or after.head is None
            or (
                history.kind == "unchanged"
                and (history.commits or before.head != after.head)
            )
            or (history.kind == "linear" and not 1 <= len(history.commits) <= 100)
        ):
            problem = "Captured history does not link the session boundaries."

    if problem is None and envelope.patch_prefixes != "a/b":
        problem = "Legacy capture did not record Git patch prefixes; ambiguous paths cannot be attributed. Rerun capture with this version."

    # Parse once. An unknown block could conceal an initial or committed path,
    # so do not positively attribute any later material in that case.
    before_staged: dict[str, str] = {}
    before_unstaged: dict[str, str] = {}
    after_staged: dict[str, str] = {}
    after_unstaged: dict[str, str] = {}
    commit_patches: list[dict[str, str]] = []
    if problem is None:
        assert before is not None and after is not None and history is not None
        try:
            before_staged, before_unstaged = (
                _patches(before.staged_patch),
                _patches(before.unstaged_patch),
            )
            after_staged, after_unstaged = (
                _patches(after.staged_patch),
                _patches(after.unstaged_patch),
            )
            commit_patches = [_patches(commit.patch) for commit in history.commits]
            for boundary, staged, unstaged in [
                (before, before_staged, before_unstaged),
                (after, after_staged, after_unstaged),
            ]:
                paths = {fact.path for fact in boundary.paths}
                if (
                    boundary.dirty != bool(paths)
                    or not (staged.keys() | unstaged.keys()) <= paths
                ):
                    raise ValueError("Inconsistent boundary facts")
        except ValueError:
            problem = "Git patch or boundary facts are unsupported or inconsistent; inspect git-session.json and rerun capture."

    if problem:
        result.limitations.append(problem)
        result.items.append(
            _item(artifact, "history", None, "indeterminate", ["/history"], [problem])
        )
    touched = {path for patches in commit_patches for path in patches}
    if after is not None:
        for index, fact in enumerate(after.paths):
            limits = _path_limits(after, fact.path)
            label: GitAttributionClass = "indeterminate"
            locators = ["/before", f"/after/paths/{index}", "/history"]
            if (
                envelope.capture_status == "complete"
                and before == after
                and history is not None
                and history.kind == "unchanged"
                and not history.commits
                and (fact.status != "??" or _same_untracked(after, after, fact.path))
            ):
                # Exact boundary equality establishes known initial material even
                # in legacy captures; it needs no interpretation of path prefixes.
                label = "pre-existing"
            elif problem:
                limits.append(problem)
            elif fact.path not in initial:
                label = "session-attributed"
            elif (
                before is not None
                and fact.status == initial[fact.path]
                and fact.path not in touched
                and (
                    (fact.status == "??" and _same_untracked(before, after, fact.path))
                    or (
                        fact.status != "??"
                        and fact.path in (before_staged.keys() | before_unstaged.keys())
                        and before_staged.get(fact.path) == after_staged.get(fact.path)
                        and before_unstaged.get(fact.path)
                        == after_unstaged.get(fact.path)
                    )
                )
            ):
                label = "pre-existing"
            else:
                limits.append(_SAME_PATH)
            # The referenced boundary contains the patches/untracked bytes as well
            # as the inventory row; downstream consumers need not reopen Git.
            locators.append("/after")
            result.items.append(
                _item(artifact, "final", fact.path, label, locators, limits)
            )
    if not problem and history is not None:
        for index, (commit, patches) in enumerate(
            zip(history.commits, commit_patches, strict=True)
        ):
            if not patches:
                result.items.append(
                    _item(
                        artifact,
                        "commit",
                        None,
                        "session-attributed",
                        ["/before/head", "/after/head", f"/history/commits/{index}"],
                        [
                            "The commit is in the session range but contains no captured path changes; empty or excluded-only commits do not establish file changes."
                        ],
                        commit.head,
                    )
                )
            for path in patches:
                dirty = path in initial
                result.items.append(
                    _item(
                        artifact,
                        "commit",
                        path,
                        "indeterminate" if dirty else "session-attributed",
                        ["/before", f"/history/commits/{index}"],
                        [_SAME_PATH] if dirty else [],
                        commit.head,
                    )
                )
    return result
