from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from patchtrace.models.report import EvidenceReference
from patchtrace.session.transcript import normalize_transcript

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

_FINAL_OUTPUT_MARKERS = frozenset(("Final answer:", "• Final answer:"))
_PASS_RESULT_RE = re.compile(
    r"(?:\b\d+ passed\b|\ball checks passed\b|\bno issues found\b|"
    r"\bsuccessfully built\b)",
    re.IGNORECASE,
)
_FAIL_RESULT_RE = re.compile(
    r"(?:\b\d+ failed\b|\bfound \d+ errors?\b|\berror:|\bfailed\b)",
    re.IGNORECASE,
)


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

    normalized_transcript = normalize_transcript(transcript_text)
    for raw_line in normalized_transcript.normalized_text.splitlines():
        line = _normalize_transcript_line(raw_line)
        if not line or not _is_command_test_signal(line):
            continue
        if line in seen:
            continue

        signals.append(line)
        seen.add(line)
        if len(signals) >= limit:
            break

    return signals


def collect_command_evidence(
    normalized_transcript: str,
    *,
    artifact_path: str,
) -> list[CommandEvidence]:
    """Collect exact command invocations and bounded result lines before final output."""
    lines = normalized_transcript.splitlines()
    marker_indexes = [
        index for index, line in enumerate(lines) if line in _FINAL_OUTPUT_MARKERS
    ]
    if len(marker_indexes) == 1:
        lines = lines[: marker_indexes[0]]

    evidence: list[CommandEvidence] = []
    for index, line in enumerate(lines):
        command = _extract_invoked_command(line)
        if command is None:
            continue

        command_reference = EvidenceReference(
            artifact_path=artifact_path,
            locator=f"normalized transcript line {index + 1}",
            description=f"Captured invocation of `{command}`.",
        )
        result: CommandResult = "unknown"
        result_reference: EvidenceReference | None = None
        for result_index in range(index + 1, len(lines)):
            if _extract_invoked_command(lines[result_index]) is not None:
                break
            parsed_result = _parse_result(lines[result_index])
            if parsed_result == "unknown":
                continue
            result = parsed_result
            result_reference = EvidenceReference(
                artifact_path=artifact_path,
                locator=f"normalized transcript line {result_index + 1}",
                description=(
                    f"Captured output reports that `{command}` {parsed_result}."
                ),
            )
            break

        evidence.append(
            CommandEvidence(
                command=command,
                command_reference=command_reference,
                result=result,
                result_reference=result_reference,
            )
        )
    return evidence


def _normalize_transcript_line(raw_line: str) -> str:
    line = raw_line.replace("`", "").strip()
    for prompt in ("$ ", "> ", "› ", "• Ran "):
        if line.startswith(prompt):
            return line[len(prompt) :].strip()
    return line


def _extract_invoked_command(line: str) -> str | None:
    stripped = line.strip()
    for prompt in ("• Ran ", "$ ", "> "):
        if not stripped.startswith(prompt):
            continue
        command = _normalize_command(stripped[len(prompt) :])
        if is_verification_command(command):
            return command
    return None


def _parse_result(line: str) -> CommandResult:
    if _FAIL_RESULT_RE.search(line):
        return "failed"
    if _PASS_RESULT_RE.search(line):
        return "passed"
    return "unknown"


def _normalize_command(command: str) -> str:
    return " ".join(command.replace("`", "").strip().split())


def is_verification_command(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in _COMMAND_SIGNAL_MARKERS)


def _is_command_test_signal(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in _COMMAND_SIGNAL_MARKERS) or any(
        marker in lowered for marker in _TEST_OUTPUT_MARKERS
    )
