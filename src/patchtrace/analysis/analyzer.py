from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from patchtrace.models.report import (
    AnalysisResult,
    ClaimAssessment,
    ClaimCategory,
    ClaimMaterialStatus,
    ClaimRelationship,
    ClaimSupport,
    EvidenceReference,
)
from patchtrace.models.run import RunManifest
from patchtrace.session.transcript import normalize_transcript

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
_DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+) b/(.+)$")

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
    patch_paths: dict[str, EvidenceReference]
    material_references: tuple[EvidenceReference, ...]


def analyze_run(manifest: RunManifest, *, run_dir: Path) -> AnalysisResult:
    """Assess explicit final file/change claims against local run evidence."""
    transcript_path = _find_artifact_path(
        manifest.artifact_paths,
        "agent-session.txt",
    )
    transcript_text = _read_artifact_text(run_dir, transcript_path)
    if transcript_text is None:
        return AnalysisResult(
            run_id=manifest.run_id,
            claim_material_status="missing",
            claim_assessments=[],
        )

    normalized = normalize_transcript(transcript_text)
    status: ClaimMaterialStatus = normalized.final_output_status
    if normalized.final_output is None:
        return AnalysisResult(
            run_id=manifest.run_id,
            claim_material_status=status,
            claim_assessments=[],
        )

    path_evidence = _load_path_evidence(manifest, run_dir)
    assessments = _assess_final_output(
        normalized.final_output,
        transcript_path or "agent-session.txt",
        path_evidence,
    )
    return AnalysisResult(
        run_id=manifest.run_id,
        claim_material_status=status,
        claim_assessments=assessments,
    )


def _assess_final_output(
    final_output: str,
    transcript_path: str,
    path_evidence: _PathEvidence,
) -> list[ClaimAssessment]:
    assessments: list[ClaimAssessment] = []
    for line_number, raw_line in enumerate(final_output.splitlines(), start=1):
        claim = _strip_list_marker(raw_line)
        if not claim or _GENERIC_COMPLETION_RE.fullmatch(claim):
            continue

        source = EvidenceReference(
            artifact_path=transcript_path,
            locator=f"final response line {line_number}",
            description="Explicit statement in the identified final response.",
        )
        if _NO_FILES_CHANGED_RE.fullmatch(claim):
            assessments.append(_assess_no_files_changed(claim, source, path_evidence))
            continue

        claimed_path = _extract_path(claim)
        if claimed_path is not None and _CHANGE_VERB_RE.match(claim):
            assessments.append(
                _assess_file_change(claim, claimed_path, source, path_evidence)
            )
            continue

        if _is_specific_completed_change(claim):
            assessments.append(_assess_completed_change(claim, source))

    return assessments


def _assess_file_change(
    claim: str,
    claimed_path: str,
    source: EvidenceReference,
    path_evidence: _PathEvidence,
) -> ClaimAssessment:
    reference = path_evidence.changed_files.get(claimed_path)
    if reference is None:
        reference = path_evidence.patch_paths.get(claimed_path)

    if reference is not None:
        return _assessment(
            claim=claim,
            category=ClaimCategory.FILE_CHANGE,
            source=source,
            support=ClaimSupport.SUPPORTED,
            evidence_references=[reference],
            evidence_gap=None,
            next_action=None,
        )

    if path_evidence.changed_files_available or path_evidence.patch_available:
        return _assessment(
            claim=claim,
            category=ClaimCategory.FILE_CHANGE,
            source=source,
            support=ClaimSupport.UNSUPPORTED,
            evidence_references=list(path_evidence.material_references),
            evidence_gap=(
                f"No captured changed-file or diff reference matches `{claimed_path}`."
            ),
            next_action=(
                f"Confirm whether `{claimed_path}` changed and provide the matching diff."
            ),
        )

    return _assessment(
        claim=claim,
        category=ClaimCategory.FILE_CHANGE,
        source=source,
        support=ClaimSupport.CANNOT_DETERMINE,
        evidence_references=[],
        evidence_gap="Changed-file and diff evidence are unavailable.",
        next_action="Capture git changed-file or diff evidence and rerun PatchTrace.",
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
            evidence_gap="Captured git evidence lists files changed during the run.",
            next_action=(
                "Reconcile the final claim with the captured changed-file evidence."
            ),
        )

    if path_evidence.changed_files_available and path_evidence.patch_available:
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
        evidence_gap="Changed-file or diff evidence is unavailable.",
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
        return _PathEvidence(False, {}, False, {}, ())

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
    return _PathEvidence(
        changed_files_available=changed_files_text is not None,
        changed_files=_changed_file_references(
            changed_files_text,
            manifest.git_evidence.changed_files_path,
        ),
        patch_available=patch_text is not None,
        patch_paths=_patch_references(patch_text, manifest.git_evidence.patch_path),
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
        path = _normalize_path(raw_path.strip())
        if not path:
            continue
        references[path] = EvidenceReference(
            artifact_path=artifact_path,
            locator=f"line {line_number}",
            description=f"Captured changed-file entry for `{path}`.",
        )
    return references


def _patch_references(
    text: str | None,
    artifact_path: str,
) -> dict[str, EvidenceReference]:
    if text is None:
        return {}
    references: dict[str, EvidenceReference] = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = _DIFF_HEADER_RE.fullmatch(line)
        if match is None:
            continue
        path = _normalize_path(match.group(2))
        references[path] = EvidenceReference(
            artifact_path=artifact_path,
            locator=f"diff header line {line_number}",
            description=f"Captured diff entry for `{path}`.",
        )
    return references


def _extract_path(claim: str) -> str | None:
    for candidate in _BACKTICKED_TEXT_RE.findall(claim):
        if any(character.isspace() for character in candidate):
            continue
        path = _normalize_path(candidate)
        if "/" in path or Path(path).suffix:
            return path
    return None


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
    normalized = path.strip().removeprefix("./")
    if normalized.startswith(("a/", "b/")):
        return normalized[2:]
    return normalized


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
