from __future__ import annotations

import shlex
from pathlib import Path

from patchtrace.models.report import AgentFeedbackReport, SummaryReport
from patchtrace.models.run import RunManifest
from patchtrace.reports.summary import build_summary_report


def build_agent_feedback_report(
    manifest: RunManifest,
    *,
    run_dir: Path | None = None,
) -> AgentFeedbackReport:
    summary = build_summary_report(manifest, run_dir=run_dir)
    return AgentFeedbackReport(
        run_id=summary.run_id,
        command=summary.command,
        wrapped_command_exit_status=summary.wrapped_command_exit_status,
        outcome=summary.outcome,
        artifact_paths=summary.artifact_paths,
        transcript_status=summary.transcript_status,
        changed_files=summary.changed_files,
        diff_material_status=summary.diff_material_status,
        command_test_signals=summary.command_test_signals,
        evidence_gaps=summary.evidence_gaps,
        requested_followups=_requested_followups(summary),
    )


def render_agent_feedback_markdown(report: AgentFeedbackReport) -> str:
    lines = [
        "# PatchTrace Agent Feedback",
        "",
        "Paste this back to the agent:",
        "",
        "```text",
        f"PatchTrace captured bounded local evidence for run `{report.run_id}`.",
        "",
        "Wrapped command:",
        f"- Command: `{shlex.join(report.command)}`",
        f"- Exit status: `{report.wrapped_command_exit_status}`",
        f"- Outcome: `{report.outcome}`",
        "",
        "Local evidence:",
        f"- Transcript: `{report.transcript_status}`",
        f"- Diff material: `{report.diff_material_status}`",
        "- Changed files:",
        *(
            [f"  - `{changed_file}`" for changed_file in report.changed_files]
            if report.changed_files
            else ["  - None captured."]
        ),
        "- Command/test signals:",
        *(
            [f"  - `{signal}`" for signal in report.command_test_signals]
            if report.command_test_signals
            else ["  - None detected."]
        ),
        "",
        "Evidence gaps to close:",
        *[f"- {gap}" for gap in report.evidence_gaps],
        "",
        "Follow-up work requested:",
        *[f"- {followup}" for followup in report.requested_followups],
        "",
        "Local artifacts to reference:",
        *[f"- `{artifact_path}`" for artifact_path in report.artifact_paths],
        "```",
        "",
    ]
    return "\n".join(lines)


def _requested_followups(report: SummaryReport) -> list[str]:
    followups: list[str] = []

    if report.wrapped_command_exit_status != 0:
        followups.append("Address the wrapped command failure and rerun it.")
    if report.transcript_status == "missing":
        followups.append(
            "Rerun with transcript capture or attach the missing transcript."
        )
    if not report.changed_files:
        followups.append(
            "Explain why no file changes were expected, or make the intended change."
        )
    if report.diff_material_status == "empty":
        followups.append(
            "Explain why no diff material was expected, or rerun after producing the patch."
        )
    elif report.diff_material_status == "missing":
        followups.append("Rerun where git patch material can be captured.")
    if not report.command_test_signals:
        followups.append("Run the relevant tests and paste the exact command output.")

    if not followups:
        followups.append(
            "Point reviewers to the captured artifacts and exact command/test signals."
        )

    return followups
