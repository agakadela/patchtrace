from __future__ import annotations

import re

from patchtrace.analysis.test_evidence import (
    CommandEvidence,
    CommandResult,
    is_verification_command,
    parse_command_result,
)
from patchtrace.analysis.test_evidence import (
    extract_command_test_signals as extract_signals,
)
from patchtrace.codex.transcript import _FINAL_OUTPUT_MARKERS, normalize_transcript
from patchtrace.models.report import EvidenceReference

_INTERRUPTED_RE = re.compile(
    r"\b(?:interrupted|KeyboardInterrupt|cancelled|canceled)\b", re.IGNORECASE
)


def extract_command_test_signals(
    transcript_text: str,
    *,
    limit: int = 12,
) -> list[str]:
    normalized = normalize_transcript(transcript_text).normalized_text
    return extract_signals(
        "\n".join(_normalize_transcript_line(line) for line in normalized.splitlines()),
        limit=limit,
    )


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
        if command is None or not is_verification_command(command):
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
            if _INTERRUPTED_RE.search(lines[result_index]):
                result = "unknown"
                result_reference = EvidenceReference(
                    artifact_path=artifact_path,
                    locator=f"normalized transcript line {result_index + 1}",
                    description=f"Captured interruption of `{command}`; result unknown.",
                )
                break
            parsed_result = parse_command_result(lines[result_index])
            if parsed_result == "unknown" or result == "failed":
                continue
            result = parsed_result
            result_reference = EvidenceReference(
                artifact_path=artifact_path,
                locator=f"normalized transcript line {result_index + 1}",
                description=(
                    f"Captured output reports that `{command}` {parsed_result}."
                ),
            )

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
        return _normalize_command(stripped[len(prompt) :])
    return None


def _normalize_command(command: str) -> str:
    return " ".join(command.replace("`", "").strip().split())
