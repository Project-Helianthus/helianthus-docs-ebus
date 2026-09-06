from __future__ import annotations

import importlib.util
import pathlib
import re

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("graphql_face_provenance", ROOT / "scripts/check_graphql_face_provenance.py")
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def texts() -> tuple[str, str]:
    return (
        (ROOT / "api/graphql.md").read_text(encoding="utf-8"),
        (ROOT / "architecture/atr/07-live-validation-acceptance.md").read_text(encoding="utf-8"),
    )


def mcp_text() -> str:
    return (ROOT / "api/mcp.md").read_text(encoding="utf-8")


def rejects(doc_old: str | None = None, doc_new: str = "", atr_old: str | None = None, atr_new: str = "") -> None:
    doc, atr = texts()
    if doc_old is not None:
        assert doc_old in doc
        doc = doc.replace(doc_old, doc_new, 1)
    if atr_old is not None:
        assert atr_old in atr
        atr = atr.replace(atr_old, atr_new, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc, atr)


def test_accepts_current_independent_label_contract() -> None:
    CHECKER.validate_text(*texts())
    CHECKER.validate_mcp_text(mcp_text())


@pytest.mark.parametrize(
    ("old", "new"),
    (
        (CHECKER.HEADING, "### Device Face Discovery Provenance"),
        ("  discoverySource: String", "  discovery_source: String"),
        ("  verificationState: String", "  verification_state: String"),
        ("  discoverySource: String", "  discoverySource: String!"),
        ("| `static_seed` |\n", "| `manual` |\n"),
        ("| `identity_confirmed` |\n", "| `verified` |\n"),
        ("| `passive_observed` | `corroborated_pending` |", "| `passive_observed` | `candidate` |"),
        ("no source label determines or\nrestricts the state label.", "each source label determines its state label."),
        (CHECKER.SOURCE_RETENTION, CHECKER.SOURCE_RETENTION.replace("MUST NOT", "MAY")),
        ("`static_seed` / `identity_confirmed`", "`static_seed` / `candidate`"),
        ("`passive_observed` / `identity_confirmed`", "`passive_observed` / `corroborated_pending`"),
        (CHECKER.DEVICES_FACE, "`devices` selects an arbitrary face."),
        (CHECKER.NON_PROOF, "A discovery source or verification state proves a\n"
         "supported device, current qualification, stable cross-address identity, and\n"
         "live behavior."),
        (CHECKER.TOPOLOGY_NON_PROOF, "Topology grouping proves identity."),
        ("canonical or alias face's discovery provenance", "device-level provenance"),
        ("returned device identity remains canonical", "returned identity follows the queried face"),
        ("`device(address:)` returns `null` for an unknown address.", "Unknown lookup behavior is unspecified."),
        ("both\nfields resolve to GraphQL `null`", "both fields resolve to empty strings"),
        ("A slotless entry remains visible through\n`devices` and `device(address:)`", "A slotless entry is excluded."),
        ("This matches MCP, which omits both\nsnake-case provenance members for the same slotless condition.", "MCP behavior is unrelated."),
        ("The current gateway schema exposes", "The future gateway schema will expose"),
        (CHECKER.GATEWAY_REVIEWED_HEAD, "0" * 40),
        (CHECKER.GATEWAY_REVIEWED_MERGE_TREE, "1" * 40),
        (CHECKER.GATEWAY_MAIN_MERGE, "2" * 40),
        (CHECKER.REGISTRY_DEPENDENCY, "3" * 40),
    ),
)
def test_rejects_document_contract_mutations(old: str, new: str) -> None:
    rejects(doc_old=old, doc_new=new)


def test_rejects_missing_or_non_nullable_current_fields() -> None:
    rejects(doc_old="  discoverySource: String\n")
    rejects(doc_old="  verificationState: String\n", doc_new="  verificationState: String!\n")


def test_rejects_appended_stale_pending_section() -> None:
    doc, atr = texts()
    stale = """

### Pending gateway #939/#940 implementation: Device Face Discovery Provenance

This extension is pending gateway #939/#940 implementation and is not present
in the current gateway schema. The future camel-case fields are exactly:

```graphql
extend type Device {
  discoverySource: String
  verificationState: String
}
```
"""
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + stale, atr)


def test_rejects_duplicate_current_provenance_heading() -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + "\n" + CHECKER.HEADING + "\n", atr)


def test_accepts_unrelated_device_extension() -> None:
    doc, atr = texts()
    CHECKER.validate_text(doc + "\nextend type Device { firmwareLabel: String }\n", atr)


def test_rejects_device_definition_moved_out_of_current_types() -> None:
    doc, atr = texts()
    current = CHECKER._current_types_section(doc)
    match = re.search(r"^type Device \{\n.*?^\}\n", current, re.M | re.S)
    assert match is not None
    device = match.group(0)
    moved = doc.replace(device, "", 1) + "\n### Historical Device example\n\n```graphql\n" + device + "```\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(moved, atr)


def test_rejects_duplicate_device_definition_in_current_types() -> None:
    doc, atr = texts()
    next_heading = doc.index("\n### ", doc.index("### Types (Current)") + 1)
    duplicate = "\ntype Device {\n  discoverySource: String!\n}\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc[:next_heading] + duplicate + doc[next_heading:], atr)


@pytest.mark.parametrize(
    "declaration",
    (
        "type Device implements Node { discoverySource: String! }",
        "type Device @key(fields: \"address\") { verificationState: String! }",
    ),
)
def test_rejects_decorated_duplicate_device_definition(declaration: str) -> None:
    doc, atr = texts()
    next_heading = doc.index("\n### ", doc.index("### Types (Current)") + 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc[:next_heading] + "\n" + declaration + "\n" + doc[next_heading:], atr)


def test_rejects_duplicate_current_types_heading() -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + "\n### Types (Current)\n", atr)


@pytest.mark.parametrize(
    "duplicate",
    (
        "discoverySource:String!",
        "\tverificationState:String!",
        "  discoverySource(format: Boolean): String!",
        '  discoverySource(format: String = ")"): String!',
    ),
)
def test_rejects_whitespace_equivalent_duplicate_fields(duplicate: str) -> None:
    doc, atr = texts()
    marker = "  manufacturer: String!"
    assert marker in doc
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace(marker, duplicate + "\n" + marker, 1), atr)


@pytest.mark.parametrize(
    "extension",
    (
        "extend type Device { discoverySource(format: Boolean): String! }",
        "extend type Device implements Node { discoverySource(format: Boolean): String! }",
        "extend type Device @key(fields: \"address\") { verificationState: String! }",
    ),
)
def test_rejects_argument_bearing_provenance_extension(extension: str) -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + "\n" + extension + "\n", atr)


@pytest.mark.parametrize(
    "entry",
    (
        "  - `ebus.v1.registry.devices.get`",
        "  * `ebus.v1.registry.devices.get`",
        "  - `ebus.v1.registry.devices.get` (duplicate)",
    ),
)
def test_rejects_duplicate_mcp_devices_get_entry(entry: str) -> None:
    text = mcp_text() + "\n" + entry + "\n    - provenance is always active_confirmed.\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(text)


def test_rejects_obsolete_atr_spelling() -> None:
    rejects(
        atr_old="verificationState=corroborated_pending`",
        atr_new="verificationState=corroborated`",
    )


def test_rejects_mcp_source_rewrite_rule() -> None:
    text = mcp_text()
    assert CHECKER.MCP_SOURCE_RETENTION in text
    mutated = text.replace(
        CHECKER.MCP_SOURCE_RETENTION,
        "Verification advancement rewrites every source to `active_confirmed`.",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(mutated)


def test_rejects_mcp_source_rewrite_outside_devices_get_entry() -> None:
    text = mcp_text() + "\nactive scan (→ `active_confirmed/identity_confirmed`)\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(text)


@pytest.mark.parametrize(
    "pin",
    (
        CHECKER.GATEWAY_REVIEWED_HEAD,
        CHECKER.GATEWAY_REVIEWED_MERGE_TREE,
        CHECKER.GATEWAY_MAIN_MERGE,
        CHECKER.REGISTRY_DEPENDENCY,
    ),
)
def test_rejects_wrong_mcp_runtime_or_dependency_pin(pin: str) -> None:
    text = mcp_text()
    mutated = text.replace(pin, "f" * 40, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(mutated)
