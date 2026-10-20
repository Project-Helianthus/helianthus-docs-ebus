"""Guard the target documentation contract, not runtime adapter acceptance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from markdown_it import MarkdownIt
import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "api/semantic-snapshot-read.md"

# Keep normative clauses together so changing a bound or weakening a rejection
# requires an explicit contract-test change. Line wrapping is immaterial.
CLAUSES = (
    """Require 1–32 distinct asset IDs, each at most 256 UTF-8 bytes and valid as
    SemReg `AssetID`. Reject duplicates, nulls, unknown arguments, wildcards,
    native locators and empty selection as `INVALID_ARGUMENT`. IDs are compared
    byte-for-byte, without trimming, case folding or protocol interpretation.""",
    """All GraphQL aliases in one operation share that capture and one
    evaluation context; take the union of their selected IDs before capture.
    The operation-wide union also has the 32-asset bound. MCP captures once per
    tool call.""",
    """Bound the complete serialized shared view to 4 MiB, before GraphQL field
    selection or MCP wrapping. Kernel and projection collection limits also
    apply, including 32 source keys per disposition. Overflow
    fails the whole read with `RESOURCE_EXHAUSTED`; no truncation, pagination
    across changing snapshots or successful partial dump is allowed.""",
    """Within one asset, snapshot, evaluation, projection and any selection must bind
    the identical snapshot ID and complete revision vector. Candidate references
    also bind exact candidate revisions. Validate this before exposure. A mismatch
    fails the entire read with `CONFLICT`; never splice an older fact, newer
    capability or a cached evaluation into a superficially consistent response.""",
    """An unwired provider fails the whole request with `UNAVAILABLE`, rather than
    fabricating empty snapshots.""",
    """Preserve all reason codes in source quality. For `fact_unavailable`,
    `capability_unavailable` and `capability_unqualified`, first identify the exact
    source keys that causally withhold this item. Intersect native reasons across
    all candidates of all those causal keys, not across every supporting key.
    An available sibling key is non-causal and cannot erase the explanation of an
    unavailable key.""",
    """Every candidate on a causal key must itself explain the
    selected outcome through its original quality: unavailable/withdrawn for
    availability, or candidate/rejected qualification for unqualified capability
    support (a fact's admission also considers promotion and validity).""",
    """A candidate
    on a causal key without explanatory quality or without the common reason
    prevents a fabricated native explanation; keep the surface fallback instead.""",
    """Never join candidates using a fact ID alone: match the complete `FactKey`,
    including pack ID/version and every dimension ID, value kind and value.""",
    """Expiry-only evaluation cannot manufacture a native availability reason, and an
    instance-only qualification/availability failure cannot borrow unrelated fact
    reasons. With no causal fact explanation, retain the existing surface fallback.""",
    """When that intersection contains several codes, use the lexically first one for
    the disposition's single `reason`. For other outcomes retain the applicable
    owner reasons with the same lexical tie-break.""",
    """The STD-01 rule below takes precedence for affected eeBUS items.""",
    """Sort assets by `asset_id`, not request order. Preserve the kernel's canonical
    array orders: facts by canonical `FactKey` bytes; candidates by `candidate_id`;
    conflicts by `conflict_id`; bindings/instances by primary ID; source paths by
    source/epoch/generation/binding; evidence by owner/kind/contract/digest; reasons
    by definition ID. Use the serialization contract's full ordering rules,
    including the retained tuple and numeric generation comparison. Sort projection
    requests/dispositions by `(kind,item_id)`, loss by its canonical key, and
    selections by `(canonical key,policy_id,policy_version)`. Reject duplicates.""",
    """Object field order is not semantic. The same capture, evaluation context and
    mapping/policy versions produce the same shared-view data and array order on
    both surfaces after the field-name mapping below.""",
    """The ordinary GraphQL root returns the shared view directly; the normal GraphQL
    `data`/`errors` response envelope remains. Use typed objects for the referenced
    SemReg records, string scalars for 64-bit values/IDs/digests, `Boolean` for
    booleans and `Int` for `Decimal.exponent10`. All matching `Value` arms are
    nullable; `kind` determines the one present arm. Required record members and
    arrays stay non-null. Optional MCP fields are nullable in GraphQL. Enum/code
    string values, contract identifiers and units are unchanged.""",
    """Convert snake_case member names recursively to camelCase on GraphQL, leaving
    already single-word members unchanged.""",
    """`meta.contract` is `{name: "helianthus-ebus-mcp", major: 1, minor: 0}`;
    `meta.consistency.mode` is `EVALUATED_SEMREG_PUBLICATION`, as on the existing
    SemReg-backed PV tool. This tool takes only `asset_ids`: it does not accept the
    legacy `LIVE`/`SNAPSHOT` consistency selector or a replay snapshot ID.""",
    """Request failures have null `data` and the existing error object members
    `code`, `message`, `retriable`, `source_layer`; messages are sanitized and
    `source_layer` is `gateway`. Invalid input, conflict and overflow are not
    retriable; provider unavailability and timeout are retriable. GraphQL maps the
    same request failures to `errors[].extensions.code` with a null root, without
    inventing an MCP-shaped GraphQL envelope.""",
)

MAPPINGS = {
    "asset_ids, asset_id, binding_id, snapshot_id": "assetIds, assetId, bindingId, snapshotId",
    "unavailable_reason, identity_links": "unavailableReason, identityLinks",
    "candidate_id, candidate_revision, source_epoch_id": "candidateId, candidateRevision, sourceEpochId",
    "driver_generation, retained_observations": "driverGeneration, retainedObservations",
    "evaluated_at, evaluate_monotonic, freshness_policy": "evaluatedAt, evaluateMonotonic, freshnessPolicy",
    "unix_nanoseconds, clock_id, uncertainty_ns": "unixNanoseconds, clockId, uncertaintyNs",
    "effective_availability, evaluation_digest": "effectiveAvailability, evaluationDigest",
    "pack_id, pack_version, fact_id, item_id": "packId, packVersion, factId, itemId",
    "source_keys, source_items, presentation_only": "sourceKeys, sourceItems, presentationOnly",
    "exponent10, known, revisions.semantic": "exponent10, known, revisions.semantic",
}


def normalized(text: str) -> str:
    return " ".join(text.split())


def validate_contract(text: str) -> None:
    tokens = MarkdownIt("commonmark").parse(text)
    visible = normalized(" ".join(
        "".join(
            f"`{child.content}`" if child.type == "code_inline" else
            "\n" if child.type in ("softbreak", "hardbreak") else child.content
            for child in token.children or () if child.type != "html_inline"
        ) for token in tokens if token.type == "inline"
    ))
    for clause in CLAUSES:
        assert normalized(clause) in visible, f"Missing contract clause: {normalized(clause)}"
    table = re.search(r"\| MCP / SemReg \| GraphQL \|\n(.*?)(?:\n\n|\Z)", text, re.S)
    assert table is not None, "Missing transport mapping table"
    assert normalized(table[0]) in visible, "Hidden transport mapping table"
    rows = re.findall(r"^\| (`.*?) \| (.*?) \|$", table[1], re.M)
    assert len(rows) == len(MAPPINGS)
    assert {left.replace("`", ""): right.replace("`", "") for left, right in rows} == MAPPINGS
    examples = [json.loads(token.content) for token in tokens
                if token.type == "fence" and token.info == "json"]
    ids = [f"asset:{pack}" for pack in ("evse", "infrastructure", "pv", "storage", "thermal")]
    assert examples[0] == {"name": "semantic.v1.snapshot.get", "arguments": {"asset_ids": ids}}
    assert examples[1] == {"assetIds": ids}
    assert examples[2] == dict(zip(
        ("semantic", "identity", "facts", "services", "capabilities"),
        ("7", "2", "5", "1", "1"), strict=True,
    ))
    assert examples[3] == {
        "kind": "fact", "item_id": "thermal.measurement.humidity_relative",
        "outcome": "unknown", "source_keys": [], "loss": [], "reason": "semantic.read.reason.value_unknown",
    }
    assert examples[4] == {"assets": [{
        "asset_id": "asset:missing", "selections": [],
        "unavailable_reason": "semantic.read.reason.asset_unknown",
    }]}
    assert examples[5] == [
        {"kind": "quantity", "quantity": {"number": {"coefficient": "0", "exponent10": 0}, "unit": "unit.watt"}},
        {"kind": "boolean", "boolean": False}, {"kind": "text", "text": ""},
    ]
    assert len(examples) == 8
    success_data = {"assets": [
        {"asset_id": "asset:missing", "selections": [],
         "unavailable_reason": "semantic.read.reason.asset_unknown"},
        {"asset_id": "asset:withheld", "selections": [],
         "unavailable_reason": "semantic.read.reason.publication_withheld"},
    ]}
    overflow_error = {
        "code": "RESOURCE_EXHAUSTED",
        "message": "semantic snapshot read exceeds bounds",
        "retriable": False, "source_layer": "gateway",
    }
    for example, data, error in (
        (examples[6], success_data, None),
        (examples[7], None, overflow_error),
    ):
        # Compare the complete body: unavailable entries omit the snapshot
        # triplet, errors have no partial data, and metadata has no legacy
        # snapshot ID or Modbus limits. Require publication placeholders and
        # hydrate only in memory, hashing actual and expected data independently.
        assert example["meta"]["data_hash"] == "<computed-data-hash>"
        actual_serialized = json.dumps(example["data"], sort_keys=True, separators=(",", ":"))
        example["meta"]["data_hash"] = hashlib.sha256(actual_serialized.encode("utf-8")).hexdigest()
        serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
        assert example == {
            "data": data, "error": error,
            "meta": {
                "contract": {"name": "helianthus-ebus-mcp", "major": 1, "minor": 0},
                "consistency": {"mode": "EVALUATED_SEMREG_PUBLICATION"},
                "data_timestamp": "1970-01-01T00:00:00Z",
                "data_hash": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
            },
        }


def test_semantic_snapshot_read_contract() -> None:
    validate_contract(DOCUMENT.read_text(encoding="utf-8"))


@pytest.mark.parametrize("clause", CLAUSES)
@pytest.mark.parametrize("replacement", ("omitted", "<!-- {clause} -->", "\n\n```text\n{clause}\n```\n\n"))
def test_semantic_snapshot_read_rejects_missing_or_hidden_clause(clause: str, replacement: str) -> None:
    text = DOCUMENT.read_text(encoding="utf-8")
    pattern = r"\s+".join(re.escape(word) for word in clause.split())
    match = re.search(pattern, text)
    assert match is not None
    with pytest.raises(AssertionError, match="Missing contract clause"):
        validate_contract(text[:match.start()] + replacement.format(clause=normalized(clause)) + text[match.end():])


@pytest.mark.parametrize("old,new", (
    (
        "Never join candidates using a fact ID alone: match the complete `FactKey`,\n"
        "including pack ID/version and every dimension ID, value kind and value.",
        "Join candidates using a fact ID alone; matching the complete `FactKey` is optional.",
    ),
    (
        "Intersect native reasons across\nall candidates of all those causal keys, not across every supporting key.",
        "Intersect native reasons across\nsome candidates of some causal keys, not across every supporting key.",
    ),
))
def test_semantic_snapshot_read_rejects_causal_selection_weakening(old: str, new: str) -> None:
    text = DOCUMENT.read_text(encoding="utf-8")
    assert old in text
    with pytest.raises(AssertionError, match="Missing contract clause"):
        validate_contract(text.replace(old, new, 1))


@pytest.mark.parametrize("source,target", tuple(MAPPINGS.items()))
def test_semantic_snapshot_read_rejects_mapping_drift(source: str, target: str) -> None:
    text = DOCUMENT.read_text(encoding="utf-8")
    row = f"| `{source.replace(', ', '`, `')}` | `{target.replace(', ', '`, `')}` |"
    assert row in text
    with pytest.raises(AssertionError):
        validate_contract(text.replace(row, row.replace(target.split(', ')[0], "wrongField"), 1))


@pytest.mark.parametrize("old,new", (
    ('"assetIds": ["asset:evse"', '"assetIds": ["asset:other"'),
    ('"semantic":"7"', '"semantic":7'),
    ('"outcome": "unknown"', '"outcome": "exact"'),
    ('"selections": []', '"selections": null'),
    ('"boolean":false', '"boolean":null'),
))
def test_semantic_snapshot_read_rejects_example_drift(old: str, new: str) -> None:
    text = DOCUMENT.read_text(encoding="utf-8")
    assert old in text
    with pytest.raises(AssertionError):
        validate_contract(text.replace(old, new))


def test_semantic_snapshot_read_registered_in_local_gate() -> None:
    gate = (ROOT / "scripts/ci_local.sh").read_text(encoding="utf-8")
    assert "python3 -m pytest -q tests/test_semantic_snapshot_read_contract.py\n" in gate


@pytest.mark.parametrize("example_index", (6, 7))
@pytest.mark.parametrize("mutation", (
    "hash", "contract", "consistency", "timestamp", "limits", "snapshot_id",
    "data", "error", "extra_member",
))
def test_semantic_snapshot_read_rejects_complete_envelope_drift(
    example_index: int, mutation: str,
) -> None:
    text = DOCUMENT.read_text(encoding="utf-8")
    fences = list(re.finditer(r"```json\n(.*?)\n```", text, re.S))
    fence = fences[example_index]
    example = json.loads(fence[1])
    if mutation == "hash":
        example["meta"]["data_hash"] = "wrong-digest"
    elif mutation == "contract":
        example["meta"]["contract"]["name"] = "helianthus-modbus-mcp"
    elif mutation == "consistency":
        example["meta"]["consistency"]["mode"] = "LIVE"
    elif mutation == "timestamp":
        del example["meta"]["data_timestamp"]
    elif mutation == "limits":
        example["meta"]["limits"] = {}
    elif mutation == "snapshot_id":
        example["meta"]["consistency"]["snapshot_id"] = "synthetic-snapshot"
    elif mutation == "data":
        if example_index == 6:
            example["data"]["assets"][0]["snapshot"] = {}
        else:
            example["data"] = {"assets": []}
    elif mutation == "error":
        if example_index == 6:
            example["error"] = {}
        else:
            example["error"]["retriable"] = True
    else:
        example["extra"] = None
    mutated = text[:fence.start(1)] + json.dumps(example) + text[fence.end(1):]
    with pytest.raises(AssertionError):
        validate_contract(mutated)


@pytest.mark.parametrize("example_index", (6, 7))
@pytest.mark.parametrize("escaped", (False, True))
def test_semantic_snapshot_read_rejects_published_digest(example_index: int, escaped: bool) -> None:
    text = DOCUMENT.read_text(encoding="utf-8")
    fences = list(re.finditer(r"```json\n(.*?)\n```", text, re.S))
    fence = fences[example_index]
    example = json.loads(fence[1])
    serialized = json.dumps(example["data"], sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    published = "".join(f"\\u{ord(char):04x}" for char in digest) if escaped else digest
    body = fence[1].replace("<computed-data-hash>", published)
    # Both encodings recover the correct digest, but neither may be published.
    assert json.loads(body)["meta"]["data_hash"] == digest
    mutated = text[:fence.start(1)] + body + text[fence.end(1):]
    with pytest.raises(AssertionError):
        validate_contract(mutated)
