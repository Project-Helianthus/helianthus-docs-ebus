#!/usr/bin/env python3
"""List the heavy Docs Checks suites whose inputs are identical in two checkouts.

The pull-request workflow runs this script from the trusted base checkout with
the base copy of scripts/ci_suite_inputs.json, so a pull request cannot narrow
the inputs of its own suites. A suite is listed only when every file matched by
the shared inputs or by the suite's inputs exists in both checkouts with the
same bytes, and no such file exists in only one of them. The output is one line
of space-separated suite identifiers, possibly empty; scripts/ci_local.sh skips
exactly the listed suites. Any doubt (a missing checkout, a malformed manifest)
ends with a nonzero exit status and no output, and the caller runs every suite.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
from pathlib import Path

DEFAULT_MANIFEST = Path(__file__).resolve().with_name("ci_suite_inputs.json")
SUITE_ID_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789_")
# Interpreter and tool caches are never inputs; a stale cache must not force runs.
IGNORED_DIRECTORIES = {".git", "__pycache__", ".pytest_cache"}


def load_manifest(path: Path) -> tuple[list[str], dict[str, list[str]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError(f"{path}: expected a version 1 manifest object")
    shared = data.get("shared_inputs")
    suites = data.get("suites")
    if not isinstance(shared, list) or not shared:
        raise ValueError(f"{path}: shared_inputs must be a non-empty list")
    if not isinstance(suites, dict) or not suites:
        raise ValueError(f"{path}: suites must be a non-empty object")
    result: dict[str, list[str]] = {}
    for suite_id, suite in suites.items():
        if not suite_id or not set(suite_id) <= SUITE_ID_CHARS:
            raise ValueError(f"{path}: invalid suite identifier {suite_id!r}")
        inputs = suite.get("inputs") if isinstance(suite, dict) else None
        if not isinstance(inputs, list) or not inputs:
            raise ValueError(f"{path}: suite {suite_id} needs a non-empty inputs list")
        result[suite_id] = inputs
    for pattern in shared + [p for inputs in result.values() for p in inputs]:
        if (not isinstance(pattern, str) or not pattern or pattern.startswith("/")
                or "\\" in pattern or ".." in pattern.split("/")):
            raise ValueError(f"{path}: invalid input pattern {pattern!r}")
    return shared, result


def matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-2])
    return fnmatch.fnmatchcase(path, pattern)


def tree_files(root: Path) -> dict[str, Path]:
    """Map every repository-relative file path under root to its path, skipping caches."""
    files: dict[str, Path] = {}
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORED_DIRECTORIES)
        for name in filenames:
            full = Path(directory) / name
            files[full.relative_to(root).as_posix()] = full
    return files


def same_file(left: Path, right: Path) -> bool:
    if left.is_symlink() or right.is_symlink():
        return left.is_symlink() and right.is_symlink() and os.readlink(left) == os.readlink(right)
    return left.read_bytes() == right.read_bytes()


def changed_paths(base: Path, head: Path) -> set[str]:
    base_files, head_files = tree_files(base), tree_files(head)
    changed = set(base_files) ^ set(head_files)
    for path in set(base_files) & set(head_files):
        if not same_file(base_files[path], head_files[path]):
            changed.add(path)
    return changed


def unchanged_suites(base: Path, head: Path, manifest: Path) -> list[str]:
    shared, suites = load_manifest(manifest)
    changed = changed_paths(base, head)
    if any(matches(path, pattern) for path in changed for pattern in shared):
        return []
    return [suite_id for suite_id, inputs in suites.items()
            if not any(matches(path, pattern) for path in changed for pattern in inputs)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", required=True, type=Path, help="trusted base checkout")
    parser.add_argument("--head", required=True, type=Path, help="pull-request head checkout")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    for root in (args.base, args.head):
        if not root.is_dir() or root.is_symlink():
            print(f"{root}: not a checkout directory", file=sys.stderr)
            return 2
    try:
        suites = unchanged_suites(args.base, args.head, args.manifest)
    except (OSError, ValueError) as error:
        print(f"ci_suite_inputs: {error}", file=sys.stderr)
        return 2
    print(" ".join(suites))
    return 0


if __name__ == "__main__":
    sys.exit(main())
