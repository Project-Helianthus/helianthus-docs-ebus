#!/usr/bin/env python3
"""Validate the closed PUBLIC_GRAPHQL_M2M_V1 fixture deterministically."""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import re
import sys
from pathlib import Path

DECIMAL = re.compile(r"-?(0|[1-9][0-9]*)$")
NONNEGATIVE_INTEGER = re.compile(r"0|[1-9][0-9]*$")
SHA256 = re.compile(r"sha256:[0-9a-f]{64}$")
TOKEN = re.compile(r"[A-Za-z0-9._:-]+$")
FORBIDDEN = {"raw_registers", "source_shadow", "endpoint", "endpoints", "address", "credentials", "history"}


class ValidationError(Exception):
    pass


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _set_path(value, pointer, replacement):
    result = copy.deepcopy(value)
    parts = pointer.split("/")[1:]
    parent = result
    for part in parts[:-1]:
        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
    leaf = parts[-1]
    if isinstance(parent, list):
        parent[int(leaf)] = replacement
    else:
        parent[leaf] = replacement
    return result


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _valid_timestamp(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _valid_dimensions(dimensions, definition):
    if not isinstance(dimensions, dict) or len(dimensions) != 1 or set(dimensions) != set(definition["dimensions"]):
        return False
    key, value = next(iter(dimensions.items()))
    if key == "scope":
        return value == "total"
    if key == "phase":
        return value in {"L1", "L2", "L3"}
    if key == "phase_pair":
        return value in {"L1_L2", "L2_L3", "L3_L1"}
    return isinstance(value, str) and 1 <= len(value) <= 64 and TOKEN.fullmatch(value) is not None


def _valid_value(value, definition, canonical_manifest):
    if not isinstance(value, dict) or value.get("kind") != definition["value_kind"]:
        return False
    if value["kind"] == "decimal":
        return (
            set(value) == {"kind", "coefficient", "scale"}
            and isinstance(value["coefficient"], str)
            and DECIMAL.fullmatch(value["coefficient"]) is not None
            and isinstance(value["scale"], int)
            and not isinstance(value["scale"], bool)
            and -18 <= value["scale"] <= 18
        )
    domain = canonical_manifest["value_domains"][definition["value_domain"]]
    if value["kind"] == "enum":
        return set(value) == {"kind", "symbol"} and value["symbol"] in domain
    return (
        set(value) == {"kind", "symbols"}
        and isinstance(value["symbols"], list)
        and len(value["symbols"]) <= 64
        and len(value["symbols"]) == len(set(value["symbols"]))
        and all(symbol in domain for symbol in value["symbols"])
    )


def validate_case(case, manifest, canonical_manifest):
    errors = set()
    request, response = case["request"], case["response"]
    if set(request) != {"contract_id", "asset_ref"}:
        errors.add("request_fields")
    if request.get("contract_id") not in manifest["contract_negotiation"]["accepted"]:
        errors.add("contract_negotiation")
    if response.get("contract_id") != request.get("contract_id"):
        errors.add("contract_negotiation")
    if set(response) != set(manifest["required_response_fields"]):
        errors.add("response_fields")
    if response.get("canonical_contract_id") != canonical_manifest["contract_id"]:
        errors.add("canonical_projection")
    if not isinstance(request.get("asset_ref"), str) or request["asset_ref"] != response.get("asset_ref"):
        errors.add("asset")
    if not isinstance(response.get("generation"), str) or NONNEGATIVE_INTEGER.fullmatch(response["generation"]) is None:
        errors.add("time_identity")
    if not isinstance(response.get("evaluated_monotonic_ns"), str) or NONNEGATIVE_INTEGER.fullmatch(response["evaluated_monotonic_ns"]) is None:
        errors.add("time_identity")
    if not _valid_timestamp(response.get("produced_at")):
        errors.add("time_identity")
    if response.get("source_time_state") not in {"UNAVAILABLE", "VALID", "INVALID"}:
        errors.add("source_time_state")
    if any(key in FORBIDDEN for key in _walk_keys(case)):
        errors.add("forbidden_surface")
    facts = response.get("facts", [])
    catalog = {fact["id"]: fact for fact in canonical_manifest["facts"]}
    seen = set()
    origins = set()
    for fact in facts:
        if set(fact) != set(manifest["required_fact_fields"]):
            errors.add("fact_fields")
            continue
        definition = catalog.get(fact["fact_id"])
        identity = (fact["fact_id"], tuple(sorted(fact["dimensions"].items())))
        if definition is None or fact["fact_id"] not in manifest["catalog_fact_ids"] or identity in seen:
            errors.add("catalog")
        seen.add(identity)
        if definition and (
            fact["unit"] != definition["unit"]
            or not _valid_dimensions(fact["dimensions"], definition)
            or fact["freshness_policy"] != definition["freshness_policy"]
        ):
            errors.add("canonical_projection")
        value = fact["value"]
        if definition and not _valid_value(value, definition, canonical_manifest):
            errors.add("decimal_encoding" if definition["value_kind"] == "decimal" else "value_domain")
        if fact["availability"] not in canonical_manifest["state_axes"]["availability"] or fact["freshness"] not in canonical_manifest["state_axes"]["freshness"] or fact["quality"] not in canonical_manifest["state_axes"]["quality"]:
            errors.add("state_axes")
        if f'{fact["availability"]}/{fact["freshness"]}' not in canonical_manifest["allowed_availability_freshness_pairs"]:
            errors.add("state_axes")
        temporal = [fact["receipt_monotonic_ns"], fact["fresh_until_monotonic_ns"], fact["retain_until_monotonic_ns"]]
        if any(not isinstance(item, str) or NONNEGATIVE_INTEGER.fullmatch(item) is None for item in temporal):
            errors.add("time_identity")
        elif int(temporal[0]) > int(temporal[1]) or int(temporal[1]) >= int(temporal[2]):
            errors.add("time_identity")
        continuity = fact["continuity"]
        if definition and definition["accumulator"]:
            if not isinstance(continuity, dict) or continuity.get("state") not in {"BASELINE", "CONTIGUOUS", "ROLLOVER", "RESET", "DISCONTINUITY"}:
                errors.add("continuity")
        elif continuity is not None:
            errors.add("continuity")
        if not SHA256.fullmatch(fact["origin_ref"]):
            errors.add("provenance")
        origins.add(fact["origin_ref"])
    if len(facts) > manifest["max_facts_per_snapshot"]:
        errors.add("bounded_snapshot")
    capabilities = response.get("capabilities", [])
    capability_ids = [item.get("id") for item in capabilities if isinstance(item, dict)]
    if (
        any(set(item) != set(manifest["capability_fields"]) or item["outcome"] not in {"SATISFIED", "NOT_SATISFIED"} for item in capabilities)
        or capability_ids != [item["id"] for item in canonical_manifest["capability_packs"]]
    ):
        errors.add("capability")
    if len(capabilities) > manifest["max_capabilities_per_snapshot"]:
        errors.add("bounded_snapshot")
    provenance = response.get("provenance", [])
    if any(set(item) != set(manifest["opaque_provenance_fields"]) or not SHA256.fullmatch(item["origin_ref"]) or not SHA256.fullmatch(item["evidence_ref"]) for item in provenance):
        errors.add("provenance")
    if origins != {item["origin_ref"] for item in provenance}:
        errors.add("provenance")
    if len(provenance) > manifest["max_provenance_per_snapshot"]:
        errors.add("bounded_snapshot")
    return sorted(errors)


def validate(manifest_path: Path, canonical_manifest_path: Path, cases_path: Path):
    manifest, canonical, cases = map(load_json, (manifest_path, canonical_manifest_path, cases_path))
    if manifest["source_contract"] != canonical["contract_id"] or manifest["catalog_fact_ids"] != [fact["id"] for fact in canonical["facts"]]:
        raise ValidationError("manifest_source_lock")
    errors = validate_case(cases["positive"], manifest, canonical)
    if errors:
        raise ValidationError("positive: " + ", ".join(errors))
    for negative in cases["negative"]:
        candidate = _set_path(cases["positive"], negative["path"], negative["value"])
        if negative["error"] not in validate_case(candidate, manifest, canonical):
            raise ValidationError("negative: " + negative["id"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--canonical-manifest", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    args = parser.parse_args()
    try:
        validate(args.manifest, args.canonical_manifest, args.cases)
    except (ValidationError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"public_graphql_m2m_v1_invalid: {error}", file=sys.stderr)
        return 1
    print("public_graphql_m2m_v1_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
