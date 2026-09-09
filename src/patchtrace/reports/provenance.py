from collections import Counter

from patchtrace.models.report import (
    GitAttribution,
    GitAttributionClass,
    GitAttributionItem,
)

_ACTIONS: dict[GitAttributionClass, str] = {
    "session-attributed": "Review session-attributed material",
    "pre-existing": "Keep pre-existing material separate from session changes",
    "indeterminate": "Resolve indeterminate material using the cited sources before attributing it",
}


def render_git_attribution(attribution: GitAttribution) -> list[str]:
    """Present validated observations without interpreting Git evidence."""
    counts = Counter(item.attribution for item in attribution.items)
    lines = [
        "Git attribution:",
        "- Counts describe material observations, not unique files.",
    ]
    for label, action in _ACTIONS.items():
        lines.append(f"- {label}: {counts[label]} observation(s).")
        if counts[label]:
            lines.append(f"  - Next action: {action}.")
    for item in attribution.items:
        lines.append(f"- [{item.attribution}] {item.material}: {_subject(item)}")
        lines.extend(
            f"  - Source: `{ref.artifact_path}` (`{ref.locator}`): {ref.description}"
            for ref in item.evidence_references
        )
        lines.extend(f"  - Limitation: {limit}" for limit in item.limitations)
    if not attribution.items:
        lines.append(
            "- No attributed observations available; inspect limitations below."
        )
    lines.append("- Git attribution limitations:")
    lines.extend(f"  - {limit}" for limit in attribution.limitations)
    if not attribution.limitations:
        lines.append("  - None recorded.")
    return lines


def git_review_targets(attribution: GitAttribution) -> list[str]:
    if not attribution.items:
        return [
            "Inspect Git attribution limitations and source artifacts before choosing review targets."
        ]
    return [
        f"{_ACTIONS[item.attribution]}: {_subject(item)} ({item.material})."
        for item in attribution.items
    ]


def _subject(item: GitAttributionItem) -> str:
    if item.path is not None:
        subject = f"`{item.path}`"
    elif item.material == "history":
        subject = "history range (no path attribution)"
    else:
        subject = "no captured path changes"
    if item.commit_head is not None:
        subject += f"; commit `{item.commit_head}`"
    return subject
