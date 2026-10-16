"""Exercise the published maintenance check against source-fixture drift."""

import csv
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
INDEX = Path("development/b524-provisional-name-evidence.md")
CLASSIFICATIONS = Path("development/b524-provisional-name-gap-classifications.json")
FIXTURES = Path("protocols/vaillant/fixtures")
CANONICAL = FIXTURES / "b524-op02-register-names.csv"
CORRESPONDENCE = FIXTURES / "b524-register-name-correspondence.csv"
MATRIX = FIXTURES / "b524-op02-requester-register-matrix.csv"


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    for relative in (INDEX, CLASSIFICATIONS, CANONICAL, MATRIX, CORRESPONDENCE):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def run_check():
    snippet = INDEX.read_text(encoding="utf-8").split("```python\n", 1)[1].split("```", 1)[0]
    exec(compile(snippet, str(INDEX), "exec"), {})


def change_cell(path, field, value):
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames
        rows = list(reader)
    row = next(
        row for row in rows
        if (row["opcode"], row["group"], row["register"])
        == ("0x02", "0x00", "0x0007")
    )
    row[field] = value
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_b524_provisional_name_evidence_current_sources(checkout, capsys):
    run_check()
    output = capsys.readouterr().out
    assert "Open rows: 142" in output
    assert "Missing: []" in output
    assert "Extra: []" in output


@pytest.mark.parametrize(
    ("path", "field", "value"),
    [
        (CANONICAL, "open_question", "Meaning is not established."),
        (MATRIX, "family", "Other family"),
        (MATRIX, "instance", "dynamic"),
    ],
)
def test_b524_provisional_name_evidence_rejects_source_drift(checkout, path, field, value):
    change_cell(path, field, value)
    with pytest.raises(AssertionError):
        run_check()


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("VRC700 family: 00; VRC720 family: 00", "Unknown"),
        ("Polarity unresolved, so no Boolean name is given:", "Meaning is not established:"),
        ("(functional-module family)", "(different family)"),
    ],
)
def test_b524_provisional_name_evidence_rejects_index_drift(checkout, before, after):
    INDEX.write_text(INDEX.read_text(encoding="utf-8").replace(before, after, 1), encoding="utf-8")
    with pytest.raises(AssertionError):
        run_check()


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("| P |", "| M |"),
        ("| M, P, V |", "| M, V |"),
        ("| M, V, W |", "| M, V |"),
        ("| P |", "| P, X |"),
        ("| P |", "|  |"),
    ],
)
def test_b524_provisional_name_evidence_rejects_gap_drift(checkout, before, after):
    text = INDEX.read_text(encoding="utf-8")
    assert before in text
    INDEX.write_text(text.replace(before, after, 1), encoding="utf-8")
    with pytest.raises(AssertionError):
        run_check()


@pytest.mark.parametrize("gap", ["X", "", "P, X", "P, "])
def test_b524_provisional_name_evidence_rejects_invalid_taxonomy(checkout, gap):
    classifications = json.loads(CLASSIFICATIONS.read_text(encoding="utf-8"))
    classifications[gap] = classifications.pop("P")
    CLASSIFICATIONS.write_text(json.dumps(classifications), encoding="utf-8")
    text = INDEX.read_text(encoding="utf-8")
    INDEX.write_text(text.replace("| P |", f"| {gap} |", 1), encoding="utf-8")
    with pytest.raises(AssertionError, match="invalid gap classification"):
        run_check()


@pytest.mark.parametrize(
    "question",
    ["Value class and encoding are not established.", "Meaning is not established."],
)
def test_b524_provisional_name_evidence_rejects_stale_gap(checkout, question):
    change_cell(CANONICAL, "open_question", question)
    text = INDEX.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("| 0x0007 | `unknown_11` |"):
            cells = line.split("|")
            cells[-2] = f" {question} "
            lines[i] = "|".join(cells)
            break
    else:
        pytest.fail("target row missing")
    INDEX.write_text("".join(lines), encoding="utf-8")
    with pytest.raises(AssertionError):
        run_check()


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("368 OP02 entries and 2 OP06 entries", "369 OP02 entries and 2 OP06 entries"),
        ("368 OP02 entries and 2 OP06 entries", "368 OP02 entries and 3 OP06 entries"),
        ("142 of 368", "143 of 368"),
        ("142 of 368", "142 of 369"),
        ("131 retain documented terms", "132 retain documented terms"),
        ("11 use pre-existing", "12 use pre-existing"),
        ("| 0x02 | 0x00 | 108 |", "| 0x02 | 0x00 | 999 |"),
        ("| 0x02 | 0x09 | 5 |\n", ""),
        ("| 0x02 | 0x09 | 5 |", "| 0x02 | 0x0A | 5 |"),
        ("| 0x02 | 0x09 | 5 |", "| 0x02 | 0x09 | 5 |\n| 0x02 | 0x09 | 5 |"),
    ],
)
def test_b524_provisional_name_evidence_rejects_summary_drift(checkout, before, after):
    text = INDEX.read_text(encoding="utf-8")
    assert before in text
    INDEX.write_text(text.replace(before, after, 1), encoding="utf-8")
    with pytest.raises(AssertionError, match="published"):
        run_check()


def test_b524_provisional_name_evidence_allows_presentation_changes(checkout):
    text = INDEX.read_text(encoding="utf-8")
    text = text.replace("`0=off 1=on`", "0=off   1=on", 1)
    text = text.replace("| M, P, V |", "| `V`,  M, P |", 1)
    text = text.replace("VRC700 family: 00; VRC720 family: 00", "VRC720 family: 00; VRC700 family: 00", 1)
    INDEX.write_text(text, encoding="utf-8")
    run_check()


@pytest.mark.parametrize("opcode", ["0x02", "0x06"])
@pytest.mark.parametrize("mutation", ["add", "remove"])
def test_b524_provisional_name_evidence_rejects_correspondence_drift(checkout, opcode, mutation):
    with CORRESPONDENCE.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames
        rows = list(reader)
    row = next(row for row in rows if row["opcode"] == opcode)
    if mutation == "add":
        rows.append(dict(row))
    else:
        rows.remove(row)
    with CORRESPONDENCE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(AssertionError, match="published correspondence totals differ"):
        run_check()
