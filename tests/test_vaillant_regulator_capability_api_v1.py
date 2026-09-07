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
from validate_vaillant_regulator_capability_api_v1 import (  # noqa: E402
    ValidationError,
    SDL,
    resolve,
    validate,
    validate_sdl,
)


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
    assert resolve(["PROVIDER_FAILURE"]) == "UNKNOWN"


def test_resolve_rejects_unknown_catalog_tokens_before_precedence() -> None:
    for states in (["PRESENT", "TYPO"], ["UNKNOWN", "TYPO"]):
        try:
            resolve(states)
        except ValidationError:
            continue
        raise AssertionError(f"unsupported states accepted: {states!r}")


def test_validator_rejects_missing_field_compatibility_or_heuristic_reintroduction() -> None:
    manifest, cases = load(MANIFEST), load(CASES)
    missing_default = copy.deepcopy(manifest)
    missing_default["defaults"]["missing_or_older_gateway_field"] = "NONE"
    assert "defaults" in validate(missing_default, cases)
    heuristic = copy.deepcopy(manifest)
    heuristic["consumer_constraints"]["forbidden_inference_inputs"].remove("vrc_prefix")
    assert "consumer_constraints" in validate(heuristic, cases)


def test_validator_requires_closed_forbidden_inference_input_list() -> None:
    manifest, cases = load(MANIFEST), load(CASES)
    mutations = (
        {"basv_prefix": True},
        ["basv_prefix", "basv_prefix", "display_name", "per_device_role"],
        ["basv_prefix", "vrc_prefix", "display_name"],
        ["basv_prefix", "vrc_prefix", "display_name", "per_device_role", "extra"],
        ["basv_prefix", "vrc_prefix", "display_name", 1],
    )
    for forbidden_inputs in mutations:
        candidate = copy.deepcopy(manifest)
        candidate["consumer_constraints"]["forbidden_inference_inputs"] = forbidden_inputs
        assert "consumer_constraints" in validate(candidate, cases)


def test_validator_requires_complete_consumer_constraints_object() -> None:
    manifest, cases = load(MANIFEST), load(CASES)
    extra = copy.deepcopy(manifest)
    extra["consumer_constraints"]["allowed_inference_inputs"] = []
    assert "consumer_constraints" in validate(extra, cases)
    deleted = copy.deepcopy(manifest)
    del deleted["consumer_constraints"]["absence_grace_part_of_field"]
    assert "consumer_constraints" in validate(deleted, cases)
    type_drift = copy.deepcopy(manifest)
    type_drift["consumer_constraints"]["absence_grace_part_of_field"] = "false"
    assert "consumer_constraints" in validate(type_drift, cases)


def test_validator_rejects_undeclared_top_level_machine_keys() -> None:
    manifest, cases = load(MANIFEST), load(CASES)
    extra_manifest = copy.deepcopy(manifest)
    extra_manifest["undeclared"] = True
    assert "manifest_shape" in validate(extra_manifest, cases)
    extra_cases = copy.deepcopy(cases)
    extra_cases["undeclared"] = True
    assert "case_shape" in validate(manifest, extra_cases)


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


def test_validator_rejects_source_coordinate_mutations() -> None:
    manifest, cases = load(MANIFEST), load(CASES)
    mutations = (
        ("gateway", "repository", "other/gateway"),
        ("gateway", "revision", "0" * 40),
        ("gateway", "issues", [193]),
        ("gateway", "pull_requests", [211]),
        ("ebusreg", "historical_controller_capability_merge", "0" * 40),
        ("consumer", "repository", "other/consumer"),
    )
    for section, key, value in mutations:
        candidate = copy.deepcopy(manifest)
        candidate["sources"][section][key] = value
        assert "sources" in validate(candidate, cases)


def test_validator_rejects_duplicated_or_missing_fixture_cases() -> None:
    manifest, cases = load(MANIFEST), load(CASES)
    duplicated = copy.deepcopy(cases)
    duplicated["positive"] = [copy.deepcopy(cases["positive"][0]) for _ in cases["positive"]]
    assert "positive_cases" in validate(manifest, duplicated)
    missing = copy.deepcopy(cases)
    missing["negative"] = missing["negative"][:-1]
    assert "negative_cases" in validate(manifest, missing)


def test_validator_rejects_boolean_versions() -> None:
    manifest, cases = load(MANIFEST), load(CASES)
    boolean_contract = copy.deepcopy(manifest)
    boolean_contract["contract_version"] = True
    assert "identity" in validate(boolean_contract, cases)
    boolean_schema = copy.deepcopy(cases)
    boolean_schema["schema_version"] = True
    assert "case_schema" in validate(manifest, boolean_schema)


def test_sdl_rejects_required_root_argument(tmp_path: Path) -> None:
    mutated = tmp_path / "mutated.graphql"
    mutated.write_text(
        SDL.read_text(encoding="utf-8").replace(
            "vaillant_regulator_capability: VaillantRegulatorCapability!",
            "vaillant_regulator_capability(required: Boolean!): VaillantRegulatorCapability!",
        ),
        encoding="utf-8",
    )
    assert validate_sdl(mutated) == ["sdl_arguments"]


def test_sdl_rejects_redirected_configured_query_root(tmp_path: Path) -> None:
    mutated = tmp_path / "redirected.graphql"
    mutated.write_text(
        SDL.read_text(encoding="utf-8")
        + "\nschema { query: Root }\ntype Root { placeholder: String! }\n",
        encoding="utf-8",
    )
    assert validate_sdl(mutated) == ["sdl_query_root"]


def test_sdl_rejects_deprecated_public_root(tmp_path: Path) -> None:
    mutated = tmp_path / "deprecated.graphql"
    mutated.write_text(
        SDL.read_text(encoding="utf-8").replace(
            "vaillant_regulator_capability: VaillantRegulatorCapability!",
            "vaillant_regulator_capability: VaillantRegulatorCapability! @deprecated(reason: \"test\")",
        ),
        encoding="utf-8",
    )
    assert validate_sdl(mutated) == ["sdl_deprecated"]


def test_sdl_rejects_deprecated_required_enum_state(tmp_path: Path) -> None:
    mutated = tmp_path / "deprecated-enum.graphql"
    mutated.write_text(
        SDL.read_text(encoding="utf-8").replace(
            "  PRESENT\n",
            "  PRESENT @deprecated(reason: \"test\")\n",
        ),
        encoding="utf-8",
    )
    assert validate_sdl(mutated) == ["sdl_enum_deprecated"]


def test_sdl_rejects_undeclared_extra_query_root_field(tmp_path: Path) -> None:
    mutated = tmp_path / "extra-query-field.graphql"
    mutated.write_text(
        SDL.read_text(encoding="utf-8").replace(
            "  vaillant_regulator_capability: VaillantRegulatorCapability!\n}",
            "  vaillant_regulator_capability: VaillantRegulatorCapability!\n  extra_root: Boolean!\n}",
        ),
        encoding="utf-8",
    )
    assert validate_sdl(mutated) == ["sdl_query_fields"]


def test_sdl_rejects_configured_mutation_operation(tmp_path: Path) -> None:
    mutated = tmp_path / "mutation-operation.graphql"
    mutated.write_text(
        SDL.read_text(encoding="utf-8")
        + "\ntype Mutation { undeclared: Boolean! }\nschema { query: Query mutation: Mutation }\n",
        encoding="utf-8",
    )
    assert validate_sdl(mutated) == ["sdl_operations"]


def test_validator_cli_is_deterministic() -> None:
    result = subprocess.run([sys.executable, "scripts/validate_vaillant_regulator_capability_api_v1.py"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "vaillant_regulator_capability_api_v1_ok"
