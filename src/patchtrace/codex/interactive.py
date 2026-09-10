from hashlib import sha256
from pathlib import Path

from patchtrace.models.run import TaskDelivery

# Verified with codex-cli 0.144.1 --help and the official CLI reference:
# https://learn.chatgpt.com/docs/developer-commands?surface=cli
_VALUE_OPTIONS = frozenset(
    (
        "-c",
        "--config",
        "--enable",
        "--disable",
        "-i",
        "--image",
        "-m",
        "--model",
        "--local-provider",
        "-p",
        "--profile",
        "-s",
        "--sandbox",
        "-C",
        "--cd",
        "--add-dir",
        "-a",
        "--ask-for-approval",
    )
)
_FLAGS = frozenset(("--oss", "--search", "--no-alt-screen", "--strict-config"))
_SUBCOMMANDS = frozenset(
    (
        "exec",
        "e",
        "review",
        "login",
        "logout",
        "mcp",
        "plugin",
        "mcp-server",
        "app-server",
        "remote-control",
        "app",
        "completion",
        "update",
        "doctor",
        "sandbox",
        "debug",
        "apply",
        "a",
        "resume",
        "archive",
        "delete",
        "unarchive",
        "fork",
        "cloud",
        "exec-server",
        "features",
        "help",
    )
)


def validate_interactive_command(command: list[str], *, has_task: bool) -> None:
    """Accept only invocation shapes verified for a new, local interactive session."""
    args = iter(command[1:])
    positional = False
    for arg in args:
        option, equals, value = arg.partition("=")
        if option in _VALUE_OPTIONS:
            if not (value if equals else next(args, "")):
                raise ValueError("Missing option value for interactive Codex")
        elif arg in _FLAGS:
            continue
        elif arg == "--" and not has_task:
            remaining = list(args)
            if len(remaining) > 1 or positional:
                raise ValueError("Expected one interactive Codex prompt")
            return
        elif (
            not has_task
            and not arg.startswith("-")
            and not positional
            and arg not in _SUBCOMMANDS
        ):
            positional = True
        else:
            raise ValueError(
                "Unsupported interactive Codex invocation: use a new session with "
                "documented options; omit subcommands and, with --task-file, any "
                "additional prompt. Use generic run for other commands."
            )


def new_task_delivery(digest: str) -> TaskDelivery:
    return TaskDelivery(
        mode="codex_interactive_argv",
        artifact_sha256=digest,
        boundary="argv",
        limitations=[
            "Confirmation observes only process launch with the prepared argv; "
            "Codex/model receipt and understanding are unobservable.",
            "The executable is selected by the user, not authenticated by PatchTrace.",
            "The prompt is visible in process arguments and subject to OS argument-size limits.",
        ],
    )


def prepare_task_command(
    command: list[str], artifact: Path, digest: str
) -> tuple[list[str], TaskDelivery]:
    validate_interactive_command(command, has_task=True)
    raw = artifact.read_bytes()
    if sha256(raw).hexdigest() != digest:
        raise ValueError("Preserved task digest changed; inspect task.md and rerun")
    prompt = raw.decode(
        "utf-8"
    )  # No BOM stripping, newline conversion, or parse rendering.
    if "\0" in prompt:
        raise ValueError("NUL cannot be delivered in an interactive argv prompt")
    delivery = new_task_delivery(digest)
    delivery.prompt_sha256 = sha256(prompt.encode("utf-8")).hexdigest()
    return [*command, "--", prompt], delivery
