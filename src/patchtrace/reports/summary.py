from __future__ import annotations

import shlex
from pathlib import Path

from patchtrace.analysis.test_evidence import extract_command_test_signals
from patchtrace.models.report import DiffMaterialStatus, SummaryReport, TranscriptStatus
from patchtrace.models.run import RunManifest


def build_summary_report(
    manifest: RunManifest,
    *,
    run_dir: Path | None = None,
) -> SummaryReport:
    transcript_text = _read_artifact_text(
        run_dir,
        _find_artifact_path(manifest.artifact_paths, "agent-session.txt"),
    )
    transcript_status: TranscriptStatus = (
        "present" if transcript_text is not None else "missing"
    )
    changed_files = _read_changed_files(manifest, run_dir)
    diff_material_status = _diff_material_status(manifest, run_dir)
    command_test_signals = (
        extract_command_test_signals(transcript_text) if transcript_text else []
    )

    evidence_gaps = [
        "PatchTrace has not verified correctness, safety, or production readiness.",
        "No claim extraction or final verdict has run in this phase.",
    ]
    if transcript_status == "missing":
        evidence_gaps.append("Transcript artifact is missing for this run.")
    if manifest.git_evidence is None:
        evidence_gaps.append("Git evidence was not captured for this run.")
    elif not changed_files:
        evidence_gaps.append("No changed files were captured for this run.")
    if diff_material_status == "empty":
        evidence_gaps.append("No git patch material was captured for this run.")
    elif diff_material_status == "missing":
        evidence_gaps.append("Git patch material is missing for this run.")
    if not command_test_signals:
        evidence_gaps.append("No obvious command or test signals were detected.")
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
        transcript_status=transcript_status,
        changed_files=changed_files,
        diff_material_status=diff_material_status,
        command_test_signals=command_test_signals,
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
        "## Local Evidence",
        f"- Transcript: `{report.transcript_status}`",
        f"- Diff material: `{report.diff_material_status}`",
        "",
        "### Changed Files",
        *(
            [f"- `{changed_file}`" for changed_file in report.changed_files]
            if report.changed_files
            else ["- None captured."]
        ),
        "",
        "## Command/Test Signals",
        *(
            [f"- `{signal}`" for signal in report.command_test_signals]
            if report.command_test_signals
            else ["- None detected."]
        ),
        "",
        "## Artifacts Written",
        *[f"- `{artifact_path}`" for artifact_path in report.artifact_paths],
        "",
        "## Evidence Gaps",
        *[f"- {gap}" for gap in report.evidence_gaps],
        "",
    ]
    return "\n".join(lines)


def _find_artifact_path(artifact_paths: list[str], artifact_name: str) -> str | None:
    for artifact_path in artifact_paths:
        if Path(artifact_path).name == artifact_name:
            return artifact_path
    return None


def _read_artifact_text(run_dir: Path | None, artifact_path: str | None) -> str | None:
    if artifact_path is None:
        return None
    if run_dir is None:
        return ""

    path = run_dir / artifact_path
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _read_changed_files(manifest: RunManifest, run_dir: Path | None) -> list[str]:
    if manifest.git_evidence is None or run_dir is None:
        return []

    changed_files_text = _read_artifact_text(
        run_dir,
        manifest.git_evidence.changed_files_path,
    )
    if changed_files_text is None:
        return []
    return [line for line in changed_files_text.splitlines() if line]


def _diff_material_status(
    manifest: RunManifest,
    run_dir: Path | None,
) -> DiffMaterialStatus:
    if manifest.git_evidence is None:
        return "missing"
    if (
        run_dir is not None
        and not (run_dir / manifest.git_evidence.patch_path).is_file()
    ):
        return "missing"
    if manifest.git_evidence.patch_material_present:
        return "present"
    return "empty"
