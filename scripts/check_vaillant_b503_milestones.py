#!/usr/bin/env python3
"""Validate the bounded B503 live-monitor milestone contract."""
from __future__ import annotations

import pathlib
import re
import sys


DOC = pathlib.Path("protocols/vaillant/ebus-vaillant-B503.md")
MILESTONE_HEADING = "## 14. Companion Links (downstream code milestones)"
MILESTONE_TABLE_HEADER = ("Milestone", "Repo", "Artefact")
MARKDOWN_TABLE_DELIMITER_CELL = re.compile(r"^:?-{3,}:?$")
SESSION_SECTION_START = "## 6. Live-Monitor Session"
SESSION_SECTION_END = "## 7. Gateway Operational Contract"
REFRESHING_PUBLIC_SECTION_START = "#### 7.1.1 Refreshing session state (public)"
REFRESHING_PUBLIC_SECTION_END = "### 7.2 Quiesce timing bounds (normative)"
REFRESH_SECTION_START = "### 7.3 Retry and refresh"
REFRESH_SECTION_END = "### 7.4 Ownership release"
RECONNECT_SECTION_START = "### 7.5 Reconnect handling"
RECONNECT_SECTION_END = "### 7.6 30s idle-timeout semantics"
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
DISABLED_PUBLIC_MAPPING = (
    "**Stable public `Disabled` mapping:** `Disabled` with `owned:false` represents\n"
    "only an explicit operator or configuration disable. Enable failure, the 30s\n"
    "idle timeout, transport disconnect, and gateway restart may traverse the\n"
    "internal cleanup path through `DISABLED`, but their stable public session\n"
    "observation is `Idle` with `owned:false` after cleanup. `Disabled` is never\n"
    "reported with `owned:true`."
)
REFRESHING_CLEANUP_CONTRACT = (
    "When a locally token-owning consumer leaves a target or navigates away while\n"
    "its session is `Refreshing`, it MUST queue that target/token disable without\n"
    "invoking the busy operation. After successful refresh reaches `Active`, it\n"
    "dispatches the queued disable; after refresh failure reaches `Idle`, it clears\n"
    "the queued pair without a disable."
)
REFRESHING_UNKNOWN_STRIP_CONTRACT = (
    "During a held `Refreshing` epoch, the\n"
    "session strip remains observable alongside temporarily `UNKNOWN` capability,\n"
    "but it is status-only: no B503 card, tabs, or operations are admitted until\n"
    "capability returns `AVAILABLE`."
)
REFRESH_SUCCESS_CONTINUATION = (
    "On refresh success for a surviving authenticated current-owner handle →\n"
    "  revalidate that same token/target/epoch ownership and return to `Active`;\n"
    "  this is continuation, not reconstruction or auto-resume. On refresh failure\n"
    "  → release the ownership gate and return to `Idle`."
)
NO_AUTO_RESUME_RECONSTRUCTION = (
    "Gateway MUST NOT reconstruct or auto-resume a session after restart, a lost\n"
    "  owner handle, or an absent/invalid current issuer token; each requires an\n"
    "  explicit new client Enable. The surviving authenticated current-owner refresh\n"
    "  path in §7.3 is the only continuation allowed across an epoch advance."
)
REFRESH_FAILURE_DIAGRAM = "REFRESHING --> IDLE: refresh failure releases gate"
REFRESH_FAILURE_TRANSITION = (
    "| `REFRESHING` | refresh failure | `IDLE` | release ownership gate; "
    "surface the Gateway-supplied failure outcome |"
)
REFRESH_FAILURE_LOCK = "the direct `REFRESHING → IDLE` refresh-failure path"
FORBIDDEN_REFRESH_FAILURE_CONTRADICTIONS = (
    "REFRESHING --> DISABLED: refresh failure releases gate",
    "on entry to `DISABLED` from a\nheld-owner state",
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


def _is_markdown_table_delimiter(row: tuple[str, ...] | None) -> bool:
    return row is not None and len(row) == len(MILESTONE_TABLE_HEADER) and all(
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


def _require_exact_row(rows: tuple[tuple[str, ...], ...], expected: tuple[str, ...]) -> None:
    matching_id_rows = [row for row in rows if row[0] == expected[0]]
    if matching_id_rows != [expected]:
        raise CheckError(f"missing exact §14 B503 milestone row: {expected!r}")


def validate_text(text: str) -> None:
    session_section = _section(text, SESSION_SECTION_START, SESSION_SECTION_END)
    if SESSION_STATE_CONTRACT not in session_section:
        raise CheckError("missing five-state B503 session contract in §6.1")
    if DISABLED_PUBLIC_MAPPING not in session_section:
        raise CheckError("missing stable public Disabled mapping in §6")
    for fragment in (
        REFRESH_FAILURE_DIAGRAM,
        REFRESH_FAILURE_TRANSITION,
        REFRESH_FAILURE_LOCK,
    ):
        if fragment not in session_section:
            raise CheckError(
                f"missing coherent B503 Refreshing failure contract in §6.1: {fragment!r}"
            )
    for fragment in FORBIDDEN_REFRESH_FAILURE_CONTRADICTIONS:
        if fragment in session_section:
            raise CheckError(
                f"forbidden B503 Refreshing failure contradiction in §6.1: {fragment!r}"
            )
    for fragment in FORBIDDEN_SESSION_STATE_CLAUSES:
        if fragment in session_section:
            raise CheckError(f"forbidden §6 B503 session-state contradiction: {fragment!r}")

    refreshing_public_section = _section(
        text, REFRESHING_PUBLIC_SECTION_START, REFRESHING_PUBLIC_SECTION_END
    )
    for fragment in (REFRESHING_CLEANUP_CONTRACT, REFRESHING_UNKNOWN_STRIP_CONTRACT):
        if fragment not in refreshing_public_section:
            raise CheckError(
                f"missing public Refreshing consumer contract in §7.1.1: {fragment!r}"
            )

    refresh_section = _section(text, REFRESH_SECTION_START, REFRESH_SECTION_END)
    if REFRESH_SUCCESS_CONTINUATION not in refresh_section:
        raise CheckError("missing authenticated Refreshing continuation contract in §7.3")
    reconnect_section = _section(text, RECONNECT_SECTION_START, RECONNECT_SECTION_END)
    if NO_AUTO_RESUME_RECONSTRUCTION not in reconnect_section:
        raise CheckError("missing no-reconstruction boundary in §7.5")

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
