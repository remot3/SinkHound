"""Command line interface for SinkHound."""

import argparse
from pathlib import Path

from .scanner import scan_repository


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Scan git history for dangerous patterns")
    subparsers = parser.add_subparsers(dest="command")

    scan = subparsers.add_parser("scan", help="Scan a repository")
    scan.add_argument("--sinks", required=True, type=Path, help="YAML file with sink definitions")
    scan.add_argument("--branch", required=True, help="Branch to scan")
    scan.add_argument("--repo", required=True, help="Repository URL")
    scan.add_argument(
        "--ignore-ext",
        nargs="*",
        default=[],
        help="File extensions to skip during scanning (e.g. .js .css)",
    )

    args = parser.parse_args(argv)

    if args.command == "scan":
        scan_repository(args.repo, args.branch, args.sinks, ignore_ext=args.ignore_ext)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

