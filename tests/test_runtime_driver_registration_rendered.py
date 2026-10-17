"""Rendered section and visibility regressions for the registration guard."""

from pathlib import Path
import textwrap

import pytest

from scripts import check_runtime_driver_registration as checker


ROOT = Path(__file__).resolve().parents[1]
TEXT = (ROOT / checker.DOCUMENT).read_text(encoding="utf-8")
NAMES = tuple(checker.REQUIREMENTS)


@pytest.mark.parametrize("indent", range(4))
@pytest.mark.parametrize("closing", ["", " #", " ###   "])
@pytest.mark.parametrize("headings", [(checker.START,), (checker.END,), (checker.START, checker.END)])
def test_equivalent_heading_syntax(indent: int, closing: str, headings: tuple[str, ...]) -> None:
    changed = TEXT
    for heading in headings:
        changed = changed.replace(heading, " " * indent + heading + closing)
    assert checker.validate(changed) == []


def test_wrapped_visible_contract() -> None:
    changed = TEXT
    for required in checker.REQUIREMENTS.values():
        if not required.startswith("|"):
            changed = changed.replace(required, textwrap.fill(
                " ".join(required.split()), 61,
                break_long_words=False, break_on_hyphens=False,
            ))
    assert checker.validate(changed) == []


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("change", ["missing", "weakened", "before", "after", "intervening"])
def test_each_obligation_requires_exact_unit_in_section(name: str, change: str) -> None:
    required = checker.REQUIREMENTS[name]
    changed = TEXT.replace(required, "")
    if change == "weakened":
        # Retain every original keyword, but change the complete normative unit.
        changed = TEXT.replace(required, required + " Optional.")
    elif change == "before":
        changed = required + "\n\n" + changed
    elif change == "after":
        changed += "\n\n" + required
    elif change == "intervening":
        changed = changed.replace(checker.END, "## Other\n\n" + required + "\n\n" + checker.END)
    assert checker.validate(changed)
    if change != "intervening":
        assert name in checker.validate(changed)


CONTAINERS = [
    ("<details>", "</details>"),
    ('<details open="open">', "</details>"),
    ("<DETAILS\n open\n>", "</DETAILS>"),
    ("<div>", "</div>"),
    ("<details/>", "</details>"),
    ("<section>\n<details open>", "</details>\n</section>"),
    ("<!--", "-->"),
    ("```text", "```"),
    ("~~~text", "~~~"),
]


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("opening,closing", CONTAINERS)
def test_html_and_example_obligations_are_excluded(name: str, opening: str, closing: str) -> None:
    required = checker.REQUIREMENTS[name]
    changed = TEXT.replace(required, f"\n\n{opening}\n\n{required}\n\n{closing}\n\n")
    assert name in checker.validate(changed)


@pytest.mark.parametrize("opening,closing", CONTAINERS)
@pytest.mark.parametrize("heading", ["## Other", checker.START, checker.END])
@pytest.mark.parametrize("indent,closing_hashes", [(0, ""), (3, " ###")])
def test_hidden_headings_do_not_change_boundaries(
    opening: str, closing: str, heading: str, indent: int, closing_hashes: str
) -> None:
    hidden = f"\n\n{opening}\n\n{' ' * indent}{heading}{closing_hashes}\n\n{closing}\n\n"
    assert checker.validate(TEXT.replace(checker.END, hidden + checker.END)) == []


@pytest.mark.parametrize("opening", ["<details>", "<details open>", "<div\n class=\"example\"\n>", "<!--"])
def test_unclosed_container_fails_closed(opening: str) -> None:
    assert checker.validate(TEXT.replace(checker.START, opening + "\n\n" + checker.START))


def test_mismatched_close_does_not_restore_visibility() -> None:
    assert checker.validate("<details>\n\n</div>\n\n" + TEXT)


@pytest.mark.parametrize("position", ["before", "inside", "after"])
@pytest.mark.parametrize("heading", [checker.START, checker.END])
def test_duplicate_heading_at_each_location(position: str, heading: str) -> None:
    if position == "before":
        changed = heading + "\n\n" + TEXT
    elif position == "inside":
        changed = TEXT.replace(checker.END, heading + "\n\n" + checker.END)
    else:
        changed = TEXT + "\n\n" + heading + "\n"
    assert checker.validate(changed)


def test_intervening_visible_heading_rejected() -> None:
    assert checker.validate(TEXT.replace(checker.END, "## Other\n\n" + checker.END))


def test_s5_before_s0_rejected() -> None:
    assert checker.validate(TEXT.replace(checker.START, "## Temporary").replace(
        checker.END, checker.START
    ).replace("## Temporary", checker.END))


def test_inline_html_container_spans_paragraphs() -> None:
    required = checker.REQUIREMENTS["validation and freeze"]
    hidden = f"prefix <span>\n\n{required}\n\n</span>\n"
    assert "validation and freeze" in checker.validate(TEXT.replace(required, hidden))


def test_code_inline_tags_do_not_open_containers() -> None:
    changed = TEXT.replace(checker.START, "`<details>`\n\n" + checker.START)
    assert checker.validate(changed) == []
