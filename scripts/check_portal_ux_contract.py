#!/usr/bin/env python3
"""Validate the public INT-10 Portal and Vaillant B503 target contract."""
from __future__ import annotations

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
B503_RECONNECT_ERROR = (
    "On a B503 GraphQL error or transport reconnect, the browser renders only the\n"
    "Gateway-supplied error or availability state. It neither preserves\n"
    "`AVAILABLE`, replays a session enable/disable action, nor changes route; it\n"
    "may re-query only the selected target after Gateway publishes a new state."
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
    B503_RECONNECT_ERROR,
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
DOM_ATTRIBUTE_REFERENCE = re.compile(
    r"\b([A-Za-z_:][A-Za-z0-9_:.-]*)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s`>]+))",
    re.IGNORECASE,
)
DOM_SELECTOR_TOKEN = re.compile(
    r"(?<![0-9a-f])(?:0x)?02[\s_:-]*0[12](?![0-9a-f])", re.IGNORECASE
)
DOM_COMMAND_TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


class CheckError(ValueError):
    """The public Portal contract is missing a required safety boundary."""


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
    if normalized.startswith("0x"):
        normalized = normalized[2:]
    if re.fullmatch(r"[0-9a-f]+", normalized):
        return normalized
    return None


def _reject_prohibited_dom_references(target: str) -> None:
    for match in DOM_ATTRIBUTE_REFERENCE.finditer(target):
        attribute = match.group(1)
        value = next(group for group in match.groups()[1:] if group is not None)
        for selector_match in DOM_SELECTOR_TOKEN.finditer(value):
            normalized = _normalized_hex_selector(selector_match.group(0))
            if normalized in FORBIDDEN_INSTALLATION_SELECTORS:
                raise CheckError(
                    "api/portal.md: prohibited B503 installation selector in DOM attribute "
                    f"reference: {attribute}={value!r}"
                )
        command_tokens = {
            token.lower() for token in DOM_COMMAND_TOKEN.findall(value)
        }
        prohibited_commands = command_tokens & FORBIDDEN_B503_DOM_COMMAND_TOKENS
        if prohibited_commands:
            raise CheckError(
                "api/portal.md: prohibited B503 command token in DOM attribute "
                f"reference: {attribute}={value!r}"
            )


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
