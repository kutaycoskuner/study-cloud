# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-12
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Project entry point: one short command per task, so nobody has to remember script paths.

1. parse_args: a bare run prints the help; a task flag (--init) says what to do
2. run the chosen task:
   --init  creates or updates .env from .env.example (scripts/init_env.py)

Not the web app: that is app/main.py, started by uvicorn or the Docker image.

Requires: Python 3.10+; --init uses the standard library only, so it works before the
venv exists.

Run: python main.py --help
"""

import argparse
import sys

from scripts import init_env

EPILOG = """\
examples:
  python main.py --init              create or update .env from .env.example, asking first
  python main.py --init --dry-run    show what --init would do, write nothing

see README.md
"""


# -----------------------------------------------------------------------------------------
#   cli
# -----------------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Defines the CLI; its help text is also the guide a bare run prints."""
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="study-cloud project tasks.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--init", action="store_true",
                        help="create or update .env from .env.example (asks before each write)")
    parser.add_argument("--dry-run", action="store_true",
                        help="with a task: show what it would do, write nothing")
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace | None:
    """
    Parses the arguments; prints the guide when no task flag is given.

    Returns:
        The arguments, or None when nothing should run (the guide was printed).
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.init:
        parser.print_help()
        if argv:
            print("\nNothing run: add a task, e.g. python main.py --init " + " ".join(argv))
        return None
    return args


# -----------------------------------------------------------------------------------------
#   tasks
# -----------------------------------------------------------------------------------------

def init(dry_run: bool) -> int:
    """Runs scripts/init_env.py as if it were called with --run."""
    return init_env.main(["--run"] + (["--dry-run"] if dry_run else []))


# -----------------------------------------------------------------------------------------
#   main
# -----------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    # 1. CLI: without a task flag, print the guide and stop
    args = parse_args(argv)
    if args is None:
        return 2 if argv else 0

    # 2. Run the task
    return init(args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
