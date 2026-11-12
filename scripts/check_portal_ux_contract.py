#!/usr/bin/env python3
"""Validate the public INT-10 Portal and Vaillant B503 target contract."""
from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import json
import pathlib
import re
import sys
from urllib.parse import unquote

from markdown_it import MarkdownIt


# Rule identifiers retain a one-to-one inventory of the prior obligations.
RULES = json.loads((pathlib.Path(__file__).parent / "rules/portal_ux.json").read_text())


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


DOC = pathlib.Path("api/portal.md")
TARGET_START = _rule("TARGET_START")
TARGET_END = _rule("TARGET_END")

AVAILABILITY_ROWS = _rule("AVAILABILITY_ROWS")
AVAILABILITY_TABLE_HEADER = _rule("AVAILABILITY_TABLE_HEADER")
AVAILABILITY_TABLE_SEPARATOR = _rule("AVAILABILITY_TABLE_SEPARATOR")
PROJECTION_CARD_ADMISSION = _rule("PROJECTION_CARD_ADMISSION")
SELECTED_TARGET_TYPED_HISTORY = _rule("SELECTED_TARGET_TYPED_HISTORY")
B503_KEYBOARD_ACCESSIBILITY = _rule("B503_KEYBOARD_ACCESSIBILITY")
B503_CAPABILITY_RECONNECT = _rule("B503_CAPABILITY_RECONNECT")
B503_FIELD_OPERATION_ERRORS = _rule("B503_FIELD_OPERATION_ERRORS")
B503_FRONTEND_EPOCH_ROLLOVER = _rule("B503_FRONTEND_EPOCH_ROLLOVER")
B503_SESSION_STATE_CONTRACT = _rule("B503_SESSION_STATE_CONTRACT")
B503_DISABLED_PUBLIC_MAPPING = _rule("B503_DISABLED_PUBLIC_MAPPING")
B503_REFRESHING_CLEANUP = _rule("B503_REFRESHING_CLEANUP")
B503_ENABLING_CLEANUP = _rule("B503_ENABLING_CLEANUP")
B503_TARGET_CLEANUP_SCOPE = _rule("B503_TARGET_CLEANUP_SCOPE")
B503_REFRESHING_UNKNOWN_STRIP = _rule("B503_REFRESHING_UNKNOWN_STRIP")
B503_ACTIVE_UNKNOWN_OWNER = _rule("B503_ACTIVE_UNKNOWN_OWNER")
B503_REFRESH_CONTINUATION = _rule("B503_REFRESH_CONTINUATION")
FORBIDDEN_B503_SESSION_STATE_CLAUSES = _rule("FORBIDDEN_B503_SESSION_STATE_CLAUSES")
B503_SESSION_STATE_CONTRADICTION_PATTERNS = (
    re.compile(
        _rule("B503_SESSION_STATE_CONTRADICTION_PATTERNS_fragment_5"),
        re.IGNORECASE,
    ),
    re.compile(
        r"`Disabled`\s+(?:(?:may|can|must|shall)\s+be\s+|is\s+)?"
        r"(?:reported|rendered|published|returned)\s+with\s+`owned:true`",
        re.IGNORECASE,
    ),
)
B503_MAIN_ROUTE_OPERATIONS = _rule("B503_MAIN_ROUTE_OPERATIONS")
B503_NO_EXPIRED_STATE = _rule("B503_NO_EXPIRED_STATE")

REQUIRED = (
    TARGET_START,
    "Gateway #552 is open;",
    "`helianthus.gateway.portal-catalog/v1`",
    _rule("REQUIRED_fragment_4"),
    "`POST /graphql/portal/v1`",
    "`PortalCatalogV1`",
    "`PortalActionInvokeV1`",
    "No B503 operation is admitted on this route.",
    _rule("REQUIRED_fragment_9"),
    "does not use a central vendor switch or an arbitrary-English parser",
    "`Thermal/HVAC`, `PV`, `Storage/BMS`, `EVSE`, and\n`Infrastructure`",
    "must not require a vendor switch, a product branch, or compatibility logic in\ncentral bootstrap or rendering code.",
    "`(driver_id, manifest_id, manifest_version)`",
    "`catalog_revision`, `catalog_digest`,\nand `evaluation_instant`",
    "lifecycle, freshness, projection-loss, quality, and provenance",
    "Accepted source records and accepted semantic records remain distinct from the\nbrowser presentation state.",
    "Discovery\npermission controls visibility",
    _rule("REQUIRED_fragment_18"),
    B503_MAIN_ROUTE_OPERATIONS,
    "`vaillantCapabilities(targetAddress:)`",
    "`vaillantErrors(targetAddress:)`",
    "`vaillantServiceCurrent(targetAddress:)`",
    "`vaillantErrorHistory(targetAddress:index:)`",
    "`vaillantErrorsHistory(targetAddress:limit:)`",
    "`vaillantServiceHistory(targetAddress:index:)`",
    "`vaillantLiveMonitor(action:issuerToken:targetAddress:)`",
    "`vaillantLiveMonitorSession(targetAddress:)`",
    "`POST /graphql` endpoint. That endpoint is protected by the stable eBUS MCP\ngraduation/parity contract.",
    "exclusive operation-to-route\nsplit, not a fallback or compatibility shim.",
    "does not expand the\naccepted #974 catalog/action endpoint.",
    _rule("REQUIRED_fragment_31"),
    "`M8-TGT-01`,\n`M8-TGT-02`, `M8-TGT-03`, and `M8-TGT-04`",
    _rule("REQUIRED_fragment_33"),
    "Any late enable completion after a switch follows the same prior-target cleanup\nand cannot mutate the new target.",
    B503_NO_EXPIRED_STATE,
    'data-testid="b503-state-available"',
    'data-testid="b503-state-not-supported"',
    'data-testid="b503-state-transport-down"',
    'data-testid="b503-state-session-busy"',
    'data-testid="b503-state-unknown"',
    'data-testid="b503-session-strip"',
    'data-testid="b503-session-state-label"',
    B503_SESSION_STATE_CONTRACT,
    "base `SESSION_BUSY` presentation is neutral.",
    B503_TARGET_CLEANUP_SCOPE,
    "An `ACTIVE` prior target receives an immediate target-specific\ndisable using its locally held issuer token.",
    B503_ENABLING_CLEANUP,
    B503_REFRESHING_CLEANUP,
    "This is switch-time cleanup, never passive timeout cleanup.",
    _rule("REQUIRED_fragment_50"),
    "never derives a foreign owner from `owned`\nor from an absent local token.",
    "never disables a gate-held session without a\nlocally held issuer token.",
    "Leaving the B503 perspective uses the same locally-token-bound cleanup\nrule as target switching.",
    PROJECTION_CARD_ADMISSION,
    SELECTED_TARGET_TYPED_HISTORY,
    B503_KEYBOARD_ACCESSIBILITY,
    B503_CAPABILITY_RECONNECT,
    B503_FIELD_OPERATION_ERRORS,
    B503_FRONTEND_EPOCH_ROLLOVER,
    B503_DISABLED_PUBLIC_MAPPING,
    B503_ACTIVE_UNKNOWN_OWNER,
    B503_REFRESHING_UNKNOWN_STRIP,
    B503_REFRESH_CONTINUATION,
    'data-testid="b503-install-writes-banner"',
    'id="b503-ad02-tooltip-anchor"',
    "generic AD02 installation-write warning",
    "It exposes no device command name, selector\nname, or control.",
    "real installation/device write still needs action-time\noperator confirmation.",
    "scripts/check_portal_ux_contract.py",
)

FORBIDDEN = _rule("FORBIDDEN")

FORBIDDEN_B503_DOM_COMMAND_TOKENS = frozenset((
    "clear",
    "delete",
    "reset",
    "clearerrorhistory",
    "clearservicehistory",
))
FORBIDDEN_INSTALLATION_SELECTORS = frozenset(("0201", "0202"))
DOM_SELECTOR_TOKEN = re.compile(
    r"(?<![0-9])(?:0x)?02[\s_:-]*(?:0x)?0[12](?![0-9])", re.IGNORECASE
)
DOM_COMMAND_TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
PLAIN_CONTROL_NOUN = re.compile(
    r"\b(?:button|control|link|action|command|selector|menu|item|affordance|"
    r"capability|operation|service|feature)\b",
    re.IGNORECASE,
)
PLAIN_AFFIRMATIVE_CONTROL_VERB = re.compile(
    _rule("PLAIN_AFFIRMATIVE_CONTROL_VERB_fragment_2"),
    re.IGNORECASE,
)
PLAIN_CONTROL_CLAUSE_BOUNDARY = re.compile(
    r"\s*(?:;|\bbut\b|\bhowever\b)\s*", re.IGNORECASE
)
PLAIN_AFFIRMATIVE_DOUBLE_NEGATIVE = re.compile(
    _rule("PLAIN_AFFIRMATIVE_DOUBLE_NEGATIVE_fragment_2"),
    re.IGNORECASE,
)
PLAIN_AFFIRMATIVE_ENABLED_STATE = re.compile(
    r"\b(?:must|shall|may|can|will|is|are|was|were)\s+"
    r"(?:be\s+|remain\s+)?enabled\b",
    re.IGNORECASE,
)
COMPACT_PROHIBITED_COMMAND = re.compile(
    _rule("COMPACT_PROHIBITED_COMMAND_fragment_2"),
    re.IGNORECASE,
)
INLINE_CODE_FRAGMENT = re.compile(r"\x60([^\x60\n]+)\x60")
INLINE_CODE_ATTRIBUTE = re.compile(
    r"(?<![A-Za-z0-9_:.-])([A-Za-z_:][A-Za-z0-9_:.-]*)\s*=\s*"
    r"(?:\"([^\"]*)\"|'([^']*)'|([^\s]+))"
)
DOM_RELEVANT_ATTRIBUTE_NAME = re.compile(
    _rule("DOM_RELEVANT_ATTRIBUTE_NAME_fragment_2"),
    re.IGNORECASE,
)
HTML_URL_ATTRIBUTE_NAMES = frozenset(
    (
        "href", "xlink:href", "src", "srcset", "imagesrcset", "action", "formaction",
        "poster", "cite", "data", "ping",
    )
)
HTML_VOID_ELEMENTS = frozenset((
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
))
NON_RENDERING_CONTAINERS = frozenset(
    (
        "audio", "canvas", "defs", "desc", "head", "iframe", "metadata",
        "noscript", "object", "pre", "script", "style", "template", "title",
        "video",
    )
)
B503_ROUTE_SURFACE_MARKERS = _rule("B503_ROUTE_SURFACE_MARKERS")
B503_ROUTE_SURFACE_PARAGRAPHS = _rule("B503_ROUTE_SURFACE_PARAGRAPHS")
MARKDOWN = MarkdownIt("commonmark")
TABLE_MARKDOWN = MarkdownIt("commonmark").enable("table")
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
CSS_LINE_CONTINUATION = re.compile(r"\\(?:\r\n|[\n\r\f])")
CSS_ESCAPE = re.compile(
    r"\\([0-9a-fA-F]{1,6})(?:\r\n|[ \t\r\n\f])?|\\([^\r\n\f0-9a-fA-F])"
)
HTML_COMMENT = re.compile(r"<!--.*?(?:-->|$)", re.DOTALL)
COMMONMARK_AUTOLINK = re.compile(
    r"<(?:https?://|mailto:)[^<>\s]+>", re.IGNORECASE
)
ISO_DATE = re.compile(r"(?<![0-9])\d{4}-\d{2}-\d{2}(?![0-9])")
COMPACT_B503_SELECTOR = re.compile(
    r"(?:b503(?:selector)?|selector)020([12])(?![0-9])"
)


class CheckError(ValueError):
    """The public Portal contract is missing a required safety boundary."""


class _DOMSnippetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, list[tuple[str, str | None]], list[str]]] = []
        self._stack: list[tuple[str, list[tuple[str, str | None]], list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element = (tag, attrs, [])
        self.elements.append(element)
        if tag.lower() not in HTML_VOID_ELEMENTS:
            self._stack.append(element)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag, attrs, []))

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        for _, _, text in self._stack:
            text.append(data)


class _VisibleContractSourceParser(HTMLParser):
    """Retain source visible to a CommonMark reader, excluding inert HTML."""

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
        # The raw target is audited separately for route/control/selector DOM.
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

    def handle_decl(self, decl: str) -> None:
        if not self._inert_stack:
            self.parts.append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        if not self._inert_stack:
            self.parts.append(f"<?{data}>")


def _visible_contract_source(target: str) -> str:
    parser = _VisibleContractSourceParser()
    parser.feed(COMMONMARK_AUTOLINK.sub("", target))
    parser.close()
    return "".join(parser.parts)


def _decode_css_escapes(value: str) -> str:
    value = CSS_LINE_CONTINUATION.sub("", value)

    def replace(match: re.Match[str]) -> str:
        if match.group(1) is None:
            return match.group(2)
        codepoint = int(match.group(1), 16)
        if codepoint == 0 or 0xD800 <= codepoint <= 0xDFFF or codepoint > sys.maxunicode:
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


def _target_line_bounds(text: str) -> tuple[int, int]:
    """Locate the target only from rendered CommonMark level-two headings."""
    tokens = MARKDOWN.parse(text)
    start_line: int | None = None
    start_title = TARGET_START.removeprefix("## ")
    end_title = TARGET_END.removeprefix("## ")
    for index, token in enumerate(tokens[:-1]):
        if token.type != "heading_open" or token.tag != "h2" or token.map is None:
            continue
        title = tokens[index + 1]
        if title.type != "inline":
            continue
        if start_line is None and title.content == start_title:
            start_line = token.map[0]
            continue
        if start_line is not None and title.content == end_title:
            return start_line, token.map[0]
    raise CheckError("api/portal.md: INT-10 rendered H2 section boundary missing")


def _target_section(text: str) -> str:
    start_line, end_line = _target_line_bounds(text)
    return "".join(text.splitlines(keepends=True)[start_line:end_line])


def _require_genuine_availability_table(text: str) -> None:
    """Require the frozen rows to be a Markdown table in the original document."""
    start_line, end_line = _target_line_bounds(text)
    lines = text.splitlines()
    header_lines = [
        index
        for index in range(start_line, min(end_line, len(lines)))
        if lines[index] == AVAILABILITY_TABLE_HEADER
    ]
    table_starts = {
        token.map[0]
        for token in TABLE_MARKDOWN.parse(text)
        if token.type == "table_open" and token.map is not None
    }
    if len(header_lines) != 1 or header_lines[0] not in table_starts:
        raise CheckError(
            "api/portal.md: B503 availability rows must be one rendered Markdown table"
        )


def _availability_table_rows(target: str) -> list[str]:
    lines = target.splitlines()
    try:
        header_index = lines.index(AVAILABILITY_TABLE_HEADER)
    except ValueError as exc:
        raise CheckError("api/portal.md: B503 availability table header missing") from exc
    if header_index + 1 >= len(lines) or lines[header_index + 1] != AVAILABILITY_TABLE_SEPARATOR:
        raise CheckError("api/portal.md: B503 availability table separator missing")

    rows: list[str] = []
    for line in lines[header_index + 2 :]:
        if not line.startswith("|"):
            break
        rows.append(line)
    return rows


def _normalized_hex_selector(value: str) -> str | None:
    normalized = re.sub(r"[\s_:-]", "", value.lower())
    normalized = normalized.replace("0x", "")
    if re.fullmatch(r"[0-9a-f]+", normalized):
        return normalized
    return None


def _identifier_tokens(value: str) -> set[str]:
    segmented = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    segmented = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", segmented)
    return {token.lower() for token in DOM_COMMAND_TOKEN.findall(segmented)}


def _selector_tokens(value: str) -> set[str]:
    without_dates = ISO_DATE.sub("", value)
    tokens = {
        _normalized_hex_selector(match.group(0))
        for match in DOM_SELECTOR_TOKEN.finditer(without_dates)
    }
    compact = re.sub(r"[^a-z0-9]", "", without_dates.casefold()).replace("0x", "")
    tokens.update(
        f"020{match.group(1)}" for match in COMPACT_B503_SELECTOR.finditer(compact)
    )
    return {token for token in tokens if token is not None}


def _compact_prohibited_command_tokens(value: str) -> set[str]:
    candidates = _identifier_tokens(value)
    candidates.add(re.sub(r"[^a-z0-9]", "", value.lower()))
    return {
        candidate
        for candidate in candidates
        if COMPACT_PROHIBITED_COMMAND.fullmatch(candidate)
    }


def _reject_prohibited_command_tokens(context: str, value: str) -> None:
    prohibited_commands = (
        _identifier_tokens(value) & FORBIDDEN_B503_DOM_COMMAND_TOKENS
    ) | _compact_prohibited_command_tokens(value)
    if prohibited_commands:
        raise CheckError(
            "api/portal.md: prohibited B503 command token in DOM "
            f"{context}: {value!r}"
        )


def _reject_prohibited_dom_component(context: str, value: str) -> None:
    value = unescape(value)
    if _selector_tokens(value) & FORBIDDEN_INSTALLATION_SELECTORS:
        raise CheckError(
            "api/portal.md: prohibited B503 installation selector in DOM "
            f"{context}: {value!r}"
        )
    _reject_prohibited_command_tokens(context, value)


def _decoded_dom_attribute_value(attribute: str, value: str) -> str:
    decoded = unescape(value)
    normalized_attribute = attribute.casefold()
    if (
        normalized_attribute in HTML_URL_ATTRIBUTE_NAMES
        or normalized_attribute.startswith("on")
    ):
        decoded = unquote(decoded)
    return decoded


def _parsed_dom_elements(target: str) -> list[tuple[str, list[tuple[str, str | None]], list[str]]]:
    parser = _DOMSnippetParser()
    # HTMLParser treats CommonMark autolinks as unterminated HTML tags and then
    # misclassifies following prose as descendant DOM text.
    parser.feed(COMMONMARK_AUTOLINK.sub("", target))
    parser.close()
    return parser.elements


def _target_inline_tokens(document: str) -> list[object]:
    """Parse once so CommonMark resolves document-scoped references correctly."""
    start_line, end_line = _target_line_bounds(document)
    return [
        token
        for token in MARKDOWN.parse(document)
        if token.type == "inline"
        and token.map is not None
        and start_line <= token.map[0] < end_line
    ]


def _target_html_blocks(document: str) -> list[str]:
    start_line, end_line = _target_line_bounds(document)
    return [
        token.content
        for token in MARKDOWN.parse(document)
        if token.type == "html_block"
        and token.map is not None
        and start_line <= token.map[0] < end_line
    ]


def _target_fenced_contents(document: str) -> list[str]:
    start_line, end_line = _target_line_bounds(document)
    return [
        token.content
        for token in MARKDOWN.parse(document)
        if token.type in ("fence", "code_block")
        and token.map is not None
        and start_line <= token.map[0] < end_line
    ]


def _rendered_children(children: list[object] | None) -> str:
    rendered: list[str] = []
    for child in children or ():
        if child.type in ("text", "text_special", "code_inline"):
            rendered.append(child.content)
        elif child.type == "image":
            rendered.append(_rendered_children(child.children))
        elif child.type in ("softbreak", "hardbreak"):
            rendered.append("\n")
        # Formatting and raw HTML tags have no rendered text of their own. Text
        # nested between raw inline tags is emitted as adjacent text tokens.
    return "".join(rendered)


def _plain_rendered_children(children: list[object] | None) -> str:
    rendered: list[str] = []
    for child in children or ():
        if child.type in ("text", "text_special", "code_inline"):
            rendered.append(child.content)
        elif child.type in ("softbreak", "hardbreak"):
            rendered.append("\n")
    return "".join(rendered)


def _affirmative_control_verb(clause: str) -> re.Match[str] | None:
    for match in PLAIN_AFFIRMATIVE_CONTROL_VERB.finditer(clause):
        prefix = clause[: match.start()].casefold()
        suffix = clause[match.end() :].casefold()
        if re.search(
            r"(?:do|does|did|must|shall|may|can|is|are|was|were)\s+not\s+$",
            prefix,
        ):
            continue
        if re.search(
            r"(?:(?:do|does|did|is|are|was|were|can|must|shall|may)n['’]t|"
            r"cannot)\s+$",
            prefix,
        ):
            continue
        if re.search(r"\bnever\s+$", prefix):
            continue
        if re.match(r"\s+no\b", suffix):
            continue
        if re.match(
            r"\s+(?:not|absent|unavailable|unsupported|hidden|disabled|"
            r"prohibited|forbidden)\b",
            suffix,
        ):
            continue
        if re.match(r"^\s*no\b", clause, re.IGNORECASE):
            continue
        if (
            match.group(0).casefold() in {"be", "is", "are"}
            and PLAIN_CONTROL_NOUN.search(clause) is None
        ):
            continue
        return match
    return None


def _reject_affirmative_control_text(plain: str, context: str) -> None:
    for sentence in re.split(r"(?<=[.!?])\s+", plain):
        for clause in PLAIN_CONTROL_CLAUSE_BOUNDARY.split(sentence):
            if not clause:
                continue
            if not (
                (_identifier_tokens(clause) & FORBIDDEN_B503_DOM_COMMAND_TOKENS)
                or _compact_prohibited_command_tokens(clause)
            ):
                continue
            if PLAIN_AFFIRMATIVE_DOUBLE_NEGATIVE.search(clause) is not None:
                raise CheckError(
                    f"api/portal.md: double-negative {context} clause requires a "
                    f"prohibited B503 control: {clause!r}"
                )
            if PLAIN_AFFIRMATIVE_ENABLED_STATE.search(clause) is not None:
                raise CheckError(
                    f"api/portal.md: enabled {context} state requires a prohibited "
                    f"B503 control: {clause!r}"
                )
            if _affirmative_control_verb(clause) is not None:
                raise CheckError(
                    f"api/portal.md: affirmative {context} description exposes a "
                    f"prohibited B503 control: {clause!r}"
                )


def _reject_affirmative_plain_markdown_controls(document: str) -> None:
    for inline in _target_inline_tokens(document):
        _reject_affirmative_control_text(
            _plain_rendered_children(inline.children), "plain-Markdown"
        )
    for content in _target_fenced_contents(document):
        _reject_affirmative_control_text(content, "fenced-content")


def _markdown_dom_references(document: str) -> list[tuple[str, str]]:
    references: list[tuple[str, str]] = []
    for inline in _target_inline_tokens(document):
        children = inline.children or ()
        link_labels: list[list[str]] = []
        for child in children:
            if child.type == "link_open":
                link_labels.append([])
                references.append(
                    ("Markdown link destination", unquote(child.attrGet("href") or ""))
                )
                title = child.attrGet("title")
                if title is not None:
                    references.append(("Markdown link title", title))
                continue
            if child.type == "link_close":
                if link_labels:
                    references.append(("Markdown link label", "".join(link_labels.pop())))
                continue
            if child.type == "image":
                references.append(("Markdown image alt", _rendered_children(child.children)))
                references.append(
                    ("Markdown image destination", unquote(child.attrGet("src") or ""))
                )
                title = child.attrGet("title")
                if title is not None:
                    references.append(("Markdown image title", title))
            if link_labels:
                link_labels[-1].append(_rendered_children([child]))
    return references


def _normalized_rendered(value: str) -> str:
    return " ".join(value.split()).casefold()


def _normalized_commonmark_paragraph(value: str) -> str:
    inlines = [token for token in MARKDOWN.parse(value) if token.type == "inline"]
    if len(inlines) != 1:
        raise AssertionError("frozen route surface must be exactly one paragraph")
    return _normalized_rendered(_rendered_children(inlines[0].children))


def _mentions_route_surface(value: str) -> bool:
    value = unquote(value)
    return (
        re.search(r"\b(?:REST|MCP)\b", value, re.IGNORECASE) is not None
        or any(
            marker in value.casefold()
            for marker in B503_ROUTE_SURFACE_MARKERS[2:]
        )
    )


def _decode_css_escapes(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        hexadecimal = match.group(1)
        if hexadecimal is None:
            return match.group(2)
        codepoint = int(hexadecimal, 16)
        if codepoint == 0 or codepoint > sys.maxunicode or 0xD800 <= codepoint <= 0xDFFF:
            return "\uFFFD"
        return chr(codepoint)

    return re.sub(
        r"\\(?:([0-9a-fA-F]{1,6})(?:[ \t\r\n\f]|\r\n)?|([^\r\n\f]))",
        replace,
        value,
    )


def _css_route_destinations(value: str) -> list[str]:
    css = _decode_css_escapes(unescape(value))
    destinations = [
        unquote(match.group(2).strip())
        for match in re.finditer(
            r"""url\(\s*(["']?)(.*?)\1\s*\)""", css, re.IGNORECASE
        )
    ]
    destinations.extend(
        unquote(match.group(2).strip())
        for match in re.finditer(
            r"""@import\s+(["'])(.*?)\1""", css, re.IGNORECASE
        )
    )
    return destinations


def _html_element_route_destinations(
    tag: str,
    attrs: list[tuple[str, str | None]],
    text: list[str],
    depth: int = 0,
) -> list[str]:
    destinations = [
        _decoded_dom_attribute_value(attribute, value)
        for attribute, value in attrs
        if value is not None
        and (
            attribute.casefold() in HTML_URL_ATTRIBUTE_NAMES
            or attribute.casefold().startswith("on")
        )
    ]
    for attribute, value in attrs:
        if value is None or attribute.casefold() != "srcdoc":
            continue
        if depth >= 8:
            raise CheckError("api/portal.md: srcdoc nesting exceeds the route-audit bound")
        embedded = unescape(value)
        for child_tag, child_attrs, child_text in _parsed_dom_elements(embedded):
            destinations.extend(
                _html_element_route_destinations(
                    child_tag, child_attrs, child_text, depth + 1
                )
            )
    for attribute, value in attrs:
        if value is not None and attribute.casefold() == "style":
            destinations.extend(_css_route_destinations(value))
    if tag.casefold() == "style":
        destinations.extend(_css_route_destinations("".join(text)))
    attributes = {
        attribute.casefold(): value
        for attribute, value in attrs
        if value is not None
    }
    if (
        tag.casefold() == "meta"
        and (attributes.get("http-equiv") or "").strip().casefold() == "refresh"
    ):
        content = unescape(attributes.get("content") or "")
        match = re.search(r"(?:^|;)\s*url\s*=\s*(.+?)\s*$", content, re.IGNORECASE)
        if match is not None:
            destination = match.group(1).strip()
            if (
                len(destination) >= 2
                and destination[0] == destination[-1]
                and destination[0] in "\"'"
            ):
                destination = destination[1:-1]
            destinations.append(unquote(destination))
    return destinations


def _inline_route_destinations(children: list[object] | None) -> list[str]:
    destinations: list[str] = []
    for child in children or ():
        if child.type == "link_open":
            destinations.append(child.attrGet("href") or "")
        elif child.type == "image":
            destinations.append(child.attrGet("src") or "")
        elif child.type == "html_inline":
            for tag, attrs, text in _parsed_dom_elements(child.content):
                destinations.extend(_html_element_route_destinations(tag, attrs, text))
    return destinations


def _authorizes_url_fallback(visible: str, destinations: list[str]) -> bool:
    if not destinations:
        return False
    normalized = " ".join(visible.split())
    has_failure = re.search(
        r"\b(?:main\s+graphql|graphql|fixed\s+route|b503\s+route)\b.*"
        r"\b(?:fail(?:s|ed|ure)?|unavailable)\b",
        normalized,
        re.IGNORECASE,
    ) or re.search(
        r"\b(?:fail(?:s|ed|ure)?|unavailable)\b.*"
        r"\b(?:main\s+graphql|graphql|fixed\s+route|b503\s+route)\b",
        normalized,
        re.IGNORECASE,
    )
    has_fallback = re.search(
        r"\b(?:use|uses|used|try|tries|retry|retries|fallback|backup|"
        r"switch|switches|reroute|reroutes)\b",
        normalized,
        re.IGNORECASE,
    )
    return bool(has_failure and has_fallback)


def _literal_html_route_destinations(target: str) -> list[str]:
    destinations: list[str] = []
    for tag, attrs, text in _parsed_dom_elements(target):
        destinations.extend(_html_element_route_destinations(tag, attrs, text))
    return destinations


def _reject_unapproved_route_surface_paragraphs(document: str) -> None:
    target = _target_section(document)
    if any(
        _mentions_route_surface(destination)
        for destination in _literal_html_route_destinations(target)
    ) or any(
        _mentions_route_surface(content)
        for content in _target_fenced_contents(document)
    ):
        raise CheckError(
            "api/portal.md: B503 route surfaces must remain confined to the five "
            "frozen route/provenance paragraphs"
        )
    for block in _target_html_blocks(document):
        elements = _parsed_dom_elements(block)
        visible = " ".join("".join(text) for _, _, text in elements)
        destinations = [
            destination
            for tag, attrs, text in elements
            for destination in _html_element_route_destinations(tag, attrs, text)
        ]
        if _authorizes_url_fallback(visible, destinations):
            raise CheckError(
                "api/portal.md: arbitrary URL fallback is outside the fixed B503 routes"
            )
    expected = [
        _normalized_commonmark_paragraph(value)
        for value in B503_ROUTE_SURFACE_PARAGRAPHS
    ]
    found: list[str] = []
    for inline in _target_inline_tokens(document):
        visible = _rendered_children(inline.children)
        destinations = _inline_route_destinations(inline.children)
        if _authorizes_url_fallback(visible, destinations):
            raise CheckError(
                "api/portal.md: arbitrary URL fallback is outside the fixed B503 routes"
            )
        if _mentions_route_surface(visible) or any(
            _mentions_route_surface(destination)
            for destination in destinations
        ):
            found.append(_normalized_rendered(visible))
    if found != expected:
        raise CheckError(
            "api/portal.md: B503 route surfaces must remain confined to the five "
            "frozen route/provenance paragraphs"
        )


def _reject_installation_selectors_in_target(document: str) -> None:
    for inline in _target_inline_tokens(document):
        rendered = _rendered_children(inline.children)
        if _selector_tokens(unescape(rendered)) & FORBIDDEN_INSTALLATION_SELECTORS:
            raise CheckError(
                "api/portal.md: B503 installation selectors 0201/0202 must not "
                "appear in the public target section"
            )
    for content in _target_fenced_contents(document):
        if _selector_tokens(unescape(content)) & FORBIDDEN_INSTALLATION_SELECTORS:
            raise CheckError(
                "api/portal.md: B503 installation selectors 0201/0202 must not "
                "appear in fenced target-section content"
            )


def _inline_code_dom_attributes(target: str) -> list[tuple[str, str]]:
    attributes: list[tuple[str, str]] = []
    for fragment in INLINE_CODE_FRAGMENT.findall(target):
        parsed = [
            (
                match.group(1),
                next(group for group in match.groups()[1:] if group is not None),
            )
            for match in INLINE_CODE_ATTRIBUTE.finditer(fragment)
        ]
        if any(
            DOM_RELEVANT_ATTRIBUTE_NAME.fullmatch(attribute) is not None
            or attribute.casefold() in HTML_URL_ATTRIBUTE_NAMES
            for attribute, _ in parsed
        ):
            attributes.extend(parsed)
    return attributes


def _reject_prohibited_dom_references(target: str, document: str) -> None:
    for context, value in _markdown_dom_references(document):
        _reject_prohibited_dom_component(context, value)
    for attribute, value in _inline_code_dom_attributes(target):
        _reject_prohibited_dom_component("inline-code attribute name", attribute)
        _reject_prohibited_dom_component(
            f"inline-code attribute value for {attribute}",
            _decoded_dom_attribute_value(attribute, value),
        )
    for tag, attrs, text in _parsed_dom_elements(target):
        _reject_prohibited_dom_component("element name", tag)
        for attribute, value in attrs:
            _reject_prohibited_dom_component("attribute name", attribute)
            if value is not None:
                _reject_prohibited_dom_component(
                    f"attribute value for {attribute}",
                    _decoded_dom_attribute_value(attribute, value),
                )
        _reject_prohibited_dom_component("element text", "".join(text))


def validate_text(text: str) -> None:
    target = _target_section(text)
    _require_genuine_availability_table(text)
    # REQUIRED is deliberately limited to the frozen INT-10 contract. Content
    # inside comments or declared non-rendering HTML containers is not part of
    # the visible public contract.
    rendered_target_source = _rendered_contract_source(target)
    for fragment in REQUIRED:
        if fragment not in rendered_target_source:
            raise CheckError(
                "api/portal.md: missing required INT-10 target contract fragment: "
                f"{fragment!r}"
            )
    for fragment in FORBIDDEN:
        if fragment in text:
            raise CheckError(f"api/portal.md: forbidden stale or premature wording: {fragment!r}")
    for fragment in FORBIDDEN_B503_SESSION_STATE_CLAUSES:
        if fragment in target:
            raise CheckError(
                "api/portal.md: forbidden B503 session-state contradiction: "
                f"{fragment!r}"
            )
    for pattern in B503_SESSION_STATE_CONTRADICTION_PATTERNS:
        match = pattern.search(target)
        if match is not None:
            raise CheckError(
                "api/portal.md: forbidden declarative B503 session-state "
                f"contradiction: {match.group(0)!r}"
            )
    remaining_target = target.replace(B503_NO_EXPIRED_STATE, "", 1)
    if re.search(r"\bEXPIRED\b", remaining_target, re.IGNORECASE) is not None:
        raise CheckError(
            "api/portal.md: EXPIRED must not be reintroduced as a B503 "
            "availability or session state"
        )
    _reject_unapproved_route_surface_paragraphs(text)
    _reject_installation_selectors_in_target(text)
    _reject_prohibited_dom_references(target, text)
    _reject_affirmative_plain_markdown_controls(text)
    expected_availability_rows = list(AVAILABILITY_ROWS.values())
    if _availability_table_rows(rendered_target_source) != expected_availability_rows:
        raise CheckError(
            "api/portal.md: B503 availability table must contain exactly the five "
            "frozen reason/selector/presentation rows, with no duplicates or extra rows"
        )


def main() -> int:
    try:
        validate_text(DOC.read_text(encoding="utf-8"))
    except (OSError, CheckError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print("Portal UX contract gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
