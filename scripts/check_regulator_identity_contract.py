#!/usr/bin/env python3
"""Keep the public qualified-identity contract synchronized across its docs."""

from __future__ import annotations

import argparse
import pathlib
import re
import sys


class CheckError(Exception):
    """Raised when a required public-contract statement is absent."""


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def require(text: str, path: pathlib.Path, fragment: str) -> None:
    if normalize_whitespace(fragment) not in normalize_whitespace(text):
        raise CheckError(f"{path}: missing required qualified-identity contract fragment: {fragment!r}")


def forbid(text: str, path: pathlib.Path, fragment: str) -> None:
    if fragment in text:
        raise CheckError(f"{path}: forbidden legacy identity-merge wording remains: {fragment!r}")


PERMISSION = r"(?:may|can|is permitted(?:\s+to)?|must(?!\s+not))"

# This is deliberately a small, contract-specific contradiction check rather
# than a natural-language policy parser.  Each pattern is applied to a bounded
# Markdown paragraph/sentence after whitespace and case normalization.  It
# rejects an affirmative exception to one of the six qualified-identity rules;
# the required normative wording remains checked below.
CONTRADICTORY_PERMISSIONS = (
    (
        "serial-only merge",
        re.compile(
            rf"\bserial(?:-only)?(?:\s+(?:match|alone))?\s+{PERMISSION}"
            r"(?:\s+\w+){0,8}\s+merge(?:\s+\w+){0,4}\s+independent\s+addresses\b"
        ),
    ),
    (
        "partial-triple merge",
        re.compile(
            rf"\b(?:empty|partial)(?:\s+\w+){{0,2}}\s+triples?\b"
            rf"(?:\s+\w+){{0,6}}\s+{PERMISSION}(?:\s+\w+){{0,8}}\s+"
            r"(?:merge|establish|create)(?:\s+\w+){0,5}\s+"
            r"(?:independent\s+addresses|(?:cross-address\s+)?stable\s+identity\s+key)\b"
        ),
    ),
    (
        "sentinel identity proof",
        re.compile(
            rf"\bsentinel(?:\s+\w+){{0,4}}\s+{PERMISSION}(?:\s+\w+){{0,8}}\s+"
            r"(?:identity\s+proof|cross-address\s+merge|stable\s+identity(?:\s+key)?)\b"
        ),
    ),
    (
        "topology alias identity promotion",
        re.compile(
            rf"\btopology\s+alias(?:ing)?(?:\s+\w+){{0,5}}\s+{PERMISSION}"
            r"(?:\s+\w+){0,8}\s+(?:stable\s+identity|cross-address\s+identity\s+merge|"
            r"cross-address\s+stable\s+identity\s+key)\b"
        ),
    ),
    (
        "same-address partial-enrichment merge",
        re.compile(
            rf"\bsame-address\s+partial\s+enrichment(?:\s+\w+){{0,5}}\s+{PERMISSION}"
            r"(?:\s+\w+){0,8}\s+merge(?:\s+\w+){0,4}\s+independent\s+addresses\b"
        ),
    ),
    (
        "confirmation provenance rewrite",
        re.compile(
            rf"\bidentity\s+confirmation(?:\s+\w+){{0,5}}\s+{PERMISSION}"
            r"(?:\s+\w+){0,8}\s+(?:rewrite|replace|change)(?:\s+\w+){0,5}\s+"
            r"(?:static_seed|passive_observed|provenance|source\s+labels?)\b"
        ),
    ),
)


def contract_clauses(text: str) -> tuple[str, ...]:
    """Return normalized, bounded prose clauses for contradiction checks."""
    paragraphs = re.split(r"\n\s*\n", text)
    clauses = []
    for paragraph in paragraphs:
        normalized = normalize_whitespace(paragraph).casefold()
        clauses.extend(re.split(r"(?<=[.!?])\s+", normalized))
    return tuple(clause for clause in clauses if clause)


def reject_contradictory_permissions(text: str, path: pathlib.Path) -> None:
    for clause in contract_clauses(text):
        for rule, pattern in CONTRADICTORY_PERMISSIONS:
            if pattern.search(clause):
                raise CheckError(f"{path}: contradictory qualified-identity permission for {rule}: {clause!r}")


def validate_documents(root: pathlib.Path) -> None:
    enrichment_path = root / "architecture/regulator-identity-enrichment.md"
    atr_path = root / "architecture/atr/04-sn-merge-gate.md"
    overview_path = root / "architecture/overview.md"
    enrichment = enrichment_path.read_text(encoding="utf-8")
    atr = atr_path.read_text(encoding="utf-8")
    overview = overview_path.read_text(encoding="utf-8")

    for path, text in (
        (enrichment_path, enrichment),
        (atr_path, atr),
        (overview_path, overview),
    ):
        reject_contradictory_permissions(text, path)

    for fragment in (
        "A cross-address identity merge requires an exact normalized\n"
        "  `(Manufacturer, DeviceID, SerialNumber)` triple.",
        "Empty or partial triples create no cross-address stable\nidentity key.",
        "`0`,\n`0x00000000`, `0xFFFFFFFF`, or `0x7FFFFFFF`.",
        "Only while recognizing those\nhexadecimal sentinels, case is ignored, one optional `0x` prefix is accepted,\nand leading zeros are ignored.",
        "That narrow recognition rule MUST NOT parse,\nrewrite, or otherwise reinterpret ordinary product serial formats.",
        "Explicit topology aliasing based on source/target or canonical-companion\n  evidence MAY group faces before a qualified identity exists. It is not a\n  cross-address identity merge.",
        "Partial enrichment of an already-known address MAY retain last-known-good\nfields for that same address. It MUST NOT establish a cross-address stable\nidentity key or merge independent addresses.",
        "a serial-only match, a\nMAC-only match, or a matching model signature alone MUST NOT merge independent\naddresses.",
        "A static candidate becomes\n`identity_confirmed` only after a complete qualified observation.",
        "Identity\nconfirmation MUST NOT rewrite a face's `static_seed` or `passive_observed`\nsource label.",
    ):
        require(enrichment, enrichment_path, fragment)

    for fragment in (
        "Cross-address identity merge is permitted only when the exact normalized\n`(Manufacturer, DeviceID, SerialNumber)` triple matches.",
        "Empty or partial triples create no\ncross-address stable identity key.",
        "`SerialNumber` MUST NOT be a sentinel value: `0`, `0x00000000`,\n`0xFFFFFFFF`, or `0x7FFFFFFF`.",
        "This exception MUST NOT parse, rewrite, or otherwise\nreinterpret ordinary product serial formats.",
        "serial alone, MAC alone, model signature alone, companion\nrelation alone, or address co-occurrence alone.",
        "Explicit topology aliasing based on source/target or canonical-companion\nevidence is separate from identity merge",
        "A static\ncandidate becomes `identity_confirmed` only after a complete qualified\nobservation.",
        "it MUST NOT rewrite `static_seed` or `passive_observed` source labels.",
    ):
        require(atr, atr_path, fragment)

    require(
        overview,
        overview_path,
        "Cross-address identity merge requires an exact normalized `(Manufacturer,\nDeviceID, SerialNumber)` triple; an empty or partial triple creates no stable\nidentity key.",
    )
    forbid(overview, overview_path, "DeviceID` is not part of the serial/MAC identity key")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        validate_documents(args.root)
    except (CheckError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print("Qualified identity documentation contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
