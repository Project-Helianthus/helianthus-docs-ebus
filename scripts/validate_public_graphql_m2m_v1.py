#!/usr/bin/env python3
"""Validate the closed PUBLIC_GRAPHQL_M2M_V1 fixture deterministically."""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import ipaddress
import json
import re
import sys
from pathlib import Path

from graphql import GraphQLError, build_schema, parse, validate as graphql_validate

DECIMAL = re.compile(r"-?(0|[1-9][0-9]*)$")
NONNEGATIVE_INTEGER = re.compile(r"0|[1-9][0-9]*$")
POSITIVE_INTEGER = re.compile(r"[1-9][0-9]*$")
SHA256 = re.compile(r"sha256:[0-9a-f]{64}$")
TOKEN = re.compile(r"[A-Za-z0-9._:-]+$")
SOURCE_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9._@-]*$")
VERSION_TOKEN = re.compile(r"[0-9][0-9A-Za-z._-]*$")
ASSET = re.compile(r"pv-asset-[A-Za-z0-9_-]{1,96}$")
ROOT = Path(__file__).resolve().parents[1]
SDL_PATH = ROOT / "api/public-graphql-m2m-v1.graphql"
GRAPHQL_SCHEMA = build_schema(SDL_PATH.read_text(encoding="utf-8"))
FORBIDDEN = {
    "rawRegisters",
    "raw_registers",
    "sourceShadow",
    "sourceShadowContents",
    "source_shadow",
    "endpoint",
    "endpoints",
    "address",
    "credentials",
    "history",
    "privateFixturePath",
}
INTERNAL_RESPONSE_FIELDS = {
    "contract_id",
    "canonical_contract_id",
    "asset_ref",
    "generation",
    "produced_at",
    "evaluated_monotonic_ns",
    "source_time_state",
    "current_source_origin_ref",
    "facts",
    "capabilities",
    "provenance",
    "requested_outputs",
    "projection_report",
}
INTERNAL_FACT_FIELDS = {
    "fact_id",
    "dimensions",
    "value",
    "unit",
    "quality",
    "availability",
    "freshness",
    "receipt_monotonic_ns",
    "fresh_until_monotonic_ns",
    "retain_until_monotonic_ns",
    "freshness_policy",
    "origin_ref",
    "continuity",
}
INTERNAL_PROVENANCE_FIELDS = {
    "origin_ref",
    "source_protocol",
    "source_profile_id",
    "source_profile_version",
    "source_validity",
    "source_registry_ref",
    "source_observation_ref",
    "evidence_ref",
}


class ValidationError(Exception):
    pass


def _validate_raw_json_depth(text, max_depth):
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > max_depth:
                raise ValidationError(
                    f"JSON nesting exceeds max_depth={max_depth}"
                )
        elif character in "]}":
            depth -= 1


def load_json(path: Path, *, max_depth=64):
    text = path.read_text(encoding="utf-8")
    return loads_json(text, max_depth=max_depth)


def loads_json(text, *, max_depth=64):
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    _validate_raw_json_depth(text, max_depth)
    return json.loads(
        text,
        object_pairs_hook=no_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValidationError(f"non-finite JSON number: {value}")
        ),
    )


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


def _walk_keys(value, *, max_depth=64):
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        if depth > max_depth:
            raise ValidationError("json depth exceeds conformance bound")
        if isinstance(current, dict):
            for key, child in current.items():
                yield key
                stack.append((child, depth + 1))
        elif isinstance(current, list):
            stack.extend((child, depth + 1) for child in current)


def _compact_json_size(value):
    return len(
        json.dumps(
            value,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )


def validate_query_document(query, manifest):
    errors = set()
    if not isinstance(query, str):
        return ["query_syntax"]
    try:
        document = parse(query, no_location=True, max_tokens=4096)
    except (GraphQLError, RecursionError):
        return ["query_syntax"]

    operations = [
        definition
        for definition in document.definitions
        if definition.kind == "operation_definition"
    ]
    if (
        len(operations) != 1
        or len(document.definitions) != 1
        or operations[0].operation.value != "query"
        or operations[0].name is None
        or operations[0].name.value != manifest["request_bounds"]["operation_name"]
    ):
        errors.add("query_operations")
    if any(
        definition.kind in {"fragment_definition", "fragment_spread"}
        for definition in document.definitions
    ):
        errors.add("query_fragment")

    selected_fields = 0
    max_depth = 0
    stack = [
        (operation.selection_set, 0)
        for operation in operations
        if operation.selection_set is not None
    ]
    allowed_inline_types = {
        "M2MDecimalValue",
        "M2MEnumValue",
        "M2MBitfieldValue",
    }
    while stack:
        selection_set, parent_depth = stack.pop()
        for selection in selection_set.selections:
            if selection.kind == "field":
                selected_fields += 1
                depth = parent_depth + 1
                max_depth = max(max_depth, depth)
                if selection.alias is not None:
                    errors.add("query_alias")
                if selection.name.value.startswith("__"):
                    errors.add("query_introspection")
                if selection.directives:
                    errors.add("query_directive")
                if selection.selection_set is not None:
                    stack.append((selection.selection_set, depth))
            elif selection.kind == "fragment_spread":
                errors.add("query_fragment")
            elif selection.kind == "inline_fragment":
                fragment_depth = parent_depth + 1
                max_depth = max(max_depth, fragment_depth)
                if selection.directives:
                    errors.add("query_directive")
                type_name = (
                    selection.type_condition.name.value
                    if selection.type_condition is not None
                    else None
                )
                if type_name not in allowed_inline_types:
                    errors.add("query_fragment")
                stack.append((selection.selection_set, fragment_depth))
            else:
                errors.add("query_syntax")
    if selected_fields > manifest["request_bounds"]["max_selected_fields"]:
        errors.add("query_fields")
    if max_depth > manifest["request_bounds"]["max_query_depth"]:
        errors.add("query_depth")
    if any(operation.directives for operation in operations):
        errors.add("query_directive")
    try:
        if graphql_validate(GRAPHQL_SCHEMA, document, max_errors=100):
            errors.add("query_schema")
    except RecursionError:
        errors.add("query_schema")
    return sorted(errors)


def _normalize_dimensions(value):
    if not isinstance(value, list) or not value:
        raise TypeError("dimensions must be a non-empty GraphQL list")
    dimensions = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"key", "value"}:
            raise TypeError("dimension must contain key and value")
        key = item["key"]
        if not isinstance(key, str) or key in dimensions:
            raise ValueError("dimension keys must be unique strings")
        dimensions[key] = item["value"]
    return dimensions


def _normalize_value(value):
    if not isinstance(value, dict):
        raise TypeError("value must be an object")
    fields = set(value)
    if fields == {"coefficient", "scale"}:
        return {"kind": "DECIMAL", **value}
    if fields == {"symbol"}:
        return {"kind": "ENUM", **value}
    if fields == {"symbols"}:
        return {"kind": "BITFIELD", **value}
    return {"kind": "INVALID", **value}


def _normalize_continuity(value):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"state", "delta", "modulus", "evidenceRef"}:
        raise TypeError("continuity has an invalid GraphQL shape")
    return {
        "state": value["state"],
        "delta": None if value["delta"] is None else _normalize_value(value["delta"]),
        "modulus": None if value["modulus"] is None else _normalize_value(value["modulus"]),
        "evidence_ref": value["evidenceRef"],
    }


def _normalize_case(case):
    request = case["request"]["body"]["variables"]["request"]
    response = case["response"]["body"]["data"]["m2mCurrentSnapshot"]
    facts = []
    for fact in response["facts"]:
        facts.append(
            {
                "fact_id": fact["factId"],
                "dimensions": _normalize_dimensions(fact["dimensions"]),
                "value": _normalize_value(fact["value"]),
                "unit": fact["unit"],
                "quality": fact["quality"],
                "availability": fact["availability"],
                "freshness": fact["freshness"],
                "receipt_monotonic_ns": fact["receiptMonotonicNs"],
                "fresh_until_monotonic_ns": fact["freshUntilMonotonicNs"],
                "retain_until_monotonic_ns": fact["retainUntilMonotonicNs"],
                "freshness_policy": fact["freshnessPolicy"],
                "origin_ref": fact["originRef"],
                "continuity": _normalize_continuity(fact["continuity"]),
            }
        )
    provenance = [
        {
            "origin_ref": item["originRef"],
            "source_protocol": item["sourceProtocol"],
            "source_profile_id": item["sourceProfileId"],
            "source_profile_version": item["sourceProfileVersion"],
            "source_validity": item["sourceValidity"],
            "source_registry_ref": item["sourceRegistryRef"],
            "source_observation_ref": item["sourceObservationRef"],
            "evidence_ref": item["evidenceRef"],
        }
        for item in response["provenance"]
    ]
    requested_outputs = [
        {
            "source_ref": item["sourceRef"],
            "requested_output_ref": item["requestedOutputRef"],
        }
        for item in response["requestedOutputs"]
    ]
    projection_report = [
        {
            "source_ref": item["sourceRef"],
            "requested_output_ref": item["requestedOutputRef"],
            "fact_id": item["factId"],
            "dimensions": None
            if item["dimensions"] is None
            else _normalize_dimensions(item["dimensions"]),
            "outcome": item["outcome"],
        }
        for item in response["projectionReport"]
    ]
    return {
        "request": {
            "contract_id": request["contractId"],
            "asset_ref": request["assetRef"],
        },
        "response": {
            "contract_id": response["contractId"],
            "canonical_contract_id": response["canonicalContractId"],
            "asset_ref": response["assetRef"],
            "generation": response["generation"],
            "produced_at": response["producedAt"],
            "evaluated_monotonic_ns": response["evaluatedMonotonicNs"],
            "source_time_state": response["sourceTimeState"],
            "current_source_origin_ref": response["currentSourceOriginRef"],
            "facts": facts,
            "capabilities": copy.deepcopy(response["capabilities"]),
            "provenance": provenance,
            "requested_outputs": requested_outputs,
            "projection_report": projection_report,
        },
    }


def _valid_timestamp(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _looks_like_network_endpoint(value):
    candidate = value.strip("[]")
    try:
        ipaddress.ip_address(candidate)
        return True
    except ValueError:
        pass
    if re.fullmatch(r"(?:tcp|udp|http|https)://.+", value, re.I):
        return True
    return re.fullmatch(r"[^/\s]+:[0-9]{1,5}", value) is not None


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
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 64
        and TOKEN.fullmatch(value) is not None
        and not _looks_like_network_endpoint(value)
    )


def _valid_value(value, definition, canonical_manifest):
    expected_kind = definition["value_kind"].upper()
    if not isinstance(value, dict) or value.get("kind") != expected_kind:
        return False
    if value["kind"] == "DECIMAL":
        return (
            set(value) == {"kind", "coefficient", "scale"}
            and isinstance(value["coefficient"], str)
            and DECIMAL.fullmatch(value["coefficient"]) is not None
            and isinstance(value["scale"], int)
            and not isinstance(value["scale"], bool)
            and -18 <= value["scale"] <= 18
        )
    domain = canonical_manifest["value_domains"][definition["value_domain"]]
    if value["kind"] == "ENUM":
        return set(value) == {"kind", "symbol"} and value["symbol"] in domain
    return (
        set(value) == {"kind", "symbols"}
        and isinstance(value["symbols"], list)
        and len(value["symbols"]) <= 64
        and len(value["symbols"]) == len(set(value["symbols"]))
        and all(symbol in domain for symbol in value["symbols"])
    )


def _valid_continuity_decimal(value, *, positive=False):
    if not isinstance(value, dict) or set(value) != {"kind", "coefficient", "scale"}:
        return False
    if value.get("kind") != "DECIMAL" or not isinstance(value.get("coefficient"), str):
        return False
    if (
        DECIMAL.fullmatch(value["coefficient"]) is None
        or not isinstance(value.get("scale"), int)
        or isinstance(value["scale"], bool)
        or not -18 <= value["scale"] <= 18
    ):
        return False
    coefficient = int(value["coefficient"])
    return coefficient > 0 if positive else coefficient >= 0


def _valid_continuity(value):
    if not isinstance(value, dict) or set(value) != {"state", "delta", "modulus", "evidence_ref"}:
        return False
    state = value.get("state")
    delta, modulus, evidence = value.get("delta"), value.get("modulus"), value.get("evidence_ref")
    if state == "BASELINE":
        return delta is None and modulus is None and evidence is None
    if state == "CONTIGUOUS":
        return _valid_continuity_decimal(delta) and modulus is None and evidence is None
    if state == "ROLLOVER":
        return _valid_continuity_decimal(delta) and _valid_continuity_decimal(modulus, positive=True) and isinstance(evidence, str) and SHA256.fullmatch(evidence) is not None
    if state == "RESET":
        return delta is None and modulus is None and isinstance(evidence, str) and SHA256.fullmatch(evidence) is not None
    if state == "DISCONTINUITY":
        return delta is None and modulus is None and (evidence is None or isinstance(evidence, str) and SHA256.fullmatch(evidence) is not None)
    return False


def _validate_case(
    case,
    manifest,
    canonical_manifest,
    source_registry,
    expected_current_source_ref,
):
    errors = set()
    request, response = case["request"], case["response"]
    if set(request) != {"contract_id", "asset_ref"}:
        errors.add("request_fields")
    if request.get("contract_id") not in manifest["contract_negotiation"]["accepted"]:
        errors.add("contract_negotiation")
    if response.get("contract_id") != request.get("contract_id"):
        errors.add("contract_negotiation")
    if set(response) != INTERNAL_RESPONSE_FIELDS:
        errors.add("response_fields")
    if response.get("canonical_contract_id") != canonical_manifest["contract_id"]:
        errors.add("canonical_projection")
    if (
        not isinstance(request.get("asset_ref"), str)
        or ASSET.fullmatch(request["asset_ref"]) is None
        or _looks_like_network_endpoint(request["asset_ref"])
        or request["asset_ref"] != response.get("asset_ref")
    ):
        errors.add("asset")
    if not isinstance(response.get("generation"), str) or POSITIVE_INTEGER.fullmatch(response["generation"]) is None:
        errors.add("time_identity")
    if not isinstance(response.get("evaluated_monotonic_ns"), str) or NONNEGATIVE_INTEGER.fullmatch(response["evaluated_monotonic_ns"]) is None:
        errors.add("time_identity")
    if not _valid_timestamp(response.get("produced_at")):
        errors.add("time_identity")
    if response.get("source_time_state") not in {"UNAVAILABLE", "VALID", "INVALID"}:
        errors.add("source_time_state")
    if (
        not isinstance(response.get("current_source_origin_ref"), str)
        or SHA256.fullmatch(response["current_source_origin_ref"]) is None
    ):
        errors.add("current_source_binding")
    try:
        if any(key in FORBIDDEN for key in _walk_keys(case)):
            errors.add("forbidden_surface")
    except ValidationError:
        errors.add("structural_shape")
        return sorted(errors)
    facts = response.get("facts", [])
    catalog = {fact["id"]: fact for fact in canonical_manifest["facts"]}
    policies = {policy["id"]: policy for policy in canonical_manifest["freshness_policies"]}
    seen = set()
    observed = {}
    origins = set()
    for fact in facts:
        if set(fact) != INTERNAL_FACT_FIELDS:
            errors.add("fact_fields")
            continue
        definition = catalog.get(fact["fact_id"])
        identity = (fact["fact_id"], tuple(sorted(fact["dimensions"].items())))
        if definition is None or fact["fact_id"] not in manifest["catalog_fact_ids"] or identity in seen:
            errors.add("catalog")
        seen.add(identity)
        observed[identity] = fact
        if any(
            isinstance(value, str) and _looks_like_network_endpoint(value)
            for value in fact["dimensions"].values()
        ):
            errors.add("dimension_redaction")
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
        else:
            receipt, fresh_until, retain_until = map(int, temporal)
            evaluated = int(response["evaluated_monotonic_ns"])
            if definition:
                policy = policies[definition["freshness_policy"]]
                if fresh_until != receipt + policy["fresh_seconds"] * 1_000_000_000 or retain_until != receipt + policy["retain_seconds"] * 1_000_000_000:
                    errors.add("freshness_policy")
            if fact["freshness"] == "FRESH" and not receipt <= evaluated < fresh_until:
                errors.add("freshness_evaluation")
            if fact["freshness"] == "STALE" and not fresh_until <= evaluated < retain_until:
                errors.add("freshness_evaluation")
            if fact["freshness"] == "EXPIRED" and evaluated < retain_until:
                errors.add("freshness_evaluation")
        continuity = fact["continuity"]
        if definition and definition["accumulator"]:
            if not _valid_continuity(continuity):
                errors.add("continuity")
        elif continuity is not None:
            errors.add("continuity")
        if not SHA256.fullmatch(fact["origin_ref"]):
            errors.add("provenance")
        origins.add(fact["origin_ref"])
    if not facts:
        errors.add("empty_snapshot")
    if len(facts) > manifest["max_facts_per_snapshot"]:
        errors.add("bounded_snapshot")
    capabilities = response.get("capabilities", [])
    capability_ids = [item.get("id") for item in capabilities if isinstance(item, dict)]
    if any(set(item) != set(manifest["capability_fields"]) or item["outcome"] not in {"SATISFIED", "NOT_SATISFIED"} for item in capabilities) or capability_ids != [item["id"] for item in canonical_manifest["capability_packs"]]:
        errors.add("capability")
    for capability, pack in zip(capabilities, canonical_manifest["capability_packs"]):
        required = {
            (item["fact_id"], tuple(sorted(item["dimensions"].items())))
            for item in pack["required"]
        }
        complete = required <= set(observed)
        supported = complete and not any(observed[key]["availability"] == "UNSUPPORTED" for key in required)
        expected = "SATISFIED" if supported else "NOT_SATISFIED"
        if capability.get("outcome") != expected:
            errors.add("capability_outcome")
    if len(capabilities) > manifest["max_capabilities_per_snapshot"]:
        errors.add("bounded_snapshot")
    provenance = response.get("provenance", [])
    if any(
        set(item) != INTERNAL_PROVENANCE_FIELDS
        or not isinstance(item["source_protocol"], str)
        or SOURCE_TOKEN.fullmatch(item["source_protocol"]) is None
        or not isinstance(item["source_profile_id"], str)
        or SOURCE_TOKEN.fullmatch(item["source_profile_id"]) is None
        or not isinstance(item["source_profile_version"], str)
        or VERSION_TOKEN.fullmatch(item["source_profile_version"]) is None
        or item["source_validity"] != canonical_manifest["provenance"]["source_validity_required"]
        or any(
            not isinstance(item[field], str) or SHA256.fullmatch(item[field]) is None
            for field in (
                "origin_ref",
                "source_registry_ref",
                "source_observation_ref",
                "evidence_ref",
            )
        )
        for item in provenance
    ):
        errors.add("provenance")
    registry_entries = {
        (
            item["source_protocol"],
            item["source_profile_id"],
            item["source_profile_version"],
            item["source_validity"],
        ): item["registry_ref"]
        for item in source_registry["entries"]
    }
    origin_refs = []
    for item in provenance:
        profile_parts = item["source_profile_id"].rsplit("@", 1)
        registry_key = (
            item["source_protocol"],
            item["source_profile_id"],
            item["source_profile_version"],
            item["source_validity"],
        )
        if (
            len(profile_parts) != 2
            or profile_parts[1] != item["source_profile_version"]
            or registry_entries.get(registry_key) != item["source_registry_ref"]
            or item["origin_ref"] != item["source_observation_ref"]
        ):
            errors.add("provenance_binding")
        origin_refs.append(item["origin_ref"])
    if len(origin_refs) != len(set(origin_refs)):
        errors.add("origin_uniqueness")
    if (
        origin_refs.count(response["current_source_origin_ref"]) != 1
        or response["current_source_origin_ref"] != expected_current_source_ref
    ):
        errors.add("current_source_binding")
    if origins != {item["origin_ref"] for item in provenance}:
        errors.add("provenance")
    if not provenance:
        errors.add("empty_snapshot")
    if len(provenance) > manifest["max_provenance_per_snapshot"]:
        errors.add("bounded_snapshot")
    requested_outputs = response.get("requested_outputs", [])
    requested_identities = []
    for item in requested_outputs:
        if (
            not isinstance(item, dict)
            or set(item) != {"source_ref", "requested_output_ref"}
            or any(
                not isinstance(item[field], str)
                or SHA256.fullmatch(item[field]) is None
                for field in ("source_ref", "requested_output_ref")
            )
            or item["source_ref"] not in set(origin_refs)
        ):
            errors.add("projection_accounting")
            continue
        requested_identities.append(
            (item["source_ref"], item["requested_output_ref"])
        )
    if (
        len(requested_identities) != len(set(requested_identities))
        or len(requested_outputs) > manifest["max_requested_outputs_per_snapshot"]
    ):
        errors.add("projection_accounting")
    projection_report = response.get("projection_report", [])
    projection_identities = []
    mapped_identities = set()
    for item in projection_report:
        if (
            not isinstance(item, dict)
            or set(item)
            != {
                "source_ref",
                "requested_output_ref",
                "fact_id",
                "dimensions",
                "outcome",
            }
            or not isinstance(item["source_ref"], str)
            or SHA256.fullmatch(item["source_ref"]) is None
            or not isinstance(item["requested_output_ref"], str)
            or SHA256.fullmatch(item["requested_output_ref"]) is None
            or item["outcome"] not in canonical_manifest["projection_outcomes"]
        ):
            errors.add("projection_accounting")
            continue
        projection_identities.append(
            (item["source_ref"], item["requested_output_ref"])
        )
        if item["outcome"] == "MAPPED":
            identity = (
                item["fact_id"],
                tuple(sorted(item["dimensions"].items()))
                if isinstance(item["dimensions"], dict)
                else (),
            )
            if (
                not isinstance(item["fact_id"], str)
                or not isinstance(item["dimensions"], dict)
                or identity not in observed
                or item["source_ref"] != observed[identity]["origin_ref"]
            ):
                errors.add("projection_accounting")
            mapped_identities.add(identity)
        elif (
            item["fact_id"] is not None
            or item["dimensions"] is not None
            or item["source_ref"] != response["current_source_origin_ref"]
        ):
            errors.add("projection_accounting")
    if (
        len(projection_identities) != len(set(projection_identities))
        or set(projection_identities) != set(requested_identities)
        or mapped_identities != set(observed)
        or len(projection_report) > manifest["max_projection_report_per_snapshot"]
    ):
        errors.add("projection_accounting")
    return sorted(errors)


def _load_source_registry(manifest):
    relative = manifest.get("source_registry_fixture")
    if not isinstance(relative, str):
        raise ValidationError("source_registry_fixture")
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as error:
        raise ValidationError("source_registry_fixture") from error
    return load_json(path, max_depth=manifest["json_admission"]["max_depth"])


def _load_canonical_conformance_fixture(manifest):
    relative = manifest.get("canonical_conformance_fixture")
    if not isinstance(relative, str):
        raise ValidationError("canonical_conformance_fixture")
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as error:
        raise ValidationError("canonical_conformance_fixture") from error
    return load_json(path, max_depth=manifest["json_admission"]["max_depth"])


def _project_canonical_fixture(canonical, manifest):
    if manifest.get("provenance_projection_loss") != {
        "source_shadow_ref": "WITHHELD_SOURCE_SHADOW_REFERENCE"
    }:
        raise ValidationError("canonical_fixture_parity")

    def project_value(value):
        return {key: copy.deepcopy(item) for key, item in value.items() if key != "kind"}

    def project_continuity(continuity):
        if continuity is None:
            return None
        return {
            "state": continuity["state"],
            "delta": None
            if continuity["delta"] is None
            else project_value(continuity["delta"]),
            "modulus": None
            if continuity["modulus"] is None
            else project_value(continuity["modulus"]),
            "evidenceRef": continuity["evidence_ref"],
        }

    facts = []
    for fact in canonical["facts"]:
        temporal = fact["temporal"]
        facts.append(
            {
                "factId": fact["fact_id"],
                "dimensions": [
                    {"key": key, "value": value}
                    for key, value in sorted(fact["dimensions"].items())
                ],
                "value": project_value(fact["value"]),
                "unit": fact["unit"],
                "quality": fact["quality"],
                "availability": fact["availability"],
                "freshness": fact["freshness"],
                "receiptMonotonicNs": str(temporal["receipt_monotonic_ns"]),
                "freshUntilMonotonicNs": str(temporal["fresh_until_monotonic_ns"]),
                "retainUntilMonotonicNs": str(temporal["retain_until_monotonic_ns"]),
                "freshnessPolicy": temporal["freshness_policy"],
                "originRef": fact["origin_ref"],
                "continuity": project_continuity(fact.get("continuity")),
            }
        )

    provenance = []
    for origin in canonical["origins"]:
        provenance.append(
            {
                "originRef": origin["source_observation_ref"],
                "sourceProtocol": origin["source_protocol"],
                "sourceProfileId": origin["source_profile_id"],
                "sourceProfileVersion": origin["source_profile_version"],
                "sourceValidity": origin["source_validity"],
                "sourceRegistryRef": origin["source_registry_ref"],
                "sourceObservationRef": origin["source_observation_ref"],
                "evidenceRef": origin["evidence_ref"],
            }
        )
    return {
        "contractId": manifest["contract_id"],
        "canonicalContractId": canonical["contract_id"],
        "assetRef": canonical["asset_ref"],
        "generation": str(canonical["generation"]),
        "producedAt": canonical["produced_at"],
        "evaluatedMonotonicNs": str(canonical["evaluated_monotonic_ns"]),
        "sourceTimeState": canonical["source_time_state"],
        "currentSourceOriginRef": canonical["source_provenance"][
            "source_observation_ref"
        ],
        "facts": facts,
        "capabilities": copy.deepcopy(canonical["capabilities"]),
        "provenance": provenance,
        "requestedOutputs": [
            {
                "sourceRef": item["source_ref"],
                "requestedOutputRef": item["requested_output_ref"],
            }
            for item in canonical["requested_outputs"]
        ],
        "projectionReport": [
            {
                "sourceRef": item["source_ref"],
                "requestedOutputRef": item["requested_output_ref"],
                "factId": item["fact_id"],
                "dimensions": None
                if item["dimensions"] is None
                else [
                    {"key": key, "value": value}
                    for key, value in sorted(item["dimensions"].items())
                ],
                "outcome": item["outcome"],
            }
            for item in canonical["projection_report"]
        ],
    }


def validate_canonical_fixture_projection(cases, manifest):
    try:
        canonical = _load_canonical_conformance_fixture(manifest)
        expected = _project_canonical_fixture(canonical, manifest)
    except (KeyError, OSError, TypeError, ValidationError) as error:
        raise ValidationError("canonical_fixture_parity") from error
    try:
        actual = cases["positive"]["response"]["body"]["data"][
            "m2mCurrentSnapshot"
        ]
    except (KeyError, TypeError):
        raise ValidationError("canonical_fixture_parity")
    if actual != expected:
        raise ValidationError("canonical_fixture_parity")


def validate_case(case, manifest, canonical_manifest, source_registry=None):
    """Validate the GraphQL HTTP envelope after a mandatory lossless mapping."""
    if not isinstance(case, dict):
        return ["structural_shape"]
    request_envelope, response_envelope = case.get("request"), case.get("response")
    if not isinstance(request_envelope, dict) or not isinstance(response_envelope, dict):
        return ["structural_shape"]
    errors = set()
    if source_registry is None:
        try:
            source_registry = _load_source_registry(manifest)
        except (KeyError, OSError, TypeError, ValidationError):
            return ["provenance_binding"]
    try:
        canonical_fixture = _load_canonical_conformance_fixture(manifest)
        expected_current_source_ref = canonical_fixture["source_provenance"][
            "source_observation_ref"
        ]
    except (KeyError, OSError, TypeError, ValidationError):
        return ["current_source_binding"]
    if source_registry.get("contract") != manifest["source_registry_contract"]:
        errors.add("provenance_binding")
    if (
        set(request_envelope) != {"method", "path", "rawBody", "body"}
        or request_envelope.get("method") != manifest["request_bounds"]["method"]
        or request_envelope.get("path") != manifest["route"]
        or not isinstance(request_envelope.get("body"), dict)
    ):
        errors.add("request_envelope")
    request_body = request_envelope.get("body")
    if not isinstance(request_body, dict):
        errors.add("structural_shape")
        return sorted(errors)
    raw_request_body = request_envelope.get("rawBody")
    if not isinstance(raw_request_body, str):
        errors.add("request_envelope")
        return sorted(errors)
    if len(raw_request_body.encode("utf-8")) > manifest["request_bounds"]["max_body_bytes"]:
        errors.add("request_bytes")
    try:
        decoded_raw_body = loads_json(
            raw_request_body,
            max_depth=manifest["json_admission"]["max_depth"],
        )
    except (TypeError, ValidationError, json.JSONDecodeError):
        errors.add("request_envelope")
        return sorted(errors)
    if decoded_raw_body != request_body:
        errors.add("request_envelope")
    if set(request_body) != {"operationName", "query", "variables"}:
        errors.add("request_envelope")
    if (
        request_body.get("operationName") != manifest["request_bounds"]["operation_name"]
        or request_body.get("query") != manifest["conformance_query"]
    ):
        errors.add("query_shape")
    errors.update(validate_query_document(request_body.get("query"), manifest))
    variables = request_body.get("variables")
    if not isinstance(variables, dict) or set(variables) != {"request"} or not isinstance(variables.get("request"), dict):
        errors.add("structural_shape")
        return sorted(errors)
    request = variables["request"]
    if set(request) != {"contractId", "assetRef"}:
        errors.add("request_fields")
    if (
        set(response_envelope) != {"status", "body"}
        or type(response_envelope.get("status")) is not int
        or response_envelope.get("status") != 200
        or not isinstance(response_envelope.get("body"), dict)
    ):
        errors.add("response_envelope")
    response_body = response_envelope.get("body")
    if not isinstance(response_body, dict) or set(response_body) != {"data"} or not isinstance(response_body.get("data"), dict):
        errors.add("structural_shape")
        return sorted(errors)
    data = response_body["data"]
    if set(data) != {"m2mCurrentSnapshot"} or not isinstance(data.get("m2mCurrentSnapshot"), dict):
        errors.add("structural_shape")
        return sorted(errors)
    response = data["m2mCurrentSnapshot"]
    if set(response) != set(manifest["required_response_fields"]):
        errors.add("response_fields")
    try:
        if any(
            key in FORBIDDEN
            for key in _walk_keys(
                case, max_depth=manifest["json_admission"]["max_depth"]
            )
        ):
            errors.add("forbidden_surface")
    except ValidationError:
        errors.add("structural_shape")
        return sorted(errors)
    if _compact_json_size(request_body) > manifest["request_bounds"]["max_body_bytes"]:
        errors.add("request_bytes")
    if _compact_json_size(response_body) > manifest["request_bounds"]["max_response_bytes"]:
        errors.add("response_bytes")
    for field in (
        "facts",
        "capabilities",
        "provenance",
        "requestedOutputs",
        "projectionReport",
    ):
        items = response.get(field, [])
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            errors.add("structural_shape")
            return sorted(errors)
    for fact in response["facts"]:
        if set(fact) != set(manifest["required_fact_fields"]):
            errors.add("fact_fields")
    for item in response["provenance"]:
        if set(item) != set(manifest["opaque_provenance_fields"]):
            errors.add("provenance_fields")
    for item in response["requestedOutputs"]:
        if set(item) != set(manifest["requested_output_fields"]):
            errors.add("projection_accounting")
    for item in response["projectionReport"]:
        if set(item) != set(manifest["projection_report_fields"]):
            errors.add("projection_accounting")
    try:
        normalized = _normalize_case(case)
        errors.update(
            _validate_case(
                normalized,
                manifest,
                canonical_manifest,
                source_registry,
                expected_current_source_ref,
            )
        )
        return sorted(errors)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        errors.add("structural_shape")
        return sorted(errors)


def validate_error_envelopes(cases, manifest):
    expected_codes = {
        manifest["error_contract"]["contract_incompatible"],
        manifest["error_contract"]["asset_forbidden"],
        manifest["error_contract"]["asset_not_found"],
        manifest["error_contract"]["source_unavailable"],
        manifest["error_contract"]["request_invalid"],
        manifest["error_contract"]["query_rejected"],
        manifest["error_contract"]["request_limit_exceeded"],
    }
    errors = cases.get("errors")
    if (
        not isinstance(errors, list)
        or len(errors) != len(expected_codes)
        or {item.get("code") for item in errors if isinstance(item, dict)}
        != expected_codes
    ):
        raise ValidationError("error_envelope_codes")
    for item in errors:
        if set(item) != {"code", "response"} or not isinstance(
            item["response"], dict
        ):
            raise ValidationError("error_envelope_shape")
        response = item["response"]
        expected_error = {
            "message": manifest["error_contract"]["authenticated_error_message"],
            "path": manifest["error_contract"]["authenticated_error_path"],
            "extensions": {"code": item["code"]},
        }
        if (
            set(response) != {"status", "body"}
            or type(response["status"]) is not int
            or response["status"]
            != manifest["error_contract"]["authenticated_graphql_http_status"]
            or response["body"]
            != {
                "data": manifest["error_contract"]["data_on_error"],
                "errors": [expected_error],
            }
            or _compact_json_size(response["body"])
            > manifest["request_bounds"]["max_response_bytes"]
        ):
            raise ValidationError("error_envelope_shape")


def validate_semantic_rejections(cases, manifest):
    expected = {
        "contract-incompatible-isolated": "contract_incompatible",
        "asset-forbidden-isolated": "asset_forbidden",
        "asset-not-found-isolated": "asset_not_found",
        "source-unavailable-isolated": "source_unavailable",
        "precedence-contract-before-asset": "contract_incompatible",
        "precedence-allowlist-before-existence": "asset_forbidden",
        "precedence-existence-before-source": "asset_not_found",
    }
    items = cases.get("semantic_rejections")
    if (
        not isinstance(items, list)
        or len(items) != len(expected)
        or {
            item.get("id"): (item.get("category"), item.get("code"))
            for item in items
            if isinstance(item, dict)
        }
        != {
            item_id: (category, manifest["error_contract"][category])
            for item_id, category in expected.items()
        }
    ):
        raise ValidationError("semantic_rejection_mapping")
    envelopes = {item["code"]: item["response"] for item in cases["errors"]}
    for item in items:
        if set(item) != {
            "category",
            "code",
            "id",
            "request",
            "serverState",
            "responseCodeRef",
        }:
            raise ValidationError("semantic_rejection_shape")
        request = item["request"]
        state = item["serverState"]
        if (
            not isinstance(request, dict)
            or set(request) != {"contractId", "assetRef"}
            or not isinstance(request["contractId"], str)
            or not isinstance(request["assetRef"], str)
            or ASSET.fullmatch(request["assetRef"]) is None
            or not isinstance(state, dict)
            or set(state)
            != {
                "authenticated",
                "allowedAssets",
                "presentAssets",
                "snapshotAvailableAssets",
            }
            or state["authenticated"] is not True
            or any(
                not isinstance(values, list)
                or len(values) != len(set(values))
                or any(ASSET.fullmatch(value) is None for value in values)
                for values in (
                    state["allowedAssets"],
                    state["presentAssets"],
                    state["snapshotAvailableAssets"],
                )
            )
            or item["responseCodeRef"] != item["code"]
            or item["responseCodeRef"] not in envelopes
        ):
            raise ValidationError("semantic_rejection_shape")
        asset = request["assetRef"]
        if request["contractId"] not in manifest["contract_negotiation"]["accepted"]:
            reached = "contract_incompatible"
        elif asset not in state["allowedAssets"]:
            reached = "asset_forbidden"
        elif asset not in state["presentAssets"]:
            reached = "asset_not_found"
        elif asset not in state["snapshotAvailableAssets"]:
            reached = "source_unavailable"
        else:
            reached = None
        if (
            reached != item["category"]
            or manifest["error_contract"].get(reached) != item["code"]
        ):
            raise ValidationError("semantic_rejection_mapping")
        if item["id"] == "precedence-contract-before-asset" and not (
            asset not in state["allowedAssets"]
            and asset not in state["presentAssets"]
            and asset not in state["snapshotAvailableAssets"]
        ):
            raise ValidationError("semantic_rejection_precedence")
        if item["id"] == "precedence-allowlist-before-existence" and not (
            request["contractId"] in manifest["contract_negotiation"]["accepted"]
            and asset not in state["allowedAssets"]
            and asset not in state["presentAssets"]
            and asset not in state["snapshotAvailableAssets"]
        ):
            raise ValidationError("semantic_rejection_precedence")
        if item["id"] == "precedence-existence-before-source" and not (
            request["contractId"] in manifest["contract_negotiation"]["accepted"]
            and asset in state["allowedAssets"]
            and asset not in state["presentAssets"]
            and asset not in state["snapshotAvailableAssets"]
        ):
            raise ValidationError("semantic_rejection_precedence")


def validate_admission_sequences(cases, manifest):
    model = manifest["admission_model"]
    bounds = manifest["request_bounds"]
    if model != {
        "logical_client_identity": "MTLS_PRINCIPAL_FINGERPRINT",
        "clock": "MONOTONIC_INTEGER_MILLISECONDS",
        "same_timestamp_order": "FIXTURE_EVENT_ORDER",
        "evaluation_order": ["concurrency", "rate"],
        "rejected_request_consumes_rate_token": False,
        "concurrency": {
            "request_is_in_flight_from": "ADMIT",
            "request_is_in_flight_until": "COMPLETE",
            "maximum": bounds["max_concurrency_per_client"],
        },
        "rate": {
            "algorithm": "TOKEN_BUCKET",
            "initial_tokens": bounds["burst_per_client"],
            "capacity": bounds["burst_per_client"],
            "refill_tokens": bounds["requests_per_second_per_client"],
            "refill_interval_ms": 1000,
        },
    }:
        raise ValidationError("admission_model")
    sequences = cases.get("admission_sequences")
    if not isinstance(sequences, dict) or set(sequences) != {
        "concurrency",
        "rate",
        "client_isolation",
    }:
        raise ValidationError("admission_sequence_shape")
    expected_ids = {
        "concurrency": "same-client-overlap-v1",
        "rate": "same-client-token-bucket-v1",
        "client_isolation": "two-principal-isolation-v1",
    }
    for category, sequence in sequences.items():
        if (
            not isinstance(sequence, dict)
            or set(sequence) != {"id", "events"}
            or sequence["id"] != expected_ids[category]
            or not isinstance(sequence["events"], list)
            or not sequence["events"]
        ):
            raise ValidationError("admission_sequence_shape")
        capacity = model["rate"]["capacity"]
        refill = model["rate"]["refill_tokens"]
        interval = model["rate"]["refill_interval_ms"]
        last_event_ms = -1
        clients = {}
        rejected = 0
        for event in sequence["events"]:
            if not isinstance(event, dict) or set(event) not in (
                {"clientRef", "requestId", "atMs", "action", "outcome"},
                {"clientRef", "requestId", "atMs", "action", "outcome", "code"},
            ):
                raise ValidationError("admission_sequence_shape")
            client_ref = event["clientRef"]
            request_id = event["requestId"]
            at_ms = event["atMs"]
            if (
                not isinstance(client_ref, str)
                or not client_ref
                or not isinstance(request_id, str)
                or not request_id
                or type(at_ms) is not int
                or at_ms < last_event_ms
            ):
                raise ValidationError("admission_sequence_shape")
            state = clients.setdefault(
                client_ref,
                {
                    "tokens": model["rate"]["initial_tokens"],
                    "last_refill_ms": 0,
                    "active": set(),
                },
            )
            elapsed_intervals = (at_ms - state["last_refill_ms"]) // interval
            if elapsed_intervals > 0:
                state["tokens"] = min(
                    capacity, state["tokens"] + elapsed_intervals * refill
                )
                state["last_refill_ms"] += elapsed_intervals * interval
            last_event_ms = at_ms
            if event["action"] == "COMPLETE":
                if (
                    event["outcome"] != "COMPLETE"
                    or "code" in event
                    or request_id not in state["active"]
                ):
                    raise ValidationError("admission_sequence_mapping")
                state["active"].remove(request_id)
                continue
            if event["action"] != "START" or request_id in state["active"]:
                raise ValidationError("admission_sequence_mapping")
            should_reject = (
                len(state["active"]) >= model["concurrency"]["maximum"]
                or state["tokens"] < 1
            )
            if should_reject:
                rejected += 1
                if event.get("outcome") != "REJECT" or event.get("code") != manifest[
                    "error_contract"
                ]["request_limit_exceeded"]:
                    raise ValidationError("admission_sequence_mapping")
            else:
                if event.get("outcome") != "ADMIT" or "code" in event:
                    raise ValidationError("admission_sequence_mapping")
                state["active"].add(request_id)
                state["tokens"] -= 1
        if (
            any(state["active"] for state in clients.values())
            or rejected == 0
            or (category == "client_isolation" and len(clients) != 2)
            or (category != "client_isolation" and len(clients) != 1)
        ):
            raise ValidationError("admission_sequence_mapping")


def validate_request_rejections(cases, manifest):
    expected = manifest["request_rejection_codes"]
    items = cases.get("request_rejections")
    if (
        not isinstance(items, list)
        or len(items) != len(expected)
        or {
            item.get("category"): item.get("code")
            for item in items
            if isinstance(item, dict)
        }
        != expected
    ):
        raise ValidationError("request_rejection_mapping")
    envelopes = {item["code"]: item["response"] for item in cases["errors"]}
    sequences = cases["admission_sequences"]
    for item in items:
        if set(item) != {"category", "code", "stimulus", "responseCodeRef"}:
            raise ValidationError("request_rejection_shape")
        category = item["category"]
        stimulus = item["stimulus"]
        if (
            not isinstance(stimulus, dict)
            or item["responseCodeRef"] != item["code"]
            or item["responseCodeRef"] not in envelopes
        ):
            raise ValidationError("request_rejection_shape")
        if category in {"malformed_json", "duplicate_json_key"}:
            if set(stimulus) != {"rawBody"} or not isinstance(stimulus["rawBody"], str):
                raise ValidationError("request_rejection_shape")
            try:
                loads_json(
                    stimulus["rawBody"],
                    max_depth=manifest["json_admission"]["max_depth"],
                )
            except json.JSONDecodeError:
                reached = "malformed_json"
            except ValidationError:
                reached = "duplicate_json_key"
            else:
                reached = None
        elif category == "request_envelope":
            reached = (
                category
                if set(stimulus) == {"method"}
                and stimulus["method"] != manifest["request_bounds"]["method"]
                else None
            )
        elif category == "request_body_bytes":
            reached = (
                category
                if set(stimulus) == {"prefixPaddingBytes"}
                and type(stimulus["prefixPaddingBytes"]) is int
                and stimulus["prefixPaddingBytes"]
                + len(cases["positive"]["request"]["rawBody"].encode("utf-8"))
                > manifest["request_bounds"]["max_body_bytes"]
                else None
            )
        elif category in {"concurrency", "rate"}:
            reached = (
                category
                if set(stimulus) == {"sequenceRef"}
                and stimulus["sequenceRef"] == sequences[category]["id"]
                else None
            )
        else:
            mutation = stimulus.get("queryMutation") if set(stimulus) == {"queryMutation"} else None
            query = manifest["conformance_query"]
            if mutation == "alias_root":
                query = query.replace(
                    "m2mCurrentSnapshot(request:",
                    "snapshot: m2mCurrentSnapshot(request:",
                    1,
                )
                reached = category if "query_alias" in validate_query_document(query, manifest) else None
            elif mutation == "introspection":
                query = query.replace("contractId", "__typename contractId", 1)
                reached = category if "query_introspection" in validate_query_document(query, manifest) else None
            elif mutation == "depth_9":
                query = (
                    "query M2MCurrentSnapshot($request: M2MCurrentSnapshotRequest!) "
                    "{ m2mCurrentSnapshot(request: $request) { a { b { c { d { e { f { g { h { i } } } } } } } } } }"
                )
                reached = category if "query_depth" in validate_query_document(query, manifest) else None
            elif mutation == "selected_fields_257":
                query = query.replace("contractId", " ".join(["contractId"] * 257), 1)
                reached = category if "query_fields" in validate_query_document(query, manifest) else None
            else:
                reached = None
        if reached != category:
            raise ValidationError("request_rejection_mapping")


def validate(manifest_path: Path, canonical_manifest_path: Path, cases_path: Path):
    manifest = load_json(manifest_path)
    max_depth = manifest["json_admission"]["max_depth"]
    canonical = load_json(canonical_manifest_path, max_depth=max_depth)
    cases = load_json(cases_path, max_depth=max_depth)
    if manifest["source_contract"] != canonical["contract_id"] or manifest["catalog_fact_ids"] != [fact["id"] for fact in canonical["facts"]]:
        raise ValidationError("manifest_source_lock")
    validate_canonical_fixture_projection(cases, manifest)
    errors = validate_case(cases["positive"], manifest, canonical)
    if errors:
        raise ValidationError("positive: " + ", ".join(errors))
    try:
        capability_case = copy.deepcopy(cases["positive"])
        capability_payload = copy.deepcopy(cases["capability_satisfied_projection"])
        capability_case["response"]["body"]["data"][
            "m2mCurrentSnapshot"
        ] = capability_payload
        capability_case["request"]["body"]["variables"]["request"][
            "assetRef"
        ] = capability_payload["assetRef"]
        capability_case["request"]["rawBody"] = json.dumps(
            capability_case["request"]["body"],
            ensure_ascii=True,
            separators=(",", ":"),
        )
    except (KeyError, TypeError):
        raise ValidationError("capability_satisfied_projection")
    capability_errors = validate_case(capability_case, manifest, canonical)
    if capability_errors:
        raise ValidationError(
            "capability_satisfied_projection: " + ", ".join(capability_errors)
        )
    for negative in cases["negative"]:
        candidate = _set_path(cases["positive"], negative["path"], negative["value"])
        if negative["error"] not in validate_case(candidate, manifest, canonical):
            raise ValidationError("negative: " + negative["id"])
    validate_error_envelopes(cases, manifest)
    validate_semantic_rejections(cases, manifest)
    validate_admission_sequences(cases, manifest)
    validate_request_rejections(cases, manifest)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--canonical-manifest", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    args = parser.parse_args()
    try:
        validate(args.manifest, args.canonical_manifest, args.cases)
    except (
        AttributeError,
        IndexError,
        KeyError,
        OSError,
        RecursionError,
        TypeError,
        ValueError,
        ValidationError,
        json.JSONDecodeError,
    ) as error:
        print(f"public_graphql_m2m_v1_invalid: {error}", file=sys.stderr)
        return 1
    print("public_graphql_m2m_v1_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
