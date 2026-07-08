from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from patchtrace.models.run import RunOutcome, TriggerSource

DiffMaterialStatus = Literal["present", "empty", "missing"]
TranscriptStatus = Literal["present", "missing"]


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
