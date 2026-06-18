import { z } from "zod";

import { assessAgentClaims, type AgentClaimAssessment } from "../claims/claim-analysis.js";
import type { ReviewedInput, SavedMaterials } from "../evidence/local-materials.js";
import { analyzeRiskAndReviewFirst, type ReviewFirstTarget, type RiskArea } from "../risk/risk-analysis.js";
import { assessTestQuality, type TestQualityAssessment } from "../test-quality/test-quality-analysis.js";

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

const AgentClaimAssessmentSchema = z.object({
  claim: z.string().min(1),
  support: z.enum(["supported", "partially_supported", "unsupported", "contradicted", "cannot_determine"]),
  assessment: z.string().min(1),
});

const TestQualityAssessmentSchema = z.object({
  observedCommand: z.string().min(1).optional(),
  result: z.enum(["pass", "fail", "missing", "unknown"]),
  evidenceSummary: z.string().min(1),
  appearsToProve: z.array(z.string().min(1)),
  weakOrMissing: z.array(z.string().min(1)),
});

const BriefShellInputSchema = z.object({
  agentClaims: z.array(AgentClaimAssessmentSchema),
  changedFiles: z.array(z.string()),
  inputsReviewed: z.array(ReviewedInputSchema).min(1),
  reviewFirst: z.array(ReviewFirstTargetSchema),
  riskAreas: z.array(RiskAreaSchema),
  testQuality: TestQualityAssessmentSchema,
});

export interface BriefShellInput {
  agentClaims: AgentClaimAssessment[];
  changedFiles: string[];
  inputsReviewed: ReviewedInput[];
  reviewFirst: ReviewFirstTarget[];
  riskAreas: RiskArea[];
  testQuality: TestQualityAssessment;
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

function formatAgentClaims(agentClaims: AgentClaimAssessment[]): string[] {
  if (agentClaims.length === 0) {
    return [
      "## Agent claims and support",
      "",
      "No explicit agent claims were extracted from the provided summary.",
      "",
    ];
  }

  return [
    "## Agent claims and support",
    "",
    "| Agent claim | Support | Evidence-backed assessment |",
    "|---|---|---|",
    ...agentClaims.map((claim) => `| ${claim.claim} | ${claim.support} | ${claim.assessment} |`),
    "",
  ];
}

function formatTestQuality(testQuality: TestQualityAssessment): string[] {
  const commandLines = testQuality.observedCommand
    ? ["Observed test command:", "", "```text", testQuality.observedCommand, "```", ""]
    : ["Observed test command: not provided.", ""];

  return [
    "## Test quality",
    "",
    ...commandLines,
    `Result: ${testQuality.result}.`,
    "",
    testQuality.evidenceSummary,
    "",
    "What the test evidence appears to prove:",
    "",
    ...(testQuality.appearsToProve.length === 0
      ? ["- No behavioral proof was identified from the provided test evidence."]
      : testQuality.appearsToProve.map((item) => `- ${item}`)),
    "",
    "What remains weak or missing:",
    "",
    ...testQuality.weakOrMissing.map((item) => `- ${item}`),
    "",
  ];
}

export function buildBriefShellInput(materials: SavedMaterials): BriefShellInput {
  const riskAnalysis = analyzeRiskAndReviewFirst({
    changedFiles: materials.changedFiles,
    diffText: materials.diffText,
  });

  return {
    agentClaims: assessAgentClaims({
      diffText: materials.diffText,
      summaryText: materials.summaryText,
      testOutputText: materials.testOutputText,
    }),
    changedFiles: materials.changedFiles,
    inputsReviewed: materials.inputsReviewed,
    reviewFirst: riskAnalysis.reviewFirst,
    riskAreas: riskAnalysis.riskAreas,
    testQuality: assessTestQuality({
      diffText: materials.diffText,
      summaryText: materials.summaryText,
      testOutputText: materials.testOutputText,
    }),
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
    "This brief confirms PatchTrace read the provided local material and generated deterministic risk, claim-support, test-quality, and review-first guidance. Cannot-verify analysis will be filled by a later analyzer slice.",
    "",
    "## Inputs reviewed",
    "",
    ...parsed.inputsReviewed.map(formatInput),
    "",
    "## Changed files",
    "",
    ...formatChangedFiles(parsed.changedFiles),
    "",
    ...formatAgentClaims(parsed.agentClaims),
    ...formatRiskAreas(parsed.riskAreas),
    ...formatTestQuality(parsed.testQuality),
    ...formatReviewFirst(parsed.reviewFirst),
  ].join("\n");
}
