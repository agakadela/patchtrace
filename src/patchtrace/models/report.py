from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from patchtrace.models.run import RunOutcome, TriggerSource

DiffMaterialStatus = Literal["present", "empty", "missing"]
TranscriptStatus = Literal["present", "missing"]
ClaimMaterialStatus = Literal["identified", "ambiguous", "missing"]
ClaimRelationship = Literal[
    "Evidence supports this claim",
    "Evidence partially supports this claim",
    "No supporting evidence found",
    "Available evidence conflicts with this claim",
    "Cannot assess from available material",
]


class ClaimCategory(StrEnum):
    FILE_CHANGE = "file_change"
    COMPLETED_CHANGE = "completed_change"
    TEST = "test"
    VERIFICATION_COMMAND = "verification_command"


class ClaimSupport(StrEnum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"
    CANNOT_DETERMINE = "cannot_determine"


class EvidenceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_path: str
    locator: str
    description: str


class ClaimAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim: str
    category: ClaimCategory
    claim_source: EvidenceReference
    support: ClaimSupport
    relationship: ClaimRelationship
    evidence_references: list[EvidenceReference]
    evidence_gap: str | None
    next_action: str | None


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    claim_material_status: ClaimMaterialStatus
    claim_assessments: list[ClaimAssessment]
    verdict: str
    most_important_gap: str
    next_action: str
    transcript_status: TranscriptStatus
    changed_files: list[str]
    diff_material_status: DiffMaterialStatus
    command_test_signals: list[str]
    evidence_gaps: list[str]


class SummaryReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    command: list[str]
    wrapped_command_exit_status: int
    outcome: RunOutcome
    artifact_paths: list[str]
    transcript_status: TranscriptStatus
    changed_files: list[str]
    diff_material_status: DiffMaterialStatus
    command_test_signals: list[str]
    evidence_gaps: list[str]
    verdict: str
    most_important_gap: str
    next_action: str


class AgentFeedbackReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    command: list[str]
    wrapped_command_exit_status: int
    outcome: RunOutcome
    artifact_paths: list[str]
    transcript_status: TranscriptStatus
    changed_files: list[str]
    diff_material_status: DiffMaterialStatus
    command_test_signals: list[str]
    evidence_gaps: list[str]
    verdict: str
    most_important_gap: str
    next_action: str
    requested_followups: list[str]


class VerificationBriefReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    command: list[str]
    trigger_source: TriggerSource
    started_at: datetime
    ended_at: datetime
    wrapped_command_exit_status: int
    outcome: RunOutcome
    artifact_paths: list[str]
    transcript_status: TranscriptStatus
    changed_files: list[str]
    diff_material_status: DiffMaterialStatus
    command_test_signals: list[str]
    evidence_gaps: list[str]
    review_first_targets: list[str]
    claim_material_status: ClaimMaterialStatus
    claim_assessments: list[ClaimAssessment]
