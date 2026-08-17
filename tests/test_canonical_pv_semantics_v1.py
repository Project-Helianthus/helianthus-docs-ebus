import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/platform/canonical-pv-semantics-v1.md"
MANIFEST = ROOT / "docs/platform/manifests/canonical-pv-v1.json"
SCHEMA = ROOT / "docs/platform/schemas/canonical-pv-observation-v1.schema.json"
SOURCE_REGISTRY = (
    ROOT
    / "docs/platform/fixtures/canonical-pv/v1/source-registry-bindings.json"
)
SOURCE_REGISTRY_SCHEMA = (
    ROOT
    / "docs/platform/schemas/canonical-pv-source-registry-bindings-v1.schema.json"
)
GOLDEN = (
    ROOT
    / "docs/platform/fixtures/canonical-pv/v1/golden-three-phase.json"
)
MIXED = (
    ROOT
    / "docs/platform/fixtures/canonical-pv/v1/golden-mixed-retention.json"
)
NEGATIVE = (
    ROOT
    / "docs/platform/fixtures/canonical-pv/v1/negative-cases.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from validate_canonical_pv_v1 import (  # noqa: E402
    ValidationError,
    validate,
    validate_semantics,
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fact_key(fact):
    return fact["fact_id"], tuple(sorted(fact["dimensions"].items()))


def schema_accepts(document):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as stream:
        json.dump(document, stream)
        stream.flush()
        result = subprocess.run(
            ["jv", str(SCHEMA), stream.name],
            capture_output=True,
            check=False,
            text=True,
        )
    return result.returncode == 0, result.stdout + result.stderr


def apply_mutation(document, mutation):
    result = copy.deepcopy(document)
    mutations = mutation if isinstance(mutation, list) else [mutation]
    for item in mutations:
        parts = [
            part.replace("~1", "/").replace("~0", "~")
            for part in item["path"].split("/")[1:]
        ]
        parent = result
        for part in parts[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        leaf = parts[-1]
        if item["op"] == "remove":
            if isinstance(parent, list):
                parent.pop(int(leaf))
            else:
                del parent[leaf]
        elif item["op"] in {"add", "replace"}:
            if isinstance(parent, list) and leaf == "-":
                parent.append(item["value"])
            elif isinstance(parent, list):
                parent[int(leaf)] = item["value"]
            else:
                parent[leaf] = item["value"]
        else:
            raise AssertionError(f"unsupported mutation operation: {item['op']}")
    return result


def test_manifest_closes_catalog_and_state_axes():
    manifest = load_json(MANIFEST)
    assert manifest["contract_id"] == "helianthus.canonical-pv/v1"
    assert manifest["status"] == "CANDIDATE_PRE_IMPLEMENTATION"
    assert manifest["owner"] == "helianthus-ebusreg"
    assert manifest["write_authority"] == "NONE"
    decimal = manifest["value_encoding"]["decimal"]
    assert decimal["coefficient_json_type"] == "canonical_integer_string"
    assert decimal["scale_minimum"] == -18
    assert decimal["scale_maximum"] == 18

    facts = {fact["id"]: fact for fact in manifest["facts"]}
    assert set(facts) == {
        "pv.ac.power.active",
        "pv.ac.power.apparent",
        "pv.ac.power.reactive",
        "pv.ac.power_factor",
        "pv.ac.frequency",
        "pv.ac.current",
        "pv.ac.voltage.line_to_neutral",
        "pv.ac.voltage.line_to_line",
        "pv.energy.active_export_total",
        "pv.dc.current",
        "pv.dc.voltage",
        "pv.dc.power.active",
        "pv.dc.energy.active_total",
        "pv.temperature",
        "pv.operating.state",
        "pv.event.flags",
        "pv.rating.ac.active_power",
    }
    assert len(facts) == len(manifest["facts"])
    assert manifest["state_axes"] == {
        "quality": ["GOOD", "SUSPECT", "BAD"],
        "availability": ["AVAILABLE", "UNAVAILABLE", "UNSUPPORTED"],
        "freshness": ["FRESH", "STALE", "EXPIRED"],
    }
    assert manifest["allowed_availability_freshness_pairs"] == [
        "AVAILABLE/FRESH",
        "AVAILABLE/STALE",
        "UNAVAILABLE/EXPIRED",
        "UNSUPPORTED/EXPIRED",
    ]
    assert manifest["value_domains"] == {
        "pv.operating.state.v1": [
            "UNKNOWN",
            "OFF",
            "STANDBY",
            "STARTING",
            "OPERATING",
            "DERATED",
            "FAULT",
            "SHUTTING_DOWN",
        ],
        "pv.event.flags.v1": [
            "GROUND_FAULT",
            "DC_OVER_VOLTAGE",
            "AC_DISCONNECT",
            "DC_DISCONNECT",
            "GRID_DISCONNECT",
            "CABINET_OPEN",
            "MANUAL_SHUTDOWN",
            "OVER_TEMPERATURE",
            "FREQUENCY_OUT_OF_RANGE",
            "VOLTAGE_OUT_OF_RANGE",
            "COMMUNICATION_FAULT",
            "INTERNAL_FAULT",
        ],
    }

    allowed_units = set(manifest["units"])
    allowed_dimensions = set(manifest["dimensions"])
    policy_ids = {policy["id"] for policy in manifest["freshness_policies"]}
    for fact in facts.values():
        assert fact["value_kind"] in {"decimal", "enum", "bitfield"}
        assert fact["unit"] in allowed_units
        assert set(fact["dimensions"]) <= allowed_dimensions
        assert fact["freshness_policy"] in policy_ids
        assert isinstance(fact["accumulator"], bool)
        if fact["value_kind"] in {"enum", "bitfield"}:
            assert fact["value_domain"] in manifest["value_domains"]


def test_freshness_and_counter_policy_are_registry_owned_and_fail_closed():
    manifest = load_json(MANIFEST)
    policies = {
        policy["id"]: (policy["fresh_seconds"], policy["retain_seconds"])
        for policy in manifest["freshness_policies"]
    }
    assert policies == {
        "pv.telemetry.fast.v1": (30, 300),
        "pv.status.v1": (60, 600),
        "pv.accumulator.v1": (900, 86400),
        "pv.rating.v1": (86400, 2592000),
    }
    assert all(fresh < retain for fresh, retain in policies.values())
    assert manifest["lifecycle"]["clock"] == "monotonic_receipt_time"
    assert manifest["lifecycle"]["source_time_drives_expiry"] is False
    assert (
        manifest["lifecycle"]["source_error_deletes_prior_observation"]
        is False
    )
    assert manifest["source_binding"] == {
        "version": 1,
        "selected_sources_per_update": 1,
        "ambiguous_sources": "FAIL_CLOSED",
        "gateway_schedule_is_precedence": False,
    }
    transitions = [
        (item["from"], item["event"], item["to"])
        for item in manifest["lifecycle"]["transitions"]
    ]
    assert transitions == [
        ("AVAILABLE/FRESH", "fresh_threshold_elapsed", "AVAILABLE/STALE"),
        ("AVAILABLE/FRESH", "accepted_observation", "AVAILABLE/FRESH"),
        ("AVAILABLE/STALE", "accepted_observation", "AVAILABLE/FRESH"),
        ("AVAILABLE/STALE", "retain_threshold_elapsed", "UNAVAILABLE/EXPIRED"),
        ("UNAVAILABLE/EXPIRED", "accepted_observation", "AVAILABLE/FRESH"),
    ]
    assert len(transitions) == len(set(transitions))

    continuity = manifest["counter_continuity"]
    assert continuity["states"] == [
        "BASELINE",
        "CONTIGUOUS",
        "ROLLOVER",
        "RESET",
        "DISCONTINUITY",
    ]
    assert continuity["unexplained_decrease"] == "DISCONTINUITY_NO_DELTA"
    assert continuity["guessed_rollover_or_reset_forbidden"] is True


def test_source_ids_are_not_silently_repurposed():
    manifest = load_json(MANIFEST)
    source_ids = {
        item["source_id"]: item for item in manifest["source_id_compatibility"]
    }
    assert set(source_ids) == {
        "sunspec.phase1@1.0.0",
        "sunspec.inverter.three_phase.monitoring@1.0.0",
    }
    assert all(item["canonical_alias"] is None for item in source_ids.values())
    assert manifest["compatibility"]["reinterpretation_requires_new_major_contract"]
    assert (
        manifest["compatibility"]["required_pack_member_change_requires_new_pack_id"]
        is True
    )
    assert manifest["compatibility"]["additive_optional_facts_allowed"] is False


def test_golden_fixture_satisfies_three_phase_capability():
    manifest = load_json(MANIFEST)
    golden = load_json(GOLDEN)
    assert golden["contract_id"] == manifest["contract_id"]
    assert golden["asset_ref"] == "pv-asset-01"
    assert isinstance(golden["generation"], int) and golden["generation"] > 0

    catalog = {fact["id"]: fact for fact in manifest["facts"]}
    observed = {fact_key(fact): fact for fact in golden["facts"]}
    assert len(observed) == len(golden["facts"])
    required = manifest["capability_packs"][0]["required"]
    for requirement in required:
        key = (
            requirement["fact_id"],
            tuple(sorted(requirement["dimensions"].items())),
        )
        assert key in observed

    for fact in golden["facts"]:
        definition = catalog[fact["fact_id"]]
        assert fact["unit"] == definition["unit"]
        assert set(fact["dimensions"]) == set(definition["dimensions"])
        assert fact["value"]["kind"] == definition["value_kind"]
        assert fact["quality"] == "GOOD"
        assert fact["availability"] == "AVAILABLE"
        assert fact["freshness"] == "FRESH"
        if fact["value"]["kind"] == "decimal":
            assert set(fact["value"]) == {"kind", "coefficient", "scale"}
            assert re.fullmatch(r"-?(0|[1-9][0-9]*)", fact["value"]["coefficient"])
            assert isinstance(fact["value"]["scale"], int)
    lifetime = next(
        fact
        for fact in golden["facts"]
        if fact["fact_id"] == "pv.energy.active_export_total"
    )
    assert lifetime["value"]["coefficient"] == "9007199254740993"
    assert int(lifetime["value"]["coefficient"]) > 2**53
    dc_current = next(
        fact
        for fact in golden["facts"]
        if fact["fact_id"] == "pv.dc.current"
    )
    assert len(dc_current["dimensions"]["input_id"]) == 64


def test_golden_temporal_provenance_and_projection_are_closed():
    manifest = load_json(MANIFEST)
    golden = load_json(GOLDEN)
    assert golden["source_time_state"] == "UNAVAILABLE"
    assert not validate_semantics(golden, manifest, load_json(SOURCE_REGISTRY))
    for fact in golden["facts"]:
        temporal = fact["temporal"]
        assert temporal["receipt_monotonic_ns"] < temporal["fresh_until_monotonic_ns"]
        assert temporal["fresh_until_monotonic_ns"] < temporal["retain_until_monotonic_ns"]

    provenance = golden["source_provenance"]
    assert set(provenance) == set(manifest["provenance"]["required"])
    for key in ("source_observation_ref", "source_shadow_ref", "evidence_ref"):
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", provenance[key])

    forbidden = {"endpoint", "address", "credentials", "raw_words"}
    serialized = json.dumps(golden, sort_keys=True).lower()
    assert not any(f'"{field}"' in serialized for field in forbidden)
    outcomes = {item["outcome"] for item in golden["projection_report"]}
    assert outcomes == {"MAPPED", "WITHHELD"}
    assert outcomes <= set(manifest["projection_outcomes"])

    accumulator = next(
        fact
        for fact in golden["facts"]
        if fact["fact_id"] == "pv.energy.active_export_total"
    )
    assert accumulator["continuity"] == {
        "state": "BASELINE",
        "delta": None,
        "modulus": None,
        "evidence_ref": None,
    }


def test_scaled_accumulator_delta_uses_canonical_decimal():
    manifest = load_json(MANIFEST)
    candidate = copy.deepcopy(load_json(GOLDEN))
    accumulator = next(
        fact
        for fact in candidate["facts"]
        if fact["fact_id"] == "pv.energy.active_export_total"
    )
    accumulator["continuity"] = {
        "state": "CONTIGUOUS",
        "delta": {"kind": "decimal", "coefficient": "1", "scale": -2},
        "modulus": None,
        "evidence_ref": None,
    }
    accepted, output = schema_accepts(candidate)
    assert accepted, output
    assert not validate_semantics(candidate, manifest, load_json(SOURCE_REGISTRY))


def test_protocol_neutral_source_registry_binding():
    manifest = load_json(MANIFEST)
    source_registry = copy.deepcopy(load_json(SOURCE_REGISTRY))
    candidate = copy.deepcopy(load_json(GOLDEN))
    provenance = candidate["source_provenance"]
    provenance["source_protocol"] = "eebus_spine"
    provenance["source_profile_id"] = "eebus.pv.three_phase@1.0.0"
    provenance["source_profile_version"] = "1.0.0"
    provenance["source_registry_ref"] = "sha256:cf17b95284984414c9d8ec13b5dde1e2dab5b12c81373436c5849669f61fc22a"
    candidate["origins"][0] = copy.deepcopy(provenance)
    source_registry["entries"].append(
        {
            "source_protocol": "eebus_spine",
            "source_profile_id": "eebus.pv.three_phase@1.0.0",
            "source_profile_version": "1.0.0",
            "source_validity": "terminal_verified",
            "registry_ref": provenance["source_registry_ref"],
        }
    )
    accepted, output = schema_accepts(candidate)
    assert accepted, output
    assert not validate_semantics(candidate, manifest, source_registry)


def test_mixed_retention_preserves_fact_level_origins():
    manifest = load_json(MANIFEST)
    source_registry = load_json(SOURCE_REGISTRY)
    mixed = load_json(MIXED)
    accepted, output = schema_accepts(mixed)
    assert accepted, output
    assert not validate_semantics(mixed, manifest, source_registry)
    facts = {fact["fact_id"]: fact for fact in mixed["facts"]}
    assert facts["pv.ac.power.active"]["origin_ref"] == mixed["source_provenance"]["source_observation_ref"]
    assert facts["pv.energy.active_export_total"]["origin_ref"] != facts["pv.ac.power.active"]["origin_ref"]
    assert facts["pv.energy.active_export_total"]["freshness"] == "STALE"


def test_schema_is_recursive_closed_and_golden_validates():
    def visit(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(load_json(SCHEMA))
    visit(load_json(SOURCE_REGISTRY_SCHEMA))
    accepted, output = schema_accepts(load_json(GOLDEN))
    assert accepted, output


def test_public_manifest_aware_validator_accepts_golden():
    for document in (GOLDEN, MIXED):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/validate_canonical_pv_v1.py"),
                "--document",
                str(document),
                "--manifest",
                str(MANIFEST),
                "--schema",
                str(SCHEMA),
                "--source-registry",
                str(SOURCE_REGISTRY),
                "--source-registry-schema",
                str(SOURCE_REGISTRY_SCHEMA),
            ],
            capture_output=True,
            check=False,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout.strip() == "canonical_pv_v1_ok"


def test_negative_fixtures_are_rejected_by_declared_rule():
    manifest = load_json(MANIFEST)
    golden = load_json(GOLDEN)
    negative = load_json(NEGATIVE)
    assert negative["fixture_contract"] == "helianthus.canonical-pv.negative-cases/v1"
    assert negative["base"] == GOLDEN.name
    assert len(negative["cases"]) >= 6
    assert len({case["id"] for case in negative["cases"]}) == len(negative["cases"])
    for case in negative["cases"]:
        assert set(case) == {"id", "mutation", "expected_rule"}
        candidate = apply_mutation(golden, case["mutation"])
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as stream:
            json.dump(candidate, stream)
            stream.flush()
            with pytest.raises(ValidationError):
                validate(
                    Path(stream.name),
                    MANIFEST,
                    SCHEMA,
                    SOURCE_REGISTRY,
                    SOURCE_REGISTRY_SCHEMA,
                )
        accepted, _ = schema_accepts(candidate)
        if not accepted:
            assert case["expected_rule"] in {
                "schema_closed",
                "continuity_evidence",
                "dimension_domain",
                "source_admission",
                "projection_binding",
                "projection_redaction",
                "provenance_redaction",
                "provenance_binding",
                "lifecycle_state_pair",
                "capability_uniqueness",
                "capability_inventory",
                "projection_coverage",
            }
            continue
        assert case["expected_rule"] in validate_semantics(
            candidate,
            manifest,
            load_json(SOURCE_REGISTRY),
        )


def test_human_contract_preserves_ownership_and_private_boundary():
    text = " ".join(DOC.read_text(encoding="utf-8").split())
    required_phrases = [
        "`helianthus-ebusreg` owns the canonical fact identity",
        "gateway scheduling order is never precedence",
        "binary JSON floating-point values are forbidden",
        "must never guess rollover or reset",
        "`MAPPED`, `WITHHELD`, or `UNREPRESENTABLE`",
        "`PUBLIC_GRAPHQL_M2M_V1`",
        "no Fronius support claim",
    ]
    for phrase in required_phrases:
        assert phrase in text
