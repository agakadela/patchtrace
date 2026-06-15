import { describe, expect, it } from "vitest";

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
  it("prints analyze help without running analysis", () => {
    const buffered = createBufferedIo();

    const exitCode = main(["analyze", "--help"], buffered.io);

    expect(exitCode).toBe(0);
    expect(buffered.stdout()).toContain("Usage: patchtrace analyze");
    expect(buffered.stdout()).toContain("--summary <path>");
    expect(buffered.stdout()).toContain("--test-output <path>");
    expect(buffered.stdout()).toContain("Analysis is not implemented in this scaffold yet.");
    expect(buffered.stderr()).toBe("");
  });
});
