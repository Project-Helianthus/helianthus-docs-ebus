#!/usr/bin/env python3
"""Keep CC0 wire references separate from AGPL application contracts."""

from __future__ import annotations

import re
import sys
from pathlib import Path


PROJECT = re.compile(r"\b(?:Helianthus|VRC[ -]Explorer)\b", re.IGNORECASE)
APP_TEXT = re.compile(r"\b(?:planner|GraphQL|MCP|Portal|Browser)\b", re.IGNORECASE)
ARGV = re.compile(r"(?<![\w#/-])--[a-z][a-z0-9-]*(?=[\s`=,.;)]|$)")
URL = re.compile(r"https?://[^\s)<>]+")
LINK = re.compile(r"\]\(([^\s)]+)\)")
EVIDENCE_HEADING = re.compile(
    r"^#{1,6}\s+(?:Sources?|References?|Provenance|Evidence)\b", re.I
)
UNPUBLISHABLE = re.compile(
    r"private(?:-context)?/|private static analysis|restricted static.analysis|_work_[\w-]+/|"
    r"(?<![\w/-])(?-i:[A-Z][A-Z0-9]*\d[A-Z0-9]*[-_](?:[\w-]*\.md|(?:DEEP|ANALYSIS|NOTES)\b))|"
    r"(?-i:\b[A-Z]{2,})-(?:B[0-9A-F]{3}|corrections|semantic|protocol|timer)[\w-]*(?:\.md|-)",
    re.IGNORECASE,
)


def unpublishable_attribution(root: Path) -> list[str]:
    errors = []
    for path in root.rglob("*.md"):
        if any(
            part in {".git", ".venv", ".pytest_cache", ".ruff_cache"}
            for part in path.relative_to(root).parts
        ):
            continue
        if UNPUBLISHABLE.search(path.read_text()):
            errors.append(f"{path.relative_to(root)}: nonpublishable attribution")
    return errors


def violations(root: Path) -> list[str]:
    errors: list[str] = []
    for area in ("protocols", "types"):
        for path in (root / area).rglob("*.json"):
            if re.search(
                r"b524-(?:operation-(?:read-plan|edit-plan|reads-artifact)|native-write-qualification)",
                path.name,
            ):
                errors.append(
                    f"{path.relative_to(root)}: application schema/fixture in CC0 tree"
                )
        for path in sorted((root / area).rglob("*.md")):
            evidence = False
            previous = ""
            for number, line in enumerate(path.read_text().splitlines(), 1):
                if line.startswith("#"):
                    evidence = bool(EVIDENCE_HEADING.match(line))
                # A source citation may name the tool that collected evidence;
                # that exception never admits CLI instructions or app contracts.
                source = evidence or bool(re.match(r"^> ?Source:|^Source:", line, re.I))
                # A negative scope statement excludes product policy rather
                # than describing it; the pinned Modbus reference uses this form.
                exclusion = previous.endswith("contains no") and line == (
                    "Helianthus scheduler, profile, qualification, gateway, or semantic policy."
                )
                prose = URL.sub("", line)
                if ARGV.search(prose):
                    errors.append(
                        f"{path.relative_to(root)}:{number}: CLI argument in CC0 reference"
                    )
                if APP_TEXT.search(prose) or (
                    PROJECT.search(prose) and not (source or exclusion)
                ):
                    errors.append(
                        f"{path.relative_to(root)}:{number}: application text in CC0 reference"
                    )
                for match in LINK.finditer(line):
                    target = match.group(1).split("#", 1)[0]
                    if not target or ":" in target:
                        continue
                    resolved = (path.parent / target).resolve()
                    if not any(
                        resolved.is_relative_to((root / zone).resolve())
                        for zone in ("protocols", "types")
                    ):
                        errors.append(
                            f"{path.relative_to(root)}:{number}: link crosses into AGPL application docs"
                        )
                previous = line
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = violations(root) + unpublishable_attribution(root)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("CC0 protocol/type and AGPL application boundary passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
