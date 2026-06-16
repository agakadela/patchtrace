export interface CliIo {
  stdout: {
    write(chunk: string): void;
  };
  stderr: {
    write(chunk: string): void;
  };
}

export const processIo: CliIo = {
  stdout: process.stdout,
  stderr: process.stderr,
};
