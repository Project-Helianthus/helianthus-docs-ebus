#!/usr/bin/env python3
"""Reject unqualified common-contract terms on the Markdown pages.

The common semantic contract in docs-semantic owns the words plane, lens and
the canonical identity of semantic facts. Pages here keep their native words
only with a native qualifier: "registry plane" and "registry projection" for
the per-device registry views, "method bundle" for a registry plane's methods,
and "MCP semantic plane" for the data family of one `ebus_v1_semantic_*` tool.

The checker reads every `*.md` page under the root, outside hidden
directories, with whitespace runs (line wraps included) read as one space and
letter case ignored. It rejects:

- "semantic plane" or "semantic planes" unless the word before it is "MCP";
- "semantic lens" or "semantic lenses";
- "canonical semantic identity" or "canonical semantic identities".

A hyphen may stand for the space inside a term. The quotation list names the
only other accepted occurrences: each entry is one exact page path and one
exact excerpt of that page that holds the term. An entry that no longer
matches its page exactly once is reported as stale, so the list cannot hold an
exemption that nothing uses.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIPPED_DIRECTORIES = {"node_modules"}
PLANE = re.compile(r"\bsemantic[\s-]+planes?\b", re.IGNORECASE)
TERMS = (
    PLANE,
    re.compile(r"\bsemantic[\s-]+lens(?:es)?\b", re.IGNORECASE),
    re.compile(r"\bcanonical[\s-]+semantic[\s-]+identit(?:y|ies)\b", re.IGNORECASE),
)
PLANE_QUALIFIERS = ("MCP",)
PREVIOUS_WORD = re.compile(r"(\S+)\s*$")

# Pages outside this change that keep their wording until their own follow-up
# qualifies it. Each entry is (page path, exact excerpt, reason).
QUOTATION_LIST = (
    (
        "architecture/adapter-direct-multiplexer.md",
        "- Semantic planes: zones=2,",
        "recorded verification result, kept verbatim",
    ),
    (
        "deployment/adapter-direct-migration.md",
        "Verify via MCP or GraphQL that semantic planes populate normally.",
        "operator step naming the MCP data families; qualified by a follow-up",
    ),
    (
        "development/ad11-rollback-equivalence.md",
        "| Semantic key | Semantic plane, entity/instance scope,",
        "recorded equivalence table, kept verbatim",
    ),
    (
        "development/b524-provisional-name-evidence.md",
        "the semantic plane projects this selector",
        "pinned evidence row, kept verbatim",
    ),
)


def normalized(text: str) -> tuple[str, list[int]]:
    """Collapse whitespace runs to one space and map each character to its line."""
    chars: list[str] = []
    lines: list[int] = []
    line = 1
    pending_space = False
    for char in text:
        if char.isspace():
            pending_space = bool(chars)
            if char == "\n":
                line += 1
            continue
        if pending_space:
            chars.append(" ")
            lines.append(line)
            pending_space = False
        chars.append(char)
        lines.append(line)
    return "".join(chars), lines


def pages(root: Path) -> list[Path]:
    found = []
    for path in sorted(root.rglob("*.md")):
        parts = path.relative_to(root).parts
        if any(part.startswith(".") or part in SKIPPED_DIRECTORIES for part in parts):
            continue
        if path.is_file():
            found.append(path)
    return found


def qualified(text: str, start: int, pattern: re.Pattern[str]) -> bool:
    if pattern is not PLANE:
        return False
    previous = PREVIOUS_WORD.search(text, 0, start)
    return previous is not None and previous.group(1) in PLANE_QUALIFIERS


def quoted_spans(rel: str, text: str, quotations) -> tuple[list[range], list[str]]:
    spans: list[range] = []
    stale: list[str] = []
    for path, excerpt, _reason in quotations:
        if path != rel:
            continue
        excerpt_text = " ".join(excerpt.split())
        count = text.count(excerpt_text)
        if count != 1:
            stale.append(f"{rel}: quotation list entry matches {count} times: {excerpt!r}")
            continue
        start = text.index(excerpt_text)
        spans.append(range(start, start + len(excerpt_text)))
    return spans, stale


def page_findings(rel: str, raw: str, quotations) -> list[str]:
    text, lines = normalized(raw)
    spans, errors = quoted_spans(rel, text, quotations)
    for pattern in TERMS:
        for match in pattern.finditer(text):
            if qualified(text, match.start(), pattern):
                continue
            if any(match.start() in span and match.end() - 1 in span for span in spans):
                continue
            errors.append(
                f"{rel}:{lines[match.start()]}: unqualified {match.group(0)!r}; "
                "qualify the native meaning or point to the common contract"
            )
    return errors


def findings(root: Path, quotations=QUOTATION_LIST) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for path in pages(root):
        rel = path.relative_to(root).as_posix()
        seen.add(rel)
        errors.extend(page_findings(rel, path.read_text(encoding="utf-8"), quotations))
    for path, excerpt, _reason in quotations:
        if path not in seen:
            errors.append(f"{path}: quotation list names a missing page: {excerpt!r}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    errors = findings(args.root.resolve())
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print(f"Semantic term qualifier check failed: {len(errors)} finding(s).", file=sys.stderr)
        return 1
    print("Semantic term qualifier check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
