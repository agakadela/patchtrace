from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from patchtrace.models.run import RunManifest, TaskDelivery


@pytest.mark.parametrize(
    "changes",
    [
        {"prompt_sha256": "b" * 64},
        {"confirmation": "process_started", "attempted": False},
        {"prompt_sha256": None},
        {"mode": "retained_only"},
        {"boundary": "none"},
    ],
)
def test_contradictory_delivery_evidence_is_rejected(
    changes: dict[str, object],
) -> None:
    data = dict(
        mode="codex_interactive_argv",
        artifact_sha256="a" * 64,
        prompt_sha256="a" * 64,
        boundary="argv",
        attempted=True,
        confirmation="process_started",
        limitations=["No receipt proof."],
    )
    with pytest.raises(ValidationError):
        TaskDelivery.model_validate(data | changes)


@pytest.mark.parametrize(
    "change",
    ["task_digest", "capture_mode", "no_task", "not_started", "failed_complete"],
)
def test_run_delivery_is_bound_to_task_and_lifecycle(change: str) -> None:
    data: dict[str, object] = dict(
        run_id="delivery",
        command=["codex"],
        trigger_source="manual_cli",
        started_at=datetime.now(UTC),
        ended_at=datetime.now(UTC),
        artifact_paths=["task.md", "task.json"],
        wrapped_command_exit_status=0,
        process_outcome="completed",
        analysis_outcome="degraded",
        package_outcome="complete",
        capture_mode="codex_interactive",
        task={"sha256": "a" * 64, "parse_status": "valid"},
        task_delivery=dict(
            mode="codex_interactive_argv",
            artifact_sha256="a" * 64,
            prompt_sha256="a" * 64,
            boundary="argv",
            attempted=True,
            confirmation="process_started",
            limitations=["No receipt proof."],
        ),
    )
    if change == "task_digest":
        data["task"] = {"sha256": "b" * 64, "parse_status": "valid"}
    elif change == "capture_mode":
        data["capture_mode"] = "generic_pty"
    elif change == "no_task":
        data["task"] = None
    elif change == "not_started":
        data.update(
            process_outcome="not_started",
            wrapped_command_exit_status=None,
            package_outcome="partial",
        )
    else:
        delivery = data["task_delivery"]
        assert isinstance(delivery, dict)
        delivery["confirmation"] = "failed"
    with pytest.raises(ValidationError):
        RunManifest.model_validate(data)
