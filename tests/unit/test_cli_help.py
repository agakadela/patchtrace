from typer.testing import CliRunner

from patchtrace.cli.app import app

runner = CliRunner()


def test_help_lists_phase_2_command_surface() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "run" in result.output
    assert "analyze" in result.output
    assert "watch" in result.output


def test_unimplemented_commands_exit_without_claiming_success() -> None:
    command_args = (
        ["analyze"],
        ["watch"],
    )

    for args in command_args:
        result = runner.invoke(app, args)

        assert result.exit_code == 1
        assert "not implemented" in result.output
