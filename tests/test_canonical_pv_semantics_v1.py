import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/platform/canonical-pv-semantics-v1.md"
MANIFEST = ROOT / "docs/platform/manifests/canonical-pv-v1.json"
GOLDEN = (
    ROOT
    / "docs/platform/fixtures/canonical-pv/v1/golden-three-phase.json"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fact_key(fact):
    return fact["fact_id"], tuple(sorted(fact["dimensions"].items()))


def test_manifest_closes_catalog_and_state_axes():
    manifest = load_json(MANIFEST)
    assert manifest["contract_id"] == "helianthus.canonical-pv/v1"
    assert manifest["status"] == "CANDIDATE_PRE_IMPLEMENTATION"
    assert manifest["owner"] == "helianthus-ebusreg"
    assert manifest["write_authority"] == "NONE"

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

    allowed_units = set(manifest["units"])
    allowed_dimensions = set(manifest["dimensions"])
    policy_ids = {policy["id"] for policy in manifest["freshness_policies"]}
    for fact in facts.values():
        assert fact["value_kind"] in {"decimal", "enum", "bitfield"}
        assert fact["unit"] in allowed_units
        assert set(fact["dimensions"]) <= allowed_dimensions
        assert fact["freshness_policy"] in policy_ids
        assert isinstance(fact["accumulator"], bool)


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
            assert isinstance(fact["value"]["coefficient"], int)
            assert isinstance(fact["value"]["scale"], int)


def test_golden_temporal_provenance_and_projection_are_closed():
    manifest = load_json(MANIFEST)
    golden = load_json(GOLDEN)
    temporal = golden["temporal"]
    assert temporal["receipt_monotonic_ns"] < temporal["fresh_until_monotonic_ns"]
    assert temporal["fresh_until_monotonic_ns"] < temporal["retain_until_monotonic_ns"]
    assert temporal["source_time_state"] == "UNAVAILABLE"

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
    assert accumulator["continuity"] == {"state": "BASELINE", "delta": None}


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
