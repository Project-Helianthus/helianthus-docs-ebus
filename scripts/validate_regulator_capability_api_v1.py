#!/usr/bin/env python3
"""Validate the closed, machine-readable regulator capability API contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from graphql import build_schema

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/platform/manifests/regulator-capability-api-v1.json"
CASES = ROOT / "docs/platform/fixtures/regulator-capability-api-v1/cases.json"
SDL = ROOT / "api/regulator-capability-v1.graphql"

EXPECTED_STATES = {"UNKNOWN", "NONE", "PRESENT"}
EXPECTED_FORBIDDEN_INPUTS = {"basv_prefix", "vrc_prefix", "display_name", "per_device_role"}
EXPECTED_GATEWAY_REVISION = "f52c08405e48609fb05ae8b231d1530bcfb46094"
EXPECTED_EBUSREG_REVISION = "e24532a50caa00c113751b98b88239e045d731e8"


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
    if any(state == "PRESENT" for state in states):
        return "PRESENT"
    if not states or any(state in {"UNKNOWN", "CATALOG_FAILURE", "PROVIDER_UNWIRED", "MISSING_FIELD"} for state in states):
        return "UNKNOWN"
    if all(state == "NONE" for state in states):
        return "NONE"
    raise ValidationError(f"unsupported catalog state sequence: {states!r}")


def validate(manifest: dict, cases: dict) -> list[str]:
    errors: list[str] = []
    if manifest.get("contract_id") != "REGULATOR_CAPABILITY_API_V1" or manifest.get("contract_version") != 1:
        errors.append("identity")
    graphql = manifest.get("graphql")
    if graphql != {"root_field": "regulator_capability", "type": "RegulatorCapability!", "enum": ["UNKNOWN", "NONE", "PRESENT"]}:
        errors.append("graphql")
    if manifest.get("mcp") != {"tool": "ebus.v1.runtime.status.get", "data_field": "regulator_capability"}:
        errors.append("mcp")
    if manifest.get("semantic_snapshot") != {"object": "runtime_status", "field": "regulator_capability"}:
        errors.append("semantic_snapshot")
    defaults = manifest.get("defaults")
    if not isinstance(defaults, dict) or set(defaults.values()) != {"UNKNOWN"} or set(defaults) != {"provider_unwired", "provider_failure", "missing_or_older_gateway_field"}:
        errors.append("defaults")
    constraints = manifest.get("consumer_constraints")
    if not isinstance(constraints, dict) or set(constraints.get("forbidden_inference_inputs", [])) != EXPECTED_FORBIDDEN_INPUTS or constraints.get("absence_grace_part_of_field") is not False or constraints.get("none_and_unknown_need_settled_removal_signal") is not False:
        errors.append("consumer_constraints")
    sources = manifest.get("sources")
    if not isinstance(sources, dict) or sources.get("gateway", {}).get("revision") != EXPECTED_GATEWAY_REVISION or sources.get("ebusreg", {}).get("revision") != EXPECTED_EBUSREG_REVISION or sources.get("documentation_issue") != 511 or sources.get("consumer", {}).get("issue") != 101:
        errors.append("sources")
    if cases.get("schema_version") != 1:
        errors.append("case_schema")
    positive = cases.get("positive")
    if not isinstance(positive, list) or len(positive) != 7:
        errors.append("positive_cases")
    else:
        for case in positive:
            if not isinstance(case, dict) or resolve(case.get("catalog_states", [])) != case.get("result") or case.get("result") not in EXPECTED_STATES:
                errors.append("positive_case_result")
                break
    negative = cases.get("negative")
    if not isinstance(negative, list) or len(negative) != 3:
        errors.append("negative_cases")
    else:
        forbidden = next((case.get("forbidden_inputs") for case in negative if "forbidden_inputs" in case), None)
        if set(forbidden or []) != EXPECTED_FORBIDDEN_INPUTS:
            errors.append("negative_forbidden_inputs")
        for case in negative:
            if "forbidden_result" in case and resolve(case.get("catalog_states", [])) == case["forbidden_result"]:
                errors.append("negative_case_result")
                break
    return errors


def validate_sdl() -> list[str]:
    schema = build_schema(SDL.read_text(encoding="utf-8"))
    query = schema.get_type("Query")
    enum = schema.get_type("RegulatorCapability")
    if query is None or enum is None:
        return ["sdl_missing_type"]
    field = query.fields.get("regulator_capability")
    if field is None or str(field.type) != "RegulatorCapability!":
        return ["sdl_root"]
    if set(enum.values) != EXPECTED_STATES:
        return ["sdl_enum"]
    return []


def main() -> int:
    try:
        errors = validate(load(MANIFEST), load(CASES)) + validate_sdl()
    except ValidationError as error:
        print(f"regulator_capability_api_v1_invalid: {error}", file=sys.stderr)
        return 1
    if errors:
        print(f"regulator_capability_api_v1_invalid: {','.join(errors)}", file=sys.stderr)
        return 1
    print("regulator_capability_api_v1_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
