import { readFileSync } from "node:fs";
import { basename } from "node:path";

import { parseChangedFiles } from "../patch/changed-files.js";

export interface LocalMaterialPaths {
  diff: string;
  changedFiles: string;
  summary: string;
  testOutput?: string;
}

export interface ReviewedInput {
  option: "--diff" | "--changed-files" | "--summary" | "--test-output";
  path: string;
  fileName: string;
  bytes: number;
  lineCount: number;
}

export interface SavedMaterials {
  diffText: string;
  changedFilesText: string;
  changedFiles: string[];
  summaryText: string;
  testOutputText?: string;
  inputsReviewed: ReviewedInput[];
}

export class LocalMaterialReadError extends Error {
  readonly option: ReviewedInput["option"];
  readonly path: string;
  readonly reason: "not-found" | "unreadable";

  constructor(option: ReviewedInput["option"], path: string, reason: "not-found" | "unreadable") {
    super(
      reason === "not-found"
        ? `Input file not found for ${option}: ${path}`
        : `Input file is not readable for ${option}: ${path}`,
    );
    this.name = "LocalMaterialReadError";
    this.option = option;
    this.path = path;
    this.reason = reason;
  }
}

function countLines(text: string): number {
  if (text.length === 0) {
    return 0;
  }

  const lines = text.split(/\r?\n/);

  if (lines.at(-1) === "") {
    return lines.length - 1;
  }

  return lines.length;
}

function readMaterial(option: ReviewedInput["option"], path: string) {
  try {
    const text = readFileSync(path, "utf8");

    return {
      input: {
        option,
        path,
        fileName: basename(path),
        bytes: Buffer.byteLength(text, "utf8"),
        lineCount: countLines(text),
      },
      text,
    };
  } catch (error) {
    if (error && typeof error === "object" && "code" in error && error.code === "ENOENT") {
      throw new LocalMaterialReadError(option, path, "not-found");
    }

    throw new LocalMaterialReadError(option, path, "unreadable");
  }
}

export function readSavedMaterials(paths: LocalMaterialPaths): SavedMaterials {
  const diff = readMaterial("--diff", paths.diff);
  const changedFiles = readMaterial("--changed-files", paths.changedFiles);
  const summary = readMaterial("--summary", paths.summary);
  const optionalTestOutput = paths.testOutput ? readMaterial("--test-output", paths.testOutput) : undefined;

  return {
    diffText: diff.text,
    changedFilesText: changedFiles.text,
    changedFiles: parseChangedFiles(changedFiles.text),
    summaryText: summary.text,
    testOutputText: optionalTestOutput?.text,
    inputsReviewed: [diff.input, changedFiles.input, summary.input, optionalTestOutput?.input].filter(
      (input): input is ReviewedInput => Boolean(input),
    ),
  };
}
