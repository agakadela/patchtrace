import { existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import { main } from "../src/cli/index.js";

function createBufferedIo() {
  let stdout = "";
  let stderr = "";

  return {
    io: {
      stdout: {
        write(chunk: string) {
          stdout += chunk;
        },
      },
      stderr: {
        write(chunk: string) {
          stderr += chunk;
        },
      },
    },
    stdout: () => stdout,
    stderr: () => stderr,
  };
}

describe("patchtrace CLI", () => {
  const tempDirs: string[] = [];

  afterEach(() => {
    for (const dir of tempDirs.splice(0)) {
      rmSync(dir, { force: true, recursive: true });
    }
  });

  function createTempDir(): string {
    const dir = mkdtempSync(join(tmpdir(), "patchtrace-cli-"));
    tempDirs.push(dir);
    return dir;
  }

  const paymentFixture = join("evals", "fixtures", "payment-webhook-idempotency");

  it("prints analyze help without running analysis", () => {
    const buffered = createBufferedIo();

    const exitCode = main(["analyze", "--help"], buffered.io);

    expect(exitCode).toBe(0);
    expect(buffered.stdout()).toContain("Usage: patchtrace analyze");
    expect(buffered.stdout()).toContain("--summary <path>");
    expect(buffered.stdout()).toContain("--test-output <path>");
    expect(buffered.stdout()).toContain("Generate a VERIFICATION_BRIEF.md from local patch material.");
    expect(buffered.stderr()).toBe("");
  });

  it("writes a Markdown brief shell from saved fixture material", () => {
    const buffered = createBufferedIo();
    const outPath = join(createTempDir(), "VERIFICATION_BRIEF.md");

    const exitCode = main(
      [
        "analyze",
        "--diff",
        join(paymentFixture, "patch.diff"),
        "--changed-files",
        join(paymentFixture, "changed-files.txt"),
        "--summary",
        join(paymentFixture, "agent-summary.md"),
        "--test-output",
        join(paymentFixture, "test-output.txt"),
        "--out",
        outPath,
      ],
      buffered.io,
    );

    expect(exitCode).toBe(0);
    expect(buffered.stderr()).toBe("");
    expect(existsSync(outPath)).toBe(true);

    const brief = readFileSync(outPath, "utf8");
    expect(brief).toContain("# VERIFICATION_BRIEF.md");
    expect(brief).toContain("## Conservative verdict");
    expect(brief).toContain("## Inputs reviewed");
    expect(brief).toContain("patch.diff");
    expect(brief).toContain("changed-files.txt");
    expect(brief).toContain("agent-summary.md");
    expect(brief).toContain("test-output.txt");
    expect(brief).toContain("--changed-files: `evals/fixtures/payment-webhook-idempotency/changed-files.txt` (130 bytes, 4 lines)");
  });

  it("fails with an actionable error when a local input path is missing", () => {
    const buffered = createBufferedIo();
    const outPath = join(createTempDir(), "VERIFICATION_BRIEF.md");

    const exitCode = main(
      [
        "analyze",
        "--diff",
        join(paymentFixture, "missing.diff"),
        "--changed-files",
        join(paymentFixture, "changed-files.txt"),
        "--summary",
        join(paymentFixture, "agent-summary.md"),
        "--test-output",
        join(paymentFixture, "test-output.txt"),
        "--out",
        outPath,
      ],
      buffered.io,
    );

    expect(exitCode).toBe(1);
    expect(buffered.stderr()).toContain("Input file not found for --diff");
    expect(buffered.stderr()).toContain("evals/fixtures/payment-webhook-idempotency/missing.diff");
    expect(existsSync(outPath)).toBe(false);
  });

  it("fails with an actionable error when the output path cannot be written", () => {
    const buffered = createBufferedIo();
    const outPath = createTempDir();

    const exitCode = main(
      [
        "analyze",
        "--diff",
        join(paymentFixture, "patch.diff"),
        "--changed-files",
        join(paymentFixture, "changed-files.txt"),
        "--summary",
        join(paymentFixture, "agent-summary.md"),
        "--test-output",
        join(paymentFixture, "test-output.txt"),
        "--out",
        outPath,
      ],
      buffered.io,
    );

    expect(exitCode).toBe(1);
    expect(buffered.stdout()).toBe("");
    expect(buffered.stderr()).toContain(`Could not write verification brief to ${outPath}`);
  });
});
