from __future__ import annotations

import importlib.util
import pathlib

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "vaillant_b503_milestones", ROOT / "scripts/check_vaillant_b503_milestones.py"
)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def contract() -> str:
    return (ROOT / "protocols/vaillant/ebus-vaillant-B503.md").read_text(encoding="utf-8")


def table_row(cells: tuple[str, ...]) -> str:
    return f"| {' | '.join(cells)} |"


def test_accepts_current_b503_milestone_contract() -> None:
    CHECKER.validate_text(contract())


def test_rejects_five_state_contract_hidden_in_html_comment() -> None:
    text = contract().replace(
        CHECKER.SESSION_STATE_CONTRACT,
        f"<!-- {CHECKER.SESSION_STATE_CONTRACT} -->",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_five_state_contract_hidden_in_fenced_code() -> None:
    text = contract().replace(
        CHECKER.SESSION_STATE_CONTRACT,
        f"```text\n{CHECKER.SESSION_STATE_CONTRACT}\n```",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_five_state_contract_stored_only_in_html_attribute() -> None:
    text = contract().replace(
        CHECKER.SESSION_STATE_CONTRACT,
        f'<div data-contract="{CHECKER.SESSION_STATE_CONTRACT}"></div>',
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_five_state_contract_stored_only_in_markdown_link_title() -> None:
    text = contract().replace(
        CHECKER.SESSION_STATE_CONTRACT,
        f'[status](./contract "{CHECKER.SESSION_STATE_CONTRACT}")',
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_five_state_contract_stored_only_in_markdown_image_alt() -> None:
    text = contract().replace(
        CHECKER.SESSION_STATE_CONTRACT,
        f"![{CHECKER.SESSION_STATE_CONTRACT}](contract.png)",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize("container", sorted(CHECKER.NON_RENDERING_CONTAINERS))
def test_rejects_five_state_contract_hidden_in_inert_html(container: str) -> None:
    text = contract().replace(
        CHECKER.SESSION_STATE_CONTRACT,
        f"<{container}>{CHECKER.SESSION_STATE_CONTRACT}</{container}>",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_accepts_five_state_contract_in_visible_html() -> None:
    text = contract().replace(
        CHECKER.SESSION_STATE_CONTRACT,
        f"<div>{CHECKER.SESSION_STATE_CONTRACT}</div>",
        1,
    )
    CHECKER.validate_text(text)


@pytest.mark.parametrize("container", ("details", "dialog"))
def test_closed_disclosure_cannot_supply_five_state_contract(container: str) -> None:
    text = contract().replace(
        CHECKER.SESSION_STATE_CONTRACT,
        f"<{container}>{CHECKER.SESSION_STATE_CONTRACT}</{container}>",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize("container", ("details", "dialog"))
def test_open_disclosure_can_supply_five_state_contract(container: str) -> None:
    text = contract().replace(
        CHECKER.SESSION_STATE_CONTRACT,
        f"<{container} open>{CHECKER.SESSION_STATE_CONTRACT}</{container}>",
        1,
    )
    CHECKER.validate_text(text)


def test_rejects_five_state_contract_hidden_by_standard_html_attribute() -> None:
    text = contract().replace(
        CHECKER.SESSION_STATE_CONTRACT,
        f"<div hidden>{CHECKER.SESSION_STATE_CONTRACT}</div>",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "style",
    (
        "display:none",
        "DISPLAY: none",
        "visibility: hidden",
        "display:none!important",
        "display: none !IMPORTANT",
        "visibility:hidden !important",
        "display:none!important;display:block",
        "display:block;display:none!important",
        "visibility:hidden!important;visibility:visible",
    ),
)
def test_rejects_five_state_contract_hidden_by_inline_style(style: str) -> None:
    text = contract().replace(
        CHECKER.SESSION_STATE_CONTRACT,
        f'<div style="{style}">{CHECKER.SESSION_STATE_CONTRACT}</div>',
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "style",
    ("display:none;display:block!important", "display:none!important;display:block!important"),
)
def test_accepts_later_important_visible_inline_style(style: str) -> None:
    text = contract().replace(
        CHECKER.SESSION_STATE_CONTRACT,
        f'<div style="{style}">{CHECKER.SESSION_STATE_CONTRACT}</div>',
        1,
    )
    CHECKER.validate_text(text)


def test_rejects_five_state_contract_stored_in_svg_metadata() -> None:
    text = contract().replace(
        CHECKER.SESSION_STATE_CONTRACT,
        f"<svg><desc>{CHECKER.SESSION_STATE_CONTRACT}</desc><text>status</text></svg>",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_missing_current_capability_table_authority() -> None:
    text = contract().replace(
        CHECKER.CURRENT_CAPABILITY_TABLE_AUTHORITY,
        "The archived plan AD18 entry is canonical and wins on conflict.",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize("clause", CHECKER.FORBIDDEN_PLAN_CONFLICT_AUTHORITY)
def test_rejects_archived_plan_conflict_authority(clause: str) -> None:
    text = contract().replace(
        CHECKER.CAPABILITY_TRUTH_TABLE_SECTION_END,
        f"{clause}.\n\n{CHECKER.CAPABILITY_TRUTH_TABLE_SECTION_END}",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    ("current", "unsafe"),
    (
        (
            CHECKER.REFRESH_FAILURE_CAPABILITY_PRECEDENCE,
            "- On refresh revealing `TRANSPORT_DOWN` or `UNKNOWN` → surface that value literally.",
        ),
        (
            CHECKER.CLEANUP_SCOPED_TRANSPORT_DOWN_FORBIDDEN,
            "- silent fallback to `UNKNOWN` once `TRANSPORT_DOWN` is knowable.",
        ),
    ),
)
def test_rejects_cleanup_unaware_transport_down_precedence(
    current: str, unsafe: str
) -> None:
    text = contract().replace(current, unsafe, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    ("current", "unsafe"),
    (
        (
            CHECKER.COLD_BOOT_TRUTH_ROW,
            ("1", "cold-boot, no successful dispatch yet", "`AVAILABLE`", "n/a"),
        ),
        (
            CHECKER.DISCONNECT_ACTIVE_TRUTH_ROW,
            (
                "3",
                "disconnect during ACTIVE session",
                "`TRANSPORT_DOWN` (literal)",
                "in-flight requests fail `TRANSPORT_DOWN`; no late mutation",
            ),
        ),
        (
            CHECKER.RECONNECT_PRE_DISPATCH_TRUTH_ROW,
            (
                "4",
                "reconnect, before first post-reconnect dispatch",
                "`AVAILABLE`",
                "retain the pre-disconnect state",
            ),
        ),
        (
            CHECKER.STALE_EPOCH_COMPLETION_TRUTH_ROW,
            (
                "8",
                "stale in-flight completion across epoch rollover",
                "`AVAILABLE`",
                "epoch-N reply may satisfy a post-reconnect waiter",
            ),
        ),
    ),
)
def test_rejects_unsafe_unchecked_capability_truth_rows(
    current: tuple[str, ...], unsafe: tuple[str, ...]
) -> None:
    text = contract().replace(table_row(current), table_row(unsafe), 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_cleanup_unaware_dispatch_failure_truth_row() -> None:
    text = contract().replace(
        table_row(CHECKER.DISPATCH_FAILURE_TRUTH_ROW),
        "| 6 | timeout/NAK/CRC during dispatch | `UPSTREAM_RPC_FAILED` to caller; capability stays last-known | n/a |",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    ("current", "unsafe"),
    (
        (
            CHECKER.STEADY_AVAILABLE_TRUTH_ROW,
            ("2", "post-first-success steady state", "`AVAILABLE`", "n/a"),
        ),
        (
            CHECKER.RECONNECT_AVAILABLE_TRUTH_ROW,
            (
                "5",
                "reconnect, post-first-success-after-reconnect",
                "`AVAILABLE`",
                "n/a",
            ),
        ),
    ),
)
def test_rejects_available_before_restart_fence_clearance(
    current: tuple[str, ...], unsafe: tuple[str, ...]
) -> None:
    text = contract().replace(table_row(current), table_row(unsafe), 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_old_all_read_only_milestone_contradiction() -> None:
    text = contract().replace(
        table_row(CHECKER.M2B_GRAPHQL),
        table_row(CHECKER.FORBIDDEN_ALL_READ_ONLY_MILESTONES[0]),
        1,
    ).replace(
        table_row(CHECKER.M3_PORTAL),
        table_row(CHECKER.FORBIDDEN_ALL_READ_ONLY_MILESTONES[1]),
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_missing_install_write_non_exposure() -> None:
    text = contract().replace(CHECKER.INSTALL_WRITE_NON_EXPOSURE, "", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_install_write_non_exposure_copied_outside_normative_section() -> None:
    text = contract().replace(CHECKER.INSTALL_WRITE_NON_EXPOSURE, "", 1)
    text += f"\n{CHECKER.INSTALL_WRITE_NON_EXPOSURE}\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "clause",
    (
        "The public GraphQL surface MAY expose `02 01` and `02 02`.",
        "The public surface CAN publish `02 01` or `02 02`.",
        "The public GraphQL surface MAY expose 02 01.",
        "The Portal surface CAN offer 02 02.",
        "Home Assistant MAY expose 02 01.",
        "HA services CAN publish 02 02.",
        "The public API MAY expose 02 01.",
        "The public GraphQL mutation MAY expose 02 01.",
        "MCP tools MAY expose 02 02.",
        "Portal controls MAY expose 02 01.",
        "Portal SHOULD expose 02 01.",
        "The public GraphQL surface SHALL publish 02 02.",
        "Home Assistant WILL offer 02 01.",
        "Portal MUST expose 0x02 0x01.",
        "Portal MUST expose 0202.",
        "GraphQL MUST expose selector 02-01.",
        "MCP SHOULD publish selector `02/02`.",
        "`02 01` SHOULD be exposed by Portal.",
        "0202 SHALL be published by the public GraphQL surface.",
        "selector 02-01 WILL be offered by Home Assistant.",
        "Portal MUST make selector 02 01 available.",
        "GraphQL SHALL surface 0202.",
        "MCP MUST provide a control for 02-02.",
        "`02 01` SHOULD be made available through Portal.",
        "0202 WILL be supported by Home Assistant.",
        "Portal permits exposing 02 01.",
    ),
)
def test_rejects_affirmative_install_write_exposure_inside_normative_section(
    clause: str,
) -> None:
    text = contract().replace(
        CHECKER.INSTALL_WRITE_SECTION_END,
        f"{clause}\n\n{CHECKER.INSTALL_WRITE_SECTION_END}",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "clause",
    (
        "The public GraphQL surface MUST NOT expose `02 01` and `02 02`.",
        "`02 01` MUST NOT be exposed by Portal.",
    ),
)
def test_rejects_duplicate_noncanonical_install_write_clause(clause: str) -> None:
    text = contract().replace(
        CHECKER.INSTALL_WRITE_SECTION_END,
        f"{clause}\n\n{CHECKER.INSTALL_WRITE_SECTION_END}",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        (
            "`UNKNOWN` (temporary during refresh; remains `UNKNOWN` after any triggering DISABLE)",
            "`AVAILABLE`",
        ),
        (
            "only `vaillantCapabilities` and `vaillantLiveMonitorSession` status queries remain admitted",
            "no status query remains admitted",
        ),
        (
            "retain fail-closed cleanup, and admit no Enable",
            "clears cleanup and admits Enable",
        ),
    ),
)
def test_rejects_refresh_truth_row_without_unknown_capability_or_status_only_admission(
    old: str, new: str
) -> None:
    text = contract().replace(old, new, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "replacement",
    (
        "four stable states: `Idle`, `Enabling`, `Active`, and `Disabled`.",
        "`Disabled` may be reported with `owned:true`.",
    ),
)
def test_rejects_missing_refreshing_or_disabled_ownership_contract(
    replacement: str,
) -> None:
    text = contract().replace(CHECKER.SESSION_STATE_CONTRACT, replacement, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_ambiguous_refreshed_disable_failure_layering() -> None:
    precise = CHECKER.REFRESH_DISABLE_TRANSITION
    ambiguous = precise.replace(
        "retain `(targetAddress, fresh gatewayCleanupAttemptID, transportEpoch[N+1])` "
        "as process-local cleanup, publish `UNKNOWN`, and admit no Enable",
        "clear cleanup and admit Enable",
    )
    assert ambiguous != precise
    text = contract().replace(precise, ambiguous, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize("clause", CHECKER.FORBIDDEN_SESSION_STATE_CLAUSES)
def test_rejects_session_state_contradiction_inside_normative_section(
    clause: str,
) -> None:
    text = contract().replace(
        CHECKER.SESSION_SECTION_END,
        f"{clause}\n\n{CHECKER.SESSION_SECTION_END}",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    ("section_end", "clause"),
    (
        (
            CHECKER.REFRESHING_PUBLIC_SECTION_END,
            "`Refreshing` accepts live-monitor operations.",
        ),
        (
            CHECKER.NORMALIZATION_SECTION_END,
            "`Disabled` is reported with `owned:true`.",
        ),
    ),
)
def test_rejects_session_state_contradiction_outside_section_six(
    section_end: str, clause: str
) -> None:
    text = contract().replace(section_end, f"{clause}\n\n{section_end}", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_missing_current_public_session_authority_in_status_section() -> None:
    text = contract().replace(
        CHECKER.CURRENT_PUBLIC_SESSION_AUTHORITY,
        "The amendment-1 plan remains authority for every public FSM.",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "replacement",
    (
        "The old session key remains authoritative after an epoch advance.",
        "Gateway silently changes the epoch without fencing old completions.",
        "If refresh fails, no rebound key is installed and the owner is released "
        "to `IDLE`.",
    ),
)
def test_rejects_missing_atomic_owner_key_epoch_rebinding(replacement: str) -> None:
    text = contract().replace(CHECKER.REFRESH_OWNER_REBINDING, replacement, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    ("clause", "replacement"),
    (
        (
            CHECKER.OWNER_CONDITIONAL_MUTEX_SCOPE,
            "All cleanup obligations are no-ops after the owner is released.",
        ),
        (
            CHECKER.DISABLED_PUBLIC_MAPPING,
            "Disabled maps all cleanup outcomes without a public distinction.",
        ),
        (
            CHECKER.REFRESHING_CLEANUP_CONTRACT,
            "Refreshing ownership needs no queued cleanup.",
        ),
        (
            CHECKER.REFRESHING_UNKNOWN_STRIP_CONTRACT,
            "Unknown capability hides the session strip.",
        ),
        (
            CHECKER.ACTIVE_UNKNOWN_OWNER_CONTRACT,
            "UNKNOWN capability hides every Active session control.",
        ),
        (
            CHECKER.REFRESH_SUCCESS_CONTINUATION,
            "Refresh success always reconstructs an Active session.",
        ),
        (
            CHECKER.NO_AUTO_RESUME_RECONSTRUCTION,
            "Every reconnect resumes without an explicit Enable.",
        ),
        (
            CHECKER.REFRESHING_DISCONNECT_FENCE,
            "A later reconnect enters Refreshing after every transport disconnect.",
        ),
        (
            CHECKER.DISCONNECT_CLEANUP_OBLIGATION,
            "Transport disconnect drops every pending cleanup obligation.",
        ),
        (
            CHECKER.DISCONNECT_CLEANUP_MUTEX_INDEPENDENCE,
            "No-owner disconnect discards pending defensive cleanup, while restart retains it.",
        ),
        (
            CHECKER.UNCONFIRMED_CLEANUP_OBLIGATION,
            "Any terminal defensive-disable outcome clears cleanup.",
        ),
        (
            CHECKER.GATEWAY_CLEANUP_ATTEMPT_ID,
            "Gateway reuses the browser-local cleanup identity.",
        ),
        (
            CHECKER.RESTART_RELEASE_CONTRACT,
            "Gateway restart discards cleanup and immediately publishes AVAILABLE.",
        ),
        (
            CHECKER.RESTART_CLEANUP_FENCE,
            "Gateway restart performs no target cleanup before B503 availability.",
        ),
        (
            CHECKER.RESTART_CLEANUP_FENCE,
            "Gateway automatically disables every qualified B503 target after restart.",
        ),
    ),
)
def test_rejects_missing_disabled_mapping_or_refreshing_consumer_contract(
    clause: str, replacement: str
) -> None:
    text = contract().replace(clause, replacement, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_available_prerequisite_for_post_refresh_owner_controls() -> None:
    replacement = CHECKER.REFRESHING_UNKNOWN_STRIP_CONTRACT.replace(
        "resumes immediately\nunder `UNKNOWN`; it does not wait for `AVAILABLE`",
        "remains blocked until capability returns `AVAILABLE`",
    )
    assert replacement != CHECKER.REFRESHING_UNKNOWN_STRIP_CONTRACT
    text = contract().replace(CHECKER.REFRESHING_UNKNOWN_STRIP_CONTRACT, replacement, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        (
            CHECKER.ACTIVE_READ_TRANSITION,
            "| `ACTIVE` | read request | `ACTIVE` | reset idle timer |",
        ),
        (
            CHECKER.ACTIVE_READ_FAILURE_TRANSITION,
            CHECKER.ACTIVE_READ_FAILURE_TRANSITION.replace(
                "do not reset the idle timer",
                "reset the idle timer",
            ),
        ),
    ),
)
def test_rejects_idle_timer_reset_before_success(old: str, new: str) -> None:
    text = contract().replace(old, new, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_idle_timeout_suppressed_by_failed_read_requests() -> None:
    unsafe = CHECKER.IDLE_TIMEOUT_TRIGGER_CONTRACT.replace(
        "without a successful read", "without a read request"
    )
    text = contract().replace(CHECKER.IDLE_TIMEOUT_TRIGGER_CONTRACT, unsafe, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_ambiguous_configuration_disabled_restart_mapping() -> None:
    text = contract().replace(
        "A still-effective\nout-of-band disabled condition takes precedence across Gateway restart",
        "Gateway restart always presents Idle even when a configuration disable remains effective",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        (
            CHECKER.ENABLE_ADMISSION_OPERATION,
            "| ENABLE | none (new claim) | succeeds iff FSM is `IDLE` |",
        ),
        (
            CHECKER.IDLE_ENABLE_TRANSITION,
            "| `IDLE` | enable request, no owner | `ENABLING` | emit enable frame |",
        ),
        (
            CHECKER.IDLE_ENABLE_REJECT_TRANSITION,
            "| `IDLE` | transport disconnected | `ENABLING` | try enable anyway |",
        ),
    ),
)
def test_rejects_enable_without_connected_available_admission(old: str, new: str) -> None:
    text = contract().replace(old, new, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "transition",
    (
        CHECKER.EXPLICIT_DISABLE_PRE_EMISSION_DISCONNECT_TRANSITION,
        CHECKER.REFRESH_DISABLE_PRE_EMISSION_DISCONNECT_TRANSITION,
    ),
)
def test_rejects_disable_emission_or_retry_after_pre_emission_disconnect(
    transition: str,
) -> None:
    for unsafe in (
        transition.replace("emit no disable frame", "emit disable exactly once"),
        transition.replace("perform no reconnect retry", "retry after reconnect"),
    ):
        text = contract().replace(transition, unsafe, 1)
        with pytest.raises(CHECKER.CheckError):
            CHECKER.validate_text(text)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        (
            CHECKER.EXPLICIT_DISABLE_CONFIRMED_TRANSITION,
            CHECKER.EXPLICIT_DISABLE_CONFIRMED_TRANSITION.replace(
                "this session action never produces public `Disabled`",
                "this session action produces public `Disabled`",
            ),
        ),
        (
            CHECKER.ADMIN_DISABLED_TRANSITION,
            CHECKER.ADMIN_DISABLED_TRANSITION.replace(
                "this condition is distinct from the current-owner session DISABLE action",
                "this condition is the current-owner session DISABLE action",
            ),
        ),
    ),
)
def test_rejects_conflated_session_and_administrative_disable(old: str, new: str) -> None:
    text = contract().replace(old, new, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    ("section_end", "clause"),
    (
        (
            CHECKER.SESSION_SECTION_END,
            "Gateway automatically emits a B503 disable after every process restart.",
        ),
        (
            CHECKER.RECONNECT_SECTION_END,
            "After restart, Gateway automatically dispatches a B503 enable.",
        ),
        (
            CHECKER.NORMALIZATION_SECTION_END,
            "Gateway automatically emits a B503 disable after every process restart.",
        ),
    ),
)
def test_rejects_automatic_b503_write_after_restart(
    section_end: str, clause: str
) -> None:
    text = contract().replace(
        section_end,
        f"{clause}\n\n{section_end}",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_operator_authorized_target_specific_restart_recovery() -> None:
    text = contract().replace(
        CHECKER.RECONNECT_SECTION_END,
        "After restart, separately operator-authorized target-specific recovery "
        "may emit one B503 disable.\n\n"
        f"{CHECKER.RECONNECT_SECTION_END}",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_additional_ack_to_disabled_transition() -> None:
    contradictory = (
        "| `ENABLING` | ACK after enable-frame emission | `DISABLED` | "
        "retain cleanup and admit no Enable |"
    )
    text = contract().replace(
        CHECKER.SESSION_TRANSITION_TABLE_END,
        f"{contradictory}\n\n{CHECKER.SESSION_TRANSITION_TABLE_END}",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "contradictory",
    (
        "A valid disable ACK proves session settlement and clears cleanup.",
        "An enable NAK proves that no native session exists and admits Enable.",
    ),
)
def test_rejects_additive_ack_or_nak_settlement_contradiction(
    contradictory: str,
) -> None:
    text = contract().replace(
        CHECKER.SESSION_SECTION_END,
        f"{contradictory}\n\n{CHECKER.SESSION_SECTION_END}",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        (
            CHECKER.IDLE_TIMEOUT_ACK_CONTRACT,
            "Idle timeout always keeps capability AVAILABLE and admits Enable.",
        ),
        (
            CHECKER.NORMALIZED_REFRESH_DISABLE_CONTRACT,
            "A refreshed DISABLE always completes cleanup to Idle.",
        ),
    ),
)
def test_rejects_missing_valid_ack_cleanup_in_later_normative_sections(
    old: str, new: str
) -> None:
    text = contract().replace(old, new, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "unsafe_settlement",
    (
        "A valid disable ACK proves settlement and clears cleanup.",
        "An enable NAK proves that no native session exists and admits Enable.",
    ),
)
def test_rejects_ack_or_nak_as_session_settlement(
    unsafe_settlement: str,
) -> None:
    text = contract().replace(
        CHECKER.CONFIRMED_CLEANUP_DEFINITION,
        unsafe_settlement,
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_refresh_failure_capability_other_than_unknown() -> None:
    current = contract()
    old = CHECKER.REFRESH_FAILURE_CAPABILITY_PRECEDENCE
    assert old in current
    text = current.replace(
        old,
        "On refresh failure, publish `TRANSPORT_DOWN` and admit Enable.",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_terminal_outcome_as_reconnect_settlement() -> None:
    replacement = CHECKER.REFRESHING_DISCONNECT_FENCE.replace(
        "and waits for a future accepted settlement contract.",
        "and treats any terminal cleanup result as settlement.",
    )
    assert replacement != CHECKER.REFRESHING_DISCONNECT_FENCE
    text = contract().replace(CHECKER.REFRESHING_DISCONNECT_FENCE, replacement, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_transport_down_as_reconnect_cleanup_capability() -> None:
    replacement = CHECKER.REFRESHING_DISCONNECT_FENCE.replace(
        "publishes `UNKNOWN`",
        "publishes `TRANSPORT_DOWN`",
    )
    assert replacement != CHECKER.REFRESHING_DISCONNECT_FENCE
    text = contract().replace(CHECKER.REFRESHING_DISCONNECT_FENCE, replacement, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_capability_truth_table_hidden_in_fenced_code() -> None:
    table = "\n".join(
        (
            table_row(CHECKER.CAPABILITY_TRUTH_TABLE_HEADER),
            "|---|---|---|---|",
            *(table_row(row) for row in CHECKER.CAPABILITY_TRUTH_ROWS),
        )
    )
    text = contract().replace(table, f"```text\n{table}\n```", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_capability_truth_table_wrapped_in_preformatted_html() -> None:
    table = "\n".join(
        (
            table_row(CHECKER.CAPABILITY_TRUTH_TABLE_HEADER),
            "|---|---|---|---|",
            *(table_row(row) for row in CHECKER.CAPABILITY_TRUTH_ROWS),
        )
    )
    text = contract().replace(table, f"<pre>\n{table}\n</pre>", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "container", ("audio", "canvas", "iframe", "noscript", "object", "video")
)
def test_rejects_capability_truth_table_stored_as_html_fallback(
    container: str,
) -> None:
    table = "\n".join(
        (
            table_row(CHECKER.CAPABILITY_TRUTH_TABLE_HEADER),
            "|---|---|---|---|",
            *(table_row(row) for row in CHECKER.CAPABILITY_TRUTH_ROWS),
        )
    )
    text = contract().replace(table, f"<{container}>\n{table}\n</{container}>", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_milestone_table_hidden_in_fenced_code() -> None:
    current = contract()
    table = "\n".join(
        (
            table_row(CHECKER.MILESTONE_TABLE_HEADER),
            "|---|---|---|",
            *(table_row(row) for row in CHECKER._milestone_table(current)),
        )
    )
    assert table in current
    text = current.replace(table, f"```text\n{table}\n```", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_milestone_table_wrapped_in_preformatted_html() -> None:
    current = contract()
    table = "\n".join(
        (
            table_row(CHECKER.MILESTONE_TABLE_HEADER),
            "|---|---|---|",
            *(table_row(row) for row in CHECKER._milestone_table(current)),
        )
    )
    assert table in current
    text = current.replace(table, f"<pre>\n{table}\n</pre>", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "container", ("audio", "canvas", "iframe", "noscript", "object", "video")
)
def test_rejects_milestone_table_stored_as_html_fallback(container: str) -> None:
    current = contract()
    table = "\n".join(
        (
            table_row(CHECKER.MILESTONE_TABLE_HEADER),
            "|---|---|---|",
            *(table_row(row) for row in CHECKER._milestone_table(current)),
        )
    )
    assert table in current
    text = current.replace(table, f"<{container}>\n{table}\n</{container}>", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        (
            CHECKER.IDLE_DISCONNECT_TRANSITION,
            "| `IDLE` | transport disconnect | `DISABLED` | wait for reconnect |",
        ),
        (
            CHECKER.DISABLED_DISCONNECT_TRANSITION,
            "| `DISABLED` | transport reconnect | `IDLE` | clear cleanup and admit Enable |",
        ),
    ),
)
def test_rejects_unbounded_disconnect_reconnect_state_change(old: str, new: str) -> None:
    text = contract().replace(old, new, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_install_write_contract_hidden_in_fenced_code() -> None:
    text = contract().replace(
        CHECKER.INSTALL_WRITE_SECTION,
        f"```text\n{CHECKER.INSTALL_WRITE_SECTION}\n```",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        (
            CHECKER.REFRESH_FAILURE_DIAGRAM,
            "REFRESHING --> DISABLED: refresh failure releases gate",
        ),
        (
            CHECKER.HELD_OWNER_DISABLED_RELEASE,
            "on entry to `DISABLED` from `ENABLING` or `ACTIVE`",
        ),
        (
            CHECKER.REFRESH_READ_DIAGRAM,
            "REFRESHING --> ACTIVE: refresh succeeds; request outcome unspecified",
        ),
        (
            CHECKER.REFRESH_DISABLE_DIAGRAM,
            "REFRESHING --> ACTIVE: refresh succeeds; triggering DISABLE once",
        ),
        (
            CHECKER.REFRESH_READ_TRANSITION,
            "| `REFRESHING` | refresh succeeds | `ACTIVE` | retry budget consumed |",
        ),
        (
            CHECKER.REFRESH_DISABLE_TRANSITION,
            "| `REFRESHING` | refresh succeeds for DISABLE | `ACTIVE` | dispatch disable |",
        ),
        (
            CHECKER.REFRESH_DISABLE_UNCONFIRMED_TRANSITION,
            "| `REFRESHING` | disable outcome ambiguous | `IDLE` | release slot |",
        ),
        (
            CHECKER.UNCONFIRMED_CLEANUP_TRANSITION,
            "| `DISABLED` | cleanup times out | `IDLE` | admit Enable |",
        ),
        (
            CHECKER.CONFIRMED_CLEANUP_TRANSITION,
            "| `DISABLED` | any terminal result | `IDLE` | clear cleanup |",
        ),
        (
            CHECKER.UNCONFIRMED_CLEANUP_DIAGRAM,
            "DISABLED --> IDLE: cleanup lacks valid disable ACK",
        ),
        (
            CHECKER.CONFIRMED_CLEANUP_DIAGRAM,
            "DISABLED --> IDLE: any terminal cleanup outcome",
        ),
        (
            CHECKER.CONFIRMED_CLEANUP_DEFINITION,
            "Any terminal disable outcome clears cleanup.",
        ),
        (
            CHECKER.EXPLICIT_DISABLE_CONFIRMED_TRANSITION,
            "| `ACTIVE` | explicit disable | `IDLE` | return any outcome |",
        ),
        (
            CHECKER.EXPLICIT_DISABLE_UNCONFIRMED_TRANSITION,
            "| `ACTIVE` | explicit disable failure | `IDLE` | admit Enable |",
        ),
        (
            CHECKER.DISCONNECT_TRANSITION,
            CHECKER.DISCONNECT_TRANSITION.replace(
                "publish `UNKNOWN`, and perform no automatic reconnect write",
                "publish `AVAILABLE` and perform an automatic reconnect write",
            ),
        ),
        (
            CHECKER.RESTART_TRANSITION,
            "| any | gateway restart | `IDLE` | publish AVAILABLE |",
        ),
    ),
)
def test_rejects_refresh_failure_diagram_or_lock_contradiction(
    old: str, new: str
) -> None:
    text = contract().replace(old, new, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "clause",
    (
        "`Refreshing` accepts live-monitor operations.",
        "Live-monitor operations are permitted while `Refreshing`.",
        "`Disabled` is reported with `owned:true`.",
        "`Disabled` can be rendered with `owned:true`.",
    ),
)
def test_rejects_declarative_session_state_contradictions(clause: str) -> None:
    text = contract().replace("### 6.2 Ownership key", clause + "\n\n### 6.2 Ownership key", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        (
            "triggering request remains pending during refresh; after successful rebind,\n"
            "  Gateway dispatches that request's native operation exactly once",
            "triggering request returns SESSION_BUSY while refresh proceeds",
        ),
        (
            table_row(CHECKER.REFRESHING_CAPABILITY_TRUTH_ROW),
            table_row(CHECKER.REFRESHING_CAPABILITY_TRUTH_ROW).replace(
                "subsequent live-monitor operations are `SESSION_BUSY`",
                "subsequent live-monitor operations remain pending",
            ),
        ),
        (
            CHECKER.REFRESH_FAILURE_TRANSITION,
            CHECKER.REFRESH_FAILURE_TRANSITION.replace(
                "return the exact Gateway-supplied failure without dispatching the triggering native operation",
                "retry the triggering native operation after refresh failure",
            ),
        ),
        (
            "Its emitted native\n"
            "outcome, or its pre-emission `TRANSPORT_DOWN`, is returned and recorded exactly,\n"
            "while Gateway retains process-local fail-closed cleanup.",
            "Any ACK or NAK clears Gateway cleanup.",
        ),
        (
            CHECKER.ENABLING_CLEANUP_CONTRACT,
            "A failed enable may leave cleanup registered for a later session.",
        ),
    ),
)
def test_rejects_ambiguous_triggering_refresh_request_outcome(
    old: str, new: str
) -> None:
    text = contract()
    assert old in text
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text.replace(old, new, 1))


@pytest.mark.parametrize(
    "required_failure",
    (
        "`ctx.Done`\nbefore bus turnaround",
        "ACK timeout",
        "NAK",
        "CRC mismatch",
        "bus-arbitration timeout",
        "epoch-advance discard",
        "transport disconnect",
        "gateway restart",
        "or any other\nterminal failure",
    ),
)
def test_rejects_incomplete_enabling_cleanup_failure_set(
    required_failure: str,
) -> None:
    text = contract()
    assert CHECKER.ENABLING_CLEANUP_CONTRACT in text
    replacement = CHECKER.ENABLING_CLEANUP_CONTRACT.replace(
        required_failure, "omitted failure"
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(
            text.replace(CHECKER.ENABLING_CLEANUP_CONTRACT, replacement, 1)
        )


@pytest.mark.parametrize(
    "required_fragment",
    (
        CHECKER.ENABLING_CANCEL_DIAGRAM,
        CHECKER.ENABLING_FAILURE_DIAGRAM,
        CHECKER.ENABLING_ACK_TRANSITION,
        CHECKER.ENABLING_CANCEL_TRANSITION,
        CHECKER.ENABLING_AMBIGUOUS_FAILURE_TRANSITION,
        CHECKER.ENABLING_NAK_TRANSITION,
        CHECKER.ENABLING_DIRECT_IDLE_LOCK,
        CHECKER.DISCONNECT_TRANSITION,
    ),
)
def test_rejects_missing_terminal_enabling_transition(required_fragment: str) -> None:
    text = contract()
    assert required_fragment in text
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text.replace(required_fragment, "omitted", 1))


@pytest.mark.parametrize(
    ("fragment", "replacement"),
    (
        (
            CHECKER.ENABLING_EPOCH_PRE_DIAGRAM,
            "ENABLING --> REFRESHING: epoch advance before enable frame emission",
        ),
        (
            CHECKER.ENABLING_EPOCH_POST_DIAGRAM,
            "ENABLING --> IDLE: epoch advance after enable frame emission",
        ),
        (
            CHECKER.ENABLING_EPOCH_PRE_OPERATION,
            "| Epoch advance under any handle | — | held handle → `REFRESHING`; refresh once per §7.3 |",
        ),
        (
            CHECKER.ENABLING_EPOCH_POST_OPERATION,
            "| Epoch advance after emission | — | release directly to `IDLE` |",
        ),
        (
            CHECKER.ENABLING_EPOCH_PRE_TRANSITION,
            "| `ENABLING` | epoch advance before emission | `REFRESHING` | refresh once |",
        ),
        (
            CHECKER.ENABLING_EPOCH_POST_TRANSITION,
            "| `ENABLING` | epoch advance after emission | `IDLE` | discard completion |",
        ),
        (
            CHECKER.ENABLING_DIRECT_IDLE_LOCK,
            "the direct `ENABLING → REFRESHING` epoch-advance path",
        ),
    ),
)
def test_rejects_ambiguous_enabling_epoch_advance_contract(
    fragment: str, replacement: str
) -> None:
    text = contract().replace(fragment, replacement, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_exactly_one_post_epoch_defensive_disable() -> None:
    text = contract().replace(
        CHECKER.ENABLING_EPOCH_POST_OPERATION,
        CHECKER.ENABLING_EPOCH_POST_OPERATION.replace(
            "at most one defensive disable",
            "exactly one defensive disable",
        ),
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_non_delimiter_milestone_table_separator() -> None:
    table_start = (
        f"{CHECKER.MILESTONE_HEADING}\n\n"
        "| Milestone | Repo | Artefact |\n"
        "|---|---|---|"
    )
    text = contract().replace(
        table_start,
        table_start.removesuffix("|---|---|") + "| bad | bad | bad |",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize("expected", (CHECKER.M2B_GRAPHQL, CHECKER.M3_PORTAL))
def test_rejects_required_milestone_row_copied_after_milestone_table(
    expected: tuple[str, ...],
) -> None:
    stale_row = (expected[0], expected[1], "stale row")
    text = contract().replace(
        table_row(expected), table_row(stale_row), 1
    ) + f"\n{table_row(expected)}\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_required_m3_cells_moved_to_the_wrong_milestone_row() -> None:
    wrong_row = (
        "`M1_DECODER`",
        CHECKER.M3_PORTAL[1],
        CHECKER.M3_PORTAL[2],
    )
    text = contract().replace(table_row(CHECKER.M3_PORTAL), table_row(wrong_row), 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)
