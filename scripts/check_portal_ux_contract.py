#!/usr/bin/env python3
"""Validate the public INT-10 Portal and Vaillant B503 target contract."""
from __future__ import annotations

from html.parser import HTMLParser
import pathlib
import re
import sys


DOC = pathlib.Path("api/portal.md")
TARGET_START = "## Contribution-Driven Portal Contract V1 (INT-10 Target)"
TARGET_END = "## Observe-First Contract Ownership"

AVAILABILITY_ROWS = {
    "AVAILABLE": "| `AVAILABLE` | `data-testid=\"b503-state-available\"` | Render admitted B503 tabs and the session strip for the selected target. |",
    "NOT_SUPPORTED": "| `NOT_SUPPORTED` | `data-testid=\"b503-state-not-supported\"` | State that the selected target does not support the B503 surface; do not infer a value. |",
    "TRANSPORT_DOWN": "| `TRANSPORT_DOWN` | `data-testid=\"b503-state-transport-down\"` | State that transport is unavailable and offer only a retry/reconnect hint. |",
    "SESSION_BUSY": "| `SESSION_BUSY` | `data-testid=\"b503-state-session-busy\"` | State neutrally that bounded ownership-or-lifecycle contention makes the session busy; do not infer a foreign owner. |",
    "UNKNOWN": "| `UNKNOWN` | `data-testid=\"b503-state-unknown\"` | State that capability is undetermined; do not equate it with unsupported. |",
}
AVAILABILITY_TABLE_HEADER = "| Reason | Stable selector | Required presentation truth |"
AVAILABILITY_TABLE_SEPARATOR = "|---|---|---|"
PROJECTION_CARD_ADMISSION = (
    "The section-projection card\n"
    "uses `data-role=\"projection-b503-card\"` only for `AVAILABLE` B503 capability."
)
SELECTED_TARGET_TYPED_HISTORY = (
    "The History tab uses the typed B503 history GraphQL records for the selected\n"
    "target and has `data-role=\"vaillant-b503-tab-history\"`; it does not infer\n"
    "history from labels or retained aggregate data."
)
B503_KEYBOARD_ACCESSIBILITY = (
    "The selected-target B503 tabs expose a `role=\"tablist\"` with one named\n"
    "`role=\"tab\"` and matching `role=\"tabpanel\"` for Errors, Service, History, and\n"
    "Live-Monitor. Each tab exposes `aria-selected`; ArrowLeft, ArrowRight, Home,\n"
    "and End move tab focus, while Enter and Space select the focused tab. The\n"
    "session strip is a named `role=\"status\"` for the selected target."
)
B503_CAPABILITY_RECONNECT = (
    "On a Gateway capability transition or transport reconnect, the browser renders\n"
    "only the Gateway-supplied availability state. It neither preserves\n"
    "`AVAILABLE`, replays a session enable/disable action, nor changes route; it\n"
    "may re-query only the selected target after Gateway publishes a new state."
)
B503_FIELD_OPERATION_ERRORS = (
    "On a selected-target context cancellation before bus turnaround, the browser\n"
    "renders the Gateway-supplied structured `UPSTREAM_TIMEOUT` alongside the\n"
    "unchanged last-known B503 availability. On a selected-target bus/arbitration\n"
    "timeout, NAK, or CRC failure, it renders structured `UPSTREAM_RPC_FAILED`\n"
    "alongside that same availability. Neither field-operation error becomes\n"
    "`TRANSPORT_DOWN` or invalidates capability."
)
B503_FRONTEND_EPOCH_ROLLOVER = (
    "Each target-bound asynchronous request captures a frontend presentation epoch\n"
    "at dispatch. Target switch, B503 navigation-away, and reconnect advance that\n"
    "epoch; a completion may mutate presentation only when both its target address\n"
    "and captured epoch still match, otherwise it is discarded."
)

REQUIRED = (
    TARGET_START,
    "Gateway #552 is open;",
    "`helianthus.gateway.portal-catalog/v1`",
    "The browser obtains the catalog read model only through `POST /graphql/portal/v1`\nand the fixed `PortalCatalogV1` operation.",
    "`POST /graphql/portal/v1`",
    "`PortalCatalogV1`",
    "`PortalActionInvokeV1`",
    "No B503 operation is admitted on this route.",
    "no REST compatibility shim, no alternate Portal API\nroute, no dual semantic publication, and no direct MCP/native fallback.",
    "does not use a central vendor switch or an arbitrary-English parser",
    "`Thermal/HVAC`, `PV`, `Storage/BMS`, `EVSE`, and\n`Infrastructure`",
    "must not require a vendor switch, a product branch, or compatibility logic in\ncentral bootstrap or rendering code.",
    "`(driver_id, manifest_id, manifest_version)`",
    "`catalog_revision`, `catalog_digest`,\n`evaluation_instant`, and caller `authorization_scope`",
    "lifecycle, freshness, projection-loss, quality, and provenance",
    "Accepted source records and accepted semantic records remain distinct from the\nbrowser presentation state.",
    "Discovery\npermission controls visibility",
    "revalidates the request-bound caller,\ncatalog revision/digest claim, contribution identity/digest, resource and\ncapability, semantic snapshot/revision, binding, source epoch/generation,\ntyped preconditions, route, deadline, and idempotency key.",
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
    "`M8-TGT-01`,\n`M8-TGT-02`, `M8-TGT-03`, and `M8-TGT-04`",
    "Changing target atomically invalidates the active target-bound presentation:\ncapability, current errors/service, history, live-monitor strip, and pending\ncompletion must not bleed into the new target.",
    "Any late enable completion after a switch follows the same prior-target cleanup\nand cannot mutate the new target.",
    "`EXPIRED` is\ninternal-only",
    'data-testid="b503-state-available"',
    'data-testid="b503-state-not-supported"',
    'data-testid="b503-state-transport-down"',
    'data-testid="b503-state-session-busy"',
    'data-testid="b503-state-unknown"',
    'data-testid="b503-session-strip"',
    'data-testid="b503-session-state-label"',
    '`Idle`, `Enabling`, `Active`, and\n`Disabled`',
    "base `SESSION_BUSY` presentation is neutral.",
    "On every target switch, before\nadmitting the new target presentation, the browser begins targeted cleanup for\neach prior target that it locally owns and whose session is `ENABLING` or\n`ACTIVE`.",
    "An `ACTIVE` prior target receives an immediate target-specific\ndisable using its locally held issuer token.",
    "For an `ENABLING` prior target,\nthe browser registers that same target-specific disable at switch time and\ndispatches it immediately when the locally initiated enable completes with its\nissuer token.",
    "This is switch-time cleanup, never passive timeout cleanup.",
    "Gateway's session view exposes only `state`\nand opaque `owned`: `owned` means that the Gateway session gate is held, not\nwhich client holds it.",
    "never derives a foreign owner from `owned`\nor from an absent local token.",
    "never disables a gate-held session without a\nlocally held issuer token.",
    "Leaving the B503 perspective uses the same locally-token-bound cleanup\nrule as target switching.",
    PROJECTION_CARD_ADMISSION,
    SELECTED_TARGET_TYPED_HISTORY,
    B503_KEYBOARD_ACCESSIBILITY,
    B503_CAPABILITY_RECONNECT,
    B503_FIELD_OPERATION_ERRORS,
    B503_FRONTEND_EPOCH_ROLLOVER,
    'data-testid="b503-install-writes-banner"',
    'id="b503-ad02-tooltip-anchor"',
    "generic AD02 installation-write warning",
    "It exposes no device command name, selector\nname, or control.",
    "real installation/device write still needs action-time\noperator confirmation.",
    "scripts/check_portal_ux_contract.py",
)

FORBIDDEN = (
    "/portal/api/v1/b503",
    "Gateway #552 is implemented",
    "Gateway #552 has been implemented",
    "Gateway #552 is complete",
)

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
COMPACT_PROHIBITED_COMMAND = re.compile(
    r"^(?:"
    r"b503(?:clear(?!ance|ly)|delete|reset|clearerrorhistory|clearservicehistory)[a-z0-9]*"
    r"|(?:clear(?!ance|ly)|clearerrorhistory|clearservicehistory|delete|reset)[a-z0-9]*"
    r")$",
    re.IGNORECASE,
)
INLINE_CODE_FRAGMENT = re.compile(r"\x60([^\x60\n]+)\x60")
INLINE_CODE_ATTRIBUTE = re.compile(
    r"(?<![A-Za-z0-9_:.-])([A-Za-z_:][A-Za-z0-9_:.-]*)\s*=\s*"
    r"(?:\"([^\"]*)\"|'([^']*)'|([^\s]+))"
)
DOM_RELEVANT_ATTRIBUTE_NAME = re.compile(
    r"^(?:id|class|for|hidden|name|role|title|value|data-[A-Za-z0-9_:.-]+|aria-[A-Za-z0-9_:.-]+)$",
    re.IGNORECASE,
)
B503_FALLBACK_CONTRADICTIONS = (
    re.compile(
        r"\bmain (?:GraphQL|\x60POST /graphql\x60)(?: route)? "
        r"(?:failure|fails|is unavailable) (?:allows|allowing|may use) "
        r"(?:REST(?: fallback)?|MCP(?: fallback)?|native I/O|the other route)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bmain (?:GraphQL|\x60POST /graphql\x60)(?: route)?(?: failure)? "
        r"(?:falls?|falling) back to "
        r"(?:REST(?: fallback)?|MCP(?: fallback)?|native I/O|the other route)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bmain (?:GraphQL|\x60POST /graphql\x60)(?: route)?"
        r"(?: failure| fails| is unavailable)?[,:; ]+"
        r"(?:the browser )?(?:may )?use "
        r"(?:REST(?: fallback)?|MCP(?: fallback)?|native I/O|the other route) instead\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bmain (?:GraphQL|\x60POST /graphql\x60)(?: route)? uses "
        r"(?:REST(?: fallback)?|MCP(?: fallback)?|native I/O|the other route) "
        r"as a fallback\b",
        re.IGNORECASE,
    ),
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


def _target_section(text: str) -> str:
    try:
        start = text.index(TARGET_START)
        end = text.index(TARGET_END, start)
    except ValueError as exc:
        raise CheckError("api/portal.md: INT-10 target section boundary missing") from exc
    return text[start:end]


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
    tokens = {
        _normalized_hex_selector(match.group(0))
        for match in DOM_SELECTOR_TOKEN.finditer(value)
    }
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
    if _selector_tokens(value) & FORBIDDEN_INSTALLATION_SELECTORS:
        raise CheckError(
            "api/portal.md: prohibited B503 installation selector in DOM "
            f"{context}: {value!r}"
        )
    _reject_prohibited_command_tokens(context, value)


def _parsed_dom_elements(target: str) -> list[tuple[str, list[tuple[str, str | None]], list[str]]]:
    parser = _DOMSnippetParser()
    parser.feed(target)
    parser.close()
    return parser.elements


def _inline_code_dom_attributes(target: str) -> list[tuple[str, str]]:
    attributes: list[tuple[str, str]] = []
    for fragment in INLINE_CODE_FRAGMENT.findall(target):
        for match in INLINE_CODE_ATTRIBUTE.finditer(fragment):
            attribute = match.group(1)
            if DOM_RELEVANT_ATTRIBUTE_NAME.fullmatch(attribute) is None:
                continue
            value = next(group for group in match.groups()[1:] if group is not None)
            attributes.append((attribute, value))
    return attributes


def _reject_prohibited_dom_references(target: str) -> None:
    for attribute, value in _inline_code_dom_attributes(target):
        _reject_prohibited_dom_component("inline-code attribute name", attribute)
        _reject_prohibited_dom_component(
            f"inline-code attribute value for {attribute}", value
        )
    for tag, attrs, text in _parsed_dom_elements(target):
        _reject_prohibited_dom_component("element name", tag)
        for attribute, value in attrs:
            _reject_prohibited_dom_component("attribute name", attribute)
            if value is not None:
                _reject_prohibited_dom_component(
                    f"attribute value for {attribute}", value
                )
        _reject_prohibited_dom_component("element text", "".join(text))


def validate_text(text: str) -> None:
    target = _target_section(text)
    for fragment in REQUIRED:
        if fragment not in target:
            raise CheckError(
                "api/portal.md: missing required INT-10 target contract fragment: "
                f"{fragment!r}"
            )
    for fragment in FORBIDDEN:
        if fragment in text:
            raise CheckError(f"api/portal.md: forbidden stale or premature wording: {fragment!r}")
    for contradiction in B503_FALLBACK_CONTRADICTIONS:
        if contradiction.search(target):
            raise CheckError(
                "api/portal.md: affirmative B503 main-GraphQL fallback contradiction"
            )
    _reject_prohibited_dom_references(target)
    expected_availability_rows = list(AVAILABILITY_ROWS.values())
    if _availability_table_rows(target) != expected_availability_rows:
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
