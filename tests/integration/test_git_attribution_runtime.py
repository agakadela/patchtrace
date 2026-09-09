from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from typer.testing import CliRunner

from patchtrace.analysis.analyzer import analyze_run
from patchtrace.cli.app import app
from patchtrace.models.report import AnalysisResult
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


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.mark.parametrize(
    ("scenario", "expected"),
    [
        ("clean", {("final", "tracked.txt", "session-attributed")}),
        (
            "unchanged-dirty",
            {
                ("initial", "tracked.txt", "pre-existing"),
                ("final", "tracked.txt", "pre-existing"),
            },
        ),
        (
            "dirty-same-path",
            {
                ("initial", "tracked.txt", "pre-existing"),
                ("final", "tracked.txt", "indeterminate"),
            },
        ),
        ("new-untracked", {("final", "new.txt", "session-attributed")}),
        ("committed", {("commit", "tracked.txt", "session-attributed")}),
        (
            "partial-commit",
            {
                ("initial", "tracked.txt", "pre-existing"),
                ("final", "tracked.txt", "indeterminate"),
                ("commit", "tracked.txt", "indeterminate"),
            },
        ),
        ("commit-revert", {("commit", "tracked.txt", "session-attributed")}),
        ("rewrite", {("history", None, "indeterminate")}),
    ],
)
def test_cli_git_attribution_matrix(
    tmp_path: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
    scenario: str,
    expected: set[tuple[str, str | None, str]],
) -> None:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.name", "PatchTrace Test")
    git(tmp_path, "config", "user.email", "patchtrace-test@example.com")
    (tmp_path / "tracked.txt").write_text("baseline\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "initial")
    if scenario in {"unchanged-dirty", "dirty-same-path", "partial-commit"}:
        (tmp_path / "tracked.txt").write_text("pre-existing\n")
    if scenario == "partial-commit":
        git(tmp_path, "add", "tracked.txt")

    script = ["from pathlib import Path", "import subprocess"]
    if scenario in {"clean", "dirty-same-path", "committed", "commit-revert"}:
        script.append("Path('tracked.txt').write_text('session edit\\n')")
    if scenario == "new-untracked":
        script.append("Path('new.txt').write_bytes(b'new\\x00bytes')")
    if scenario in {"committed", "partial-commit", "commit-revert"}:
        script.append(
            "subprocess.run(['git', 'commit', '-am', 'session commit'], check=True)"
        )
    if scenario == "partial-commit":
        script.append("Path('tracked.txt').write_text('later session edit\\n')")
    if scenario == "commit-revert":
        script.extend(
            [
                "Path('tracked.txt').write_text('baseline\\n')",
                "subprocess.run(['git', 'commit', '-am', 'revert'], check=True)",
            ]
        )
    if scenario == "rewrite":
        script.append(
            "subprocess.run(['git', 'commit', '--amend', '-m', 'rewrite'], check=True)"
        )
    script.append("print('• Final answer:\\nDone.')")
    monkeypatch.chdir(tmp_path)
    output = CliRunner().invoke(
        app, ["run", "--", sys.executable, "-c", "; ".join(script)]
    )
    assert output.exit_code == 0, output.output
    manifest_path = next(run_storage.rglob("run.json"))
    manifest = RunManifest.model_validate_json(manifest_path.read_text())
    result = analyze_run(manifest, run_dir=manifest_path.parent)
    result = AnalysisResult.model_validate_json(result.model_dump_json())
    assert {
        (item.material, item.path, item.attribution)
        for item in result.git_attribution.items
    } == expected
    if scenario == "commit-revert":
        assert len(result.git_attribution.items) == 2
    # Every source locator resolves within the exact captured JSON artifact.
    envelope = json.loads((manifest_path.parent / "git-session.json").read_text())
    for item in result.git_attribution.items:
        for ref in item.evidence_references:
            assert ref.artifact_path == "git-session.json"
            value = envelope
            for segment in ref.locator.lstrip("/").split("/"):
                value = (
                    value[int(segment)] if isinstance(value, list) else value[segment]
                )

    reports = [
        (manifest_path.parent / name).read_text()
        for name in ("SUMMARY.md", "AGENT_FEEDBACK.md", "VERIFICATION_BRIEF.md")
    ]
    # Completed analysis is sufficient even when the source artifacts disappear.
    for name in (
        "agent-session.txt",
        "git-session.json",
        "changed-files.txt",
        "git-before.txt",
        "git-after.txt",
        "patch.diff",
    ):
        (manifest_path.parent / name).unlink()
    assert reports == [
        render_summary_markdown(build_summary_report(manifest, analysis_result=result)),
        render_agent_feedback_markdown(
            build_agent_feedback_report(manifest, analysis_result=result)
        ),
        render_verification_brief_markdown(
            build_verification_brief_report(manifest, analysis_result=result)
        ),
    ]
    sections = [
        report.split("Git attribution:\n", 1)[1].split("\n\n", 1)[0]
        for report in reports
    ]
    assert sections[0] == sections[1] == sections[2]
    counts = Counter(item.attribution for item in result.git_attribution.items)
    for label in ("session-attributed", "pre-existing", "indeterminate"):
        assert f"{label}: {counts[label]} observation(s)." in sections[0]
    for item in result.git_attribution.items:
        assert f"[{item.attribution}] {item.material}:" in sections[0]
        if item.path is not None:
            assert f"`{item.path}`" in sections[0]
        if item.commit_head is not None:
            assert f"commit `{item.commit_head}`" in sections[0]
        for ref in item.evidence_references:
            assert f"`{ref.artifact_path}` (`{ref.locator}`)" in sections[0]
        for limitation in item.limitations:
            assert limitation in sections[0]
    for limitation in result.git_attribution.limitations:
        assert limitation in sections[0]
    for report in reports:
        assert "Changed Files" not in report
        assert "Changed files:" not in report
        if scenario in {"committed", "commit-revert", "rewrite"}:
            assert "No captured file changes require review." not in report
    if scenario == "unchanged-dirty":
        assert "[session-attributed]" not in sections[0]
        assert "Keep pre-existing material separate from session changes" in reports[2]


@pytest.mark.parametrize("quote_path", ["true", "false"])
def test_unusual_tracked_paths_and_binary_material(
    tmp_path: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
    quote_path: str,
) -> None:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.name", "PatchTrace Test")
    git(tmp_path, "config", "user.email", "patchtrace-test@example.com")
    git(tmp_path, "config", "core.quotePath", quote_path)
    names = ["space and b/slash.txt", 'żółć "quote" tab\t newline\n.txt', "binary.bin"]
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"before\x00\xff")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "initial")
    script = (
        "from pathlib import Path; "
        + "; ".join(f"Path({name!r}).write_bytes(b'after\\x00\\xff')" for name in names)
        + "; import subprocess; subprocess.run(['git', 'commit', '-am', 'change'], check=True)"
    )
    monkeypatch.chdir(tmp_path)
    output = CliRunner().invoke(app, ["run", "--", sys.executable, "-c", script])
    assert output.exit_code == 0, output.output
    manifest_path = next(run_storage.rglob("run.json"))
    result = analyze_run(
        RunManifest.model_validate_json(manifest_path.read_text()),
        run_dir=manifest_path.parent,
    )
    assert {
        (item.material, item.path, item.attribution)
        for item in result.git_attribution.items
    } == {("commit", name, "session-attributed") for name in names}


@pytest.mark.parametrize(
    "change", ["no-prefix", "mnemonic-prefix", "type-change", "empty-commit"]
)
def test_captured_git_variants_keep_attribution(
    tmp_path: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.name", "PatchTrace Test")
    git(tmp_path, "config", "user.email", "patchtrace-test@example.com")
    (tmp_path / "tracked.txt").write_text("baseline\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "initial")
    if change in {"no-prefix", "mnemonic-prefix"}:
        git(
            tmp_path,
            "config",
            "diff.noprefix" if change == "no-prefix" else "diff.mnemonicPrefix",
            "true",
        )
        (tmp_path / "tracked.txt").write_text("old work\n")
    if change == "type-change":
        script = "from pathlib import Path; Path('tracked.txt').unlink(); Path('tracked.txt').symlink_to('target')"
    elif change == "empty-commit":
        script = "import subprocess; subprocess.run(['git', 'commit', '--allow-empty', '-m', 'empty'], check=True)"
    else:
        script = "print('no edits')"
    monkeypatch.chdir(tmp_path)
    output = CliRunner().invoke(app, ["run", "--", sys.executable, "-c", script])
    assert output.exit_code == 0, output.output
    manifest_path = next(run_storage.rglob("run.json"))
    result = analyze_run(
        RunManifest.model_validate_json(manifest_path.read_text()),
        run_dir=manifest_path.parent,
    )
    items = result.git_attribution.items
    if change in {"no-prefix", "mnemonic-prefix"}:
        assert len(items) == 2
        assert {item.attribution for item in items} == {"pre-existing"}
    else:
        assert len(items) == 1
        assert items[0].attribution == "session-attributed"
        assert items[0].path == (None if change == "empty-commit" else "tracked.txt")
        assert items[0].material == ("commit" if change == "empty-commit" else "final")


def test_equal_custom_prefixes_cannot_hide_initial_untracked_material(
    tmp_path: Path,
    run_storage: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.name", "PatchTrace Test")
    git(tmp_path, "config", "user.email", "patchtrace-test@example.com")
    git(tmp_path, "commit", "--allow-empty", "-m", "initial")
    git(tmp_path, "config", "diff.srcPrefix", "same/")
    git(tmp_path, "config", "diff.dstPrefix", "same/")
    (tmp_path / "pre-existing.txt").write_text("prior work\n")
    monkeypatch.chdir(tmp_path)
    script = "import subprocess; subprocess.run(['git', 'add', 'pre-existing.txt'], check=True); subprocess.run(['git', 'commit', '-m', 'session'], check=True)"
    output = CliRunner().invoke(app, ["run", "--", sys.executable, "-c", script])
    assert output.exit_code == 0, output.output
    manifest_path = next(run_storage.rglob("run.json"))
    result = analyze_run(
        RunManifest.model_validate_json(manifest_path.read_text()),
        run_dir=manifest_path.parent,
    )
    assert {
        (item.material, item.path, item.attribution)
        for item in result.git_attribution.items
    } == {
        ("initial", "pre-existing.txt", "pre-existing"),
        ("commit", "pre-existing.txt", "indeterminate"),
    }
