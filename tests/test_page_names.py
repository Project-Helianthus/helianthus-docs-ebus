"""Tests for scripts/check_page_names.py and architecture/page-status.json.

The row identity of the status table is (path, previous_path, status, basis).
Each field is varied by a negative control below:

- path: an upper-case or underscore destination, a duplicate destination, a
  destination whose directory entry is spelled differently, a missing
  destination and a changed directory each fail;
- previous_path: a duplicate earlier name, an earlier name that already
  conforms, a control-file earlier name, a leftover earlier entry and any
  remaining reference to the earlier basename each fail, except pinned
  provenance and kept link text on a References line whose target is renamed;
- status: a value outside the closed set, a missing value, and a promotion
  (candidate text graded as accepted contract or implemented) each fail;
- basis: a sentence that is not on the page and an unknown status with a free
  sentence each fail.
"""

from __future__ import annotations

import json
import os
import posixpath
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_page_names as checker  # noqa: E402

BASIS = "This page is a **Hypothesis** about one candidate layout."
COMMIT = "ab" * 20  # synthetic 40-digit hexadecimal owner commit


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def table(**overrides) -> dict:
    value = {
        "table": "Synthetic status table",
        "scope": "Synthetic rows for checker tests.",
        "statuses": list(checker.STATUSES),
        "control_files": list(checker.CONTROL_FILES),
        "tree_indexes": ["guide/index.md"],
        "unlinked_pages": {},
        "pages": [
            {
                "path": "guide/new-page.md",
                "previous_path": "guide/Old_Page.md",
                "status": "candidate",
                "basis": BASIS,
            }
        ],
        "inherited_unresolved_anchors": [],
        "pinned_provenance": [],
        "known_unresolved_links": [],
    }
    value.update(overrides)
    return value


def save_table(root: Path, value: dict) -> None:
    write(root, checker.TABLE, json.dumps(value, indent=2) + "\n")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    write(root, "README.md", "# Synthetic\n\n- [Guide index](guide/index.md)\n")
    write(
        root,
        "guide/index.md",
        "# Guide pages\n\n- [new-page.md](new-page.md)\n- [other.md](other.md)\n",
    )
    write(
        root,
        "guide/new-page.md",
        f"# New page\n\n{BASIS}\n\n## Section one\n\nBody.\n",
    )
    write(root, "guide/other.md", "# Other\n\nSee [the section](new-page.md#section-one).\n")
    save_table(root, table())
    return root


def errors(root: Path) -> list[str]:
    return checker.check(root)


def assert_fails(root: Path, fragment: str) -> None:
    found = errors(root)
    assert any(fragment in error for error in found), found


def rename_row(root: Path, new_path: str) -> None:
    old = root / "guide/new-page.md"
    target = root / new_path
    target.parent.mkdir(parents=True, exist_ok=True)
    old.rename(target)
    value = table()
    value["pages"][0]["path"] = new_path
    save_table(root, value)
    link = posixpath.relpath(new_path, "guide")
    write(root, "guide/index.md", f"# Guide pages\n\n- [p]({link})\n- [other.md](other.md)\n")
    write(root, "guide/other.md", "# Other\n")


def test_file_key_shortens_a_content_address_segment() -> None:
    digest = "0123456789abcdef" * 4
    assert checker.file_key(f"guide/history/{digest}/page.json") == (
        "guide/history/0123456789abcdef/page.json"
    )
    assert checker.file_key("guide/history/page.json") == "guide/history/page.json"


def test_repository_passes() -> None:
    assert checker.check(ROOT) == []


def test_repository_table_is_the_bounded_rename() -> None:
    value = json.loads((ROOT / checker.TABLE).read_text(encoding="utf-8"))
    rows = value["pages"]
    assert len(rows) == 154
    assert value["statuses"] == list(checker.STATUSES)
    assert value["control_files"] == list(checker.CONTROL_FILES)
    for row in rows:
        assert row["status"] in checker.STATUSES
        assert checker.KEBAB.fullmatch(posixpath.basename(row["path"]))
        assert not checker.KEBAB.fullmatch(posixpath.basename(row["previous_path"]))
        assert posixpath.dirname(row["path"]) == posixpath.dirname(row["previous_path"])
        assert posixpath.basename(row["path"]) == (
            posixpath.basename(row["previous_path"]).lower().replace("_", "-")
        )
    assert value["tree_indexes"] == [
        "api/index.md",
        "architecture/index.md",
        "deployment/index.md",
        "development/index.md",
        "protocols/index.md",
    ]


def test_synthetic_repository_passes(repo: Path) -> None:
    assert errors(repo) == []
    assert checker.main(["--root", str(repo)]) == 0


def test_main_fails_closed(repo: Path) -> None:
    (repo / "guide/new-page.md").unlink()
    assert checker.main(["--root", str(repo)]) == 1


@pytest.mark.parametrize("name", ["guide/New-Page.md", "guide/new_page.md", "guide/new--page.md"])
def test_destination_must_be_lowercase_kebab_case(repo: Path, name: str) -> None:
    rename_row(repo, name)
    assert_fails(repo, "basename is not lowercase kebab-case")


def test_duplicate_destination_fails(repo: Path) -> None:
    value = table()
    value["pages"].append(dict(value["pages"][0], previous_path="guide/Other_Page.md"))
    save_table(repo, value)
    assert_fails(repo, "destination guide/new-page.md is listed 2 times")


def test_duplicate_earlier_name_fails(repo: Path) -> None:
    write(repo, "guide/second-page.md", f"# Second\n\n{BASIS}\n")
    write(
        repo,
        "guide/index.md",
        "# Guide pages\n\n- [a](new-page.md)\n- [b](second-page.md)\n- [c](other.md)\n",
    )
    value = table()
    value["pages"].append(dict(value["pages"][0], path="guide/second-page.md"))
    save_table(repo, value)
    assert_fails(repo, "earlier name guide/Old_Page.md is listed 2 times")


def test_destination_entry_spelling_is_compared_exactly(repo: Path) -> None:
    # On a case-insensitive filesystem Path.exists() is still true here.
    os.rename(repo / "guide/new-page.md", repo / "guide/NEW-PAGE.md")
    found = errors(repo)
    assert any("no directory entry with this exact spelling" in e for e in found), found
    assert any("collides with a different entry ignoring letter case" in e for e in found), found


def test_missing_destination_fails(repo: Path) -> None:
    (repo / "guide/new-page.md").unlink()
    assert_fails(repo, "no directory entry with this exact spelling")


def test_directory_change_fails(repo: Path) -> None:
    value = table()
    value["pages"][0]["previous_path"] = "other/Old_Page.md"
    save_table(repo, value)
    assert_fails(repo, "directory changed from other")


def test_leftover_earlier_entry_fails(repo: Path) -> None:
    write(repo, "guide/Old_Page.md", "# Old\n")
    assert_fails(repo, "earlier entry Old_Page.md is still present")


def test_earlier_name_must_need_the_rename(repo: Path) -> None:
    value = table()
    value["pages"][0]["previous_path"] = "guide/old-page.md"
    save_table(repo, value)
    assert_fails(repo, "already conforms")


@pytest.mark.parametrize("name", checker.CONTROL_FILES)
def test_control_files_are_not_renamed_pages(repo: Path, name: str) -> None:
    value = table()
    value["pages"][0]["previous_path"] = f"guide/{name}"
    save_table(repo, value)
    assert_fails(repo, "repository control files are not renamed pages")


@pytest.mark.parametrize("status", ["current", "proposed", "Candidate", ""])
def test_status_outside_closed_set_fails(repo: Path, status: str) -> None:
    value = table()
    value["pages"][0]["status"] = status
    save_table(repo, value)
    found = errors(repo)
    assert any(
        "outside the closed set" in e or "every field must be a non-empty string" in e
        for e in found
    ), found


def test_null_status_fails(repo: Path) -> None:
    value = table()
    value["pages"][0]["status"] = None
    save_table(repo, value)
    assert_fails(repo, "every field must be a non-empty string")


@pytest.mark.parametrize(
    ("status", "fragment"),
    [
        ("accepted contract", "basis does not state the accepted contract status"),
        ("implemented", "basis does not state the implemented status"),
        ("historical", "basis does not state the historical status"),
    ],
)
def test_candidate_text_cannot_be_promoted(repo: Path, status: str, fragment: str) -> None:
    value = table()
    value["pages"][0]["status"] = status
    save_table(repo, value)
    assert_fails(repo, fragment)


def test_contract_wording_on_candidate_text_is_not_accepted(repo: Path) -> None:
    sentence = "This candidate contract is a **Hypothesis**."
    write(repo, "guide/new-page.md", f"# New page\n\n{sentence}\n\n## Section one\n")
    value = table()
    value["pages"][0].update(status="accepted contract", basis=sentence)
    save_table(repo, value)
    assert_fails(repo, "a candidate basis cannot carry an accepted contract")


def test_implemented_basis_cannot_deny_implementation(repo: Path) -> None:
    sentence = "No runtime feature is implemented."
    write(repo, "guide/new-page.md", f"# New page\n\n{sentence}\n\n## Section one\n")
    value = table()
    value["pages"][0].update(status="implemented", basis=sentence)
    save_table(repo, value)
    assert_fails(repo, "the basis denies implementation")


def test_basis_must_stay_on_the_page(repo: Path) -> None:
    value = table()
    value["pages"][0]["basis"] = "This page is a **Hypothesis** about another layout."
    save_table(repo, value)
    assert_fails(repo, "basis sentence is not on the page")


def test_basis_ignores_line_wrapping(repo: Path) -> None:
    write(
        repo,
        "guide/new-page.md",
        "# New page\n\nThis page is a **Hypothesis**\nabout one candidate layout.\n\n## Section one\n",
    )
    assert errors(repo) == []


def test_unknown_status_uses_the_fixed_sentence(repo: Path) -> None:
    value = table()
    value["pages"][0]["status"] = "unknown"
    save_table(repo, value)
    assert_fails(repo, "an unknown status uses the fixed basis sentence")
    value["pages"][0]["basis"] = checker.NO_STATEMENT
    save_table(repo, value)
    assert errors(repo) == []


@pytest.mark.parametrize(
    "text",
    [
        "See [old](Old_Page.md).\n",
        "PAGE = ROOT / 'guide' / 'Old_Page.md'\n",
        f"[old]({checker.BRANCH_URL}guide/Old_Page.md)\n",
    ],
)
def test_remaining_reference_to_earlier_name_fails(repo: Path, text: str) -> None:
    write(repo, "notes/refs.txt", text)
    assert_fails(repo, "still names the earlier page Old_Page.md")


def test_pinned_provenance_keeps_the_earlier_path(repo: Path) -> None:
    pinned = {"owner_commit": COMMIT, "owner_path": "guide/Old_Page.md"}
    write(repo, "data/registry.json", json.dumps(pinned) + "\n")
    save_table(repo, table(pinned_provenance=[{
        "file": "data/registry.json", "path": "guide/Old_Page.md", "count": 1,
    }]))
    assert errors(repo) == []


@pytest.mark.parametrize("commit", ["main", COMMIT[:12], ""])
def test_unpinned_provenance_is_not_exempt(repo: Path, commit: str) -> None:
    unpinned = {"owner_commit": commit, "owner_path": "guide/Old_Page.md"}
    write(repo, "data/registry.json", json.dumps(unpinned) + "\n")
    assert_fails(repo, "still names the earlier page Old_Page.md")


def test_link_spelling_must_match_the_entry(repo: Path) -> None:
    write(repo, "guide/other.md", "# Other\n\nSee [the page](NEW-PAGE.md).\n")
    assert_fails(repo, "link spelling differs from guide/new-page.md")


@pytest.mark.parametrize(
    "target",
    ["new-page.md#missing", f"{checker.BRANCH_URL}guide/new-page.md#missing"],
)
def test_anchor_into_renamed_page_must_resolve(repo: Path, target: str) -> None:
    write(repo, "guide/other.md", f"# Other\n\nSee [missing]({target}).\n")
    assert_fails(repo, "anchor #missing is not on guide/new-page.md")


def test_reference_definitions_are_checked(repo: Path) -> None:
    write(repo, "guide/other.md", "# Other\n\nSee [missing][m].\n\n[m]: new-page.md#missing\n")
    assert_fails(repo, "anchor #missing is not on guide/new-page.md")


def test_inherited_unresolved_anchor_is_an_exact_finite_list(repo: Path) -> None:
    write(repo, "guide/other.md", "# Other\n\nSee [missing](new-page.md#missing).\n")
    entry = {"source": "guide/other.md", "target": "guide/new-page.md", "anchor": "missing"}
    save_table(repo, table(inherited_unresolved_anchors=[entry]))
    assert errors(repo) == []
    write(repo, "guide/other.md", "# Other\n")
    assert_fails(repo, "no longer occurs unresolved")


def test_duplicate_and_explicit_anchors_resolve(repo: Path) -> None:
    write(
        repo,
        "guide/new-page.md",
        f'# New page\n\n{BASIS}\n\n## Section one\n\n## Section one\n\n<a id="kept"></a>\n',
    )
    write(
        repo,
        "guide/other.md",
        "# Other\n\n[a](new-page.md#section-one-1) [b](new-page.md#kept)\n",
    )
    assert errors(repo) == []


def test_index_swap_fails(repo: Path) -> None:
    write(repo, "guide/quiet-page.md", "# Quiet page\n")
    save_table(repo, table(unlinked_pages={
        "guide/index.md": [checker.page_identifier("guide/quiet-page.md")],
    }))
    assert errors(repo) == []
    write(repo, "guide/index.md", "# Guide\n[a](new-page.md) [b](quiet-page.md)\n")
    assert_fails(repo, "guide/index.md: unlinked page identifiers differ")
    assert_fails(repo, "guide/other.md")


@pytest.mark.parametrize("value", [[], None, {"guide/index.md": 1},
    {"guide/index.md": ["INVALID"]}, {"other/index.md": []},
    {"guide/index.md": ["abcdef0123456789", "abcdef0123456789"]}])
def test_malformed_unlinked_pages_fails(repo: Path, value) -> None:
    save_table(repo, table(unlinked_pages=value))
    assert_fails(repo, "unlinked_pages must map listed tree indexes to identifier lists")


def test_unrelated_commit_does_not_hide_stale_name(repo: Path) -> None:
    write(repo, "data/registry.json", json.dumps({
        "owner_commit": COMMIT, "owner_path": "guide/other.md",
        "note": "guide/Old_Page.md",
    }))
    assert_fails(repo, "still names the earlier page Old_Page.md")


def test_pinned_count_must_match(repo: Path) -> None:
    write(repo, "data/registry.json", json.dumps({
        "owner_commit": COMMIT, "owner_path": "guide/Old_Page.md",
    }))
    save_table(repo, table(pinned_provenance=[{
        "file": "data/registry.json", "path": "guide/Old_Page.md", "count": 2,
    }]))
    assert_fails(repo, "occurrence count differs")


def test_missing_link_fails(repo: Path) -> None:
    write(repo, "guide/other.md", "# Other\n[page](absent-page.md)\n")
    assert_fails(repo, "missing link target absent-page.md")


def test_known_missing_link_must_remain_unresolved(repo: Path) -> None:
    write(repo, "guide/other.md", "# Other\n[page](absent-page.md)\n")
    save_table(repo, table(known_unresolved_links=[{
        "source": "guide/other.md", "target": "absent-page.md",
    }]))
    assert errors(repo) == []
    write(repo, "guide/absent-page.md", "# Page\n")
    assert_fails(repo, "no longer occurs unresolved")


def test_readme_must_link_every_tree_index(repo: Path) -> None:
    write(repo, "README.md", "# Synthetic\n")
    assert_fails(repo, "README.md: does not link the tree index guide/index.md")


def test_missing_tree_index_fails(repo: Path) -> None:
    (repo / "guide/index.md").unlink()
    assert_fails(repo, "guide/index.md: tree index is missing")


def test_listed_page_outside_indexes_needs_a_readme_link(repo: Path) -> None:
    save_table(repo, table(tree_indexes=[]))
    assert_fails(repo, "README.md: guide/new-page.md has no tree index and is not linked")
    write(repo, "README.md", "# Synthetic\n\n- [page](guide/new-page.md)\n")
    assert errors(repo) == []


@pytest.mark.parametrize(
    ("key", "value", "fragment"),
    [
        ("statuses", ["implemented", "candidate"], "statuses must be exactly"),
        ("control_files", ["README.md"], "control_files must be exactly"),
        ("tree_indexes", ["guide/start.md"], "tree_indexes must list"),
        ("pages", [], "pages must be a non-empty list"),
    ],
)
def test_table_shape_is_closed(repo: Path, key: str, value, fragment: str) -> None:
    save_table(repo, table(**{key: value}))
    assert_fails(repo, fragment)


def test_unknown_or_missing_top_level_keys_fail(repo: Path) -> None:
    value = table()
    value["aliases"] = {}
    save_table(repo, value)
    assert_fails(repo, "top-level keys must be exactly")
    value = table()
    del value["inherited_unresolved_anchors"]
    save_table(repo, value)
    assert_fails(repo, "top-level keys must be exactly")


def test_unreadable_table_fails(repo: Path) -> None:
    write(repo, checker.TABLE, "{")
    assert_fails(repo, "unreadable status table")


@pytest.mark.parametrize(
    "text",
    [
        "# Notes\n\n## References\n\n- [`Old_Page.md`](../guide/new-page.md)\n",
        "# Notes\n\n## Cross-References\n\nSee [`Old_Page.md#section-one`](../guide/new-page.md#section-one).\n",
        "# Notes\n\n| Field | Value |\n|---|---|\n| Reference | [`Old_Page.md`](../guide/new-page.md) |\n",
    ],
)
def test_references_line_keeps_link_text_with_renamed_target(repo: Path, text: str) -> None:
    write(repo, "notes/refs.md", text)
    assert errors(repo) == []


@pytest.mark.parametrize(
    "text",
    [
        # outside a References section the link text follows the rename
        "# Notes\n\n## Scope\n\n- [`Old_Page.md`](../guide/new-page.md)\n",
        # the kept text needs the renamed target
        "# Notes\n\n## References\n\n- [`Old_Page.md`](../guide/other.md)\n",
        # plain text on a References line is not link text
        "# Notes\n\n## References\n\n- Old_Page.md\n",
        # a fenced block is not a References line
        "# Notes\n\n## References\n\n```text\n[`Old_Page.md`](../guide/new-page.md)\n```\n",
    ],
)
def test_earlier_name_outside_kept_link_text_fails(repo: Path, text: str) -> None:
    write(repo, "notes/refs.md", text)
    assert_fails(repo, "still names the earlier page Old_Page.md")
