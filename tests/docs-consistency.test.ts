import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const repoRoot = process.cwd();

function readRepoFile(path: string): string {
  return readFileSync(join(repoRoot, path), "utf8");
}

describe("project truth docs", () => {
  it("describe the current Phase 2 scaffold truthfully", () => {
    const plan = readRepoFile("docs/PLAN.md");
    const architecture = readRepoFile("docs/ARCHITECTURE.md");

    expect(plan).not.toContain("A placeholder CI file exists at `workflows/ci.yml`");
    expect(architecture).not.toContain("implementation has not been scaffolded yet");
    expect(architecture).not.toContain("init.ts");
  });

  it("documents lint as an active Phase 2 feedback loop", () => {
    const spec = readRepoFile("docs/SPEC.md");
    const adr = readRepoFile("docs/decisions/ADR-0001-project-foundation.md");
    const packageJson = JSON.parse(readRepoFile("package.json")) as {
      scripts?: Record<string, string>;
    };

    expect(packageJson.scripts?.lint).toBeDefined();
    expect(spec).toContain("pnpm lint");
    expect(adr).toContain("Lint: `pnpm lint` after scaffold.");
  });
});
