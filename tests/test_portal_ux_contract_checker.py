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


def test_fenced_fake_target_end_cannot_truncate_later_dom_audit() -> None:
    text = contract().replace(
        CHECKER.TARGET_END,
        (
            f"```text\n{CHECKER.TARGET_END}\n```\n\n"
            "<button>Reset</button>\n\n"
            f"{CHECKER.TARGET_END}"
        ),
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_required_contract_clause_hidden_in_html_comment() -> None:
    clause = CHECKER.B503_FRONTEND_EPOCH_ROLLOVER
    rejects(clause, f"<!-- {clause} -->")


@pytest.mark.parametrize("container", sorted(CHECKER.NON_RENDERING_CONTAINERS))
def test_rejects_required_contract_clause_hidden_in_inert_html(
    container: str,
) -> None:
    clause = CHECKER.B503_FRONTEND_EPOCH_ROLLOVER
    rejects(clause, f"<{container}>{clause}</{container}>")


def test_accepts_required_contract_clause_in_visible_html() -> None:
    clause = CHECKER.B503_FRONTEND_EPOCH_ROLLOVER
    text = contract()
    CHECKER.validate_text(text.replace(clause, f"<div>{clause}</div>", 1))


@pytest.mark.parametrize("container", ("details", "dialog"))
def test_closed_disclosure_cannot_supply_required_contract_clause(
    container: str,
) -> None:
    clause = CHECKER.B503_FRONTEND_EPOCH_ROLLOVER
    rejects(clause, f"<{container}>{clause}</{container}>")


@pytest.mark.parametrize("container", ("details", "dialog"))
def test_open_disclosure_can_supply_visible_contract_clause(container: str) -> None:
    clause = CHECKER.B503_FRONTEND_EPOCH_ROLLOVER
    text = contract().replace(clause, f"<{container} open>{clause}</{container}>", 1)
    CHECKER.validate_text(text)


def test_rejects_stale_internal_expired_state() -> None:
    rejects(
        CHECKER.B503_NO_EXPIRED_STATE,
        "`EXPIRED` is internal-only and is never a public browser state.",
    )


@pytest.mark.parametrize(
    "clause",
    (
        "`EXPIRED` is an internal session state.",
        "Gateway may publish `EXPIRED` as a sixth availability reason.",
    ),
)
def test_rejects_reintroduced_expired_state(clause: str) -> None:
    rejects_target_insertion(clause)


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
        (CHECKER.B503_TARGET_CLEANUP_SCOPE,
         "Target-switch cleanup is optional."),
        (CHECKER.B503_ENABLING_CLEANUP,
         "An ENABLING prior target waits for passive timeout."),
        (CHECKER.B503_REFRESH_CONTINUATION,
         "After restart Gateway automatically disables every qualified B503 target."),
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


def test_rejects_compact_b503_installation_selector_context() -> None:
    rejects_target_insertion('<button id="b5030201control">Read</button>')


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


def test_accepts_iso_date_in_dom_attribute() -> None:
    accepts_target_insertion('<time datetime="2026-02-01">Accepted</time>')


def test_accepts_commonmark_autolink_followed_by_benign_prose() -> None:
    accepts_target_insertion(
        "<https://example.com>\n\nClear prose follows."
    )


def test_rejects_installation_selector_even_in_prose() -> None:
    rejects_target_insertion(
        "A preset is clearly available; 0201, query=reset, and action = delete are prose."
    )


@pytest.mark.parametrize(
    "snippet",
    (
        "The B503 pane exposes a Reset button.",
        "Add a Clear history control.",
        "A Delete link is rendered.",
        "The pane provides a ClearServiceHistory action.",
        "The pane has a Reset button.",
        "A Clear history control is available.",
        "Users can click the Delete link.",
        "The Reset control appears in the menu.",
        "The pane exposes Reset.",
        "There MUST be a Reset button.",
        "There is a Clear history control.",
        "The pane exposes a Re**set** button.",
        "The pane exposes a Re&#115;et button.",
        "The pane exposes a `Reset` button.",
        "A Reset capability is required.",
        "The Reset button MUST NOT be hidden.",
        "The Clear history control is not disabled.",
        "A Delete action isn't unavailable.",
        "The Reset button shall remain enabled.",
        "The Reset button remains on screen.",
        "The pane does not expose a Reset button, but it renders a Delete link.",
    ),
)
def test_rejects_affirmative_plain_markdown_control(snippet: str) -> None:
    rejects_target_insertion(snippet)


@pytest.mark.parametrize(
    "snippet",
    (
        "The B503 pane does not expose a Reset button.",
        "The B503 pane exposes no Reset button.",
        "No Reset control is rendered.",
        "There MUST NOT be a Reset button.",
        "The Reset control is absent.",
        "A Clear history action is prohibited.",
        "The pane doesn't expose a Reset button.",
        "The pane cannot expose a Reset button.",
        "The Reset button MUST be hidden.",
        "The Clear history control MUST remain disabled.",
        "Resetting the presentation model is not a device control.",
    ),
)
def test_accepts_negative_or_non_control_plain_markdown(snippet: str) -> None:
    accepts_target_insertion(snippet)


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
        '<a href="#re%73et">Read</a>',
        '<a href="#02%2001">Read</a>',
        '<img src="clear%73ervicehistory.svg">',
        inline_code('href="#re%73et"'),
        inline_code('src="02%2001.svg"'),
        inline_code('action="/clear"'),
        inline_code('formaction="#re%73et"'),
        inline_code('poster="02%2001.png"'),
        inline_code('cite="/delete"'),
        inline_code('data="/clearservicehistory"'),
    ),
)
def test_rejects_percent_encoded_html_url_attribute_control(snippet: str) -> None:
    rejects_target_insertion(snippet)


def test_accepts_safe_percent_encoded_html_url_attribute() -> None:
    accepts_target_insertion('<a href="#status%20details">Read</a>')
    accepts_target_insertion(inline_code('src="topology%20view.svg"'))
    for attribute in ("action", "formaction", "poster", "cite", "data"):
        accepts_target_insertion(inline_code(f'{attribute}="/status%20details"'))


@pytest.mark.parametrize(
    "snippet",
    (
        "[Reset](#reset)",
        "[Clear history](../history)",
        "![Reset](reset.svg)",
        "[Read status](#clearservicehistory)",
        "[Clear history][clear-history]\n\n[clear-history]: /history",
        "[Reset][]\n\n[Reset]: #status",
        "[Clear history]\n\n[Clear history]: /history",
        "![Reset][]\n\n[Reset]: image.svg",
        "[Read status][safe]\n\n[safe]: #clearservicehistory",
        "[Re&#x73;et](#safe)",
        "[selector 02&#x20;01](#safe)",
        "[Read status](#cl&#x65;ar)",
        "[Re&#115;et][]\n\n[Re&#115;et]: #status",
    ),
)
def test_rejects_prohibited_markdown_link_or_image_control(snippet: str) -> None:
    rejects_target_insertion(snippet)


def test_accepts_safe_markdown_link_and_image() -> None:
    accepts_target_insertion(
        "[Read status](#status) ![Topology](topology.svg)\n\n"
        "[Details][] [Topology]\n\n[Details]: #details\n[Topology]: topology.svg"
    )
    accepts_target_insertion("[Read stat&#x75;s](#status)")


@pytest.mark.parametrize(
    "snippet",
    (
        "[Re<i></i>set](#safe)",
        "![02<i></i>01](safe.svg)",
        "[Read](https://example.test/(safe)/reset)",
        "[Read](#re%73et)",
        "[Read](#02%2001)",
        "![Status](clear%73ervicehistory.svg)",
        "[Read][duplicate]\n\n[duplicate]: #safe \"Reset\"\n[duplicate]: #safe",
        "[Read][multiline]\n\n[multiline]: #safe\n  \"Reset\"",
    ),
)
def test_commonmark_ast_rejects_renderer_equivalent_control_bypass(
    snippet: str,
) -> None:
    rejects_target_insertion(snippet)


@pytest.mark.parametrize(
    "label",
    ("Reset", "Clear history", "selector 02 01"),
)
def test_rejects_target_reference_resolved_outside_target_section(label: str) -> None:
    text = contract().replace(
        CHECKER.TARGET_END,
        f"[{label}][outside]\n\n{CHECKER.TARGET_END}",
        1,
    )
    text += "\n[outside]: #safe\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_accepts_safe_target_reference_resolved_outside_target_section() -> None:
    text = contract().replace(
        CHECKER.TARGET_END,
        f"[Read status][outside]\n\n{CHECKER.TARGET_END}",
        1,
    )
    text += "\n[outside]: #status\n"
    CHECKER.validate_text(text)


def test_rejects_required_contract_clause_hidden_by_standard_html_attribute() -> None:
    clause = CHECKER.B503_FRONTEND_EPOCH_ROLLOVER
    text = contract().replace(clause, f"<div hidden>{clause}</div>", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "style",
    (
        "display:none",
        "display:none/**/",
        "display:/**/none",
        r"dis\70 lay:none",
        r"display:n\6f ne",
        "DISPLAY: none",
        "visibility: hidden",
        "visibility: collapse",
        "display:none!important",
        "display: none !IMPORTANT",
        "visibility:hidden !important",
        "visibility:collapse !important",
        "display:none!important;display:block",
        "display:block;display:none!important",
        "visibility:hidden!important;visibility:visible",
        "visibility:collapse!important;visibility:visible",
    ),
)
def test_rejects_required_contract_clause_hidden_by_inline_style(style: str) -> None:
    clause = CHECKER.B503_FRONTEND_EPOCH_ROLLOVER
    text = contract().replace(clause, f'<div style="{style}">{clause}</div>', 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "style",
    (
        "display:none;display:block!important",
        "display:none!important;display:block!important",
        "visibility:collapse;visibility:visible!important",
        "visibility:collapse!important;visibility:visible!important",
    ),
)
def test_accepts_later_important_visible_inline_style(style: str) -> None:
    clause = CHECKER.B503_FRONTEND_EPOCH_ROLLOVER
    text = contract().replace(clause, f'<div style="{style}">{clause}</div>', 1)
    CHECKER.validate_text(text)


def test_rejects_required_clause_stored_in_svg_metadata() -> None:
    clause = CHECKER.B503_FRONTEND_EPOCH_ROLLOVER
    rejects(clause, f"<svg><desc>{clause}</desc><text>status</text></svg>")


def test_rejects_required_contract_clause_hidden_in_fenced_code() -> None:
    clause = CHECKER.B503_FRONTEND_EPOCH_ROLLOVER
    rejects(clause, f"```text\n{clause}\n```")


def test_rejects_required_contract_clause_stored_only_in_html_attribute() -> None:
    clause = CHECKER.B503_FRONTEND_EPOCH_ROLLOVER
    rejects(clause, f'<div data-contract="{clause}"></div>')


def test_rejects_required_contract_clause_stored_only_in_link_destination() -> None:
    clause = "Gateway #552 is open;"
    rejects(clause, f"[status](<{clause}>)")


def test_rejects_required_contract_clause_stored_only_in_image_alt() -> None:
    clause = "Gateway #552 is open;"
    rejects(clause, f"![{clause}](status.png)")


def test_rejects_availability_table_hidden_in_fenced_code() -> None:
    table = "\n".join(
        (
            CHECKER.AVAILABILITY_TABLE_HEADER,
            CHECKER.AVAILABILITY_TABLE_SEPARATOR,
            *CHECKER.AVAILABILITY_ROWS.values(),
        )
    )
    text = contract().replace(table, f"```text\n{table}\n```", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_availability_table_wrapped_in_preformatted_html() -> None:
    table = "\n".join(
        (
            CHECKER.AVAILABILITY_TABLE_HEADER,
            CHECKER.AVAILABILITY_TABLE_SEPARATOR,
            *CHECKER.AVAILABILITY_ROWS.values(),
        )
    )
    text = contract().replace(table, f"<pre>\n{table}\n</pre>", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_availability_table_wrapped_in_raw_html_block() -> None:
    table = "\n".join(
        (
            CHECKER.AVAILABILITY_TABLE_HEADER,
            CHECKER.AVAILABILITY_TABLE_SEPARATOR,
            *CHECKER.AVAILABILITY_ROWS.values(),
        )
    )
    text = contract().replace(table, f"<div>\n{table}\n</div>", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "container", ("audio", "canvas", "iframe", "noscript", "object", "video")
)
def test_rejects_availability_table_stored_as_html_fallback(container: str) -> None:
    table = "\n".join(
        (
            CHECKER.AVAILABILITY_TABLE_HEADER,
            CHECKER.AVAILABILITY_TABLE_SEPARATOR,
            *CHECKER.AVAILABILITY_ROWS.values(),
        )
    )
    text = contract().replace(table, f"<{container}>\n{table}\n</{container}>", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "title",
    ('"Reset"', "'Clear history'", "(selector 02 01)"),
)
def test_rejects_prohibited_document_scoped_reference_title(title: str) -> None:
    text = contract().replace(
        CHECKER.TARGET_END,
        f"[Read status][outside]\n\n{CHECKER.TARGET_END}",
        1,
    )
    text += f"\n[outside]: #status {title}\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_accepts_safe_document_scoped_reference_title() -> None:
    text = contract().replace(
        CHECKER.TARGET_END,
        f"[Read status][outside]\n\n{CHECKER.TARGET_END}",
        1,
    )
    text += '\n[outside]: #status "Current status"\n'
    CHECKER.validate_text(text)


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
    "fragment", ("query=reset", "operation = delete")
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


@pytest.mark.parametrize(
    "clause",
    (
        "If main GraphQL is unavailable, retry GET /portal/api/v1/projection/devices.",
        "Use `/portal/api/v1/snapshots/latest` instead when the B503 route fails.",
        "Use GET /portal/api/v1 when the B503 route fails.",
        "Retry GET /portal/api/v%31/projection/devices.",
        "Use [fallback](/portal/api/v1/projection/devices) when GraphQL fails.",
        "If main GraphQL is unavailable, use [backup](https://backup.example/b503).",
        'If main GraphQL is unavailable, use <a href="/portal/api/v1/projection/devices">fallback</a>.',
        '<p>If main GraphQL is unavailable, use <a href="https://backup.example/b503">backup</a>.</p>',
        'If main GraphQL is unavailable, use <form action="/portal/api/v%31/projection/devices">fallback</form>.',
        'If main GraphQL is unavailable, use <a href="#safe" ping="/portal/api/v1/projection/devices">fallback</a>.',
        '<img srcset="/portal/api/v1/projection/devices 1x" alt="fallback">',
        '<meta http-equiv="refresh" content="0;url=/portal/api/v1/projection/devices">',
        '<meta HTTP-EQUIV="Refresh" content="0; URL=/portal/api/v%31/projection/devices">',
        '<svg><a xlink:href="%2fportal%2fapi%2fv1%2fb503">Use this backup when GraphQL fails</a></svg>',
        '<button onclick="location=\'/portal/api/v1/projection/devices\'">Use backup when GraphQL fails</button>',
        '<button onclick="location=\'%2fportal%2fapi%2fv1/projection/devices\'">Use backup when GraphQL fails</button>',
        "<div style=\"background-image:url('/portal/api/v1/projection/devices')\">state</div>",
        '<style>@import "/portal/api/v%31/projection/devices";</style>',
        r'''<div style="background:url('/portal\2f api/v1/projection/devices')">state</div>''',
        "<iframe srcdoc=\"&lt;img src='/portal/api/v1/projection/devices'&gt;\"></iframe>",
        "Fallback:\n\n```text\nGET /portal/api/v1/projection/devices\n```",
    ),
)
def test_rejects_concrete_portal_api_fallback_route(clause: str) -> None:
    rejects_target_insertion(clause)


def test_accepts_unrelated_literal_html_destination() -> None:
    accepts_target_insertion('<a href="https://example.invalid/help">Help</a>.')
    accepts_target_insertion(
        '<p>For background, see <a href="https://example.invalid/help">Help</a>.</p>'
    )
    accepts_target_insertion(
        '<meta name="description" content="/portal/api/v1/projection/devices">'
    )
    accepts_target_insertion(
        '<div style="background-image:url(https://example.invalid/help.png)">Help</div>'
    )
    accepts_target_insertion(
        r'''<div style="background:url('https\3a //example.invalid/help.png')">Help</div>'''
    )
    accepts_target_insertion(
        '<iframe srcdoc="&lt;p&gt;safe status&lt;/p&gt;"></iframe>'
    )


def test_rejects_failed_triggering_disable_left_in_browser_queue() -> None:
    replacement = CHECKER.B503_REFRESHING_CLEANUP.replace(
        "The browser clears the queued pair without issuing a second disable.",
        "The browser leaves the queued pair pending after a native failure.",
    )
    rejects(CHECKER.B503_REFRESHING_CLEANUP, replacement)


def test_rejects_installation_selector_in_fenced_content() -> None:
    rejects_target_insertion("Selector example:\n\n```text\n02 01\n```")


def test_rejects_prohibited_control_in_fenced_content() -> None:
    rejects_target_insertion(
        "Normative control example:\n\n```text\nThe Reset button is available.\n```"
    )


def test_accepts_safe_fenced_content() -> None:
    accepts_target_insertion("Status example:\n\n```text\navailability=UNKNOWN\n```")


@pytest.mark.parametrize(
    "clause",
    (
        "main GraphQL failure does not allow REST fallback.",
        "main GraphQL does not fall back to REST.",
        "main GraphQL does not use REST as a fallback.",
        "If the main GraphQL route fails, the browser does not retry via REST.",
        "main GraphQL does not switch to MCP.",
        "main GraphQL fails over to REST.",
        "main GraphQL retries via `REST`.",
        "main GraphQL switches from `POST /graphql` to `POST /graphql/portal/v1`.",
        "B503 requests may use `GET /graphql`.",
        "main GraphQL retries through `PortalCatalogV1`.",
        "main GraphQL is rerouted through MCP.",
        "main GraphQL uses `PortalActionInvokeV1` after failure.",
    ),
)
def test_rejects_any_extra_b503_route_surface_clause(clause: str) -> None:
    rejects_target_insertion(clause)


@pytest.mark.parametrize(
    "clause",
    (
        "Portal MUST make selector 02 01 available.",
        "GraphQL SHALL surface 0202.",
        "MCP MUST provide a control for 02-02.",
        "`02 01` SHOULD be made available through Portal.",
    ),
)
def test_rejects_installation_selector_in_every_normative_form(clause: str) -> None:
    rejects_target_insertion(clause)


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


@pytest.mark.parametrize(
    "replacement",
    (
        "UNKNOWN capability hides every Active session control.",
        "Any UNKNOWN target may render live-monitor controls.",
        "An Active owner may issue another Enable while settlement is unknown.",
    ),
)
def test_rejects_missing_active_unknown_current_owner_exception(
    replacement: str,
) -> None:
    rejects(CHECKER.B503_ACTIVE_UNKNOWN_OWNER, replacement)


@pytest.mark.parametrize(
    "replacement",
    (
        CHECKER.B503_REFRESHING_UNKNOWN_STRIP.replace(
            "resumes immediately under `UNKNOWN`; it does not\nwait for `AVAILABLE`",
            "remains unavailable until capability is `AVAILABLE`",
        ),
        CHECKER.B503_REFRESHING_UNKNOWN_STRIP.replace(
            "the same target and\nissuer token",
            "any target or issuer token",
        ),
    ),
)
def test_rejects_stranded_or_unbound_post_refresh_owner_controls(
    replacement: str,
) -> None:
    rejects(CHECKER.B503_REFRESHING_UNKNOWN_STRIP, replacement)


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
            CHECKER.B503_ENABLING_CLEANUP,
            "A failed prior-target enable leaves its cleanup registered for the next session.",
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


def test_rejects_ambiguous_configuration_disabled_restart_mapping() -> None:
    rejects(
        "A still-effective\nout-of-band disabled condition takes precedence across Gateway\nrestart",
        "Gateway restart always presents Idle even when a configuration disable remains effective",
    )


def test_rejects_session_disable_as_public_disabled_state() -> None:
    rejects(
        "It is never the result of a current-owner live-monitor\nsession DISABLE action",
        "It is the result of a current-owner live-monitor session DISABLE action",
    )


@pytest.mark.parametrize(
    "required_failure",
    (
        "cancellation before bus turnaround",
        "ACK timeout",
        "NAK",
        "CRC mismatch",
        "bus-arbitration timeout",
        "epoch-advance discard",
        "transport disconnect",
        "gateway restart",
        "or any other terminal failure",
    ),
)
def test_rejects_incomplete_enabling_cleanup_failure_set(
    required_failure: str,
) -> None:
    rejects(
        CHECKER.B503_ENABLING_CLEANUP,
        CHECKER.B503_ENABLING_CLEANUP.replace(required_failure, "omitted failure"),
    )


@pytest.mark.parametrize("clause", CHECKER.FORBIDDEN_B503_SESSION_STATE_CLAUSES)
def test_rejects_unsafe_b503_refreshing_state_contradiction(clause: str) -> None:
    rejects_target_insertion(clause)


@pytest.mark.parametrize(
    "clause",
    (
        "`Refreshing` accepts live-monitor operations.",
        "Live-monitor operations are permitted while `Refreshing`.",
        "`Disabled` is reported with `owned:true`.",
        "`Disabled` can be rendered with `owned:true`.",
    ),
)
def test_rejects_declarative_b503_session_state_contradiction(clause: str) -> None:
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
