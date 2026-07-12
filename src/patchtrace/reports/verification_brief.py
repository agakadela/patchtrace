from __future__ import annotations

import shlex
from datetime import datetime

from patchtrace.models.report import (
    AnalysisResult,
    ClaimAssessment,
    SummaryReport,
    VerificationBriefReport,
)
from patchtrace.models.run import RunManifest
from patchtrace.reports.summary import build_summary_report


def build_verification_brief_report(
    manifest: RunManifest,
    *,
    analysis_result: AnalysisResult,
) -> VerificationBriefReport:
    summary = build_summary_report(manifest, analysis_result=analysis_result)
    return VerificationBriefReport(
        run_id=summary.run_id,
        command=summary.command,
        trigger_source=manifest.trigger_source,
        started_at=manifest.started_at,
        ended_at=manifest.ended_at,
        wrapped_command_exit_status=summary.wrapped_command_exit_status,
        outcome=summary.outcome,
        artifact_paths=summary.artifact_paths,
        transcript_status=summary.transcript_status,
        changed_files=summary.changed_files,
        diff_material_status=summary.diff_material_status,
        command_test_signals=summary.command_test_signals,
        evidence_gaps=summary.evidence_gaps,
        review_first_targets=_review_first_targets(summary),
        claim_material_status=analysis_result.claim_material_status,
        claim_assessments=analysis_result.claim_assessments,
    )


def render_verification_brief_markdown(report: VerificationBriefReport) -> str:
    lines = [
        "# PatchTrace Verification Brief",
        "",
        "## Run Metadata",
        f"- Run ID: `{report.run_id}`",
        f"- Command: `{shlex.join(report.command)}`",
        f"- Trigger source: `{report.trigger_source}`",
        f"- Started at: `{_format_datetime(report.started_at)}`",
        f"- Ended at: `{_format_datetime(report.ended_at)}`",
        f"- Exit status: `{report.wrapped_command_exit_status}`",
        f"- Outcome: `{report.outcome}`",
        "",
        "## Local Evidence",
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
        "## Conservative Labels",
        f"- Transcript: `{report.transcript_status}`",
        f"- Diff material: `{report.diff_material_status}`",
        f"- Command/test signals: `{_signals_status(report)}`",
        f"- Wrapped command: `{_wrapped_command_status(report)}`",
        "",
        "## Review First",
        *[f"- {target}" for target in report.review_first_targets],
        "",
        "## Claim Assessments",
        *_render_claim_assessments(report),
        "",
        "## Artifacts Written",
        *[f"- `{artifact_path}`" for artifact_path in report.artifact_paths],
        "",
        "## Evidence Gaps",
        *[f"- {gap}" for gap in report.evidence_gaps],
        "",
        "## Assessment Limits",
        "- Claim relationships describe captured evidence only; they do not prove "
        "correctness, safety, acceptance, or production readiness.",
        "- Only explicit claims in uniquely identified final output are assessed.",
        "",
    ]
    return "\n".join(lines)


def _render_claim_assessments(report: VerificationBriefReport) -> list[str]:
    if not report.claim_assessments:
        return [
            "- No bounded explicit final claims were extracted.",
            f"- Claim material: `{report.claim_material_status}`.",
        ]

    lines: list[str] = []
    for index, assessment in enumerate(report.claim_assessments, start=1):
        if lines:
            lines.append("")
        lines.extend(_render_claim_assessment(index, assessment))
    return lines


def _render_claim_assessment(
    index: int,
    assessment: ClaimAssessment,
) -> list[str]:
    category = assessment.category.value.replace("_", " ").capitalize()
    lines = [
        f"### Claim {index}: {category}",
        f"- Claim: {assessment.claim}",
        "- Source: "
        f"`{assessment.claim_source.artifact_path}` "
        f"(`{assessment.claim_source.locator}`)",
        f"- Relationship: **{assessment.relationship}**",
        "- Evidence:",
    ]
    if assessment.evidence_references:
        lines.extend(
            "  - "
            f"`{reference.artifact_path}` (`{reference.locator}`): "
            f"{reference.description}"
            for reference in assessment.evidence_references
        )
    else:
        lines.append("  - None matched.")
    if assessment.evidence_gap is not None:
        lines.append(f"- Evidence gap: {assessment.evidence_gap}")
    if assessment.next_action is not None:
        lines.append(f"- Next action: {assessment.next_action}")
    return lines


def _review_first_targets(report: SummaryReport) -> list[str]:
    if not report.changed_files:
        return ["No changed files were captured; inspect git evidence artifacts first."]

    targets = [f"Review `{report.changed_files[0]}` first."]
    targets.extend(
        f"Then review `{changed_file}`." for changed_file in report.changed_files[1:]
    )
    return targets


def _signals_status(report: VerificationBriefReport) -> str:
    return "present" if report.command_test_signals else "missing"


def _wrapped_command_status(report: VerificationBriefReport) -> str:
    if report.wrapped_command_exit_status == 0:
        return "zero exit"
    return f"non-zero exit {report.wrapped_command_exit_status}"


def _format_datetime(value: datetime) -> str:
    return value.isoformat()
