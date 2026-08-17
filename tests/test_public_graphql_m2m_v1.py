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
