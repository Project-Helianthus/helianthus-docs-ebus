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


def accepts_target_insertion(fragment: str) -> None:
    text = contract()
    assert CHECKER.TARGET_END in text
    CHECKER.validate_text(
        text.replace(CHECKER.TARGET_END, f"{fragment}\n\n{CHECKER.TARGET_END}", 1)
    )


def with_availability_row(row: str) -> str:
    text = contract()
    marker = "\n\nThe selectors above are stable browser-test identifiers"
    assert marker in text
    return text.replace(marker, f"\n{row}{marker}", 1)


def dom_with_attribute(attribute: str) -> str:
    return f"<span {attribute}></span>"


def inline_code(fragment: str) -> str:
    return f"{chr(96)}{fragment}{chr(96)}"


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
        ("On every target switch, before\nadmitting the new target presentation, the browser begins targeted cleanup for\neach prior target that it locally owns and whose session is `ENABLING` or\n`ACTIVE` or `REFRESHING`.",
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


@pytest.mark.parametrize(
    "attribute",
    (
        'id="b503-clear"',
        'value="delete"',
        'data-testid="b503-reset"',
        'hidden="clearerrorhistory"',
        'aria-label="clearservicehistory"',
        'data-command="ClearErrorHistoryAction"',
        'id="b503ResetButton"',
        'aria-label="DeleteServiceHistory"',
        'id="resetbutton"',
        'id="clearerrorhistorybutton"',
        'id="b503resetlink"',
        'id="b503resetmenuitem"',
        'id="b503clearbutton"',
        'id="clearbutton"',
        'id="clearlink"',
        'id="vaillantresetbutton"',
        'id="vaillantclearbutton"',
    ),
)
def test_rejects_exact_b503_command_token_in_any_dom_attribute(attribute: str) -> None:
    rejects_target_insertion(dom_with_attribute(attribute))


@pytest.mark.parametrize(
    "attribute",
    (
        'id="b503-0201"',
        'value="02-01"',
        'data-testid="b503-selector-0x0201"',
        'hidden="0202"',
        'data-selector="02 01"',
        'data-command="02-02"',
        'data-other="0x0202"',
        'id="b503Selector0201Button"',
        'id="b503Selector0202Control"',
        'id="b503-0201button"',
        'id="x_0202control"',
        'id="0x02 0x01"',
        'data-command="0x02-0x02"',
    ),
)
def test_rejects_normalized_installation_selector_in_any_dom_attribute(attribute: str) -> None:
    rejects_target_insertion(dom_with_attribute(attribute))


@pytest.mark.parametrize(
    "attribute",
    (
        'data-selector="0x0203"',
        'data-command="0203"',
        'data-selector="02-03"',
        'data-other="0x0203"',
        'id="b503-clearance"',
        'title="preset clearly available"',
        'id="b503PresetButton"',
        'title="clearlyAvailable"',
        'id="b503Selector02010Button"',
        'id="b503-02010button"',
        'id="x_02020control"',
        'id="presetbutton"',
        'id="clearancebutton"',
        'id="b503presetlink"',
        'id="b503clearance"',
        'id="clearlyAvailable"',
        'id="clearfix"',
        'id="clearfixbutton"',
        'id="vaillantpresetbutton"',
        'id="vaillantclearfixbutton"',
    ),
)
def test_accepts_safe_or_substring_dom_attribute_reference(attribute: str) -> None:
    accepts_target_insertion(dom_with_attribute(attribute))


def test_accepts_harmless_prose_outside_dom_attribute_references() -> None:
    accepts_target_insertion(
        "A preset is clearly available; 0201, query=reset, and action = delete are prose."
    )


@pytest.mark.parametrize(
    "snippet",
    (
        '<input aria-label="Search">The distinction is clear.',
        '<img alt="Topology">The distinction is clear.',
        "<br>The distinction is clear.",
    ),
)
def test_accepts_benign_prose_after_void_dom_element(snippet: str) -> None:
    accepts_target_insertion(snippet)


@pytest.mark.parametrize(
    "snippet",
    (
        "[Reset](#reset)",
        "[Clear history](../history)",
        "![Reset](reset.svg)",
        "[Read status](#clearservicehistory)",
        "[Clear history][clear-history]",
    ),
)
def test_rejects_prohibited_markdown_link_or_image_control(snippet: str) -> None:
    rejects_target_insertion(snippet)


def test_accepts_safe_markdown_link_and_image() -> None:
    accepts_target_insertion("[Read status](#status) ![Topology](topology.svg)")


@pytest.mark.parametrize(
    "attribute",
    (
        'data-testid="b503-reset"',
        'id="b503-0201"',
        'aria-label="ClearErrorHistoryAction"',
    ),
)
def test_rejects_dom_relevant_inline_code_attribute(attribute: str) -> None:
    rejects_target_insertion(inline_code(attribute))


@pytest.mark.parametrize(
    "fragment",
    (
        'title="safe" aria-label="Reset"',
        'title="safe" data-command="0x02-0x02"',
    ),
)
def test_rejects_dom_relevant_attribute_inside_multi_attribute_inline_code(
    fragment: str,
) -> None:
    rejects_target_insertion(inline_code(fragment))


@pytest.mark.parametrize(
    "fragment", ("query=reset", "action = delete")
)
def test_accepts_non_dom_inline_code_assignment(fragment: str) -> None:
    accepts_target_insertion(inline_code(fragment))


@pytest.mark.parametrize(
    "fragment", ('onclick="reset()"', 'onkeydown="clearErrorHistory()"')
)
def test_rejects_standalone_event_handler_inline_code(fragment: str) -> None:
    rejects_target_insertion(inline_code(fragment))


@pytest.mark.parametrize(
    "fragment",
    (
        'query=preview title="safe"',
        'data-testid="b503-safe" onclick="preview()"',
    ),
)
def test_accepts_safe_multi_attribute_inline_code(fragment: str) -> None:
    accepts_target_insertion(inline_code(fragment))


@pytest.mark.parametrize(
    "fragment",
    (
        'data-testid="b503-safe" onclick="reset()"',
        'aria-label="safe" oncommand="delete()"',
        'title="safe" data-command="02-01"',
    ),
)
def test_rejects_every_attribute_after_inline_dom_marker(fragment: str) -> None:
    rejects_target_insertion(inline_code(fragment))


@pytest.mark.parametrize(
    "snippet",
    (
        "<button>Reset</button>",
        "<b503-reset-button>",
        '<button aria-label="Clear error history">Read</button>',
        "<span>Delete</span>",
        "<button>Clear <strong>error history</strong></button>",
        "<button><span>Re</span><span>set</span></button>",
        "<B503ClearErrorHistoryButton></B503ClearErrorHistoryButton>",
    ),
)
def test_rejects_prohibited_command_in_dom_element_name_or_content(snippet: str) -> None:
    rejects_target_insertion(snippet)


@pytest.mark.parametrize(
    "snippet",
    (
        "<b503-preset-button>",
        "<button>Clearly available</button>",
        '<span aria-label="Clearance">Read</span>',
        "<button><span>Pre</span><span>set</span></button>",
    ),
)
def test_accepts_benign_dom_element_name_or_content(snippet: str) -> None:
    accepts_target_insertion(snippet)


@pytest.mark.parametrize(
    "snippet",
    (
        "<b503-0201-button></b503-0201-button>",
        "<span>02 01</span>",
        '<button selector-0201="safe">Read</button>',
    ),
)
def test_rejects_protected_selector_in_every_parsed_dom_component(snippet: str) -> None:
    rejects_target_insertion(snippet)


@pytest.mark.parametrize(
    "clause",
    (
        "main GraphQL failure allows REST fallback.",
        "main GraphQL failure may use MCP fallback.",
        "main GraphQL is unavailable allowing native I/O.",
        "main GraphQL failure allows the other route.",
        "main GraphQL falls back to REST.",
        "main GraphQL failure: use MCP instead.",
        "main GraphQL uses REST as a fallback.",
        "If the main GraphQL route fails, the browser retries via REST.",
        "When main GraphQL is unavailable, the browser switches to MCP.",
        "After main GraphQL has failed, the browser reroutes through native I/O.",
        "main GraphQL failure: routes via the other route.",
    ),
)
def test_rejects_affirmative_b503_main_graphql_fallback_clause(clause: str) -> None:
    rejects_target_insertion(clause)


def test_accepts_negative_b503_main_graphql_fallback_clause() -> None:
    accepts_target_insertion("main GraphQL failure does not allow REST fallback.")
    accepts_target_insertion("main GraphQL does not fall back to REST.")
    accepts_target_insertion("main GraphQL does not use REST as a fallback.")
    accepts_target_insertion(
        "If the main GraphQL route fails, the browser does not retry via REST."
    )
    accepts_target_insertion("main GraphQL does not switch to MCP.")


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


@pytest.mark.parametrize(
    "replacement",
    (
        "The strip states are `Idle`, `Enabling`, `Active`, and `Disabled`.",
    ),
)
def test_rejects_incomplete_b503_refreshing_state_contract(
    replacement: str,
) -> None:
    rejects(CHECKER.B503_SESSION_STATE_CONTRACT, replacement)


@pytest.mark.parametrize(
    ("clause", "replacement"),
    (
        (
            CHECKER.B503_REFRESHING_CLEANUP,
            "Refreshing cleanup is optional after target switch or navigation.",
        ),
        (
            CHECKER.B503_REFRESHING_UNKNOWN_STRIP,
            "UNKNOWN capability hides the session strip and all B503 content.",
        ),
        (
            CHECKER.B503_SESSION_STATE_CONTRACT,
            "Refreshing blocks every B503 operation, including status queries.",
        ),
        (
            CHECKER.B503_DISABLED_PUBLIC_MAPPING,
            "Disabled maps every cleanup path regardless of ownership.",
        ),
        (
            CHECKER.B503_REFRESH_CONTINUATION,
            "Every reconnect reconstructs an active session without a client Enable.",
        ),
    ),
)
def test_rejects_missing_refreshing_cleanup_strip_or_disabled_mapping(
    clause: str, replacement: str
) -> None:
    rejects(clause, replacement)


@pytest.mark.parametrize("clause", CHECKER.FORBIDDEN_B503_SESSION_STATE_CLAUSES)
def test_rejects_unsafe_b503_refreshing_state_contradiction(clause: str) -> None:
    rejects_target_insertion(clause)


@pytest.mark.parametrize(
    ("clause", "replacement"),
    (
        (
            CHECKER.B503_KEYBOARD_ACCESSIBILITY,
            "B503 accessibility follows generic browser behavior.",
        ),
        (
            CHECKER.B503_CAPABILITY_RECONNECT,
            "The browser may retry or preserve B503 state after reconnect.",
        ),
        (
            CHECKER.B503_FIELD_OPERATION_ERRORS,
            "Field operation errors clear B503 availability.",
        ),
        (
            CHECKER.B503_FRONTEND_EPOCH_ROLLOVER,
            "Asynchronous completion always updates the current B503 view.",
        ),
    ),
)
def test_rejects_missing_b503_accessibility_error_or_epoch_clause(
    clause: str, replacement: str
) -> None:
    rejects(clause, replacement)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        ("structured `UPSTREAM_TIMEOUT`", "structured `UPSTREAM_RPC_FAILED`"),
        ("structured `UPSTREAM_RPC_FAILED`", "structured `UPSTREAM_TIMEOUT`"),
    ),
)
def test_rejects_collapsed_b503_timeout_error_mapping(old: str, new: str) -> None:
    rejects(old, new)


def test_rejects_int10_safety_fragment_moved_beyond_target_section() -> None:
    fragment = "no direct MCP/native fallback."
    text = contract().replace(fragment, "", 1)
    text = text.replace(CHECKER.TARGET_END, f"{CHECKER.TARGET_END}\n\n{fragment}", 1)
    rejects_text(text)
