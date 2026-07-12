from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict, cast

from patchtrace.analysis.test_evidence import extract_command_test_signals
from patchtrace.session.transcript import normalize_transcript

FIXTURE = Path(__file__).parents[1] / "fixtures" / "codex_transcript_noise.json"


class TranscriptFixture(TypedDict):
    raw_transcript: str
    normalized_text: str
    final_output: str
    command_test_signals: list[str]


def test_normalizes_synthetic_codex_transcript_and_identifies_final_output() -> None:
    fixture = _load_fixture()

    transcript = normalize_transcript(fixture["raw_transcript"])

    assert transcript.normalized_text == fixture["normalized_text"]
    assert transcript.final_output_status == "identified"
    assert transcript.final_output == fixture["final_output"]


def test_leaves_unmarked_final_output_ambiguous() -> None:
    transcript = normalize_transcript("Agent discussed options.\nImplemented parser.\n")

    assert transcript.normalized_text == "Agent discussed options.\nImplemented parser."
    assert transcript.final_output_status == "ambiguous"
    assert transcript.final_output is None


def test_marks_empty_transcript_final_output_missing() -> None:
    transcript = normalize_transcript("\x1b[2K\r\n\x00\t\n")

    assert transcript.normalized_text == ""
    assert transcript.final_output_status == "missing"
    assert transcript.final_output is None


def test_command_test_signals_use_cleaned_transcript_lines() -> None:
    fixture = _load_fixture()

    signals = extract_command_test_signals(fixture["raw_transcript"])

    assert signals == fixture["command_test_signals"]
    assert all("\x1b" not in signal for signal in signals)
    assert all("GITHUB_PAT_TOKEN" not in signal for signal in signals)


def _load_fixture() -> TranscriptFixture:
    return cast(
        TranscriptFixture,
        json.loads(FIXTURE.read_text(encoding="utf-8")),
    )
