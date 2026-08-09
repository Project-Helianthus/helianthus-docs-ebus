from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
from copy import deepcopy

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PLATFORM_ROOT = REPO_ROOT / "docs/platform"
SCHEMA_ROOT = PLATFORM_ROOT / "schemas"
FIXTURE_ROOT = PLATFORM_ROOT / "fixtures/leaf-promotion-dossier/v1"
PAGE = PLATFORM_ROOT / "leaf-promotion-dossier-lock-v1.md"
README = PLATFORM_ROOT / "README.md"
SCHEMA = SCHEMA_ROOT / "leaf-promotion-dossier-v1.schema.json"
RESULT_SCHEMA = SCHEMA_ROOT / "leaf-promotion-lock-result-v1.schema.json"
CAPTURED_SCHEMA = (
    SCHEMA_ROOT / "leaf-promotion-captured-assessment-v1.schema.json"
)
REGISTRY = SCHEMA_ROOT / "leaf-promotion-registry-v1.json"
VALIDATOR = REPO_ROOT / "scripts/validate_leaf_promotion_dossier.py"
DOSSIER = FIXTURE_ROOT / "positive/dossier.json"
RESULT = FIXTURE_ROOT / "positive/result.json"
CAPTURED_PROFILE = FIXTURE_ROOT / "positive/captured-runtime-zero-profile.json"
M7_LIVE_STATUS = (
    PLATFORM_ROOT
    / "fixtures/candidate-fact-graph/v1/positive/live-public-status.json"
)
NEGATIVE_ROOT = FIXTURE_ROOT / "negative"
NEGATIVE_CAPTURED_ROOT = FIXTURE_ROOT / "negative-captured"
EXPECTED_NEGATIVE = {
    "b524-namespace-mismatch.json": "identity.native",
    "coexistence-drift.json": "coexistence.invalid",
    "coexistence-run-mismatch.json": "coexistence.invalid",
    "coexistence-view-hash-mismatch.json": "coexistence.invalid",
    "comparator-incomplete.json": "schema.dossier",
    "dossier-hash-mismatch.json": "hash.dossier",
    "inherited-source.json": "inheritance.forbidden",
    "lease-holder-mismatch.json": "mutable.safety",
    "lease-window-invalid.json": "mutable.safety",
    "mutable-cycle-duplicate.json": "mutable.safety",
    "mutable-cycle-input-duplicate.json": "mutable.safety",
    "mutable-cycle-outside-lease.json": "mutable.safety",
    "mutable-direct-adapter-write.json": "mutable.safety",
    "mutable-missing-cycle.json": "schema.dossier",
    "mutable-nonexclusive-writer.json": "mutable.safety",
    "mutable-rollback-failed.json": "mutable.rollback",
    "provenance-hash-mismatch.json": "provenance.binding",
    "replay-hash-mismatch.json": "hash.replay",
    "synthetic-promotion.json": "evidence.ineligible",
    "forged-captured-promotion.json": "evidence.ineligible",
    "source-binding-mismatch.json": "provenance.binding",
    "terminal-not-withheld.json": "state.terminal",
    "unknown-field.json": "schema.dossier",
    "unordered-leaves.json": "identity.native",
    "zero-promoted-m9-open.json": "consumer.block",
}
EXPECTED_CAPTURED_NEGATIVE = {
    "caller-authored-status.json": "assessment.derivation",
    "fabricated-dossier.json": "promotion.forbidden",
    "fabricated-promotion.json": "captured.result",
    "graph-replay-mismatch.json": "projection.replay",
    "identity-leak.json": "captured.result",
    "m9-open.json": "consumer.block",
    "secret-leak.json": "captured.result",
    "status-mismatch.json": "assessment.derivation",
    "synthetic-as-live.json": "captured.status",
    "unknown-field.json": "captured.result",
    "unordered-assessments.json": "assessment.ordering",
    "wrong-m7-predecessor.json": "captured.predecessor",
    "wrong-m8-predecessor.json": "captured.predecessor",
}


def load_json(path: pathlib.Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, value: object) -> pathlib.Path:
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return path


def validator_module():
    spec = importlib.util.spec_from_file_location("msp085_validator", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_validator(
    command: str, dossier: pathlib.Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            command,
            "--dossier",
            str(dossier),
            "--registry",
            str(REGISTRY),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONHASHSEED": "random"},
    )


def test_msp085_contract_inventory_is_canonical_and_navigable() -> None:
    for path in (
        PAGE,
        SCHEMA,
        RESULT_SCHEMA,
        CAPTURED_SCHEMA,
        REGISTRY,
        VALIDATOR,
        DOSSIER,
        RESULT,
        CAPTURED_PROFILE,
    ):
        assert path.is_file(), f"missing MSP-085 contract artifact: {path}"
    assert {path.name for path in NEGATIVE_ROOT.glob("*.json")} == set(
        EXPECTED_NEGATIVE
    )
    assert {path.name for path in NEGATIVE_CAPTURED_ROOT.glob("*.json")} == set(
        EXPECTED_CAPTURED_NEGATIVE
    )
    page = PAGE.read_text(encoding="utf-8")
    assert page.startswith(
        "Canonical source: this page.\n\n# Leaf Promotion Dossier Lock V1"
    )
    assert "leaf-promotion-dossier-lock-v1.md" in README.read_text(encoding="utf-8")


def test_normative_page_closes_every_required_boundary() -> None:
    page = PAGE.read_text(encoding="utf-8")
    for phrase in (
        "MSP-085",
        "M8.5",
        "exact canonical semantic path",
        "B509",
        "B524",
        "B555",
        "OP=0x02",
        "OP=0x06",
        "separate namespaces",
        "entity/service/feature/path",
        "comparator type",
        "window",
        "tolerance",
        "conversion",
        "rounding",
        "minimum samples",
        "maximum missing",
        "stale cutoff",
        "conflict threshold",
        "NO_SIGNAL",
        "CLOUD_ONLY",
        "CONFLICT",
        "NOT_TESTED",
        "WITHHELD",
        "RAW_DEBUG_ONLY",
        "coexistence no-drift",
        "replay regeneration",
        "provenance",
        "redacted hashes",
        "retest trigger",
        "no family inheritance",
        "no device inheritance",
        "no sibling inheritance",
        "lab whitelist",
        "lease",
        "one writer",
        "gateway/router write path",
        "abort conditions",
        "rollback after every cycle",
        "three independent perturbation cycles",
        "zero promoted leaves",
        "blocks all M9 consumer work",
        "off-LAN",
        "synthetic",
        "no positive promotion claim",
        "SYNTHETIC_CONFORMANCE",
        "CAPTURED_RUNTIME_ZERO_PROMOTION",
        "18 actual facts",
        "14 `RAW_ONLY`",
        "four `WITHHELD`",
        "dossier_count=0",
        "PRIVATE_OPERATOR",
        "caller-authored status",
        "one unreleased V1",
    ):
        assert phrase in page
    assert "eeBUS protocol semantics" not in page


def test_machine_contract_and_registry_are_closed() -> None:
    schema = load_json(SCHEMA)
    result_schema = load_json(RESULT_SCHEMA)
    captured_schema = load_json(CAPTURED_SCHEMA)
    registry = load_json(REGISTRY)
    assert schema["$id"].endswith("leaf-promotion-dossier-v1.schema.json")
    assert result_schema["$id"].endswith(
        "leaf-promotion-lock-result-v1.schema.json"
    )
    assert schema["additionalProperties"] is False
    assert result_schema["additionalProperties"] is False
    assert captured_schema["additionalProperties"] is False
    assert captured_schema["properties"]["dossiers"]["maxItems"] == 0
    assert captured_schema["properties"]["export_tier"]["const"] == (
        "PRIVATE_OPERATOR"
    )
    assert registry["contract"] == "helianthus.platform.leaf-promotion-registry.v1"
    assert registry["gate"] == "MSP-085"
    assert registry["terminal_states"] == [
        "NO_SIGNAL",
        "CLOUD_ONLY",
        "CONFLICT",
        "NOT_TESTED",
    ]
    assert registry["ebus_source_families"] == ["B509", "B524", "B555"]
    assert registry["b524_namespaces"] == ["OP_0X02", "OP_0X06"]
    assert registry["required_perturbation_cycles"] == 3
    assert registry["zero_promotion_consumer_gate"] == (
        "BLOCKED_ZERO_PROMOTED_LEAVES"
    )
    assert registry["current_evidence_policy"] == (
        "OFF_LAN_OR_SYNTHETIC_CANNOT_PROMOTE"
    )
    assert registry["profiles"] == {
        "SYNTHETIC_CONFORMANCE": {
            "live_promotion_claim": False,
            "persist_private_assessment": False,
        },
        "CAPTURED_RUNTIME_ZERO_PROMOTION": {
            "live_promotion_claim": False,
            "persist_private_assessment": False,
        },
    }
    assert registry["captured_runtime_predecessors"] == {
        "m7_gateway_source_commit": (
            "8bcba2107d10b149f984ac9546ea6427a9cda8a1"
        ),
        "m7_docs_source_commit": (
            "35d2eba256a77b6575a2b45c07e73f054ff74ced"
        ),
        "m8_gateway_source_commit": (
            "89cf8876a9cd8aa4e6aab9ad21cc05cac523426a"
        ),
        "m8_docs_source_commit": (
            "9cede4c61a4f73019142b7418cf6f87537cf645c"
        ),
    }
    assert set(registry["source_artifacts"]) == {
        "m7_graph",
        "m7_replay",
        "m8_evidence",
        "m8_report",
    }
    assert len(registry["validation_precedence"]) >= 12
    assert registry["captured_validation_precedence"] == [
        "json.syntax",
        "limits.exceeded",
        "registry.binding",
        "captured.input",
        "captured.predecessor",
        "source.validator.category",
        "captured.status",
        "captured.coexistence",
        "captured.schema",
        "assessment.ordering",
        "assessment.derivation",
        "promotion.forbidden",
        "consumer.block",
        "redaction.public",
        "captured.result",
        "hash.result",
    ]


def test_canonical_artifacts_match_gateway_pr_773_exact_bytes() -> None:
    expected_sha256 = {
        REGISTRY: "ad33736c00aa2c3ecaac981606d25c064088c80cb72ca5389b83c5d9df40f6a3",
        DOSSIER: "3b12e3b6f625f6efb28fced19d679ab73b974fc4369e0dba9f61f1a2d104ec64",
        RESULT: "a4e5deb1027e337e917304addfa1aebaaf8f04659d7de38b36083c78525d1a04",
    }
    for path, expected in expected_sha256.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


def test_corrected_canonical_registry_dossier_result_hash_chain_is_closed() -> None:
    module = validator_module()
    registry = load_json(REGISTRY)
    dossier = load_json(DOSSIER)
    result = load_json(RESULT)

    assert registry["captured_runtime_sources"]["m7_terminal_source_bundle"] == (
        "internal/candidatefacts/testdata/canonical/source/"
        "source-terminal-bundle.json"
    )
    assert registry["captured_runtime_sources"]["m7_terminal_source_replay"] == (
        "internal/candidatefacts/testdata/canonical/source/"
        "source-terminal-replay-result.json"
    )
    registry_digest = "sha256:" + hashlib.sha256(REGISTRY.read_bytes()).hexdigest()
    assert dossier["registry"]["digest"] == registry_digest

    dossier_payload = {
        key: value for key, value in dossier.items() if key != "dossier_hash"
    }
    assert dossier["dossier_hash"] == module.digest(
        module.DOSSIER_DOMAIN, dossier_payload
    )
    assert result["dossier_hash"] == dossier["dossier_hash"]
    result_payload = {
        key: value for key, value in result.items() if key != "result_hash"
    }
    assert result["result_hash"] == module.digest(
        module.RESULT_DOMAIN, result_payload
    )


def test_zero_promotion_fixture_is_explicit_valid_and_blocks_m9() -> None:
    dossier = load_json(DOSSIER)
    result = load_json(RESULT)
    assert dossier["dossier_id"] == result["dossier_id"]
    assert "fixture_id" not in dossier
    assert dossier["evidence_class"] == "SYNTHETIC_OFFLINE_FIXTURE"
    assert dossier["capture_context"] == "OFF_LAN"
    assert dossier["positive_promotion_claim"] is False
    assert dossier["profile"] == "SYNTHETIC_CONFORMANCE"
    assert result["profile"] == "SYNTHETIC_CONFORMANCE"
    assert result["export_tier"] == "PUBLIC_REDACTED"
    assert [leaf["terminal_state"] for leaf in dossier["leaves"]] == [
        "NO_SIGNAL",
        "CLOUD_ONLY",
        "CONFLICT",
        "NOT_TESTED",
    ]
    assert all(leaf["decision"] == "WITHHELD" for leaf in dossier["leaves"])
    assert all(leaf["visibility"] == "RAW_DEBUG_ONLY" for leaf in dossier["leaves"])
    assert result["verdict"] == "VALID_ZERO_PROMOTION"
    assert result["counts"] == {"total": 4, "promoted": 0, "withheld": 4}
    assert result["m9_consumer_gate"] == "BLOCKED_ZERO_PROMOTED_LEAVES"


def test_captured_runtime_profile_binds_every_actual_m7_fact() -> None:
    status = load_json(M7_LIVE_STATUS)
    profile = load_json(CAPTURED_PROFILE)
    assert profile["contract"] == (
        "helianthus.platform.leaf-promotion-captured-profile-fixture.v1"
    )
    assert profile["profile"] == "CAPTURED_RUNTIME_ZERO_PROMOTION"
    assert profile["persisted_live_result"] is False
    assert profile["expected_counts"] == {
        "total": 18,
        "promoted": 0,
        "withheld": 18,
    }
    assert profile["m9_consumer_gate"] == "BLOCKED_ZERO_PROMOTED_LEAVES"
    assert profile["m7_status_projection_id"] == status["projection_id"]
    assert profile["m7_status_projection_hash"] == status["projection_hash"]
    assert profile["fact_count"] == status["fact_count"]


def test_captured_runtime_profile_is_public_redacted() -> None:
    serialized = CAPTURED_PROFILE.read_text(encoding="utf-8").lower()
    for forbidden in (
        "semantic_path",
        "proposed_path",
        "source_address",
        "target_address",
        "entity",
        "feature",
        "service",
        "ship_id",
        "ski",
        "private_key",
        "trust_store",
        "candidate_ref",
    ):
        assert forbidden not in serialized


def test_captured_negative_vectors_are_closed_and_categorized() -> None:
    for name, category in EXPECTED_CAPTURED_NEGATIVE.items():
        descriptor = load_json(NEGATIVE_CAPTURED_ROOT / name)
        assert descriptor["contract"] == (
            "helianthus.platform.leaf-promotion-captured-negative-fixture.v1"
        )
        assert descriptor["expected_category"] == category
        assert set(descriptor) == {"contract", "mutation", "expected_category"}


def captured_assessment_fixture(module) -> dict[str, object]:
    status = load_json(M7_LIVE_STATUS)
    registry = load_json(REGISTRY)
    source = registry["captured_runtime_predecessors"] | {
        "m7_graph_id": status["source_graph_id"],
        "m7_graph_hash": status["source_graph_hash"],
        "m7_replay_id": status["source_replay_id"],
        "m7_replay_hash": status["source_replay_hash"],
        "m7_status_projection_id": status["projection_id"],
        "m7_status_projection_hash": status["projection_hash"],
        "m8_evidence_id": "mrcv1:sha256:" + "a" * 64,
        "m8_evidence_hash": "sha256:" + "a" * 64,
        "m8_report_id": "mrcrv1:sha256:" + "b" * 64,
        "m8_report_hash": "sha256:" + "b" * 64,
        "coexistence_verdict": "PASS",
    }
    assessments = []
    for index, fact in enumerate(status["facts"], start=1):
        reason = (
            "SOURCE_STATUS_WITHHELD"
            if fact["status"] == "WITHHELD"
            else "SOURCE_STATUS_RAW_ONLY"
        )
        assessments.append(
            {
                "candidate_id": fact["candidate_id"],
                "semantic_path": f"/private/candidate_{index:04d}",
                "fact_hash": fact["fact_hash"],
                "source_status": fact["status"],
                "terminal_state": fact["terminal_negative_state"],
                "eligibility": {
                    "exact_ebus_identity": False,
                    "exact_eebus_path": False,
                    "comparator_match": False,
                    "captured_evidence_eligible": False,
                    "coexistence_no_drift": True,
                },
                "decision": "WITHHELD",
                "withholding_reasons": [
                    reason,
                    "EXACT_EBUS_IDENTITY_MISSING",
                    "EXACT_EEBUS_PATH_MISSING",
                    "COMPARATOR_NOT_MATCHED",
                    "CAPTURED_EVIDENCE_INELIGIBLE",
                ],
                "retest_trigger": {
                    "trigger": "SOURCE_RECOVERED",
                    "required_source_kinds": ["EBUS", "EEBUS"],
                    "minimum_new_samples": 1,
                },
            }
        )
    value = {
        "contract": module.CAPTURED_ASSESSMENT_CONTRACT,
        "schema_version": 1,
        "profile": "CAPTURED_RUNTIME_ZERO_PROMOTION",
        "export_tier": "PRIVATE_OPERATOR",
        "source_bindings": source,
        "assessments": assessments,
        "dossiers": [],
        "m9_consumer_gate": "BLOCKED_ZERO_PROMOTED_LEAVES",
        "assessment_hash": "sha256:" + "0" * 64,
    }
    view = {key: item for key, item in value.items() if key != "assessment_hash"}
    value["assessment_hash"] = module.digest(
        module.CAPTURED_ASSESSMENT_DOMAIN, view
    )
    return value


def test_captured_runtime_public_result_is_derived_not_persisted(
    tmp_path: pathlib.Path,
) -> None:
    module = validator_module()
    private = captured_assessment_fixture(module)
    module._schema_validate(
        private,
        "leaf-promotion-captured-assessment-v1.schema.json",
        "captured.schema",
    )
    result = module.build_captured_result(private)
    assert result["counts"] == {"total": 18, "promoted": 0, "withheld": 18}
    assert result["dossier_count"] == 0
    assert len(result["assessments"]) == 18
    assert all("semantic_path" not in item for item in result["assessments"])
    result_path = write_json(tmp_path / "captured-result.json", result)
    checked = subprocess.run(
        ["jv", str(RESULT_SCHEMA), str(result_path)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr


def test_captured_derivation_reuses_canonical_m7_and_m8_validators() -> None:
    # Private live inputs are intentionally absent from git. Dependency closure
    # therefore cannot be proven by a committed end-to-end positive fixture.
    source = VALIDATOR.read_text(encoding="utf-8")
    for call in (
        "status_projector.load_verified_projection(",
        "coexistence.verify(",
        "coexistence.report(",
    ):
        assert call in source


def captured_cli_command(
    *, replay: pathlib.Path, registry: pathlib.Path = REGISTRY
) -> list[str]:
    candidate_root = PLATFORM_ROOT / "fixtures/candidate-fact-graph/v1/positive"
    synchronized_root = PLATFORM_ROOT / "fixtures/synchronized-evidence/v1/positive"
    coexistence_root = PLATFORM_ROOT / "fixtures/coexistence-no-drift/v1/positive"
    return [
        sys.executable,
        str(VALIDATOR),
        "derive-captured",
        "--registry",
        str(registry),
        "--m7-graph",
        str(candidate_root / "graph.json"),
        "--m7-replay",
        str(replay),
        "--m7-registry",
        str(PLATFORM_ROOT / "schemas/draft-candidate-fact-registry-v1.json"),
        "--m7-source-bundle",
        str(synchronized_root / "bundle.json"),
        "--m7-source-replay",
        str(synchronized_root / "replay-result.json"),
        "--m7-live-status",
        str(M7_LIVE_STATUS),
        "--m7-terminal-graph",
        str(candidate_root / "source-terminal-graph.json"),
        "--m7-terminal-replay",
        str(candidate_root / "source-terminal-replay-result.json"),
        "--m7-terminal-source-bundle",
        str(candidate_root / "source-terminal-bundle.json"),
        "--m7-terminal-source-replay",
        str(candidate_root / "source-terminal-source-replay.json"),
        "--m8-evidence",
        str(coexistence_root / "evidence.json"),
        "--m8-report",
        str(coexistence_root / "report.json"),
        "--m8-registry",
        str(PLATFORM_ROOT / "schemas/multi-runtime-coexistence-registry-v1.json"),
    ]


def test_synthetic_inputs_cannot_substitute_for_captured_runtime() -> None:
    replay = (
        PLATFORM_ROOT
        / "fixtures/candidate-fact-graph/v1/positive/replay-result.json"
    )
    completed = subprocess.run(
        captured_cli_command(replay=replay),
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert completed.stdout == "captured.status\n"
    assert completed.stderr == ""


def test_graph_replay_mismatch_fails_before_captured_status() -> None:
    replay = (
        PLATFORM_ROOT
        / "fixtures/candidate-fact-graph/v1/positive/source-terminal-replay-result.json"
    )
    completed = subprocess.run(
        captured_cli_command(replay=replay),
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert completed.stdout == "projection.replay\n"
    assert completed.stderr == ""


def test_m7_snapshot_is_immutable_when_source_changes_after_validation(
    tmp_path: pathlib.Path,
) -> None:
    module = validator_module()
    source_graph = tmp_path / "source-graph.json"
    original_graph = b'{"graph":"validated"}\n'
    source_graph.write_bytes(original_graph)
    verified_raw = {
        "graph": source_graph.read_bytes(),
        "replay": b'{"replay":"validated"}\n',
    }
    source_graph.write_bytes(b'{"graph":"swapped-after-validation"}\n')

    snapshot_root = tmp_path / "snapshot"
    snapshot_root.mkdir()
    graph_path, replay_path = module._write_verified_m7_snapshot(
        snapshot_root, verified_raw
    )

    assert graph_path.read_bytes() == original_graph
    assert replay_path.read_bytes() == verified_raw["replay"]
    assert graph_path.read_bytes() != source_graph.read_bytes()


@pytest.mark.parametrize(
    ("mutation", "value"),
    [
        ("candidate_id", "192.168.37.21"),
        ("m7_graph_id", "/private/captures/graph.raw"),
        ("m8_evidence_id", "/private/captures/device.raw"),
        ("retest_trigger", "/private/retry/device.raw"),
        ("secret", "synthetic-private-key"),
    ],
)
def test_public_result_schema_rejects_identity_path_and_secret_leaks(
    tmp_path: pathlib.Path, mutation: str, value: str
) -> None:
    module = validator_module()
    result = module.build_captured_result(captured_assessment_fixture(module))
    if mutation == "candidate_id":
        result["assessments"][0]["candidate_id"] = value
    elif mutation == "m7_graph_id":
        result["source_bindings"]["m7_graph_id"] = value
    elif mutation == "m8_evidence_id":
        result["source_bindings"]["m8_evidence_id"] = value
    elif mutation == "retest_trigger":
        result["assessments"][0]["retest_trigger"]["trigger"] = value
    elif mutation == "secret":
        result["private_key"] = value
    else:
        raise AssertionError(mutation)
    result_path = write_json(tmp_path / f"{mutation}.json", result)
    checked = subprocess.run(
        ["jv", str(RESULT_SCHEMA), str(result_path)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert checked.returncode != 0


def test_malformed_captured_registry_shape_fails_without_traceback(
    tmp_path: pathlib.Path,
) -> None:
    registry = load_json(REGISTRY)
    registry["profiles"] = 1
    registry_path = write_json(tmp_path / "registry.json", registry)
    replay = (
        PLATFORM_ROOT
        / "fixtures/candidate-fact-graph/v1/positive/replay-result.json"
    )
    completed = subprocess.run(
        captured_cli_command(replay=replay, registry=registry_path),
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert completed.stdout == "registry.binding\n"
    assert completed.stderr == ""


@pytest.mark.parametrize(
    "mutation,category",
    [
        ("CALLER_AUTHORED_STATUS", "assessment.derivation"),
        ("FABRICATED_DOSSIER", "promotion.forbidden"),
        ("FABRICATED_DOSSIER_METADATA", "captured.result"),
        ("FABRICATED_PROMOTION", "captured.result"),
        ("IDENTITY_LEAK", "captured.result"),
        ("M9_OPEN", "consumer.block"),
        ("MISSING_ASSESSMENTS", "captured.result"),
        ("PROFILE_RELABEL", "captured.result"),
        ("SECRET_LEAK", "captured.result"),
        ("SOURCE_BINDING_MISMATCH", "assessment.derivation"),
        ("STATUS_MISMATCH", "assessment.derivation"),
        ("UNKNOWN_FIELD", "captured.result"),
        ("UNORDERED_ASSESSMENTS", "assessment.ordering"),
    ],
)
def test_captured_result_mutations_fail_closed(
    mutation: str, category: str
) -> None:
    module = validator_module()
    private = captured_assessment_fixture(module)
    result = module.build_captured_result(private)
    if mutation in {"CALLER_AUTHORED_STATUS", "STATUS_MISMATCH"}:
        result["assessments"][0]["source_status"] = "RAW_ONLY"
    elif mutation == "FABRICATED_DOSSIER":
        result["dossier_count"] = 1
    elif mutation == "FABRICATED_DOSSIER_METADATA":
        result["dossier_id"] = "fabricated-dossier"
        result["dossier_hash"] = "sha256:" + "f" * 64
    elif mutation == "FABRICATED_PROMOTION":
        result["assessments"][0]["decision"] = "PROMOTED"
    elif mutation == "IDENTITY_LEAK":
        result["assessments"][0]["semantic_path"] = "/private/path"
    elif mutation == "M9_OPEN":
        result["m9_consumer_gate"] = "READY_FOR_M9"
    elif mutation == "MISSING_ASSESSMENTS":
        del result["assessments"]
    elif mutation == "PROFILE_RELABEL":
        result["profile"] = "SYNTHETIC_CONFORMANCE"
    elif mutation == "SECRET_LEAK":
        result["private_key"] = "synthetic-secret"
    elif mutation == "SOURCE_BINDING_MISMATCH":
        result["source_bindings"]["m8_evidence_hash"] = "sha256:" + "f" * 64
    elif mutation == "UNKNOWN_FIELD":
        result["unknown"] = True
    elif mutation == "UNORDERED_ASSESSMENTS":
        private["assessments"][0], private["assessments"][1] = (
            private["assessments"][1],
            private["assessments"][0],
        )
    else:
        raise AssertionError(mutation)
    with pytest.raises(module.Failure) as error:
        module.captured_result_check(result, private)
    assert str(error.value) == category


@pytest.mark.parametrize("source", ["m7", "m8"])
def test_captured_predecessor_mismatch_fails_closed(source: str) -> None:
    module = validator_module()
    registry = load_json(REGISTRY)
    status = load_json(M7_LIVE_STATUS)
    predecessor = registry["captured_runtime_predecessors"]
    graph = {
        "graph_id": status["source_graph_id"],
        "graph_hash": status["source_graph_hash"],
    }
    replay = {
        "replay_id": status["source_replay_id"],
        "replay_hash": status["source_replay_hash"],
    }
    evidence = {
        "evidence_class": "CAPTURED_RUNTIME_EVIDENCE",
        "runs": [
            {
                "provenance": {
                    "runtime": {
                        "source_commit": predecessor["m8_gateway_source_commit"]
                    }
                }
            }
        ],
    }
    report = {
        "evidence_class": "CAPTURED_RUNTIME_EVIDENCE",
        "verdict": "PASS",
    }
    if source == "m7":
        graph["graph_hash"] = "sha256:" + "f" * 64
    else:
        evidence["runs"][0]["provenance"]["runtime"]["source_commit"] = "f" * 40
    with pytest.raises(module.Failure) as error:
        module._captured_predecessor_check(
            registry, graph, replay, status, evidence, report
        )
    assert str(error.value) == "captured.predecessor"


def test_fixture_covers_source_families_and_b524_namespaces_exactly() -> None:
    leaves = load_json(DOSSIER)["leaves"]
    families = [leaf["source_identity"]["ebus"]["family"] for leaf in leaves]
    assert set(families) == {"B509", "B524", "B555"}
    b524 = [leaf["source_identity"]["ebus"] for leaf in leaves if leaf["source_identity"]["ebus"]["family"] == "B524"]
    assert {(item["opcode"], item["namespace"]) for item in b524} == {
        (2, "OP_0X02"),
        (6, "OP_0X06"),
    }
    for leaf in leaves:
        assert leaf["semantic_path"].startswith("/")
        assert set(leaf["source_identity"]["eebus"]) == {
            "entity",
            "service",
            "feature",
            "path",
        }
        assert leaf["inheritance"] == {
            "family": False,
            "device": False,
            "sibling": False,
        }


def test_comparator_provenance_replay_and_retest_fields_are_mandatory() -> None:
    for leaf in load_json(DOSSIER)["leaves"]:
        assert set(leaf["comparator"]) == {
            "type",
            "window",
            "tolerance",
            "conversion",
            "rounding",
            "minimum_samples",
            "maximum_missing",
            "stale_cutoff_ns",
            "conflict_threshold",
            "observed_samples",
            "missing_samples",
            "outcome",
        }
        assert set(leaf["provenance"]) == {
            "source_artifact_ids",
            "redacted_input_hashes",
            "normalized_output_hash",
        }
        assert leaf["coexistence_proof"]["no_drift"] is True
        assert leaf["coexistence_proof"]["rollback_exact"] is True
        assert leaf["replay"]["deterministic"] is True
        assert leaf["retest_trigger"]["trigger"]


def test_positive_dossier_and_result_are_schema_valid() -> None:
    for schema, fixture in ((SCHEMA, DOSSIER), (RESULT_SCHEMA, RESULT)):
        completed = subprocess.run(
            ["jv", str(schema), str(fixture)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr


def test_replay_is_byte_deterministic_and_matches_golden() -> None:
    first = run_validator("replay", DOSSIER)
    second = run_validator("replay", DOSSIER)
    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert first.stdout == RESULT.read_text(encoding="utf-8")
    assert second.stdout == first.stdout
    assert first.stderr == second.stderr == ""


def test_replay_is_offline_under_host_variation(tmp_path: pathlib.Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "replay",
            "--dossier",
            str(DOSSIER),
            "--registry",
            str(REGISTRY),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        env={
            "PATH": os.environ["PATH"],
            "HOME": str(tmp_path / "unavailable-home"),
            "LANG": "invalid_LOCALE",
            "LC_ALL": "C",
            "TZ": "Pacific/Kiritimati",
            "PYTHONHASHSEED": "9876",
        },
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stdout == RESULT.read_text(encoding="utf-8")
    assert completed.stderr == ""


def refresh_dossier_hash(dossier: dict[str, object]) -> None:
    payload = {key: value for key, value in dossier.items() if key != "dossier_hash"}
    encoded = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    dossier["dossier_hash"] = "sha256:" + hashlib.sha256(
        b"HELIANTHUS:LEAF-PROMOTION-DOSSIER:V1\0" + encoded
    ).hexdigest()


def refresh_leaf_replay(leaf: dict[str, object]) -> None:
    payload = {
        key: leaf[key]
        for key in (
            "leaf_id",
            "semantic_path",
            "source_identity",
            "comparator",
            "decision",
            "terminal_state",
        )
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    value = "sha256:" + hashlib.sha256(
        b"HELIANTHUS:LEAF-PROMOTION-REPLAY:V1\0" + encoded
    ).hexdigest()
    leaf["provenance"]["normalized_output_hash"] = value
    leaf["replay"]["expected_output_hash"] = value
    leaf["replay"]["actual_output_hash"] = value


def apply_mutation(dossier: dict[str, object], mutation: str) -> None:
    first = dossier["leaves"][0]
    mutable = dossier["leaves"][3]
    if mutation == "B524_NAMESPACE_MISMATCH":
        dossier["leaves"][1]["source_identity"]["ebus"]["namespace"] = "OP_0X06"
    elif mutation == "COEXISTENCE_DRIFT":
        first["coexistence_proof"]["no_drift"] = False
    elif mutation == "COEXISTENCE_RUN_MISMATCH":
        first["coexistence_proof"]["scenario_run_ids"][0] = "forged-run"
    elif mutation == "COEXISTENCE_VIEW_HASH_MISMATCH":
        first["coexistence_proof"]["protected_view_hashes"][0] = (
            "sha256:" + "f" * 64
        )
    elif mutation == "COMPARATOR_INCOMPLETE":
        del first["comparator"]["rounding"]
    elif mutation == "DOSSIER_HASH_MISMATCH":
        dossier["dossier_hash"] = "sha256:" + "f" * 64
        return
    elif mutation == "INHERITED_SOURCE":
        first["inheritance"]["sibling"] = True
    elif mutation == "LEASE_HOLDER_MISMATCH":
        mutable["mutable_proof"]["lease"]["holder"] = "different-writer"
    elif mutation == "LEASE_WINDOW_INVALID":
        mutable["mutable_proof"]["lease"]["valid_until"] = (
            mutable["mutable_proof"]["lease"]["valid_from"]
        )
    elif mutation == "MUTABLE_CYCLE_DUPLICATE":
        mutable["mutable_proof"]["cycles"][1]["cycle_id"] = mutable["mutable_proof"]["cycles"][0]["cycle_id"]
    elif mutation == "MUTABLE_CYCLE_INPUT_DUPLICATE":
        mutable["mutable_proof"]["cycles"][1]["perturbation_input_hash"] = (
            mutable["mutable_proof"]["cycles"][0]["perturbation_input_hash"]
        )
    elif mutation == "MUTABLE_CYCLE_OUTSIDE_LEASE":
        mutable["mutable_proof"]["cycles"][2]["performed_at"] = (
            "2026-07-20T01:00:01Z"
        )
    elif mutation == "MUTABLE_DIRECT_ADAPTER_WRITE":
        mutable["mutable_proof"]["direct_adapter_write"] = True
    elif mutation == "MUTABLE_MISSING_CYCLE":
        mutable["mutable_proof"]["cycles"].pop()
    elif mutation == "MUTABLE_NONEXCLUSIVE_WRITER":
        mutable["mutable_proof"]["one_writer"] = False
    elif mutation == "MUTABLE_ROLLBACK_FAILED":
        mutable["mutable_proof"]["cycles"][2]["rollback"] = "FAILED"
    elif mutation == "PROVENANCE_HASH_MISMATCH":
        first["provenance"]["redacted_input_hashes"][0] = "sha256:" + "f" * 64
    elif mutation == "REPLAY_HASH_MISMATCH":
        first["replay"]["actual_output_hash"] = "sha256:" + "f" * 64
    elif mutation == "SYNTHETIC_PROMOTION":
        first["decision"] = "PROMOTED"
        first["terminal_state"] = None
        first["visibility"] = "LOCKED_NOT_EXPOSED"
        refresh_leaf_replay(first)
    elif mutation == "FORGED_CAPTURED_PROMOTION":
        dossier["evidence_class"] = "CAPTURED_RUNTIME_EVIDENCE"
        dossier["capture_context"] = "SAME_LAN_LAB"
        dossier["positive_promotion_claim"] = True
        first["decision"] = "PROMOTED"
        first["terminal_state"] = None
        first["visibility"] = "LOCKED_NOT_EXPOSED"
        first["comparator"]["outcome"] = "MATCH"
        first["comparator"]["observed_samples"] = 3
        first["comparator"]["missing_samples"] = 0
        dossier["m9_consumer_gate"] = "READY_FOR_M9"
        refresh_leaf_replay(first)
    elif mutation == "SOURCE_BINDING_MISMATCH":
        dossier["source_bindings"]["m8_evidence_hash"] = "sha256:" + "f" * 64
        for leaf in dossier["leaves"]:
            leaf["provenance"]["redacted_input_hashes"][1] = "sha256:" + "f" * 64
    elif mutation == "UNORDERED_LEAVES":
        dossier["leaves"][0], dossier["leaves"][1] = (
            dossier["leaves"][1],
            dossier["leaves"][0],
        )
    elif mutation == "TERMINAL_NOT_WITHHELD":
        first["decision"] = "PROMOTED"
    elif mutation == "UNKNOWN_FIELD":
        dossier["promoted"] = True
    elif mutation == "ZERO_PROMOTED_M9_OPEN":
        dossier["m9_consumer_gate"] = "READY_FOR_M9"
    else:
        raise AssertionError(f"unhandled MSP-085 mutation: {mutation}")
    refresh_dossier_hash(dossier)


@pytest.mark.parametrize(
    "name,category", sorted(EXPECTED_NEGATIVE.items()), ids=sorted(EXPECTED_NEGATIVE)
)
def test_negative_mutations_fail_at_one_precedence_category(
    tmp_path: pathlib.Path, name: str, category: str
) -> None:
    descriptor = load_json(NEGATIVE_ROOT / name)
    assert descriptor["contract"] == (
        "helianthus.platform.leaf-promotion-negative-fixture.v1"
    )
    dossier = deepcopy(load_json(DOSSIER))
    apply_mutation(dossier, descriptor["mutation"])
    completed = run_validator("verify", write_json(tmp_path / name, dossier))
    assert completed.returncode == 1
    assert completed.stdout == f"{category}\n"
    assert completed.stderr == ""


def test_production_validator_has_no_fixture_mutation_language() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    for token in (
        "B524_NAMESPACE_MISMATCH",
        "SYNTHETIC_PROMOTION",
        "ZERO_PROMOTED_M9_OPEN",
        "expand_negative_fixture",
    ):
        assert token not in source
