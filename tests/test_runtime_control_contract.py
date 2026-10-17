from pathlib import Path
import subprocess
import sys

import pytest

from scripts import check_runtime_control_contract as checker


DOCUMENTS = {r["path"]: (checker.ROOT / r["path"]).read_text(encoding="utf-8")
             for r in checker.RULES}
OBLIGATIONS = [(r["path"], clause) for r in checker.RULES for clause in r["required"]]


def test_runtime_control_contract_repository() -> None:
    assert checker.validate(DOCUMENTS) == []


@pytest.mark.parametrize(("path", "clause"), OBLIGATIONS)
@pytest.mark.parametrize("wrapper", ["", "<!--\n{}\n-->", "```text\n{}\n```", "<pre>\n\n{}\n\n</pre>"])
def test_runtime_control_contract_missing_or_non_normative(path, clause, wrapper) -> None:
    documents = dict(DOCUMENTS)
    assert clause in documents[path]
    documents[path] = documents[path].replace(clause, wrapper.format(clause))
    assert checker.validate(documents)


@pytest.mark.parametrize(("before", "after"), [
    ("catalog revision `C + 1`", "catalog revision 1"),
    ("`H + 1` through", "`1` through"),
    ("a changing START occupies the current slot as typed START", "a changing START has no typed slot"),
    ("FAILED_PRECONDITION before TRANSITION_BUSY", "TRANSITION_BUSY before FAILED_PRECONDITION"),
    ("never drop it or reinterpret it as missing", "drop it and reinterpret it as missing"),
    ("Observation-only changes do not advance it", "Observation-only changes advance it"),
    ('"ExpectedRevision": "7"', '"ExpectedRevision": "0"'),
    ('"ExpectedRevision": "7"', '"ExpectedRevision": 7'),
    ('"ExpectedRevision": "7"', '"ExpectedRevision": "07"'),
    ('"ExpectedRevision": "7"', '"ExpectedRevision": "18446744073709551616"'),
    ('"ExpectedRevision": "7"', '"ExpectedRevision": "7", "request_id": "example"'),
    ('"ExpectedRevision": "7"', '"ExpectedRevision": "7", "idempotency_key": "example"'),
    ('"ExpectedRevision": "7"', '"ExpectedRevision": "7", "ExpectedRevision": "8"'),
    ('"revision": "8"', '"revision": "8", "operation_id": "example"'),
    ('"revision": "8"', '"revision": "8", "disposition": "ACCEPTED"'),
    ('"revision": "8"', '"revision": "8", "completed": false'),
    ('"revision": "7"', '"revision": 7'),
    ('"catalog_revision": "29"', '"catalog_revision": 29'),
    ('"manager_revision": "29"', '"manager_revision": 29'),
])
def test_runtime_control_contract_rejects_regressions(before, after) -> None:
    documents = {p: s.replace(before, after) for p, s in DOCUMENTS.items()}
    assert documents != DOCUMENTS
    assert checker.validate(documents)


def test_runtime_control_contract_ignores_prose_wrapping() -> None:
    documents = dict(DOCUMENTS)
    for rule in checker.RULES:
        for clause in rule["required"]:
            if not clause.startswith("|"):
                documents[rule["path"]] = documents[rule["path"]].replace(
                    clause, checker.normalize(clause))
    assert checker.validate(documents) == []


def test_runtime_control_contract_cli(tmp_path: Path) -> None:
    command = [sys.executable, str(checker.ROOT / "scripts/check_runtime_control_contract.py"),
               "--root", str(tmp_path)]
    assert subprocess.run(command, capture_output=True).returncode == 1
    for path, text in DOCUMENTS.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    valid = subprocess.run(command, capture_output=True, text=True)
    assert valid.returncode == 0, valid.stderr
    assert "documentation only" in valid.stdout
    target = tmp_path / checker.API
    target.write_text(DOCUMENTS[checker.API].replace('"revision": "8"', '"revision": 8'))
    invalid = subprocess.run(command, capture_output=True, text=True)
    assert invalid.returncode == 1
    assert "invalid closed request/result examples" in invalid.stderr


def test_runtime_control_contract_registered_in_local_gate() -> None:
    gate = (checker.ROOT / "scripts/ci_local.sh").read_text(encoding="utf-8")
    assert "python3 scripts/check_runtime_control_contract.py\n" in gate
    assert "python3 -m pytest -q tests/test_runtime_control_contract.py\n" in gate
