from __future__ import annotations

import shlex

from patchtrace.models.report import (
    AnalysisResult,
    SummaryReport,
)
from patchtrace.models.run import RunManifest
from patchtrace.reports.provenance import render_git_attribution


def build_summary_report(
    manifest: RunManifest,
    *,
    analysis_result: AnalysisResult,
) -> SummaryReport:
    return SummaryReport(
        run_id=manifest.run_id,
        command=manifest.command,
        wrapped_command_exit_status=manifest.wrapped_command_exit_status,
        process_outcome=manifest.process_outcome,
        analysis_outcome=analysis_result.analysis_outcome,
        artifact_paths=manifest.artifact_paths,
        transcript_status=analysis_result.transcript_status,
        git_attribution=analysis_result.git_attribution,
        diff_material_status=analysis_result.diff_material_status,
        command_test_signals=analysis_result.command_test_signals,
        evidence_gaps=analysis_result.evidence_gaps,
        verdict=analysis_result.verdict,
        most_important_gap=analysis_result.most_important_gap,
        next_action=analysis_result.next_action,
    )


def render_summary_markdown(report: SummaryReport) -> str:
    lines = [
        "# PatchTrace Summary",
        "",
        "## Quick Decision",
        f"- Verdict: {report.verdict}",
        f"- Most important gap: {report.most_important_gap}",
        f"- Recommended next action: {report.next_action}",
        "",
        "## Run",
        f"- Run ID: `{report.run_id}`",
        f"- Command: `{shlex.join(report.command)}`",
        f"- Exit status: `{report.wrapped_command_exit_status}`",
        f"- Process outcome: `{report.process_outcome}`",
        f"- Analysis outcome: `{report.analysis_outcome}`",
        "- Package outcome: see `run.json` (authoritative after all writes).",
        "",
        "## Local Evidence",
        f"- Transcript: `{report.transcript_status}`",
        f"- Diff material: `{report.diff_material_status}`",
        "",
        *render_git_attribution(report.git_attribution),
        "",
        "## Command/Test Signals",
        *(
            [f"- `{signal}`" for signal in report.command_test_signals]
            if report.command_test_signals
            else ["- None detected."]
        ),
        "",
        "## Required Artifacts",
        *[f"- `{artifact_path}`" for artifact_path in report.artifact_paths],
        "",
        "## Evidence Gaps",
        *[f"- {gap}" for gap in report.evidence_gaps],
        "",
    ]
    return "\n".join(lines)
