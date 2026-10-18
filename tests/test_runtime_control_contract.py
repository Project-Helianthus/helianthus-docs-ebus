import json
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


SNAPSHOT_EXAMPLE = next(
    t.content for t in checker.MarkdownIt().parse(
        DOCUMENTS[checker.API].split("## `DriverSnapshotV1`", 1)[1].split("### Field Invariants", 1)[0]
    ) if t.type == "fence" and t.info.strip() == "json"
)
# Independent expected sets ensure removing a member from the checker is caught.
SNAPSHOT_FIELDS = (
    "schema_version", "driver_id", "desired_state", "observed_state", "reason",
    "retry", "generation", "desired_revision", "revision", "attempt",
    "capabilities", "effective_capabilities", "safety_quarantined", "changed_at_utc",
)
SHAPE_FIELDS = [(None, SNAPSHOT_FIELDS), ("reason", ("code", "retryable")),
                ("retry", ("eligible", "budget_remaining", "not_before_utc"))]


def snapshot_documents(snapshot) -> dict[str, str]:
    documents = dict(DOCUMENTS)
    documents[checker.API] = documents[checker.API].replace(
        SNAPSHOT_EXAMPLE, json.dumps(snapshot) + "\n", 1)
    return documents


@pytest.mark.parametrize(("parent", "field"), [
    (parent, field) for parent, fields in SHAPE_FIELDS for field in fields
])
def test_runtime_control_contract_snapshot_requires_every_member(parent, field) -> None:
    snapshot = json.loads(SNAPSHOT_EXAMPLE)
    target = snapshot if parent is None else snapshot[parent]
    del target[field]
    assert checker.validate(snapshot_documents(snapshot))


@pytest.mark.parametrize("parent", [None, "reason", "retry"])
def test_runtime_control_contract_snapshot_rejects_unknown_members(parent) -> None:
    snapshot = json.loads(SNAPSHOT_EXAMPLE)
    target = snapshot if parent is None else snapshot[parent]
    target["debug"] = True
    assert checker.validate(snapshot_documents(snapshot))


@pytest.mark.parametrize(("parent", "value"), [
    (parent, value) for parent in [None, "reason", "retry"]
    for value in [[], "invalid", 1, True, None]
    if parent != "retry" or value is not None
])
def test_runtime_control_contract_snapshot_requires_objects(parent, value) -> None:
    snapshot = json.loads(SNAPSHOT_EXAMPLE)
    if parent is None:
        snapshot = value
    else:
        snapshot[parent] = value
    assert checker.validate(snapshot_documents(snapshot))


def test_runtime_control_contract_snapshot_allows_null_retry_and_reordered_members() -> None:
    snapshot = json.loads(SNAPSHOT_EXAMPLE)
    snapshot["retry"] = None
    snapshot["reason"] = dict(reversed(list(snapshot["reason"].items())))
    snapshot = dict(reversed(list(snapshot.items())))
    assert checker.validate(snapshot_documents(snapshot)) == []


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
    ("load it empty or reinterpret it as missing", "load it empty and reinterpret it as missing"),
    ("START takes the reserved slot as a typed START replacement", "START returns TRANSITION_BUSY"),
    ("is never used for optimistic control", "is used for optimistic control"),
    ("| 6 | `ExpectedRevision` differs", "| 5 | `ExpectedRevision` differs"),
    ("| `TRANSITION_BUSY` | Yes |", "| `PERMISSION_DENIED` | Yes |"),
    ("| CTL-15 |", "| CTL-16 |"),
    ("Final D4 removes G5 lifecycle principal/authorization checks", "Final D4 keeps lifecycle checks"),
    ("carry no principal and no authorization", "carry a principal and an authorization"),
    ("Observation-only changes do not", "Observation-only changes do"),
    ("`STOPPED` and is not started until a new start decision is accepted",
     "`STOPPED` and is started without a new start decision"),
    ("whose durable desired state is\n  `RUNNING`", "whose durable desired state is\n  `RUNNING` or `STOPPED`"),
    ("STOPPED   --start-->    STARTING", "DISABLED  --start-->    STARTING\nSTOPPED   --start-->    STARTING"),
    ("The normative textual forms include `STARTING -> RUNNING`",
     "The normative textual forms include `DISABLED` -> `STARTING`, `STARTING -> RUNNING`"),
    ("| CTL-17 |", "| CTL-16 |"),
    ("readback agreement alone never reopens admission. A failed", "readback agreement reopens admission. A failed"),
    ("fsync of the temp file, rename refused) is discarded",
     "fsync of the temp file, rename refused, or parent-directory durability not established) is discarded"),
    ("including a failed\n  parent-directory fsync after a successful rename), the service",
     "), the service"),
    ("staging is not treated as discarded", "staging is discarded"),
    ("and readback agrees with the cached view, and\n  readback agreement alone", "and readback agrees with the cached view, and\n  readback agreement"),
    ("Directory durability is established, never inferred.", "Directory durability is inferred from readback."),
    ("readback agreement alone never reopens admission.", "readback agreement reopens admission."),
    ('"ExpectedRevision": "7"', '"ExpectedRevision": "0"'),
    ('"ExpectedRevision": "7"', '"ExpectedRevision": 7'),
    ('"ExpectedRevision": "7"', '"ExpectedRevision": "07"'),
    ('"ExpectedRevision": "7"', '"ExpectedRevision": "18446744073709551616"'),
    ('"ExpectedRevision": "7"', '"ExpectedRevision": "7", "request_id": "example"'),
    ('"ExpectedRevision": "7"', '"ExpectedRevision": "7", "idempotency_key": "example"'),
    ('"ExpectedRevision": "7"', '"ExpectedRevision": "7", "ExpectedRevision": "8"'),
    ('"desired_revision": "8"', '"desired_revision": "8", "operation_id": "example"'),
    ('"desired_revision": "8"', '"desired_revision": "8", "disposition": "ACCEPTED"'),
    ('"desired_revision": "8"', '"desired_revision": "8", "completed": false'),
    ('"desired_revision": "8"', '"revision": "8"'),
    ('"desired_revision": "7"', '"desired_revision": 7'),
    ('"desired_revision": "7"', '"desired_revision": "7", "principal": "operator"'),
    ('"revision": "29"', '"revision": 29'),
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
    target.write_text(DOCUMENTS[checker.API].replace('"desired_revision": "8"', '"desired_revision": 8'))
    invalid = subprocess.run(command, capture_output=True, text=True)
    assert invalid.returncode == 1
    assert "invalid closed request/result examples" in invalid.stderr


def test_runtime_control_contract_registered_in_local_gate() -> None:
    gate = (checker.ROOT / "scripts/ci_local.sh").read_text(encoding="utf-8")
    assert "python3 scripts/check_runtime_control_contract.py\n" in gate
    assert "python3 -m pytest -q tests/test_runtime_control_contract.py\n" in gate
