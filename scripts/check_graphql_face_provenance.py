#!/usr/bin/env python3
"""Validate the current GraphQL and MCP device-face provenance contract."""
from __future__ import annotations

import pathlib
import re
import sys


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
    return _heading_section(text, HEADING, "current implementation")


def _heading_section(text: str, heading: str, label: str) -> str:
    masked_text = _mask_markdown_fences(text)
    matches = list(re.finditer(rf"(?m)^{re.escape(heading)}[ \t]*$", masked_text))
    if len(matches) != 1:
        raise CheckError(f"{label} heading must appear exactly once")
    start = matches[0].start()
    remainder = masked_text[matches[0].end() :]
    level = len(heading) - len(heading.lstrip("#"))
    end = re.search(rf"(?m)^#{{1,{level}}}[ \t]+", remainder)
    return text[start : matches[0].end() + (end.start() if end else len(remainder))]


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


def _device_blocks(text: str) -> list[tuple[bool, str, str]]:
    """Return Device definition/extension bodies with GraphQL nesting honored."""
    masked = _mask_graphql_literals(text)
    pattern = re.compile(r"(?<![`A-Za-z0-9_])(?:(extend)\s+)?type\s+Device\b(?!`)")
    blocks: list[tuple[bool, str, str]] = []
    for match in pattern.finditer(masked):
        parens = brackets = 0
        body_start = -1
        position = match.end()
        definition = re.compile(
            r"(?:(?:extend)\s+)?(?:schema|scalar|type|interface|union|enum|input|directive)\b"
        )
        while position < len(masked):
            if (
                parens == 0
                and brackets == 0
                and (position == 0 or masked[position - 1] not in "@_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
                and definition.match(masked, position)
            ):
                break
            character = masked[position]
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
        blocks.append((bool(match.group(1)), text[body_start + 1 : body_end], masked[body_start + 1 : body_end]))
    return blocks


def _device_field_tokens(masked_body: str) -> tuple[tuple[str, str, bool], ...]:
    """Return top-level field name/type/nullability from ignored-token-free input."""
    tokens = list(re.finditer(r"[A-Za-z_][A-Za-z0-9_]*|[(){}\[\]:!]", masked_body))
    parens = brackets = braces = 0
    fields: list[tuple[str, str, bool]] = []
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
            if following == ":":
                type_name = tokens[index + 2].group(0) if index + 2 < len(tokens) else ""
                nullable = index + 3 >= len(tokens) or tokens[index + 3].group(0) != "!"
                fields.append((value, type_name, nullable))
    return tuple(fields)


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


def _mask_markdown_fences(text: str) -> str:
    """Mask fenced code blocks while preserving offsets/newlines."""
    masked: list[str] = []
    fence_character = ""
    fence_length = 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^[ \t]*([~`]{3,})", line)
        closer = re.match(r"^[ \t]*([~`]{3,})[ \t]*(?:\r?\n)?$", line)
        is_open = not fence_character and marker is not None
        is_close = (
            bool(fence_character)
            and closer is not None
            and closer.group(1)[0] == fence_character
            and len(closer.group(1)) >= fence_length
        )
        if fence_character or is_open:
            masked.append("".join("\n" if character == "\n" else " " for character in line))
        else:
            masked.append(line)
        if is_open:
            fence_character = marker.group(1)[0]
            fence_length = len(marker.group(1))
        elif is_close:
            fence_character = ""
            fence_length = 0
    return "".join(masked)


def _mask_html_comments(text: str) -> str:
    """Mask non-rendered Markdown HTML comments."""
    return re.sub(
        r"<!--.*?(?:-->|$)",
        lambda match: "".join(
            "\n" if character == "\n" else " " for character in match.group(0)
        ),
        text,
        flags=re.S,
    )


def _mcp_device_section(text: str) -> str:
    text = _mask_html_comments(text)
    inventory = _heading_section(text, "## Implemented Surface", "implemented surface")
    masked_inventory = _mask_markdown_fences(inventory)
    entries = list(re.finditer(
        r"(?m)^  (?:[-+*]|[0-9]+[.)])[ \t]+`ebus\.v1\.registry\.devices\.get`[^\n]*$",
        masked_inventory,
    ))
    if len(entries) != 1:
        raise CheckError("MCP registry devices.get entry must appear exactly once")
    start = entries[0].start()
    if inventory[start : entries[0].end()].strip() != "- `ebus.v1.registry.devices.get`":
        raise CheckError("MCP registry devices.get section missing")
    remainder = masked_inventory[entries[0].end() :]
    next_entry = re.search(
        r"(?m)^  (?:[-+*]|[0-9]+[.)])[ \t]+`",
        remainder,
    )
    end = entries[0].end() + (next_entry.start() if next_entry else len(remainder))
    return inventory[start:end]


def _validate_pins(section: str, *, surface: str) -> None:
    visible = _mask_html_comments(section)
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
    visible_text = _mask_html_comments(text)
    types_current = _current_types_section(visible_text)
    current_blocks = [block for block in _device_blocks(types_current) if not block[0]]
    if len(current_blocks) != 1:
        raise CheckError("current types must contain exactly one Device definition")
    body, masked_body = current_blocks[0][1], current_blocks[0][2]
    all_fields = [field for _, _, block in _device_blocks(visible_text) for field in _device_fields(block)]
    current_fields = _device_fields(masked_body)
    current_declarations = _device_field_tokens(masked_body)
    for name in ("discoverySource", "verificationState"):
        declarations = [entry for entry in current_declarations if entry[0] == name]
        if (
            all_fields.count(name) != 1
            or current_fields.count(name) != 1
            or declarations != [(name, "String", True)]
        ):
            raise CheckError("current Device must declare exact nullable camel-case fields")

    section = _section(visible_text)
    stale = (
        "Pending gateway #939/#940 implementation",
        "pending gateway #939/#940 implementation",
        "is not present in the current gateway schema",
        "future camel-case fields",
    )
    normalized_visible = re.sub(r"\s+", " ", visible_text)
    if any(re.sub(r"\s+", " ", fragment) in normalized_visible for fragment in stale):
        raise CheckError("stale pending provenance status remains")
    if "The current gateway schema exposes the nullable camel-case fields" not in section:
        raise CheckError("current provenance status missing")
    _validate_pins(section, surface="GraphQL")
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
    section = _mcp_device_section(text)
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
        if fragment not in section:
            raise CheckError(f"required MCP provenance rule missing: {fragment!r}")
    if re.search(r"active\s+scan\s*\(\s*→\s*`active_confirmed\s*/\s*identity_confirmed`\s*\)", text):
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
