#!/usr/bin/env python3
"""Guard durable-control documentation and examples, not gateway behavior.

Reviewed normative paragraphs/rows are frozen in runtime_control_contract.json.
Contract edits require a corresponding reviewed fixture update. Examples cannot
substitute for normative prose; request/result examples are checked separately.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from markdown_it import MarkdownIt


ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads(Path(__file__).with_name("runtime_control_contract.json").read_text())
API = "api/driver-runtime-v1.md"
LIFECYCLE = "architecture/runtime-driver-lifecycle.md"
REFUSAL_ORDER = [
    ("1", "`INVALID_ARGUMENT`"), ("2", "`NOT_FOUND`"), ("3", "`FAILED_PRECONDITION`"),
    ("3", "`UNAVAILABLE`"), ("4", "`FAILED_PRECONDITION`"), ("5", "`INVALID_ARGUMENT`"),
    ("5", "`DEADLINE_EXCEEDED`"), ("6", "`REVISION_CONFLICT` with current view"),
    ("6", "`FAILED_PRECONDITION`"), ("7", "`FAILED_PRECONDITION`"),
    ("8", "`TRANSITION_BUSY`"), ("9", "`RESOURCE_EXHAUSTED`"), ("10", "`COUNTER_EXHAUSTED`"),
]
CTL_IDS = ["CTL-01 / CTL-02"] + [f"CTL-{n:02d}" for n in range(3, 16)]
# Request/result members that would reintroduce receipts or a lifecycle principal.
FORBIDDEN_MEMBERS = {"idempotency_key", "request_id", "operation_id", "disposition",
                     "completed", "outcome", "principal", "authorization", "receipt"}


def normalize(text: str) -> str:
    return " ".join(text.split())


def prose(text: str) -> str:
    lines = text.splitlines(keepends=True)
    for token in MarkdownIt().parse(text):
        if token.type in {"fence", "code_block", "html_block"} and token.map:
            start, end = token.map
            lines[start:end] = ["\n"] * (end - start)
    return re.sub(r"<!--.*?-->", "", "".join(lines), flags=re.DOTALL)


def units(text: str) -> set[str]:
    result = set()
    for block in re.split(r"\n\s*\n", text.strip()):
        for unit in block.splitlines() if block.startswith("|") else [block]:
            result.add(normalize(unit))
    return result


def revision(value: object) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"0|[1-9][0-9]{0,19}", value) is not None
        and int(value) <= (1 << 64) - 1
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
        # A start/end marker must be an actual, unique section heading.
        headings = list(re.finditer(r"^ {0,3}#{2,3} .+$", text, re.MULTILINE))
        starts = [m for m in headings if m.group().lstrip().startswith(start)]
        ends = [m for m in headings if m.group().lstrip().startswith(end)]
        if len(starts) != 1 or len(ends) != 1 or starts[0].end() >= ends[0].start():
            errors.append(f"{rule['path']}: invalid section {start}")
            continue
        present = units(text[starts[0].end():ends[0].start()])
        for required in rule["required"]:
            if normalize(required) not in present:
                errors.append(f"{rule['path']}: changed obligation: {normalize(required)[:100]}")

    # Exactly one request/result pair, independent of whitespace/key order.
    api = documents[API]
    section = api.split("## Mutating Tools", 1)[-1].split("### Unproven-close", 1)[0]
    examples = [t.content for t in MarkdownIt().parse(section)
                if t.type == "fence" and t.info.strip() == "json"]
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
                    if t.type == "fence" and t.info.strip() == "json"]
        try:
            assert len(examples) == 1
            obj = json.loads(examples[0], object_pairs_hook=closed_object)
            assert all(revision(obj[f]) for f in fields)
            assert not {"active_operation_id", "last_operation"} & obj.keys()
            assert not FORBIDDEN_MEMBERS & obj.keys()
        except (ValueError, TypeError, AssertionError, KeyError):
            errors.append(f"{API}: invalid revision example in {heading}")

    # Refusal table: exact row order and codes, no authorization refusal.
    lifecycle = prose(documents[LIFECYCLE])
    rows = [[c.strip() for c in line.strip().strip("|").split("|")]
            for line in lifecycle.splitlines()
            if re.match(r"^\|\s*\d+\s*\|", line)]
    if [(r[0], r[2]) for r in rows if len(r) == 4] != REFUSAL_ORDER or len(rows) != len(REFUSAL_ORDER):
        errors.append(f"{LIFECYCLE}: refusal table order or codes changed")
    # CTL vectors: every id exactly once, in order.
    ctl = [m.group(1).strip() for m in re.finditer(r"^\| (CTL-[^|]+?) \|", lifecycle, re.MULTILINE)]
    if ctl != CTL_IDS:
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
