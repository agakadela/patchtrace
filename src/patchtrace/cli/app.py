from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import typer

from patchtrace.analysis.analyzer import analyze_run
from patchtrace.models.run import GitEvidenceManifest, RunManifest, RunOutcome
from patchtrace.reports.feedback import (
    build_agent_feedback_report,
    render_agent_feedback_markdown,
)
from patchtrace.reports.summary import build_summary_report, render_summary_markdown
from patchtrace.reports.verification_brief import (
    build_verification_brief_report,
    render_verification_brief_markdown,
)
from patchtrace.session.recorder import record_command
from patchtrace.storage.runs import create_run_paths, write_run_manifest
from patchtrace.vcs.git import GitCommandError, is_inside_work_tree
from patchtrace.vcs.snapshot import capture_git_evidence, capture_git_status

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Record agent sessions and generate local verification material.",
)


def _exit_not_implemented(command_name: str) -> None:
    typer.echo(
        f"patchtrace {command_name} is not implemented in this scaffold yet.",
        err=True,
    )
    raise typer.Exit(1)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def run(ctx: typer.Context) -> None:
    """Wrap an agent command and record local run material."""
    command = list(ctx.args)
    if not command:
        typer.echo("Usage: patchtrace run -- <command>", err=True)
        raise typer.Exit(2)

    workspace = Path.cwd()
    try:
        if not is_inside_work_tree(workspace):
            typer.echo(
                "PatchTrace run requires a Git work tree so patch evidence can be "
                "captured. Run from inside a git repository.",
                err=True,
            )
            raise typer.Exit(1)
        git_before_status = capture_git_status(workspace)
    except GitCommandError as error:
        typer.echo(f"Unable to inspect Git state: {error}", err=True)
        raise typer.Exit(1) from error

    run_paths = create_run_paths(workspace)
    started_at = datetime.now(UTC)
    run_paths.git_before_path.write_text(git_before_status, encoding="utf-8")
    recorded_session = record_command(
        command=command,
        transcript_path=run_paths.transcript_path,
        cwd=workspace,
    )
    ended_at = datetime.now(UTC)
    try:
        git_evidence = capture_git_evidence(workspace)
    except GitCommandError as error:
        typer.echo(f"Unable to capture Git evidence: {error}", err=True)
        raise typer.Exit(1) from error

    run_paths.git_after_path.write_text(git_evidence.after_status, encoding="utf-8")
    changed_files = "\n".join(git_evidence.changed_files)
    run_paths.changed_files_path.write_text(
        changed_files + ("\n" if changed_files else ""),
        encoding="utf-8",
    )
    run_paths.patch_path.write_text(git_evidence.patch, encoding="utf-8")

    outcome: RunOutcome = (
        "completed" if recorded_session.exit_status == 0 else "wrapped_command_failed"
    )
    git_before_path = run_paths.relative_artifact_path(run_paths.git_before_path)
    git_after_path = run_paths.relative_artifact_path(run_paths.git_after_path)
    changed_files_path = run_paths.relative_artifact_path(run_paths.changed_files_path)
    patch_path = run_paths.relative_artifact_path(run_paths.patch_path)
    summary_path = run_paths.relative_artifact_path(run_paths.summary_path)
    feedback_path = run_paths.relative_artifact_path(run_paths.feedback_path)
    verification_brief_path = run_paths.relative_artifact_path(
        run_paths.verification_brief_path
    )
    manifest = RunManifest(
        run_id=run_paths.run_id,
        command=command,
        trigger_source="manual_cli",
        started_at=started_at,
        ended_at=ended_at,
        artifact_paths=[
            run_paths.relative_artifact_path(run_paths.manifest_path),
            run_paths.relative_artifact_path(run_paths.transcript_path),
            git_before_path,
            git_after_path,
            changed_files_path,
            patch_path,
            summary_path,
            feedback_path,
            verification_brief_path,
        ],
        wrapped_command_exit_status=recorded_session.exit_status,
        outcome=outcome,
        git_evidence=GitEvidenceManifest(
            git_before_path=git_before_path,
            git_after_path=git_after_path,
            changed_files_path=changed_files_path,
            patch_path=patch_path,
            patch_material_present=git_evidence.patch_material_present,
        ),
    )
    analysis_result = analyze_run(manifest, run_dir=run_paths.run_dir)
    summary = build_summary_report(manifest, analysis_result=analysis_result)
    run_paths.summary_path.write_text(
        render_summary_markdown(summary),
        encoding="utf-8",
    )
    feedback = build_agent_feedback_report(
        manifest,
        analysis_result=analysis_result,
    )
    run_paths.feedback_path.write_text(
        render_agent_feedback_markdown(feedback),
        encoding="utf-8",
    )
    verification_brief = build_verification_brief_report(
        manifest,
        analysis_result=analysis_result,
    )
    run_paths.verification_brief_path.write_text(
        render_verification_brief_markdown(verification_brief),
        encoding="utf-8",
    )
    write_run_manifest(run_paths, manifest)

    display_run_dir = run_paths.run_dir.relative_to(workspace).as_posix()
    typer.echo(f"PatchTrace review package written to {display_run_dir}")
    typer.echo("Review the package before deciding next steps.")
    if recorded_session.exit_status != 0:
        typer.echo(
            "Wrapped command exited with status "
            f"{recorded_session.exit_status}; review package recorded.",
            err=True,
        )
        raise typer.Exit(recorded_session.exit_status)


@app.command()
def analyze() -> None:
    """Placeholder for analyzing existing local material."""
    _exit_not_implemented("analyze")


@app.command()
def watch() -> None:
    """Placeholder for patch-only watch mode."""
    _exit_not_implemented("watch")


def main() -> None:
    app()
