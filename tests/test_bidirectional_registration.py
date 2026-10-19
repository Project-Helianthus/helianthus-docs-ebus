from pathlib import Path
import subprocess
import sys

import pytest

from scripts import check_bidirectional_registration as checker


ROOT = Path(__file__).resolve().parents[1]
TEXT = (ROOT / checker.DOCUMENT).read_text(encoding="utf-8")
BLOCKS = [block for blocks in checker.REQUIREMENTS.values() for block in blocks]


def test_bidirectional_registration_repository() -> None:
    assert checker.validate(TEXT) == []


@pytest.mark.parametrize("heading", [
    "Snapshot reads, selection and explicit publication",
    "Synthetic-peer acceptance obligations",
])
def test_bidirectional_registration_requires_normative_sections(heading) -> None:
    before, section = TEXT.split(f"## {heading}\n\n", 1)
    _, separator, following = section.partition("\n## ")
    assert checker.validate(before + separator + following)


@pytest.mark.parametrize("block", BLOCKS)
@pytest.mark.parametrize("change", ["missing", "optional", "example", "hidden", "relocated"])
def test_bidirectional_registration_requires_visible_normative_blocks(block, change) -> None:
    assert TEXT.count(block) == 1
    replacement = {
        "missing": "",
        "optional": block + " Optional.",
        "example": f"```text\n{block}\n```",
        "hidden": f"<!--\n{block}\n-->",
        "relocated": "",
    }[change]
    changed = TEXT.replace(block, replacement)
    if change == "relocated":
        changed += "\n\n## Other\n\n" + block
    assert checker.validate(changed)


@pytest.mark.parametrize(("before", "after"), [
    ("Maximum hops remain 8", "Maximum hops remain 9"),
    ("positive and at most 300 seconds", "positive and at most 600 seconds"),
    ("`northbound` | Consumes", "`outbound` | Consumes"),
    ("every hook declaration fails", "every hook declaration succeeds"),
    ("including\nthe reserved", "excluding\nthe reserved"),
    ("before effects", "after effects"),
    ("disjoint sink namespace", "shared source namespace"),
    ("exactly one pending successor", "multiple pending successors"),
    ("missing recovery material keeps that sink closed", "missing recovery material opens that sink"),
    ("old work cannot affect a successor", "old work may affect a successor"),
    ("at hop zero", "at hop one"),
    ("Egress changes neither path nor count", "Egress increments the count"),
    ("before hop-budget exhaustion", "after hop-budget exhaustion"),
    ("must not implicitly publish", "may implicitly publish"),
    ("it cannot\nsilently switch candidate or target", "it may\nsilently switch candidate or target"),
    ("without native equipment", "with native equipment"),
    ("Stale selection and lost response cannot silently republish or reroute",
     "Stale selection and lost response may silently republish or reroute"),
    ("with independent expected values and a named production mutation",
     "without independent expected values or a named production mutation"),
])
def test_bidirectional_registration_rejects_weakened_clauses(before, after) -> None:
    assert before in TEXT
    assert checker.validate(TEXT.replace(before, after))


def test_bidirectional_registration_allows_rewrapping() -> None:
    changed = TEXT
    for block in BLOCKS:
        if not block.startswith("|"):
            changed = changed.replace(block, checker.normalize(block))
    assert checker.validate(changed) == []


def test_bidirectional_registration_cli(tmp_path) -> None:
    document = tmp_path / checker.DOCUMENT
    document.parent.mkdir(parents=True)
    for text, expected in [(TEXT, 0), (TEXT.replace("Maximum hops remain 8", "Maximum hops remain 9"), 1)]:
        document.write_text(text, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_bidirectional_registration.py"),
             "--root", str(tmp_path)], capture_output=True, text=True, check=False,
        )
        assert result.returncode == expected, result.stderr


def test_bidirectional_registration_gate_registration() -> None:
    gate = (ROOT / "scripts/ci_local.sh").read_text()
    assert "python3 scripts/check_bidirectional_registration.py\n" in gate
    assert "python3 -m pytest -q tests/test_bidirectional_registration.py\n" in gate
