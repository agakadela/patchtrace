from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from patchtrace.models.run import RunOutcome


class SummaryReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    command: list[str]
    wrapped_command_exit_status: int
    outcome: RunOutcome
    artifact_paths: list[str]
    evidence_gaps: list[str]
