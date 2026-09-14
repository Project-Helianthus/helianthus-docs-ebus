#!/usr/bin/env python3
"""Validate the public INT-10 Portal and Vaillant B503 target contract."""
from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import pathlib
import re
import sys
from urllib.parse import unquote

from markdown_it import MarkdownIt


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
B503_SESSION_STATE_CONTRACT = (
    "The strip states are `Idle`, `Enabling`, `Active`, and\n"
    "`Refreshing`, and `Disabled`. `Refreshing` means an epoch refresh holds the\n"
    "ownership gate; the already-admitted triggering request remains pending and\n"
    "new bus-facing live-monitor reads/actions are busy. Status-only\n"
    "`vaillantCapabilities(targetAddress:)` and\n"
    "`vaillantLiveMonitorSession(targetAddress:)` queries remain available to observe\n"
    "availability and session completion. Refresh success returns `Active` and\n"
    "completes a triggering read with exactly one native operation result, or\n"
    "dispatches a triggering current-owner disable exactly once; only a valid disable\n"
    "ACK completes its `Disabled` cleanup to `Idle`.\n"
    "Refresh failure releases the gate, presents session `Idle` with `owned:false`,\n"
    "retains Gateway's process-local cleanup obligation, and completes that request\n"
    "with the exact unavailable failure without dispatching its native operation;\n"
    "Enable remains unavailable.\n"
    "`Disabled` is never reported with `owned:true`."
)
B503_DISABLED_PUBLIC_MAPPING = (
    "`Disabled` with `owned:false` maps only an\n"
    "explicit operator or configuration disable; enable failure, the 30-second idle\n"
    "timeout, transport disconnect, and gateway restart map to `Idle` with\n"
    "`owned:false`; while cleanup is pending, capability remains unavailable and\n"
    "`Idle` does not admit Enable."
)
B503_REFRESHING_CLEANUP = (
    "For a `REFRESHING` prior target, the browser queues that\n"
    "same token-bound disable without invoking an operation while Refreshing is busy;\n"
    "after refresh succeeds to `Active`, it dispatches the queued disable. After\n"
    "refresh failure presents `Idle`, Gateway retains the process-local cleanup\n"
    "obligation. The browser clears the queued pair without a client disable.\n"
    "If the triggering request was already the current-owner disable, that single\n"
    "disable is the only client dispatch. A valid disable ACK completes `Disabled`\n"
    "cleanup to `Idle`; every other outcome returns exactly and leaves Gateway's\n"
    "process-local defensive cleanup in force. In both cases the browser clears\n"
    "the queued pair without issuing a second disable."
)
B503_ENABLING_CLEANUP = (
    "For an\n"
    "`ENABLING` prior target, the browser registers cleanup at switch time under the\n"
    "exact `(targetAddress, localEnableAttemptID, presentationEpoch)` tuple and\n"
    "uses a fresh browser-local opaque `localEnableAttemptID` allocated before\n"
    "dispatch and never reused. It\n"
    "dispatches a target-specific disable immediately only when that same attempt\n"
    "completes successfully with its issuer token. If that attempt does not complete\n"
    "successfully with an issuer token—including cancellation before bus turnaround,\n"
    "ACK timeout, NAK, CRC mismatch, bus-arbitration timeout, epoch-advance discard,\n"
    "transport disconnect, gateway restart, or any other terminal failure—the\n"
    "browser clears the registration without issuing a client disable before it may\n"
    "admit any later enable; the registration never transfers to a later attempt or\n"
    "session."
)
B503_TARGET_CLEANUP_SCOPE = (
    "On every target switch, before\n"
    "admitting the new target presentation, the browser begins targeted cleanup for\n"
    "each prior target whose session is `ACTIVE` or `REFRESHING` and for which it\n"
    "holds a local issuer token, plus each `ENABLING` prior target for which it owns\n"
    "the locally initiated pending enable attempt."
)
B503_REFRESHING_UNKNOWN_STRIP = (
    "When a selected target has Gateway session state `Refreshing` with `owned:true`,\n"
    "the session strip remains observable alongside temporarily `UNKNOWN` capability.\n"
    "It is status-only: the section-projection card, B503 tabs, and every new\n"
    "bus-facing B503 read/action remain unavailable until capability is `AVAILABLE`\n"
    "again. Only the status-only `vaillantCapabilities(targetAddress:)` and\n"
    "`vaillantLiveMonitorSession(targetAddress:)` queries remain available; no other\n"
    "operation gains permission."
)
B503_REFRESH_CONTINUATION = (
    "Refresh success revalidates only a surviving authenticated current-owner\n"
    "token/target/epoch handle and returns it to `Active`; it is continuation, not\n"
    "reconstruction or auto-resume. The pending triggering request then completes\n"
    "from exactly one dispatch using the rebound key: a read returns to `Active`,\n"
    "while a current-owner disable completes cleanup to `Idle` only after a valid\n"
    "disable ACK. Any other disable outcome releases the owner, retains only the\n"
    "Gateway's process-local defensive-cleanup obligation, and presents `Idle` with\n"
    "`owned:false` alongside capability `UNKNOWN`; Enable remains unavailable. After restart, a lost owner\n"
    "handle, or an\n"
    "absent/invalid current issuer token, Gateway does not reconstruct the session\n"
    "and the client must issue a new explicit Enable. After restart, each qualified\n"
    "target's live-monitor capability is `UNKNOWN`, Enable is unavailable, and\n"
    "Gateway emits no automatic B503 enable or disable. The Portal exposes no\n"
    "recovery control. Only a separately operator-authorized target-specific\n"
    "maintenance recovery outside public GraphQL/Portal v1 may issue one disable,\n"
    "with action-time confirmation; a valid disable ACK permits normal availability\n"
    "evaluation, while every other outcome remains fail-closed.\n"
    "A terminal transport disconnect releases ownership. A later reconnect has no\n"
    "owner and does not enter `Refreshing`; when defensive cleanup is pending, it\n"
    "must complete before capability can become `AVAILABLE` or a new explicit client\n"
    "Enable can be admitted."
)
FORBIDDEN_B503_SESSION_STATE_CLAUSES = (
    "`Refreshing` may accept live-monitor operations.",
    "`Disabled` may be reported with `owned:true`.",
)
B503_SESSION_STATE_CONTRADICTION_PATTERNS = (
    re.compile(
        r"(?:`Refreshing`\s+(?:(?:may|can|must|shall)\s+)?"
        r"(?:accept|allow|permit)s?\s+(?:new\s+|bus-facing\s+)?live-monitor operations?"
        r"|live-monitor operations?\s+(?:are|remain)\s+"
        r"(?:accepted|allowed|permitted)\s+(?:during|while)\s+`Refreshing`)",
        re.IGNORECASE,
    ),
    re.compile(
        r"`Disabled`\s+(?:(?:may|can|must|shall)\s+be\s+|is\s+)?"
        r"(?:reported|rendered|published|returned)\s+with\s+`owned:true`",
        re.IGNORECASE,
    ),
)
B503_MAIN_ROUTE_OPERATIONS = (
    "- `vaillantCapabilities(targetAddress:)`\n"
    "- `vaillantErrors(targetAddress:)`\n"
    "- `vaillantServiceCurrent(targetAddress:)`\n"
    "- `vaillantErrorHistory(targetAddress:index:)`\n"
    "- `vaillantErrorsHistory(targetAddress:limit:)`\n"
    "- `vaillantServiceHistory(targetAddress:index:)`\n"
    "- `vaillantLiveMonitor(action:issuerToken:targetAddress:)`\n"
    "- `vaillantLiveMonitorSession(targetAddress:)`"
)
B503_NO_EXPIRED_STATE = (
    "`B503Availability` has exactly these five public reasons. `Refreshing` remains\n"
    "only a session observation. `EXPIRED` is neither an availability reason nor a\n"
    "session state and MUST NOT be implemented as an internal or public sixth state."
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
    "source contract commit `a39d43fbeaf8d745222b85649ebb8494203163f0` and current open\nevidence head `a39d43fbeaf8d745222b85649ebb8494203163f0`; #975 remains open,\nintermediate, and unmerged, and this documentation does not claim it is\nmerged.",
    "`M8-TGT-01`,\n`M8-TGT-02`, `M8-TGT-03`, and `M8-TGT-04`",
    "Changing target atomically invalidates the active target-bound presentation:\ncapability, current errors/service, history, live-monitor strip, and pending\ncompletion must not bleed into the new target.",
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
    B503_DISABLED_PUBLIC_MAPPING,
    B503_REFRESHING_UNKNOWN_STRIP,
    B503_REFRESH_CONTINUATION,
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
PLAIN_CONTROL_NOUN = re.compile(
    r"\b(?:button|control|link|action|command|selector|menu|item|affordance|"
    r"capability|operation|service|feature)\b",
    re.IGNORECASE,
)
PLAIN_AFFIRMATIVE_CONTROL_VERB = re.compile(
    r"\b(?:expose(?:s|d)?|render(?:s|ed)?|show(?:s|ed)?|offer(?:s|ed)?|"
    r"provide(?:s|d)?|include(?:s|d)?|add(?:s|ed)?|display(?:s|ed)?|"
    r"present(?:s|ed)?|create(?:s|d)?|support(?:s|ed)?|allow(?:s|ed)?|"
    r"contain(?:s|ed)?|feature(?:s|d)?|list(?:s|ed)?|"
    r"publish(?:es|ed)?|surface(?:s|d)?|exist(?:s|ed)?|appear(?:s|ed)?|"
    r"use(?:s|d)?|click(?:s|ed)?|remain(?:s|ed)?|"
    r"has|have|be|is|are|available|visible)\b",
    re.IGNORECASE,
)
PLAIN_CONTROL_CLAUSE_BOUNDARY = re.compile(
    r"\s*(?:;|\bbut\b|\bhowever\b)\s*", re.IGNORECASE
)
PLAIN_AFFIRMATIVE_DOUBLE_NEGATIVE = re.compile(
    r"\b(?:(?:must|shall|may|can|is|are|was|were)\s+(?:not|never)\s+"
    r"(?:be\s+|remain\s+)?|(?:is|are|was|were)n['’]t\s+)"
    r"(?:hidden|disabled|absent|unavailable|unsupported|prohibited|forbidden)\b",
    re.IGNORECASE,
)
PLAIN_AFFIRMATIVE_ENABLED_STATE = re.compile(
    r"\b(?:must|shall|may|can|will|is|are|was|were)\s+"
    r"(?:be\s+|remain\s+)?enabled\b",
    re.IGNORECASE,
)
COMPACT_PROHIBITED_COMMAND = re.compile(
    r"^(?:"
    r"(?:b503|vaillant)(?:clear(?!ance|ly|fix)|delete|reset|clearerrorhistory|clearservicehistory)[a-z0-9]*"
    r"|(?:clear(?!ance|ly|fix)|clearerrorhistory|clearservicehistory|delete|reset)[a-z0-9]*"
    r")$",
    re.IGNORECASE,
)
INLINE_CODE_FRAGMENT = re.compile(r"\x60([^\x60\n]+)\x60")
INLINE_CODE_ATTRIBUTE = re.compile(
    r"(?<![A-Za-z0-9_:.-])([A-Za-z_:][A-Za-z0-9_:.-]*)\s*=\s*"
    r"(?:\"([^\"]*)\"|'([^']*)'|([^\s]+))"
)
DOM_RELEVANT_ATTRIBUTE_NAME = re.compile(
    r"^(?:id|class|for|hidden|name|role|title|value|href|src|data-[A-Za-z0-9_:.-]+|aria-[A-Za-z0-9_:.-]+|on[a-z][A-Za-z0-9_:.-]*)$",
    re.IGNORECASE,
)
HTML_URL_ATTRIBUTE_NAMES = frozenset(
    (
        "href", "src", "srcset", "imagesrcset", "action", "formaction",
        "poster", "cite", "data", "ping",
    )
)
HTML_VOID_ELEMENTS = frozenset((
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
))
NON_RENDERING_CONTAINERS = frozenset(("head", "script", "style", "template"))
B503_ROUTE_SURFACE_MARKERS = (
    "rest",
    "mcp",
    "native i/o",
    "/portal/api/v1",
    "/graphql/portal/v1",
    "portalcatalogv1",
    "portalactioninvokev1",
    "/graphql",
    "other route",
)
B503_ROUTE_SURFACE_PARAGRAPHS = (
    "The historical `/portal/api/v1/*` endpoints documented below remain their own\n"
    "endpoint contracts. They are not a transport or semantic fallback for this\n"
    "INT-10 B503 presentation.",
    "The browser obtains the catalog read model only through `POST /graphql/portal/v1`\n"
    "and the fixed `PortalCatalogV1` operation. The only action operation on that\n"
    "route is `PortalActionInvokeV1`; it is governed by the action-admission rules\n"
    "below. No B503 operation is admitted on this route.\n"
    "For this B503 UX there is no REST compatibility shim, no alternate Portal API\n"
    "route, no dual semantic publication, and no direct MCP/native fallback.\n"
    "The host does not use a central vendor switch or an arbitrary-English parser to\n"
    "recover a contribution, field state, or action meaning.",
    "Every rendered field is identified by its contribution identity, resource ID,\n"
    "field ID, exact SemReg field `DefinitionRef`, service `DefinitionRef`,\n"
    "capability `DefinitionRef`, and canonical-unit `DefinitionRef`. A B503 card\n"
    "can display only a field admitted through this chain. It must show the\n"
    "Gateway-supplied lifecycle, freshness, projection-loss, quality, and provenance\n"
    "state; it cannot reconstruct any of them from a label, a historical aggregate,\n"
    "or a raw MCP response.",
    "The `Vaillant B503` card is a contribution-driven section-projection card. It\n"
    "appears only for an admitted selected resource whose B503 capability state is\n"
    "`AVAILABLE`; it identifies the selected target and enters the B503 perspective\n"
    "without creating another B503 data model. Target selection is resource-scoped.\n"
    "Every target-bearing B503 read or session request uses only the main public\n"
    "`POST /graphql` endpoint. That endpoint is protected by the stable eBUS MCP\n"
    "graduation/parity contract. These operations are not `PortalCatalogV1` or\n"
    "`PortalActionInvokeV1` operations, and they do not call `/graphql/portal/v1`:",
    "The catalog/action route and the B503 route are an exclusive operation-to-route\n"
    "split, not a fallback or compatibility shim. The B503 route does not expand the\n"
    "accepted #974 catalog/action endpoint. If either fixed route is unavailable,\n"
    "the UI renders the Gateway-supplied unavailable state and does not try the\n"
    "other route, REST, MCP, or native I/O.",
)
MARKDOWN = MarkdownIt("commonmark")
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
        hidden = any(name.casefold() == "hidden" for name, _ in attrs)
        if self._inert_stack or normalized in NON_RENDERING_CONTAINERS or hidden:
            if normalized not in HTML_VOID_ELEMENTS:
                self._inert_stack.append(normalized)
            return
        self.parts.append(self.get_starttag_text())

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        hidden = any(name.casefold() == "hidden" for name, _ in attrs)
        if (
            not self._inert_stack
            and tag.casefold() not in NON_RENDERING_CONTAINERS
            and not hidden
        ):
            self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.casefold()
        if self._inert_stack:
            for index in range(len(self._inert_stack) - 1, -1, -1):
                if self._inert_stack[index] == normalized:
                    del self._inert_stack[index:]
                    return
            return
        self.parts.append(f"</{tag}>")

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


def _visible_prose_source(text: str) -> str:
    """Remove CommonMark fenced and indented code while preserving line boundaries."""
    lines = text.splitlines(keepends=True)
    for token in MARKDOWN.parse(text):
        if token.type not in {"fence", "code_block"} or token.map is None:
            continue
        for index in range(token.map[0], min(token.map[1], len(lines))):
            lines[index] = "\n" if lines[index].endswith("\n") else ""
    return "".join(lines)


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
    if attribute.casefold() in HTML_URL_ATTRIBUTE_NAMES:
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
    start = document.index(TARGET_START)
    end = document.index(TARGET_END, start)
    start_line = document.count("\n", 0, start)
    end_line = document.count("\n", 0, end)
    return [
        token
        for token in MARKDOWN.parse(document)
        if token.type == "inline"
        and token.map is not None
        and start_line <= token.map[0] < end_line
    ]


def _target_html_blocks(document: str) -> list[str]:
    start = document.index(TARGET_START)
    end = document.index(TARGET_END, start)
    start_line = document.count("\n", 0, start)
    end_line = document.count("\n", 0, end)
    return [
        token.content
        for token in MARKDOWN.parse(document)
        if token.type == "html_block"
        and token.map is not None
        and start_line <= token.map[0] < end_line
    ]


def _target_fenced_contents(document: str) -> list[str]:
    start = document.index(TARGET_START)
    end = document.index(TARGET_END, start)
    start_line = document.count("\n", 0, start)
    end_line = document.count("\n", 0, end)
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
        if codepoint == 0 or codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
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
        if value is not None and attribute.casefold() in HTML_URL_ATTRIBUTE_NAMES
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
    # REQUIRED is deliberately limited to the frozen INT-10 contract. Content
    # inside comments or declared non-rendering HTML containers is not part of
    # the visible public contract.
    rendered_target_source = _visible_contract_source(_visible_prose_source(target))
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
