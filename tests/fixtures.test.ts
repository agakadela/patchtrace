import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const repoRoot = process.cwd();
const fixturesRoot = join(repoRoot, "evals", "fixtures");
const paymentWebhookFixture = "payment-webhook-idempotency";

function discoverFixtureNames(): string[] {
  if (!existsSync(fixturesRoot)) {
    return [];
  }

  return readdirSync(fixturesRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
}

describe("fixture discovery", () => {
  it("discovers the payment webhook idempotency fixture and expected brief", () => {
    expect(discoverFixtureNames()).toContain(paymentWebhookFixture);

    const fixturePath = join(fixturesRoot, paymentWebhookFixture);

    for (const fileName of [
      "agent-summary.md",
      "changed-files.txt",
      "patch.diff",
      "test-output.txt",
      "notes.md",
      "VERIFICATION_BRIEF.md",
    ]) {
      expect(existsSync(join(fixturePath, fileName)), `${fileName} should exist`).toBe(true);
    }

    const expectedBrief = readFileSync(join(fixturePath, "VERIFICATION_BRIEF.md"), "utf8");

    expect(expectedBrief).toContain("Duplicate webhook claim: partially supported");
    expect(expectedBrief).toContain("Weak or missing duplicate-event test evidence");
    expect(expectedBrief).toContain("Payment/webhook/access risk");
    expect(expectedBrief).toContain("Cannot verify Stripe production settings");
    expect(expectedBrief).toContain("Review first");
    expect(expectedBrief).toContain("Conservative verdict: needs_human_review");
  });
});
