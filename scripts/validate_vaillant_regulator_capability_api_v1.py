#!/usr/bin/env python3
"""Validate the closed, Vaillant-only regulator capability API contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from graphql import build_schema, parse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/platform/manifests/vaillant-regulator-capability-api-v1.json"
CASES = ROOT / "docs/platform/fixtures/vaillant-regulator-capability-api-v1/cases.json"
SDL = ROOT / "api/vaillant-regulator-capability-v1.graphql"

EXPECTED_STATES = {"UNKNOWN", "NONE", "PRESENT"}
EXPECTED_FORBIDDEN_INPUTS = {"basv_prefix", "vrc_prefix", "display_name", "per_device_role"}
EXPECTED_MANIFEST_KEYS = {
    "contract_id",
    "contract_version",
    "graphql",
    "mcp",
    "semantic_snapshot",
    "precedence",
    "defaults",
    "consumer_constraints",
    "catalog_classifier",
    "scope",
    "sources",
}
EXPECTED_CASES_KEYS = {"schema_version", "positive", "negative", "catalog_classifier"}
EXPECTED_CONSUMER_CONSTRAINT_KEYS = {
    "forbidden_inference_inputs",
    "absence_grace_part_of_field",
    "none_and_unknown_need_settled_removal_signal",
}
EXPECTED_SDL_DEFINITIONS = {
    ("object_type_definition", "Query"),
    ("enum_type_definition", "VaillantRegulatorCapability"),
}
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
EXPECTED_CATALOG_CLASSIFIER = {
    "contract_status": "target_ebusreg_169",
    "evidence_status": "unknown_pending_implementation",
    "capability_index_row": "nonempty_normalized_part_number_and_role",
    "enrichment_index": "distinct_richer_metadata_index",
    "controller_roles": ["Regulator", "Thermostat"],
    "role_match": "case_insensitive",
    "present": "known_capability_index_row_with_controller_role",
    "none": "known_capability_index_row_with_other_nonempty_role",
    "unknown": ["missing_part_number", "missing_catalog_row", "roleless_catalog_row"],
    "classification": "read_only",
    "does_not_admit": ["profile", "b524", "routing", "control"],
    "does_not_bypass_issue": 167,
}
EXPECTED_PRECEDENCE = {
    "present": "any_vaillant_identity_catalog_classified_regulator",
    "none": "at_least_one_detected_vaillant_identity_and_every_detected_identity_catalog_known_non_regulator",
    "unknown": [
        "catalog_failure",
        "no_vaillant_inventory",
        "catalog_lookup_miss_for_detected_vaillant_identity_without_present",
    ],
}
EXPECTED_SOURCES = {
    "gateway": {
        "repository": "Project-Helianthus/helianthus-ebusgateway",
        "revision": "76d66a60b2895b3392bba798a5f690a1d73daa1f",
        "issues": [193, 194, 946],
        "pull_requests": [211, 212, 947],
    },
    "ebusreg": {
        "repository": "Project-Helianthus/helianthus-ebusreg",
        "revision": "e24532a50caa00c113751b98b88239e045d731e8",
        "historical_controller_capability_merge": "ad503214d698ee5a0c58da2ce637a54dd714409b",
        "issue": 97,
        "pull_request": 98,
        "capability_role_policy_issue": 169,
    },
    "documentation_issue": 532,
    "consumer": {
        "repository": "Project-Helianthus/helianthus-ha-integration",
        "issue": 101,
    },
}
EXPECTED_POSITIVE_CASES = [
    {"name": "present_wins_over_unknown", "catalog_states": ["NONE", "UNKNOWN", "PRESENT"], "result": "PRESENT"},
    {"name": "none_requires_known_non_regulator_inventory", "catalog_states": ["NONE", "NONE"], "result": "NONE"},
    {"name": "catalog_lookup_miss_is_unknown", "catalog_states": ["NONE", "UNKNOWN"], "result": "UNKNOWN"},
    {"name": "empty_inventory_is_unknown", "catalog_states": [], "result": "UNKNOWN"},
    {"name": "catalog_failure_is_unknown", "catalog_states": ["CATALOG_FAILURE"], "result": "UNKNOWN"},
    {"name": "unwired_provider_is_unknown", "catalog_states": ["PROVIDER_UNWIRED"], "result": "UNKNOWN"},
    {"name": "provider_failure_is_unknown", "catalog_states": ["PROVIDER_FAILURE"], "result": "UNKNOWN"},
    {"name": "older_gateway_field_is_unknown", "catalog_states": ["MISSING_FIELD"], "result": "UNKNOWN"},
]
EXPECTED_NEGATIVE_CASES = [
    {"name": "no_identity_is_not_none", "catalog_states": [], "forbidden_result": "NONE"},
    {"name": "catalog_lookup_miss_is_not_none", "catalog_states": ["NONE", "UNKNOWN"], "forbidden_result": "NONE"},
    {"name": "name_or_role_is_not_input", "forbidden_inputs": ["basv_prefix", "vrc_prefix", "display_name", "per_device_role"]},
]
EXPECTED_CATALOG_CLASSIFIER_CASES = [
    {"name": "incomplete_enrichment_regulator_is_present", "part_number": "PN-REG", "catalog_record": {"part_number": "PN-REG", "role": "rEgUlAtOr", "brand": "", "family": "", "product_model": ""}, "result": "PRESENT"},
    {"name": "thermostat_is_present_case_insensitively", "part_number": "PN-THERM", "catalog_record": {"part_number": "PN-THERM", "role": "THERMOSTAT", "brand": "", "family": "", "product_model": ""}, "result": "PRESENT"},
    {"name": "known_other_role_is_none", "part_number": "PN-BOILER", "catalog_record": {"part_number": "PN-BOILER", "role": "Boiler", "brand": "", "family": "", "product_model": ""}, "result": "NONE"},
    {"name": "roleless_row_is_unknown", "part_number": "PN-ROLELESS", "catalog_record": {"part_number": "PN-ROLELESS", "role": "  ", "brand": "", "family": "", "product_model": ""}, "result": "UNKNOWN"},
    {"name": "missing_catalog_row_is_unknown", "part_number": "PN-MISSING", "catalog_record": None, "result": "UNKNOWN"},
    {"name": "missing_part_number_is_unknown", "part_number": "  ", "catalog_record": {"part_number": "PN-REG", "role": "Regulator", "brand": "", "family": "", "product_model": ""}, "result": "UNKNOWN"},
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


def resolve_catalog_classifier(part_number: str, record: object) -> str:
    if not isinstance(part_number, str):
        raise ValidationError(f"invalid part number: {part_number!r}")
    normalized_part_number = part_number.strip()
    if not normalized_part_number or record is None:
        return "UNKNOWN"
    if not isinstance(record, dict):
        raise ValidationError(f"invalid catalog record: {record!r}")
    record_part_number = record.get("part_number")
    role = record.get("role")
    if not isinstance(record_part_number, str) or not isinstance(role, str):
        raise ValidationError(f"invalid catalog record: {record!r}")
    if record_part_number.strip() != normalized_part_number or not role.strip():
        return "UNKNOWN"
    if role.strip().casefold() in {"regulator", "thermostat"}:
        return "PRESENT"
    return "NONE"


def validate(manifest: dict, cases: dict) -> list[str]:
    errors: list[str] = []
    if set(manifest) != EXPECTED_MANIFEST_KEYS:
        errors.append("manifest_shape")
    if set(cases) != EXPECTED_CASES_KEYS:
        errors.append("case_shape")
    contract_version = manifest.get("contract_version")
    if (
        manifest.get("contract_id") != "VAILLANT_REGULATOR_CAPABILITY_API_V1"
        or type(contract_version) is not int
        or contract_version != 1
    ):
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
    if manifest.get("catalog_classifier") != EXPECTED_CATALOG_CLASSIFIER:
        errors.append("catalog_classifier")
    defaults = manifest.get("defaults")
    if not isinstance(defaults, dict) or set(defaults.values()) != {"UNKNOWN"} or set(defaults) != {"provider_unwired", "provider_failure", "missing_or_older_gateway_field"}:
        errors.append("defaults")
    constraints = manifest.get("consumer_constraints")
    forbidden_inputs = constraints.get("forbidden_inference_inputs") if isinstance(constraints, dict) else None
    if (
        not isinstance(constraints, dict)
        or set(constraints) != EXPECTED_CONSUMER_CONSTRAINT_KEYS
        or not isinstance(forbidden_inputs, list)
        or len(forbidden_inputs) != len(EXPECTED_FORBIDDEN_INPUTS)
        or any(type(item) is not str for item in forbidden_inputs)
        or set(forbidden_inputs) != EXPECTED_FORBIDDEN_INPUTS
        or constraints.get("absence_grace_part_of_field") is not False
        or constraints.get("none_and_unknown_need_settled_removal_signal") is not False
    ):
        errors.append("consumer_constraints")
    if manifest.get("sources") != EXPECTED_SOURCES:
        errors.append("sources")
    schema_version = cases.get("schema_version")
    if type(schema_version) is not int or schema_version != 1:
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
    catalog_classifier_cases = cases.get("catalog_classifier")
    if catalog_classifier_cases != EXPECTED_CATALOG_CLASSIFIER_CASES:
        errors.append("catalog_classifier_cases")
    else:
        for case in catalog_classifier_cases:
            try:
                result = resolve_catalog_classifier(case["part_number"], case["catalog_record"])
            except (KeyError, ValidationError):
                errors.append("catalog_classifier_case_result")
                break
            if result != case["result"]:
                errors.append("catalog_classifier_case_result")
                break
    return errors


def validate_sdl(sdl_path: Path = SDL) -> list[str]:
    sdl = sdl_path.read_text(encoding="utf-8")
    schema = build_schema(sdl)
    query = schema.query_type
    enum = schema.get_type("VaillantRegulatorCapability")
    if query is None or query.name != "Query":
        return ["sdl_query_root"]
    if schema.mutation_type is not None or schema.subscription_type is not None:
        return ["sdl_operations"]
    definitions = {
        (definition.kind, getattr(getattr(definition, "name", None), "value", None))
        for definition in parse(sdl).definitions
    }
    if len(definitions) != len(EXPECTED_SDL_DEFINITIONS) or definitions != EXPECTED_SDL_DEFINITIONS:
        return ["sdl_definitions"]
    if enum is None:
        return ["sdl_missing_type"]
    if set(query.fields) != {"vaillant_regulator_capability"}:
        return ["sdl_query_fields"]
    field = query.fields.get("vaillant_regulator_capability")
    if field is None or str(field.type) != "VaillantRegulatorCapability!":
        return ["sdl_root"]
    if field.args:
        return ["sdl_arguments"]
    if field.deprecation_reason is not None:
        return ["sdl_deprecated"]
    if set(enum.values) != EXPECTED_STATES:
        return ["sdl_enum"]
    if any(enum.values[state].deprecation_reason is not None for state in EXPECTED_STATES):
        return ["sdl_enum_deprecated"]
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
