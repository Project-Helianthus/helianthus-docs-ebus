from __future__ import annotations

import importlib.util
import pathlib

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "portal_ux_contract", ROOT / "scripts/check_portal_ux_contract.py"
)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def contract() -> str:
    return (ROOT / "api/portal.md").read_text(encoding="utf-8")


def rejects(old: str, new: str) -> None:
    text = contract()
    assert old in text
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text.replace(old, new, 1))


def rejects_target_insertion(token: str) -> None:
    text = contract()
    assert CHECKER.TARGET_END in text
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text.replace(CHECKER.TARGET_END, f"{token}\n\n{CHECKER.TARGET_END}", 1))


def rejects_text(text: str) -> None:
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def with_availability_row(row: str) -> str:
    text = contract()
    marker = "\n\nThe selectors above are stable browser-test identifiers"
    assert marker in text
    return text.replace(marker, f"\n{row}{marker}", 1)


def test_accepts_current_portal_ux_contract() -> None:
    CHECKER.validate_text(contract())


@pytest.mark.parametrize(
    ("old", "new"),
    (
        ('data-testid="b503-state-unknown"', 'data-testid="b503-state-pending"'),
        ('data-testid="b503-session-strip"', 'data-testid="b503-session"'),
        ('data-testid="b503-install-writes-banner"', 'data-testid="install-writes"'),
        ("no REST compatibility shim", "a REST compatibility shim"),
        ("no direct MCP/native fallback", "a direct MCP/native fallback"),
        ("must not require a vendor switch", "may require a vendor switch"),
        ("an arbitrary-English parser", "a label parser"),
        ("Gateway #552 is open;", "Gateway #552 is implemented;"),
        ("real installation/device write still needs action-time\noperator confirmation.",
         "real installation/device write is enabled by this banner."),
        ("Accepted source records and accepted semantic records remain distinct from the\nbrowser presentation state.",
         "The browser may create semantic state from source records."),
        ("Discovery\npermission controls visibility",
         "The browser decides action visibility"),
        ("`POST /graphql` endpoint. That endpoint is protected by the stable eBUS MCP\ngraduation/parity contract.",
         "B503 endpoint is unspecified."),
        ("The browser obtains the catalog read model only through `POST /graphql/portal/v1`\nand the fixed `PortalCatalogV1` operation.",
         "The browser obtains the catalog read model through an unspecified endpoint."),
        ("exclusive operation-to-route\nsplit, not a fallback or compatibility shim.",
         "B503 may fall back to the catalog route."),
        ("base `SESSION_BUSY` presentation is neutral.",
         "base `SESSION_BUSY` presentation identifies another client."),
        ("`vaillantErrorsHistory(targetAddress:limit:)`", "`vaillantErrorsHistory()`"),
        ("`vaillantLiveMonitorSession(targetAddress:)`", "`vaillantLiveMonitorSession()`"),
        ("On every target switch, before\nadmitting the new target presentation, the browser begins targeted cleanup for\neach prior target that it locally owns and whose session is `ENABLING` or\n`ACTIVE`.",
         "Target-switch cleanup is optional."),
        ("For an `ENABLING` prior target,\nthe browser registers that same target-specific disable at switch time and\ndispatches it immediately when the locally initiated enable completes with its\nissuer token.",
         "An ENABLING prior target waits for passive timeout."),
        ("Changing target atomically invalidates the active target-bound presentation:\ncapability, current errors/service, history, live-monitor strip, and pending\ncompletion must not bleed into the new target.",
         "Target changes retain current presentation state."),
        ("Any late enable completion after a switch follows the same prior-target cleanup\nand cannot mutate the new target.",
         "Late completion behavior is unspecified."),
        ("never disables a gate-held session without a\nlocally held issuer token.",
         "disables a gate-held session based only on owned."),
        ("Leaving the B503 perspective uses the same locally-token-bound cleanup\nrule as target switching.",
         "Leaving the B503 perspective retains the session."),
    ),
)
def test_rejects_contract_regressions(old: str, new: str) -> None:
    rejects(old, new)


@pytest.mark.parametrize("token", CHECKER.FORBIDDEN_B503_DOM_VOCABULARY)
def test_rejects_b503_command_vocabulary(token: str) -> None:
    rejects_target_insertion(token)


def test_rejects_availability_selector_swap() -> None:
    not_supported = CHECKER.AVAILABILITY_ROWS["NOT_SUPPORTED"]
    wrong = not_supported.replace(
        'b503-state-not-supported', 'b503-state-transport-down'
    )
    rejects_text(contract().replace(not_supported, wrong, 1))


def test_rejects_availability_row_moved_outside_target_section() -> None:
    row = CHECKER.AVAILABILITY_ROWS["TRANSPORT_DOWN"]
    text = contract().replace(row, "", 1)
    text = text.replace(CHECKER.TARGET_END, f"{CHECKER.TARGET_END}\n\n{row}", 1)
    rejects_text(text)


def test_rejects_availability_presentation_mismatch() -> None:
    row = CHECKER.AVAILABILITY_ROWS["UNKNOWN"]
    wrong = row.replace(
        "State that capability is undetermined; do not equate it with unsupported.",
        "State that transport is unavailable and offer only a retry/reconnect hint.",
    )
    rejects_text(contract().replace(row, wrong, 1))


def test_rejects_extra_availability_row() -> None:
    rejects_text(
        with_availability_row(
            '| `FUTURE` | `data-testid="b503-state-future"` | Custom future state. |'
        )
    )


def test_rejects_duplicate_availability_row() -> None:
    rejects_text(with_availability_row(CHECKER.AVAILABILITY_ROWS["AVAILABLE"]))


def test_rejects_custom_expired_availability_row() -> None:
    rejects_text(
        with_availability_row(
            '| `EXPIRED` | `data-testid="b503-state-expired"` | Render expired B503 state. |'
        )
    )


def test_rejects_projection_card_admission_beyond_available() -> None:
    rejects(
        CHECKER.PROJECTION_CARD_ADMISSION,
        'The section-projection card uses `data-role="projection-b503-card"` for any B503 state.',
    )


def test_rejects_history_without_selected_target_typed_records() -> None:
    rejects(
        CHECKER.SELECTED_TARGET_TYPED_HISTORY,
        'The History tab has `data-role="vaillant-b503-tab-history"`.',
    )


def test_rejects_history_label_or_aggregate_inference() -> None:
    rejects(
        CHECKER.SELECTED_TARGET_TYPED_HISTORY,
        "The History tab may infer history from labels or retained aggregate data.",
    )


def test_rejects_int10_safety_fragment_moved_beyond_target_section() -> None:
    fragment = "no direct MCP/native fallback."
    text = contract().replace(fragment, "", 1)
    text = text.replace(CHECKER.TARGET_END, f"{CHECKER.TARGET_END}\n\n{fragment}", 1)
    rejects_text(text)
