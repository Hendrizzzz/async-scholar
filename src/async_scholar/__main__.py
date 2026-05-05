from __future__ import annotations

import argparse

from async_scholar import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="async_scholar",
        description=(
            "AsyncScholar is a local-first lecture monitoring scaffold for "
            "transcription, event detection, alerts, archives, and review."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
