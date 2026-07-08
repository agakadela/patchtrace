from __future__ import annotations

import shlex
from datetime import datetime
from pathlib import Path

from patchtrace.models.report import SummaryReport, VerificationBriefReport
from patchtrace.models.run import RunManifest
from patchtrace.reports.summary import build_summary_report


def build_verification_brief_report(
    manifest: RunManifest,
    *,
    run_dir: Path | None = None,
) -> VerificationBriefReport:
    summary = build_summary_report(manifest, run_dir=run_dir)
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
        "## Artifacts Written",
        *[f"- `{artifact_path}`" for artifact_path in report.artifact_paths],
        "",
        "## Evidence Gaps",
        *[f"- {gap}" for gap in report.evidence_gaps],
        "",
        "## Phase 3 Limits",
        "- Phase 3 does not perform full claim-vs-diff matching or prove correctness.",
        "- This brief reports bounded local evidence only.",
        "",
    ]
    return "\n".join(lines)


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
