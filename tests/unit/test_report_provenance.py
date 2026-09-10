from datetime import UTC, datetime

import pytest

from patchtrace.models.report import (
    AnalysisResult,
    EvidenceReference,
    GitAttribution,
    GitAttributionItem,
)
from patchtrace.models.run import RunManifest
from patchtrace.reports.feedback import (
    build_agent_feedback_report,
    render_agent_feedback_markdown,
)
from patchtrace.reports.summary import build_summary_report, render_summary_markdown
from patchtrace.reports.verification_brief import (
    build_verification_brief_report,
    render_verification_brief_markdown,
)


@pytest.mark.parametrize("with_items", [True, False])
def test_reports_preserve_shared_provenance_without_snapshot_fallback(
    with_items: bool,
) -> None:
    reference = EvidenceReference(
        artifact_path="git-session.json",
        locator="/before/paths/0",
        description="Captured initial material.",
    )
    items = [
        GitAttributionItem(
            material="initial",
            path="existing.txt",
            attribution="pre-existing",
            evidence_references=[reference],
            limitations=[],
        ),
        GitAttributionItem(
            material="final",
            path="existing.txt",
            attribution="indeterminate",
            evidence_references=[reference.model_copy(update={"locator": "/after"})],
            limitations=["Initial and later material cannot be separated."],
        ),
        GitAttributionItem(
            material="commit",
            path="session.txt",
            commit_head="abc123",
            attribution="session-attributed",
            evidence_references=[
                reference.model_copy(update={"locator": "/history/commits/0"})
            ],
            limitations=[],
        ),
        GitAttributionItem(
            material="commit",
            path=None,
            commit_head="def456",
            attribution="session-attributed",
            evidence_references=[
                reference.model_copy(update={"locator": "/history/commits/1"})
            ],
            limitations=["Empty commit does not establish file changes."],
        ),
        GitAttributionItem(
            material="history",
            path=None,
            attribution="indeterminate",
            evidence_references=[reference.model_copy(update={"locator": "/history"})],
            limitations=["History cannot be separated."],
        ),
    ]
    attribution = GitAttribution(
        items=items if with_items else [],
        limitations=[
            "Session attribution does not prove agent or byte-level authorship.",
            *([] if with_items else ["Attribution unavailable; rerun capture."]),
        ],
    )
    result = AnalysisResult(
        run_id="provenance",
        analysis_outcome="completed",
        claim_material_status="identified",
        claim_assessments=[],
        verdict="Review required.",
        most_important_gap="Human review remains necessary.",
        next_action="Review the evidence.",
        transcript_status="present",
        changed_files=["stale-snapshot-only.txt"],
        diff_material_status="present",
        command_test_signals=[],
        evidence_gaps=[],
        git_attribution=attribution,
    )
    now = datetime.now(UTC)
    manifest = RunManifest(
        capture_mode="codex_interactive",
        run_id=result.run_id,
        command=["fake"],
        trigger_source="manual_cli",
        started_at=now,
        ended_at=now,
        wrapped_command_exit_status=0,
        process_outcome="completed",
        analysis_outcome="not_run",
        package_outcome="partial",
        artifact_paths=["git-session.json"],
    )
    summary = build_summary_report(manifest, analysis_result=result)
    feedback = build_agent_feedback_report(manifest, analysis_result=result)
    brief = build_verification_brief_report(manifest, analysis_result=result)

    assert summary.git_attribution == feedback.git_attribution == brief.git_attribution
    assert summary.git_attribution == attribution
    sections = []
    for markdown in (
        render_summary_markdown(summary),
        render_agent_feedback_markdown(feedback),
        render_verification_brief_markdown(brief),
    ):
        assert "stale-snapshot-only.txt" not in markdown
        assert "Changed files:" not in markdown
        section = markdown.split("Git attribution:\n", 1)[1].split("\n\n", 1)[0]
        sections.append(section)
        for label, count in [
            ("session-attributed", 2),
            ("pre-existing", 1),
            ("indeterminate", 2),
        ]:
            assert f"{label}: {count if with_items else 0} observation(s)" in section
        assert "Counts describe material observations, not unique files." in section
        for limitation in attribution.limitations:
            assert limitation in section
        for item in attribution.items:
            assert f"[{item.attribution}] {item.material}" in section
            if item.path is not None:
                assert f"`{item.path}`" in section
            if item.commit_head is not None:
                assert f"`{item.commit_head}`" in section
            for ref in item.evidence_references:
                assert (
                    f"`{ref.artifact_path}` (`{ref.locator}`): {ref.description}"
                    in section
                )
            for limitation in item.limitations:
                assert limitation in section
    assert sections[0] == sections[1] == sections[2]
    targets = "\n".join(brief.review_first_targets)
    if with_items:
        assert "Review session-attributed material" in targets
        assert "Keep pre-existing material" in targets
        assert "Resolve indeterminate material" in targets
        assert "`existing.txt`" in targets
        assert "`session.txt`" in targets
        assert "`def456`" in targets
        assert "history range" in targets
    else:
        assert "Inspect Git attribution limitations" in targets
