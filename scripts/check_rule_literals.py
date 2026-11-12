#!/usr/bin/env python3
"""Reject new long strings in module-level checker assignments."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def literals(source: str) -> list[dict]:
    result = []
    for statement in ast.parse(source).body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        for node in ast.walk(statement):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) > 120:
                result.append({"assignment": ast.unparse(statement.target) if isinstance(statement, ast.AnnAssign)
                               else ",".join(ast.unparse(t) for t in statement.targets),
                               "value": node.value})
    return result


def check(root: Path = ROOT) -> list[str]:
    baseline = json.loads((root / "scripts/rules/literal_baseline.json").read_text())
    current = {str(p.relative_to(root)): literals(p.read_text())
               for p in sorted((root / "scripts").glob("check_*.py"))}
    current = {path: entries for path, entries in current.items() if entries}
    return [] if current == baseline else ["long checker literals differ from exact existing-debt inventory"]


def main() -> int:
    errors = check()
    for error in errors:
        print(error)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
