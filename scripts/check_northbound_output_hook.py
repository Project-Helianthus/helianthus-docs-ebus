#!/usr/bin/env python3
"""Guard the northbound output hook page.

Reviewed paragraphs are frozen in the adjacent contract fixture. Reuse the
registration guard's rendered visibility rules so an example or a comment
cannot satisfy an obligation. Whitespace wrapping is immaterial.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from scripts.check_runtime_driver_registration import normalize, visible_units
except ModuleNotFoundError:
    from check_runtime_driver_registration import normalize, visible_units


DOCUMENT = Path("architecture/northbound-output-hook.md")
REQUIREMENTS = json.loads(
    Path(__file__).with_name("northbound_output_hook_contract.json").read_text()
)


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
    for heading, blocks in REQUIREMENTS.items():
        present = sections.get(heading, [])
        for block in blocks:
            if normalize(block) not in present:
                errors.append(
                    f"changed obligation in {heading}: {normalize(block)[:80]}"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    document = args.root / DOCUMENT
    try:
        text = document.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors = [f"missing {DOCUMENT.as_posix()}" if isinstance(exc, FileNotFoundError) else str(exc)]
    else:
        errors = validate(text)
    if errors:
        for error in errors:
            print(f"northbound_output_hook_invalid: {error}", file=sys.stderr)
        return 1
    print("northbound_output_hook_ok (documentation only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
