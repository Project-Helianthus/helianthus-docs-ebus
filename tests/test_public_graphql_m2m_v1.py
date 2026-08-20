import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/platform/manifests/public-graphql-m2m-v1.json"
CANONICAL = ROOT / "docs/platform/manifests/canonical-pv-v1.json"
CASES = ROOT / "docs/platform/fixtures/public-graphql-m2m/v1/cases.json"
SDL = ROOT / "api/public-graphql-m2m-v1.graphql"
DOC = ROOT / "docs/platform/public-graphql-m2m-v1.md"
sys.path.insert(0, str(ROOT / "scripts"))
from validate_public_graphql_m2m_v1 import validate, validate_case  # noqa: E402


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_manifest_is_locked_to_canonical_catalog_and_closed_public_surface():
    manifest, canonical = load(MANIFEST), load(CANONICAL)
    assert manifest["route"] == "/graphql/m2m/v1"
    assert manifest["source_contract"] == canonical["contract_id"]
    assert manifest["catalog_fact_ids"] == [fact["id"] for fact in canonical["facts"]]
    assert manifest["query_only"] and manifest["single_asset"]
    assert manifest["dedicated_tls_listener"] is True
    assert len(canonical["facts"]) == 17
    assert manifest["max_facts_per_snapshot"] == 256
    assert manifest["max_provenance_per_snapshot"] == 256
    assert manifest["max_capabilities_per_snapshot"] == 1
    assert manifest["required_response_fields"] == ["contract_id", "canonical_contract_id", "asset_ref", "generation", "produced_at", "evaluated_monotonic_ns", "source_time_state", "facts", "capabilities", "provenance"]
    assert manifest["operator_authority"] == ["dedicated_listener", "server_identity", "ca_and_trust_root", "client_certificate_issuance", "asset_allowlist", "rotation", "revocation"]
    assert manifest["request_bounds"] == {"method": "POST", "operation_name": "M2MCurrentSnapshot", "max_body_bytes": 16384, "max_query_depth": 8, "max_selected_fields": 256, "max_concurrency_per_client": 1, "requests_per_second_per_client": 1, "burst_per_client": 2, "max_response_bytes": 1048576, "forbidden_graphql_features": ["batching", "aliases", "fragments", "directives", "introspection", "get", "subscriptions", "multiple_operations"]}
    assert manifest["error_contract"]["partial_snapshot_on_error"] is False
    assert manifest["credential_rotation"]["maximum_simultaneously_valid_certificates_per_principal"] == 2
    assert manifest["forbidden_surface"] == ["raw_registers", "source_shadow", "endpoints", "mutations", "subscriptions", "history", "unbounded_lists", "generic_graphql_fallback"]


def test_sdl_is_structurally_query_only_and_has_no_generic_surface():
    sdl = SDL.read_text(encoding="utf-8")
    assert "type Query" in sdl and "m2mCurrentSnapshot" in sdl
    assert "type Mutation" not in sdl and "type Subscription" not in sdl
    for required in ("canonicalContractId", "producedAt", "sourceTimeState", "M2MSourceTimeState", "symbols: [String!]", "M2MCapabilityOutcome"):
        assert required in sdl
    for forbidden in ("rawRegister", "sourceShadow", "endpoint", "history", "nodes"):
        assert forbidden not in sdl


def test_fixture_and_document_cover_security_recovery_and_private_ingress_boundary():
    validate(MANIFEST, CANONICAL, CASES)
    text = DOC.read_text(encoding="utf-8")
    for phrase in ("dedicated TLS listener", "verified server identity", "per-client mTLS", "fails closed", "fresh full snapshot", "not comparable across restart", "only public semantic ingress"):
        assert phrase in text


def test_negative_cases_are_rejected_with_declared_category():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    for negative in cases["negative"]:
        candidate = copy.deepcopy(cases["positive"])
        parent = candidate
        parts = negative["path"].split("/")[1:]
        for part in parts[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        if isinstance(parent, list):
            parent[int(parts[-1])] = negative["value"]
        else:
            parent[parts[-1]] = negative["value"]
        assert negative["error"] in validate_case(candidate, manifest, canonical)


def test_validator_cli_is_deterministic():
    result = subprocess.run([sys.executable, "scripts/validate_public_graphql_m2m_v1.py", "--manifest", str(MANIFEST), "--canonical-manifest", str(CANONICAL), "--cases", str(CASES)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "public_graphql_m2m_v1_ok"


def test_capability_outcome_is_derived_from_required_fact_identities():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    required = {
        (item["fact_id"], tuple(sorted(item["dimensions"].items())))
        for item in canonical["capability_packs"][0]["required"]
    }
    observed = {
        (item["fact_id"], tuple(sorted(item["dimensions"].items())))
        for item in cases["positive"]["response"]["facts"]
    }
    assert required <= observed
    candidate = copy.deepcopy(cases["positive"])
    candidate["response"]["facts"] = [
        item
        for item in candidate["response"]["facts"]
        if not (
            item["fact_id"] == "pv.ac.current"
            and item["dimensions"] == {"phase": "L3"}
        )
    ]
    assert "capability_outcome" in validate_case(candidate, manifest, canonical)


def test_opaque_dimensions_reject_network_endpoints():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    fact = copy.deepcopy(candidate["response"]["facts"][0])
    fact.update(
        fact_id="pv.dc.current",
        dimensions={"input_id": "192.168.1.1:502"},
        unit="A",
    )
    candidate["response"]["facts"].append(fact)
    assert "dimension_redaction" in validate_case(candidate, manifest, canonical)


def test_freshness_deadlines_and_state_follow_canonical_policy():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    fact = candidate["response"]["facts"][0]
    fact["fresh_until_monotonic_ns"] = str(int(fact["receipt_monotonic_ns"]) + 1)
    assert "freshness_policy" in validate_case(candidate, manifest, canonical)


def test_accumulator_continuity_variants_are_closed():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    energy = next(
        item
        for item in candidate["response"]["facts"]
        if item["fact_id"] == "pv.energy.active_export_total"
    )
    invalid = [
        {"state": "BASELINE", "delta": {"kind": "DECIMAL", "coefficient": "1", "scale": 0}, "modulus": None, "evidence_ref": None},
        {"state": "CONTIGUOUS", "delta": None, "modulus": None, "evidence_ref": None},
        {"state": "ROLLOVER", "delta": {"kind": "DECIMAL", "coefficient": "1", "scale": 0}, "modulus": None, "evidence_ref": "sha256:" + "a" * 64},
        {"state": "RESET", "delta": None, "modulus": None, "evidence_ref": None},
        {"state": "DISCONTINUITY", "delta": {"kind": "DECIMAL", "coefficient": "1", "scale": 0}, "modulus": None, "evidence_ref": None},
    ]
    for continuity in invalid:
        energy["continuity"] = continuity
        assert "continuity" in validate_case(candidate, manifest, canonical)


def test_freshness_transition_boundaries_are_exact():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    candidate["response"]["facts"] = [candidate["response"]["facts"][0]]
    candidate["response"]["capabilities"][0]["outcome"] = "NOT_SATISFIED"
    fact = candidate["response"]["facts"][0]
    fresh_until = int(fact["fresh_until_monotonic_ns"])
    retain_until = int(fact["retain_until_monotonic_ns"])

    cases_to_check = [
        (fresh_until - 1, "AVAILABLE", "FRESH"),
        (fresh_until, "AVAILABLE", "STALE"),
        (retain_until - 1, "AVAILABLE", "STALE"),
        (retain_until, "UNAVAILABLE", "EXPIRED"),
    ]
    for evaluated, availability, freshness in cases_to_check:
        candidate["response"]["evaluated_monotonic_ns"] = str(evaluated)
        fact["availability"] = availability
        fact["freshness"] = freshness
        errors = validate_case(candidate, manifest, canonical)
        assert "freshness_evaluation" not in errors
        assert "state_axes" not in errors


def test_empty_success_snapshot_is_rejected():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    candidate["response"]["facts"] = []
    candidate["response"]["provenance"] = []
    candidate["response"]["capabilities"][0]["outcome"] = "NOT_SATISFIED"
    assert "empty_snapshot" in validate_case(candidate, manifest, canonical)


def test_validator_fails_closed_on_wrong_json_container_types(tmp_path):
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    malformed = [
        [],
        {"request": [], "response": {}},
        {"request": {}, "response": []},
        {"request": {}, "response": {"facts": [None]}},
        {"request": {}, "response": {"facts": ["not-an-object"]}},
    ]
    for candidate in malformed:
        assert "structural_shape" in validate_case(candidate, manifest, canonical)

    invalid_cases = copy.deepcopy(cases)
    invalid_cases["positive"]["response"] = []
    invalid_path = tmp_path / "invalid-cases.json"
    invalid_path.write_text(json.dumps(invalid_cases), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_public_graphql_m2m_v1.py",
            "--manifest",
            str(MANIFEST),
            "--canonical-manifest",
            str(CANONICAL),
            "--cases",
            str(invalid_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert result.stderr.startswith("public_graphql_m2m_v1_invalid:")
    assert "Traceback" not in result.stderr


def test_generation_is_a_positive_canonical_integer_string():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    candidate["response"]["generation"] = "0"
    assert "time_identity" in validate_case(candidate, manifest, canonical)


def test_sdl_uses_closed_non_null_value_variants():
    sdl = SDL.read_text(encoding="utf-8")
    assert "value: M2MValue!" in sdl
    assert "union M2MValue = M2MDecimalValue | M2MEnumValue | M2MBitfieldValue" in sdl
    assert "type M2MDecimalValue { kind: M2MValueKind!, coefficient: String!, scale: Int! }" in sdl
    assert "type M2MEnumValue { kind: M2MValueKind!, symbol: String! }" in sdl
    assert "type M2MBitfieldValue { kind: M2MValueKind!, symbols: [String!]! }" in sdl
    assert "type M2MValue {" not in sdl


def test_public_provenance_projects_safe_canonical_fields_and_declares_loss():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    required = set(canonical["provenance"]["required"])
    assert set(manifest["opaque_provenance_fields"]) == {
        "origin_ref",
        "source_protocol",
        "source_profile_id",
        "source_profile_version",
        "source_validity",
        "source_registry_ref",
        "source_observation_ref",
        "evidence_ref",
    }
    assert manifest["provenance_projection_loss"] == {
        "source_shadow_ref": "WITHHELD_SOURCE_SHADOW_REFERENCE"
    }
    assert required == (
        set(manifest["opaque_provenance_fields"]) - {"origin_ref"}
    ) | set(manifest["provenance_projection_loss"])
    assert set(cases["positive"]["response"]["provenance"][0]) == set(
        manifest["opaque_provenance_fields"]
    )
