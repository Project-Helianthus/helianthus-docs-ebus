"""Tests for scripts/check_semantic_term_qualifiers.py.

A quotation list entry is keyed by (page path, excerpt). Each field is varied
by a negative control below:

- page path: the same excerpt on another page is still rejected, which catches
  a checker that matches an excerpt without its path; an entry naming a
  missing page is reported, which catches a checker that ignores unknown paths;
- excerpt: another occurrence of the term on the listed page is still
  rejected, which catches a checker that exempts the whole page; an excerpt
  that no longer occurs, or occurs twice, is reported as stale, which catches a
  checker that keeps unused or ambiguous exemptions.

The reason field is documentation only and is not part of the key.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_semantic_term_qualifiers as checker  # noqa: E402


def page(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_repository_pages_pass() -> None:
    assert checker.findings(ROOT) == []
    assert checker.main(["--root", str(ROOT)]) == 0


@pytest.mark.parametrize(
    "text",
    [
        "The semantic plane holds zones.",
        "All Semantic Planes are published.",
        "the semantic\nplane wraps across lines",
        "the semantic-plane page",
        "one semantic lens answers it",
        "two Semantic Lenses",
        "Canonical semantic identity is a tuple.",
        "canonical semantic\nidentities differ",
        "the registry semantic plane",
    ],
)
def test_rejects_unqualified_terms(tmp_path: Path, text: str) -> None:
    page(tmp_path, "architecture/page.md", text)
    errors = checker.findings(tmp_path, quotations=())
    assert len(errors) == 1
    assert errors[0].startswith("architecture/page.md:")


def test_reports_the_line_of_a_wrapped_term(tmp_path: Path) -> None:
    page(tmp_path, "api/page.md", "# Title\n\nEvery semantic\nplane is listed.\n")
    assert checker.findings(tmp_path, quotations=())[0].startswith("api/page.md:3:")


@pytest.mark.parametrize(
    "text",
    [
        "every MCP semantic plane required by the gate",
        "all 12 MCP semantic planes return data",
        "every MCP\nsemantic plane is non-null",
        "a registry plane and a registry projection",
        "a method bundle of the system plane",
        "the semantic snapshot and the semantic poller",
        "canonical identity of a semantic fact",
        "the lens of the common contract",
    ],
)
def test_accepts_qualified_and_unrelated_wording(tmp_path: Path, text: str) -> None:
    page(tmp_path, "architecture/page.md", text)
    assert checker.findings(tmp_path, quotations=()) == []


@pytest.mark.parametrize(
    "text",
    ["the mcp semantic plane", "an MCP-like semantic plane", "MCP: semantic plane"],
)
def test_qualifier_is_the_exact_previous_word(tmp_path: Path, text: str) -> None:
    page(tmp_path, "architecture/page.md", text)
    assert len(checker.findings(tmp_path, quotations=())) == 1


def test_qualifier_does_not_apply_to_lens_or_identity(tmp_path: Path) -> None:
    page(tmp_path, "a.md", "MCP semantic lens and MCP canonical semantic identity")
    assert len(checker.findings(tmp_path, quotations=())) == 2


def test_skips_hidden_directories(tmp_path: Path) -> None:
    page(tmp_path, ".tmp/before/page.md", "the semantic plane")
    page(tmp_path, ".github/page.md", "the semantic plane")
    assert checker.findings(tmp_path, quotations=()) == []


QUOTE = (("docs/quoted.md", "the semantic plane projects this", "kept verbatim"),)


def test_quotation_entry_accepts_its_exact_excerpt(tmp_path: Path) -> None:
    page(tmp_path, "docs/quoted.md", "Here the semantic\nplane projects this selector.")
    assert checker.findings(tmp_path, quotations=QUOTE) == []


def test_quotation_path_field_is_part_of_the_key(tmp_path: Path) -> None:
    page(tmp_path, "docs/quoted.md", "the semantic plane projects this")
    page(tmp_path, "docs/other.md", "the semantic plane projects this")
    errors = checker.findings(tmp_path, quotations=QUOTE)
    assert len(errors) == 1
    assert errors[0].startswith("docs/other.md:1:")


def test_quotation_excerpt_field_is_part_of_the_key(tmp_path: Path) -> None:
    page(tmp_path, "docs/quoted.md", "the semantic plane projects this. A semantic plane.")
    errors = checker.findings(tmp_path, quotations=QUOTE)
    assert len(errors) == 1
    assert "unqualified 'semantic plane'" in errors[0]


@pytest.mark.parametrize(
    "text",
    ["the plane projects this", "the semantic plane projects this; the semantic plane projects this"],
)
def test_stale_or_ambiguous_quotation_is_reported(tmp_path: Path, text: str) -> None:
    page(tmp_path, "docs/quoted.md", text)
    errors = checker.findings(tmp_path, quotations=QUOTE)
    assert any("quotation list entry matches" in error for error in errors)


def test_quotation_for_missing_page_is_reported(tmp_path: Path) -> None:
    page(tmp_path, "docs/other.md", "no terms here")
    errors = checker.findings(tmp_path, quotations=QUOTE)
    assert errors == ["docs/quoted.md: quotation list names a missing page: 'the semantic plane projects this'"]


def test_repository_quotation_list_entries_are_live() -> None:
    for path, excerpt, reason in checker.QUOTATION_LIST:
        text, _lines = checker.normalized((ROOT / path).read_text(encoding="utf-8"))
        assert text.count(" ".join(excerpt.split())) == 1, path
        assert reason


def test_main_reports_failure(tmp_path: Path, capsys) -> None:
    page(tmp_path, "a.md", "the semantic plane")
    assert checker.main(["--root", str(tmp_path)]) == 1
    assert "a.md:1: unqualified" in capsys.readouterr().err
