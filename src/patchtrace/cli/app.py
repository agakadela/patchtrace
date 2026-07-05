from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import typer

from patchtrace.models.run import RunManifest, RunOutcome
from patchtrace.session.recorder import record_command
from patchtrace.storage.runs import create_run_paths, write_run_manifest

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

    run_paths = create_run_paths(Path.cwd())
    started_at = datetime.now(UTC)
    recorded_session = record_command(
        command=command,
        transcript_path=run_paths.transcript_path,
        cwd=Path.cwd(),
    )
    ended_at = datetime.now(UTC)

    outcome: RunOutcome = (
        "completed" if recorded_session.exit_status == 0 else "wrapped_command_failed"
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
        ],
        wrapped_command_exit_status=recorded_session.exit_status,
        outcome=outcome,
    )
    write_run_manifest(run_paths, manifest)

    typer.echo(f"PatchTrace run material written to {run_paths.run_dir}")
    if recorded_session.exit_status != 0:
        typer.echo(
            "Wrapped command exited with status "
            f"{recorded_session.exit_status}; run material recorded.",
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
