# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-12
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Creates local secret files (e.g. .env) from their committed examples.

1. parse_args: without --run, print the help and stop, so nothing is written by accident
2. check_terminal: every write is asked first, so a real run needs an interactive terminal
3. ensure_file, per pair in FILES: a missing target is created from its example after a y,
   with empty values filled by generated secrets on request; an existing target is checked
   for keys the example has and it lacks, which can be appended
4. print_report: one line per file saying what was done

Why: docker-compose.yaml reads .env, which is gitignored, so every fresh checkout needs
one; copying it by hand is easy to forget and leaves the password empty.

Requires: Python 3.10+, standard library only.

Inputs -> outputs: .env.example -> .env (repo root).

Run: python scripts/init_env.py --help

Notes: generated values are never printed, so they can't end up in a terminal log; read
them in the file itself. Existing values are never changed, only missing keys appended.
"""

import argparse
import re
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# example -> file created from it, both relative to the repo root; add a line per new pair
FILES = {".env.example": ".env"}

KEY_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$")

EPILOG = """\
examples:
  python scripts/init_env.py --run              create or update the files, asking first
  python scripts/init_env.py --run --dry-run    show what --run would do, write nothing

note:
  PostgreSQL takes POSTGRES_PASSWORD only when its data volume is first created; after
  changing it in .env, the old password stays valid until `docker compose down -v`
  (which deletes the database data).

see README.md, "Setup Python Environment"
"""


# -----------------------------------------------------------------------------------------
#   cli
# -----------------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Defines the CLI; its help text is also the guide a bare run prints."""
    pairs = ", ".join(f"{src} -> {dst}" for src, dst in FILES.items())
    parser = argparse.ArgumentParser(
        prog="python scripts/init_env.py",
        description=f"Creates local secret files from their examples ({pairs}).",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--run", action="store_true", help="create or update the files")
    parser.add_argument("--dry-run", action="store_true",
                        help="with --run: show what would happen, write nothing")
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace | None:
    """
    Parses the arguments; prints the guide when --run is missing.

    Returns:
        The arguments, or None when nothing should run (the guide was printed).
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.run:
        parser.print_help()
        if argv:
            print("\nNothing run: add --run to start, e.g. python scripts/init_env.py --run "
                  + " ".join(argv))
        return None
    return args


def check_terminal(dry_run: bool) -> bool:
    """Returns False (and says why) when a real run has no terminal to ask in."""
    if dry_run or sys.stdin.isatty():
        return True
    print("No interactive terminal to ask in: nothing written. "
          "Run it in a terminal, or add --dry-run to only see what it would do.")
    return False


# -----------------------------------------------------------------------------------------
#   files
# -----------------------------------------------------------------------------------------

def read(path: Path) -> str:
    """Reads a text file without translating its line endings."""
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def write(path: Path, text: str, dry_run: bool) -> None:
    """Writes a text file as given (line endings kept); does nothing in a dry run."""
    if dry_run:
        return
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def parse_keys(text: str) -> dict[str, str]:
    """Returns KEY -> value for every KEY=value line; comments and blank lines are skipped."""
    keys = {}
    for line in text.splitlines():
        match = KEY_LINE.match(line)
        if match:
            keys[match.group(1)] = match.group(2).strip()
    return keys


def line_ending(text: str) -> str:
    """Returns the file's line ending, so appended lines match it."""
    return "\r\n" if "\r\n" in text else "\n"


def ask(question: str, dry_run: bool) -> bool:
    """Asks a y/N question; a dry run says what it would ask and continues as if yes."""
    if dry_run:
        print(f"  (dry run) would ask: {question}")
        return True
    try:
        return input(f"  {question} [y/N] ").strip().lower() == "y"
    except EOFError:
        # stdin closed or redirected (Windows reports NUL as a terminal, so check_terminal
        # can't catch every case): no answer counts as no
        print("(no input: counted as no)")
        return False


def fill_empty(text: str, dry_run: bool) -> tuple[str, list[str]]:
    """
    Offers a generated secret for every key with an empty value.

    Returns:
        The text with the accepted values filled in, and the names of the filled keys.
        The values themselves are never printed.
    """
    filled = []
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        match = KEY_LINE.match(line)
        if match and not match.group(2).strip():
            key = match.group(1)
            if ask(f"{key} is empty: fill it with a generated random value?", dry_run):
                ending = line[len(line.rstrip("\r\n")):]
                lines[i] = f"{key}={secrets.token_urlsafe(24)}{ending}"
                filled.append(key)
    return "".join(lines), filled


def create_file(example: Path, target: Path, dry_run: bool) -> str:
    """Creates target from example after a y; returns the report line."""
    if not ask(f"{target.name} is missing: create it from {example.name}?", dry_run):
        return f"{target.name}: missing, not created (answered no)"
    text, filled = fill_empty(read(example), dry_run)
    write(target, text, dry_run)
    return f"{target.name}: created from {example.name}; generated values: {', '.join(filled) or 'none'}"


def update_file(example: Path, target: Path, dry_run: bool) -> str:
    """Offers to append the keys target lacks; returns the report line."""
    example_text, target_text = read(example), read(target)
    example_keys, target_keys = parse_keys(example_text), parse_keys(target_text)
    unknown = [k for k in target_keys if k not in example_keys]
    if unknown:
        print(f"  {target.name} has keys {example.name} doesn't list (kept): {', '.join(unknown)}")
    missing = [k for k in example_keys if k not in target_keys]
    if not missing:
        return f"{target.name}: exists and has every key of {example.name}, nothing to do"
    print(f"  {target.name} lacks keys from {example.name}: {', '.join(missing)}")
    if not ask(f"append them to {target.name}?", dry_run):
        return f"{target.name}: missing keys not added (answered no): {', '.join(missing)}"
    newline = line_ending(target_text)
    added = [line for line in example_text.splitlines()
             if (m := KEY_LINE.match(line)) and m.group(1) in missing]
    chunk, filled = fill_empty(newline.join(added) + newline, dry_run)
    separator = "" if not target_text or target_text.endswith(("\n", "\r")) else newline
    write(target, target_text + separator + chunk, dry_run)
    return (f"{target.name}: appended {', '.join(missing)}; "
            f"generated values: {', '.join(filled) or 'none'}")


def ensure_file(example: Path, target: Path, dry_run: bool) -> str:
    """Creates or updates target from example; returns the report line."""
    print(f"\n{example.name} -> {target.name}")
    if not example.exists():
        return f"{target.name}: example {example.name} not found, nothing done"
    if not target.exists():
        return create_file(example, target, dry_run)
    return update_file(example, target, dry_run)


def print_report(results: list[str], dry_run: bool) -> None:
    """Prints what was done per file, last, under one header."""
    print("\n=== RESULT ===" + (" (dry run: nothing written)" if dry_run else ""))
    for line in results:
        print(line)


# -----------------------------------------------------------------------------------------
#   main
# -----------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    # 1. CLI: without --run, print the guide and stop
    args = parse_args(argv)
    if args is None:
        return 2 if argv else 0

    # 2. Asking needs a terminal (a dry run only reports)
    if not check_terminal(args.dry_run):
        return 1

    # 3. Create or update each file
    results = [ensure_file(ROOT / src, ROOT / dst, args.dry_run) for src, dst in FILES.items()]

    # 4. Report
    print_report(results, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
