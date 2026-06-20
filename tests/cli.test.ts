import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
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
    expect(brief).toContain("## Agent claims and support");
    expect(brief).toContain("Duplicate Stripe webhooks do not double-grant paid access.");
    expect(brief).toContain("partially_supported");
    expect(brief).toContain("## Test quality");
    expect(brief).toContain("Weak or missing duplicate-event test evidence.");
  });

  it("derives payment risk and review-first guidance from changed paths and diff text", () => {
    const buffered = createBufferedIo();
    const tempDir = createTempDir();
    const outPath = join(tempDir, "VERIFICATION_BRIEF.md");
    const summaryPath = join(tempDir, "agent-summary.md");
    writeFileSync(summaryPath, "# Agent Summary\n\nEverything is done.\n", "utf8");

    const exitCode = main(
      [
        "analyze",
        "--diff",
        join(paymentFixture, "patch.diff"),
        "--changed-files",
        join(paymentFixture, "changed-files.txt"),
        "--summary",
        summaryPath,
        "--test-output",
        join(paymentFixture, "test-output.txt"),
        "--out",
        outPath,
      ],
      buffered.io,
    );

    expect(exitCode).toBe(0);
    expect(buffered.stderr()).toBe("");

    const brief = readFileSync(outPath, "utf8");
    expect(brief).toContain("No explicit agent claims were extracted from the provided summary.");
    expect(brief).not.toContain("Duplicate Stripe webhooks do not double-grant paid access.");
    expect(brief).toContain("## Risk areas");
    expect(brief).toContain(
      "Payment/webhook/access risk: `app/api/stripe/webhook/route.ts` accepts provider events and can grant paid access.",
    );
    expect(brief).toContain(
      "Entitlement risk: `src/lib/billing/entitlements.ts` updates plan state and customer linkage.",
    );
    expect(brief).toContain(
      "Idempotency-storage risk: `src/lib/billing/stripe-events.ts` records processed events but the diff does not show uniqueness or transactional guarantees.",
    );
    expect(brief).toContain(
      "Test-quality risk: `tests/api/stripe-webhook.test.ts` exercises the happy path and sequential duplicate path, but it does not demonstrate the highest-risk duplicate delivery cases.",
    );
    expect(brief).toContain("## Review first");
    expect(brief).toContain(
      "1. `app/api/stripe/webhook/route.ts` - confirm idempotency ordering, signature handling, error behavior, and whether duplicate event checks are race-safe.",
    );
    expect(brief).toContain(
      "2. `src/lib/billing/stripe-events.ts` - confirm `eventId` has a unique database constraint and that event recording is atomic with the entitlement decision or otherwise safe under retries.",
    );
    expect(brief).toContain(
      "3. `src/lib/billing/entitlements.ts` - confirm paid access updates are correct, auditable, and scoped to the intended user/customer mapping.",
    );
    expect(brief).toContain(
      "4. `tests/api/stripe-webhook.test.ts` - add or inspect tests for concurrent duplicates, database constraint behavior, realistic signed payloads, and partial-failure cases.",
    );
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

  it("writes an insufficient-material brief when patch material is missing", () => {
    const buffered = createBufferedIo();
    const outPath = join(createTempDir(), "VERIFICATION_BRIEF.md");

    const exitCode = main(
      [
        "analyze",
        "--summary",
        join(paymentFixture, "agent-summary.md"),
        "--out",
        outPath,
      ],
      buffered.io,
    );

    expect(exitCode).toBe(0);
    expect(buffered.stderr()).toBe("");
    expect(existsSync(outPath)).toBe(true);

    const brief = readFileSync(outPath, "utf8");
    expect(brief).toContain("Conservative verdict: insufficient_material");
    expect(brief).toContain("PatchTrace cannot analyze changed files or diff hunks because no saved patch material was provided.");
    expect(brief).toContain("--summary: `evals/fixtures/payment-webhook-idempotency/agent-summary.md`");
    expect(brief).toContain("No changed files were listed in the provided material.");
    expect(brief).toContain("Result: missing.");
    expect(brief).toContain("No test output was provided.");
    expect(brief).toContain("Add `--diff <path>` with a saved patch diff.");
    expect(brief).toContain("Add `--changed-files <path>` with the changed-file list for that diff.");
    expect(brief).toContain("Add `--test-output <path>` with the relevant test or command output.");
  });

  it("asks only for changed files when diff and test output are already provided", () => {
    const buffered = createBufferedIo();
    const outPath = join(createTempDir(), "VERIFICATION_BRIEF.md");

    const exitCode = main(
      [
        "analyze",
        "--diff",
        join(paymentFixture, "patch.diff"),
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

    const brief = readFileSync(outPath, "utf8");
    expect(brief).toContain("Conservative verdict: insufficient_material");
    expect(brief).toContain("--diff: `evals/fixtures/payment-webhook-idempotency/patch.diff`");
    expect(brief).toContain("--test-output: `evals/fixtures/payment-webhook-idempotency/test-output.txt`");
    expect(brief).toContain(
      "PatchTrace cannot complete saved-material analysis because the changed-file list is missing.",
    );
    expect(brief).toContain(
      "Cannot verify changed-file scope because `--changed-files <path>` was not provided with usable local material.",
    );
    expect(brief).toContain("Add `--changed-files <path>` with the changed-file list for that diff.");
    expect(brief).not.toContain("Cannot verify diff hunks because `--diff <path>` was not provided");
    expect(brief).not.toContain("Cannot verify test behavior because `--test-output <path>` was not provided.");
    expect(brief).not.toContain("Add `--diff <path>` with a saved patch diff.");
    expect(brief).not.toContain("Add `--test-output <path>` with the relevant test or command output.");
  });

  it("asks only for the diff when changed files and test output are already provided", () => {
    const buffered = createBufferedIo();
    const outPath = join(createTempDir(), "VERIFICATION_BRIEF.md");

    const exitCode = main(
      [
        "analyze",
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

    const brief = readFileSync(outPath, "utf8");
    expect(brief).toContain("Conservative verdict: insufficient_material");
    expect(brief).toContain("--changed-files: `evals/fixtures/payment-webhook-idempotency/changed-files.txt`");
    expect(brief).toContain("--test-output: `evals/fixtures/payment-webhook-idempotency/test-output.txt`");
    expect(brief).toContain("PatchTrace cannot complete saved-material analysis because the patch diff is missing.");
    expect(brief).toContain("Cannot verify diff hunks because `--diff <path>` was not provided with usable local material.");
    expect(brief).toContain("Add `--diff <path>` with a saved patch diff.");
    expect(brief).not.toContain("Cannot verify changed-file scope because `--changed-files <path>` was not provided");
    expect(brief).not.toContain("Cannot verify test behavior because `--test-output <path>` was not provided.");
    expect(brief).not.toContain("Add `--changed-files <path>` with the changed-file list for that diff.");
    expect(brief).not.toContain("Add `--test-output <path>` with the relevant test or command output.");
  });

  it("represents omitted test output as missing evidence", () => {
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
        "--out",
        outPath,
      ],
      buffered.io,
    );

    expect(exitCode).toBe(0);
    expect(buffered.stderr()).toBe("");

    const brief = readFileSync(outPath, "utf8");
    expect(brief).toContain("Result: missing.");
    expect(brief).toContain("No test output was provided.");
    expect(brief).toContain("Test output is missing, so PatchTrace cannot assess behavioral proof.");
    expect(brief).not.toContain("Result: pass.");
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
