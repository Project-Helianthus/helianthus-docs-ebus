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


@pytest.mark.parametrize(
    "heading",
    (
        "### Current Device Face Discovery *Provenance*",
        "### Types *(Current)*",
    ),
)
def test_rejects_duplicate_rendered_heading_with_inline_markup(heading: str) -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + "\n" + heading + "\n", atr)


def test_rejects_duplicate_rendered_heading_with_image_alt_text() -> None:
    doc, atr = texts()
    duplicate = "### Current Device Face Discovery ![Provenance](missing.png)"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + "\n" + duplicate + "\n", atr)


def test_rejects_fenced_example_as_current_provenance_heading() -> None:
    doc, atr = texts()
    replacement = f"```markdown\n{CHECKER.HEADING}\n```"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace(CHECKER.HEADING, replacement, 1), atr)


def test_accepts_fenced_example_beside_real_provenance_heading() -> None:
    doc, atr = texts()
    CHECKER.validate_text(doc + f"\n```markdown\n{CHECKER.HEADING}\n```\n", atr)


def test_rejects_heading_behind_invalid_fence_closer() -> None:
    doc, atr = texts()
    replacement = f"```markdown\n{CHECKER.HEADING}\n``` trailing text"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace(CHECKER.HEADING, replacement, 1), atr)


def test_accepts_heading_after_complete_fence_closer() -> None:
    doc, atr = texts()
    CHECKER.validate_text(doc + "\n```graphql info string\nexample\n```   \n", atr)


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


def test_accepts_directive_only_device_extension_before_other_definition() -> None:
    doc, atr = texts()
    CHECKER.validate_text(
        doc + "\nextend type Device @tag\ntype Other { discoverySource: String }\n",
        atr,
    )


def test_accepts_directive_only_device_extension_before_query_definition() -> None:
    doc, atr = texts()
    CHECKER.validate_text(
        doc + "\nextend type Device @tag\nquery Q { discoverySource(format: true) }\n",
        atr,
    )


@pytest.mark.parametrize(
    "following",
    (
        "type Other { discoverySource: String }",
        "interface Other { discoverySource: String }",
        "enum Other { discoverySource }",
        "input Other { discoverySource: String }",
    ),
)
def test_directive_only_device_extension_stops_at_any_following_definition(following: str) -> None:
    doc, atr = texts()
    CHECKER.validate_text(doc + "\nextend type Device @tag " + following + "\n", atr)


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
    fence = doc.index("```graphql\n", doc.index("### Types (Current)"))
    close = doc.index("```\n", fence + len("```graphql\n"))
    duplicate = "\ntype Device {\n  discoverySource: String!\n}\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc[:close] + duplicate + doc[close:], atr)


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
    fence = doc.index("```graphql\n", doc.index("### Types (Current)"))
    close = doc.index("```\n", fence + len("```graphql\n"))
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc[:close] + "\n" + declaration + "\n" + doc[close:], atr)


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
        "   - `ebus.v1.registry.devices.get`",
        "  * `ebus.v1.registry.devices.get`",
        "  - `ebus.v1.registry.devices.get` (duplicate)",
    ),
)
def test_rejects_duplicate_mcp_devices_get_entry(entry: str) -> None:
    marker = "  - `ebus.v1.registry.devices.get`\n"
    text = mcp_text().replace(marker, marker + entry + "\n", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(text)


@pytest.mark.parametrize("replacement", ("", "  - `ebus.v1.registry.devices.scan`\n"))
def test_requires_exactly_one_mcp_devices_list_entry(replacement: str) -> None:
    marker = "  - `ebus.v1.registry.devices.list`\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(mcp_text().replace(marker, replacement, 1))


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

def test_ignores_historical_device_outside_current_sdl_fence() -> None:
    doc, atr = texts()
    historical = '\n## Historical SDL\n\n```graphql\ntype Device { discoverySource: String! verificationState: String! }\n```\n'
    CHECKER.validate_text(doc + historical, atr)


def test_rejects_four_space_fence_closer() -> None:
    doc, atr = texts()
    hidden = '```graphql\n    ```\n' + CHECKER.HEADING + '\n```\n'
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(hidden, atr)


def test_mcp_section_stops_at_column_zero_parent() -> None:
    text = mcp_text()
    marker = '  - `ebus.v1.registry.devices.get`\n'
    text = text.replace(marker, marker + '- unrelated parent\n', 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(text)


def test_mcp_section_stops_at_three_space_sibling() -> None:
    text = mcp_text()
    marker = '  - `ebus.v1.registry.devices.get`\n'
    text = text.replace(marker, marker + '   - unrelated sibling\n', 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(text)

def test_rejects_mixed_fence_delimiter_closer() -> None:
    doc, atr = texts()
    hidden = '```graphql\n```~~~\n' + CHECKER.HEADING + '\n```\n'
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(hidden, atr)


def test_ignores_illustrative_fenced_device_schema_outside_current_schema() -> None:
    doc, atr = texts()
    illustrative = '\n## Example\n\n```graphql\nextend type Device { discoverySource: String! verificationState: String! }\n```\n'
    CHECKER.validate_text(doc + illustrative, atr)

def test_rejects_device_outside_current_graphql_fence() -> None:
    doc, atr = texts()
    marker = '```graphql\n'
    start = doc.index(marker, doc.index('### Types (Current)'))
    close = doc.index('```\n', start + len(marker))
    device_start = doc.index('type Device', start)
    moved = doc[:device_start] + '```\n' + doc[device_start:close] + '```graphql\n' + doc[close:]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(moved, atr)


def test_accepts_homogeneous_fence_with_info_string() -> None:
    doc, atr = texts()
    CHECKER.validate_text(doc + '\n```graphql example\ntype Other { x: String }\n```\n', atr)


def test_ignores_non_graphql_fence_inside_current_types() -> None:
    doc, atr = texts()
    boundary = '\n### Current Device Face Discovery Provenance'
    example = '\n```text\ntype Device { discoverySource: String! }\n```\n'
    CHECKER.validate_text(doc.replace(boundary, example + boundary, 1), atr)


@pytest.mark.parametrize("separator", ("\u00a0", "\v"))
def test_rejects_non_graphql_device_token_separator(separator: str) -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace("type Device {", "type" + separator + "Device {", 1), atr)


def test_rejects_html_comment_syntax_inside_current_sdl() -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace("discoverySource: String", "discoverySource: <!-- --> String", 1), atr)


def test_accepts_html_comment_text_inside_graphql_description() -> None:
    doc, atr = texts()
    CHECKER.validate_text(doc.replace("  discoverySource: String", '  """literal <!-- --> text"""\n  discoverySource: String', 1), atr)


def test_rejects_backtick_in_backtick_fence_info_string() -> None:
    doc, atr = texts()
    marker = "```graphql\n"
    start = doc.index(marker, doc.index("### Types (Current)"))
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc[:start] + "```graphql`\n" + doc[start + len(marker):], atr)


def test_fenced_literal_comment_opener_does_not_hide_later_markdown_comment() -> None:
    doc, atr = texts()
    doc = doc.replace("  discoverySource: String", '  """literal <!-- text"""\n  discoverySource: String', 1)
    section = CHECKER._section(doc)
    hidden = doc.replace(section, "<!--\n" + section + "\n-->\n", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(hidden, atr)


@pytest.mark.parametrize(
    "suffix",
    (
        " @deprecated !",
        " garbage",
        " @deprecated garbage",
        " @deprecated(reason: \"legacy\") !",
    ),
)
def test_rejects_invalid_trailing_tokens_after_nullable_field(suffix: str) -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(
            doc.replace("  discoverySource: String", "  discoverySource: String" + suffix, 1),
            atr,
        )


def test_accepts_legal_trailing_directive_after_nullable_field() -> None:
    doc, atr = texts()
    CHECKER.validate_text(
        doc.replace(
            "  discoverySource: String",
            '  discoverySource: String @deprecated(reason: "legacy")',
            1,
        ),
        atr,
    )


@pytest.mark.parametrize(
    "header",
    (
        "type Device garbage {",
        "type Device implements {",
    ),
)
def test_rejects_malformed_current_device_header(header: str) -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace("type Device {", header, 1), atr)


def test_accepts_legal_current_device_header_modifiers() -> None:
    doc, atr = texts()
    CHECKER.validate_text(
        doc.replace(
            "type Device {",
            'type Device implements Node @key(fields: "address") {',
            1,
        ),
        atr,
    )


def test_rejects_device_definition_split_across_graphql_fences() -> None:
    doc, atr = texts()
    split = doc.replace(
        "  discoverySource: String",
        "```\nprose between invalid SDL fragments\n```graphql\n  discoverySource: String",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(split, atr)


def test_invalid_backtick_opener_does_not_hide_duplicate_heading() -> None:
    doc, atr = texts()
    duplicate = doc + "\n```graphql`\n" + CHECKER.HEADING + "\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(duplicate, atr)


@pytest.mark.parametrize("indent", (" ", "  ", "   "))
def test_rejects_indented_duplicate_atx_headings(indent: str) -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + "\n" + indent + CHECKER.HEADING + "\n", atr)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + "\n" + indent + "### Types (Current)\n", atr)


def test_rejects_invalid_tokens_after_current_device_definition() -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace("}\n\ntype Plane", "}\ngarbage\n\ntype Plane", 1), atr)


def test_setext_heading_ends_current_types_section() -> None:
    doc, atr = texts()
    current = CHECKER._current_types_section(doc)
    match = re.search(r"^type Device \{\n.*?^\}\n", current, re.M | re.S)
    assert match is not None
    moved = doc.replace(match.group(0), "Historical schema\n---\n" + match.group(0), 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(moved, atr)


def test_setext_heading_ends_provenance_section() -> None:
    doc, atr = texts()
    separated = doc.replace(
        CHECKER.HEADING + "\n",
        CHECKER.HEADING + "\n\nHistorical rules\n---\n",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(separated, atr)


@pytest.mark.parametrize("indent", ("    ", "\t"))
def test_ignores_indented_historical_device_examples(indent: str) -> None:
    doc, atr = texts()
    CHECKER.validate_text(
        doc + "\n" + indent + "extend type Device { discoverySource: String }\n",
        atr,
    )


def test_rejects_provenance_section_hidden_in_raw_html_block() -> None:
    doc, atr = texts()
    section = CHECKER._section(doc)
    hidden = doc.replace(section, "<pre>\n" + section + "</pre>\n", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(hidden, atr)


@pytest.mark.parametrize(
    "visible_html",
    (
        "<div>extend type Device { discovery&#83;ource: String! }</div>",
        "<div>extend type Device { discoverySource&colon; String! }</div>",
        "<div>Pending gateway #939/#940 implementation</div>",
    ),
)
def test_rejects_raw_html_contract_bypass_anywhere(visible_html: str) -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + "\n" + visible_html + "\n", atr)


def test_rejects_raw_html_stale_mcp_rule_anywhere() -> None:
    text = mcp_text()
    stale = "<div>active scan (→ active_confirmed / identity_confirmed)</div>"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(text + "\n" + stale + "\n")


def test_ignores_inline_code_device_example() -> None:
    doc, atr = texts()
    CHECKER.validate_text(
        doc + "\n`extend type Device { discoverySource: String }`\n",
        atr,
    )


def test_rejects_device_extension_in_image_alt_text() -> None:
    doc, atr = texts()
    alt_declaration = "![extend type Device { discoverySource: String! }](missing.png)"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + "\n" + alt_declaration + "\n", atr)


@pytest.mark.parametrize("heading", ("### Types (Current)", CHECKER.HEADING))
def test_rejects_blockquoted_contract_heading(heading: str) -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace(heading, "> " + heading, 1), atr)


def test_rejects_provenance_contract_wrapped_in_fence() -> None:
    doc, atr = texts()
    section = CHECKER._section(doc)
    heading, body = section.split("\n", 1)
    fenced = heading + "\n\n~~~text\n" + body + "~~~\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace(section, fenced, 1), atr)


def test_rejects_mcp_contract_wrapped_in_fence() -> None:
    text = mcp_text()
    section = CHECKER._mcp_device_section(text)
    first, body = section.split("\n", 1)
    fenced = first + "\n    ~~~text\n" + body + "    ~~~\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(text.replace(section, fenced, 1))


def test_rejects_devices_get_moved_under_legacy_aliases() -> None:
    text = mcp_text()
    section = CHECKER._mcp_device_section(text)
    moved = text.replace(section, "", 1).replace(
        "- Legacy aliases\n",
        "- Legacy aliases\n" + section,
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(moved)


def test_rejects_devices_get_duplicated_under_legacy_aliases() -> None:
    text = mcp_text()
    duplicate = "  - `ebus.v1.registry.devices.get`\n"
    mutated = text.replace("- Legacy aliases\n", "- Legacy aliases\n" + duplicate, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(mutated)


def test_rejects_duplicate_contract_heading_after_inline_comment_literal() -> None:
    doc, atr = texts()
    appended = "\n`<!--`\n\n" + CHECKER.HEADING + "\n\n-->\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + appended, atr)


def test_rejects_four_space_core_devices_get_duplicate() -> None:
    text = mcp_text()
    duplicate = "    - `ebus.v1.registry.devices.get`\n"
    mutated = text.replace(
        "- Core stable (`ebus.v1.*`)\n",
        "- Core stable (`ebus.v1.*`)\n" + duplicate,
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(mutated)


def test_rejects_annotated_core_devices_get_duplicate() -> None:
    text = mcp_text()
    duplicate = "  - `ebus.v1.registry.devices.get` (deprecated)\n"
    mutated = text.replace(
        "  - `ebus.v1.registry.planes.list`\n",
        "  - `ebus.v1.registry.planes.list`\n" + duplicate,
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(mutated)


def test_rejects_formatted_devices_get_duplicate_under_legacy_aliases() -> None:
    text = mcp_text()
    duplicate = "  - **`ebus.v1.registry.devices.get`**\n"
    mutated = text.replace("- Legacy aliases\n", "- Legacy aliases\n" + duplicate, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(mutated)


@pytest.mark.parametrize(
    "tool",
    (
        "ebus.v1.registry.devices.get",
        "ebus.v1.registry.devices.list",
    ),
)
def test_rejects_prefixed_device_tool_duplicate_under_legacy_aliases(tool: str) -> None:
    text = mcp_text()
    duplicate = f"  - Deprecated: `{tool}`\n"
    mutated = text.replace("- Legacy aliases\n", "- Legacy aliases\n" + duplicate, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(mutated)


@pytest.mark.parametrize(
    "tool",
    (
        "ebus.v1.registry.devices.get",
        "ebus.v1.registry.devices.list",
    ),
)
def test_rejects_plain_device_tool_duplicate_under_legacy_aliases(tool: str) -> None:
    text = mcp_text()
    duplicate = f"  - {tool}\n"
    mutated = text.replace("- Legacy aliases\n", "- Legacy aliases\n" + duplicate, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(mutated)


@pytest.mark.parametrize(
    "tool",
    (
        "ebus.v1.registry.devices.get",
        "ebus.v1.registry.devices.list",
    ),
)
def test_rejects_html_code_device_tool_duplicate_under_legacy_aliases(tool: str) -> None:
    text = mcp_text()
    duplicate = f"  - <code>{tool}</code>\n"
    mutated = text.replace("- Legacy aliases\n", "- Legacy aliases\n" + duplicate, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(mutated)


@pytest.mark.parametrize("title", ("discoverySource", "verificationState"))
def test_rejects_label_table_inside_lazy_blockquote(title: str) -> None:
    doc, atr = texts()
    prompt = f"Allowed `{title}` labels:"
    mutation = f"> {prompt}\n| label |"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace(prompt + "\n\n| label |", mutation, 1), atr)


def test_rejects_initial_pair_table_inside_lazy_blockquote() -> None:
    doc, atr = texts()
    prompt = "Typical initial combinations are examples, not an exhaustive pairing rule:"
    mutation = f"> {prompt}\n| `discoverySource` | `verificationState` |"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(
            doc.replace(
                prompt + "\n\n| `discoverySource` | `verificationState` |",
                mutation,
                1,
            ),
            atr,
        )


def test_rejects_provenance_contract_inside_hidden_html_container() -> None:
    doc, atr = texts()
    section = CHECKER._section(doc)
    heading, body = section.split("\n", 1)
    hidden = heading + "\n\n<div hidden>\n\n" + body + "\n</div>\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace(section, hidden, 1), atr)


def test_rejects_mcp_provenance_inside_hidden_html_container() -> None:
    text = mcp_text()
    section = CHECKER._mcp_device_section(text)
    first, body = section.split("\n", 1)
    hidden = first + "    <div hidden>\n\n" + body + "\n    </div>\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(text.replace(section, hidden, 1))


@pytest.mark.parametrize("prefix", ("> ", "  - "))
def test_rejects_nested_current_graphql_fence(prefix: str) -> None:
    doc, atr = texts()
    current = CHECKER._current_types_section(doc)
    lines = current.splitlines(keepends=True)
    start = next(index for index, line in enumerate(lines) if line == "```graphql\n")
    end = next(index for index in range(start + 1, len(lines)) if lines[index] == "```\n")
    for index in range(start, end + 1):
        lines[index] = prefix + lines[index]
    nested = "".join(lines)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace(current, nested, 1), atr)


def test_rejects_visible_device_extension_beside_current_sdl() -> None:
    doc, atr = texts()
    current = CHECKER._current_types_section(doc)
    contradictory = "\nextend type Device { discoverySource: String! }\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace(current, current + contradictory, 1), atr)


@pytest.mark.parametrize("interface_name", ("type", "extend", "schema"))
def test_rejects_visible_device_extension_with_keyword_named_interface(interface_name: str) -> None:
    doc, atr = texts()
    contradictory = f"\nextend type Device implements {interface_name} {{ discoverySource: String! }}\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + contradictory, atr)


def test_rejects_visible_device_extension_after_fenced_copy_of_current_types() -> None:
    doc, atr = texts()
    current = CHECKER._current_types_section(doc)
    example = "````markdown\n" + current + "````\n\n"
    contradictory = "extend type Device { discoverySource: String! }\n\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace(current, example + contradictory + current, 1), atr)


def test_rejects_weakened_graphql_and_mcp_conclusion_labels() -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace(CHECKER.PROVEN_CONCLUSION, "Conclusion: Hypothesis.", 1), atr)
    text = mcp_text()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(text.replace(CHECKER.PROVEN_CONCLUSION, "Conclusion: Unknown.", 1))


def test_rejects_contradictory_graphql_and_mcp_conclusion_labels() -> None:
    doc, atr = texts()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc.replace(CHECKER.PROVEN_CONCLUSION, CHECKER.PROVEN_CONCLUSION + "\n\nConclusion: Unknown.", 1), atr)
    text = mcp_text()
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(text.replace(CHECKER.PROVEN_CONCLUSION, CHECKER.PROVEN_CONCLUSION + " Conclusion: Unknown.", 1))


def test_rejects_device_extension_after_unmatched_quote_in_prior_prose() -> None:
    doc, atr = texts()
    appended = '\n"\n\nextend type Device { discoverySource: String! }\n'
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + appended, atr)


def test_rejects_device_extension_after_markdown_hash_in_same_prose_span() -> None:
    doc, atr = texts()
    appended = "\nVariant #1: extend type Device { discoverySource: String! }\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + appended, atr)


def test_rejects_visible_device_declaration_with_bounded_graphql_comment() -> None:
    doc, atr = texts()
    appended = "\ntype # note\nDevice { discoverySource: String! }\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + appended, atr)


def test_rejects_visible_device_extension_inside_raw_html_block() -> None:
    doc, atr = texts()
    appended = "\n<div>\nextend type Device { verificationState: String! }\n</div>\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc + appended, atr)


@pytest.mark.parametrize("title", ("discoverySource", "verificationState"))
def test_rejects_escaped_pipe_label_paragraph(title: str) -> None:
    doc, atr = texts()
    start = doc.index(f"Allowed `{title}` labels:")
    table_start = doc.index("| label |", start)
    table_end = doc.index("\n\n", table_start)
    table = doc[table_start:table_end]
    escaped = table.replace("|", r"\|")
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc[:table_start] + escaped + doc[table_end:], atr)
