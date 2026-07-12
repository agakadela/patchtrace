from __future__ import annotations

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


def _normalize_transcript_line(raw_line: str) -> str:
    line = raw_line.replace("`", "").strip()
    for prompt in ("$ ", "> ", "› ", "• Ran "):
        if line.startswith(prompt):
            return line[len(prompt) :].strip()
    return line


def _is_command_test_signal(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in _COMMAND_SIGNAL_MARKERS) or any(
        marker in lowered for marker in _TEST_OUTPUT_MARKERS
    )
