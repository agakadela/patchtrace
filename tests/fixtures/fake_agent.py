from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exit-code", type=int, default=0)
    args = parser.parse_args()

    print("fake agent says hello")
    print(f"fake agent exiting with {args.exit_code}")
    return int(args.exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
