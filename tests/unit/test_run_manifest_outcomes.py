from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from patchtrace.models.run import RunManifest


def manifest_data() -> dict[str, object]:
    now = datetime.now(UTC)
    return dict(
        schema_version=2,
        run_id="outcomes",
        command=["fake"],
        trigger_source="manual_cli",
        started_at=now,
        ended_at=now,
        artifact_paths=[],
        wrapped_command_exit_status=0,
        process_outcome="completed",
        analysis_outcome="degraded",
        package_outcome="complete",
    )


def test_successful_process_can_have_degraded_analysis_and_complete_package() -> None:
    manifest = RunManifest.model_validate(manifest_data())
    assert manifest.process_outcome == "completed"
    assert manifest.analysis_outcome == "degraded"
    assert manifest.package_outcome == "complete"
    assert "outcome" not in manifest.model_dump()
    assert "verdict" not in manifest.model_dump()


@pytest.mark.parametrize(
    "changes",
    [
        {"process_outcome": "completed", "wrapped_command_exit_status": 7},
        {"process_outcome": "failed", "wrapped_command_exit_status": 0},
        {"process_outcome": "not_started", "wrapped_command_exit_status": 0},
        {"process_outcome": "unknown", "wrapped_command_exit_status": 0},
        {"process_outcome": "failed", "wrapped_command_exit_status": None},
        {"wrapped_command_exit_status": -1},
        {"analysis_outcome": "failed", "package_outcome": "complete"},
        {"analysis_outcome": "not_run", "package_outcome": "complete"},
        {"ended_at": None, "package_outcome": "complete"},
        {"failures": [{"stage": "report_write", "message": "disk full"}]},
        {"process_outcome": "unknown", "wrapped_command_exit_status": None},
    ],
)
def test_contradictory_lifecycle_facts_are_rejected(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        RunManifest.model_validate(manifest_data() | changes)


def test_legacy_combined_outcome_is_not_silently_upgraded() -> None:
    data = manifest_data()
    for key in (
        "schema_version",
        "process_outcome",
        "analysis_outcome",
        "package_outcome",
    ):
        del data[key]
    data["outcome"] = "completed"
    with pytest.raises(ValidationError):
        RunManifest.model_validate(data)
