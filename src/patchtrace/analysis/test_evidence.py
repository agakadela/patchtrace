from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from patchtrace.models.report import EvidenceReference
from patchtrace.session.transcript import normalize_terminal_text

_COMMAND_SIGNAL_MARKERS = (
    "uv run pytest",
    "uv run ruff",
    "uv run mypy",
    "uv build",
    "pytest",
    "ruff check",
    "ruff format",
    "mypy ",
    "npm test",
    "pnpm test",
    "yarn test",
    "bun test",
    "cargo test",
    "go test",
    "make test",
    "tox",
    "nox",
)

_TEST_OUTPUT_MARKERS = (
    " test session starts ",
    " collected ",
    " passed",
    " failed",
    " error",
)

CommandResult = Literal["passed", "failed", "unknown"]

_PASS_RESULT_RE = re.compile(
    r"(?:\b[1-9]\d* passed\b|\ball checks passed\b|\bno issues found\b|"
    r"\bsuccessfully built\b)",
    re.IGNORECASE,
)
_FAIL_RESULT_RE = re.compile(
    r"(?:\b[1-9]\d* errors?\b|\berror:|\bfailed\b)",
    re.IGNORECASE,
)
_ZERO_FAILURE_RE = re.compile(r"\b0 (?:failed|errors?)\b", re.IGNORECASE)


@dataclass(frozen=True)
class CommandEvidence:
    command: str
    command_reference: EvidenceReference
    result: CommandResult
    result_reference: EvidenceReference | None


def extract_command_test_signals(
    transcript_text: str,
    *,
    limit: int = 12,
) -> list[str]:
    signals: list[str] = []
    seen: set[str] = set()

    normalized_transcript = normalize_terminal_text(transcript_text)
    for raw_line in normalized_transcript.splitlines():
        line = raw_line.replace("`", "").strip().removeprefix("$ ").removeprefix("> ")
        if not line or not _is_command_test_signal(line):
            continue
        if line in seen:
            continue

        signals.append(line)
        seen.add(line)
        if len(signals) >= limit:
            break

    return signals


def parse_command_result(line: str) -> CommandResult:
    if _FAIL_RESULT_RE.search(_ZERO_FAILURE_RE.sub("", line)):
        return "failed"
    if _PASS_RESULT_RE.search(line):
        return "passed"
    return "unknown"


def is_verification_command(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in _COMMAND_SIGNAL_MARKERS)


def _is_command_test_signal(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in _COMMAND_SIGNAL_MARKERS) or any(
        marker in lowered for marker in _TEST_OUTPUT_MARKERS
    )
