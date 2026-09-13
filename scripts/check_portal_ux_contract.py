#!/usr/bin/env python3
"""Validate the public INT-10 Portal and Vaillant B503 target contract."""
from __future__ import annotations

import pathlib
import sys


DOC = pathlib.Path("api/portal.md")

REQUIRED = (
    "## Contribution-Driven Portal Contract V1 (INT-10 Target)",
    "Gateway #552 is open;",
    "`helianthus.gateway.portal-catalog/v1`",
    "`POST /graphql/portal/v1`",
    "`PortalCatalogV1`",
    "`PortalActionInvokeV1`",
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
    "`vaillantServiceHistory(targetAddress:index:)`",
    "`vaillantLiveMonitor(action:issuerToken:targetAddress:)`",
    "`M8-TGT-01`, `M8-TGT-02`, `M8-TGT-03`, and `M8-TGT-04`",
    "`EXPIRED` is\ninternal-only",
    'data-testid="b503-state-available"',
    'data-testid="b503-state-not-supported"',
    'data-testid="b503-state-transport-down"',
    'data-testid="b503-state-session-busy"',
    'data-testid="b503-state-unknown"',
    'data-testid="b503-session-strip"',
    'data-testid="b503-session-state-label"',
    'data-testid="b503-session-owned-by-other"',
    '`Idle`, `Enabling`, `Active`, and\n`Disabled`',
    'data-role="vaillant-b503-tab-history"',
    'data-role="projection-b503-card"',
    'data-testid="b503-install-writes-banner"',
    'id="b503-ad02-tooltip-anchor"',
    "real installation/device write still needs action-time operator confirmation.",
    "scripts/check_portal_ux_contract.py",
)

FORBIDDEN = (
    "/portal/api/v1/b503",
    "Gateway #552 is implemented",
    "Gateway #552 has been implemented",
    "Gateway #552 is complete",
)


class CheckError(ValueError):
    """The public Portal contract is missing a required safety boundary."""


def validate_text(text: str) -> None:
    for fragment in REQUIRED:
        if fragment not in text:
            raise CheckError(f"api/portal.md: missing required contract fragment: {fragment!r}")
    for fragment in FORBIDDEN:
        if fragment in text:
            raise CheckError(f"api/portal.md: forbidden stale or premature wording: {fragment!r}")


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
