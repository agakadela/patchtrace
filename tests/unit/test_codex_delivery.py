from hashlib import sha256
from pathlib import Path

import pytest

from patchtrace.codex.interactive import (
    prepare_task_command,
    validate_interactive_command,
)


def test_prompt_comes_from_preserved_bytes_without_shell_or_text_normalization(
    tmp_path: Path,
) -> None:
    raw = b"\xef\xbb\xbf## Outcome\r\nZa\xc5\xbc\xc3\xb3\xc5\x82\xc4\x87 `echo no` $(touch nope)  \r\n## Requirements\r\n1. Keep it.  "
    artifact = tmp_path / "task.md"
    artifact.write_bytes(raw)
    digest = sha256(raw).hexdigest()
    command, delivery = prepare_task_command(
        ["codex", "--no-alt-screen"], artifact, digest
    )
    assert command == ["codex", "--no-alt-screen", "--", raw.decode("utf-8")]
    assert sha256(command[-1].encode("utf-8")).hexdigest() == digest
    assert delivery.artifact_sha256 == delivery.prompt_sha256 == digest
    assert delivery.confirmation == "unverified"
    assert not delivery.attempted
    assert delivery.boundary == "argv"


@pytest.mark.parametrize(
    "args",
    [
        ["exec"],
        ["resume", "--last"],
        ["other prompt"],
        ["--", "prompt"],
        ["--help"],
        ["--unknown"],
        ["-m"],
        ["--image", "one.png", "two.png"],
    ],
)
def test_conflicting_or_unverified_invocations_are_rejected(
    tmp_path: Path, args: list[str]
) -> None:
    artifact = tmp_path / "task.md"
    artifact.write_bytes(b"task")
    with pytest.raises(ValueError, match="interactive"):
        prepare_task_command(["codex", *args], artifact, sha256(b"task").hexdigest())


def test_changed_preserved_artifact_prevents_delivery(tmp_path: Path) -> None:
    artifact = tmp_path / "task.md"
    artifact.write_bytes(b"changed")
    with pytest.raises(ValueError, match="digest"):
        prepare_task_command(["codex"], artifact, sha256(b"original").hexdigest())


def test_nul_is_explicit_delivery_failure(tmp_path: Path) -> None:
    artifact = tmp_path / "task.md"
    artifact.write_bytes(b"task\0")
    with pytest.raises(ValueError, match="NUL"):
        prepare_task_command(["codex"], artifact, sha256(b"task\0").hexdigest())


@pytest.mark.parametrize(
    "args",
    [
        ["exec"],
        ["app-server"],
        ["resume", "--last"],
        ["--remote", "ws://example.test"],
        ["--help"],
    ],
)
def test_explicit_interactive_mode_rejects_other_modes_even_without_task(
    args: list[str],
) -> None:
    with pytest.raises(ValueError, match="interactive"):
        validate_interactive_command(["codex", *args], has_task=False)


def test_supported_options_are_preserved_with_prompt(tmp_path: Path) -> None:
    raw = b"task"
    artifact = tmp_path / "task.md"
    artifact.write_bytes(raw)
    command = [
        "codex",
        "--model=chosen-model",
        "-c",
        'model_reasoning_effort="low"',
        "--sandbox",
        "read-only",
        "-i",
        "one.png",
        "--image=two.png",
    ]
    prepared, _ = prepare_task_command(command, artifact, sha256(raw).hexdigest())
    assert prepared == [*command, "--", "task"]
