#!/usr/bin/env python3
"""Validate the bounded B503 live-monitor milestone contract."""
from __future__ import annotations

import pathlib
import sys


DOC = pathlib.Path("protocols/vaillant/ebus-vaillant-B503.md")
MILESTONE_HEADING = "## 14. Companion Links (downstream code milestones)"
MILESTONE_TABLE_HEADER = ("Milestone", "Repo", "Artefact")
SESSION_SECTION_START = "### 6.1 State machine (plan AD04)"
SESSION_SECTION_END = "### 6.2 Ownership key"
INSTALL_WRITE_SECTION_START = "## 9. Install-Writes Non-Exposure (v1 invariant)"
INSTALL_WRITE_SECTION_END = "## 10. F.xxx Decimal Caveat (LOCAL_CAPTURE only)"
M2B_GRAPHQL = (
    "`M2b_GATEWAY_GRAPHQL`",
    "`helianthus-ebusgateway`",
    "GraphQL diagnostic read-only parity + `vaillantCapabilities.b503` signal and "
    "five-state `vaillantLiveMonitor` session status (`Idle` / `Enabling` / "
    "`Active` / `Refreshing` / `Disabled`); only the bounded session "
    "enable/disable action through the §6 FSM",
)
M3_PORTAL = (
    "`M3_PORTAL`",
    "`helianthus-ebusgateway`",
    "Vaillant pane (errors / service / live-monitor diagnostic reads) plus "
    "Gateway-owned five-state live-monitor session strip (`Idle` / `Enabling` / "
    "`Active` / `Refreshing` / `Disabled`) and only the bounded session "
    "enable/disable action through the §6 FSM",
)
INSTALL_WRITE_NON_EXPOSURE = (
    "> **`02 01` and `02 02` MUST NOT be exposed on any public surface in v1.**"
)
SESSION_STATE_CONTRACT = (
    "five stable states: `Idle`, `Enabling`, `Active`, `Refreshing`, and `Disabled`.\n"
    "`Refreshing` means an epoch refresh holds the ownership gate and all\n"
    "live-monitor operations are busy. Refresh success returns `Active`; refresh\n"
    "failure releases the gate and returns `Idle`. `Disabled` is never reported with\n"
    "`owned:true`."
)
FORBIDDEN_SESSION_STATE_CLAUSES = (
    "`Refreshing` may accept live-monitor operations.",
    "`Disabled` may be reported with `owned:true`.",
)
FORBIDDEN_ALL_READ_ONLY_MILESTONES = (
    (
        "`M2b_GATEWAY_GRAPHQL`",
        "`helianthus-ebusgateway`",
        "GraphQL read-only parity + `vaillantCapabilities.b503` signal",
    ),
    (
        "`M3_PORTAL`",
        "`helianthus-ebusgateway`",
        "Vaillant pane (errors / service / live-monitor tabs, read-only)",
    ),
)


class CheckError(ValueError):
    """The canonical B503 milestone text contradicts the v1 session boundary."""


def _parse_table_row(line: str) -> tuple[str, ...] | None:
    if not line.startswith("|") or not line.endswith("|"):
        return None
    return tuple(cell.strip() for cell in line.strip("|").split("|"))


def _section(text: str, start_marker: str, end_marker: str) -> str:
    try:
        start = text.index(start_marker)
        end = text.index(end_marker, start)
    except ValueError as exc:
        raise CheckError(
            f"missing canonical B503 section boundary: {start_marker!r}"
        ) from exc
    return text[start:end]


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
    if separator_index >= len(lines) or _parse_table_row(lines[separator_index]) is None:
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


def _require_exact_row(rows: tuple[tuple[str, ...], ...], expected: tuple[str, ...]) -> None:
    matching_id_rows = [row for row in rows if row[0] == expected[0]]
    if matching_id_rows != [expected]:
        raise CheckError(f"missing exact §14 B503 milestone row: {expected!r}")


def validate_text(text: str) -> None:
    session_section = _section(text, SESSION_SECTION_START, SESSION_SECTION_END)
    if SESSION_STATE_CONTRACT not in session_section:
        raise CheckError("missing five-state B503 session contract in §6.1")
    for fragment in FORBIDDEN_SESSION_STATE_CLAUSES:
        if fragment in session_section:
            raise CheckError(f"forbidden §6 B503 session-state contradiction: {fragment!r}")

    rows = _milestone_table(text)
    for expected in (M2B_GRAPHQL, M3_PORTAL):
        _require_exact_row(rows, expected)
    for fragment in FORBIDDEN_ALL_READ_ONLY_MILESTONES:
        if fragment in rows:
            raise CheckError(f"forbidden all-read-only B503 milestone: {fragment!r}")
    install_write_section = _section(
        text, INSTALL_WRITE_SECTION_START, INSTALL_WRITE_SECTION_END
    )
    if INSTALL_WRITE_NON_EXPOSURE not in install_write_section:
        raise CheckError(
            f"missing required §9 B503 public non-exposure fragment: "
            f"{INSTALL_WRITE_NON_EXPOSURE!r}"
        )


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
