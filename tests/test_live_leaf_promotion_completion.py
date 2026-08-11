from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE = (
    ROOT
    / "docs/platform/evidence/leaf-promotion-captured-multi-leaf/v1"
    / "live-vr940-0.6.37-20260812"
)
M8_EVIDENCE = LIVE / "m8-evidence.json"
M8_REPORT = LIVE / "m8-report.json"
PUBLIC_RESULT = LIVE / "public-result.json"
COMPLETION = LIVE / "README.md"
M8_VALIDATOR = ROOT / "scripts/validate_multi_runtime_coexistence.py"
M85_VALIDATOR = ROOT / "scripts/validate_captured_multi_leaf_promotion.py"
M8_REGISTRY = ROOT / "docs/platform/schemas/multi-runtime-coexistence-registry-v1.json"
M85_REGISTRY = (
    ROOT / "docs/platform/schemas/leaf-promotion-captured-multi-leaf-registry-v1.json"
)
M7_REGISTRY = ROOT / "docs/platform/schemas/draft-candidate-fact-registry-v1.json"
M7 = ROOT / "docs/platform/fixtures/candidate-fact-graph/v1/positive"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_validator():
    spec = importlib.util.spec_from_file_location("live_m85_validator", M85_VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_published_bytes_and_source_bindings_are_exact() -> None:
    assert sha256(M8_EVIDENCE) == "529c18ea157fb7ea366e864f27927c680725f77d90295c4b2d1841fbc47d05cf"
    assert sha256(M8_REPORT) == "b2663e24d6c290a5ab3f508dbb5858e56c9f22337e0e023bfd7bffbf632f5306"
    assert sha256(PUBLIC_RESULT) == "ae5998f450ec08b936104134f2c5c04546ed26fe5df8aaa13d6a0546c9382784"

    evidence = load(M8_EVIDENCE)
    report = load(M8_REPORT)
    result = load(PUBLIC_RESULT)
    assert evidence["export_tier"] == report["export_tier"] == "PUBLIC_REDACTED"
    assert report["verdict"] == "PASS"
    assert result["source_bindings"]["m8_evidence_bytes_hash"] == "sha256:" + sha256(M8_EVIDENCE)
    assert result["source_bindings"]["m8_report_bytes_hash"] == "sha256:" + sha256(M8_REPORT)
    assert result["source_bindings"]["m8_evidence_hash"] == evidence["evidence_hash"]
    assert result["source_bindings"]["m8_report_hash"] == report["report_hash"]


def test_m8_public_evidence_passes_the_canonical_validator() -> None:
    terminal = {
        "--m7-graph": M7 / "source-terminal-graph.json",
        "--m7-replay": M7 / "source-terminal-replay-result.json",
        "--m7-source-bundle": M7 / "source-terminal-bundle.json",
        "--m7-source-replay": M7 / "source-terminal-source-replay.json",
        "--m7-terminal-graph": M7 / "source-terminal-graph.json",
        "--m7-terminal-replay": M7 / "source-terminal-replay-result.json",
        "--m7-terminal-source-bundle": M7 / "source-terminal-bundle.json",
        "--m7-terminal-source-replay": M7 / "source-terminal-source-replay.json",
    }
    command = [
        sys.executable,
        str(M8_VALIDATOR),
        "verify-public",
        "--evidence",
        str(M8_EVIDENCE),
        "--registry",
        str(M8_REGISTRY),
        "--m7-registry",
        str(M7_REGISTRY),
    ]
    for option, path in terminal.items():
        command.extend((option, str(path)))
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "public-only-ok"


def test_live_result_is_valid_and_keeps_all_promotions_unexposed() -> None:
    result = load(PUBLIC_RESULT)
    validator = load_validator()
    registry = load(M85_REGISTRY)
    validator._verify_public_structure(result, registry)

    assert result["evidence_mode"] == "LIVE_CAPTURE"
    assert result["export_tier"] == "PUBLIC_REDACTED"
    assert result["counts"] == {"total": 18, "promoted": 3, "withheld": 15}
    assert result["verdict"] == "VALID_PROMOTION_LOCK"
    assert result["m9_consumer_gate"] == "READY_FOR_M9_PLANNING"
    promoted = [item for item in result["candidate_results"] if item["decision"] == "PROMOTED"]
    assert [item["candidate_id"] for item in promoted] == [
        "m7-candidate-0012",
        "m7-candidate-0014",
        "m7-candidate-0016",
    ]
    assert all(item["visibility"] == "LOCKED_NOT_EXPOSED" for item in promoted)
    assert all(item["window_outcomes"] == ["MATCH", "MATCH"] for item in promoted)


def test_public_projection_has_no_private_identity_or_secret_fields() -> None:
    result = load(PUBLIC_RESULT)

    def keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return {str(key).lower() for key in value} | {
                nested for item in value.values() for nested in keys(item)
            }
        if isinstance(value, list):
            return {nested for item in value for nested in keys(item)}
        return set()

    forbidden = {
        "candidate_ref",
        "semantic_path",
        "ski",
        "ship_id",
        "service_id",
        "device_address",
        "entity_address",
        "feature_address",
        "private_key",
        "private_key_pem",
        "trust_store_bytes",
        "token",
    }
    assert keys(result).isdisjoint(forbidden)
    assert "PRIVATE_REDACTED" not in PUBLIC_RESULT.read_text(encoding="utf-8")


def test_completion_record_stops_before_m9_consumers() -> None:
    text = COMPLETION.read_text(encoding="utf-8")
    assert "READY_FOR_M9_PLANNING" in text
    assert "does not authorize M9 implementation" in text
    assert "LOCKED_NOT_EXPOSED" in text
    assert "GraphQL, Portal, Home Assistant" in text
