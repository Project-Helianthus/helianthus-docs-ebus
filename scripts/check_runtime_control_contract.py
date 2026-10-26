#!/usr/bin/env python3
"""Guard durable-control documentation and examples, not gateway behavior.

Reviewed normative paragraphs/rows are frozen in runtime_control_contract.json.
Contract edits require a corresponding reviewed fixture update. Examples cannot
substitute for normative prose; request/result examples are checked separately.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

from markdown_it import MarkdownIt


ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads(Path(__file__).with_name("runtime_control_contract.json").read_text())
API = "api/driver-runtime-v1.md"
MCP = "api/mcp.md"
LIFECYCLE = "architecture/runtime-driver-lifecycle.md"
REFUSAL_ORDER = [
    ("1", "`INVALID_ARGUMENT`"), ("2", "`NOT_FOUND`"), ("3", "`FAILED_PRECONDITION`"),
    ("3", "`UNAVAILABLE`"), ("4", "`FAILED_PRECONDITION`"), ("5", "`INVALID_ARGUMENT`"),
    ("5", "`DEADLINE_EXCEEDED`"), ("6", "`REVISION_CONFLICT` with current view"),
    ("6", "`FAILED_PRECONDITION`"), ("7", "`FAILED_PRECONDITION`"),
    ("8", "`TRANSITION_BUSY`"), ("9", "`RESOURCE_EXHAUSTED`"), ("10", "`COUNTER_EXHAUSTED`"),
]
CTL_IDS = ["CTL-01 / CTL-02"] + [f"CTL-{n:02d}" for n in range(3, 20)]
MANAGER = "docs/platform/driver-runtime-manager-v1.md"
# A configured-disabled driver is refused START (refusal order 4), so no start
# transition out of DISABLED may appear in any arrow or textual transition form.
DISABLED_START = re.compile(r"DISABLED`?\s*(?:-+\s*[\w ]*-+>|-+>|=+>|\u2192)\s*`?STARTING")
# The startup bullet that sent every configured-enabled descriptor to STARTING.
OLD_STARTUP = re.compile(r"configured-enabled descriptor enters\s+`STARTING`")
# Request/result members that would reintroduce receipts or a lifecycle principal.
FORBIDDEN_MEMBERS = {"idempotency_key", "request_id", "operation_id", "disposition",
                     "completed", "outcome", "principal", "authorization", "receipt"}
SNAPSHOT_MEMBERS = {
    "schema_version", "driver_id", "desired_state", "observed_state", "reason",
    "retry", "generation", "desired_revision", "revision", "attempt",
    "capabilities", "effective_capabilities", "safety_quarantined", "changed_at_utc",
}
REASON_MEMBERS = {"code", "retryable"}
RETRY_MEMBERS = {"eligible", "budget_remaining", "not_before_utc"}
# G5 driver object: eight required members plus the one optional `recovery`
# member, allowed only while the observed state is BACKOFF.
OBSERVED_STATES = {"DISABLED", "STOPPED", "STARTING", "RUNNING", "DEGRADED",
                   "BACKOFF", "STOPPING", "FAILED"}
DESIRED_STATES = {"RUNNING", "STOPPED"}
DRIVER_MEMBERS = {"driver_id", "enabled", "desired_state", "desired_revision",
                  "observed_state", "reason", "safety_quarantined", "revision"}
RECOVERY = "recovery"
RECOVERY_STATES = {"BACKOFF"}
RECOVERY_MEMBERS = {"attempt", "next_attempt_at", "last_failure_class",
                    "last_failure_cause"}
FAILURE_CLASSES = {"DIAL_FAILED", "TIMEOUT", "TRANSPORT_CLOSED", "OTHER"}
CAUSE_MAX_CHARS = 160
DRIVER_ID = re.compile(r"[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*")
REASON_CODE = re.compile(r"[A-Z][A-Z_]*")
UTC_TIMESTAMP = re.compile(
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.[0-9]{1,9})?Z")
# Address shapes that must not survive in the cause text: IPv4, IPv6 or hardware
# address groups, host:port, URL scheme, absolute or drive path, user@host and a
# dotted host name. A fixture lint; the gateway owns the stripping.
ADDRESS_SHAPES = tuple(re.compile(pattern) for pattern in (
    r"[0-9]{1,3}(?:\.[0-9]{1,3}){3}",
    r"::|(?:[0-9A-Fa-f]{1,4}:){2,}",
    r"\S:[0-9]{1,5}(?![0-9])",
    r"[A-Za-z][A-Za-z0-9+.-]*://",
    r"(?:^|[\s(])/[A-Za-z0-9._-]|[A-Za-z]:\\|\\",
    r"\S@\S",
    r"[A-Za-z0-9-]\.[A-Za-z0-9-]",
))
UNAVAILABLE_SECTION = "### Envelope, lifecycle errors and acceptance vectors"
UNAVAILABLE_CASE_SECTION = "### Unavailable reads with invalid durable bounds"
UNAVAILABLE_VIEW_MEMBERS = {
    "success_catalog", "catalog_revision", "drivers", "desired_revision",
    "revision", "manager_revision",
}


def contains_read_view(value: object) -> bool:
    if isinstance(value, dict):
        return bool(UNAVAILABLE_VIEW_MEMBERS & value.keys()) or any(
            contains_read_view(child) for child in value.values()
        )
    if isinstance(value, list):
        return any(contains_read_view(child) for child in value)
    return False


def unavailable_envelope(value: object) -> bool:
    if not isinstance(value, dict) or value.keys() != {"meta", "data", "error"}:
        return False
    meta, error = value["meta"], value["error"]
    return (
        value["data"] is None
        and not contains_read_view(value)
        and isinstance(meta, dict)
        and meta.keys() == {"contract", "consistency", "data_timestamp", "data_hash"}
        and isinstance(meta["contract"], dict)
        and meta["contract"].keys() == {"name", "major", "minor"}
        and meta["contract"]["name"] == "helianthus-ebus-mcp"
        and type(meta["contract"]["major"]) is int and meta["contract"]["major"] == 1
        and type(meta["contract"]["minor"]) is int and meta["contract"]["minor"] == 0
        and meta["consistency"] == {"mode": "LIVE"}
        and meta["data_timestamp"] == "2000-01-01T00:00:00Z"
        and meta["data_hash"] == hashlib.sha256(b"null").hexdigest()
        and isinstance(error, dict)
        and error.keys() == {"code", "message", "retriable", "source_layer"}
        and error["code"] == "UNAVAILABLE"
        and error["message"] == "Durable control state unavailable; offline repair required"
        and error["retriable"] is False and error["source_layer"] == "gateway"
    )


def snapshot_shape(value: object) -> bool:
    return (
        isinstance(value, dict) and value.keys() == SNAPSHOT_MEMBERS
        and isinstance(value["reason"], dict) and value["reason"].keys() == REASON_MEMBERS
        and (value["retry"] is None or (
            isinstance(value["retry"], dict) and value["retry"].keys() == RETRY_MEMBERS
        ))
    )


def normalize(text: str) -> str:
    return " ".join(text.split())


def table_blocks(text: str) -> list[list[str]]:
    lines = text.splitlines()
    return [lines[token.map[0]:token.map[1]]
            for token in MarkdownIt().enable("table").parse(text)
            if token.type == "table_open" and token.map]


def prose(text: str) -> str:
    lines = text.splitlines(keepends=True)
    for token in MarkdownIt().parse(text):
        if token.type in {"fence", "code_block", "html_block"} and token.map:
            start, end = token.map
            lines[start:end] = ["\n"] * (end - start)
    return re.sub(r"<!--.*?-->", "", "".join(lines), flags=re.DOTALL)


def units(text: str) -> list[str]:
    result = []
    for block in re.split(r"\n\s*\n", text.strip("\n")):
        for unit in block.splitlines() if block.lstrip().startswith("|") else [block]:
            # Keep indented table rows unequal to the frozen, unindented rows.
            result.append(unit if unit.lstrip().startswith("|") and not unit.startswith("|")
                          else normalize(unit))
    return result


def revision(value: object) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"0|[1-9][0-9]{0,19}", value) is not None
        and int(value) <= (1 << 64) - 1
    )


def utc_timestamp(value: object) -> bool:
    """RFC 3339 UTC with the Z designator: a real calendar date and clock time."""
    match = UTC_TIMESTAMP.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        return False
    try:
        datetime(*(int(group) for group in match.groups()))
    except ValueError:
        return False
    return True


def failure_cause(value: object) -> bool:
    return (
        isinstance(value, str) and len(value) <= CAUSE_MAX_CHARS
        and all(" " <= char <= "~" for char in value)
        and not any(shape.search(value) for shape in ADDRESS_SHAPES)
    )


def recovery_object(value: object) -> bool:
    return (
        isinstance(value, dict) and value.keys() == RECOVERY_MEMBERS
        and type(value["attempt"]) is int and value["attempt"] >= 1
        and utc_timestamp(value["next_attempt_at"])
        and isinstance(value["last_failure_class"], str)
        and value["last_failure_class"] in FAILURE_CLASSES
        and failure_cause(value["last_failure_cause"])
    )


def driver_object(value: object) -> bool:
    """The closed G5 driver object; `recovery` is optional and BACKOFF-only."""
    if not isinstance(value, dict) or not DRIVER_MEMBERS <= value.keys() <= DRIVER_MEMBERS | {RECOVERY}:
        return False
    state = value["observed_state"]
    return (
        isinstance(value["driver_id"], str) and len(value["driver_id"]) <= 128
        and DRIVER_ID.fullmatch(value["driver_id"]) is not None
        and type(value["enabled"]) is bool and type(value["safety_quarantined"]) is bool
        and isinstance(value["desired_state"], str) and value["desired_state"] in DESIRED_STATES
        and revision(value["desired_revision"]) and value["desired_revision"] != "0"
        and isinstance(state, str) and state in OBSERVED_STATES
        and isinstance(value["reason"], str) and REASON_CODE.fullmatch(value["reason"]) is not None
        and revision(value["revision"])
        and (RECOVERY not in value
             or (state in RECOVERY_STATES and recovery_object(value[RECOVERY])))
    )


def closed_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate member")
        result[key] = value
    return result


def validate(documents: dict[str, str]) -> list[str]:
    errors = []
    for rule in RULES:
        text = prose(documents[rule["path"]])
        start, end = rule["start"], rule["end"]
        # Markers must be actual, unique section headings; a null end freezes
        # the final section through EOF.
        headings = list(re.finditer(r"^ {0,3}#{2,3} .+$", text, re.MULTILINE))
        starts = [m for m in headings if m.group().lstrip().startswith(start)]
        ends = [m for m in headings if end and m.group().lstrip().startswith(end)]
        section_end = ends[0].start() if len(ends) == 1 else len(text)
        if (len(starts) != 1 or (end is not None and len(ends) != 1)
                or starts[0].end() >= section_end):
            errors.append(f"{rule['path']}: invalid section {start}")
            continue
        if parent := rule.get("parent"):
            owners = [m for m in headings
                      if m.group().lstrip().startswith("## ")
                      and m.start() < starts[0].start()]
            matches = [m for m in headings if m.group().lstrip() == parent]
            if (len(matches) != 1 or not owners or owners[-1] != matches[0]
                    or any(m.group().lstrip().startswith("## ")
                           for m in headings
                           if starts[0].end() < m.start() < section_end)):
                errors.append(f"{rule['path']}: invalid owning section {parent}")
        present = units(text[starts[0].end():section_end])
        for required in rule["required"]:
            if normalize(required) not in present:
                errors.append(f"{rule['path']}: changed obligation: {normalize(required)[:100]}")
        if rule.get("exact") and present != [normalize(s) for s in rule["required"]]:
            errors.append(f"{rule['path']}: unexpected contract content in {start}")
        section_text = normalize(text[starts[0].end():section_end])
        if rule.get("ordered"):
            positions = [section_text.find(normalize(clause)) for clause in rule["required"]]
            if positions != sorted(positions):
                errors.append(f"{rule['path']}: obligation order changed")
        for needle in rule.get("contains", []):
            if normalize(needle) not in section_text:
                errors.append(f"{rule['path']}: changed obligation: {normalize(needle)[:100]}")
        for pattern in rule.get("forbidden", []):
            if re.search(pattern, section_text):
                errors.append(f"{rule['path']}: forbidden classification: {pattern[:60]}")

    # G5 examples are separate from normative prose and use the closed wire
    # projection, not the older DriverSnapshotV1 proposal. Count every fence,
    # regardless of info string, so unexpected rendered examples cannot hide.
    mcp_section = documents[MCP].split("### Read and mutation data", 1)[-1].split(
        "### Envelope, lifecycle errors and acceptance vectors", 1)[0]
    examples = [t.content for t in MarkdownIt().parse(mcp_section)
                if t.type == "fence"]
    try:
        listing, single, decision = [
            json.loads(s, object_pairs_hook=closed_object) for s in examples]
        assert isinstance(listing, dict) and listing.keys() == {"catalog_revision", "drivers"}
        assert revision(listing["catalog_revision"]) and listing["catalog_revision"] != "0"
        assert isinstance(listing["drivers"], list) and len(listing["drivers"]) == 1
        driver = listing["drivers"][0]
        assert driver == {
            "driver_id": "ebus.primary", "enabled": True,
            "desired_state": "RUNNING", "desired_revision": "7",
            "observed_state": "BACKOFF", "reason": "RETRY_SCHEDULED",
            "safety_quarantined": False, "revision": listing["catalog_revision"],
            "recovery": {
                "attempt": 3, "next_attempt_at": "2000-01-01T00:00:08Z",
                "last_failure_class": "DIAL_FAILED",
                "last_failure_cause": "dial: connection refused",
            },
        }
        assert type(driver["enabled"]) is bool and type(driver["safety_quarantined"]) is bool
        assert driver_object(driver)
        # The running driver carries no recovery member at all.
        assert isinstance(single, dict) and single.keys() == {"catalog_revision", "driver"}
        assert revision(single["catalog_revision"]) and single["catalog_revision"] != "0"
        assert single["driver"] == {
            "driver_id": "ebus.primary", "enabled": True,
            "desired_state": "RUNNING", "desired_revision": "7",
            "observed_state": "RUNNING", "reason": "NONE",
            "safety_quarantined": False, "revision": single["catalog_revision"],
        }
        assert type(single["driver"]["enabled"]) is bool
        assert type(single["driver"]["safety_quarantined"]) is bool
        assert driver_object(single["driver"])
        assert isinstance(decision, dict) and decision.keys() == {"desired_state", "desired_revision"}
        assert decision["desired_state"] in {"RUNNING", "STOPPED"}
        assert revision(decision["desired_revision"]) and decision["desired_revision"] != "0"
    except (ValueError, TypeError, AssertionError, KeyError):
        errors.append(f"{MCP}: invalid G5 closed data examples")

    # Both categorical failures are complete, closed envelopes. Parse every
    # fence in the owning section, rejecting duplicate JSON members as well.
    failure_section = documents[MCP].split(UNAVAILABLE_SECTION, 1)[-1].split("\n## ", 1)[0]
    examples = [t.content for t in MarkdownIt().parse(failure_section)
                if t.type == "fence"]
    try:
        assert len(examples) == 2
        for example in examples:
            envelope = json.loads(example, object_pairs_hook=closed_object)
            assert envelope["meta"]["data_hash"] == "<computed-data-hash>"
            envelope["meta"]["data_hash"] = hashlib.sha256(b"null").hexdigest()
            assert unavailable_envelope(envelope)
    except (ValueError, TypeError, AssertionError, KeyError):
        errors.append(f"{MCP}: invalid unavailable-read failure envelopes")

    # Check the table's closed row structure and outcomes independently of the
    # prose freeze, including the two input/registry refusal collisions.
    case_rule = next(r for r in RULES if r["start"] == UNAVAILABLE_CASE_SECTION)
    case_section = prose(documents[LIFECYCLE]).split(UNAVAILABLE_CASE_SECTION, 1)[-1].split(
        case_rule["end"], 1)[0]
    case_rows = [line for line in case_section.splitlines() if line.lstrip().startswith("|")]
    expected_rows = [line for line in case_rule["required"] if line.startswith("|")]
    cells = [[cell.strip() for cell in row.strip().strip("|").split("|")]
             for row in case_rows]
    expected_cells = [[cell.strip() for cell in row.strip("|").split("|")]
                      for row in expected_rows]
    if (table_blocks(case_section) != [case_rows]
            or len(cells) != 27 or any(len(row) != 2 for row in cells)
            or cells != expected_cells):
        errors.append(f"{LIFECYCLE}: invalid unavailable-read case table")

    # Historical proposal consistency only; G5 above owns public acceptance.
    # Exactly one archived request/result pair, independent of whitespace/key order.
    api = documents[API]
    section = api.split("## Mutating Tools", 1)[-1].split("### Unproven-close", 1)[0]
    examples = [t.content for t in MarkdownIt().parse(section)
                if t.type == "fence"]
    try:
        request, result = [json.loads(s, object_pairs_hook=closed_object) for s in examples]
        assert set(request) == {"DriverID", "ExpectedRevision"}
        assert request["DriverID"] == "eebus.primary"
        assert revision(request["ExpectedRevision"]) and request["ExpectedRevision"] != "0"
        assert set(result) == {"desired_state", "desired_revision"}
        assert result["desired_state"] in {"RUNNING", "STOPPED"}
        assert revision(result["desired_revision"]) and result["desired_revision"] != "0"
    except (ValueError, TypeError, AssertionError, KeyError):
        errors.append(f"{API}: invalid closed request/result examples")

    for heading, following, fields in (
        ("## `DriverSnapshotV1`", "### Field Invariants", ("desired_revision", "revision")),
        ("## `drivers.v1.list`", "## Mutating Tools", ("manager_revision",)),
    ):
        section = api.split(heading, 1)[-1].split(following, 1)[0]
        examples = [t.content for t in MarkdownIt().parse(section)
                    if t.type == "fence"]
        try:
            assert len(examples) == 1
            obj = json.loads(examples[0], object_pairs_hook=closed_object)
            assert isinstance(obj, dict)
            if heading == "## `DriverSnapshotV1`":
                assert snapshot_shape(obj)
            assert all(revision(obj[f]) for f in fields)
            assert not {"active_operation_id", "last_operation"} & obj.keys()
            assert not FORBIDDEN_MEMBERS & obj.keys()
        except (ValueError, TypeError, AssertionError, KeyError):
            errors.append(f"{API}: invalid revision example in {heading}")

    # Startup follows durable desired state; DISABLED has no start transition.
    manager_raw = normalize(documents[MANAGER])
    for name, raw in ((MANAGER, manager_raw), (LIFECYCLE, normalize(documents[LIFECYCLE]))):
        if DISABLED_START.search(raw):
            errors.append(f"{name}: DISABLED to STARTING start transition reintroduced")
    if OLD_STARTUP.search(manager_raw):
        errors.append(f"{MANAGER}: startup sends every configured-enabled descriptor to STARTING")

    # Refusal table: exact row order and codes, no authorization refusal.
    lifecycle = prose(documents[LIFECYCLE])
    tables = table_blocks(lifecycle)
    refusal_rows = [line for line in lifecycle.splitlines()
                    if re.match(r"^\|\s*\d+\s*\|", line)]
    rows = [[c.strip() for c in line.strip().strip("|").split("|")]
            for line in refusal_rows]
    if (not any(table[2:] == refusal_rows for table in tables)
            or [(r[0], r[2]) for r in rows if len(r) == 4] != REFUSAL_ORDER
            or len(rows) != len(REFUSAL_ORDER)):
        errors.append(f"{LIFECYCLE}: refusal table order or codes changed")
    # CTL vectors: every id exactly once, in order.
    ctl = [m.group(1).strip() for m in re.finditer(r"^\| (CTL-[^|]+?) \|", lifecycle, re.MULTILINE)]
    ctl_rows = [line for line in lifecycle.splitlines() if re.match(r"^\| CTL-", line)]
    if ctl != CTL_IDS or not any(table[2:] == ctl_rows for table in tables):
        errors.append(f"{LIFECYCLE}: CTL vector ids changed: {ctl}")
    # D4: no lifecycle principal or authorization refusal anywhere in the API.
    if "PERMISSION_DENIED" in prose(api) or "PERMISSION_DENIED" in "".join("|".join(r) for r in rows):
        errors.append(f"{API}: authorization refusal reintroduced")
    for marker in ("Final D4 removes G5 lifecycle principal/authorization checks",
                   "No lifecycle principal, authority,"):
        if marker not in normalize(lifecycle):
            errors.append(f"{LIFECYCLE}: D4 no-principal rule missing")
    if "the lifecycle tools carry no principal and no authorization check" not in normalize(prose(api)):
        errors.append(f"{API}: D4 no-principal rule missing")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        documents = {r["path"]: (args.root / r["path"]).read_text(encoding="utf-8")
                     for r in RULES}
        errors = validate(documents)
    except (OSError, UnicodeError) as exc:
        errors = [str(exc)]
    for error in errors:
        print(f"runtime_control_contract_invalid: {error}", file=sys.stderr)
    if errors:
        return 1
    print("runtime_control_contract_ok (documentation only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
