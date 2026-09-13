#!/usr/bin/env python3
"""Validate the bounded B503 live-monitor milestone contract."""
from __future__ import annotations

import pathlib
import sys


DOC = pathlib.Path("protocols/vaillant/ebus-vaillant-B503.md")
M2B_GRAPHQL = (
    "| `M2b_GATEWAY_GRAPHQL` | `helianthus-ebusgateway` | GraphQL diagnostic "
    "read-only parity + `vaillantCapabilities.b503` signal; only the bounded "
    "`vaillantLiveMonitor` session enable/disable action through the §6 FSM |"
)
M3_PORTAL = (
    "| `M3_PORTAL` | `helianthus-ebusgateway` | Vaillant pane (errors / service "
    "/ live-monitor diagnostic reads) plus Gateway-owned live-monitor session strip "
    "and only the bounded session enable/disable action through the §6 FSM |"
)
INSTALL_WRITE_NON_EXPOSURE = (
    "> **`02 01` and `02 02` MUST NOT be exposed on any public surface in v1.**"
)
FORBIDDEN_ALL_READ_ONLY_MILESTONES = (
    "| `M2b_GATEWAY_GRAPHQL` | `helianthus-ebusgateway` | GraphQL read-only parity "
    "+ `vaillantCapabilities.b503` signal |",
    "| `M3_PORTAL` | `helianthus-ebusgateway` | Vaillant pane (errors / service "
    "/ live-monitor tabs, read-only) |",
)


class CheckError(ValueError):
    """The canonical B503 milestone text contradicts the v1 session boundary."""


def validate_text(text: str) -> None:
    for fragment in (M2B_GRAPHQL, M3_PORTAL, INSTALL_WRITE_NON_EXPOSURE):
        if fragment not in text:
            raise CheckError(f"missing required B503 milestone fragment: {fragment!r}")
    for fragment in FORBIDDEN_ALL_READ_ONLY_MILESTONES:
        if fragment in text:
            raise CheckError(f"forbidden all-read-only B503 milestone: {fragment!r}")


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
