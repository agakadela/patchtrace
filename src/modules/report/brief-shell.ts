import { z } from "zod";

import type { ReviewedInput, SavedMaterials } from "../evidence/local-materials.js";
import { analyzeRiskAndReviewFirst, type ReviewFirstTarget, type RiskArea } from "../risk/risk-analysis.js";

const ReviewedInputSchema = z.object({
  option: z.enum(["--diff", "--changed-files", "--summary", "--test-output"]),
  path: z.string().min(1),
  fileName: z.string().min(1),
  bytes: z.number().int().nonnegative(),
  lineCount: z.number().int().nonnegative(),
});

const RiskAreaSchema = z.object({
  label: z.string().min(1),
  filePath: z.string().min(1),
  detail: z.string().min(1),
});

const ReviewFirstTargetSchema = z.object({
  filePath: z.string().min(1),
  guidance: z.string().min(1),
});

const BriefShellInputSchema = z.object({
  changedFiles: z.array(z.string()),
  inputsReviewed: z.array(ReviewedInputSchema).min(1),
  reviewFirst: z.array(ReviewFirstTargetSchema),
  riskAreas: z.array(RiskAreaSchema),
});

export interface BriefShellInput {
  changedFiles: string[];
  inputsReviewed: ReviewedInput[];
  reviewFirst: ReviewFirstTarget[];
  riskAreas: RiskArea[];
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

function formatRiskAreas(riskAreas: RiskArea[]): string[] {
  if (riskAreas.length === 0) {
    return [];
  }

  return ["## Risk areas", "", ...riskAreas.map((risk) => `- ${risk.label}: \`${risk.filePath}\` ${risk.detail}`), ""];
}

function formatReviewFirst(reviewFirst: ReviewFirstTarget[]): string[] {
  if (reviewFirst.length === 0) {
    return [];
  }

  return [
    "## Review first",
    "",
    ...reviewFirst.map((target, index) => `${index + 1}. \`${target.filePath}\` - ${target.guidance}`),
    "",
  ];
}

export function buildBriefShellInput(materials: SavedMaterials): BriefShellInput {
  const riskAnalysis = analyzeRiskAndReviewFirst({
    changedFiles: materials.changedFiles,
    diffText: materials.diffText,
  });

  return {
    changedFiles: materials.changedFiles,
    inputsReviewed: materials.inputsReviewed,
    reviewFirst: riskAnalysis.reviewFirst,
    riskAreas: riskAnalysis.riskAreas,
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
    "This brief confirms PatchTrace read the provided local material and generated the first deterministic risk and review-first guidance. Detailed claim-support, test-quality, and cannot-verify analysis will be filled by later analyzer slices.",
    "",
    "## Inputs reviewed",
    "",
    ...parsed.inputsReviewed.map(formatInput),
    "",
    "## Changed files",
    "",
    ...formatChangedFiles(parsed.changedFiles),
    "",
    ...formatRiskAreas(parsed.riskAreas),
    ...formatReviewFirst(parsed.reviewFirst),
  ].join("\n");
}
