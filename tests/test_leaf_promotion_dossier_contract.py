from __future__ import annotations

import hashlib
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
REGISTRY = SCHEMA_ROOT / "leaf-promotion-registry-v1.json"
VALIDATOR = REPO_ROOT / "scripts/validate_leaf_promotion_dossier.py"
DOSSIER = FIXTURE_ROOT / "positive/dossier.json"
RESULT = FIXTURE_ROOT / "positive/result.json"
NEGATIVE_ROOT = FIXTURE_ROOT / "negative"
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


def load_json(path: pathlib.Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, value: object) -> pathlib.Path:
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return path


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
    for path in (PAGE, SCHEMA, RESULT_SCHEMA, REGISTRY, VALIDATOR, DOSSIER, RESULT):
        assert path.is_file(), f"missing MSP-085 contract artifact: {path}"
    assert {path.name for path in NEGATIVE_ROOT.glob("*.json")} == set(
        EXPECTED_NEGATIVE
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
    ):
        assert phrase in page
    assert "eeBUS protocol semantics" not in page


def test_machine_contract_and_registry_are_closed() -> None:
    schema = load_json(SCHEMA)
    result_schema = load_json(RESULT_SCHEMA)
    registry = load_json(REGISTRY)
    assert schema["$id"].endswith("leaf-promotion-dossier-v1.schema.json")
    assert result_schema["$id"].endswith(
        "leaf-promotion-lock-result-v1.schema.json"
    )
    assert schema["additionalProperties"] is False
    assert result_schema["additionalProperties"] is False
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
    assert len(registry["validation_precedence"]) >= 12


def test_zero_promotion_fixture_is_explicit_valid_and_blocks_m9() -> None:
    dossier = load_json(DOSSIER)
    result = load_json(RESULT)
    assert dossier["evidence_class"] == "SYNTHETIC_OFFLINE_FIXTURE"
    assert dossier["capture_context"] == "OFF_LAN"
    assert dossier["positive_promotion_claim"] is False
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
