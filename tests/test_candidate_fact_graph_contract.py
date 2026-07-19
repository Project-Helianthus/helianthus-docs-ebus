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
COEXISTENCE_PAGE = PLATFORM_ROOT / "multi-runtime-coexistence-no-drift-v1.md"
COEXISTENCE_EVIDENCE_SCHEMA = (
    PLATFORM_ROOT / "schemas/multi-runtime-coexistence-evidence-v1.schema.json"
)
COEXISTENCE_REPORT_SCHEMA = (
    PLATFORM_ROOT / "schemas/multi-runtime-coexistence-report-v1.schema.json"
)
COEXISTENCE_REGISTRY = (
    PLATFORM_ROOT / "schemas/multi-runtime-coexistence-registry-v1.json"
)


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


def test_contract_defines_exact_sampled_outcome_state_matrix() -> None:
    page = read(PAGE)
    required_rows = (
        "`MATCH` | fact | `CANDIDATE` | null | non-empty | value and unit set",
        "`MISMATCH` | fact | `CONFLICTED` | null | non-empty | null",
        "`CONFLICT` | fact | `CONFLICTED` | null | non-empty | null",
        "`CONFLICT` | terminal bundle | `WITHHELD` | `CONFLICT` | non-empty | null",
        "`INDETERMINATE` | terminal bundle | `WITHHELD` | `NOT_TESTED` | non-empty | null",
        "`NOT_EVALUATED` | terminal bundle | `WITHHELD` | `NOT_TESTED` | empty | null",
    )
    for row in required_rows:
        assert row in page
    assert "MISMATCH maps to no terminal state" in page
    assert "NO_SIGNAL` and `CLOUD_ONLY` are never synthesized" in page


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


def test_msp08_contract_inventory_is_canonical_and_gateway_ready() -> None:
    for path in (
        COEXISTENCE_PAGE,
        COEXISTENCE_EVIDENCE_SCHEMA,
        COEXISTENCE_REPORT_SCHEMA,
        COEXISTENCE_REGISTRY,
    ):
        assert path.is_file(), f"missing MSP-08 contract artifact: {path}"
    page = read(COEXISTENCE_PAGE)
    assert page.startswith(
        "Canonical source: this page.\n\n"
        "# Multi-Runtime Coexistence No-Drift V1"
    )
    assert "MSP-08" in page
    assert "EEBUS-G18" in page
    assert "multi-runtime-coexistence-no-drift-v1.md" in read(README)


def test_msp08_contract_freezes_no_drift_and_no_leak_semantics() -> None:
    page = read(COEXISTENCE_PAGE)
    required = (
        "MSP-07@ff511b035b85aef6123fb0853bb3d2f3af6fc01e",
        "ea88fef23ecb154b08f70e7f94b36e1738ed08bf",
        "EEBUS_DISABLED_BASELINE",
        "EEBUS_DISABLED_CONFIRMED",
        "EEBUS_ENABLED_NO_SERVICES",
        "EEBUS_CONNECTED_CANDIDATE_ONLY",
        "EEBUS_CONFLICTED_WITHHELD",
        "EEBUS_DISABLED_ROLLBACK",
        "RFC 8785/JCS",
        "timestamp replacement",
        "mask replacement",
        "shape hash",
        "cannot pass by dropping fields",
        "verifier-derived",
        "no empty-success",
        "CANDIDATE_DEBUG_REPLAY",
        "existing promoted eBUS leaves remain authoritative",
        "no public V2",
        "G17",
        "G19",
        "synthetic",
        "Rollback",
        "Validation Precedence",
        "Resource Bounds",
        "Gateway RED Handoff",
    )
    for phrase in required:
        assert phrase in page
    for surface in (
        "`ebus.v1` MCP responses",
        "GraphQL schema",
        "GraphQL eBUS values",
        "HA-consumed GraphQL values",
        "HA identity",
        "eBUS debug output",
        "Portal bootstrap",
        "command routing",
        "semantic registry",
        "`eebus.v1` V1 contract",
    ):
        assert surface in page


def test_msp08_machine_contract_ids_and_closed_registry_are_frozen() -> None:
    evidence_schema = json.loads(read(COEXISTENCE_EVIDENCE_SCHEMA))
    report_schema = json.loads(read(COEXISTENCE_REPORT_SCHEMA))
    registry = json.loads(read(COEXISTENCE_REGISTRY))
    assert evidence_schema["$id"] == (
        "https://docs.helianthus.local/schemas/"
        "multi-runtime-coexistence-evidence-v1.schema.json"
    )
    assert report_schema["$id"] == (
        "https://docs.helianthus.local/schemas/"
        "multi-runtime-coexistence-report-v1.schema.json"
    )
    assert evidence_schema["additionalProperties"] is False
    assert report_schema["additionalProperties"] is False
    assert registry["contract"] == (
        "helianthus.platform.multi-runtime-coexistence-registry.v1"
    )
    assert registry["gate"] == "EEBUS-G18"
    assert registry["excluded_gates"] == ["EEBUS-G17", "EEBUS-G19"]
    assert registry["m7_completion_token"] == (
        "MSP-07@ff511b035b85aef6123fb0853bb3d2f3af6fc01e"
    )
    assert registry["m7_docs_source_commit"] == (
        "ea88fef23ecb154b08f70e7f94b36e1738ed08bf"
    )
    assert registry["scenario_order"] == [
        "EEBUS_DISABLED_BASELINE",
        "EEBUS_DISABLED_CONFIRMED",
        "EEBUS_ENABLED_NO_SERVICES",
        "EEBUS_CONNECTED_CANDIDATE_ONLY",
        "EEBUS_CONFLICTED_WITHHELD",
        "EEBUS_DISABLED_ROLLBACK",
    ]
    assert len(registry["protected_views"]) == 11
    assert len(registry["validation_precedence"]) >= 18
