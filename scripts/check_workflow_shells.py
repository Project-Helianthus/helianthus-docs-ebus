#!/usr/bin/env python3
"""Bound local workflow linting without actionlint's ShellCheck stdin pipe.

Shell selection, sanitization and exclusions mirror actionlint v1.7.7's
rule_shellcheck.go. Scripts are inspected, never executed.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import time

import yaml

EXCLUSIONS = "SC1091,SC2194,SC2050,SC2154,SC2157,SC2043"
TIMEOUT = 60


def bounded(command: list[str], timeout: float = TIMEOUT) -> int:
    try:
        return subprocess.run(command, timeout=max(0.001, timeout), check=False).returncode
    except subprocess.TimeoutExpired:
        print(f"FAIL: {command[0]} timed out (limit {timeout:.1f}s)", file=sys.stderr, flush=True)
        return 1
    except OSError as error:
        print(f"FAIL: {command[0]}: {error}", file=sys.stderr)
        return 2


def sanitize_expressions(source: str) -> str:
    """Replace complete expression spans, respecting single-quoted strings."""
    parts = []
    offset = 0
    while (start := source.find("${{", offset)) != -1:
        parts.append(source[offset:start])
        index = start + 3
        quoted = False
        while index < len(source):
            if source[index] == "'":
                if quoted and source.startswith("''", index):
                    index += 2  # GitHub expression strings escape quotes by doubling.
                    continue
                quoted = not quoted
            elif not quoted and source.startswith("}}", index):
                index += 2
                break
            index += 1
        else:
            raise ValueError("unterminated GitHub expression in run script")
        parts.append("_" * len(source[start:index].encode("utf-8")))
        offset = index
    parts.append(source[offset:])
    return "".join(parts)


def scripts(workflows: list[Path]):
    for workflow in workflows:
        data = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        workflow_shell = data.get("defaults", {}).get("run", {}).get("shell")
        for job_id, job in data.get("jobs", {}).items():
            job_shell = job.get("defaults", {}).get("run", {}).get("shell")
            labels = job.get("runs-on", [])
            if isinstance(labels, dict):
                labels = labels.get("labels", [])
            if isinstance(labels, str):
                labels = [labels]
            runner_shell = "pwsh" if any(
                label.lower() == "windows" or label.lower().startswith("windows-")
                for label in labels
            ) else "bash"
            for index, step in enumerate(job.get("steps", []), 1):
                if "run" not in step:
                    continue
                shell = step.get("shell") or job_shell or workflow_shell or runner_shell
                dialect = next((sh for sh in ("bash", "sh")
                                if shell == sh or shell.startswith(sh + " ")), None)
                source = sanitize_expressions(step["run"])
                setup = "set -eo pipefail" if dialect == "bash" else "set -e"
                yield f"{workflow}:{job_id}:step {index}", dialect, f"{setup}\n{source}\n"


def shellcheck(workflows: list[Path], temp_dir: Path, timeout: float = TIMEOUT) -> int:
    deadline = time.monotonic() + timeout
    failed = 0
    checked = skipped = 0
    for index, (label, dialect, source) in enumerate(scripts(workflows), 1):
        if dialect is None:
            print(f"SKIP: {label}: non-bash/sh shell (as in actionlint)", flush=True)
            skipped += 1
            continue
        path = temp_dir / f"workflow-step-{index}.{dialect}"
        path.write_text(source, encoding="utf-8")
        print(f"ShellCheck: {label} ({dialect}; {path})", flush=True)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            print(f"FAIL: ShellCheck pass timed out (limit {timeout:.1f}s)", file=sys.stderr)
            return 1
        status = bounded(["shellcheck", "--norc", "--format=gcc", "-x", "--shell", dialect,
                          "--severity=style", "-e", EXCLUSIONS, str(path)], remaining)
        failed = failed or status
        checked += 1
    print(f"ShellCheck {'FAILED' if failed else 'passed'}: {checked} run steps checked, "
          f"{skipped} skipped.", flush=True)
    return failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("actionlint", "shellcheck", "actionlint-version"))
    parser.add_argument("--temp-dir", type=Path)
    args = parser.parse_args()
    if args.mode == "actionlint-version":
        return bounded(["actionlint", "-version"])
    workflows = sorted(path for path in Path(".github/workflows").iterdir()
                       if path.suffix in (".yml", ".yaml"))
    if not workflows:
        parser.error("no workflows found")
    if args.mode == "actionlint":
        status = bounded(["actionlint", "-shellcheck=", *map(str, workflows)])
        print(f"actionlint {'FAILED' if status else 'passed'} (embedded ShellCheck disabled).", flush=True)
        return status
    if args.temp_dir is None or not args.temp_dir.is_dir():
        parser.error("shellcheck requires an existing --temp-dir")
    try:
        return shellcheck(workflows, args.temp_dir)
    except (OSError, ValueError, TypeError, AttributeError, yaml.YAMLError) as error:
        print(f"FAIL: workflow extraction: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
