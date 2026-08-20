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
    assert manifest["required_response_fields"] == ["contractId", "canonicalContractId", "assetRef", "generation", "producedAt", "evaluatedMonotonicNs", "sourceTimeState", "facts", "capabilities", "provenance"]
    assert manifest["operator_authority"] == ["dedicated_listener", "server_identity", "ca_and_trust_root", "client_certificate_issuance", "asset_allowlist", "rotation", "revocation"]
    assert manifest["request_bounds"] == {"method": "POST", "operation_name": "M2MCurrentSnapshot", "max_body_bytes": 16384, "max_query_depth": 8, "max_selected_fields": 256, "max_concurrency_per_client": 1, "requests_per_second_per_client": 1, "burst_per_client": 2, "max_response_bytes": 1048576, "forbidden_graphql_features": ["batching", "aliases", "named_fragments", "directives", "introspection", "get", "subscriptions", "multiple_operations"], "allowed_graphql_features": ["inline_type_conditions_for_value_union"]}
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
        (item["factId"], tuple(sorted((part["key"], part["value"]) for part in item["dimensions"])))
        for item in cases["positive"]["response"]["facts"]
    }
    assert required <= observed
    candidate = copy.deepcopy(cases["positive"])
    candidate["response"]["facts"] = [
        item
        for item in candidate["response"]["facts"]
        if not (
            item["factId"] == "pv.ac.current"
            and item["dimensions"] == [{"key": "phase", "value": "L3"}]
        )
    ]
    assert "capability_outcome" in validate_case(candidate, manifest, canonical)


def test_opaque_dimensions_reject_network_endpoints():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    fact = copy.deepcopy(candidate["response"]["facts"][0])
    fact.update(
        factId="pv.dc.current",
        dimensions=[{"key": "input_id", "value": "192.168.1.1:502"}],
        unit="A",
    )
    candidate["response"]["facts"].append(fact)
    assert "dimension_redaction" in validate_case(candidate, manifest, canonical)


def test_freshness_deadlines_and_state_follow_canonical_policy():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    fact = candidate["response"]["facts"][0]
    fact["freshUntilMonotonicNs"] = str(int(fact["receiptMonotonicNs"]) + 1)
    assert "freshness_policy" in validate_case(candidate, manifest, canonical)


def test_accumulator_continuity_variants_are_closed():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    energy = next(
        item
        for item in candidate["response"]["facts"]
        if item["factId"] == "pv.energy.active_export_total"
    )
    invalid = [
        {"state": "BASELINE", "delta": {"coefficient": "1", "scale": 0}, "modulus": None, "evidenceRef": None},
        {"state": "CONTIGUOUS", "delta": None, "modulus": None, "evidenceRef": None},
        {"state": "ROLLOVER", "delta": {"coefficient": "1", "scale": 0}, "modulus": None, "evidenceRef": "sha256:" + "a" * 64},
        {"state": "RESET", "delta": None, "modulus": None, "evidenceRef": None},
        {"state": "DISCONTINUITY", "delta": {"coefficient": "1", "scale": 0}, "modulus": None, "evidenceRef": None},
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
    fresh_until = int(fact["freshUntilMonotonicNs"])
    retain_until = int(fact["retainUntilMonotonicNs"])

    cases_to_check = [
        (fresh_until - 1, "AVAILABLE", "FRESH"),
        (fresh_until, "AVAILABLE", "STALE"),
        (retain_until - 1, "AVAILABLE", "STALE"),
        (retain_until, "UNAVAILABLE", "EXPIRED"),
    ]
    for evaluated, availability, freshness in cases_to_check:
        candidate["response"]["evaluatedMonotonicNs"] = str(evaluated)
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
    assert "type M2MDecimalValue { coefficient: String!, scale: Int! }" in sdl
    assert "type M2MEnumValue { symbol: String! }" in sdl
    assert "type M2MBitfieldValue { symbols: [String!]! }" in sdl
    assert "type M2MValue {" not in sdl
    assert "M2MValueKind" not in sdl
    manifest = load(MANIFEST)
    assert manifest["value_kind_mapping"] == {
        "decimal": "M2MDecimalValue",
        "enum": "M2MEnumValue",
        "bitfield": "M2MBitfieldValue",
    }


def test_public_provenance_projects_safe_canonical_fields_and_declares_loss():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    required = set(canonical["provenance"]["required"])
    assert set(manifest["opaque_provenance_fields"]) == {
        "originRef",
        "sourceProtocol",
        "sourceProfileId",
        "sourceProfileVersion",
        "sourceValidity",
        "sourceRegistryRef",
        "sourceObservationRef",
        "evidenceRef",
    }
    assert manifest["provenance_projection_loss"] == {
        "source_shadow_ref": "WITHHELD_SOURCE_SHADOW_REFERENCE"
    }
    public_to_canonical = {
        "sourceProtocol": "source_protocol",
        "sourceProfileId": "source_profile_id",
        "sourceProfileVersion": "source_profile_version",
        "sourceValidity": "source_validity",
        "sourceRegistryRef": "source_registry_ref",
        "sourceObservationRef": "source_observation_ref",
        "evidenceRef": "evidence_ref",
    }
    projected = {
        public_to_canonical[field]
        for field in manifest["opaque_provenance_fields"]
        if field != "originRef"
    }
    assert required == projected | set(manifest["provenance_projection_loss"])
    assert set(cases["positive"]["response"]["provenance"][0]) == set(
        manifest["opaque_provenance_fields"]
    )


def test_fixture_is_the_graphql_http_envelope_wire_shape():
    manifest, cases = load(MANIFEST), load(CASES)
    assert manifest["conformance_boundary"] == "GRAPHQL_HTTP_ENVELOPE"
    request = cases["positive"]["request"]
    response = cases["positive"]["response"]
    assert request["method"] == "POST" and request["path"] == manifest["route"]
    assert set(request["body"]) == {"operationName", "query", "variables"}
    assert request["body"]["operationName"] == "M2MCurrentSnapshot"
    assert request["body"]["query"] == manifest["conformance_query"]
    assert "... on M2MDecimalValue" in request["body"]["query"]
    assert "... on M2MEnumValue" in request["body"]["query"]
    assert "... on M2MBitfieldValue" in request["body"]["query"]
    assert set(request["body"]["variables"]["request"]) == {"contractId", "assetRef"}
    assert response["status"] == 200
    payload = response["body"]["data"]["m2mCurrentSnapshot"]
    assert set(payload) == set(manifest["required_response_fields"])
    assert "canonicalContractId" in payload and "canonical_contract_id" not in payload
    fact = payload["facts"][0]
    assert set(fact) == set(manifest["required_fact_fields"])
    assert "factId" in fact and "fact_id" not in fact
    assert fact["dimensions"] == [{"key": "scope", "value": "total"}]
    assert set(fact["value"]) == {"coefficient", "scale"}
    assert "kind" not in fact["value"]
    provenance = payload["provenance"][0]
    assert "sourceProtocol" in provenance and "source_protocol" not in provenance


def test_unknown_or_private_provenance_fields_fail_closed_before_normalization():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    for field in ("unexpected", "sourceShadowContents", "privateFixturePath"):
        candidate = copy.deepcopy(cases["positive"])
        row = candidate["response"]["body"]["data"]["m2mCurrentSnapshot"]["provenance"][0]
        row[field] = "must-not-pass"
        errors = validate_case(candidate, manifest, canonical)
        assert "provenance_fields" in errors or "forbidden_surface" in errors
