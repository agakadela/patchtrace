import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const repoRoot = process.cwd();
const workflowPath = join(repoRoot, ".github", "workflows", "ci.yml");
const legacyWorkflowPath = join(repoRoot, "workflows", "ci.yml");

describe("CI workflow", () => {
  it("runs the foundation checks with pnpm from the standard GitHub Actions path", () => {
    expect(existsSync(workflowPath)).toBe(true);
    expect(existsSync(legacyWorkflowPath)).toBe(false);

    const workflow = readFileSync(workflowPath, "utf8");

    expect(workflow).toContain("actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5");
    expect(workflow).toContain("pnpm/action-setup@b906affcce14559ad1aafd4ab0e942779e9f58b1");
    expect(workflow).toContain("actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020");
    expect(workflow).toContain("cache: pnpm");
    expect(workflow).toContain("pnpm install --frozen-lockfile");
    expect(workflow).toContain("pnpm lint");
    expect(workflow).toContain("pnpm typecheck");
    expect(workflow).toContain("pnpm test");
    expect(workflow).toContain("pnpm build");
  });
});
