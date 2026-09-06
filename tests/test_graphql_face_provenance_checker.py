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


@pytest.mark.parametrize(
    ("old", "new"),
    (
        ("  discoverySource: String\n", "  discoverySource:\n    String\n"),
        ("  verificationState: String\n", "  verificationState: # ignored token\n    String\n"),
    ),
)
def test_accepts_nullable_fields_across_ignored_tokens(old: str, new: str) -> None:
    doc, atr = texts()
    assert old in doc
    CHECKER.validate_text(doc.replace(old, new, 1), atr)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        ("  discoverySource: String\n", "  discoverySource:\n    String!\n"),
        ("  verificationState: String\n", "  verificationState:\n    Boolean\n"),
        ("  verificationState: String\n", "  verificationState:\n    [String]\n"),
    ),
)
def test_rejects_non_nullable_or_non_string_tokenized_fields(old: str, new: str) -> None:
    rejects(doc_old=old, doc_new=new)


def test_rejects_nullable_spelling_hidden_in_description() -> None:
    replacement = (
        '  """Example:  discoverySource: String"""\n'
        "  discoverySource: String!\n"
    )
    rejects(doc_old="  discoverySource: String\n", doc_new=replacement)


def hide_pin_paragraph(text: str) -> str:
    first = text.index(CHECKER.GATEWAY_REVIEWED_HEAD)
    start = text.rfind("\n", 0, first) + 1
    last = text.index(CHECKER.REGISTRY_DEPENDENCY)
    end = text.find("\n", last)
    end = len(text) if end < 0 else end + 1
    return text[:start] + "<!--\n" + text[start:end] + "-->\n" + text[end:]


def test_rejects_graphql_pins_hidden_in_html_comment() -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(hide_pin_paragraph(doc), atr)


def test_rejects_mcp_pins_hidden_in_html_comment() -> None:
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(hide_pin_paragraph(mcp_text()))


def test_rejects_mcp_rule_hidden_in_html_comment() -> None:
    text = mcp_text()
    assert CHECKER.MCP_SOURCE_RETENTION in text
    hidden = text.replace(
        CHECKER.MCP_SOURCE_RETENTION,
        "<!--\n" + CHECKER.MCP_SOURCE_RETENTION + "\n-->",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(hidden)


@pytest.mark.parametrize("scope", ("block", "fields"))
def test_rejects_current_schema_hidden_in_html_comment(scope: str) -> None:
    doc, atr = texts()
    if scope == "block":
        current = CHECKER._current_types_section(doc)
        match = re.search(r"^type Device \{\n.*?^\}\n", current, re.M | re.S)
        assert match is not None
        hidden = match.group(0)
    else:
        hidden = "  discoverySource: String\n  verificationState: String\n"
        assert hidden in doc
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(
            doc.replace(hidden, "<!--\n" + hidden + "-->\n", 1),
            atr,
        )


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


def test_rejects_fenced_example_as_current_provenance_heading() -> None:
    doc, atr = texts()
    replacement = f"```markdown\n{CHECKER.HEADING}\n```"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace(CHECKER.HEADING, replacement, 1), atr)


def test_accepts_fenced_example_beside_real_provenance_heading() -> None:
    doc, atr = texts()
    CHECKER.validate_text(doc + f"\n```markdown\n{CHECKER.HEADING}\n```\n", atr)


@pytest.mark.parametrize(
    "stale",
    (
        "is not present in the current gateway schema",
        "is\nnot\tpresent   in\n the current\tgateway schema",
    ),
)
def test_rejects_stale_gateway_sentence_after_whitespace_reflow(stale: str) -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + "\n" + stale + "\n", atr)


def test_accepts_unrelated_device_extension() -> None:
    doc, atr = texts()
    CHECKER.validate_text(doc + "\nextend type Device { firmwareLabel: String }\n", atr)


def test_accepts_same_field_name_on_unrelated_type() -> None:
    doc, atr = texts()
    CHECKER.validate_text(doc + "\ntype Other { discoverySource: String }\n", atr)


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
        "type\n  Device { firmwareLabel: String }",
        "type # ignored GraphQL comment\n Device { firmwareLabel: String }",
        "type, Device { firmwareLabel: String }",
        "type\ufeffDevice { firmwareLabel: String }",
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


def test_rejects_device_moved_below_higher_level_heading() -> None:
    doc, atr = texts()
    current = CHECKER._current_types_section(doc)
    match = re.search(r"^type Device \{\n.*?^\}\n", current, re.M | re.S)
    assert match is not None
    device = match.group(0)
    moved = doc.replace(device, "", 1)
    insertion = moved.index("\n### Current Device Face Discovery Provenance")
    moved = moved[:insertion] + "\n## Historical schema\n\n```graphql\n" + device + "```\n" + moved[insertion:]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(moved, atr)


@pytest.mark.parametrize(
    "duplicate",
    (
        "discoverySource:String!",
        "\tverificationState:String!",
        "  discoverySource(format: Boolean): String!",
        '  discoverySource(format: String = ")"): String!',
        "  discoverySource # ignored GraphQL comment\n  : String!",
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
        "extend type # ignored GraphQL comment\n Device { discoverySource # ignored\n : String! }",
        "extend, type, Device { discoverySource: String! }",
        "extend\ufefftype\ufeffDevice { discoverySource: String! }",
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
    marker = "  - `ebus.v1.registry.devices.get`\n"
    text = mcp_text().replace(marker, marker + entry + "\n", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(text)


def test_accepts_non_inventory_mcp_tool_reference() -> None:
    CHECKER.validate_mcp_text(mcp_text() + "\nSee `ebus.v1.registry.devices.get` for the current tool.\n")


def test_accepts_fenced_non_inventory_mcp_example() -> None:
    CHECKER.validate_mcp_text(
        mcp_text() + "\n```text\n- `ebus.v1.registry.devices.get`\n```\n"
    )


def test_accepts_indented_non_inventory_mcp_example() -> None:
    heading = "## Implemented Surface\n"
    CHECKER.validate_mcp_text(
        mcp_text().replace(
            heading,
            heading + "\n    - `ebus.v1.registry.devices.get`\n",
            1,
        )
    )


@pytest.mark.parametrize("marker", ("*", "+", "1."))
def test_mcp_section_stops_at_supported_sibling_markers(marker: str) -> None:
    sibling = "  - `ebus.v1.registry.planes.list`"
    text = mcp_text().replace(
        sibling,
        f"  {marker} `ebus.v1.registry.planes.list`",
        1,
    )
    assert "ebus.v1.registry.planes.list" not in CHECKER._mcp_device_section(text)


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


def test_rejects_whitespace_variant_mcp_source_rewrite() -> None:
    text = mcp_text() + "\nactive  scan ( → `active_confirmed / identity_confirmed` )\n"
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
