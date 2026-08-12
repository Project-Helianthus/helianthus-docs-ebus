from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE = ROOT / "docs/platform/live/msp-085-0.6.40"
COEXISTENCE_DOC = ROOT / "docs/platform/multi-runtime-coexistence-no-drift-v1.md"
RESULT = LIVE / "m8.5-result.json"
M8_EVIDENCE = LIVE / "m8-evidence.json"
M8_REPORT = LIVE / "m8-report.json"
REGISTRY = ROOT / "docs/platform/schemas/leaf-promotion-captured-multi-leaf-registry-v1.json"
M8_REGISTRY = ROOT / "docs/platform/schemas/multi-runtime-coexistence-registry-v1.json"
M7_REGISTRY = ROOT / "docs/platform/schemas/draft-candidate-fact-registry-v1.json"
M7_FIXTURE = ROOT / "docs/platform/fixtures/candidate-fact-graph/v1/positive"


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_m8_validator():
    path = ROOT / "scripts/validate_multi_runtime_coexistence.py"
    spec = importlib.util.spec_from_file_location("msp085_final_m8_validator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_final_live_result_locks_all_eighteen_registered_semantic_paths() -> None:
    result = load(RESULT)
    registry = load(REGISTRY)

    real = [
        item for item in registry["candidate_catalog"] if item["retirement_state"] is None
    ]
    retired = [
        item for item in registry["candidate_catalog"] if item["retirement_state"] is not None
    ]
    promoted = [
        item for item in result["candidate_results"] if item["decision"] == "PROMOTED"
    ]

    assert result["counts"] == {
        "records": 22,
        "total": 18,
        "retired": 4,
        "promoted": 18,
        "withheld": 0,
    }
    assert result["verdict"] == "VALID_PROMOTION_LOCK"
    assert result["m9_consumer_gate"] == "READY_FOR_M9_PLANNING"
    assert len(real) == len(promoted) == 18
    assert len(retired) == 4
    assert len({item["semantic_path"] for item in real}) == 18
    assert [item["candidate_id"] for item in promoted] == [
        item["candidate_id"] for item in real
    ]
    assert all(item["visibility"] == "LOCKED_NOT_EXPOSED" for item in promoted)
    assert all(item["terminal_state"] is None for item in promoted)
    assert result["source_bindings"]["campaign_hash"] == (
        "sha256:4e71ee022e54fbaf36452d6ad774ac4f72ebd0ea28803f67b86d7a474d486262"
    )
    assert result["source_bindings"]["private_campaign_bytes_hash"] == (
        "sha256:ae932de0a3a02242da9923627978279d4ae3f4aa159cec060c140e9fd4763b00"
    )
    assert hashlib.sha256(RESULT.read_bytes()).hexdigest() == (
        "376e683b0930d475f6032db401ae8bdca4bafcd7dd69c64aee164ee939a5baa6"
    )
    assert hashlib.sha256(M8_EVIDENCE.read_bytes()).hexdigest() == (
        "bbf204c1e22106a3c26559822f027008a71591c7c484ba773f8d2470f45f6b81"
    )
    assert hashlib.sha256(M8_REPORT.read_bytes()).hexdigest() == (
        "eb6fb17adbb45d147b5a1382d485da61cc1908146baa201ab9ce20400f8bfbdf"
    )
    assert load(M8_REPORT)["verdict"] == "PASS"


def test_final_public_result_contains_no_operator_identity_or_semantic_path() -> None:
    result = RESULT.read_bytes().lower()
    published = b"\n".join(
        path.read_bytes().lower() for path in (RESULT, M8_EVIDENCE, M8_REPORT)
    )
    for forbidden in (
        b"candidate_ref",
        b"private_key",
        b"private key",
        b"begin private",
        b"trust_store",
        b"remote_ski",
        b"local_ski",
        b"ship_id",
        b"entity_address",
        b"feature_address",
    ):
        assert forbidden not in published
    assert b"semantic_path" not in result


def test_final_m8_public_evidence_uses_current_bound_projection() -> None:
    evidence = load(M8_EVIDENCE)
    assert evidence["normalization"]["semantic_registry_projection"] == (
        "fixed_m85_cross_protocol_ebus_core_v1"
    )
    verified = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/validate_multi_runtime_coexistence.py"),
            "verify-public",
            "--evidence",
            str(M8_EVIDENCE),
            "--registry",
            str(M8_REGISTRY),
            "--m7-registry",
            str(M7_REGISTRY),
            "--m7-terminal-graph",
            str(M7_FIXTURE / "source-terminal-graph.json"),
            "--m7-terminal-replay",
            str(M7_FIXTURE / "source-terminal-replay-result.json"),
            "--m7-terminal-source-bundle",
            str(M7_FIXTURE / "source-terminal-bundle.json"),
            "--m7-terminal-source-replay",
            str(M7_FIXTURE / "source-terminal-source-replay.json"),
            "--m7-live-status",
            str(M7_FIXTURE / "live-public-status.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert (verified.returncode, verified.stdout, verified.stderr) == (
        0,
        "public-only-ok\n",
        "",
    )


def test_final_m8_public_projection_rejects_a_missing_core_leaf() -> None:
    validator = load_m8_validator()
    evidence = load(M8_EVIDENCE)
    for run in evidence["runs"][:-1]:
        registry = next(
            view
            for view in run["protected_views"]
            if view["view_id"] == "semantic.registry"
        )["payload"]["data"]
        registry["leaves"].pop()
        registry["selection"]["selected_count"] -= 1

    with pytest.raises(validator.Failure) as raised:
        validator.check_authority(evidence)
    assert str(raised.value) == "authority.ebus"


def test_final_m8_public_projection_cannot_downgrade_by_omission() -> None:
    validator = load_m8_validator()
    evidence = load(M8_EVIDENCE)
    del evidence["normalization"]["semantic_registry_projection"]
    for run in evidence["runs"][:-1]:
        registry = next(
            view
            for view in run["protected_views"]
            if view["view_id"] == "semantic.registry"
        )["payload"]["data"]
        registry["selection"] = {
            "criteria": validator.SEMANTIC_REGISTRY_PROJECTION_LEGACY,
            "excluded_path_pattern": (
                "/schedules/Programs/<index>/Days/<index>/Slots/<index>/"
                "<StartHour|StartMinute|EndHour|EndMinute|TemperatureC|TemperatureRaw>"
            ),
            "selected_count": len(registry["leaves"]),
        }

    with pytest.raises(validator.Failure) as raised:
        validator.check_authority(evidence)
    assert str(raised.value) == "authority.ebus"


def test_canonical_m8_docs_do_not_restore_the_stale_all_leaf_projection() -> None:
    text = COEXISTENCE_DOC.read_text(encoding="utf-8")
    assert "G18 view contains every promoted eBUS leaf" not in text
    assert "Current M8.5\ncaptures use the exact eleven-leaf cross-protocol core" in text
