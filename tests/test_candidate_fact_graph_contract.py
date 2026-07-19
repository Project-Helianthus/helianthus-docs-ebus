from __future__ import annotations

import json
import pathlib


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PLATFORM_ROOT = REPO_ROOT / "docs/platform"
PAGE = PLATFORM_ROOT / "draft-candidate-fact-graph-v1.md"
README = PLATFORM_ROOT / "README.md"
SCHEMA = PLATFORM_ROOT / "schemas/draft-candidate-fact-graph-v1.schema.json"
REPLAY_SCHEMA = PLATFORM_ROOT / "schemas/draft-candidate-fact-replay-v1.schema.json"
REGISTRY = PLATFORM_ROOT / "schemas/draft-candidate-fact-registry-v1.json"


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def test_msp07_contract_inventory_is_canonical_and_navigable() -> None:
    for path in (PAGE, SCHEMA, REPLAY_SCHEMA, REGISTRY):
        assert path.is_file(), f"missing MSP-07 contract artifact: {path}"
    page = read(PAGE)
    assert page.startswith("Canonical source: this page.\n\n# Draft Candidate Fact Graph V1")
    assert "MSP-07" in page
    assert "M7" in page
    assert "draft-candidate-fact-graph-v1.md" in read(README)


def test_contract_is_closed_candidate_only_and_has_no_promotion_language() -> None:
    page = read(PAGE)
    required = (
        "candidate-only",
        "NOT_PROMOTED",
        "CANDIDATE_DEBUG_REPLAY",
        "No Promotion Or Translation",
        "No candidate fact is a command",
        "protocol-to-protocol translation",
        "vendor-restricted",
    )
    for phrase in required:
        assert phrase in page
    for surface in (
        "stable documentation navigation",
        "stable documentation search",
        "stable sitemap",
        "versioned documentation bundle",
        "release documentation bundle",
        "`ebus.v1.*`",
        "GraphQL",
        "Portal",
        "Home Assistant",
        "command routing",
        "promoted semantic",
        "stable semantic registry",
    ):
        assert surface in page


def test_contract_closes_status_identity_comparator_and_retest_fields() -> None:
    page = read(PAGE)
    for token in (
        "`RAW_ONLY`",
        "`CANDIDATE`",
        "`CONFLICTED`",
        "`WITHHELD`",
        "`NO_SIGNAL`",
        "`CLOUD_ONLY`",
        "`CONFLICT`",
        "`NOT_TESTED`",
        "confidence",
        "falsifier",
        "retest_trigger",
        "minimum_samples",
        "maximum_missing_samples",
        "stale_cutoff_ns",
        "conflict_threshold",
        "B509",
        "B524",
        "B555",
        "OP=0x02",
        "OP=0x06",
        "service/entity/feature/path",
        "native observation pointer",
        "absolute tolerance plus relative tolerance",
        "fail-closed provenance/status matrix",
        "pre-parse",
        "no family inheritance",
        "no sibling inheritance",
    ):
        assert token in page


def test_machine_schema_and_registry_are_closed() -> None:
    schema = json.loads(read(SCHEMA))
    replay_schema = json.loads(read(REPLAY_SCHEMA))
    registry = json.loads(read(REGISTRY))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    assert replay_schema["additionalProperties"] is False
    assert registry["contract"] == "helianthus.platform.draft-candidate-fact-registry.v1"
    assert set(registry) == {
        "contract",
        "version",
        "candidate_contract",
        "source_contract",
        "statuses",
        "terminal_negative_states",
        "comparators",
        "candidate_channel",
        "forbidden_surfaces",
        "validation_precedence",
        "limits",
    }
    assert registry["statuses"] == ["RAW_ONLY", "CANDIDATE", "CONFLICTED", "WITHHELD"]
    assert registry["terminal_negative_states"] == [
        "NO_SIGNAL",
        "CLOUD_ONLY",
        "CONFLICT",
        "NOT_TESTED",
    ]
    assert registry["candidate_channel"] == "CANDIDATE_DEBUG_REPLAY"
    assert len(registry["validation_precedence"]) >= 10
    assert registry["limits"]["max_total_members"] == 16384
    assert registry["limits"]["max_total_list_items"] == 8192
    sample = schema["$defs"]["ComparatorEvaluationV1"]["properties"]["samples"][
        "items"
    ]
    assert set(sample["required"]) == {"offset_ns", "left", "right", "state"}
    assert set(sample["properties"]) == {"offset_ns", "left", "right", "state"}
    assert schema["$defs"]["TokenV1"]["pattern"].startswith("^[\\x20-\\x7e]")
    assert schema["$defs"]["NullableTokenV1"]["oneOf"][0]["maxLength"] == 256
    assert schema["$defs"]["FactV1"]["properties"]["proposed_path"][
        "maxLength"
    ] == 512


def test_determinism_limits_precedence_and_replay_are_normative() -> None:
    page = read(PAGE)
    for phrase in (
        "RFC 8785/JCS",
        "negative zero",
        "portable JSON safe-integer",
        "bytewise UTF-8",
        "Validation Precedence",
        "Bounded Limits",
        "replay uses captured evidence",
        "must not read the network",
        "must not read the wall clock",
        "--source-bundle",
        "--source-replay",
        "MSP-065 synchronized-evidence verifier",
        "deep equality",
        "HELIANTHUS:SYNCHRONIZED-EVIDENCE-REPLAY:V1",
        "not a file hash",
        "trailing newline",
    ):
        assert phrase in page
