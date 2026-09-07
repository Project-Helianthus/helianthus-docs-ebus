#!/usr/bin/env python3
"""Validate the closed, Vaillant-only regulator capability API contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from graphql import build_schema

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/platform/manifests/vaillant-regulator-capability-api-v1.json"
CASES = ROOT / "docs/platform/fixtures/vaillant-regulator-capability-api-v1/cases.json"
SDL = ROOT / "api/vaillant-regulator-capability-v1.graphql"

EXPECTED_STATES = {"UNKNOWN", "NONE", "PRESENT"}
EXPECTED_FORBIDDEN_INPUTS = {"basv_prefix", "vrc_prefix", "display_name", "per_device_role"}
EXPECTED_CATALOG_STATES = {
    "NONE",
    "UNKNOWN",
    "PRESENT",
    "CATALOG_FAILURE",
    "PROVIDER_UNWIRED",
    "PROVIDER_FAILURE",
    "MISSING_FIELD",
}
EXPECTED_SCOPE = {
    "protocol_vendor": "vaillant",
    "gateway_wide": False,
    "cross_protocol": False,
}
EXPECTED_PRECEDENCE = {
    "present": "any_vaillant_identity_catalog_classified_regulator",
    "none": "at_least_one_vaillant_identity_and_all_relevant_identities_catalog_known_non_regulator",
    "unknown": [
        "catalog_failure",
        "no_vaillant_inventory",
        "unclassified_vaillant_identity_without_present",
    ],
}
EXPECTED_SOURCES = {
    "gateway": {
        "repository": "Project-Helianthus/helianthus-ebusgateway",
        "revision": "f52c08405e48609fb05ae8b231d1530bcfb46094",
        "issues": [193, 194, 946],
        "pull_requests": [211, 212],
    },
    "ebusreg": {
        "repository": "Project-Helianthus/helianthus-ebusreg",
        "revision": "e24532a50caa00c113751b98b88239e045d731e8",
        "historical_controller_capability_merge": "ad503214d698ee5a0c58da2ce637a54dd714409b",
        "issue": 97,
        "pull_request": 98,
    },
    "documentation_issue": 511,
    "consumer": {
        "repository": "Project-Helianthus/helianthus-ha-integration",
        "issue": 101,
    },
}
EXPECTED_POSITIVE_CASES = [
    {"name": "present_wins_over_unknown", "catalog_states": ["NONE", "UNKNOWN", "PRESENT"], "result": "PRESENT"},
    {"name": "none_requires_known_non_regulator_inventory", "catalog_states": ["NONE", "NONE"], "result": "NONE"},
    {"name": "unclassified_identity_is_unknown", "catalog_states": ["NONE", "UNKNOWN"], "result": "UNKNOWN"},
    {"name": "empty_inventory_is_unknown", "catalog_states": [], "result": "UNKNOWN"},
    {"name": "catalog_failure_is_unknown", "catalog_states": ["CATALOG_FAILURE"], "result": "UNKNOWN"},
    {"name": "unwired_provider_is_unknown", "catalog_states": ["PROVIDER_UNWIRED"], "result": "UNKNOWN"},
    {"name": "provider_failure_is_unknown", "catalog_states": ["PROVIDER_FAILURE"], "result": "UNKNOWN"},
    {"name": "older_gateway_field_is_unknown", "catalog_states": ["MISSING_FIELD"], "result": "UNKNOWN"},
]
EXPECTED_NEGATIVE_CASES = [
    {"name": "no_identity_is_not_none", "catalog_states": [], "forbidden_result": "NONE"},
    {"name": "unknown_is_not_none", "catalog_states": ["NONE", "UNKNOWN"], "forbidden_result": "NONE"},
    {"name": "name_or_role_is_not_input", "forbidden_inputs": ["basv_prefix", "vrc_prefix", "display_name", "per_device_role"]},
]


class ValidationError(ValueError):
    pass


def load(path: Path) -> dict:
    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise ValidationError(str(error)) from error
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain an object")
    return value


def resolve(states: list[str]) -> str:
    if not isinstance(states, list) or any(state not in EXPECTED_CATALOG_STATES for state in states):
        raise ValidationError(f"unsupported catalog state sequence: {states!r}")
    if any(state == "PRESENT" for state in states):
        return "PRESENT"
    if not states or any(state in {"UNKNOWN", "CATALOG_FAILURE", "PROVIDER_UNWIRED", "PROVIDER_FAILURE", "MISSING_FIELD"} for state in states):
        return "UNKNOWN"
    if all(state == "NONE" for state in states):
        return "NONE"
    raise ValidationError(f"unsupported catalog state sequence: {states!r}")


def validate(manifest: dict, cases: dict) -> list[str]:
    errors: list[str] = []
    if manifest.get("contract_id") != "VAILLANT_REGULATOR_CAPABILITY_API_V1" or manifest.get("contract_version") != 1:
        errors.append("identity")
    graphql = manifest.get("graphql")
    if graphql != {"root_field": "vaillant_regulator_capability", "type": "VaillantRegulatorCapability!", "enum": ["UNKNOWN", "NONE", "PRESENT"]}:
        errors.append("graphql")
    if manifest.get("mcp") != {"tool": "ebus.v1.runtime.status.get", "data_field": "vaillant_regulator_capability"}:
        errors.append("mcp")
    if manifest.get("semantic_snapshot") != {"object": "runtime_status", "field": "vaillant_regulator_capability"}:
        errors.append("semantic_snapshot")
    if manifest.get("precedence") != EXPECTED_PRECEDENCE:
        errors.append("precedence")
    if manifest.get("scope") != EXPECTED_SCOPE:
        errors.append("scope")
    defaults = manifest.get("defaults")
    if not isinstance(defaults, dict) or set(defaults.values()) != {"UNKNOWN"} or set(defaults) != {"provider_unwired", "provider_failure", "missing_or_older_gateway_field"}:
        errors.append("defaults")
    constraints = manifest.get("consumer_constraints")
    if not isinstance(constraints, dict) or set(constraints.get("forbidden_inference_inputs", [])) != EXPECTED_FORBIDDEN_INPUTS or constraints.get("absence_grace_part_of_field") is not False or constraints.get("none_and_unknown_need_settled_removal_signal") is not False:
        errors.append("consumer_constraints")
    if manifest.get("sources") != EXPECTED_SOURCES:
        errors.append("sources")
    if cases.get("schema_version") != 1:
        errors.append("case_schema")
    positive = cases.get("positive")
    if positive != EXPECTED_POSITIVE_CASES:
        errors.append("positive_cases")
    elif any(resolve(case["catalog_states"]) != case["result"] for case in positive):
        errors.append("positive_case_result")
    negative = cases.get("negative")
    if negative != EXPECTED_NEGATIVE_CASES:
        errors.append("negative_cases")
    else:
        for case in negative:
            if "forbidden_result" in case and resolve(case.get("catalog_states", [])) == case["forbidden_result"]:
                errors.append("negative_case_result")
                break
    return errors


def validate_sdl() -> list[str]:
    schema = build_schema(SDL.read_text(encoding="utf-8"))
    query = schema.get_type("Query")
    enum = schema.get_type("VaillantRegulatorCapability")
    if query is None or enum is None:
        return ["sdl_missing_type"]
    field = query.fields.get("vaillant_regulator_capability")
    if field is None or str(field.type) != "VaillantRegulatorCapability!":
        return ["sdl_root"]
    if set(enum.values) != EXPECTED_STATES:
        return ["sdl_enum"]
    return []


def main() -> int:
    try:
        errors = validate(load(MANIFEST), load(CASES)) + validate_sdl()
    except ValidationError as error:
        print(f"vaillant_regulator_capability_api_v1_invalid: {error}", file=sys.stderr)
        return 1
    if errors:
        print(f"vaillant_regulator_capability_api_v1_invalid: {','.join(errors)}", file=sys.stderr)
        return 1
    print("vaillant_regulator_capability_api_v1_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
