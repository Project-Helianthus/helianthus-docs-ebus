#!/usr/bin/env python3
"""Guard the northbound output hook page.

Reviewed paragraphs are frozen in the adjacent contract fixture. Reuse the
registration guard's rendered visibility rules so an example or a comment
cannot satisfy an obligation. Whitespace wrapping is immaterial. The owning
lifecycle page must state the narrowing directly after its hook rejection
paragraph, so the two pages cannot require opposite outcomes for `output`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from scripts.check_runtime_driver_registration import (
        REQUIREMENTS as REGISTRATION,
        normalize,
        visible_units,
    )
except ModuleNotFoundError:
    from check_runtime_driver_registration import (
        REQUIREMENTS as REGISTRATION,
        normalize,
        visible_units,
    )


DOCUMENT = Path("architecture/northbound-output-hook.md")
CONTRACT = json.loads(
    Path(__file__).with_name("northbound_output_hook_contract.json").read_text()
)
REQUIREMENTS = CONTRACT["page"]
OWNER = CONTRACT["owner"]
OWNER_DOCUMENT = Path(OWNER["document"])


def graphql_claims(sections: dict[str, list[str]]) -> list[str]:
    """The lifecycle contract has no lifecycle GraphQL API.

    Only a pinned paragraph may name GraphQL, so no added text can claim a
    GraphQL health read.
    """
    pinned = {normalize(block) for blocks in REQUIREMENTS.values() for block in blocks}
    return [
        f"GraphQL health claim: {block[:80]}"
        for blocks in sections.values()
        for block in blocks
        if "graphql" in block.lower() and block not in pinned
    ]


SUPERSEDED = "driver-runtime-v1.md"


def superseded_citations(sections: dict[str, list[str]]) -> list[str]:
    """Health authority is the MCP lifecycle contract.

    The driver runtime API page is superseded historical material, so no
    visible block may cite it as an authority for this page.
    """
    return [
        f"superseded authority cited: {block[:80]}"
        for blocks in sections.values()
        for block in blocks
        if SUPERSEDED in block
    ]


def validate(text: str) -> list[str]:
    sections: dict[str, list[str]] = {}
    current = None
    errors = []
    for kind, content in visible_units(text):
        if kind == "heading":
            current = content
            if current in sections:
                errors.append(f"duplicate section: {current}")
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(normalize(content))
    errors.extend(graphql_claims(sections))
    errors.extend(superseded_citations(sections))
    for heading, blocks in REQUIREMENTS.items():
        present = sections.get(heading, [])
        for block in blocks:
            if normalize(block) not in present:
                errors.append(
                    f"changed obligation in {heading}: {normalize(block)[:80]}"
                )
    return errors


def validate_owner(text: str) -> list[str]:
    """The owning lifecycle page names the narrowing right after its hook rule."""
    units = [normalize(content)
             for _, content in visible_units(text, include_subheadings=True)]
    rule = normalize(REGISTRATION[OWNER["follows"]])
    narrowing = normalize(OWNER["paragraph"])
    if units.count(rule) != 1:
        return [f"owner hook rule not found once in {OWNER_DOCUMENT.as_posix()}"]
    if units.count(narrowing) != 1:
        return [f"owner narrowing not found once in {OWNER_DOCUMENT.as_posix()}"]
    if units.index(narrowing) != units.index(rule) + 1:
        return ["owner narrowing does not directly follow the owner hook rule"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = []
    for relative, check in ((DOCUMENT, validate), (OWNER_DOCUMENT, validate_owner)):
        try:
            text = (args.root / relative).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"missing {relative.as_posix()}"
                          if isinstance(exc, FileNotFoundError) else str(exc))
        else:
            errors.extend(check(text))
    if errors:
        for error in errors:
            print(f"northbound_output_hook_invalid: {error}", file=sys.stderr)
        return 1
    print("northbound_output_hook_ok (documentation only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
