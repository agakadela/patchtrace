import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

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
});
