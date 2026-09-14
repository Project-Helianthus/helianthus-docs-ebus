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
            "`UNKNOWN` (temporary; not sticky `AVAILABLE`)",
            "`AVAILABLE`",
        ),
        (
            "only `vaillantCapabilities` and `vaillantLiveMonitorSession` status queries remain admitted",
            "no status query remains admitted",
        ),
        (
            "no B503 card, tabs, bus-facing reads, or actions until capability returns `AVAILABLE`",
            "B503 card and tabs remain admitted while capability is `UNKNOWN`",
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
            "No-owner disconnect discards pending defensive cleanup.",
        ),
        (
            CHECKER.UNCONFIRMED_CLEANUP_OBLIGATION,
            "Any terminal defensive-disable outcome clears cleanup.",
        ),
        (
            CHECKER.GATEWAY_CLEANUP_ATTEMPT_ID,
            "Gateway reuses the browser-local cleanup identity.",
        ),
    ),
)
def test_rejects_missing_disabled_mapping_or_refreshing_consumer_contract(
    clause: str, replacement: str
) -> None:
    text = contract().replace(clause, replacement, 1)
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
    ("old", "new"),
    (
        (
            CHECKER.REFRESH_FAILURE_DIAGRAM,
            "REFRESHING --> DISABLED: refresh failure releases gate",
        ),
        (
            CHECKER.REFRESH_FAILURE_LOCK,
            "only on entry to `DISABLED` from a held-owner state",
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
            "Every subsequent bus-facing live-monitor operation during refresh\n"
            "  returns `SESSION_BUSY`.",
            "Every live-monitor request remains pending during refresh.",
        ),
        (
            "return the exact Gateway-supplied failure to the triggering request without\n"
            "  dispatching its native operation.",
            "retry the triggering native operation after refresh failure.",
        ),
        (
            "If the triggering request was itself the\n"
            "current-owner DISABLE, that single disable is the only client dispatch. A valid\n"
            "disable ACK completes `Disabled` cleanup to `Idle`; any other outcome returns\n"
            "exactly and leaves the process-local defensive cleanup with Gateway. In both\n"
            "cases the consumer clears the queued pair without issuing a second disable.",
            "A successful triggering DISABLE leaves the queued cleanup pair pending.",
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
