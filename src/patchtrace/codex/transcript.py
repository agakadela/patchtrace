from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from patchtrace.models.report import EvidenceReference
from patchtrace.session.transcript import join_terminal_lines, normalize_terminal_text

FinalOutputStatus = Literal["identified", "ambiguous", "missing"]

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
    text = normalize_terminal_text(transcript_text)
    normalized_lines: list[str] = []

    for line in text.split("\n"):
        marker_redraw = _CODEX_MARKER_REDRAW_RE.fullmatch(line)
        if marker_redraw is not None:
            line = marker_redraw.group("marker")
        if _UNRELATED_ENV_WARNING_RE.search(line):
            continue
        normalized_lines.append(line)

    normalized_text = join_terminal_lines(normalized_lines)
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


def _bound_final_output(lines: list[str]) -> str:
    bounded_lines: list[str] = []
    for line in lines:
        if _CODEX_SHUTDOWN_MARKER in line or line.startswith(
            "[patchtrace] wrapped command exited with status "
        ):
            break
        bounded_lines.append(_CODEX_EXIT_MENU_SUFFIX_RE.sub("", line).rstrip())
    return join_terminal_lines(bounded_lines)


def final_output_lines(
    final_output: str, artifact_path: str
) -> list[tuple[str, EvidenceReference]]:
    return [
        (
            line,
            EvidenceReference(
                artifact_path=artifact_path,
                locator=f"final response line {number}",
                description="Explicit statement in the marker-selected Codex final response.",
            ),
        )
        for number, line in enumerate(final_output.splitlines(), start=1)
    ]
