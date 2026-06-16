#!/usr/bin/env node
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { z } from "zod";

import { runAnalyze } from "./commands/analyze.js";
import { processIo, type CliIo } from "./io.js";

const CommandNameSchema = z.enum(["analyze"]);

export function buildRootHelp(): string {
  return [
    "Usage: patchtrace <command> [options]",
    "",
    "Commands:",
    "  analyze  Generate a verification brief from local patch material",
    "",
    "Run `patchtrace analyze --help` for command options.",
  ].join("\n");
}

export function main(argv = process.argv.slice(2), io: CliIo = processIo): number {
  const [command, ...args] = argv;

  if (!command || command === "--help" || command === "-h") {
    io.stdout.write(`${buildRootHelp()}\n`);
    return 0;
  }

  const parsedCommand = CommandNameSchema.safeParse(command);

  if (!parsedCommand.success) {
    io.stderr.write(`Unknown command: ${command}\n\n${buildRootHelp()}\n`);
    return 1;
  }

  return runAnalyze(args, io);
}

function isDirectEntry(): boolean {
  return Boolean(process.argv[1]) && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
}

if (isDirectEntry()) {
  process.exitCode = main();
}
