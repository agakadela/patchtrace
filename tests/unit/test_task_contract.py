from hashlib import sha256
from pathlib import Path

import pytest

from patchtrace.task.contract import parse_task

FIXTURES = Path(__file__).parents[1] / "fixtures" / "tasks"


def test_valid_task_has_source_bound_ordered_ids() -> None:
    raw = (FIXTURES / "valid.md").read_bytes()
    parsed = parse_task(raw, run_id="run-one")
    assert parsed.status == "valid"
    assert parsed.run_id == "run-one"
    assert parsed.sha256 == sha256(raw).hexdigest()
    assert parsed.contract is not None
    assert parsed.contract.outcome == "Preserve the developer’s task."
    assert [item.id for item in parsed.contract.requirements] == ["REQ-001", "REQ-002"]
    assert parsed.contract.requirements[0].text == "Keep the original bytes."
    assert parsed.contract.acceptance_criteria is not None
    assert parsed.contract.acceptance_criteria[0].id == "AC-001"
    assert parsed.contract.required_verification is not None
    assert parsed.contract.required_verification[0].id == "VER-001"
    assert parsed.contract.out_of_scope is not None
    assert parsed.contract.out_of_scope[0].id == "OOS-001"
    assert parse_task(raw, run_id="run-two").contract == parsed.contract


@pytest.mark.parametrize("name, expected", [("minimal", None), ("na", [])])
def test_optional_sections_allow_omission_or_explicit_na(
    name: str, expected: list[object] | None
) -> None:
    parsed = parse_task((FIXTURES / f"{name}.md").read_bytes(), run_id="run")
    assert parsed.status == "valid"
    assert parsed.contract is not None
    assert parsed.contract.acceptance_criteria == expected
    assert parsed.contract.required_verification == expected
    assert parsed.contract.out_of_scope == expected


@pytest.mark.parametrize("name", ["invalid", "duplicate"])
def test_invalid_material_is_not_silently_rewritten(name: str) -> None:
    raw = (FIXTURES / f"{name}.md").read_bytes()
    parsed = parse_task(raw, run_id="run")
    assert parsed.status == "invalid"
    assert parsed.contract is None
    assert parsed.errors
    assert parsed.sha256 == sha256(raw).hexdigest()


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"\xff",
        b"## Outcome\nN/A\n## Requirements\n1. Do it.\n",
        b"## Requirements\n1. Do it.\n",
        b"## Outcome\nDo it.\n",
        b"## Outcome\nDo it.\n## Requirements\nN/A\n",
        b"## Outcome\nDo it.\n## Requirements\n1. \n",
        b"## Outcome\nDo it.\n## Requirements\n1. Do it.\n## Extra\nignored?\n",
        b"## Outcome\nDo it.\n## Requirements\n1. Do it.\n  1. Nested\n",
        b"```\n## Outcome\nDo it.\n## Requirements\n1. Fake\n```\n",
        b"## Outcome\nDo it.\n## Requirements\n1. Do it.\n## Out of Scope\n",
    ],
)
def test_invalid_syntax_returns_diagnostic(raw: bytes) -> None:
    result = parse_task(raw, run_id="run")
    assert result.status == "invalid"
    assert result.contract is None
    assert result.errors


def test_ids_follow_position_not_markdown_numbers() -> None:
    parsed = parse_task(
        b"## Outcome\nDo it.\n## Requirements\n7. First\n7) Second\n", run_id="run"
    )
    assert parsed.contract is not None
    assert [item.id for item in parsed.contract.requirements] == ["REQ-001", "REQ-002"]


@pytest.mark.parametrize("status, errors", [("valid", []), ("invalid", [])])
def test_parse_result_cannot_claim_validity_without_contract_or_error(
    status: str, errors: list[str]
) -> None:
    from pydantic import ValidationError

    from patchtrace.task.contract import ParsedTask

    with pytest.raises(ValidationError):
        ParsedTask.model_validate(
            {
                "run_id": "run",
                "sha256": "a" * 64,
                "status": status,
                "contract": None,
                "errors": errors,
            }
        )
