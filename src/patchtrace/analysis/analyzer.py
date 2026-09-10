from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from patchtrace.analysis.git_attribution import load_git_attribution
from patchtrace.analysis.test_evidence import (
    CommandEvidence,
    extract_command_test_signals,
    is_verification_command,
)
from patchtrace.codex import evidence as codex_evidence
from patchtrace.codex.transcript import final_output_lines, normalize_transcript
from patchtrace.models.report import (
    AnalysisResult,
    ClaimAssessment,
    ClaimCategory,
    ClaimMaterialStatus,
    ClaimRelationship,
    ClaimSupport,
    DiffMaterialStatus,
    EvidenceReference,
    GitAttribution,
)
from patchtrace.models.run import RunManifest

_BACKTICKED_TEXT_RE = re.compile(r"`([^`\n]+)`")
_CHANGE_VERB_RE = re.compile(
    r"^(?:implemented|completed|changed|updated|modified|added|created|removed|deleted|renamed|fixed)\b",
    re.IGNORECASE,
)
_NO_FILES_CHANGED_RE = re.compile(
    r"^no (?:files?|file changes?) (?:were )?changed[.!]?$",
    re.IGNORECASE,
)
_GENERIC_COMPLETION_RE = re.compile(
    r"^(?:done|fixed|everything works)[.!]?$",
    re.IGNORECASE,
)
_DIFF_HEADER_RE = re.compile(r"^diff --git a/(\S+) b/(\S+)$", re.MULTILINE)
# Only a complete, path-only statement can be established by file evidence.
_BOUNDED_FILE_CLAIM_RE = re.compile(
    r"^(changed|updated|modified|added|created|removed|deleted)\s+"
    r"`[^`\n]+`(?:(?:,\s*(?:and\s+)?|\s+and\s+)`[^`\n]+`)*[.!]?$",
    re.IGNORECASE,
)
FileOperation = Literal["changed", "modified", "added", "deleted"]
DiffChangeType = Literal["modified", "added", "deleted", "unknown"]
_FILE_OPERATIONS: dict[str, FileOperation] = {
    "changed": "changed",
    "updated": "modified",
    "modified": "modified",
    "added": "added",
    "created": "added",
    "removed": "deleted",
    "deleted": "deleted",
}
_TEST_CLAIM_RE = re.compile(r"^(?:tests?|test commands?)\b", re.IGNORECASE)
_VERIFICATION_CLAIM_RE = re.compile(
    r"^(?:verification(?: commands?)?|checks?|ran|executed)\b",
    re.IGNORECASE,
)
_PASSED_CLAIM_RE = re.compile(
    r"\b(?:pass|passed|succeeded|successfully)\b",
    re.IGNORECASE,
)
_FAILED_CLAIM_RE = re.compile(r"\b(?:fail|failed)\b", re.IGNORECASE)

_RELATIONSHIPS: dict[ClaimSupport, ClaimRelationship] = {
    ClaimSupport.SUPPORTED: "Evidence supports this claim",
    ClaimSupport.PARTIALLY_SUPPORTED: "Evidence partially supports this claim",
    ClaimSupport.UNSUPPORTED: "No supporting evidence found",
    ClaimSupport.CONTRADICTED: "Available evidence conflicts with this claim",
    ClaimSupport.CANNOT_DETERMINE: "Cannot assess from available material",
}


@dataclass(frozen=True)
class _PathEvidence:
    changed_files_available: bool
    changed_files: dict[str, EvidenceReference]
    patch_available: bool
    patch_has_content: bool
    patch_paths: dict[str, EvidenceReference]
    patch_types: dict[str, set[DiffChangeType]]
    material_references: tuple[EvidenceReference, ...]


@dataclass(frozen=True)
class _CommandClaim:
    category: ClaimCategory
    command: str
    claimed_result: str | None


def analyze_run(manifest: RunManifest, *, run_dir: Path) -> AnalysisResult:
    """Assess bounded explicit final claims against local run evidence."""
    attribution = load_git_attribution(manifest, run_dir)
    return _analyze_claims(manifest, run_dir=run_dir, git_attribution=attribution)


def _analyze_claims(
    manifest: RunManifest, *, run_dir: Path, git_attribution: GitAttribution
) -> AnalysisResult:
    path_evidence = _load_path_evidence(manifest, run_dir)
    transcript_path = _find_artifact_path(
        manifest.artifact_paths,
        "agent-session.txt",
    )
    transcript_text = _read_artifact_text(run_dir, transcript_path)
    if transcript_text is None:
        return _build_analysis_result(
            manifest,
            git_attribution=git_attribution,
            claim_material_status="missing",
            claim_assessments=[],
            path_evidence=path_evidence,
            transcript_text=None,
            command_evidence=[],
        )

    if manifest.capture_mode != "codex_interactive":
        return _build_analysis_result(
            manifest,
            git_attribution=git_attribution,
            claim_material_status="ambiguous" if transcript_text.strip() else "missing",
            claim_assessments=[],
            path_evidence=path_evidence,
            transcript_text=transcript_text,
            command_evidence=[],
        )
    normalized = normalize_transcript(transcript_text)
    status: ClaimMaterialStatus = normalized.final_output_status
    if normalized.final_output is None:
        return _build_analysis_result(
            manifest,
            git_attribution=git_attribution,
            claim_material_status=status,
            claim_assessments=[],
            path_evidence=path_evidence,
            transcript_text=transcript_text,
            command_evidence=[],
        )

    transcript_artifact = transcript_path or "agent-session.txt"
    command_evidence = codex_evidence.collect_command_evidence(
        normalized.normalized_text,
        artifact_path=transcript_artifact,
    )
    assessments = _assess_final_output(
        final_output_lines(normalized.final_output, transcript_artifact),
        path_evidence,
        command_evidence,
    )
    return _build_analysis_result(
        manifest,
        git_attribution=git_attribution,
        claim_material_status=status,
        claim_assessments=assessments,
        path_evidence=path_evidence,
        transcript_text=transcript_text,
        command_evidence=command_evidence,
    )


def _build_analysis_result(
    manifest: RunManifest,
    *,
    git_attribution: GitAttribution,
    claim_material_status: ClaimMaterialStatus,
    claim_assessments: list[ClaimAssessment],
    path_evidence: _PathEvidence,
    transcript_text: str | None,
    command_evidence: list[CommandEvidence],
) -> AnalysisResult:
    verdict, most_important_gap, next_action = _quick_decision(
        manifest,
        git_attribution=git_attribution,
        claim_material_status=claim_material_status,
        claim_assessments=claim_assessments,
        path_evidence=path_evidence,
        command_evidence=command_evidence,
    )
    return AnalysisResult(
        run_id=manifest.run_id,
        analysis_outcome=(
            "completed"
            if claim_material_status == "identified"
            and path_evidence.changed_files_available
            and path_evidence.patch_available
            else "degraded"
        ),
        git_attribution=git_attribution,
        claim_material_status=claim_material_status,
        claim_assessments=claim_assessments,
        verdict=verdict,
        most_important_gap=most_important_gap,
        next_action=next_action,
        transcript_status="present" if transcript_text is not None else "missing",
        changed_files=list(path_evidence.changed_files),
        diff_material_status=_diff_material_status(manifest, path_evidence),
        command_test_signals=(
            _command_signals(manifest, transcript_text) if transcript_text else []
        ),
        evidence_gaps=_evidence_gaps(
            manifest,
            transcript_text=transcript_text,
            path_evidence=path_evidence,
            most_important_gap=most_important_gap,
        ),
    )


def _command_signals(manifest: RunManifest, text: str) -> list[str]:
    if manifest.capture_mode == "codex_interactive":
        return codex_evidence.extract_command_test_signals(text)
    return extract_command_test_signals(text)


def _diff_material_status(
    manifest: RunManifest,
    path_evidence: _PathEvidence,
) -> DiffMaterialStatus:
    if manifest.git_evidence is None or not path_evidence.patch_available:
        return "missing"
    return "present" if manifest.git_evidence.patch_material_present else "empty"


def _evidence_gaps(
    manifest: RunManifest,
    *,
    transcript_text: str | None,
    path_evidence: _PathEvidence,
    most_important_gap: str,
) -> list[str]:
    gaps = [
        most_important_gap,
        "PatchTrace has not verified correctness, safety, or production readiness.",
        "File claim evidence describes snapshot material; Git session attribution "
        "is listed separately.",
        "Command results are transcript-derived observations, not independent "
        "execution proof; freshness relative to the final repository state is unresolved.",
    ]
    if manifest.task is None:
        gaps.append(
            "No task was supplied or captured; this generic run is not bound to "
            "a developer Task Contract. Requirement satisfaction is not evaluated."
        )
    else:
        gaps.append(
            f"Task capture: `{manifest.task.raw_path}` and `{manifest.task.parsed_path}`; "
            f"SHA-256 `{manifest.task.sha256}`; parse status `{manifest.task.parse_status}`. "
            "Requirement satisfaction is not evaluated."
        )
        delivery = manifest.task_delivery
        if delivery is None or delivery.mode == "retained_only":
            gaps.append(
                "Task delivery is unverified; PatchTrace has not submitted this artifact to the wrapped command."
            )
        else:
            gaps.append(
                f"Task delivery: `{delivery.mode}`; boundary `{delivery.boundary}`; "
                f"attempted `{delivery.attempted}`; confirmation `{delivery.confirmation}`; "
                f"prompt SHA-256 `{delivery.prompt_sha256}`."
            )
            gaps.extend(delivery.limitations)
    if manifest.capture_mode == "generic_pty":
        gaps.append(
            "Generic PTY capture has no agent-specific final-output selector; final claims are unverified."
        )
    else:
        gaps.append(
            "Codex final-output selection is marker-based compatibility evidence, not authenticated message provenance."
        )
    if transcript_text is None:
        gaps.append("Transcript artifact is missing for this run.")
    if manifest.git_evidence is None:
        gaps.append("Git evidence was not captured for this run.")
    elif not path_evidence.changed_files:
        gaps.append("The final Git snapshot contains no listed changed files.")
    diff_status = _diff_material_status(manifest, path_evidence)
    if diff_status == "empty":
        gaps.append("The final Git snapshot contains no patch material.")
    elif diff_status == "missing":
        gaps.append("Git patch material is missing for this run.")
    if not transcript_text or not _command_signals(manifest, transcript_text):
        gaps.append("No obvious command or test signals were detected.")
    return list(dict.fromkeys(gaps))


def _quick_decision(
    manifest: RunManifest,
    *,
    git_attribution: GitAttribution,
    claim_material_status: ClaimMaterialStatus,
    claim_assessments: list[ClaimAssessment],
    path_evidence: _PathEvidence,
    command_evidence: list[CommandEvidence],
) -> tuple[str, str, str]:
    if manifest.wrapped_command_exit_status != 0:
        return (
            "Review required: the wrapped command failed.",
            f"Wrapped command exited with status {manifest.wrapped_command_exit_status}.",
            "Address the wrapped command failure, rerun it, and review the new evidence.",
        )

    if claim_material_status == "missing":
        return (
            "Review blocked: agent claims could not be assessed.",
            "Transcript evidence is missing for this run.",
            (
                "Capture the agent transcript and rerun PatchTrace before relying "
                "on its claims."
            ),
        )

    latest_attempts = {attempt.command: attempt for attempt in command_evidence}
    failed_attempt = next(
        (attempt for attempt in latest_attempts.values() if attempt.result == "failed"),
        None,
    )
    if failed_attempt is not None:
        return (
            "Review required: the latest captured verification attempt failed.",
            f"Latest captured attempt of `{failed_attempt.command}` reports failure; "
            "an accurate claim about that failure does not resolve it.",
            f"Address the failure of `{failed_attempt.command}`, rerun it, "
            "and capture its output.",
        )

    priority = (
        ClaimSupport.CONTRADICTED,
        ClaimSupport.UNSUPPORTED,
        ClaimSupport.CANNOT_DETERMINE,
        ClaimSupport.PARTIALLY_SUPPORTED,
    )
    for support in priority:
        assessment = next(
            (
                candidate
                for candidate in claim_assessments
                if candidate.support is support
            ),
            None,
        )
        if assessment is None:
            continue
        verdict = {
            ClaimSupport.CONTRADICTED: (
                "Review required: available evidence conflicts with an assessed claim."
            ),
            ClaimSupport.UNSUPPORTED: (
                "Review required: an assessed claim lacks supporting evidence."
            ),
            ClaimSupport.CANNOT_DETERMINE: (
                "Review required: an assessed claim cannot be resolved from available "
                "material."
            ),
            ClaimSupport.PARTIALLY_SUPPORTED: (
                "Review required: an assessed claim has incomplete supporting evidence."
            ),
        }[support]
        return (
            verdict,
            assessment.evidence_gap
            or "The highest-priority assessed claim has an unresolved evidence gap.",
            assessment.next_action
            or "Inspect the claim and its evidence references before deciding next steps.",
        )

    no_changes = (
        manifest.git_evidence is not None
        and not manifest.git_evidence.patch_material_present
        and path_evidence.changed_files_available
        and path_evidence.patch_available
        and not path_evidence.changed_files
        and not path_evidence.patch_has_content
        and not any(
            item.attribution == "indeterminate"
            or (item.attribution == "session-attributed" and item.path is not None)
            for item in git_attribution.items
        )
    )
    if no_changes:
        return (
            "No captured file changes require review.",
            "PatchTrace cannot determine whether the absence of changes was intended.",
            "Confirm that no change was intended; otherwise capture the missing change.",
        )

    if claim_material_status == "ambiguous":
        return (
            "Review blocked: claim-bearing final output could not be identified.",
            "The transcript does not contain one unambiguous final response.",
            "Capture one explicit final response and rerun PatchTrace.",
        )

    if not claim_assessments:
        return (
            "Review required: no explicit final claims were available to assess.",
            "No bounded file, change, test, or verification-command claim was extracted.",
            "Review the local evidence directly and request specific final claims.",
        )

    return (
        "Available evidence supports the assessed claims; human review is still required.",
        "Evidence support does not establish correctness, safety, or acceptance.",
        "Review the referenced changes before deciding whether to accept them.",
    )


def _assess_final_output(
    final_lines: list[tuple[str, EvidenceReference]],
    path_evidence: _PathEvidence,
    command_evidence: list[CommandEvidence],
) -> list[ClaimAssessment]:
    assessments: list[ClaimAssessment] = []
    for raw_line, source in final_lines:
        claim = _strip_list_marker(raw_line)
        if not claim or _GENERIC_COMPLETION_RE.fullmatch(claim):
            continue

        if _NO_FILES_CHANGED_RE.fullmatch(claim):
            assessments.append(_assess_no_files_changed(claim, source, path_evidence))
            continue

        command_claim = _extract_command_claim(claim)
        if command_claim is not None:
            assessments.append(
                _assess_command_claim(claim, source, command_claim, command_evidence)
            )
            continue

        claimed_paths = _extract_paths(claim)
        if claimed_paths and _CHANGE_VERB_RE.match(claim):
            assessments.append(
                _assess_file_change(claim, claimed_paths, source, path_evidence)
            )
            continue

        if _is_specific_completed_change(claim):
            assessments.append(_assess_completed_change(claim, source))

    return assessments


def _extract_command_claim(claim: str) -> _CommandClaim | None:
    command: str | None = None
    for candidate in _BACKTICKED_TEXT_RE.findall(claim):
        normalized = " ".join(candidate.strip().split())
        if is_verification_command(normalized):
            command = normalized
            break
    if command is None:
        return None

    if _TEST_CLAIM_RE.match(claim):
        category = ClaimCategory.TEST
    elif _VERIFICATION_CLAIM_RE.match(claim):
        category = ClaimCategory.VERIFICATION_COMMAND
    else:
        return None

    claimed_result: str | None = None
    if _FAILED_CLAIM_RE.search(claim):
        claimed_result = "failed"
    elif _PASSED_CLAIM_RE.search(claim):
        claimed_result = "passed"
    return _CommandClaim(category, command, claimed_result)


def _assess_command_claim(
    claim: str,
    source: EvidenceReference,
    command_claim: _CommandClaim,
    command_evidence: list[CommandEvidence],
) -> ClaimAssessment:
    evidence = next(
        (
            candidate
            for candidate in reversed(command_evidence)
            if candidate.command == command_claim.command
        ),
        None,
    )
    if evidence is None:
        return _assessment(
            claim=claim,
            category=command_claim.category,
            source=source,
            support=ClaimSupport.UNSUPPORTED,
            evidence_references=[],
            evidence_gap=f"No captured command matches `{command_claim.command}`.",
            next_action=(
                f"Run `{command_claim.command}` and capture its result output."
            ),
        )

    references = [evidence.command_reference]
    if evidence.result_reference is not None:
        references.append(evidence.result_reference)

    if evidence.result == "unknown":
        return _assessment(
            claim=claim,
            category=command_claim.category,
            source=source,
            support=ClaimSupport.PARTIALLY_SUPPORTED,
            evidence_references=references,
            evidence_gap=(
                "The latest command attempt is captured, but its result is unknown "
                "or incomplete. Only the invocation is supported; earlier results "
                "do not establish this attempt's outcome."
            ),
            next_action=f"Capture the result output for `{command_claim.command}`.",
        )

    if (
        command_claim.claimed_result is not None
        and command_claim.claimed_result != evidence.result
    ):
        return _assessment(
            claim=claim,
            category=command_claim.category,
            source=source,
            support=ClaimSupport.CONTRADICTED,
            evidence_references=references,
            evidence_gap=(
                "Captured output reports that the claimed verification command "
                f"{evidence.result}."
            ),
            next_action=(
                "Address the captured failure, rerun the same command, and capture "
                "its output."
                if evidence.result == "failed"
                else "Reconcile the failure claim with the captured passing output."
            ),
        )

    return _assessment(
        claim=claim,
        category=command_claim.category,
        source=source,
        support=ClaimSupport.SUPPORTED,
        evidence_references=references,
        evidence_gap=None,
        next_action=None,
    )


def _assess_file_change(
    claim: str,
    claimed_paths: list[str],
    source: EvidenceReference,
    path_evidence: _PathEvidence,
) -> ClaimAssessment:
    references = []
    matched_paths = []
    for path in claimed_paths:
        reference = path_evidence.patch_paths.get(path)
        if reference is None:
            reference = path_evidence.changed_files.get(path)
        if reference is not None:
            references.append(reference)
            matched_paths.append(path)

    bounded = _BOUNDED_FILE_CLAIM_RE.fullmatch(claim)
    # Non-path backticks or extra prose cannot be silently discarded.
    operation = _FILE_OPERATIONS[bounded.group(1).lower()] if bounded else None
    supported_paths = (
        [
            path
            for path in matched_paths
            if operation == "changed"
            or path_evidence.patch_types.get(path) == {operation}
        ]
        if operation is not None
        else []
    )
    unresolved_paths = [path for path in claimed_paths if path not in supported_paths]
    targets = ", ".join(f"`{path}`" for path in unresolved_paths)

    if not path_evidence.changed_files_available and not path_evidence.patch_available:
        support = ClaimSupport.CANNOT_DETERMINE
        gap = "Changed-file and diff evidence are unavailable."
        action = "Capture git changed-file or diff evidence and rerun PatchTrace."
    elif operation is None:
        support = ClaimSupport.CANNOT_DETERMINE
        gap = (
            f"Cannot determine whether the claimed change was achieved: {claim} "
            "Observed file facts do not establish semantic correctness or completion."
        )
        action = (
            "Review the claimed behavior and provide targeted verification evidence."
        )
    elif len(supported_paths) == len(claimed_paths):
        support = ClaimSupport.SUPPORTED
        gap = None
        action = None
    elif supported_paths:
        support = ClaimSupport.PARTIALLY_SUPPORTED
        established = ", ".join(f"`{path}`" for path in supported_paths)
        gap = (
            f"Captured evidence establishes {operation} for {established} only; "
            f"it does not establish {operation} for {targets}."
        )
        action = f"Provide matching {operation} evidence for {targets}."
    elif not matched_paths:
        support = ClaimSupport.UNSUPPORTED
        gap = f"No captured changed-file or diff reference matches {targets}."
        action = f"Confirm whether {targets} changed and provide the matching diff."
    else:
        support = ClaimSupport.CANNOT_DETERMINE
        gap = f"Observed file facts do not establish {operation} for {targets}."
        action = f"Inspect the change type and provide matching {operation} evidence."

    return _assessment(
        claim=claim,
        category=ClaimCategory.FILE_CHANGE,
        source=source,
        support=support,
        evidence_references=references or list(path_evidence.material_references),
        evidence_gap=gap,
        next_action=action,
    )


def _assess_no_files_changed(
    claim: str,
    source: EvidenceReference,
    path_evidence: _PathEvidence,
) -> ClaimAssessment:
    references = list(path_evidence.changed_files.values())
    if not references:
        references = list(path_evidence.patch_paths.values())

    if references:
        return _assessment(
            claim=claim,
            category=ClaimCategory.FILE_CHANGE,
            source=source,
            support=ClaimSupport.CONTRADICTED,
            evidence_references=references[:3],
            evidence_gap="Captured git evidence lists changed files; session attribution is unresolved.",
            next_action=(
                "Reconcile the final claim with the captured changed-file evidence."
            ),
        )

    if (
        path_evidence.changed_files_available
        and path_evidence.patch_available
        and not path_evidence.patch_has_content
    ):
        return _assessment(
            claim=claim,
            category=ClaimCategory.FILE_CHANGE,
            source=source,
            support=ClaimSupport.SUPPORTED,
            evidence_references=list(path_evidence.material_references),
            evidence_gap=None,
            next_action=None,
        )

    return _assessment(
        claim=claim,
        category=ClaimCategory.FILE_CHANGE,
        source=source,
        support=ClaimSupport.CANNOT_DETERMINE,
        evidence_references=[],
        evidence_gap=(
            "Changed-file or diff evidence is unavailable or contains unparsed changes."
        ),
        next_action="Capture complete git evidence and rerun PatchTrace.",
    )


def _assess_completed_change(
    claim: str,
    source: EvidenceReference,
) -> ClaimAssessment:
    return _assessment(
        claim=claim,
        category=ClaimCategory.COMPLETED_CHANGE,
        source=source,
        support=ClaimSupport.CANNOT_DETERMINE,
        evidence_references=[],
        evidence_gap=(
            "The claim does not identify a file or other exact local evidence target."
        ),
        next_action=(
            "Name the changed file or diff location that demonstrates this change."
        ),
    )


def _assessment(
    *,
    claim: str,
    category: ClaimCategory,
    source: EvidenceReference,
    support: ClaimSupport,
    evidence_references: list[EvidenceReference],
    evidence_gap: str | None,
    next_action: str | None,
) -> ClaimAssessment:
    return ClaimAssessment(
        claim=claim,
        category=category,
        claim_source=source,
        support=support,
        relationship=_RELATIONSHIPS[support],
        evidence_references=evidence_references,
        evidence_gap=evidence_gap,
        next_action=next_action,
    )


def _load_path_evidence(manifest: RunManifest, run_dir: Path) -> _PathEvidence:
    if manifest.git_evidence is None:
        return _PathEvidence(False, {}, False, False, {}, {}, ())

    changed_files_text = _read_artifact_text(
        run_dir,
        manifest.git_evidence.changed_files_path,
    )
    patch_text = _read_artifact_text(run_dir, manifest.git_evidence.patch_path)
    material_references: list[EvidenceReference] = []
    if changed_files_text is not None:
        material_references.append(
            EvidenceReference(
                artifact_path=manifest.git_evidence.changed_files_path,
                locator="entire artifact",
                description="Changed-file inventory inspected for matching paths.",
            )
        )
    if patch_text is not None:
        material_references.append(
            EvidenceReference(
                artifact_path=manifest.git_evidence.patch_path,
                locator="entire artifact",
                description="Git diff inspected for matching file headers.",
            )
        )
    patch_paths, patch_types = _patch_references(
        patch_text, manifest.git_evidence.patch_path
    )
    return _PathEvidence(
        changed_files_available=changed_files_text is not None,
        changed_files=_changed_file_references(
            changed_files_text,
            manifest.git_evidence.changed_files_path,
        ),
        patch_available=patch_text is not None,
        patch_has_content=bool(patch_text and patch_text.strip()),
        patch_paths=patch_paths,
        patch_types=patch_types,
        material_references=tuple(material_references),
    )


def _changed_file_references(
    text: str | None,
    artifact_path: str,
) -> dict[str, EvidenceReference]:
    if text is None:
        return {}
    references: dict[str, EvidenceReference] = {}
    for line_number, raw_path in enumerate(text.splitlines(), start=1):
        path = _normalize_path(raw_path)
        if not path:
            continue
        references[path] = EvidenceReference(
            artifact_path=artifact_path,
            locator=f"line {line_number}",
            description=(
                f"Observed in captured changed-file inventory: `{path}` changed; "
                "change type unknown. This does not establish who made the change or when."
            ),
        )
    return references


def _patch_references(
    text: str | None,
    artifact_path: str,
) -> tuple[dict[str, EvidenceReference], dict[str, set[DiffChangeType]]]:
    references: dict[str, EvidenceReference] = {}
    change_types: dict[str, set[DiffChangeType]] = {}
    if text is None:
        return references, change_types
    # Parse each captured entry independently; staged and unstaged entries may
    # disagree. Never let the last entry erase an earlier change type.
    headers = list(_DIFF_HEADER_RE.finditer(text))
    line_number = 1
    previous_start = 0
    for index, match in enumerate(headers):
        line_number += text.count("\n", previous_start, match.start())
        previous_start = match.start()
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        block = text[match.end() : end].splitlines()
        metadata = []
        for line in block:
            if line.startswith(("@@", "GIT binary patch", "diff --")):
                break
            metadata.append(line)
        old_path, new_path = match.groups()
        change_type: DiffChangeType = "unknown"
        if old_path == new_path:
            if any(
                re.fullmatch(r"deleted file mode [0-7]{6}", line) for line in metadata
            ):
                change_type = "deleted"
            elif any(
                re.fullmatch(r"new file mode [0-7]{6}", line) for line in metadata
            ):
                change_type = "added"
            elif f"--- a/{old_path}" in metadata and f"+++ b/{new_path}" in metadata:
                change_type = "modified"
        for raw_path in dict.fromkeys((old_path, new_path)):
            path = _normalize_path(raw_path)
            change_types.setdefault(path, set()).add(change_type)
            types = ", ".join(sorted(change_types[path]))
            references[path] = EvidenceReference(
                artifact_path=artifact_path,
                locator=f"diff header line {line_number}",
                description=(
                    f"Observed in captured diff: `{path}`; change type: {types}. "
                    "This does not establish who made the change or when."
                ),
            )
    return references, change_types


def _extract_paths(claim: str) -> list[str]:
    paths = []
    for candidate in _BACKTICKED_TEXT_RE.findall(claim):
        path = _normalize_path(candidate)
        if _BOUNDED_FILE_CLAIM_RE.fullmatch(claim) or "/" in path or Path(path).suffix:
            paths.append(path)
    return list(dict.fromkeys(paths))


def _is_specific_completed_change(claim: str) -> bool:
    match = _CHANGE_VERB_RE.match(claim)
    if match is None:
        return False
    detail = claim[match.end() :].strip(" .:;-")
    return bool(detail)


def _strip_list_marker(line: str) -> str:
    stripped = line.strip()
    for marker in ("- ", "* ", "• "):
        if stripped.startswith(marker):
            return stripped[len(marker) :].strip()
    return stripped


def _normalize_path(path: str) -> str:
    return path.removeprefix("./")


def _find_artifact_path(artifact_paths: list[str], name: str) -> str | None:
    for artifact_path in artifact_paths:
        if Path(artifact_path).name == name:
            return artifact_path
    return None


def _read_artifact_text(run_dir: Path, artifact_path: str | None) -> str | None:
    if artifact_path is None:
        return None
    path = run_dir / artifact_path
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")
