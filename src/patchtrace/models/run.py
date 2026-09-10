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


class TaskDelivery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["retained_only", "codex_interactive_argv"]
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    prompt_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    boundary: Literal["none", "argv"]
    attempted: bool = False
    confirmation: Literal["unverified", "process_started", "failed"] = "unverified"
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_delivery(self) -> Self:
        if self.mode == "retained_only":
            if (
                self.boundary != "none"
                or self.attempted
                or self.prompt_sha256 is not None
                or self.confirmation != "unverified"
            ):
                raise ValueError("Retained tasks cannot claim delivery")
        elif self.boundary != "argv":
            raise ValueError("Interactive task delivery requires the argv boundary")
        if (
            self.prompt_sha256 is not None
            and self.prompt_sha256 != self.artifact_sha256
        ):
            raise ValueError("Prompt and artifact digests must agree")
        if self.attempted and self.prompt_sha256 is None:
            raise ValueError("Delivery attempts require a prepared prompt digest")
        if self.confirmation == "process_started" and not self.attempted:
            raise ValueError("Process confirmation requires an attempt")
        return self


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
    capture_mode: Literal["generic_pty", "codex_interactive"] = "generic_pty"
    task_delivery: TaskDelivery | None = None

    @model_validator(mode="after")
    def validate_outcomes(self) -> Self:
        if self.task_delivery is not None:
            if (
                self.task is None
                or self.task_delivery.artifact_sha256 != self.task.sha256
            ):
                raise ValueError("Delivery evidence must bind the captured task")
            if (self.task_delivery.mode == "codex_interactive_argv") != (
                self.capture_mode == "codex_interactive"
            ):
                raise ValueError("Task delivery mode must match capture mode")
            if (
                self.task_delivery.confirmation == "process_started"
                and self.process_outcome == "not_started"
            ):
                raise ValueError(
                    "Process-start confirmation cannot describe an unstarted process"
                )
            if (
                self.task_delivery.confirmation == "failed"
                and self.package_outcome == "complete"
            ):
                raise ValueError(
                    "Failed task delivery cannot produce a complete package"
                )
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
