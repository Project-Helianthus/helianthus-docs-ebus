#!/usr/bin/env python3
import argparse
import ipaddress
import json
import re
import subprocess
import sys
from pathlib import Path


class ValidationError(ValueError):
    pass


def _pairs_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path):
    try:
        with Path(path).open(encoding="utf-8") as stream:
            return json.load(
                stream,
                object_pairs_hook=_pairs_no_duplicates,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValidationError(f"non-finite JSON number: {value}")
                ),
            )
    except (json.JSONDecodeError, OSError) as error:
        raise ValidationError(str(error)) from error


def fact_key(fact):
    return fact["fact_id"], tuple(sorted(fact["dimensions"].items()))


def source_key(source):
    return (
        source["source_protocol"],
        source["source_profile_id"],
        source["source_profile_version"],
        source["source_validity"],
    )


def _looks_like_network_endpoint(value):
    candidate = value.strip("[]")
    try:
        ipaddress.ip_address(candidate)
        return True
    except ValueError:
        pass
    if re.fullmatch(r"(?:tcp|udp|http|https)://.+", value, re.I):
        return True
    return bool(re.fullmatch(r"[^/\s]+:[0-9]{1,5}", value))


def validate_schema(document_path, schema_path):
    result = subprocess.run(
        ["jv", str(schema_path), str(document_path)],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode:
        raise ValidationError("schema: " + (result.stdout + result.stderr).strip())


def validate_semantics(document, manifest, source_registry):
    errors = set()
    catalog = {fact["id"]: fact for fact in manifest["facts"]}
    policies = {policy["id"]: policy for policy in manifest["freshness_policies"]}
    domains = manifest["value_domains"]
    observed = {}

    if _looks_like_network_endpoint(document["asset_ref"]):
        errors.add("asset_ref_redaction")
    registry_entries = {}
    registry_refs = set()
    for entry in source_registry["entries"]:
        key = source_key(entry)
        if key in registry_entries or entry["registry_ref"] in registry_refs:
            errors.add("source_registry_uniqueness")
        registry_entries[key] = entry["registry_ref"]
        registry_refs.add(entry["registry_ref"])

    def validate_provenance(provenance):
        if provenance["source_validity"] != "terminal_verified":
            errors.add("source_admission")
        if any(
            _looks_like_network_endpoint(value)
            for value in provenance.values()
            if isinstance(value, str)
        ):
            errors.add("provenance_redaction")
        expected_version = provenance["source_profile_id"].rsplit("@", 1)
        if (
            len(expected_version) != 2
            or expected_version[1] != provenance["source_profile_version"]
        ):
            errors.add("provenance_binding")
        expected_registry_ref = registry_entries.get(source_key(provenance))
        if expected_registry_ref != provenance["source_registry_ref"]:
            errors.add("provenance_binding")

    provenance = document["source_provenance"]
    validate_provenance(provenance)
    origins = {}
    for origin in document["origins"]:
        validate_provenance(origin)
        origin_ref = origin["source_observation_ref"]
        if origin_ref in origins:
            errors.add("origin_uniqueness")
        origins[origin_ref] = origin
    root_origin = origins.get(provenance["source_observation_ref"])
    if root_origin != provenance:
        errors.add("root_origin_binding")

    for fact in document["facts"]:
        definition = catalog.get(fact["fact_id"])
        if definition is None:
            errors.add("catalog_closure")
            continue
        key = fact_key(fact)
        if key in observed:
            errors.add("fact_identity_uniqueness")
        observed[key] = fact
        if fact["origin_ref"] not in origins:
            errors.add("fact_origin_binding")

        if set(fact["dimensions"]) != set(definition["dimensions"]):
            errors.add("dimension_domain")
        for name, value in fact["dimensions"].items():
            domain = manifest["dimensions"][name]
            if isinstance(domain, list) and value not in domain:
                errors.add("dimension_domain")
            if isinstance(domain, dict):
                if len(value) > domain["max_length"]:
                    errors.add("dimension_domain")
                if re.fullmatch(domain["pattern"], value) is None:
                    errors.add("dimension_domain")
        if fact["unit"] != definition["unit"]:
            errors.add("catalog_closure")
        if fact["value"]["kind"] != definition["value_kind"]:
            errors.add("catalog_closure")
        domain_id = definition.get("value_domain")
        if domain_id:
            symbols = (
                [fact["value"]["symbol"]]
                if fact["value"]["kind"] == "enum"
                else fact["value"]["symbols"]
            )
            if not set(symbols) <= set(domains[domain_id]):
                errors.add("value_domain")

        temporal = fact["temporal"]
        policy = policies[definition["freshness_policy"]]
        if temporal["freshness_policy"] != policy["id"]:
            errors.add("freshness_policy")
        receipt = temporal["receipt_monotonic_ns"]
        expected_fresh = receipt + policy["fresh_seconds"] * 1_000_000_000
        expected_retain = receipt + policy["retain_seconds"] * 1_000_000_000
        if temporal["fresh_until_monotonic_ns"] != expected_fresh:
            errors.add("freshness_policy")
        if temporal["retain_until_monotonic_ns"] != expected_retain:
            errors.add("freshness_policy")
        evaluated = document["evaluated_monotonic_ns"]
        if fact["freshness"] == "FRESH" and not (
            receipt <= evaluated < temporal["fresh_until_monotonic_ns"]
        ):
            errors.add("freshness_evaluation")
        if fact["freshness"] == "STALE" and not (
            temporal["fresh_until_monotonic_ns"]
            <= evaluated
            < temporal["retain_until_monotonic_ns"]
        ):
            errors.add("freshness_evaluation")
        if (
            fact["freshness"] == "EXPIRED"
            and evaluated < temporal["retain_until_monotonic_ns"]
        ):
            errors.add("freshness_evaluation")
        if definition["accumulator"] != ("continuity" in fact):
            errors.add("continuity_evidence")
        state_pair = f'{fact["availability"]}/{fact["freshness"]}'
        if state_pair not in manifest["allowed_availability_freshness_pairs"]:
            errors.add("lifecycle_state_pair")

    packs = {pack["id"]: pack for pack in manifest["capability_packs"]}
    capability_ids = set()
    for capability in document["capabilities"]:
        if capability["id"] in capability_ids:
            errors.add("capability_uniqueness")
        capability_ids.add(capability["id"])
        required = {
            (item["fact_id"], tuple(sorted(item["dimensions"].items())))
            for item in packs[capability["id"]]["required"]
        }
        complete = required <= set(observed)
        supported = complete and not any(
            observed[key]["availability"] == "UNSUPPORTED" for key in required
        )
        expected_outcome = "SATISFIED" if supported else "NOT_SATISFIED"
        if capability["outcome"] != expected_outcome:
            errors.add("capability_outcome")
        if capability["outcome"] == "SATISFIED" and not complete:
            errors.add("capability_completeness")
            continue
        if capability["outcome"] == "SATISFIED" and not supported:
            errors.add("capability_support_state")
    if capability_ids != set(packs):
        errors.add("capability_inventory")

    projection_ids = set()
    for projection in document["projection_report"]:
        projection_id = (
            projection["source_ref"],
            projection["requested_output_ref"],
        )
        if projection_id in projection_ids:
            errors.add("projection_identity")
        projection_ids.add(projection_id)
        outcome = projection["outcome"]
        projected_fact = projection["fact_id"]
        if outcome == "MAPPED":
            projected_key = (
                projected_fact,
                tuple(sorted(projection["dimensions"].items())),
            )
            if projected_fact is None or projected_key not in observed:
                errors.add("projection_binding")
            elif projection["source_ref"] != observed[projected_key]["origin_ref"]:
                errors.add("projection_source_binding")
        elif projected_fact is not None or projection["dimensions"] is not None:
            errors.add("projection_binding")
        elif projection["source_ref"] != provenance["source_observation_ref"]:
            errors.add("projection_source_binding")

    return sorted(errors)


def validate(
    document_path,
    manifest_path,
    schema_path,
    source_registry_path,
    source_registry_schema_path,
):
    validate_schema(document_path, schema_path)
    validate_schema(source_registry_path, source_registry_schema_path)
    document = load_json(document_path)
    manifest = load_json(manifest_path)
    source_registry = load_json(source_registry_path)
    errors = validate_semantics(document, manifest, source_registry)
    if errors:
        raise ValidationError("semantic: " + ", ".join(errors))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--document", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--source-registry", required=True, type=Path)
    parser.add_argument("--source-registry-schema", required=True, type=Path)
    args = parser.parse_args()
    try:
        validate(
            args.document,
            args.manifest,
            args.schema,
            args.source_registry,
            args.source_registry_schema,
        )
    except ValidationError as error:
        print(f"canonical_pv_v1_invalid: {error}", file=sys.stderr)
        return 1
    print("canonical_pv_v1_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
