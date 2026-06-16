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

    expect(workflow).toContain("pnpm/action-setup@v4");
    expect(workflow).toContain("cache: pnpm");
    expect(workflow).toContain("pnpm install --frozen-lockfile");
    expect(workflow).toContain("pnpm typecheck");
    expect(workflow).toContain("pnpm test");
    expect(workflow).toContain("pnpm build");
  });
});
