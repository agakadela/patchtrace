from __future__ import annotations

import shlex

from patchtrace.models.report import SummaryReport
from patchtrace.models.run import RunManifest


def build_summary_report(manifest: RunManifest) -> SummaryReport:
    evidence_gaps = [
        "PatchTrace has not verified correctness, safety, or production readiness.",
        "No test command output has been parsed or verified in this phase.",
        "No claim extraction or final verdict has run in this phase.",
    ]
    if manifest.git_evidence is None:
        evidence_gaps.append("Git evidence was not captured for this run.")
    elif not manifest.git_evidence.patch_material_present:
        evidence_gaps.append("No git patch material was captured for this run.")
    if manifest.wrapped_command_exit_status != 0:
        evidence_gaps.append(
            f"Wrapped command exited with status "
            f"{manifest.wrapped_command_exit_status}."
        )

    return SummaryReport(
        run_id=manifest.run_id,
        command=manifest.command,
        wrapped_command_exit_status=manifest.wrapped_command_exit_status,
        outcome=manifest.outcome,
        artifact_paths=manifest.artifact_paths,
        evidence_gaps=evidence_gaps,
    )


def render_summary_markdown(report: SummaryReport) -> str:
    lines = [
        "# PatchTrace Summary",
        "",
        "## Run",
        f"- Run ID: `{report.run_id}`",
        f"- Command: `{shlex.join(report.command)}`",
        f"- Exit status: `{report.wrapped_command_exit_status}`",
        f"- Outcome: `{report.outcome}`",
        "",
        "## Artifacts Written",
        *[f"- `{artifact_path}`" for artifact_path in report.artifact_paths],
        "",
        "## Evidence Gaps",
        *[f"- {gap}" for gap in report.evidence_gaps],
        "",
    ]
    return "\n".join(lines)
