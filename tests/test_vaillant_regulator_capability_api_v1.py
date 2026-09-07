from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/platform/manifests/vaillant-regulator-capability-api-v1.json"
CASES = ROOT / "docs/platform/fixtures/vaillant-regulator-capability-api-v1/cases.json"
sys.path.insert(0, str(ROOT / "scripts"))
from validate_vaillant_regulator_capability_api_v1 import resolve, validate, validate_sdl  # noqa: E402


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_closed_contract_and_examples_validate() -> None:
    assert validate(load(MANIFEST), load(CASES)) == []
    assert validate_sdl() == []


def test_precedence_is_catalog_only_and_present_wins() -> None:
    assert resolve(["NONE", "UNKNOWN", "PRESENT"]) == "PRESENT"
    assert resolve(["NONE", "NONE"]) == "NONE"
    assert resolve([]) == "UNKNOWN"
    assert resolve(["NONE", "UNKNOWN"]) == "UNKNOWN"
    assert resolve(["CATALOG_FAILURE"]) == "UNKNOWN"


def test_validator_rejects_missing_field_compatibility_or_heuristic_reintroduction() -> None:
    manifest, cases = load(MANIFEST), load(CASES)
    missing_default = copy.deepcopy(manifest)
    missing_default["defaults"]["missing_or_older_gateway_field"] = "NONE"
    assert "defaults" in validate(missing_default, cases)
    heuristic = copy.deepcopy(manifest)
    heuristic["consumer_constraints"]["forbidden_inference_inputs"].remove("vrc_prefix")
    assert "consumer_constraints" in validate(heuristic, cases)


def test_validator_rejects_deleted_or_replaced_precedence() -> None:
    manifest, cases = load(MANIFEST), load(CASES)
    deleted = copy.deepcopy(manifest)
    del deleted["precedence"]
    assert "precedence" in validate(deleted, cases)
    replaced = copy.deepcopy(manifest)
    replaced["precedence"] = {"present": "any_identity", "none": "empty_inventory", "unknown": []}
    assert "precedence" in validate(replaced, cases)


def test_validator_rejects_gateway_wide_or_cross_protocol_scope() -> None:
    manifest, cases = load(MANIFEST), load(CASES)
    gateway_wide = copy.deepcopy(manifest)
    gateway_wide["scope"]["gateway_wide"] = True
    assert "scope" in validate(gateway_wide, cases)
    cross_protocol = copy.deepcopy(manifest)
    cross_protocol["scope"]["cross_protocol"] = True
    assert "scope" in validate(cross_protocol, cases)


def test_validator_cli_is_deterministic() -> None:
    result = subprocess.run([sys.executable, "scripts/validate_vaillant_regulator_capability_api_v1.py"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "vaillant_regulator_capability_api_v1_ok"
