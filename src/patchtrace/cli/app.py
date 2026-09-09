from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn

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
from patchtrace.storage.runs import (
    RunPaths,
    create_run_paths,
    write_git_session,
    write_run_manifest,
)
from patchtrace.vcs.envelope import (
    GitSessionEnvelope,
    capture_boundary,
    capture_history,
)
from patchtrace.vcs.git import GitCommandError, git_output, is_inside_work_tree
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
        repository_root = Path(
            git_output(workspace, "rev-parse", "--show-toplevel").strip()
        ).resolve()
    except GitCommandError as error:
        typer.echo(f"Unable to inspect Git state: {error}", err=True)
        raise typer.Exit(1) from error

    try:
        run_paths = create_run_paths(repository_root)
    except (OSError, ValueError, RuntimeError) as error:
        typer.echo(f"Unable to create PatchTrace run storage: {error}", err=True)
        raise typer.Exit(1) from error
    started_at = datetime.now(UTC)
    envelope = GitSessionEnvelope(
        repository_root=str(repository_root), patch_prefixes="a/b"
    )
    try:
        envelope.before = capture_boundary(repository_root)
        write_git_session(run_paths, envelope)
        run_paths.git_before_path.write_text(
            capture_git_status(repository_root), encoding="utf-8"
        )
    except (GitCommandError, OSError) as error:
        _exit_capture_failure(run_paths, envelope, "before", error)
    recorded_session = record_command(
        command=command,
        transcript_path=run_paths.transcript_path,
        cwd=workspace,
    )
    ended_at = datetime.now(UTC)
    stage = "after"
    try:
        envelope.after = capture_boundary(repository_root)
        write_git_session(run_paths, envelope)
        stage = "history"
        assert envelope.before is not None
        envelope.history = capture_history(
            repository_root, envelope.before, envelope.after
        )
        stage = "final_snapshot"
        git_evidence = capture_git_evidence(repository_root)
        envelope.capture_status = "complete"
        write_git_session(run_paths, envelope)
    except (GitCommandError, OSError) as error:
        _exit_capture_failure(run_paths, envelope, stage, error)

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
        repository_root=str(repository_root),
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
            run_paths.relative_artifact_path(run_paths.git_session_path),
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
            session_envelope_path=run_paths.relative_artifact_path(
                run_paths.git_session_path
            ),
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

    typer.echo(f"PatchTrace review package written to {run_paths.run_dir}")
    typer.echo("Review the package before deciding next steps.")
    if recorded_session.exit_status != 0:
        typer.echo(
            "Wrapped command exited with status "
            f"{recorded_session.exit_status}; review package recorded.",
            err=True,
        )
        raise typer.Exit(recorded_session.exit_status)


def _exit_capture_failure(
    paths: RunPaths,
    envelope: GitSessionEnvelope,
    stage: str,
    error: GitCommandError | OSError,
) -> NoReturn:
    envelope.capture_status = "failed"
    envelope.failed_stage = stage
    envelope.error = str(error)
    envelope.recovery = (
        "Inspect the preserved Git envelope and transcript if present. Check Git "
        "availability, repository readability and run-storage permissions, then "
        "rerun capture; this package is incomplete."
    )
    try:
        write_git_session(paths, envelope)
    except OSError as write_error:
        typer.echo(f"Unable to preserve capture failure: {write_error}", err=True)
    typer.echo(
        f"Unable to capture Git evidence ({stage}): {error}\n"
        f"Partial run material: {paths.run_dir}\n{envelope.recovery}",
        err=True,
    )
    raise typer.Exit(1) from error


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
