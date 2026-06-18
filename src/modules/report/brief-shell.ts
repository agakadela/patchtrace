import { z } from "zod";

import type { ReviewedInput, SavedMaterials } from "../evidence/local-materials.js";

const ReviewedInputSchema = z.object({
  option: z.enum(["--diff", "--changed-files", "--summary", "--test-output"]),
  path: z.string().min(1),
  fileName: z.string().min(1),
  bytes: z.number().int().nonnegative(),
  lineCount: z.number().int().nonnegative(),
});

const BriefShellInputSchema = z.object({
  changedFiles: z.array(z.string()),
  inputsReviewed: z.array(ReviewedInputSchema).min(1),
});

export interface BriefShellInput {
  changedFiles: string[];
  inputsReviewed: ReviewedInput[];
}

function formatInput(input: ReviewedInput): string {
  return `- ${input.option}: \`${input.path}\` (${input.bytes} bytes, ${input.lineCount} lines)`;
}

function formatChangedFiles(changedFiles: string[]): string[] {
  if (changedFiles.length === 0) {
    return ["- No changed files were listed in the provided material."];
  }

  return changedFiles.map((filePath) => `- \`${filePath}\``);
}

export function buildBriefShellInput(materials: SavedMaterials): BriefShellInput {
  return {
    changedFiles: materials.changedFiles,
    inputsReviewed: materials.inputsReviewed,
  };
}

export function renderBriefShell(input: BriefShellInput): string {
  const parsed = BriefShellInputSchema.parse(input);

  return [
    "# VERIFICATION_BRIEF.md",
    "",
    "## Conservative verdict",
    "",
    "Conservative verdict: needs_human_review",
    "",
    "This brief shell confirms PatchTrace read the provided local material. Detailed risk, claim-support, test-quality, and cannot-verify analysis will be filled by later analyzer slices.",
    "",
    "## Inputs reviewed",
    "",
    ...parsed.inputsReviewed.map(formatInput),
    "",
    "## Changed files",
    "",
    ...formatChangedFiles(parsed.changedFiles),
    "",
  ].join("\n");
}
