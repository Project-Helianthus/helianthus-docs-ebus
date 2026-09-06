#!/usr/bin/env python3
"""Validate the bounded pending GraphQL device-face provenance contract."""
from __future__ import annotations

import pathlib
import re
import sys


DOC = pathlib.Path("api/graphql.md")
MCP = pathlib.Path("api/mcp.md")
ATR = pathlib.Path("architecture/atr/07-live-validation-acceptance.md")
HEADING = "### Pending gateway #939/#940 implementation: Device Face Discovery Provenance"
SOURCES = ("static_seed", "passive_observed", "active_confirmed")
STATES = ("candidate", "corroborated_pending", "identity_confirmed")
INITIAL = (
    ("static_seed", "candidate"),
    ("passive_observed", "corroborated_pending"),
    ("active_confirmed", "identity_confirmed"),
)
INDEPENDENCE = (
    "Valid non-null values are the Cartesian product of the\n"
    "separately allowed source and state sets; no source label determines or\n"
    "restricts the state label."
)
DEVICES_FACE = "`devices` selects the face at each device's canonical primary `address`."
NON_PROOF = (
    "A discovery source or verification state does not prove\n"
    "a supported device, current qualification, stable cross-address identity, or\n"
    "live behavior."
)
SOURCE_RETENTION = (
    "The accepted registry rule requires `discoverySource` to preserve the original\n"
    "native discovery source. Verification advancement MUST NOT rewrite\n"
    "`static_seed` or `passive_observed` to `active_confirmed`. Retained\n"
    "`static_seed` / `identity_confirmed` and `passive_observed` / `identity_confirmed`\n"
    "forms are valid."
)
TOPOLOGY_NON_PROOF = (
    "Topology grouping does\nnot prove identity; only the documented qualified identity rule may establish a\n"
    "cross-address identity."
)
MCP_SOURCE_RETENTION = (
    "Each face retains its original\n"
    "      discovery source when verification advances: a static-seeded face\n"
    "      remains `static_seed`, a passively discovered face remains\n"
    "      `passive_observed`, and `active_confirmed` applies only when active\n"
    "      discovery created that face. Passive corroboration may advance the\n"
    "      independent verification state to `corroborated_pending`; identity\n"
    "      confirmation may advance it to `identity_confirmed`. Neither event\n"
    "      rewrites `discovery_source`."
)


class CheckError(ValueError):
    """The public GraphQL provenance contract is missing or inconsistent."""


def _section(text: str) -> str:
    start = text.find(HEADING)
    if start < 0:
        raise CheckError("pending implementation heading missing")
    end = text.find("\n### ", start + len(HEADING))
    return text[start : end if end >= 0 else None]


def _single_column(section: str, title: str) -> tuple[str, ...]:
    match = re.search(
        rf"Allowed `{re.escape(title)}` labels:\n\n\| label \|\n\|---\|\n"
        r"(?P<rows>(?:\| `[^`]+` \|\n)+)",
        section,
    )
    if match is None:
        raise CheckError(f"{title} label table missing")
    return tuple(re.findall(r"\| `([^`]+)` \|", match.group("rows")))


def _initial_pairs(section: str) -> tuple[tuple[str, str], ...]:
    match = re.search(
        r"Typical initial combinations are examples, not an exhaustive pairing rule:\n\n"
        r"\| `discoverySource` \| `verificationState` \|\n\|---\|---\|\n"
        r"(?P<rows>(?:\| `[^`]+` \| `[^`]+` \|\n)+)",
        section,
    )
    if match is None:
        raise CheckError("initial combination table missing")
    return tuple(re.findall(r"\| `([^`]+)` \| `([^`]+)` \|", match.group("rows")))


def validate_text(text: str, atr: str) -> None:
    current = re.search(r"### Types \(Current\).*?^type Device \{\n(?P<body>.*?)^\}", text, re.M | re.S)
    if current is None:
        raise CheckError("current Device definition missing")
    if "discoverySource:" in current.group("body") or "verificationState:" in current.group("body"):
        raise CheckError("pending fields leaked into Types Current")

    section = _section(text)
    pending_type = "extend type Device {\n  discoverySource: String\n  verificationState: String\n}"
    if section.count(pending_type) != 1:
        raise CheckError("pending Device extension must declare exact camel-case fields")
    if "is not present\nin the current gateway schema" not in section:
        raise CheckError("docs-first pending status missing")
    if _single_column(section, "discoverySource") != SOURCES:
        raise CheckError("discoverySource label set differs")
    if _single_column(section, "verificationState") != STATES:
        raise CheckError("verificationState label set differs")
    if _initial_pairs(section) != INITIAL:
        raise CheckError("initial combination examples differ")
    if INDEPENDENCE not in section:
        raise CheckError("independent source/state invariant missing")

    required = (
        "`static_seed` / `identity_confirmed`",
        "`passive_observed` / `identity_confirmed`",
        DEVICES_FACE,
        "projects that queried\ncanonical or alias face's discovery provenance.",
        "returned device identity remains canonical and `address` remains the canonical\nprimary address.",
        "`device(address:)` returns `null` for an unknown address.",
        "When a registry device has no address-slot record for the selected face, both\nfields resolve to GraphQL `null`.",
        "A slotless entry remains visible through\n`devices` and `device(address:)`",
        "This matches MCP, which omits both\nsnake-case provenance members for the same slotless condition.",
        "Topology alias grouping, qualified cross-address identity, native observation,\nand per-face discovery provenance are distinct records.",
        SOURCE_RETENTION,
        TOPOLOGY_NON_PROOF,
        NON_PROOF,
    )
    for fragment in required:
        if fragment not in section:
            raise CheckError(f"required provenance rule missing: {fragment!r}")

    obsolete = "verificationState=corroborated`"
    canonical = "verificationState=corroborated_pending`"
    if obsolete in atr or atr.count(canonical) != 1:
        raise CheckError("ATR must use one canonical corroborated_pending label")


def validate_mcp_text(text: str) -> None:
    if MCP_SOURCE_RETENTION not in text:
        raise CheckError("MCP source-retention rule missing")
    obsolete = "active scan (→ `active_confirmed/identity_confirmed`)"
    if obsolete in text:
        raise CheckError("MCP source-rewrite rule remains")


def main() -> int:
    try:
        validate_text(DOC.read_text(encoding="utf-8"), ATR.read_text(encoding="utf-8"))
        validate_mcp_text(MCP.read_text(encoding="utf-8"))
    except CheckError as error:
        print(f"graphql_face_provenance_error: {error}", file=sys.stderr)
        return 1
    print("graphql_face_provenance_ok sources=3 states=3 initial=3 pending=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
