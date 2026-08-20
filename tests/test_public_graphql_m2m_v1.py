import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/platform/manifests/public-graphql-m2m-v1.json"
CANONICAL = ROOT / "docs/platform/manifests/canonical-pv-v1.json"
CASES = ROOT / "docs/platform/fixtures/public-graphql-m2m/v1/cases.json"
SDL = ROOT / "api/public-graphql-m2m-v1.graphql"
DOC = ROOT / "docs/platform/public-graphql-m2m-v1.md"
sys.path.insert(0, str(ROOT / "scripts"))
from validate_public_graphql_m2m_v1 import (  # noqa: E402
    ValidationError,
    validate,
    validate_case,
    validate_query_document,
)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def response_payload(case):
    return case["response"]["body"]["data"]["m2mCurrentSnapshot"]


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
    assert manifest["required_response_fields"] == ["contractId", "canonicalContractId", "assetRef", "generation", "producedAt", "evaluatedMonotonicNs", "sourceTimeState", "currentSourceOriginRef", "facts", "capabilities", "provenance", "requestedOutputs", "projectionReport"]
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
    capability_payload = cases["capability_satisfied_projection"]
    observed = {
        (item["factId"], tuple(sorted((part["key"], part["value"]) for part in item["dimensions"])))
        for item in capability_payload["facts"]
    }
    assert required <= observed
    candidate = copy.deepcopy(cases["positive"])
    candidate["response"]["body"]["data"]["m2mCurrentSnapshot"] = copy.deepcopy(
        capability_payload
    )
    candidate["request"]["body"]["variables"]["request"]["assetRef"] = (
        capability_payload["assetRef"]
    )
    candidate["request"]["rawBody"] = json.dumps(
        candidate["request"]["body"], separators=(",", ":")
    )
    payload = response_payload(candidate)
    payload["facts"] = [
        item
        for item in payload["facts"]
        if not (
            item["factId"] == "pv.ac.current"
            and item["dimensions"] == [{"key": "phase", "value": "L3"}]
        )
    ]
    assert "capability_outcome" in validate_case(candidate, manifest, canonical)


def test_opaque_dimensions_reject_network_endpoints():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    payload = response_payload(candidate)
    fact = copy.deepcopy(payload["facts"][0])
    fact.update(
        factId="pv.dc.current",
        dimensions=[{"key": "input_id", "value": "192.168.1.1:502"}],
        unit="A",
    )
    payload["facts"].append(fact)
    assert "dimension_redaction" in validate_case(candidate, manifest, canonical)


def test_freshness_deadlines_and_state_follow_canonical_policy():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    fact = response_payload(candidate)["facts"][0]
    fact["freshUntilMonotonicNs"] = str(int(fact["receiptMonotonicNs"]) + 1)
    assert "freshness_policy" in validate_case(candidate, manifest, canonical)


def test_accumulator_continuity_variants_are_closed():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    energy = next(
        item
        for item in response_payload(candidate)["facts"]
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
    payload = response_payload(candidate)
    payload["facts"] = [payload["facts"][0]]
    payload["capabilities"][0]["outcome"] = "NOT_SATISFIED"
    fact = payload["facts"][0]
    fresh_until = int(fact["freshUntilMonotonicNs"])
    retain_until = int(fact["retainUntilMonotonicNs"])

    cases_to_check = [
        (fresh_until - 1, "AVAILABLE", "FRESH"),
        (fresh_until, "AVAILABLE", "STALE"),
        (retain_until - 1, "AVAILABLE", "STALE"),
        (retain_until, "UNAVAILABLE", "EXPIRED"),
    ]
    for evaluated, availability, freshness in cases_to_check:
        payload["evaluatedMonotonicNs"] = str(evaluated)
        fact["availability"] = availability
        fact["freshness"] = freshness
        errors = validate_case(candidate, manifest, canonical)
        assert "freshness_evaluation" not in errors
        assert "state_axes" not in errors


def test_empty_success_snapshot_is_rejected():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    payload = response_payload(candidate)
    payload["facts"] = []
    payload["provenance"] = []
    payload["capabilities"][0]["outcome"] = "NOT_SATISFIED"
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
    response_payload(candidate)["generation"] = "0"
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
    assert set(response_payload(cases["positive"])["provenance"][0]) == set(
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


def test_provenance_is_bound_to_profile_version_registry_and_unique_origin():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    mutations = [
        ("sourceProfileVersion", "2.0.0", "provenance_binding"),
        ("sourceRegistryRef", "sha256:" + "a" * 64, "provenance_binding"),
    ]
    for field, value, category in mutations:
        candidate = copy.deepcopy(cases["positive"])
        response_payload(candidate)["provenance"][0][field] = value
        assert category in validate_case(candidate, manifest, canonical)

    duplicate = copy.deepcopy(cases["positive"])
    rows = response_payload(duplicate)["provenance"]
    rows.append(copy.deepcopy(rows[0]))
    assert "origin_uniqueness" in validate_case(duplicate, manifest, canonical)


def test_http_success_status_is_exact_integer_200():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    candidate["response"]["status"] = 200.0
    assert "response_envelope" in validate_case(candidate, manifest, canonical)


def test_http_envelope_byte_bounds_are_enforced():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    oversized_response = copy.deepcopy(cases["positive"])
    response_payload(oversized_response)["facts"][0]["value"]["coefficient"] = (
        "1" * (manifest["request_bounds"]["max_response_bytes"] + 1)
    )
    assert "response_bytes" in validate_case(
        oversized_response, manifest, canonical
    )

    oversized_request = copy.deepcopy(cases["positive"])
    oversized_request["request"]["body"]["padding"] = (
        "x" * manifest["request_bounds"]["max_body_bytes"]
    )
    assert "request_bytes" in validate_case(oversized_request, manifest, canonical)


def test_deep_unknown_json_fails_closed_without_recursion_error():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(cases["positive"])
    nested = {}
    cursor = nested
    for _ in range(1500):
        cursor["nested"] = {}
        cursor = cursor["nested"]
    response_payload(candidate)["facts"][0]["unknown"] = nested
    errors = validate_case(candidate, manifest, canonical)
    assert "structural_shape" in errors


def test_raw_json_admission_rejects_depth_and_duplicate_keys(tmp_path):
    manifest = load(MANIFEST)
    assert manifest["json_admission"] == {
        "max_depth": 64,
        "duplicate_keys": "REJECT_BEFORE_SEMANTIC_DECODE",
    }
    common = [
        sys.executable,
        "scripts/validate_public_graphql_m2m_v1.py",
        "--manifest",
        str(MANIFEST),
        "--canonical-manifest",
        str(CANONICAL),
        "--cases",
    ]

    deep_path = tmp_path / "deep.json"
    depth = manifest["json_admission"]["max_depth"] + 1
    deep_path.write_text('{"nested":' * depth + "null" + "}" * depth, encoding="utf-8")
    deep = subprocess.run(common + [str(deep_path)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert deep.returncode == 1
    assert "JSON nesting exceeds max_depth=64" in deep.stderr
    assert "Traceback" not in deep.stderr

    duplicate_path = tmp_path / "duplicate.json"
    raw = CASES.read_text(encoding="utf-8")
    duplicate = raw.replace(
        '"contractId": "PUBLIC_GRAPHQL_M2M_V1",',
        '"contractId": "PUBLIC_GRAPHQL_M2M_V1", "contractId": "PUBLIC_GRAPHQL_M2M_V2",',
        1,
    )
    duplicate_path.write_text(duplicate, encoding="utf-8")
    duplicate_result = subprocess.run(common + [str(duplicate_path)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert duplicate_result.returncode == 1
    assert "duplicate JSON key: contractId" in duplicate_result.stderr
    assert "Traceback" not in duplicate_result.stderr


def test_source_registry_fixture_path_is_manifest_authority():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    candidate = copy.deepcopy(manifest)
    candidate["source_registry_fixture"] = "docs/platform/fixtures/does-not-exist.json"
    assert "provenance_binding" in validate_case(
        cases["positive"], candidate, canonical
    )


def test_authenticated_errors_have_one_exact_graphql_envelope_each():
    manifest, cases = load(MANIFEST), load(CASES)
    expected = {
        "CONTRACT_INCOMPATIBLE",
        "ASSET_FORBIDDEN",
        "ASSET_NOT_FOUND",
        "SOURCE_UNAVAILABLE",
        "REQUEST_INVALID",
        "QUERY_REJECTED",
        "REQUEST_LIMIT_EXCEEDED",
    }
    assert {item["code"] for item in cases["errors"]} == expected
    for item in cases["errors"]:
        response = item["response"]
        assert response["status"] == 200
        assert response["body"]["data"] is None
        assert response["body"]["errors"] == [
            {
                "message": "M2M request failed",
                "path": ["m2mCurrentSnapshot"],
                "extensions": {"code": item["code"]},
            }
        ]
    assert manifest["error_contract"]["authenticated_graphql_http_status"] == 200


def test_mixed_retention_binds_one_current_source_origin():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    payload = response_payload(cases["positive"])
    assert "currentSourceOriginRef" in manifest["required_response_fields"]
    assert len(payload["provenance"]) == 2
    assert payload["currentSourceOriginRef"] == payload["provenance"][0]["originRef"]
    retained = next(
        fact
        for fact in payload["facts"]
        if fact["factId"] == "pv.energy.active_export_total"
    )
    assert retained["originRef"] == payload["provenance"][1]["originRef"]
    assert validate_case(cases["positive"], manifest, canonical) == []

    candidate = copy.deepcopy(cases["positive"])
    response_payload(candidate)["currentSourceOriginRef"] = "sha256:" + "f" * 64
    assert "current_source_binding" in validate_case(candidate, manifest, canonical)
    retained_ref = response_payload(cases["positive"])["provenance"][1]["originRef"]
    retained_as_current = copy.deepcopy(cases["positive"])
    response_payload(retained_as_current)["currentSourceOriginRef"] = retained_ref
    assert "current_source_binding" in validate_case(
        retained_as_current, manifest, canonical
    )


def test_request_rejection_classes_map_to_closed_error_codes():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    assert manifest["request_rejection_codes"] == {
        "malformed_json": "REQUEST_INVALID",
        "duplicate_json_key": "REQUEST_INVALID",
        "request_envelope": "REQUEST_INVALID",
        "query_shape": "QUERY_REJECTED",
        "forbidden_graphql_feature": "QUERY_REJECTED",
        "request_body_bytes": "REQUEST_LIMIT_EXCEEDED",
        "query_depth": "REQUEST_LIMIT_EXCEEDED",
        "selected_fields": "REQUEST_LIMIT_EXCEEDED",
        "concurrency": "REQUEST_LIMIT_EXCEEDED",
        "rate": "REQUEST_LIMIT_EXCEEDED",
    }
    alias = copy.deepcopy(cases["positive"])
    alias["request"]["body"]["query"] = alias["request"]["body"]["query"].replace(
        "m2mCurrentSnapshot(request:", "snapshot: m2mCurrentSnapshot(request:", 1
    )
    assert "query_shape" in validate_case(alias, manifest, canonical)
    assert manifest["request_rejection_codes"]["query_shape"] == "QUERY_REJECTED"

    oversized = copy.deepcopy(cases["positive"])
    oversized["request"]["body"]["padding"] = "x" * manifest["request_bounds"]["max_body_bytes"]
    assert "request_bytes" in validate_case(oversized, manifest, canonical)
    assert manifest["request_rejection_codes"]["request_body_bytes"] == "REQUEST_LIMIT_EXCEEDED"


def test_raw_request_body_is_authoritative_and_bounded_before_decode():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    request = cases["positive"]["request"]
    assert json.loads(request["rawBody"]) == request["body"]
    oversized = copy.deepcopy(cases["positive"])
    oversized["request"]["rawBody"] = (
        " " * (manifest["request_bounds"]["max_body_bytes"] + 1)
        + oversized["request"]["rawBody"]
    )
    assert "request_bytes" in validate_case(oversized, manifest, canonical)


def test_request_rejection_fixtures_bind_input_class_to_exact_response():
    manifest, cases = load(MANIFEST), load(CASES)
    expected = manifest["request_rejection_codes"]
    assert {
        item["category"]: item["code"] for item in cases["request_rejections"]
    } == expected
    envelopes = {item["code"]: item["response"] for item in cases["errors"]}
    for item in cases["request_rejections"]:
        assert set(item) == {"category", "code", "stimulus", "responseCodeRef"}
        assert item["responseCodeRef"] == item["code"]
        assert envelopes[item["responseCodeRef"]]["body"]["errors"][0][
            "extensions"
        ]["code"] == item["code"]


def test_error_envelope_mutations_are_rejected_end_to_end(tmp_path):
    cases = load(CASES)
    mutations = []

    wrong_status = copy.deepcopy(cases)
    wrong_status["errors"][0]["response"]["status"] = 418
    mutations.append(wrong_status)

    wrong_body = copy.deepcopy(cases)
    wrong_body["errors"][0]["response"]["body"] = {"detail": "leak"}
    mutations.append(wrong_body)

    for field, value in (
        ("message", "leak"),
        ("path", ["other"]),
        ("extensions", {"code": "WRONG"}),
    ):
        candidate = copy.deepcopy(cases)
        candidate["errors"][0]["response"]["body"]["errors"][0][field] = value
        mutations.append(candidate)

    for index, candidate in enumerate(mutations):
        candidate_path = tmp_path / f"invalid-error-{index}.json"
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        with pytest.raises(ValidationError):
            validate(MANIFEST, CANONICAL, candidate_path)


def test_closed_error_and_request_binding_cardinality_rejects_duplicates(tmp_path):
    cases = load(CASES)
    duplicates = []

    duplicate_error = copy.deepcopy(cases)
    duplicate_error["errors"].append(copy.deepcopy(duplicate_error["errors"][0]))
    duplicates.append(duplicate_error)

    duplicate_binding = copy.deepcopy(cases)
    duplicate_binding["request_rejections"].append(
        copy.deepcopy(duplicate_binding["request_rejections"][0])
    )
    duplicates.append(duplicate_binding)

    for index, candidate in enumerate(duplicates):
        candidate_path = tmp_path / f"duplicate-closed-entry-{index}.json"
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        with pytest.raises(ValidationError):
            validate(MANIFEST, CANONICAL, candidate_path)


def test_semantic_rejections_bind_reachable_request_state_to_response(tmp_path):
    manifest, cases = load(MANIFEST), load(CASES)
    expected = {
        "contract-incompatible-isolated": ("contract_incompatible", "CONTRACT_INCOMPATIBLE"),
        "asset-forbidden-isolated": ("asset_forbidden", "ASSET_FORBIDDEN"),
        "asset-not-found-isolated": ("asset_not_found", "ASSET_NOT_FOUND"),
        "source-unavailable-isolated": ("source_unavailable", "SOURCE_UNAVAILABLE"),
        "precedence-contract-before-asset": ("contract_incompatible", "CONTRACT_INCOMPATIBLE"),
        "precedence-allowlist-before-existence": ("asset_forbidden", "ASSET_FORBIDDEN"),
        "precedence-existence-before-source": ("asset_not_found", "ASSET_NOT_FOUND"),
    }
    bindings = {item["id"]: item for item in cases["semantic_rejections"]}
    assert {
        item_id: (item["category"], item["code"])
        for item_id, item in bindings.items()
    } == expected
    envelopes = {item["code"]: item["response"] for item in cases["errors"]}
    for item in bindings.values():
        assert set(item) == {
            "category",
            "code",
            "id",
            "request",
            "serverState",
            "responseCodeRef",
        }
        assert set(item["request"]) == {"contractId", "assetRef"}
        assert item["responseCodeRef"] == item["code"]
        assert envelopes[item["responseCodeRef"]]["body"]["errors"][0][
            "extensions"
        ]["code"] == item["code"]

    reachable_mutations = {
        "contract-incompatible-isolated": lambda item: item["request"].update(
            contractId=manifest["contract_id"]
        ),
        "asset-forbidden-isolated": lambda item: item["serverState"]["allowedAssets"].append(
            item["request"]["assetRef"]
        ),
        "asset-not-found-isolated": lambda item: item["serverState"]["presentAssets"].append(
            item["request"]["assetRef"]
        ),
        "source-unavailable-isolated": lambda item: item["serverState"][
            "snapshotAvailableAssets"
        ].append(item["request"]["assetRef"]),
    }
    for item_id, mutate in reachable_mutations.items():
        candidate = copy.deepcopy(cases)
        item = next(
            binding
            for binding in candidate["semantic_rejections"]
            if binding["id"] == item_id
        )
        mutate(item)
        candidate_path = tmp_path / f"unreachable-{item_id}.json"
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        with pytest.raises(ValidationError):
            validate(MANIFEST, CANONICAL, candidate_path)

    precedence_mutations = {
        "precedence-contract-before-asset": lambda item: (
            item["serverState"]["allowedAssets"].append(item["request"]["assetRef"]),
            item["serverState"]["presentAssets"].append(item["request"]["assetRef"]),
            item["serverState"]["snapshotAvailableAssets"].append(
                item["request"]["assetRef"]
            ),
        ),
        "precedence-allowlist-before-existence": lambda item: (
            item["serverState"]["presentAssets"].append(item["request"]["assetRef"]),
            item["serverState"]["snapshotAvailableAssets"].append(
                item["request"]["assetRef"]
            ),
        ),
        "precedence-existence-before-source": lambda item: item["serverState"][
            "snapshotAvailableAssets"
        ].append(item["request"]["assetRef"]),
    }
    for item_id, mutate in precedence_mutations.items():
        candidate = copy.deepcopy(cases)
        item = next(
            binding
            for binding in candidate["semantic_rejections"]
            if binding["id"] == item_id
        )
        mutate(item)
        candidate_path = tmp_path / f"non-overlap-{item_id}.json"
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        with pytest.raises(ValidationError, match="semantic_rejection_precedence"):
            validate(MANIFEST, CANONICAL, candidate_path)


def test_every_request_rejection_has_executable_stimulus_and_limit_sequence(tmp_path):
    manifest, cases = load(MANIFEST), load(CASES)
    bindings = {
        item["category"]: item for item in cases["request_rejections"]
    }
    assert set(bindings) == set(manifest["request_rejection_codes"])
    assert {
        category: item["code"] for category, item in bindings.items()
    } == manifest["request_rejection_codes"]
    assert set(cases["admission_sequences"]) == {
        "concurrency",
        "rate",
        "client_isolation",
    }
    for category in ("concurrency", "rate"):
        sequence = cases["admission_sequences"][category]
        assert bindings[category]["stimulus"] == {"sequenceRef": sequence["id"]}
        rejected = [event for event in sequence["events"] if event["outcome"] == "REJECT"]
        assert rejected
        assert all(event["code"] == "REQUEST_LIMIT_EXCEEDED" for event in rejected)

        candidate = copy.deepcopy(cases)
        candidate["admission_sequences"][category]["events"] = [
            {**event, "outcome": "ADMIT"} if event["outcome"] == "REJECT" else event
            for event in candidate["admission_sequences"][category]["events"]
        ]
        candidate_path = tmp_path / f"unbounded-{category}.json"
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        with pytest.raises(ValidationError):
            validate(MANIFEST, CANONICAL, candidate_path)

    isolation = cases["admission_sequences"]["client_isolation"]["events"]
    starts_at_zero = [
        event
        for event in isolation
        if event["action"] == "START" and event["atMs"] == 0
    ]
    assert {(event["clientRef"], event["outcome"]) for event in starts_at_zero} == {
        ("mtls-principal-a", "ADMIT"),
        ("mtls-principal-b", "ADMIT"),
    }
    assert any(
        event["clientRef"] == "mtls-principal-a"
        and event["outcome"] == "REJECT"
        for event in isolation
    )
    assert isolation[-2]["clientRef"] == "mtls-principal-a"
    assert isolation[-2]["outcome"] == "ADMIT"

    for index in (1, len(isolation) - 2):
        candidate = copy.deepcopy(cases)
        event = candidate["admission_sequences"]["client_isolation"]["events"][index]
        event["outcome"] = "REJECT"
        event["code"] = "REQUEST_LIMIT_EXCEEDED"
        candidate_path = tmp_path / f"global-or-token-consumption-{index}.json"
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        with pytest.raises(ValidationError, match="admission_sequence_mapping"):
            validate(MANIFEST, CANONICAL, candidate_path)


def test_named_canonical_fixture_has_lossless_public_projection(tmp_path):
    cases = load(CASES)
    projection = response_payload(cases["positive"])
    assert projection["canonicalContractId"] == "helianthus.canonical-pv/v1"
    assert projection["assetRef"] == "pv-asset-mixed-01"
    assert projection["generation"] == "8"
    assert projection["producedAt"] == "2026-08-17T13:46:00Z"
    assert len(projection["facts"]) == 2
    assert len(projection["provenance"]) == 2
    assert len(projection["requestedOutputs"]) == 2
    assert len(projection["projectionReport"]) == 2

    mutations = [
        ("generation", "9"),
        ("producedAt", "2026-08-17T13:46:01Z"),
        ("facts.0.value.coefficient", "7311"),
        ("facts.0.freshUntilMonotonicNs", "1011234500001"),
        ("capabilities.0.outcome", "SATISFIED"),
        (
            "provenance.0.evidenceRef",
            "sha256:" + "e" * 64,
        ),
        (
            "requestedOutputs.0.requestedOutputRef",
            "sha256:" + "a" * 64,
        ),
        ("projectionReport.0.outcome", "WITHHELD"),
    ]
    for index, (path, value) in enumerate(mutations):
        candidate = copy.deepcopy(cases)
        target = response_payload(candidate["positive"])
        parts = path.split(".")
        for part in parts[:-1]:
            target = target[int(part)] if part.isdigit() else target[part]
        target[parts[-1]] = value
        candidate_path = tmp_path / f"canonical-parity-{index}.json"
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        with pytest.raises(ValidationError, match="canonical_fixture_parity"):
            validate(MANIFEST, CANONICAL, candidate_path)


def test_inline_fragments_count_toward_query_depth():
    manifest = load(MANIFEST)
    nested = "coefficient"
    for _ in range(9):
        nested = f"... on M2MDecimalValue {{ {nested} }}"
    query = (
        "query M2MCurrentSnapshot($request: M2MCurrentSnapshotRequest!) "
        "{ m2mCurrentSnapshot(request: $request) { facts { value { "
        + nested
        + " } } } }"
    )
    assert "query_depth" in validate_query_document(query, manifest)


def test_projection_accounting_is_in_the_closed_sdl_and_fixed_query():
    manifest = load(MANIFEST)
    sdl = SDL.read_text(encoding="utf-8")
    assert "requestedOutputs: [M2MRequestedOutput!]!" in sdl
    assert "projectionReport: [M2MProjectionReportEntry!]!" in sdl
    assert "enum M2MProjectionOutcome { MAPPED WITHHELD UNREPRESENTABLE }" in sdl
    assert "requestedOutputs { sourceRef requestedOutputRef }" in manifest[
        "conformance_query"
    ]
    assert (
        "projectionReport { sourceRef requestedOutputRef factId dimensions { key value } outcome }"
        in manifest["conformance_query"]
    )


def test_projection_accounting_rejects_partial_duplicate_and_misbound_rows():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    base = copy.deepcopy(cases["positive"])
    payload = copy.deepcopy(cases["capability_satisfied_projection"])
    base["response"]["body"]["data"]["m2mCurrentSnapshot"] = payload
    base["request"]["body"]["variables"]["request"]["assetRef"] = payload[
        "assetRef"
    ]
    base["request"]["rawBody"] = json.dumps(
        base["request"]["body"], separators=(",", ":")
    )

    candidates = []
    duplicate = copy.deepcopy(base)
    response_payload(duplicate)["requestedOutputs"].append(
        copy.deepcopy(response_payload(duplicate)["requestedOutputs"][0])
    )
    candidates.append(duplicate)
    partial = copy.deepcopy(base)
    response_payload(partial)["projectionReport"].pop()
    candidates.append(partial)
    misbound = copy.deepcopy(base)
    response_payload(misbound)["projectionReport"][0]["sourceRef"] = "sha256:" + "f" * 64
    candidates.append(misbound)
    invalid_loss = copy.deepcopy(base)
    response_payload(invalid_loss)["projectionReport"][0]["outcome"] = "WITHHELD"
    candidates.append(invalid_loss)

    for candidate in candidates:
        assert "projection_accounting" in validate_case(candidate, manifest, canonical)


def test_graphql_ast_admission_enforces_syntax_schema_and_bounds():
    manifest, canonical, cases = load(MANIFEST), load(CANONICAL), load(CASES)
    base = manifest["conformance_query"]
    mutations = [
        ("this is not GraphQL", "query_syntax"),
        (
            base.replace(
                "m2mCurrentSnapshot(request:",
                "snapshot: m2mCurrentSnapshot(request:",
                1,
            ),
            "query_alias",
        ),
        (
            "query M2MCurrentSnapshot($request: M2MCurrentSnapshotRequest!) "
            "{ m2mCurrentSnapshot(request: $request) { ...SnapshotFields } } "
            "fragment SnapshotFields on M2MCurrentSnapshot { contractId }",
            "query_fragment",
        ),
        (base.replace("contractId", "contractId @skip(if: true)", 1), "query_directive"),
        (base.replace("contractId", "__typename contractId", 1), "query_introspection"),
        (base + " query Other { __typename }", "query_operations"),
        (
            base.replace("contractId", " ".join(["contractId"] * 257), 1),
            "query_fields",
        ),
        (
            "query M2MCurrentSnapshot($request: M2MCurrentSnapshotRequest!) "
            "{ m2mCurrentSnapshot(request: $request) { a { b { c { d { e { f { g { h { i } } } } } } } } } }",
            "query_depth",
        ),
    ]
    for query, category in mutations:
        candidate_manifest = copy.deepcopy(manifest)
        candidate_manifest["conformance_query"] = query
        candidate = copy.deepcopy(cases["positive"])
        candidate["request"]["body"]["query"] = query
        candidate["request"]["rawBody"] = json.dumps(
            candidate["request"]["body"], separators=(",", ":")
        )
        assert category in validate_case(candidate, candidate_manifest, canonical)
