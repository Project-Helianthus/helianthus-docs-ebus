#!/usr/bin/env python3
"""Validate the current GraphQL and MCP device-face provenance contract."""
from __future__ import annotations

import pathlib
import re
import sys

from graphql import GraphQLError, parse
from markdown_it import MarkdownIt


DOC = pathlib.Path("api/graphql.md")
MCP = pathlib.Path("api/mcp.md")
ATR = pathlib.Path("architecture/atr/07-live-validation-acceptance.md")
HEADING = "### Current Device Face Discovery Provenance"
SOURCES = ("static_seed", "passive_observed", "active_confirmed")
STATES = ("candidate", "corroborated_pending", "identity_confirmed")
INITIAL = (
    ("static_seed", "candidate"),
    ("passive_observed", "corroborated_pending"),
    ("active_confirmed", "identity_confirmed"),
)
GATEWAY_REVIEWED_HEAD = "77b898633672e123a05d39a3cf46398cce2d72ab"
GATEWAY_REVIEWED_MERGE_TREE = "bb8f59fed4be68104d8ab206f55f7f32ea33e031"
GATEWAY_MAIN_MERGE = "f5cd9c51c60bdf422e8fc1b5690fbde52a393be3"
REGISTRY_DEPENDENCY = "e24532a50caa00c113751b98b88239e045d731e8"
PINS = (
    GATEWAY_REVIEWED_HEAD,
    GATEWAY_REVIEWED_MERGE_TREE,
    GATEWAY_MAIN_MERGE,
    REGISTRY_DEPENDENCY,
)
PROVEN_CONCLUSION = "Conclusion: Proven."
MARKDOWN = MarkdownIt("commonmark")
TABLE_MARKDOWN = MarkdownIt("commonmark").enable("table")
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


def _inline_text(token: object) -> str:
    children = getattr(token, "children", None) or ()
    return "".join(
        child.content
        for child in children
        if child.type in ("text", "code_inline", "image")
    )


def _section(text: str) -> str:
    return _heading_section(text, HEADING, "current implementation")


def _heading_section(text: str, heading: str, label: str) -> str:
    start, end = _heading_section_bounds(text, heading, label)
    return text[start:end]


def _heading_section_bounds(text: str, heading: str, label: str) -> tuple[int, int]:
    level = len(heading) - len(heading.lstrip("#"))
    title = heading[level:].strip()
    tokens = MARKDOWN.parse(text)
    matches = [
        index
        for index, token in enumerate(tokens[:-1])
        if token.type == "heading_open"
        and token.level == 0
        and token.tag == f"h{level}"
        and tokens[index + 1].type == "inline"
        and _inline_text(tokens[index + 1]) == title
    ]
    if len(matches) != 1:
        raise CheckError(f"{label} heading must appear exactly once")
    heading_token = tokens[matches[0]]
    assert heading_token.map is not None
    start_line = heading_token.map[0]
    end_line = len(text.splitlines())
    for token in tokens[matches[0] + 1 :]:
        if token.type == "heading_open" and token.level == 0 and int(token.tag[1:]) <= level:
            assert token.map is not None
            end_line = token.map[0]
            break
    offsets = _line_offsets(text)
    return offsets[start_line], offsets[end_line]


def _current_types_section(text: str) -> str:
    return _heading_section(text, "### Types (Current)", "current types")


def _mask_graphql_literals(text: str) -> str:
    """Mask GraphQL strings and comments while preserving offsets/newlines."""
    masked = list(text)
    index = 0
    while index < len(text):
        if text.startswith('"""', index):
            end = index + 3
            while end < len(text):
                if text.startswith('\\"""', end):
                    end += 4
                    continue
                if text.startswith('"""', end):
                    end += 3
                    break
                end += 1
            for position in range(index, min(end, len(text))):
                if masked[position] != "\n":
                    masked[position] = " "
            index = end
            continue
        if text[index] == '"':
            end = index + 1
            while end < len(text):
                if text[end] == "\\":
                    end += 2
                    continue
                end += 1
                if text[end - 1] == '"':
                    break
            for position in range(index, min(end, len(text))):
                if masked[position] != "\n":
                    masked[position] = " "
            index = end
            continue
        if text[index] == "#":
            end = text.find("\n", index)
            end = len(text) if end < 0 else end
            for position in range(index, end):
                masked[position] = " "
            index = end
            continue
        if text[index] in (",", "\ufeff"):
            masked[index] = " "
        index += 1
    return "".join(masked)


def _current_graphql_blocks(types_current: str) -> tuple[str, ...]:
    """Return each fenced GraphQL block inside the current Types section."""
    return tuple(
        token.content
        for token in MARKDOWN.parse(types_current)
        if token.type == "fence"
        and token.level == 0
        and token.info.strip().split(maxsplit=1)
        and token.info.strip().split(maxsplit=1)[0].lower() == "graphql"
    )


def _device_blocks(text: str, *, graphql_literals: bool = True) -> list[tuple[bool, str, str, str]]:
    """Return full Device declarations and bodies with GraphQL nesting honored."""
    masked = _mask_graphql_literals(text) if graphql_literals else text
    ignored = r"[ \t\r\n]+"
    pattern = re.compile(rf"(?<![`A-Za-z0-9_])(?:(extend){ignored})?type{ignored}Device\b(?!`)")
    blocks: list[tuple[bool, str, str, str]] = []
    for match in pattern.finditer(masked):
        parens = brackets = 0
        body_start = -1
        position = match.end()
        definition_words = {
            "schema", "scalar", "type", "interface", "union", "enum", "input",
            "directive", "query", "mutation", "subscription", "fragment",
        }
        in_implements = False
        implements_expect_name = False
        directive_expect_name = False
        while position < len(masked):
            character = masked[position]
            if parens == 0 and brackets == 0:
                if character == "@":
                    in_implements = False
                    directive_expect_name = True
                    position += 1
                    continue
                if character == "&" and in_implements:
                    implements_expect_name = True
                    position += 1
                    continue
                name = re.match(r"[A-Za-z_][A-Za-z0-9_]*", masked[position:])
                if name is not None:
                    value = name.group(0)
                    if implements_expect_name:
                        implements_expect_name = False
                    elif directive_expect_name:
                        directive_expect_name = False
                    elif value == "implements":
                        in_implements = True
                        implements_expect_name = True
                    else:
                        in_implements = False
                        if value in definition_words:
                            break
                    position += len(value)
                    continue
            if character == "(":
                parens += 1
            elif character == ")" and parens:
                parens -= 1
            elif character == "[":
                brackets += 1
            elif character == "]" and brackets:
                brackets -= 1
            elif character == "{" and parens == 0 and brackets == 0:
                body_start = position
                break
            position += 1
        if body_start < 0:
            continue
        depth = 1
        position = body_start + 1
        while position < len(masked) and depth:
            if masked[position] == "{":
                depth += 1
            elif masked[position] == "}":
                depth -= 1
            position += 1
        if depth:
            continue
        body_end = position - 1
        blocks.append((
            bool(match.group(1)),
            text[match.start() : position],
            text[body_start + 1 : body_end],
            masked[body_start + 1 : body_end],
        ))
    return blocks


def _device_fields(masked_body: str) -> tuple[str, ...]:
    tokens = list(re.finditer(r"[A-Za-z_][A-Za-z0-9_]*|[(){}\[\]:!]", masked_body))
    parens = brackets = braces = 0
    fields: list[str] = []
    for index, token in enumerate(tokens):
        value = token.group(0)
        if value == "(":
            parens += 1
        elif value == ")" and parens:
            parens -= 1
        elif value == "[":
            brackets += 1
        elif value == "]" and brackets:
            brackets -= 1
        elif value == "{":
            braces += 1
        elif value == "}" and braces:
            braces -= 1
        elif parens == 0 and brackets == 0 and braces == 0 and re.match(r"^[A-Za-z_]", value):
            following = tokens[index + 1].group(0) if index + 1 < len(tokens) else ""
            if following in ("(", ":"):
                fields.append(value)
    return tuple(fields)


def _prose_device_blocks(text: str) -> list[tuple[bool, str, str, str]]:
    """Find visible declarations without letting earlier prose alter GraphQL lexing."""
    blocks = _device_blocks(text, graphql_literals=False)
    for candidate in re.finditer(r"\b(?:extend|type)\b", text):
        blocks.extend(_device_blocks(text[candidate.start() :]))
    return blocks


def _mask_markdown_fences(text: str) -> str:
    """Mask CommonMark fenced and indented code while preserving offsets/newlines."""
    masked = list(text)
    offsets = _line_offsets(text)
    for token in MARKDOWN.parse(text):
        if token.type not in ("fence", "code_block") or token.map is None:
            continue
        start, end = offsets[token.map[0]], offsets[token.map[1]]
        for position in range(start, end):
            if masked[position] not in "\r\n":
                masked[position] = " "
    return "".join(masked)


def _visible_markdown_text(
    text: str,
    *,
    include_inline_code: bool = False,
    allowed_levels: set[int] | None = None,
    reject_html: bool = False,
    include_html_blocks: bool = False,
) -> str:
    """Return rendered text while excluding code and raw HTML containers."""
    return "".join(_visible_markdown_spans(
        text,
        include_inline_code=include_inline_code,
        allowed_levels=allowed_levels,
        reject_html=reject_html,
        include_html_blocks=include_html_blocks,
    ))


def _visible_markdown_spans(
    text: str,
    *,
    include_inline_code: bool = False,
    allowed_levels: set[int] | None = None,
    reject_html: bool = False,
    include_html_blocks: bool = False,
) -> tuple[str, ...]:
    """Return independent rendered prose spans so literal state cannot leak."""
    visible: list[str] = []
    for token in MARKDOWN.parse(text):
        if reject_html and token.type == "html_block":
            raise CheckError("public contract must not depend on raw HTML")
        if include_html_blocks and token.type == "html_block" and not token.content.lstrip().startswith("<!--"):
            visible.append(token.content + "\n")
            continue
        if (
            token.type != "inline"
            or token.children is None
            or (allowed_levels is not None and token.level not in allowed_levels)
        ):
            continue
        span: list[str] = []
        for child in token.children:
            if reject_html and child.type == "html_inline":
                raise CheckError("public contract must not depend on raw HTML")
            if child.type == "text":
                span.append(child.content)
            elif child.type == "image":
                span.append(child.content)
            elif child.type == "code_inline" and include_inline_code:
                span.append("`" + child.content + "`")
            elif child.type in ("softbreak", "hardbreak"):
                span.append("\n")
        visible.append("".join(span) + "\n")
    return tuple(visible)


def _line_offsets(text: str) -> list[int]:
    """Return character offsets for every CommonMark line boundary."""
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    if offsets[-1] < len(text):
        offsets.append(len(text))
    return offsets


def _mcp_device_section(text: str) -> str:
    inventory = _heading_section(text, "## Implemented Surface", "implemented surface")
    # Raw HTML has no stable Markdown token identity. Reject it in the tool
    # inventory so code-styled aliases cannot evade whole-inventory uniqueness.
    _visible_markdown_text(inventory, reject_html=True)
    core = _list_item(inventory, "Core stable (`ebus.v1.*`)", level=1)
    list_label = "`ebus.v1.registry.devices.list`"
    if len(_list_items(inventory, list_label, level=None)) != 1:
        raise CheckError("MCP registry devices.list must appear once in Implemented Surface")
    list_entries = _list_items(core, list_label, level=3)
    if len(list_entries) != 1 or _first_list_label(list_entries[0]) != list_label:
        raise CheckError("MCP registry devices.list must appear once under Core stable")
    get_label = "`ebus.v1.registry.devices.get`"
    if len(_list_items(inventory, get_label, level=None)) != 1:
        raise CheckError("MCP registry devices.get must appear once in Implemented Surface")
    entries = _list_items(core, get_label, level=3)
    if len(entries) != 1 or _first_list_label(entries[0]) != get_label:
        raise CheckError("MCP registry devices.get must appear once under Core stable")
    return entries[0]


def _list_items(text: str, label: str, *, level: int | None) -> tuple[str, ...]:
    """Return list items whose own first paragraph exactly matches ``label``."""
    lines = text.splitlines(keepends=True)
    matches: list[str] = []
    tokens = MARKDOWN.parse(text)
    for index, token in enumerate(tokens):
        if token.type != "list_item_open" or (level is not None and token.level != level) or token.map is None:
            continue
        item_level = token.level
        for child in tokens[index + 1 :]:
            if child.type == "list_item_close" and child.level == item_level:
                break
            if child.type == "inline" and child.level == item_level + 2:
                matches_label = child.content == label
                if label.startswith("`") and label.endswith("`") and child.children:
                    tool = label[1:-1]
                    matches_label = any(
                        part.type == "code_inline" and part.content == tool
                        for part in child.children
                    )
                    rendered = _inline_text(child)
                    matches_label = matches_label or re.search(
                        rf"(?<![A-Za-z0-9_.-]){re.escape(tool)}(?![A-Za-z0-9_.-])",
                        rendered,
                    ) is not None
                if matches_label:
                    matches.append("".join(lines[token.map[0] : token.map[1]]))
                break
    return tuple(matches)


def _first_list_label(text: str) -> str:
    inline = next((token for token in MARKDOWN.parse(text) if token.type == "inline"), None)
    return "" if inline is None else inline.content


def _list_item(text: str, label: str, *, level: int) -> str:
    matches = _list_items(text, label, level=level)
    if len(matches) != 1:
        raise CheckError(f"MCP {label} list item must appear exactly once")
    return matches[0]


def _validate_pins(section: str, *, surface: str) -> None:
    visible = section
    if tuple(re.findall(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])", visible)) != PINS:
        raise CheckError(f"{surface} provenance pins differ")
    normalized = re.sub(r"\s+", " ", visible)
    required = (
        f"reviewed gateway HEAD `{GATEWAY_REVIEWED_HEAD}`",
        f"reviewed and merge tree is identical at `{GATEWAY_REVIEWED_MERGE_TREE}`",
        f"gateway `main` is `{GATEWAY_MAIN_MERGE}`",
        f"accepted registry dependency is `{REGISTRY_DEPENDENCY}`",
    )
    for fragment in required:
        if fragment not in normalized:
            raise CheckError(f"{surface} provenance pin meaning missing: {fragment!r}")


def _contains_fragment(section: str, fragment: str) -> bool:
    """Match prose by rendered words rather than Markdown source indentation."""
    return re.sub(r"\s+", " ", fragment).strip() in re.sub(r"\s+", " ", section).strip()


def _validate_proven_conclusion(section: str, *, surface: str) -> None:
    conclusions = tuple(re.findall(r"\bConclusion:\s*(Proven|Hypothesis|Unknown)\.", section))
    if conclusions != ("Proven",):
        raise CheckError(f"{surface} provenance conclusion must be Proven only")


def _single_column(section: str, title: str) -> tuple[str, ...]:
    rows = _top_level_table_after(
        section,
        f"Allowed `{title}` labels:",
        ("label",),
        f"{title} label",
    )
    return tuple(row[0] for row in rows)


def _initial_pairs(section: str) -> tuple[tuple[str, str], ...]:
    rows = _top_level_table_after(
        section,
        "Typical initial combinations are examples, not an exhaustive pairing rule:",
        ("`discoverySource`", "`verificationState`"),
        "initial combination",
    )
    return tuple((row[0], row[1]) for row in rows)


def _top_level_table_after(
    section: str,
    prompt: str,
    headers: tuple[str, ...],
    label: str,
) -> tuple[tuple[str, ...], ...]:
    """Return code-span cells from one top-level table after an exact prompt."""
    tokens = TABLE_MARKDOWN.parse(section)
    starts = [
        index + 2
        for index, token in enumerate(tokens)
        if index > 0
        and index + 2 < len(tokens)
        and token.type == "inline"
        and token.level == 1
        and token.content == prompt
        and tokens[index - 1].type == "paragraph_open"
        and tokens[index - 1].level == 0
        and tokens[index + 1].type == "paragraph_close"
        and tokens[index + 1].level == 0
        and tokens[index + 2].type == "table_open"
        and tokens[index + 2].level == 0
    ]
    if len(starts) != 1:
        raise CheckError(f"{label} table missing or not top-level")

    rows: list[list[tuple[str, object]]] = []
    current: list[tuple[str, object]] | None = None
    cell_tag: str | None = None
    for token in tokens[starts[0] + 1 :]:
        if token.type == "table_close" and token.level == 0:
            break
        if token.type == "tr_open":
            current = []
        elif token.type in ("th_open", "td_open"):
            cell_tag = token.tag
        elif token.type == "inline" and current is not None and cell_tag is not None:
            current.append((cell_tag, token))
            cell_tag = None
        elif token.type == "tr_close" and current is not None:
            rows.append(current)
            current = None

    if not rows or tuple(cell[1].content for cell in rows[0]) != headers:
        raise CheckError(f"{label} table header differs")
    if any(cell[0] != "th" for cell in rows[0]):
        raise CheckError(f"{label} table header differs")

    values: list[tuple[str, ...]] = []
    for row in rows[1:]:
        if len(row) != len(headers) or any(cell[0] != "td" for cell in row):
            raise CheckError(f"{label} table row differs")
        parsed: list[str] = []
        for _, token in row:
            children = getattr(token, "children", None) or ()
            if len(children) != 1 or children[0].type != "code_inline":
                raise CheckError(f"{label} table values must be code labels")
            parsed.append(children[0].content)
        values.append(tuple(parsed))
    return tuple(values)


def validate_text(text: str, atr: str) -> None:
    # Public contract checks are source-stable only when visible prose is
    # represented by Markdown tokens rather than browser-decoded raw HTML.
    _visible_markdown_text(text, reject_html=True)
    visible_text = text
    current_start, current_end = _heading_section_bounds(
        visible_text,
        "### Types (Current)",
        "current types",
    )
    types_current = visible_text[current_start:current_end]
    current_graphql_blocks = _current_graphql_blocks(types_current)
    current_sdl = "\n".join(current_graphql_blocks)
    if "<!--" in _mask_graphql_literals(current_sdl):
        raise CheckError("current GraphQL SDL contains HTML comment syntax")
    current_blocks = [
        block
        for graphql_block in current_graphql_blocks
        for block in _device_blocks(graphql_block)
        if not block[0]
    ]
    if len(current_blocks) != 1:
        raise CheckError("current types must contain exactly one Device definition")
    documents = []
    for graphql_block in current_graphql_blocks:
        try:
            documents.append(parse(graphql_block))
        except GraphQLError as error:
            raise CheckError(f"current GraphQL fence is invalid: {error.message}") from error
    device_definitions = [
        definition
        for document in documents
        for definition in document.definitions
        if definition.kind == "object_type_definition" and definition.name.value == "Device"
    ]
    if len(device_definitions) != 1:
        raise CheckError("current types must contain exactly one Device definition")
    prose_spans = (
        _visible_markdown_spans(visible_text[:current_start], include_html_blocks=True)
        + _visible_markdown_spans(types_current, include_html_blocks=True)
        + _visible_markdown_spans(visible_text[current_end:], include_html_blocks=True)
    )
    all_fields = [
        field
        for span in prose_spans
        for _, _, _, block in _prose_device_blocks(span)
        for field in _device_fields(block)
    ]
    all_fields.extend(
        field
        for graphql_block in current_graphql_blocks
        for _, _, _, block in _device_blocks(graphql_block)
        for field in _device_fields(block)
    )
    device_fields = [
        field
        for document in documents
        for definition in document.definitions
        if definition.kind in ("object_type_definition", "object_type_extension")
        and definition.name.value == "Device"
        for field in (definition.fields or ())
    ]
    for name in ("discoverySource", "verificationState"):
        declarations = [field for field in device_fields if field.name.value == name]
        if (
            all_fields.count(name) != 1
            or len(declarations) != 1
            or declarations[0].arguments
            or declarations[0].type.kind != "named_type"
            or declarations[0].type.name.value != "String"
        ):
            raise CheckError("current Device must declare exact nullable camel-case fields")

    section = _visible_markdown_text(
        _section(visible_text),
        include_inline_code=True,
        allowed_levels={1},
        reject_html=True,
    )
    stale = (
        "Pending gateway #939/#940 implementation",
        "pending gateway #939/#940 implementation",
        "is not present in the current gateway schema",
        "future camel-case fields",
    )
    normalized_visible = re.sub(
        r"\s+",
        " ",
        _visible_markdown_text(visible_text, include_inline_code=True),
    )
    if any(re.sub(r"\s+", " ", fragment) in normalized_visible for fragment in stale):
        raise CheckError("stale pending provenance status remains")
    if not _contains_fragment(section, "The current gateway schema exposes the nullable camel-case fields"):
        raise CheckError("current provenance status missing")
    _validate_proven_conclusion(section, surface="GraphQL")
    _validate_pins(section, surface="GraphQL")
    source_section = _mask_markdown_fences(_section(visible_text))
    if _single_column(source_section, "discoverySource") != SOURCES:
        raise CheckError("discoverySource label set differs")
    if _single_column(source_section, "verificationState") != STATES:
        raise CheckError("verificationState label set differs")
    if _initial_pairs(source_section) != INITIAL:
        raise CheckError("initial combination examples differ")
    if not _contains_fragment(section, INDEPENDENCE):
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
        if not _contains_fragment(section, fragment):
            raise CheckError(f"required provenance rule missing: {fragment!r}")

    obsolete = "verificationState=corroborated`"
    canonical = "verificationState=corroborated_pending`"
    if obsolete in atr or atr.count(canonical) != 1:
        raise CheckError("ATR must use one canonical corroborated_pending label")


def validate_mcp_text(text: str) -> None:
    _visible_markdown_text(text, reject_html=True)
    section = _visible_markdown_text(
        _mcp_device_section(text),
        include_inline_code=True,
        reject_html=True,
    )
    _validate_proven_conclusion(section, surface="MCP")
    _validate_pins(section, surface="MCP")
    required = (
        "JSON response items carry `discovery_source` and\n      `verification_state` fields",
        "`passive_observed | static_seed | active_confirmed`",
        "`candidate | corroborated_pending | identity_confirmed`",
        "Both are omitted when the registry has no slot record for the\n      address.",
        "For `devices.list` the labels reflect the entry's\n      canonical primary address; for `devices.get(address=X)` the labels\n      reflect the queried address X.",
        MCP_SOURCE_RETENTION,
    )
    for fragment in required:
        if not _contains_fragment(section, fragment):
            raise CheckError(f"required MCP provenance rule missing: {fragment!r}")
    if re.search(
        r"active\s+scan\s*\(\s*→\s*`active_confirmed\s*/\s*identity_confirmed`\s*\)",
        _visible_markdown_text(text, include_inline_code=True),
    ):
        raise CheckError("MCP source-rewrite rule remains")


def main() -> int:
    try:
        validate_text(DOC.read_text(encoding="utf-8"), ATR.read_text(encoding="utf-8"))
        validate_mcp_text(MCP.read_text(encoding="utf-8"))
    except CheckError as error:
        print(f"graphql_face_provenance_error: {error}", file=sys.stderr)
        return 1
    print("graphql_face_provenance_ok sources=3 states=3 initial=3 current=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
