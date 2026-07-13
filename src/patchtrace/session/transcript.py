from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

FinalOutputStatus = Literal["identified", "ambiguous", "missing"]

_OSC_ESCAPE_RE = re.compile(r"\x1b\].*?(?:\x07|\x1b\\)", re.DOTALL)
_CSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_OTHER_ESCAPE_RE = re.compile(r"\x1b(?:[ -/][@-~]|[@-_])")
_FINAL_OUTPUT_MARKERS = frozenset(("Final answer:", "• Final answer:"))
_CODEX_MARKER_REDRAW_RE = re.compile(r"^(?P<marker>(?:• )?Final answer:)›.+$")
_CODEX_EXIT_MENU_SUFFIX_RE = re.compile(r"(?:/exit){2,}\s+exit Codex.*$")
_CODEX_SHUTDOWN_MARKER = "Shutting down..."
_UNRELATED_ENV_WARNING_RE = re.compile(
    r"GitHub MCP.*GITHUB_PAT_TOKEN.*not set",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class NormalizedTranscript:
    normalized_text: str
    final_output_status: FinalOutputStatus
    final_output: str | None


def normalize_transcript(transcript_text: str) -> NormalizedTranscript:
    """Remove terminal noise and conservatively bound explicit final output."""
    text = _strip_terminal_sequences(transcript_text)
    normalized_lines: list[str] = []

    for raw_line in text.replace("\r\n", "\n").split("\n"):
        line = _normalize_terminal_line(raw_line)
        marker_redraw = _CODEX_MARKER_REDRAW_RE.fullmatch(line)
        if marker_redraw is not None:
            line = marker_redraw.group("marker")
        if _UNRELATED_ENV_WARNING_RE.search(line):
            continue
        normalized_lines.append(line)

    normalized_text = _join_lines(normalized_lines)
    if not normalized_text:
        return NormalizedTranscript("", "missing", None)

    lines = normalized_text.splitlines()
    marker_indexes = [
        index for index, line in enumerate(lines) if line in _FINAL_OUTPUT_MARKERS
    ]
    if len(marker_indexes) != 1:
        return NormalizedTranscript(normalized_text, "ambiguous", None)

    final_output = _bound_final_output(lines[marker_indexes[0] + 1 :])
    if not final_output:
        return NormalizedTranscript(normalized_text, "ambiguous", None)
    return NormalizedTranscript(normalized_text, "identified", final_output)


def _strip_terminal_sequences(text: str) -> str:
    text = _OSC_ESCAPE_RE.sub("", text)
    text = _CSI_ESCAPE_RE.sub("", text)
    return _OTHER_ESCAPE_RE.sub("", text)


def _bound_final_output(lines: list[str]) -> str:
    bounded_lines: list[str] = []
    for line in lines:
        if _CODEX_SHUTDOWN_MARKER in line:
            break
        bounded_lines.append(_CODEX_EXIT_MENU_SUFFIX_RE.sub("", line).rstrip())
    return _join_lines(bounded_lines)


def _normalize_terminal_line(raw_line: str) -> str:
    line = raw_line.split("\r")[-1]
    visible: list[str] = []
    for character in line:
        if character == "\b":
            if visible:
                visible.pop()
            continue
        if character == "\t" or ord(character) >= 32 and ord(character) != 127:
            visible.append(character)
    return "".join(visible).strip()


def _join_lines(lines: list[str]) -> str:
    joined: list[str] = []
    previous_was_blank = False
    for line in lines:
        is_blank = not line
        if is_blank and (not joined or previous_was_blank):
            continue
        joined.append(line)
        previous_was_blank = is_blank
    while joined and not joined[-1]:
        joined.pop()
    return "\n".join(joined)
