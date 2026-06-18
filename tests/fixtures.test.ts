import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { readSavedMaterials } from "../src/modules/evidence/local-materials.js";
import { buildBriefShellInput, renderBriefShell } from "../src/modules/report/brief-shell.js";

const repoRoot = process.cwd();
const fixturesRoot = join(repoRoot, "evals", "fixtures");

const expectedFixtures = [
  {
    name: "payment-webhook-idempotency",
    signals: [
      "Duplicate webhook claim: partially supported",
      "Weak or missing duplicate-event test evidence",
      "Payment/webhook/access risk",
      "Cannot verify Stripe production settings",
      "Review first",
      "Conservative verdict: needs_human_review",
    ],
  },
  {
    name: "auth-session-ownership",
    signals: [
      "Auth/session ownership claim: partially supported",
      "Cannot verify server-side ownership enforcement",
      "Access-control risk",
      "Manual two-user test is missing",
      "Conservative verdict: needs_human_review",
    ],
  },
  {
    name: "weak-or-missing-test-claim-evidence",
    signals: [
      "Test coverage claim: weak",
      "Cannot verify behavior from typecheck-only evidence",
      "Weak or missing behavioral test evidence",
      "Review first",
      "Conservative verdict: insufficient_material",
    ],
  },
  {
    name: "failed-tests-agent-done",
    signals: [
      "Agent done claim: contradicted",
      "Failed test evidence",
      "Cannot verify completion while tests are failing",
      "Review first",
      "Conservative verdict: send_agent_back",
    ],
  },
  {
    name: "ai-endpoint-missing-usage-rate-limits",
    signals: [
      "AI endpoint safety claim: unsupported",
      "Cannot verify usage or rate-limit controls",
      "AI cost/control risk",
      "Failure path is not evidenced",
      "Conservative verdict: needs_human_review",
    ],
  },
];

const requiredFixtureFiles = [
  "agent-summary.md",
  "changed-files.txt",
  "patch.diff",
  "test-output.txt",
  "notes.md",
  "VERIFICATION_BRIEF.md",
];

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
  it("discovers all five V0 fixture scenarios and their expected briefs", () => {
    expect(discoverFixtureNames()).toEqual(expectedFixtures.map((fixture) => fixture.name).sort());

    for (const fixture of expectedFixtures) {
      const fixturePath = join(fixturesRoot, fixture.name);

      for (const fileName of requiredFixtureFiles) {
        expect(existsSync(join(fixturePath, fileName)), `${fixture.name}/${fileName} should exist`).toBe(true);
      }

      const expectedBrief = readFileSync(join(fixturePath, "VERIFICATION_BRIEF.md"), "utf8");

      for (const signal of fixture.signals) {
        expect(expectedBrief, `${fixture.name} should contain ${signal}`).toContain(signal);
      }
    }
  });

  it("generates payment fixture risk areas and review-first guidance", () => {
    const paymentFixturePath = join(fixturesRoot, "payment-webhook-idempotency");
    const materials = readSavedMaterials({
      changedFiles: join(paymentFixturePath, "changed-files.txt"),
      diff: join(paymentFixturePath, "patch.diff"),
      summary: join(paymentFixturePath, "agent-summary.md"),
      testOutput: join(paymentFixturePath, "test-output.txt"),
    });

    const brief = renderBriefShell(buildBriefShellInput(materials));

    expect(brief).toContain("## Risk areas");
    expect(brief).toContain("Payment/webhook/access risk: `app/api/stripe/webhook/route.ts`");
    expect(brief).toContain("Entitlement risk: `src/lib/billing/entitlements.ts`");
    expect(brief).toContain("Idempotency-storage risk: `src/lib/billing/stripe-events.ts`");
    expect(brief).toContain("Test-quality risk: `tests/api/stripe-webhook.test.ts`");
    expect(brief).toContain("## Review first");
    expect(brief).toContain("1. `app/api/stripe/webhook/route.ts`");
    expect(brief).toContain("2. `src/lib/billing/stripe-events.ts`");
    expect(brief).toContain("3. `src/lib/billing/entitlements.ts`");
    expect(brief).toContain("4. `tests/api/stripe-webhook.test.ts`");
  });
});
