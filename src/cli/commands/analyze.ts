import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

import type { CliIo } from "../io.js";
import { LocalMaterialReadError, readSavedMaterials } from "../../modules/evidence/local-materials.js";
import { buildBriefShellInput, renderBriefShell } from "../../modules/report/brief-shell.js";

interface AnalyzeOptions {
  base?: string;
  changedFiles?: string;
  diff?: string;
  head?: string;
  out?: string;
  summary?: string;
  testOutput?: string;
}

type AnalyzeOptionName = keyof AnalyzeOptions;

interface RequiredMaterialOptions {
  changedFiles: string;
  diff: string;
  out: string;
  summary: string;
  testOutput?: string;
}

interface AnalyzeOptionError {
  error: string;
}

class VerificationBriefWriteError extends Error {
  constructor(path: string, causeMessage: string) {
    super(`Could not write verification brief to ${path}: ${causeMessage}`);
    this.name = "VerificationBriefWriteError";
  }
}

const optionNames = new Map<string, AnalyzeOptionName>([
  ["--base", "base"],
  ["--changed-files", "changedFiles"],
  ["--diff", "diff"],
  ["--head", "head"],
  ["--out", "out"],
  ["--summary", "summary"],
  ["--test-output", "testOutput"],
]);

export function buildAnalyzeHelp(): string {
  return [
    "Usage: patchtrace analyze [options]",
    "",
    "Generate a VERIFICATION_BRIEF.md from local patch material.",
    "Reads saved patch material and writes a conservative Markdown brief shell.",
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

function parseAnalyzeOptions(args: string[]): { options: AnalyzeOptions } | AnalyzeOptionError {
  const options: AnalyzeOptions = {};

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    const optionName = optionNames.get(arg);

    if (!optionName) {
      return { error: `Unknown analyze option: ${arg}` };
    }

    const value = args[index + 1];

    if (!value || value.startsWith("--")) {
      return { error: `Missing value for ${arg}` };
    }

    options[optionName] = value;
    index += 1;
  }

  return { options };
}

function requireOption(options: AnalyzeOptions, optionName: AnalyzeOptionName, flag: string): string | AnalyzeOptionError {
  const value = options[optionName];

  if (!value) {
    return { error: `Missing required option ${flag}` };
  }

  return value;
}

function isAnalyzeOptionError(value: string | AnalyzeOptionError): value is AnalyzeOptionError {
  return typeof value !== "string";
}

function resolveRequiredMaterialOptions(options: AnalyzeOptions): RequiredMaterialOptions | AnalyzeOptionError {
  const diff = requireOption(options, "diff", "--diff");
  if (isAnalyzeOptionError(diff)) {
    return diff;
  }

  const changedFiles = requireOption(options, "changedFiles", "--changed-files");
  if (isAnalyzeOptionError(changedFiles)) {
    return changedFiles;
  }

  const summary = requireOption(options, "summary", "--summary");
  if (isAnalyzeOptionError(summary)) {
    return summary;
  }

  const out = requireOption(options, "out", "--out");
  if (isAnalyzeOptionError(out)) {
    return out;
  }

  return {
    changedFiles,
    diff,
    out,
    summary,
    testOutput: options.testOutput,
  };
}

function formatUnknownError(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return "unknown filesystem error";
}

function writeVerificationBrief(path: string, brief: string): void {
  try {
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, brief, "utf8");
  } catch (error) {
    throw new VerificationBriefWriteError(path, formatUnknownError(error));
  }
}

export function runAnalyze(args: string[], io: CliIo): number {
  if (args.includes("--help") || args.includes("-h")) {
    io.stdout.write(`${buildAnalyzeHelp()}\n`);
    return 0;
  }

  const parsedOptions = parseAnalyzeOptions(args);

  if ("error" in parsedOptions) {
    io.stderr.write(`${parsedOptions.error}\n\n${buildAnalyzeHelp()}\n`);
    return 1;
  }

  const materialOptions = resolveRequiredMaterialOptions(parsedOptions.options);

  if ("error" in materialOptions) {
    io.stderr.write(`${materialOptions.error}\n\n${buildAnalyzeHelp()}\n`);
    return 1;
  }

  try {
    const materials = readSavedMaterials({
      changedFiles: materialOptions.changedFiles,
      diff: materialOptions.diff,
      summary: materialOptions.summary,
      testOutput: materialOptions.testOutput,
    });
    const brief = renderBriefShell(buildBriefShellInput(materials));

    writeVerificationBrief(materialOptions.out, brief);
    io.stdout.write(`Wrote verification brief to ${materialOptions.out}\n`);

    return 0;
  } catch (error) {
    if (error instanceof LocalMaterialReadError) {
      io.stderr.write(`${error.message}\n`);
      return 1;
    }

    if (error instanceof VerificationBriefWriteError) {
      io.stderr.write(`${error.message}\n`);
      return 1;
    }

    throw error;
  }
}
