import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import check_runtime_control_contract as checker


DOCUMENTS = {r["path"]: (checker.ROOT / r["path"]).read_text(encoding="utf-8")
             for r in checker.RULES}
OBLIGATIONS = [(r["path"], clause) for r in checker.RULES for clause in r["required"]]
BRIDGE_START = "### S4/S6/S7 synthetic acceptance obligations"
BRIDGE_RULE = next(r for r in checker.RULES if r["start"] == BRIDGE_START)


def test_runtime_control_contract_repository() -> None:
    assert checker.validate(DOCUMENTS) == []


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


@pytest.mark.parametrize(("path", "row"), [
    (rule["path"], clause)
    for rule in checker.RULES
    for clause in rule["required"] if clause.startswith("|")
])
@pytest.mark.parametrize("indent", ["    ", "\t"])
def test_runtime_control_contract_rejects_indented_table_rows(path, row, indent) -> None:
    documents = dict(DOCUMENTS)
    documents[path] = documents[path].replace(row, indent + row, 1)
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
