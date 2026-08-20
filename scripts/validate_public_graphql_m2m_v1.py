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

DECIMAL = re.compile(r"-?(0|[1-9][0-9]*)$")
NONNEGATIVE_INTEGER = re.compile(r"0|[1-9][0-9]*$")
POSITIVE_INTEGER = re.compile(r"[1-9][0-9]*$")
SHA256 = re.compile(r"sha256:[0-9a-f]{64}$")
TOKEN = re.compile(r"[A-Za-z0-9._:-]+$")
SOURCE_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9._@-]*$")
VERSION_TOKEN = re.compile(r"[0-9][0-9A-Za-z._-]*$")
ASSET = re.compile(r"pv-asset-[A-Za-z0-9_-]{1,96}$")
ROOT = Path(__file__).resolve().parents[1]
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
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    text = path.read_text(encoding="utf-8")
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


def _validate_case(case, manifest, canonical_manifest, source_registry):
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
    if origin_refs.count(response["current_source_origin_ref"]) != 1:
        errors.add("current_source_binding")
    if origins != {item["origin_ref"] for item in provenance}:
        errors.add("provenance")
    if not provenance:
        errors.add("empty_snapshot")
    if len(provenance) > manifest["max_provenance_per_snapshot"]:
        errors.add("bounded_snapshot")
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
    if source_registry.get("contract") != manifest["source_registry_contract"]:
        errors.add("provenance_binding")
    if (
        set(request_envelope) != {"method", "path", "body"}
        or request_envelope.get("method") != manifest["request_bounds"]["method"]
        or request_envelope.get("path") != manifest["route"]
        or not isinstance(request_envelope.get("body"), dict)
    ):
        errors.add("request_envelope")
    request_body = request_envelope.get("body")
    if not isinstance(request_body, dict):
        errors.add("structural_shape")
        return sorted(errors)
    if set(request_body) != {"operationName", "query", "variables"}:
        errors.add("request_envelope")
    if (
        request_body.get("operationName") != manifest["request_bounds"]["operation_name"]
        or request_body.get("query") != manifest["conformance_query"]
    ):
        errors.add("query_shape")
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
    for field in ("facts", "capabilities", "provenance"):
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
    try:
        normalized = _normalize_case(case)
        errors.update(
            _validate_case(normalized, manifest, canonical_manifest, source_registry)
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
            "path": ["m2mCurrentSnapshot"],
            "extensions": {"code": item["code"]},
        }
        if (
            set(response) != {"status", "body"}
            or type(response["status"]) is not int
            or response["status"]
            != manifest["error_contract"]["authenticated_graphql_http_status"]
            or response["body"] != {"data": None, "errors": [expected_error]}
            or _compact_json_size(response["body"])
            > manifest["request_bounds"]["max_response_bytes"]
        ):
            raise ValidationError("error_envelope_shape")


def validate(manifest_path: Path, canonical_manifest_path: Path, cases_path: Path):
    manifest = load_json(manifest_path)
    max_depth = manifest["json_admission"]["max_depth"]
    canonical = load_json(canonical_manifest_path, max_depth=max_depth)
    cases = load_json(cases_path, max_depth=max_depth)
    if manifest["source_contract"] != canonical["contract_id"] or manifest["catalog_fact_ids"] != [fact["id"] for fact in canonical["facts"]]:
        raise ValidationError("manifest_source_lock")
    errors = validate_case(cases["positive"], manifest, canonical)
    if errors:
        raise ValidationError("positive: " + ", ".join(errors))
    for negative in cases["negative"]:
        candidate = _set_path(cases["positive"], negative["path"], negative["value"])
        if negative["error"] not in validate_case(candidate, manifest, canonical):
            raise ValidationError("negative: " + negative["id"])
    validate_error_envelopes(cases, manifest)


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
