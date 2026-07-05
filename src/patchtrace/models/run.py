from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

RunOutcome = Literal["completed", "wrapped_command_failed"]
TriggerSource = Literal["manual_cli"]


class GitEvidenceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    git_before_path: str
    git_after_path: str
    changed_files_path: str
    patch_path: str
    patch_material_present: bool


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    command: list[str]
    trigger_source: TriggerSource
    started_at: datetime
    ended_at: datetime
    artifact_paths: list[str]
    wrapped_command_exit_status: int
    outcome: RunOutcome
    git_evidence: GitEvidenceManifest | None = None
