from __future__ import annotations


def main() -> int:
    print("fake interactive agent ready")
    response = input("fake interactive prompt: ")
    print(f"fake interactive response: {response}")
    print("fake interactive agent done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
