from __future__ import annotations

import re
from hashlib import sha256
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TaskItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str = Field(min_length=1)


class TaskContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: str = Field(min_length=1)
    requirements: list[TaskItem] = Field(min_length=1)
    acceptance_criteria: list[TaskItem] | None
    required_verification: list[TaskItem] | None
    out_of_scope: list[TaskItem] | None


class ParsedTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    run_id: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal["valid", "invalid"]
    contract: TaskContract | None
    errors: list[str]

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if self.status == "valid":
            if self.contract is None or self.errors:
                raise ValueError("A valid parse requires a contract and no errors")
        elif self.contract is not None or not self.errors:
            raise ValueError("An invalid parse requires errors and no contract")
        return self


SECTIONS = (
    "Outcome",
    "Requirements",
    "Acceptance Criteria",
    "Required Verification",
    "Out of Scope",
)
_ITEM = re.compile(r"[0-9]+[.)][ \t]+(\S.*)")


def parse_task(raw: bytes, *, run_id: str) -> ParsedTask:
    """Parse the documented V1 subset; keep invalid input entirely unparsed."""
    digest = sha256(raw).hexdigest()
    try:
        # A UTF-8 BOM and line endings affect the digest, not parsed identifiers.
        text = raw.decode("utf-8-sig")
        sections: dict[str, list[str]] = {}
        current: str | None = None
        title_seen = False
        for number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            if line.startswith("## "):
                heading = line[3:].strip()
                if heading not in SECTIONS:
                    raise ValueError(f"Line {number}: unknown section {heading!r}")
                if heading in sections:
                    raise ValueError(f"Line {number}: duplicate section {heading!r}")
                current = heading
                sections[current] = []
            elif line.startswith("# ") and current is None and not title_seen:
                title_seen = True
            elif current is None or line.lstrip().startswith(("#", "```", "~~~")):
                raise ValueError(f"Line {number}: unsupported Task Contract V1 syntax")
            else:
                sections[current].append(line)
        outcome = "\n".join(sections.get("Outcome", [])).strip()
        if not outcome or outcome == "N/A":
            raise ValueError("Outcome requires non-empty text, not N/A")
        requirements = _items(sections, "Requirements", "REQ", required=True)
        assert requirements is not None
        contract = TaskContract(
            outcome=outcome,
            requirements=requirements,
            acceptance_criteria=_items(sections, "Acceptance Criteria", "AC"),
            required_verification=_items(sections, "Required Verification", "VER"),
            out_of_scope=_items(sections, "Out of Scope", "OOS"),
        )
    except (UnicodeError, ValueError) as error:
        return ParsedTask(
            run_id=run_id,
            sha256=digest,
            status="invalid",
            contract=None,
            errors=[str(error)],
        )
    return ParsedTask(
        run_id=run_id, sha256=digest, status="valid", contract=contract, errors=[]
    )


def _items(
    sections: dict[str, list[str]], heading: str, prefix: str, *, required: bool = False
) -> list[TaskItem] | None:
    lines = sections.get(heading)
    if lines is None and not required:
        return None
    if lines is None or not lines:
        raise ValueError(f"{heading} requires ordered items")
    if len(lines) == 1 and lines[0].strip() == "N/A" and not required:
        return []
    items: list[TaskItem] = []
    for line in lines:
        match = _ITEM.fullmatch(line)
        if match is None:
            raise ValueError(
                f"{heading}: expected a single-line ordered item: {line!r}"
            )
        items.append(
            TaskItem(id=f"{prefix}-{len(items) + 1:03d}", text=match[1].strip())
        )
    return items
