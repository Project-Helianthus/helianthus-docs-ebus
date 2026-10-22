import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

from scripts import check_runtime_control_contract as checker


DOCUMENTS = {r["path"]: (checker.ROOT / r["path"]).read_text(encoding="utf-8")
             for r in checker.RULES}
OBLIGATIONS = [(r["path"], clause) for r in checker.RULES for clause in r["required"]]
BRIDGE_START = "### S4/S6/S7 synthetic acceptance obligations"
BRIDGE_RULE = next(r for r in checker.RULES if r["start"] == BRIDGE_START)
RESET_PATH = "architecture/runtime-control-reset-durability.md"
RESET_START = "## Required ordering and failure outcomes"
RESET_RULE = next(r for r in checker.RULES if r["path"] == RESET_PATH)
QUARANTINE_DIRECTORY_ROW = next(
    line for line in DOCUMENTS[RESET_PATH].splitlines() if line.startswith("| 4 |")
)


def test_runtime_control_contract_repository() -> None:
    assert checker.validate(DOCUMENTS) == []


TABLE_GAPS = [
    (table, boundary, error)
    for marker, error in (
        ("| Case | Required read result |", "invalid unavailable-read case table"),
        ("| 1 |", "refusal table order or codes changed"),
        ("| CTL-01 / CTL-02 |", "CTL vector ids changed:"),
    )
    for table in re.findall(r"^\|.*(?:\n\|.*)*", DOCUMENTS[checker.LIFECYCLE], re.MULTILINE)
    if marker in table
    for boundary in range(1, len(table.splitlines()))
]


@pytest.mark.parametrize(("table", "boundary", "error"), TABLE_GAPS)
@pytest.mark.parametrize("blank", ["", " \t"])
def test_runtime_control_contract_rejects_table_gaps(table, boundary, error, blank) -> None:
    documents = dict(DOCUMENTS)
    lines = table.splitlines()
    lines.insert(boundary, blank)
    documents[checker.LIFECYCLE] = documents[checker.LIFECYCLE].replace(
        table, "\n".join(lines), 1)
    assert any(message.startswith(f"{checker.LIFECYCLE}: {error}")
               for message in checker.validate(documents))


UNAVAILABLE_CLAUSES = [
    (rule["path"], rule["start"], rule["end"], clause)
    for rule in checker.RULES for clause in rule["required"]
    if clause.startswith(("If either the namespace issued-revision", "With both counters valid",
                          "Keep the HTTP/API/health shell", "Synthetic read acceptance",
                          "This ordered table governs mutations", "The list/get data shapes above",
                          "For list/get, the `UNAVAILABLE` row"))
]


@pytest.mark.parametrize(("path", "start", "end", "clause"), UNAVAILABLE_CLAUSES)
@pytest.mark.parametrize("change", ["weakened", "before", "after"])
def test_runtime_control_contract_unavailable_obligation_scope(path, start, end, clause, change) -> None:
    documents = dict(DOCUMENTS)
    before, section = documents[path].split(start, 1)
    section, after = section.split(end, 1)
    assert clause in section
    section = section.replace(clause, clause + " Optional." if change == "weakened" else "")
    if change == "before":
        before += clause + "\n\n"
    elif change == "after":
        after = "\n\n" + clause + after
    documents[path] = before + start + section + end + after
    assert checker.validate(documents)


@pytest.mark.parametrize("change", ["removed", "weakened", "before", "after", "reordered"])
def test_runtime_control_contract_quarantine_directory_prerequisite(change) -> None:
    documents = dict(DOCUMENTS)
    text = documents[RESET_PATH]
    row = QUARANTINE_DIRECTORY_ROW
    assert row in RESET_RULE["required"]
    if change == "weakened":
        text = text.replace(row, row.replace("Successfully fsync", "Optionally fsync"))
    elif change == "reordered":
        following = next(line for line in text.splitlines() if line.startswith("| 5 |"))
        assert row + "\n" + following in text
        text = text.replace(row + "\n" + following, following + "\n" + row)
    else:
        text = text.replace(row, "")
        if change == "before":
            text = text.replace(RESET_START, row + "\n\n" + RESET_START)
        elif change == "after":
            text += "\n\n" + row
    documents[RESET_PATH] = text
    errors = checker.validate(documents)
    assert any(error.startswith(RESET_PATH + ": ") for error in errors)


@pytest.mark.parametrize("location", ["before", "within", "after"])
@pytest.mark.parametrize("addition", [
    "Order 4 may be skipped.",
    "| 8 | Quarantine directory fsync is optional. | Continue replacement. |",
    QUARANTINE_DIRECTORY_ROW,
])
def test_runtime_control_contract_rejects_added_reset_units(location, addition) -> None:
    documents = dict(DOCUMENTS)
    text = documents[RESET_PATH]
    if location == "before":
        text = text.replace(RESET_START, RESET_START + "\n\n" + addition, 1)
    elif location == "within":
        text = text.replace(QUARANTINE_DIRECTORY_ROW,
                            addition + "\n\n" + QUARANTINE_DIRECTORY_ROW, 1)
    else:
        text = text.replace(RESET_RULE["end"], addition + "\n\n" + RESET_RULE["end"], 1)
    documents[RESET_PATH] = text
    assert (f"{RESET_PATH}: unexpected contract content in {RESET_START}"
            in checker.validate(documents))


def test_runtime_control_contract_requires_reset_supplement(tmp_path: Path) -> None:
    for path, text in DOCUMENTS.items():
        if path == RESET_PATH:
            continue
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(checker.ROOT / "scripts/check_runtime_control_contract.py"),
         "--root", str(tmp_path)], capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert RESET_PATH in result.stderr


EXAMPLE_SECTIONS = [
    (checker.MCP, "### Read and mutation data",
     "### Envelope, lifecycle errors and acceptance vectors", "invalid G5 closed data examples"),
    (checker.API, "## Mutating Tools", "### Unproven-close",
     "invalid closed request/result examples"),
    (checker.API, "## `DriverSnapshotV1`", "### Field Invariants",
     "invalid revision example in ## `DriverSnapshotV1`"),
    (checker.API, "## `drivers.v1.list`", "## Mutating Tools",
     "invalid revision example in ## `drivers.v1.list`"),
]


@pytest.mark.parametrize(("path", "start", "end", "error"), EXAMPLE_SECTIONS)
@pytest.mark.parametrize("info", ["json", "json example", "text", ""])
@pytest.mark.parametrize("fence", ["```", "~~~"])
def test_runtime_control_contract_rejects_extra_fences(path, start, end, error, info, fence) -> None:
    documents = dict(DOCUMENTS)
    documents[path] = documents[path].replace(
        start, start + f'\n\n{fence}{info}\n{{"receipt":"unexpected"}}\n{fence}', 1)
    assert f"{path}: {error}" in checker.validate(documents)


@pytest.mark.parametrize(("path", "start", "end", "error"), EXAMPLE_SECTIONS)
@pytest.mark.parametrize("info", ["json example", "json\texample", " json "])
def test_runtime_control_contract_accepts_json_info_variants(path, start, end, error, info) -> None:
    documents = dict(DOCUMENTS)
    before, section = documents[path].split(start, 1)
    section, after = section.split(end, 1)
    documents[path] = before + start + section.replace("```json", "```" + info) + end + after
    assert checker.validate(documents) == []


@pytest.mark.parametrize("clause", BRIDGE_RULE["required"])
@pytest.mark.parametrize("change", ["weakened", "before", "after"])
def test_runtime_control_contract_bridge_obligation_scope(clause, change) -> None:
    documents = dict(DOCUMENTS)
    text = documents[checker.LIFECYCLE]
    assert clause in text
    if change == "weakened":
        # Preserve every original keyword while making the obligation optional.
        replacement = (clause[:-1] + " Optional. |" if clause.startswith("|")
                       else clause + " Optional.")
        text = text.replace(clause, replacement)
    else:
        text = text.replace(clause, "")
        if change == "before":
            text = text.replace(BRIDGE_START, clause + "\n\n" + BRIDGE_START)
        else:
            text += "\n\n" + clause
    documents[checker.LIFECYCLE] = text
    errors = checker.validate(documents)
    assert any("changed obligation: " + checker.normalize(clause)[:100] in error
               for error in errors)


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
    ("| CTL-19 |", "| CTL-18 |"),
    ("only a driver with no record compares against\n   the re-read mark", "every driver compares against the re-read mark"),
    ("and is accepted at `H + 2`", "and is refused with REVISION_CONFLICT"),
    (", where `H <= 2^64 - 3` leaves room for two increments", ""),
    ("`H <= 2^64 - 3`", "`H <= 2^64 - 2`"),
    ("If A commits first, A is accepted at `H + 1` and B is refused with REVISION_CONFLICT and no mutation.",
     "If A commits first, both requests are accepted at `H + 1`."),
    ("conflicts before the same-desired no-op check", "returns a same-desired no-op"),
    ("Take the single namespace-wide serialization point (the sole writer of the\n   control namespace, which is the shared-mark lock) for every request, never a\n   serializer scoped to one driver.",
     "Under the per-driver decision serializer,"),
    ("Take the single namespace-wide serialization point (the sole writer of the\n   control namespace, which is the shared-mark lock) for every request, never a\n   serializer scoped to one driver.",
     "Take a per-driver serialization lock for each request."),
    ("A request\n   that waited for the point re-reads the mark after acquiring it for allocation,\n   never using an earlier read.",
     "A request that waited compares against the mark it read earlier."),
    ("Still under the step 2 serialization point, check transition capacity,",
     "Check transition capacity,"),
    ("never decided against a mark read before the wait", "decided against the mark read earlier"),
    ("| 8 | The decision path is busy: the typed transition slot is full or the namespace-wide decision serialization point was held beyond the bounded wait |",
     "| 8 | No free typed transition slot |"),
    ("an expired deadline is refused with\n   `DEADLINE_EXCEEDED` (row 5) before the revision comparison and before the\n   same-desired no-op path, so neither `REVISION_CONFLICT` nor a no-op success\n   is returned past the deadline.",
     "the revision is compared first."),
    ("After the step 2 deadline recheck and revision comparison, START while",
     "START while"),
    ("An `ExpectedRevision`\n   below that value is conclusively stale", "An `ExpectedRevision`\n   below the mark is conclusively stale"),
    ("`TRANSITION_BUSY`\n   never reports an outcome of the revision comparison.", "`TRANSITION_BUSY`\n   reports a revision mismatch."),
    ("`TRANSITION_BUSY` means the decision\npath is busy: the typed transition slot is full or the namespace-wide decision\nserialization point was held beyond the bounded wait; it never reports an\noutcome of the revision comparison.",
     "`TRANSITION_BUSY` when capacity is\nunavailable."),
    ("A request that acquires the serialization\npoint after its deadline expired is refused with `DEADLINE_EXCEEDED` before the\nrevision comparison and the same-desired no-op test.", ""),
    ("with TRANSITION_BUSY when the decision path is busy (the typed slot is full or the\nnamespace-wide serialization point was held beyond the bounded wait; it never\nreports a revision-comparison outcome).",
     "with TRANSITION_BUSY when capacity is unavailable."),
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


@pytest.mark.parametrize(("before", "after"), [
    ("helianthus.runtime.list` |", "helianthus.runtime.enumerate` |"),
    ("`List()`", "`ListDrivers()`"),
    ('`{"DriverID":"ebus.primary"}`', '`{"driver_id":"ebus.primary"}`'),
    ("Detect duplicates before decoding can discard them.", "Ignore duplicates."),
    ("Normally `data` is null", "Normally `data` is empty"),
    ("`isError: true`", "`isError: false`"),
    ("| `UNAVAILABLE` | Persistence failure", "| `INTERNAL` | Persistence failure"),
    ('"catalog_revision": "29"', '"catalog_revision": 29'),
    ('"revision": "29"', '"revision": "28"'),
    ('"enabled": true', '"enabled": 1'),
    ('"reason": "RETRY_SCHEDULED",', '"reason": "RETRY_SCHEDULED", "extra": true,'),
    ('{"desired_state":"RUNNING","desired_revision":"8"}',
     '{"desired_state":"RUNNING","desired_revision":8}'),
    ('{"desired_state":"RUNNING","desired_revision":"8"}',
     '{"desired_state":"RUNNING","desired_revision":"8","receipt":"x"}'),
    ('{"desired_state":"RUNNING","desired_revision":"8"}',
     '{"desired_state":"RUNNING","desired_revision":"8","desired_revision":"9"}'),
])
def test_runtime_control_contract_mcp_rejects_wire_drift(before, after) -> None:
    documents = dict(DOCUMENTS)
    assert before in documents[checker.MCP]
    documents[checker.MCP] = documents[checker.MCP].replace(before, after, 1)
    assert any(checker.MCP in error for error in checker.validate(documents))


def test_runtime_control_contract_mcp_rejects_extra_tool() -> None:
    documents = dict(DOCUMENTS)
    row = '| `helianthus.runtime.list` | `{}` | `List()` |'
    documents[checker.MCP] = documents[checker.MCP].replace(
        row, row + '\n| `helianthus.runtime.delete` | `{}` | `Delete()` |')
    assert any("unexpected contract content" in error for error in checker.validate(documents))


@pytest.mark.parametrize(("path", "clause"), [
    (rule["path"], clause)
    for rule in checker.RULES if rule.get("exact")
    for clause in rule["required"]
])
@pytest.mark.parametrize("whitespace_variant", [False, True])
def test_runtime_control_contract_rejects_duplicate_exact_units(path, clause, whitespace_variant) -> None:
    documents = dict(DOCUMENTS)
    duplicate = checker.normalize(clause).replace(" ", "  ") if whitespace_variant else clause
    separator = "\n" if clause.startswith("|") else "\n\n"
    documents[path] = documents[path].replace(clause, clause + separator + duplicate, 1)
    assert any("unexpected contract content" in error for error in checker.validate(documents))


@pytest.mark.parametrize(("path", "start", "end", "row"), [
    (rule["path"], rule["start"], rule["end"], clause)
    for rule in checker.RULES
    for clause in rule["required"] if clause.startswith("|")
])
@pytest.mark.parametrize("indent", ["    ", "\t"])
def test_runtime_control_contract_rejects_indented_table_rows(path, start, end, row, indent) -> None:
    documents = dict(DOCUMENTS)
    before, section = documents[path].split(start, 1)
    section, after = section.split(end, 1)
    assert row in section
    documents[path] = before + start + section.replace(row, indent + row, 1) + end + after
    assert checker.validate(documents)


@pytest.mark.parametrize("value", ["0", "1", "18446744073709551615"])
def test_runtime_control_contract_mcp_issued_catalog_revision(value) -> None:
    documents = dict(DOCUMENTS)
    documents[checker.MCP] = documents[checker.MCP].replace(
        '"catalog_revision": "29"', f'"catalog_revision": "{value}"', 1).replace(
        '"revision": "29"', f'"revision": "{value}"', 1)
    errors = checker.validate(documents)
    if value == "0":
        assert f"{checker.MCP}: invalid G5 closed data examples" in errors
    else:
        assert errors == []


def test_runtime_control_contract_mcp_allows_reordered_json_members() -> None:
    documents = dict(DOCUMENTS)
    documents[checker.MCP] = documents[checker.MCP].replace(
        '{"desired_state":"RUNNING","desired_revision":"8"}',
        '{"desired_revision": "8", "desired_state": "RUNNING"}')
    assert checker.validate(documents) == []


@pytest.mark.parametrize(("path", "first", "second"), [
    (rule["path"], first, second)
    for rule in checker.RULES if rule.get("exact")
    for first, second in zip(rule["required"], rule["required"][1:])
])
def test_runtime_control_contract_rejects_reordered_exact_units(path, first, second) -> None:
    documents = dict(DOCUMENTS)
    text = documents[path]
    first_at = text.index(first)
    second_at = text.index(second, first_at + len(first))
    documents[path] = (text[:first_at] + second + text[first_at + len(first):second_at]
                       + first + text[second_at + len(second):])
    assert any("unexpected contract content" in error for error in checker.validate(documents))


@pytest.mark.parametrize(("before", "after"), [
    ("every ordinary MCP transport the gateway offers (HTTP today)",
     "ordinary MCP HTTP and stdio transports"),
    ("every ordinary MCP transport the gateway offers (HTTP\ntoday)",
     "HTTP/stdio"),
    ("members, non-object inputs and non-string values with",
     "members, non-object inputs, non-string values and trailing JSON with"),
    ("transport-level rejection of trailing data", "trailing JSON refusal"),
    ("A request body with trailing data is rejected at the transport as an invalid\n"
     "request before any tool runs; `arguments` cannot carry trailing data.", ""),
])
def test_runtime_control_contract_mcp_rejects_transport_drift(before, after) -> None:
    documents = dict(DOCUMENTS)
    assert before in documents[checker.MCP]
    documents[checker.MCP] = documents[checker.MCP].replace(before, after, 1)
    assert any(checker.MCP in error for error in checker.validate(documents))


def test_runtime_control_contract_lifecycle_offered_transports() -> None:
    text = checker.normalize(DOCUMENTS[checker.LIFECYCLE])
    assert ("Discover and dispatch all five through every ordinary MCP transport the gateway "
            "offers (HTTP today) with eeBUS disabled or absent") in text


@pytest.mark.parametrize(("path", "before", "after"), [
    (checker.API, "It is not an implementation or acceptance target.",
     "It is the implementation and acceptance target."),
    (checker.MANAGER, "`helianthus.runtime.{list,get,start,stop,restart}`",
     "`drivers.v1.{list,start,stop,restart}`"),
    (checker.MANAGER, "The historical `drivers.v1.*` tools are not delivery requirements.",
     "The `drivers.v1.*` tools are delivery requirements."),
    (checker.LIFECYCLE, "duplicate member rejection and finite context",
     "duplicate/trailing JSON rejection and finite context"),
    (checker.LIFECYCLE, "outside the service refusal sequence",
     "inside the service refusal sequence"),
    (checker.LIFECYCLE, "non-digits) | `INVALID_ARGUMENT`",
     "non-digits), trailing JSON | `INVALID_ARGUMENT`"),
])
def test_runtime_control_contract_rejects_obsolete_authority_and_body_refusal(path, before, after) -> None:
    documents = dict(DOCUMENTS)
    assert before in documents[path]
    documents[path] = documents[path].replace(before, after, 1)
    assert any(path in error for error in checker.validate(documents))


@pytest.mark.parametrize("replacement", [
    "", "## Renamed G5 contract", "### G5 runtime lifecycle MCP contract (D4)",
    "## G5 runtime lifecycle MCP contract (D4) renamed",
    "<!--\n## G5 runtime lifecycle MCP contract (D4)\n-->",
    "```text\n## G5 runtime lifecycle MCP contract (D4)\n```",
    "## G5 runtime lifecycle MCP contract (D4)\n\n## G5 runtime lifecycle MCP contract (D4)",
])
def test_runtime_control_contract_requires_g5_owning_heading(replacement) -> None:
    documents = dict(DOCUMENTS)
    documents[checker.MCP] = documents[checker.MCP].replace(
        "## G5 runtime lifecycle MCP contract (D4)", replacement, 1)
    assert any("invalid owning section" in error for error in checker.validate(documents))


@pytest.mark.parametrize("subsection", [
    "### Ordinary discovery and dispatch",
    "### Closed inputs and exact service delegation",
    "### Read and mutation data",
    "### Envelope, lifecycle errors and acceptance vectors",
])
def test_runtime_control_contract_g5_subsections_stay_under_owner(subsection) -> None:
    documents = dict(DOCUMENTS)
    documents[checker.MCP] = documents[checker.MCP].replace(
        subsection, "## Unrelated contract\n\n" + subsection, 1)
    assert any("invalid owning section" in error for error in checker.validate(documents))


def test_runtime_control_contract_lifecycle_implementation_status() -> None:
    opening = checker.normalize(DOCUMENTS[checker.LIFECYCLE].split("\n## ", 1)[0])
    assert "A5 is implemented as an internal service for lifecycle-only `ebus.primary` only" in opening
    assert "The first external ordinary-MCP contract below is pending gateway PR 2." in opening
    assert "This page claims no hardware validation or universal provider SPI." in opening


@pytest.mark.parametrize(("before", "after"), [
    ("A5 is implemented as an internal service for `ebus.primary` only",
     "A5 is not implemented as an internal service"),
    ("not a\nuniversal provider SPI", "a universal provider SPI"),
    ("the external ordinary-MCP slice remains pending",
     "the external ordinary-MCP slice has shipped"),
])
def test_runtime_control_contract_rejects_lifecycle_status_drift(before, after) -> None:
    documents = dict(DOCUMENTS)
    assert before in documents[checker.LIFECYCLE]
    documents[checker.LIFECYCLE] = documents[checker.LIFECYCLE].replace(before, after, 1)
    assert any(checker.LIFECYCLE in error for error in checker.validate(documents))


@pytest.mark.parametrize(("before", "after"), [
    ("each accepted `RESTART` advances desired revision",
     "each accepted `RESTART` may reuse desired revision"),
    ("increments generation exactly once", "increments generation at least once"),
    ("retrying the old expected revision returns\n  `REVISION_CONFLICT`",
     "retrying the old expected revision succeeds"),
    ("a valid fresh-revision `RESTART` after settlement\n  requests another replacement and is never deduplicated",
     "a valid fresh-revision `RESTART` after settlement may be deduplicated"),
    ("they allocate no revision or work and do not reset retry budgets or quarantine",
     "they may allocate work or reset retry budgets or quarantine"),
    ("There is no lifecycle GraphQL API, resolver, mutation or subscription.",
     "A later gate adds equivalent lifecycle GraphQL snapshots and mutations."),
    ("this\n   page requires no downstream lifecycle routes or controls",
     "this page requires downstream lifecycle routes and controls"),
    ("no lifecycle GraphQL surface is added", "lifecycle GraphQL parity is required"),
    ("including untyped bootstrap\nreconciliation and manager retry attempts",
     "only for typed transitions"),
])
def test_runtime_control_contract_rejects_manager_acceptance_drift(before, after) -> None:
    documents = dict(DOCUMENTS)
    assert before in documents[checker.MANAGER]
    documents[checker.MANAGER] = documents[checker.MANAGER].replace(before, after, 1)
    assert any(checker.MANAGER in error for error in checker.validate(documents))


@pytest.mark.parametrize("field", [
    "incarnation", "source", "epoch", "generation", "admission identity", "operation correlation",
])
@pytest.mark.parametrize("section", ["## Retry And Recovery", "## Stop, Drain, And Restart"])
def test_runtime_control_contract_requires_full_callback_correlation(field, section) -> None:
    documents = dict(DOCUMENTS)
    before, body = documents[checker.MANAGER].split(section, 1)
    body, after = body.split("\n## ", 1)
    assert field in body
    documents[checker.MANAGER] = before + section + body.replace(field, "omitted") + "\n## " + after
    assert any(checker.MANAGER in error for error in checker.validate(documents))


def test_runtime_control_contract_acceptance_cannot_move_before_heading() -> None:
    documents = dict(DOCUMENTS)
    heading = "## One-release Acceptance"
    before, acceptance = documents[checker.MANAGER].split(heading, 1)
    documents[checker.MANAGER] = before + acceptance + heading + "\n"
    assert any(checker.MANAGER in error for error in checker.validate(documents))


UNAVAILABLE_SECTION = "### Envelope, lifecycle errors and acceptance vectors"
UNAVAILABLE_PRECEDENCE = next(
    clause for rule in checker.RULES if rule["path"] == checker.MCP
    for clause in rule["required"] if clause.startswith("For get, the existing driver-ID")
)
UNAVAILABLE_CASE_RULE = next(
    rule for rule in checker.RULES
    if rule["start"] == "### Unavailable reads with invalid durable bounds"
)
UNAVAILABLE_CASE_ROWS = [
    clause for clause in UNAVAILABLE_CASE_RULE["required"]
    if clause.startswith("| ") and not clause.startswith("| Case |")
]


@pytest.mark.parametrize("disposition", ["unreadable", "unsupported"])
def test_runtime_control_contract_unavailable_load_dispositions(disposition) -> None:
    row = (f"| Control namespace {disposition} | "
           "`UNAVAILABLE`, null data, no usable revision |")
    assert row in UNAVAILABLE_CASE_ROWS
    assert DOCUMENTS[checker.LIFECYCLE].count(row) == 1
    for bound in ("Issued bound", "Catalog revision"):
        impossible_row = f"| {bound} {disposition} |"
        assert not any(clause.startswith(impossible_row) for clause in UNAVAILABLE_CASE_ROWS)
        documents = dict(DOCUMENTS)
        documents[checker.LIFECYCLE] = documents[checker.LIFECYCLE].replace(
            row, row.replace("Control namespace", bound), 1)
        assert (f"{checker.LIFECYCLE}: invalid unavailable-read case table"
                in checker.validate(documents))


@pytest.mark.parametrize("bound", ["Issued bound", "Catalog revision"])
@pytest.mark.parametrize(("disposition", "suffix"), [
    ("missing with existing control material", "; no bootstrap"),
    ("malformed", ""),
    ("above the unsigned 64-bit maximum", "; no wrap"),
])
def test_runtime_control_contract_unavailable_per_bound_cases(bound, disposition, suffix) -> None:
    row = (f"| {bound} {disposition} | "
           f"`UNAVAILABLE`, null data, no usable revision{suffix} |")
    assert row in UNAVAILABLE_CASE_ROWS
    assert DOCUMENTS[checker.LIFECYCLE].count(row) == 1


def unavailable_examples(text):
    section = text.split(UNAVAILABLE_SECTION, 1)[1].split("\n## ", 1)[0]
    return [token.content for token in checker.MarkdownIt().parse(section)
            if token.type == "fence"]


@pytest.mark.parametrize("index", [0, 1])
@pytest.mark.parametrize("change", [
    "is_error_true", "is_error_false", "retriable", "data", "success_catalog", "code", "hash",
    "extra", "removed", "nested_revision", "duplicate_member", "source_layer",
    "meta_extra", "error_extra", "contract_extra", "consistency_extra", "clock",
    "invalid_json", "hash_missing", "hash_string", "hash_concrete",
])
def test_runtime_control_contract_unavailable_envelope_mutations(index, change) -> None:
    documents = dict(DOCUMENTS)
    examples = unavailable_examples(documents[checker.MCP])
    assert len(examples) == 2
    original = examples[index]
    envelope = json.loads(original)
    if change in {"is_error_true", "is_error_false"}:
        envelope["isError"] = change == "is_error_true"
    elif change == "retriable":
        envelope["error"]["retriable"] = True
    elif change == "data":
        envelope["data"] = {}
    elif change == "success_catalog":
        envelope["data"] = {"catalog_revision": "0", "drivers": [
            {"desired_revision": "0", "revision": "0", "manager_revision": "0"}
        ]}
    elif change == "code":
        envelope["error"]["code"] = "FAILED_PRECONDITION"
    elif change == "hash":
        envelope["meta"]["data_hash"] = "0" * 64
    elif change == "hash_missing":
        del envelope["meta"]["data_hash"]
    elif change == "hash_string":
        envelope["meta"]["data_hash"] = "invalid"
    elif change == "hash_concrete":
        envelope["meta"]["data_hash"] = checker.hashlib.sha256(b"null").hexdigest()
    elif change == "extra":
        envelope["extra"] = None
    elif change == "nested_revision":
        envelope["meta"]["consistency"]["revision"] = "0"
    elif change == "source_layer":
        envelope["error"]["source_layer"] = "provider"
    elif change == "meta_extra":
        envelope["meta"]["extra"] = None
    elif change == "error_extra":
        envelope["error"]["extra"] = None
    elif change == "contract_extra":
        envelope["meta"]["contract"]["extra"] = None
    elif change == "consistency_extra":
        envelope["meta"]["consistency"]["extra"] = None
    elif change == "clock":
        envelope["meta"]["data_timestamp"] = "invalid"
    replacement = json.dumps(envelope, indent=2) + "\n"
    if change == "removed":
        replacement = ""
    elif change == "duplicate_member":
        replacement = replacement.replace('"data": null', '"data": {}, "data": null')
    elif change == "invalid_json":
        replacement = "{invalid JSON}\n"
    # Replace only the selected identical envelope, preserving its label.
    before, section = documents[checker.MCP].split(UNAVAILABLE_SECTION, 1)
    offset = section.index(original)
    if index == 1:
        offset = section.index(original, offset + len(original))
    section = section[:offset] + replacement + section[offset + len(original):]
    documents[checker.MCP] = before + UNAVAILABLE_SECTION + section
    assert checker.validate(documents)
    assert (f"{checker.MCP}: invalid unavailable-read failure envelopes"
            in checker.validate(documents))


@pytest.mark.parametrize("row", UNAVAILABLE_CASE_ROWS)
@pytest.mark.parametrize("change", ["removed", "weakened", "duplicated"])
def test_runtime_control_contract_unavailable_case_mutations(row, change) -> None:
    documents = dict(DOCUMENTS)
    assert documents[checker.LIFECYCLE].count(row) == 1
    replacement = {"removed": "", "weakened": row.rsplit("|", 2)[0] + "| Optional result |",
                   "duplicated": row + "\n" + row}[change]
    documents[checker.LIFECYCLE] = documents[checker.LIFECYCLE].replace(row, replacement, 1)
    assert checker.validate(documents)
    assert (f"{checker.LIFECYCLE}: invalid unavailable-read case table"
            in checker.validate(documents))


@pytest.mark.parametrize("row", [row for row in UNAVAILABLE_CASE_ROWS if row.startswith("| Get of")])
def test_runtime_control_contract_unavailable_collision_refusal(row) -> None:
    documents = dict(DOCUMENTS)
    documents[checker.LIFECYCLE] = documents[checker.LIFECYCLE].replace(
        row, row.split("| `NOT_FOUND`", 1)[0] + "| `UNAVAILABLE`, null data |", 1)
    assert checker.validate(documents)
    assert (f"{checker.LIFECYCLE}: invalid unavailable-read case table"
            in checker.validate(documents))


@pytest.mark.parametrize("path", [checker.MCP, checker.LIFECYCLE])
def test_runtime_control_contract_unavailable_precedence_removed(path) -> None:
    documents = dict(DOCUMENTS)
    assert documents[path].count(UNAVAILABLE_PRECEDENCE) == 1
    documents[path] = documents[path].replace(UNAVAILABLE_PRECEDENCE, "", 1)
    assert checker.validate(documents)


def test_runtime_control_contract_unavailable_envelopes_allow_json_formatting() -> None:
    documents = dict(DOCUMENTS)
    for example in unavailable_examples(documents[checker.MCP]):
        documents[checker.MCP] = documents[checker.MCP].replace(
            example, json.dumps(json.loads(example), sort_keys=True) + "\n", 1)
    assert checker.validate(documents) == []


@pytest.mark.parametrize("member", sorted(checker.UNAVAILABLE_VIEW_MEMBERS))
def test_runtime_control_contract_unavailable_forbids_nested_read_members(member) -> None:
    envelope = json.loads(unavailable_examples(DOCUMENTS[checker.MCP])[0])
    envelope["meta"]["consistency"]["nested"] = [{member: "0"}]
    assert checker.contains_read_view(envelope)
    assert not checker.unavailable_envelope(envelope)


MALFORMED_RECORD_READ_RULE = """With both shared counters valid, a registered driver whose existing durable
record has a missing or malformed `desired_revision` has no authoritative read
revision. After the existing get identity checks, get of that driver and the
entire list refuse with `UNAVAILABLE` and `data: null`, using the same
non-retriable read envelope as invalid shared bounds. Do not omit the driver,
substitute the current mark, or use stale cached fields. Get of an independent
driver with a validated coherent record remains usable. The current-mark
fallback applies only when the driver's record is absent, never when an
existing record is malformed; preserve that record under the load rules."""


@pytest.mark.parametrize("path", [checker.MCP, checker.LIFECYCLE])
def test_runtime_control_contract_malformed_record_read_rule(path) -> None:
    assert DOCUMENTS[path].count(MALFORMED_RECORD_READ_RULE) == 1
    assert any(MALFORMED_RECORD_READ_RULE in rule["required"]
               for rule in checker.RULES if rule["path"] == path)


@pytest.mark.parametrize("path", [checker.MCP, checker.LIFECYCLE])
@pytest.mark.parametrize("change", ["removed", "mark fallback", "partial list", "global refusal"])
def test_runtime_control_contract_malformed_record_read_mutations(path, change) -> None:
    documents = dict(DOCUMENTS)
    assert documents[path].count(MALFORMED_RECORD_READ_RULE) == 1
    replacement = {
        "removed": "",
        "mark fallback": MALFORMED_RECORD_READ_RULE.replace(
            "substitute the current mark", "reject the current mark"),
        "partial list": MALFORMED_RECORD_READ_RULE.replace(
            "entire list refuse", "partial list succeeds"),
        "global refusal": MALFORMED_RECORD_READ_RULE.replace(
            "record remains usable", "record also refuses"),
    }[change]
    documents[path] = documents[path].replace(MALFORMED_RECORD_READ_RULE, replacement, 1)
    assert checker.validate(documents)


@pytest.mark.parametrize("disposition", ["missing", "malformed"])
def test_runtime_control_contract_malformed_record_read_cases(disposition) -> None:
    row = (f"| Both counters valid; registered record has {disposition} `desired_revision` | "
           "Affected get and entire list: `UNAVAILABLE`, null data, no usable revision; "
           "independent valid get remains usable; preserve record, no mark fallback |")
    assert DOCUMENTS[checker.LIFECYCLE].count(row) == 1
    assert row in UNAVAILABLE_CASE_ROWS
