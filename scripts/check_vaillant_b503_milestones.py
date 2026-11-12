#!/usr/bin/env python3
"""Validate the bounded B503 live-monitor milestone contract."""
from __future__ import annotations

import json
import pathlib
import re
import sys
from html.parser import HTMLParser

from markdown_it import MarkdownIt


# Rule identifiers retain a one-to-one inventory of the prior obligations.
RULES = json.loads((pathlib.Path(__file__).parent / "rules/vaillant_b503.json").read_text())


def _tuple_value(value):
    return tuple(_tuple_value(item) if isinstance(item, list) else item for item in value)


def _rule(name: str):
    rule = RULES[name]
    if not rule["reason"].strip():
        raise ValueError(f"rule {name} needs a reason")
    value = rule["value"]
    if rule["kind"] == "tuple":
        return _tuple_value(value)
    if rule["kind"] not in {"str", "list", "dict"}:
        raise ValueError(f"unknown rule kind: {rule['kind']}")
    return value


DOC = pathlib.Path("architecture/protocol-routing-vaillant-b503.md")
STATUS_SECTION_START = _rule("STATUS_SECTION_START")
STATUS_SECTION_END = _rule("STATUS_SECTION_END")
MILESTONE_HEADING = _rule("MILESTONE_HEADING")
MILESTONE_TABLE_HEADER = _rule("MILESTONE_TABLE_HEADER")
MARKDOWN_TABLE_DELIMITER_CELL = re.compile(r"^:?-{3,}:?$")
HTML_COMMENT = re.compile(r"<!--.*?(?:-->|$)", re.DOTALL)
COMMONMARK_AUTOLINK = re.compile(r"<(?:https?://|mailto:)[^<>\s]+>", re.IGNORECASE)
NON_RENDERING_CONTAINERS = frozenset(
    (
        "audio", "canvas", "defs", "desc", "head", "iframe", "metadata",
        "noscript", "object", "pre", "script", "style", "template", "title",
        "video",
    )
)
HTML_VOID_ELEMENTS = frozenset((
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
))
MARKDOWN = MarkdownIt("commonmark")
TABLE_MARKDOWN = MarkdownIt("commonmark").enable("table")
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
CSS_LINE_CONTINUATION = re.compile(r"\\(?:\r\n|[\n\r\f])")
CSS_ESCAPE = re.compile(
    r"\\([0-9a-fA-F]{1,6})(?:\r\n|[ \t\r\n\f])?|\\([^\r\n\f0-9a-fA-F])"
)
SESSION_SECTION_START = _rule("SESSION_SECTION_START")
SESSION_SECTION_END = _rule("SESSION_SECTION_END")
SESSION_TRANSITION_TABLE_START = _rule("SESSION_TRANSITION_TABLE_START")
SESSION_TRANSITION_TABLE_END = _rule("SESSION_TRANSITION_TABLE_END")
SESSION_TRANSITION_TABLE_HEADER = _rule("SESSION_TRANSITION_TABLE_HEADER")
SESSION_TRANSITION_TABLE_SEPARATOR = _rule("SESSION_TRANSITION_TABLE_SEPARATOR")
REFRESHING_PUBLIC_SECTION_START = _rule("REFRESHING_PUBLIC_SECTION_START")
REFRESHING_PUBLIC_SECTION_END = _rule("REFRESHING_PUBLIC_SECTION_END")
REFRESH_SECTION_START = _rule("REFRESH_SECTION_START")
REFRESH_SECTION_END = _rule("REFRESH_SECTION_END")
RELEASE_SECTION_START = _rule("RELEASE_SECTION_START")
RELEASE_SECTION_END = _rule("RELEASE_SECTION_END")
RECONNECT_SECTION_START = _rule("RECONNECT_SECTION_START")
RECONNECT_SECTION_END = _rule("RECONNECT_SECTION_END")
IDLE_TIMEOUT_SECTION_START = _rule("IDLE_TIMEOUT_SECTION_START")
IDLE_TIMEOUT_SECTION_END = _rule("IDLE_TIMEOUT_SECTION_END")
NORMALIZATION_SECTION_START = _rule("NORMALIZATION_SECTION_START")
NORMALIZATION_SECTION_END = _rule("NORMALIZATION_SECTION_END")
INSTALL_WRITE_SECTION_START = _rule("INSTALL_WRITE_SECTION_START")
INSTALL_WRITE_SECTION_END = _rule("INSTALL_WRITE_SECTION_END")
CAPABILITY_TRUTH_TABLE_SECTION_START = _rule("CAPABILITY_TRUTH_TABLE_SECTION_START")
CAPABILITY_TRUTH_TABLE_SECTION_END = _rule("CAPABILITY_TRUTH_TABLE_SECTION_END")
CAPABILITY_TRUTH_TABLE_HEADER = _rule("CAPABILITY_TRUTH_TABLE_HEADER")
M2B_GRAPHQL = _rule("M2B_GRAPHQL")
M3_PORTAL = _rule("M3_PORTAL")
INSTALL_WRITE_NON_EXPOSURE = _rule("INSTALL_WRITE_NON_EXPOSURE")
INSTALL_WRITE_SECTION = _rule("INSTALL_WRITE_SECTION")
COLD_BOOT_TRUTH_ROW = _rule("COLD_BOOT_TRUTH_ROW")
DISCONNECT_ACTIVE_TRUTH_ROW = _rule("DISCONNECT_ACTIVE_TRUTH_ROW")
RECONNECT_PRE_DISPATCH_TRUTH_ROW = _rule("RECONNECT_PRE_DISPATCH_TRUTH_ROW")
STALE_EPOCH_COMPLETION_TRUTH_ROW = _rule("STALE_EPOCH_COMPLETION_TRUTH_ROW")
REFRESHING_CAPABILITY_TRUTH_ROW = _rule("REFRESHING_CAPABILITY_TRUTH_ROW")
STEADY_AVAILABLE_TRUTH_ROW = _rule("STEADY_AVAILABLE_TRUTH_ROW")
RECONNECT_AVAILABLE_TRUTH_ROW = _rule("RECONNECT_AVAILABLE_TRUTH_ROW")
DISPATCH_FAILURE_TRUTH_ROW = _rule("DISPATCH_FAILURE_TRUTH_ROW")
CAPABILITY_TRUTH_ROWS = (
    COLD_BOOT_TRUTH_ROW,
    STEADY_AVAILABLE_TRUTH_ROW,
    DISCONNECT_ACTIVE_TRUTH_ROW,
    RECONNECT_PRE_DISPATCH_TRUTH_ROW,
    RECONNECT_AVAILABLE_TRUTH_ROW,
    DISPATCH_FAILURE_TRUTH_ROW,
    REFRESHING_CAPABILITY_TRUTH_ROW,
    STALE_EPOCH_COMPLETION_TRUTH_ROW,
)
CURRENT_PUBLIC_SESSION_AUTHORITY = _rule("CURRENT_PUBLIC_SESSION_AUTHORITY")
CURRENT_CAPABILITY_TABLE_AUTHORITY = _rule("CURRENT_CAPABILITY_TABLE_AUTHORITY")
FORBIDDEN_PLAN_CONFLICT_AUTHORITY = _rule("FORBIDDEN_PLAN_CONFLICT_AUTHORITY")
SESSION_STATE_CONTRACT = _rule("SESSION_STATE_CONTRACT")
DISABLED_PUBLIC_MAPPING = _rule("DISABLED_PUBLIC_MAPPING")
REFRESHING_CLEANUP_CONTRACT = _rule("REFRESHING_CLEANUP_CONTRACT")
ENABLING_CLEANUP_CONTRACT = _rule("ENABLING_CLEANUP_CONTRACT")
REFRESHING_UNKNOWN_STRIP_CONTRACT = _rule("REFRESHING_UNKNOWN_STRIP_CONTRACT")
ACTIVE_UNKNOWN_OWNER_CONTRACT = _rule("ACTIVE_UNKNOWN_OWNER_CONTRACT")
REFRESH_SUCCESS_CONTINUATION = _rule("REFRESH_SUCCESS_CONTINUATION")
REFRESH_FAILURE_CAPABILITY_PRECEDENCE = _rule("REFRESH_FAILURE_CAPABILITY_PRECEDENCE")
REFRESH_OWNER_REBINDING = _rule("REFRESH_OWNER_REBINDING")
NO_AUTO_RESUME_RECONSTRUCTION = _rule("NO_AUTO_RESUME_RECONSTRUCTION")
REFRESHING_DISCONNECT_FENCE = _rule("REFRESHING_DISCONNECT_FENCE")
DISCONNECT_CLEANUP_OBLIGATION = _rule("DISCONNECT_CLEANUP_OBLIGATION")
OWNER_CONDITIONAL_MUTEX_SCOPE = _rule("OWNER_CONDITIONAL_MUTEX_SCOPE")
DISCONNECT_CLEANUP_MUTEX_INDEPENDENCE = _rule("DISCONNECT_CLEANUP_MUTEX_INDEPENDENCE")
CONFIRMED_CLEANUP_DEFINITION = _rule("CONFIRMED_CLEANUP_DEFINITION")
UNCONFIRMED_CLEANUP_OBLIGATION = _rule("UNCONFIRMED_CLEANUP_OBLIGATION")
GATEWAY_CLEANUP_ATTEMPT_ID = _rule("GATEWAY_CLEANUP_ATTEMPT_ID")
CONFIRMED_CLEANUP_DIAGRAM = _rule("CONFIRMED_CLEANUP_DIAGRAM")
EXPLICIT_DISABLE_PRE_EMISSION_DISCONNECT_TRANSITION = _rule("EXPLICIT_DISABLE_PRE_EMISSION_DISCONNECT_TRANSITION")
EXPLICIT_DISABLE_CONFIRMED_TRANSITION = _rule("EXPLICIT_DISABLE_CONFIRMED_TRANSITION")
EXPLICIT_DISABLE_UNCONFIRMED_TRANSITION = EXPLICIT_DISABLE_CONFIRMED_TRANSITION
RESTART_TRANSITION = _rule("RESTART_TRANSITION")
RESTART_RELEASE_CONTRACT = _rule("RESTART_RELEASE_CONTRACT")
RESTART_CLEANUP_FENCE = _rule("RESTART_CLEANUP_FENCE")
IDLE_TIMEOUT_ACK_CONTRACT = _rule("IDLE_TIMEOUT_ACK_CONTRACT")
IDLE_TIMEOUT_TRIGGER_CONTRACT = _rule("IDLE_TIMEOUT_TRIGGER_CONTRACT")
NORMALIZED_REFRESH_DISABLE_CONTRACT = _rule("NORMALIZED_REFRESH_DISABLE_CONTRACT")
REFRESH_FAILURE_DIAGRAM = _rule("REFRESH_FAILURE_DIAGRAM")
REFRESH_READ_DIAGRAM = _rule("REFRESH_READ_DIAGRAM")
REFRESH_DISABLE_DIAGRAM = _rule("REFRESH_DISABLE_DIAGRAM")
UNCONFIRMED_CLEANUP_DIAGRAM = _rule("UNCONFIRMED_CLEANUP_DIAGRAM")
REFRESH_READ_TRANSITION = _rule("REFRESH_READ_TRANSITION")
REFRESH_DISABLE_PRE_EMISSION_DISCONNECT_TRANSITION = _rule("REFRESH_DISABLE_PRE_EMISSION_DISCONNECT_TRANSITION")
REFRESH_DISABLE_TRANSITION = _rule("REFRESH_DISABLE_TRANSITION")
REFRESH_DISABLE_UNCONFIRMED_TRANSITION = REFRESH_DISABLE_TRANSITION
UNCONFIRMED_CLEANUP_TRANSITION = _rule("UNCONFIRMED_CLEANUP_TRANSITION")
ADMIN_DISABLED_TRANSITION = _rule("ADMIN_DISABLED_TRANSITION")
CONFIRMED_CLEANUP_TRANSITION = _rule("CONFIRMED_CLEANUP_TRANSITION")
REFRESH_FAILURE_TRANSITION = _rule("REFRESH_FAILURE_TRANSITION")
HELD_OWNER_DISABLED_RELEASE = _rule("HELD_OWNER_DISABLED_RELEASE")
ENABLING_EPOCH_PRE_DIAGRAM = _rule("ENABLING_EPOCH_PRE_DIAGRAM")
ENABLING_EPOCH_POST_DIAGRAM = _rule("ENABLING_EPOCH_POST_DIAGRAM")
ENABLING_DISCONNECT_PRE_DIAGRAM = _rule("ENABLING_DISCONNECT_PRE_DIAGRAM")
ENABLING_DISCONNECT_POST_DIAGRAM = _rule("ENABLING_DISCONNECT_POST_DIAGRAM")
ENABLING_EPOCH_PRE_OPERATION = _rule("ENABLING_EPOCH_PRE_OPERATION")
ENABLING_EPOCH_POST_OPERATION = _rule("ENABLING_EPOCH_POST_OPERATION")
ENABLING_EPOCH_PRE_TRANSITION = _rule("ENABLING_EPOCH_PRE_TRANSITION")
ENABLING_EPOCH_POST_TRANSITION = _rule("ENABLING_EPOCH_POST_TRANSITION")
ENABLING_CANCEL_DIAGRAM = _rule("ENABLING_CANCEL_DIAGRAM")
ENABLING_FAILURE_DIAGRAM = _rule("ENABLING_FAILURE_DIAGRAM")
CODE_REQUIRED_FRAGMENTS = frozenset((
    CONFIRMED_CLEANUP_DIAGRAM,
    UNCONFIRMED_CLEANUP_DIAGRAM,
    REFRESH_FAILURE_DIAGRAM,
    REFRESH_READ_DIAGRAM,
    REFRESH_DISABLE_DIAGRAM,
    ENABLING_EPOCH_PRE_DIAGRAM,
    ENABLING_EPOCH_POST_DIAGRAM,
    ENABLING_DISCONNECT_PRE_DIAGRAM,
    ENABLING_DISCONNECT_POST_DIAGRAM,
    ENABLING_CANCEL_DIAGRAM,
    ENABLING_FAILURE_DIAGRAM,
))
ENABLING_CANCEL_TRANSITION = _rule("ENABLING_CANCEL_TRANSITION")
ENABLE_ADMISSION_OPERATION = _rule("ENABLE_ADMISSION_OPERATION")
IDLE_ENABLE_TRANSITION = _rule("IDLE_ENABLE_TRANSITION")
IDLE_ENABLE_REJECT_TRANSITION = _rule("IDLE_ENABLE_REJECT_TRANSITION")
DISABLED_ENABLE_REJECT_TRANSITION = _rule("DISABLED_ENABLE_REJECT_TRANSITION")
ENABLING_ACK_TRANSITION = _rule("ENABLING_ACK_TRANSITION")
ENABLING_AMBIGUOUS_FAILURE_TRANSITION = _rule("ENABLING_AMBIGUOUS_FAILURE_TRANSITION")
ENABLING_DISCONNECT_PRE_TRANSITION = _rule("ENABLING_DISCONNECT_PRE_TRANSITION")
ACTIVE_READ_TRANSITION = _rule("ACTIVE_READ_TRANSITION")
ACTIVE_READ_FAILURE_TRANSITION = _rule("ACTIVE_READ_FAILURE_TRANSITION")
ACTIVE_IDLE_TRANSITION = _rule("ACTIVE_IDLE_TRANSITION")
ACTIVE_REFRESH_TRANSITION = _rule("ACTIVE_REFRESH_TRANSITION")
IDLE_DISCONNECT_TRANSITION = _rule("IDLE_DISCONNECT_TRANSITION")
DISCONNECT_TRANSITION = _rule("DISCONNECT_TRANSITION")
DISABLED_DISCONNECT_TRANSITION = _rule("DISABLED_DISCONNECT_TRANSITION")
CLEANUP_SCOPED_TRANSPORT_DOWN_FORBIDDEN = _rule("CLEANUP_SCOPED_TRANSPORT_DOWN_FORBIDDEN")
ENABLING_NAK_TRANSITION = ENABLING_AMBIGUOUS_FAILURE_TRANSITION
SESSION_TRANSITION_ROWS = (
    IDLE_ENABLE_TRANSITION,
    IDLE_ENABLE_REJECT_TRANSITION,
    DISABLED_ENABLE_REJECT_TRANSITION,
    ENABLING_ACK_TRANSITION,
    ENABLING_CANCEL_TRANSITION,
    ENABLING_AMBIGUOUS_FAILURE_TRANSITION,
    ENABLING_DISCONNECT_PRE_TRANSITION,
    ENABLING_EPOCH_PRE_TRANSITION,
    ENABLING_EPOCH_POST_TRANSITION,
    ACTIVE_READ_TRANSITION,
    ACTIVE_READ_FAILURE_TRANSITION,
    EXPLICIT_DISABLE_PRE_EMISSION_DISCONNECT_TRANSITION,
    EXPLICIT_DISABLE_CONFIRMED_TRANSITION,
    ACTIVE_IDLE_TRANSITION,
    ACTIVE_REFRESH_TRANSITION,
    REFRESH_READ_TRANSITION,
    REFRESH_DISABLE_PRE_EMISSION_DISCONNECT_TRANSITION,
    REFRESH_DISABLE_TRANSITION,
    REFRESH_FAILURE_TRANSITION,
    UNCONFIRMED_CLEANUP_TRANSITION,
    ADMIN_DISABLED_TRANSITION,
    IDLE_DISCONNECT_TRANSITION,
    DISCONNECT_TRANSITION,
    DISABLED_DISCONNECT_TRANSITION,
    RESTART_TRANSITION,
)
ENABLING_DIRECT_IDLE_LOCK = _rule("ENABLING_DIRECT_IDLE_LOCK")
FORBIDDEN_REFRESH_FAILURE_CONTRADICTIONS = _rule("FORBIDDEN_REFRESH_FAILURE_CONTRADICTIONS")
FORBIDDEN_ENABLING_EPOCH_CONTRADICTIONS = _rule("FORBIDDEN_ENABLING_EPOCH_CONTRADICTIONS")
RESTART_AUTOMATIC_WRITE_CONTRADICTION_PATTERNS = (
    re.compile(
        _rule("RESTART_AUTOMATIC_WRITE_CONTRADICTION_PATTERNS_fragment_5"),
        re.IGNORECASE,
    ),
    re.compile(
        _rule("RESTART_AUTOMATIC_WRITE_CONTRADICTION_PATTERNS_fragment_8"),
        re.IGNORECASE,
    ),
)
SETTLEMENT_CONTRADICTION_PATTERNS = (
    re.compile(
        _rule("SETTLEMENT_CONTRADICTION_PATTERNS_fragment_5"),
        re.IGNORECASE,
    ),
    re.compile(
        _rule("SETTLEMENT_CONTRADICTION_PATTERNS_fragment_8"),
        re.IGNORECASE,
    ),
)
FORBIDDEN_SESSION_STATE_CLAUSES = _rule("FORBIDDEN_SESSION_STATE_CLAUSES")
SESSION_STATE_CONTRADICTION_PATTERNS = (
    re.compile(
        _rule("SESSION_STATE_CONTRADICTION_PATTERNS_fragment_5"),
        re.IGNORECASE,
    ),
    re.compile(
        r"`Disabled`\s+(?:(?:may|can|must|shall)\s+be\s+|is\s+)?"
        r"(?:reported|rendered|published|returned)\s+with\s+`owned:true`",
        re.IGNORECASE,
    ),
)
FORBIDDEN_ALL_READ_ONLY_MILESTONES = _rule("FORBIDDEN_ALL_READ_ONLY_MILESTONES")


class CheckError(ValueError):
    """The canonical B503 milestone text contradicts the v1 session boundary."""


class _VisibleContractSourceParser(HTMLParser):
    """Retain contract source that is visible, excluding inert HTML content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []
        self._inert_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.casefold()
        hidden = _html_element_is_nonrendering(attrs) or (
            normalized in {"details", "dialog"}
            and not any(name.casefold() == "open" for name, _ in attrs)
        )
        if self._inert_stack or normalized in NON_RENDERING_CONTAINERS or hidden:
            if normalized not in HTML_VOID_ELEMENTS:
                self._inert_stack.append(normalized)
            return

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # Opening tags and attribute values are metadata, not rendered prose.
        return

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.casefold()
        if self._inert_stack:
            for index in range(len(self._inert_stack) - 1, -1, -1):
                if self._inert_stack[index] == normalized:
                    del self._inert_stack[index:]
                    return
            return

    def handle_data(self, data: str) -> None:
        if not self._inert_stack:
            self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if not self._inert_stack:
            self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if not self._inert_stack:
            self.parts.append(f"&#{name};")


def _visible_contract_source(text: str) -> str:
    parser = _VisibleContractSourceParser()
    parser.feed(COMMONMARK_AUTOLINK.sub("", text))
    parser.close()
    return "".join(parser.parts)


def _decode_css_escapes(value: str) -> str:
    value = CSS_LINE_CONTINUATION.sub("", value)

    def replace(match: re.Match[str]) -> str:
        if match.group(1) is None:
            return match.group(2)
        codepoint = int(match.group(1), 16)
        if codepoint == 0 or 0xD800 <= codepoint <= 0xDFFF or codepoint > 0x10FFFF:
            return "\N{REPLACEMENT CHARACTER}"
        return chr(codepoint)

    return CSS_ESCAPE.sub(replace, value)


def _html_element_is_nonrendering(attrs: list[tuple[str, str | None]]) -> bool:
    for name, value in attrs:
        if name.casefold() == "hidden":
            return True
        if name.casefold() != "style" or value is None:
            continue
        declarations: dict[str, tuple[str, bool]] = {}
        for declaration in CSS_COMMENT.sub("", value).split(";"):
            property_name, separator, property_value = declaration.partition(":")
            if separator:
                property_name = _decode_css_escapes(property_name)
                property_value = _decode_css_escapes(property_value)
                important = re.search(
                    r"\s*!important\s*$", property_value, re.IGNORECASE
                ) is not None
                normalized_value = re.sub(
                    r"\s*!important\s*$", "", property_value.casefold()
                ).strip()
                normalized_name = property_name.strip().casefold()
                prior = declarations.get(normalized_name)
                if prior is None or important or not prior[1]:
                    declarations[normalized_name] = (normalized_value, important)
        if declarations.get("display", (None, False))[0] == "none" or declarations.get(
            "visibility", (None, False)
        )[0] in {"hidden", "collapse"}:
            return True
    return False


def _visible_prose_source(text: str) -> str:
    """Remove CommonMark fenced and indented code while preserving line boundaries."""
    lines = text.splitlines(keepends=True)
    for token in MARKDOWN.parse(text):
        if token.type not in {"fence", "code_block"} or token.map is None:
            continue
        for index in range(token.map[0], min(token.map[1], len(lines))):
            lines[index] = "\n" if lines[index].endswith("\n") else ""
    return "".join(lines)


def _rendered_contract_source(text: str) -> str:
    """Reconstruct rendered CommonMark text without link/image metadata or code."""
    parts: list[str] = []
    for token in MARKDOWN.parse(text):
        if token.type == "heading_open":
            parts.append("#" * int(token.tag[1:]) + " ")
        elif token.type == "list_item_open":
            parts.append("- ")
        elif token.type == "html_block":
            parts.extend((token.content, "\n"))
        elif token.type == "inline":
            for child in token.children or ():
                if child.type == "text":
                    parts.append(child.content)
                elif child.type == "code_inline":
                    parts.extend(("`", child.content, "`"))
                elif child.type in {"softbreak", "hardbreak"}:
                    parts.append("\n")
                elif child.type == "html_inline":
                    parts.append(child.content)
            parts.append("\n")
    return _visible_contract_source("".join(parts))


def _literal_anchor_values(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, tuple):
        for item in value:
            yield from _literal_anchor_values(item)


def _normalized_rendered(text: str) -> str:
    return " ".join(_rendered_contract_source(text).split())


def _require_declared_literal_anchors_visible(prose_text: str, rendered_text: str) -> None:
    """Require the checker's current literal anchors in reader-visible prose.

    This is bounded to literal contract fragments already declared by this
    checker. It does not attempt to prove arbitrary English semantics.
    """
    normalized_document = " ".join(rendered_text.split())
    for name, value in globals().items():
        if not name.isupper():
            continue
        for anchor in _literal_anchor_values(value):
            if len(anchor) < 32 or anchor not in prose_text:
                continue
            normalized_anchor = _normalized_rendered(anchor)
            if normalized_anchor and normalized_anchor not in normalized_document:
                raise CheckError(
                    f"declared contract anchor is not reader-visible: {name}"
                )


def _parse_table_row(line: str) -> tuple[str, ...] | None:
    if not line.startswith("|") or not line.endswith("|"):
        return None
    return tuple(cell.strip() for cell in line.strip("|").split("|"))


def _is_markdown_table_delimiter(
    row: tuple[str, ...] | None, column_count: int = len(MILESTONE_TABLE_HEADER)
) -> bool:
    return row is not None and len(row) == column_count and all(
        MARKDOWN_TABLE_DELIMITER_CELL.fullmatch(cell) is not None for cell in row
    )


def _section(text: str, start_marker: str, end_marker: str) -> str:
    try:
        start = text.index(start_marker)
        end = text.index(end_marker, start)
    except ValueError as exc:
        raise CheckError(
            f"missing canonical B503 section boundary: {start_marker!r}"
        ) from exc
    return text[start:end]


def _require_genuine_markdown_table(text: str, header: str, label: str) -> None:
    """Require an exact header to begin one table in original CommonMark context."""
    header_lines = [
        index for index, line in enumerate(text.splitlines()) if line == header
    ]
    table_starts = {
        token.map[0]
        for token in TABLE_MARKDOWN.parse(text)
        if token.type == "table_open" and token.map is not None
    }
    if len(header_lines) != 1 or header_lines[0] not in table_starts:
        raise CheckError(f"{label} must be one rendered Markdown table")


def _milestone_table(text: str) -> tuple[tuple[str, ...], ...]:
    """Return only the §14 companion milestone table rows, excluding prose."""
    lines = text.splitlines()
    try:
        heading_index = lines.index(MILESTONE_HEADING)
    except ValueError as exc:
        raise CheckError(f"missing B503 milestone heading: {MILESTONE_HEADING!r}") from exc

    header_index = heading_index + 2
    if header_index >= len(lines) or _parse_table_row(lines[header_index]) != MILESTONE_TABLE_HEADER:
        raise CheckError("missing §14 B503 milestone table header")
    separator_index = header_index + 1
    if separator_index >= len(lines) or not _is_markdown_table_delimiter(
        _parse_table_row(lines[separator_index])
    ):
        raise CheckError("missing §14 B503 milestone table separator")

    rows: list[tuple[str, ...]] = []
    for line in lines[separator_index + 1 :]:
        row = _parse_table_row(line)
        if row is None:
            break
        if len(row) != len(MILESTONE_TABLE_HEADER):
            raise CheckError(f"invalid §14 B503 milestone table row: {line!r}")
        rows.append(row)
    if not rows:
        raise CheckError("missing §14 B503 milestone table rows")
    return tuple(rows)


def _capability_truth_table_rows(text: str) -> tuple[tuple[str, ...], ...]:
    section = _section(
        text, CAPABILITY_TRUTH_TABLE_SECTION_START, CAPABILITY_TRUTH_TABLE_SECTION_END
    )
    lines = section.splitlines()
    try:
        header_index = next(
            index
            for index, line in enumerate(lines)
            if _parse_table_row(line) == CAPABILITY_TRUTH_TABLE_HEADER
        )
    except StopIteration as exc:
        raise CheckError("missing §12.5 capability truth-table header") from exc
    separator_index = header_index + 1
    if separator_index >= len(lines) or not _is_markdown_table_delimiter(
        _parse_table_row(lines[separator_index]), len(CAPABILITY_TRUTH_TABLE_HEADER)
    ):
        raise CheckError("missing §12.5 capability truth-table separator")

    rows: list[tuple[str, ...]] = []
    for line in lines[separator_index + 1 :]:
        row = _parse_table_row(line)
        if row is None:
            break
        if len(row) != len(CAPABILITY_TRUTH_TABLE_HEADER):
            raise CheckError(f"invalid §12.5 capability truth-table row: {line!r}")
        rows.append(row)
    if not rows:
        raise CheckError("missing §12.5 capability truth-table rows")
    return tuple(rows)


def _require_exact_row(rows: tuple[tuple[str, ...], ...], expected: tuple[str, ...]) -> None:
    matching_id_rows = [row for row in rows if row[0] == expected[0]]
    if matching_id_rows != [expected]:
        raise CheckError(f"missing exact §14 B503 milestone row: {expected!r}")


def validate_text(text: str) -> None:
    # Exact milestone fragments must be present in rendered documentation.
    # Raw text hidden in a CommonMark HTML comment cannot satisfy the gate.
    original_text = text
    _require_genuine_markdown_table(
        original_text, SESSION_TRANSITION_TABLE_HEADER, "§6.3 transition table"
    )
    _require_genuine_markdown_table(
        original_text,
        "| " + " | ".join(CAPABILITY_TRUTH_TABLE_HEADER) + " |",
        "§12.5 capability truth table",
    )
    _require_genuine_markdown_table(
        original_text,
        "| " + " | ".join(MILESTONE_TABLE_HEADER) + " |",
        "§14 milestone table",
    )
    text = _visible_contract_source(text)
    prose_text = _visible_prose_source(text)
    _require_declared_literal_anchors_visible(
        prose_text, _rendered_contract_source(text)
    )
    status_section = _section(prose_text, STATUS_SECTION_START, STATUS_SECTION_END)
    if CURRENT_PUBLIC_SESSION_AUTHORITY not in status_section:
        raise CheckError("missing current public session authority in §1")

    session_section = _section(text, SESSION_SECTION_START, SESSION_SECTION_END)
    session_prose_section = _section(
        prose_text, SESSION_SECTION_START, SESSION_SECTION_END
    )
    session_contract_scope = _section(
        text, SESSION_SECTION_START, NORMALIZATION_SECTION_END
    )
    if SESSION_STATE_CONTRACT not in session_prose_section:
        raise CheckError("missing five-state B503 session contract in §6.1")
    if DISABLED_PUBLIC_MAPPING not in session_prose_section:
        raise CheckError("missing stable public Disabled mapping in §6")
    transition_section = _section(
        session_prose_section,
        SESSION_TRANSITION_TABLE_START,
        SESSION_TRANSITION_TABLE_END,
    )
    transition_lines = tuple(
        line for line in transition_section.splitlines() if line.startswith("|")
    )
    expected_transition_lines = (
        SESSION_TRANSITION_TABLE_HEADER,
        SESSION_TRANSITION_TABLE_SEPARATOR,
        *SESSION_TRANSITION_ROWS,
    )
    if transition_lines != expected_transition_lines:
        raise CheckError("§6.3 must contain the exact ordered finite B503 transition table")
    for fragment in (
        CONFIRMED_CLEANUP_DEFINITION,
        CONFIRMED_CLEANUP_DIAGRAM,
        UNCONFIRMED_CLEANUP_DIAGRAM,
        REFRESH_FAILURE_DIAGRAM,
        REFRESH_READ_DIAGRAM,
        REFRESH_DISABLE_DIAGRAM,
        REFRESH_READ_TRANSITION,
        REFRESH_DISABLE_TRANSITION,
        REFRESH_DISABLE_UNCONFIRMED_TRANSITION,
        UNCONFIRMED_CLEANUP_TRANSITION,
        CONFIRMED_CLEANUP_TRANSITION,
        EXPLICIT_DISABLE_CONFIRMED_TRANSITION,
        EXPLICIT_DISABLE_UNCONFIRMED_TRANSITION,
        REFRESH_FAILURE_TRANSITION,
        HELD_OWNER_DISABLED_RELEASE,
        ENABLE_ADMISSION_OPERATION,
        ENABLING_CANCEL_DIAGRAM,
        ENABLING_FAILURE_DIAGRAM,
        ENABLING_DISCONNECT_PRE_DIAGRAM,
        ENABLING_DISCONNECT_POST_DIAGRAM,
        ENABLING_ACK_TRANSITION,
        ENABLING_CANCEL_TRANSITION,
        ENABLING_AMBIGUOUS_FAILURE_TRANSITION,
        ENABLING_DISCONNECT_PRE_TRANSITION,
        ENABLING_NAK_TRANSITION,
        ENABLING_DIRECT_IDLE_LOCK,
        DISCONNECT_TRANSITION,
        RESTART_TRANSITION,
    ):
        required_scope = (
            session_section
            if fragment in CODE_REQUIRED_FRAGMENTS
            else session_prose_section
        )
        if fragment not in required_scope:
            raise CheckError(
                f"missing coherent B503 Refreshing failure contract in §6.1: {fragment!r}"
            )
    for fragment in FORBIDDEN_REFRESH_FAILURE_CONTRADICTIONS:
        if fragment in session_section:
            raise CheckError(
                f"forbidden B503 Refreshing failure contradiction in §6.1: {fragment!r}"
            )
    for fragment in FORBIDDEN_SESSION_STATE_CLAUSES:
        if fragment in session_contract_scope:
            raise CheckError(
                f"forbidden §§6-8 B503 session-state contradiction: {fragment!r}"
            )
    for pattern in SESSION_STATE_CONTRADICTION_PATTERNS:
        match = pattern.search(session_contract_scope)
        if match is not None:
            raise CheckError(
                "forbidden declarative §§6-8 B503 session-state contradiction: "
                f"{match.group(0)!r}"
            )
    for pattern in RESTART_AUTOMATIC_WRITE_CONTRADICTION_PATTERNS:
        match = pattern.search(session_contract_scope)
        if match is not None:
            raise CheckError(
                "forbidden automatic B503 restart write contradiction in §§6-8: "
                f"{match.group(0)!r}"
            )
    for pattern in SETTLEMENT_CONTRADICTION_PATTERNS:
        match = pattern.search(session_contract_scope)
        if match is not None:
            raise CheckError(
                "forbidden ACK/NAK session-settlement contradiction in §§6-8: "
                f"{match.group(0)!r}"
            )
    for fragment in (
        ENABLING_EPOCH_PRE_DIAGRAM,
        ENABLING_EPOCH_POST_DIAGRAM,
        ENABLING_EPOCH_PRE_OPERATION,
        ENABLING_EPOCH_POST_OPERATION,
        ENABLING_EPOCH_PRE_TRANSITION,
        ENABLING_EPOCH_POST_TRANSITION,
    ):
        required_scope = (
            session_section
            if fragment in CODE_REQUIRED_FRAGMENTS
            else session_prose_section
        )
        if fragment not in required_scope:
            raise CheckError(
                f"missing coherent ENABLING epoch-advance contract in §6: {fragment!r}"
            )
    for fragment in FORBIDDEN_ENABLING_EPOCH_CONTRADICTIONS:
        if fragment in session_section:
            raise CheckError(
                f"forbidden ENABLING epoch-advance contradiction in §6: {fragment!r}"
            )
    if REFRESH_OWNER_REBINDING not in session_prose_section:
        raise CheckError("missing atomic owner-key epoch rebinding contract in §6.2")

    refreshing_public_section = _section(
        prose_text, REFRESHING_PUBLIC_SECTION_START, REFRESHING_PUBLIC_SECTION_END
    )
    for fragment in (
        ENABLING_CLEANUP_CONTRACT,
        REFRESHING_CLEANUP_CONTRACT,
        REFRESHING_UNKNOWN_STRIP_CONTRACT,
        ACTIVE_UNKNOWN_OWNER_CONTRACT,
    ):
        if fragment not in refreshing_public_section:
            raise CheckError(
                f"missing public Refreshing consumer contract in §7.1.1: {fragment!r}"
            )

    refresh_section = _section(prose_text, REFRESH_SECTION_START, REFRESH_SECTION_END)
    if REFRESH_SUCCESS_CONTINUATION not in refresh_section:
        raise CheckError("missing authenticated Refreshing continuation contract in §7.3")
    if REFRESH_FAILURE_CAPABILITY_PRECEDENCE not in refresh_section:
        raise CheckError("missing cleanup-aware refresh failure capability precedence")
    release_section = _section(prose_text, RELEASE_SECTION_START, RELEASE_SECTION_END)
    for fragment in (
        OWNER_CONDITIONAL_MUTEX_SCOPE,
        UNCONFIRMED_CLEANUP_OBLIGATION,
        GATEWAY_CLEANUP_ATTEMPT_ID,
        DISCONNECT_CLEANUP_OBLIGATION,
        DISCONNECT_CLEANUP_MUTEX_INDEPENDENCE,
        RESTART_RELEASE_CONTRACT,
    ):
        if fragment not in release_section:
            raise CheckError("missing process-local disconnect cleanup obligation in §7.4")
    reconnect_section = _section(prose_text, RECONNECT_SECTION_START, RECONNECT_SECTION_END)
    if NO_AUTO_RESUME_RECONSTRUCTION not in reconnect_section:
        raise CheckError("missing no-reconstruction boundary in §7.5")
    if REFRESHING_DISCONNECT_FENCE not in reconnect_section:
        raise CheckError("missing Refreshing disconnect fence in §7.5")
    if RESTART_CLEANUP_FENCE not in reconnect_section:
        raise CheckError("missing bounded per-target restart cleanup fence in §7.5")
    idle_timeout_section = _section(
        prose_text, IDLE_TIMEOUT_SECTION_START, IDLE_TIMEOUT_SECTION_END
    )
    for fragment in (IDLE_TIMEOUT_TRIGGER_CONTRACT, IDLE_TIMEOUT_ACK_CONTRACT):
        if fragment not in idle_timeout_section:
            raise CheckError("missing successful-read idle-timeout contract in §7.6")
    normalization_section = _section(
        prose_text, NORMALIZATION_SECTION_START, NORMALIZATION_SECTION_END
    )
    if NORMALIZED_REFRESH_DISABLE_CONTRACT not in normalization_section:
        raise CheckError("missing fail-closed refreshed-DISABLE normalization in §8")

    rows = _milestone_table(prose_text)
    for expected in (M2B_GRAPHQL, M3_PORTAL):
        _require_exact_row(rows, expected)
    for fragment in FORBIDDEN_ALL_READ_ONLY_MILESTONES:
        if fragment in rows:
            raise CheckError(f"forbidden all-read-only B503 milestone: {fragment!r}")
    install_write_section = _section(
        prose_text, INSTALL_WRITE_SECTION_START, INSTALL_WRITE_SECTION_END
    )
    if install_write_section != INSTALL_WRITE_SECTION:
        raise CheckError(
            "§9 B503 installation-write classification, prohibition, enforcement, "
            "and future-plan boundary must remain exact"
        )

    truth_rows = _capability_truth_table_rows(prose_text)
    if truth_rows != CAPABILITY_TRUTH_ROWS:
        raise CheckError(
            "§12.5 capability truth table must contain the exact ordered eight-row set; "
            f"got {truth_rows!r}"
        )
    truth_prose = _section(
        prose_text,
        CAPABILITY_TRUTH_TABLE_SECTION_START,
        CAPABILITY_TRUTH_TABLE_SECTION_END,
    )
    if CURRENT_CAPABILITY_TABLE_AUTHORITY not in truth_prose:
        raise CheckError("missing current public authority for all eight §12.5 rows")
    for fragment in FORBIDDEN_PLAN_CONFLICT_AUTHORITY:
        if fragment in text:
            raise CheckError(f"forbidden archived-plan conflict authority: {fragment!r}")
    if CLEANUP_SCOPED_TRANSPORT_DOWN_FORBIDDEN not in prose_text:
        raise CheckError("missing cleanup-scoped TRANSPORT_DOWN/UNKNOWN precedence")


def main() -> int:
    try:
        validate_text(DOC.read_text(encoding="utf-8"))
    except (OSError, CheckError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print("Vaillant B503 milestone contract gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
