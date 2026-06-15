import type { CliIo } from "../io.js";

export function buildAnalyzeHelp(): string {
  return [
    "Usage: patchtrace analyze [options]",
    "",
    "Generate a VERIFICATION_BRIEF.md from local patch material.",
    "Analysis is not implemented in this scaffold yet.",
    "",
    "Options:",
    "  --base <ref>            Base git ref to compare from",
    "  --head <ref>            Head git ref to compare to",
    "  --diff <path>           Saved patch diff to analyze",
    "  --changed-files <path>  Changed-file list to analyze",
    "  --summary <path>        Agent summary or session notes",
    "  --test-output <path>    Test or command output evidence",
    "  --out <path>            Markdown brief output path",
    "  -h, --help              Show analyze help",
  ].join("\n");
}

export function runAnalyze(args: string[], io: CliIo): number {
  if (args.includes("--help") || args.includes("-h")) {
    io.stdout.write(`${buildAnalyzeHelp()}\n`);
    return 0;
  }

  io.stderr.write(
    [
      "patchtrace analyze is scaffolded, but analysis is not implemented yet.",
      "Run `patchtrace analyze --help` for the planned local-input options.",
      "",
    ].join("\n"),
  );
  return 1;
}
