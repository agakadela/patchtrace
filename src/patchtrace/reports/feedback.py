from __future__ import annotations

import shlex

from patchtrace.models.report import AgentFeedbackReport, AnalysisResult
from patchtrace.models.run import RunManifest
from patchtrace.reports.summary import build_summary_report


def build_agent_feedback_report(
    manifest: RunManifest,
    *,
    analysis_result: AnalysisResult,
) -> AgentFeedbackReport:
    summary = build_summary_report(manifest, analysis_result=analysis_result)
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
        verdict=summary.verdict,
        most_important_gap=summary.most_important_gap,
        next_action=summary.next_action,
        requested_followups=_requested_followups(analysis_result),
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
        "PatchTrace assessment:",
        f"- Verdict: {report.verdict}",
        f"- Highest-priority gap: {report.most_important_gap}",
        f"- Recommended next action: {report.next_action}",
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
        "Evidence limits and gaps:",
        *[f"- {gap}" for gap in report.evidence_gaps],
        "",
        "Follow-up work requested:",
        *(
            [f"- {followup}" for followup in report.requested_followups]
            if report.requested_followups
            else ["- None beyond the recommended next action above."]
        ),
        "",
        "Local artifacts to reference:",
        *[f"- `{artifact_path}`" for artifact_path in report.artifact_paths],
        "```",
        "",
    ]
    return "\n".join(lines)


def _requested_followups(analysis_result: AnalysisResult) -> list[str]:
    return [
        f'Claim "{assessment.claim}": {assessment.next_action}'
        for assessment in analysis_result.claim_assessments
        if assessment.next_action is not None
    ]
