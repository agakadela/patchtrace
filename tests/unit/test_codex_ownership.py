from pathlib import Path

from patchtrace.codex.transcript import final_output_lines, normalize_transcript
from patchtrace.session.transcript import normalize_terminal_text


def test_generic_cleanup_does_not_interpret_codex_tui_lines() -> None:
    text = "\x1b[32m• Final answer:›redraw\x1b[0m\r\nGitHub MCP GITHUB_PAT_TOKEN not set\r\nShutting down..."
    cleaned = normalize_terminal_text(text)
    assert "• Final answer:›redraw" in cleaned
    assert "GITHUB_PAT_TOKEN" in cleaned
    assert "Shutting down..." in cleaned


def test_generic_session_and_analysis_do_not_own_codex_markers_or_locators() -> None:
    root = Path(__file__).parents[2] / "src" / "patchtrace"
    for package in ("session", "analysis"):
        for path in (root / package).glob("*.py"):
            source = path.read_text()
            for token in (
                "Final answer:",
                "• Ran ",
                "exit Codex",
                "Shutting down...",
                "GITHUB_PAT_TOKEN",
                "final response line",
                "normalized transcript line",
            ):
                assert token not in source, (path, token)


def test_codex_boundary_owns_final_selection_and_its_locator() -> None:
    selected = normalize_transcript(
        "• Final answer:\nModified `a.py`.\nShutting down..."
    )
    assert selected.final_output == "Modified `a.py`."
    lines = final_output_lines(selected.final_output, "agent-session.txt")
    assert lines[0][1].artifact_path == "agent-session.txt"
    assert lines[0][1].locator == "final response line 1"


def test_empty_final_marker_cannot_use_recorder_footer_as_response() -> None:
    selected = normalize_transcript(
        "Final answer:\n[patchtrace] wrapped command exited with status 0\n"
    )
    assert selected.final_output is None
    assert selected.final_output_status == "ambiguous"
