from __future__ import annotations

import re

_OSC_ESCAPE_RE = re.compile(r"\x1b\].*?(?:\x07|\x1b\\)", re.DOTALL)
_CSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_OTHER_ESCAPE_RE = re.compile(r"\x1b(?:[ -/][@-~]|[@-_])")


def normalize_terminal_text(text: str) -> str:
    """Remove terminal noise without interpreting agent output."""
    text = _strip_terminal_sequences(text)
    return join_terminal_lines(
        [
            _normalize_terminal_line(line)
            for line in text.replace("\r\n", "\n").split("\n")
        ]
    )


def _strip_terminal_sequences(text: str) -> str:
    text = _OSC_ESCAPE_RE.sub("", text)
    text = _CSI_ESCAPE_RE.sub("", text)
    return _OTHER_ESCAPE_RE.sub("", text)


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


def join_terminal_lines(lines: list[str]) -> str:
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
