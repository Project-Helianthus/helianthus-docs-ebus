"""Pin the ENH session-extension nibble reservation.

Each reserved command identity is direction, nibble and name. A production
edit that changes one field must fail:

- direction: the row is moved into the other direction block. The checker
  rejects the source block. Shared nibbles 0x4 to 0x7 also duplicate the
  destination nibble; 0x8 and 0xD make the destination block mismatch.
- nibble: the row is rewritten to 0x0. That nibble is already INIT on the
  host side and RESETTED on the adapter side, so the checker reports a
  collision with the assigned command.
- name: the row's name token gains a trailing X. The checker rejects that
  direction's assignment map. The other direction stays intact, and no
  collision is reported.

Assigned-side collisions, one per direction, are the same overlap seen from
the assigned table: START rewritten to 0x4 collides with TARGET, and FAILED
rewritten to 0xD collides with TARGET_ERROR.

Contract sentences are separate from that identity. Deleting one sentence
fails the clause check. Inserting a response time fails the timing check.
An extra unreserved nibble in the reservation block fails the assignment map.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import NamedTuple

import pytest


ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    ROOT / "protocols" / "enh.md",
    ROOT / "architecture" / "enh-ens-conformance-tests.md",
)
HEADER_OF = {
    "Requests (host → adapter):": "host",
    "Responses (adapter → host):": "adapter",
    "Session to mux:": "session",
    "Mux to session:": "mux",
}
ASSIGN_RE = re.compile(r"^ +(0x[0-9A-F]) = ([A-Z][A-Z0-9_]*)$")
TIME_RE = re.compile(r"\d+\s*(?:ms|milliseconds?|seconds?)\b", re.IGNORECASE)
ASSIGNED = {
    "host": {0x0: "INIT", 0x1: "SEND", 0x2: "START", 0x3: "INFO"},
    "adapter": {
        0x0: "RESETTED",
        0x1: "RECEIVED",
        0x2: "STARTED",
        0x3: "INFO",
        0xA: "FAILED",
        0xB: "ERROR_EBUS",
        0xC: "ERROR_HOST",
    },
}
CLAUSES = (
    "Each reserved frame uses the encoded two-byte form.",
    "The short form is not used.",
    "A session that never sends TARGET sees an unchanged ENH stream.",
    "A TARGET sent to an adapter that has no extension receives the existing unknown-command error.",
    "An unreserved nibble is still an explicit protocol error.",
    "Response timing is Unknown.",
)


class Row(NamedTuple):
    direction: str
    other: str
    nibble: int
    name: str
    source_header: str
    dest_header: str

    @property
    def line(self) -> str:
        return f"  {nibble_text(self.nibble)} = {self.name}"


ROWS = (
    Row("session", "mux", 0x4, "TARGET", "Session to mux:", "Mux to session:"),
    Row("session", "mux", 0x5, "UNTARGET", "Session to mux:", "Mux to session:"),
    Row("session", "mux", 0x6, "BEGIN", "Session to mux:", "Mux to session:"),
    Row("session", "mux", 0x7, "STAGE", "Session to mux:", "Mux to session:"),
    Row("session", "mux", 0x8, "COMMIT", "Session to mux:", "Mux to session:"),
    Row("mux", "session", 0x4, "TARGETED", "Mux to session:", "Session to mux:"),
    Row("mux", "session", 0x5, "UNTARGETED", "Mux to session:", "Session to mux:"),
    Row("mux", "session", 0x6, "SLOT", "Mux to session:", "Session to mux:"),
    Row("mux", "session", 0x7, "SLOT_END", "Mux to session:", "Session to mux:"),
    Row("mux", "session", 0xD, "TARGET_ERROR", "Mux to session:", "Session to mux:"),
)


def nibble_text(value: int) -> str:
    return "0x" + format(value, "X")


def parse(text: str) -> tuple[dict[str, dict[int, str]], list[str]]:
    found: dict[str, dict[int, str]] = {}
    errors: list[str] = []
    current: str | None = None
    seen: set[str] = set()
    for line in text.splitlines():
        header = HEADER_OF.get(line.strip())
        if header is not None:
            if header in seen:
                errors.append("duplicate header " + header)
            seen.add(header)
            current = header
            found.setdefault(header, {})
            continue
        match = ASSIGN_RE.match(line)
        if match is not None and current is not None:
            nibble = int(match.group(1), 16)
            name = match.group(2)
            bucket = found[current]
            if nibble in bucket:
                errors.append("duplicate nibble " + current + " " + nibble_text(nibble))
            else:
                bucket[nibble] = name
            continue
        if line.strip() and current is not None and not line.startswith(" "):
            current = None
    return found, errors


def reserved_map() -> dict[str, dict[int, str]]:
    expected: dict[str, dict[int, str]] = {"session": {}, "mux": {}}
    for row in ROWS:
        expected[row.direction][row.nibble] = row.name
    return expected


def reserved_problems(found: dict[str, dict[int, str]]) -> list[str]:
    errors = []
    for key, want in reserved_map().items():
        got = found.get(key)
        if got != want:
            errors.append(f"assignment mismatch {key}: {got!r}")
    return errors


def assigned_problems(found: dict[str, dict[int, str]]) -> list[str]:
    errors = []
    for key, want in ASSIGNED.items():
        if key in found and found[key] != want:
            errors.append(f"assignment mismatch {key}: {found[key]!r}")
    return errors


def collision_problems(
    found: dict[str, dict[int, str]],
    fallback: dict[str, dict[int, str]],
) -> list[str]:
    errors = []
    for reserved_key, assigned_key in (("session", "host"), ("mux", "adapter")):
        reserved = found.get(reserved_key)
        if reserved is None:
            continue
        assigned = found.get(assigned_key, fallback[assigned_key])
        for nibble in sorted(set(reserved) & set(assigned)):
            errors.append(
                "collision "
                + reserved_key
                + " "
                + nibble_text(nibble)
                + " "
                + reserved[nibble]
                + " with "
                + assigned_key
                + " "
                + assigned[nibble]
            )
    return errors


def reservation_section(text: str) -> str:
    marker = "## Session extension reservation\n"
    start = text.find(marker)
    if start < 0:
        raise ValueError("missing reservation section")
    body = [marker]
    for line in text[start + len(marker):].splitlines(keepends=True):
        if line.startswith("#"):
            break
        body.append(line)
    return "".join(body)


def clause_problems(text: str) -> list[str]:
    try:
        section = reservation_section(text)
    except ValueError as exc:
        return [str(exc)]
    errors = []
    folded = section.casefold()
    for clause in CLAUSES:
        if clause.casefold() not in folded:
            errors.append("missing clause " + clause)
    if TIME_RE.search(section):
        errors.append("response time stated")
    return errors


def evaluate(text: str, fallback: dict[str, dict[int, str]]) -> list[str]:
    found, errors = parse(text)
    errors.extend(reserved_problems(found))
    errors.extend(assigned_problems(found))
    errors.extend(collision_problems(found, fallback))
    errors.extend(clause_problems(text))
    return errors


def fallback_assigned() -> dict[str, dict[int, str]]:
    found, errors = parse(PAGES[0].read_text(encoding="utf-8"))
    if errors:
        raise AssertionError(errors)
    return {"host": found["host"], "adapter": found["adapter"]}


def move_row(text: str, row: Row) -> str:
    blob = row.line + "\n"
    if text.count(blob) != 1:
        raise AssertionError(blob)
    removed = text.replace(blob, "", 1)
    needle = row.dest_header + "\n"
    if removed.count(needle) != 1:
        raise AssertionError(needle)
    return removed.replace(needle, needle + blob, 1)


def test_pages_accept_the_reservation() -> None:
    fallback = fallback_assigned()
    assert fallback == ASSIGNED
    for page in PAGES:
        text = page.read_text(encoding="utf-8")
        assert evaluate(text, fallback) == []
        for clause in CLAUSES:
            assert text.count(clause) == 1


@pytest.mark.parametrize("page", PAGES, ids=("enh", "conformance"))
@pytest.mark.parametrize("row", ROWS, ids=[row.name for row in ROWS])
def test_renamed_row_is_rejected(page: Path, row: Row) -> None:
    text = page.read_text(encoding="utf-8")
    renamed = f"  {nibble_text(row.nibble)} = {row.name}X\n"
    mutated = text.replace(row.line + "\n", renamed, 1)
    assert mutated != text
    got = evaluate(mutated, fallback_assigned())
    assert any(item.startswith(f"assignment mismatch {row.direction}:") for item in got)
    assert not any(item.startswith(f"assignment mismatch {row.other}:") for item in got)
    assert not any(item.startswith("collision ") for item in got)


@pytest.mark.parametrize("page", PAGES, ids=("enh", "conformance"))
@pytest.mark.parametrize("row", ROWS, ids=[row.name for row in ROWS])
def test_reserved_nibble_collision_is_rejected(page: Path, row: Row) -> None:
    text = page.read_text(encoding="utf-8")
    colliding = f"  0x0 = {row.name}\n"
    mutated = text.replace(row.line + "\n", colliding, 1)
    assert mutated != text
    got = evaluate(mutated, fallback_assigned())
    assert any(item.startswith(f"collision {row.direction} 0x0 ") for item in got)


@pytest.mark.parametrize("page", PAGES, ids=("enh", "conformance"))
@pytest.mark.parametrize("row", ROWS, ids=[row.name for row in ROWS])
def test_direction_move_is_rejected(page: Path, row: Row) -> None:
    text = page.read_text(encoding="utf-8")
    got = evaluate(move_row(text, row), fallback_assigned())
    assert any(item.startswith(f"assignment mismatch {row.direction}:") for item in got)
    assert any(
        item.startswith(f"assignment mismatch {row.other}:")
        or item.startswith("duplicate nibble " + row.other)
        for item in got
    )


def test_assigned_host_nibble_collision_is_rejected() -> None:
    text = PAGES[0].read_text(encoding="utf-8")
    mutated = text.replace("  0x2 = START\n", "  0x4 = START\n", 1)
    got = evaluate(mutated, fallback_assigned())
    assert any(item.startswith("collision session 0x4 ") for item in got)


def test_assigned_adapter_nibble_collision_is_rejected() -> None:
    text = PAGES[0].read_text(encoding="utf-8")
    mutated = text.replace("  0xA = FAILED\n", "  0xD = FAILED\n", 1)
    got = evaluate(mutated, fallback_assigned())
    assert any(item.startswith("collision mux 0xD ") for item in got)


@pytest.mark.parametrize("page", PAGES, ids=("enh", "conformance"))
@pytest.mark.parametrize("clause", CLAUSES)
def test_missing_clause_is_rejected(page: Path, clause: str) -> None:
    text = page.read_text(encoding="utf-8")
    assert text.count(clause) == 1
    got = evaluate(text.replace(clause, "removed", 1), fallback_assigned())
    assert "missing clause " + clause in got


@pytest.mark.parametrize("page", PAGES, ids=("enh", "conformance"))
def test_response_time_is_rejected(page: Path) -> None:
    text = page.read_text(encoding="utf-8")
    mutated = text.replace(
        "Response timing is Unknown.",
        "Response timing is Unknown. Reply within 10 ms.",
        1,
    )
    assert "response time stated" in evaluate(mutated, fallback_assigned())


@pytest.mark.parametrize("page", PAGES, ids=("enh", "conformance"))
def test_extra_unreserved_nibble_is_rejected(page: Path) -> None:
    text = page.read_text(encoding="utf-8")
    mutated = text.replace("Session to mux:\n", "Session to mux:\n  0x9 = EXTRA\n", 1)
    got = evaluate(mutated, fallback_assigned())
    assert any(item.startswith("assignment mismatch session:") for item in got)
