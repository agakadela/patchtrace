from __future__ import annotations

from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

ProcessOutcome = Literal["not_started", "completed", "failed", "unknown"]
AnalysisOutcome = Literal["not_run", "completed", "degraded", "failed"]
PackageOutcome = Literal["partial", "complete", "failed"]
TriggerSource = Literal["manual_cli"]


class RunFailure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: str = Field(min_length=1)
    message: str = Field(min_length=1)


class GitEvidenceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    git_before_path: str
    git_after_path: str
    changed_files_path: str
    patch_path: str
    patch_material_present: bool
    session_envelope_path: str | None = None


class TaskEvidenceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_path: Literal["task.md"] = "task.md"
    parsed_path: Literal["task.json"] = "task.json"
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    parse_status: Literal["valid", "invalid"]


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = 2
    run_id: str
    command: list[str]
    trigger_source: TriggerSource
    started_at: datetime
    ended_at: datetime | None
    artifact_paths: list[str]
    wrapped_command_exit_status: int | None = Field(ge=0, le=255)
    process_outcome: ProcessOutcome
    analysis_outcome: AnalysisOutcome
    package_outcome: PackageOutcome
    failures: list[RunFailure] = Field(default_factory=list)
    git_evidence: GitEvidenceManifest | None = None
    repository_root: str | None = None
    task: TaskEvidenceManifest | None = None

    @model_validator(mode="after")
    def validate_outcomes(self) -> Self:
        if self.task is not None:
            if not {self.task.raw_path, self.task.parsed_path}.issubset(
                self.artifact_paths
            ):
                raise ValueError("Task artifacts must be listed in the run inventory")
            if (
                self.task.parse_status == "invalid"
                and self.package_outcome == "complete"
            ):
                raise ValueError("An invalid task cannot produce a complete package")
        code = self.wrapped_command_exit_status
        if self.process_outcome == "completed":
            valid_process = code == 0
        elif self.process_outcome == "failed":
            valid_process = code is not None and code != 0
        else:
            valid_process = code is None
        if not valid_process:
            raise ValueError("Process outcome must agree with the observed exit status")
        if self.package_outcome == "complete" and (
            self.analysis_outcome not in ("completed", "degraded")
            or self.process_outcome not in ("completed", "failed")
            or self.ended_at is None
            or self.failures
        ):
            raise ValueError(
                "A complete package requires finished capture and analysis"
            )
        return self
