#!/usr/bin/env python3
"""Validate the bounded public qualified-identity policy and its references."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


class CheckError(Exception):
    """Raised when the canonical policy or a required public reference is invalid."""


POLICY_PATH = pathlib.Path("architecture/regulator-qualified-identity-policy.json")
POLICY_VERSION = 1
TRIPLE_MEMBERS = ["Manufacturer", "DeviceID", "SerialNumber"]
SENTINEL_SERIALS = ["0", "0x00000000", "0xFFFFFFFF", "0x7FFFFFFF"]
SENTINEL_RECOGNITION = {
    "scope": "named_hexadecimal_sentinels_only",
    "case": "insensitive",
    "prefix": "optional_single_0x",
    "leading_zeros": "ignore",
    "ordinary_serials": "never_parse_or_rewrite",
}
CONSUMER_WITNESS_REQUIRED_FIELDS = [
    "address",
    "identity_authority",
    "observation_provenance",
    "current",
    "immutable",
    "registry_observation_generation",
    "registry_proof_generation",
]
CONSUMER_WITNESS_ALLOWED_VALUES = {
    "address": ["exact_address"],
    "identity_authority": ["complete_normalized_triple_authority"],
    "observation_provenance": ["direct_observation"],
    "current": [True],
    "immutable": [True],
    "registry_observation_generation": ["positive_integer"],
    "registry_proof_generation": ["positive_integer"],
}
CONSUMER_WITNESS_PRODUCTION = {
    "producer": "registry",
    "source": "direct_complete_normalized_triple_observation",
    "bound_to": [
        "exact_address",
        "complete_normalized_triple_authority",
        "registry_observation_generation",
        "registry_proof_generation",
    ],
    "result": "immutable",
}
CONSUMER_WITNESS_CURRENTNESS = {
    "consumer_boundary": "atomic_registry_lookup_validation_use",
    "registry_state_scope": "exact_address_and_complete_normalized_triple_authority",
    "supplied_must_equal_current": [
        "address",
        "identity_authority",
        "registry_observation_generation",
        "registry_proof_generation",
    ],
    "positive_generations_or_cached_current_flag": "insufficient",
    "unavailable_until": "fresh_direct_complete_normalized_triple_observation",
}
CONSUMER_WITNESS_NON_WITNESS_INPUTS = [
    "observable_nonempty_fields",
    "identity_confirmed",
    "topology_alias",
    "topology_propagated_confirmation",
    "static_seed",
    "passive_observed",
    "caller_assertion",
    "last_known_good",
    "directed_07_04_reply",
]
TRIPLE_AUTHORITY_FIELDS = {"Manufacturer", "DeviceID", "SerialNumber"}
WITNESS_INSTANCE_FIELDS = set(CONSUMER_WITNESS_REQUIRED_FIELDS)
CURRENT_REGISTRY_STATE_FIELDS = {
    "availability",
    "address",
    "identity_authority",
    "registry_observation_generation",
    "registry_proof_generation",
}
WITNESS_FIXTURE_FIELDS = {"name", "witness", "current_registry_state", "current"}
CONSUMER_WITNESS_FIXTURE_NAMES = {
    "current_exact_address",
    "cached_after_replacement",
    "cached_after_retirement",
    "cached_after_supplied_triple_conflict",
    "observation_generation_mismatch",
    "proof_generation_mismatch",
    "authority_substitution",
    "address_substitution",
}

REQUIRED_DOCUMENT_REFERENCES = {
    pathlib.Path("architecture/regulator-identity-enrichment.md"): "[qualified-identity policy](regulator-qualified-identity-policy.json)",
    pathlib.Path("architecture/atr/01-address-table-model.md"): "[qualified-identity policy](../regulator-qualified-identity-policy.json)",
    pathlib.Path("architecture/atr/03-ack-nack-insertion-rules.md"): "[qualified-identity policy](../regulator-qualified-identity-policy.json)",
    pathlib.Path("architecture/atr/04-sn-merge-gate.md"): "[qualified-identity policy](../regulator-qualified-identity-policy.json)",
    pathlib.Path("architecture/overview.md"): "[qualified-identity policy](./regulator-qualified-identity-policy.json)",
    pathlib.Path("api/graphql.md"): "[qualified-identity policy](../architecture/regulator-qualified-identity-policy.json)",
}
REQUIRED_ATR_SYNCHRONIZATION = {
    pathlib.Path("architecture/atr/01-address-table-model.md"): "same_source_positive_ack_plus_current_exact_address_witness",
    pathlib.Path("architecture/atr/03-ack-nack-insertion-rules.md"): "same_source_positive_ack_plus_current_exact_address_witness",
}


def require_keys(value: object, context: str, keys: set[str]) -> dict[str, object]:
    if not isinstance(value, dict):
        raise CheckError(f"{context}: expected object")
    actual = set(value)
    if actual != keys:
        missing = sorted(keys - actual)
        unknown = sorted(actual - keys)
        raise CheckError(f"{context}: expected exact fields; missing={missing}, unknown={unknown}")
    return value


def require_value(value: object, expected: object, context: str) -> None:
    if value != expected or type(value) is not type(expected):
        raise CheckError(f"{context}: expected {expected!r}, got {value!r}")


def require_complete_authority(value: object, context: str) -> dict[str, object]:
    authority = require_keys(value, context, TRIPLE_AUTHORITY_FIELDS)
    for member in TRIPLE_MEMBERS:
        if not isinstance(authority[member], str) or not authority[member]:
            raise CheckError(f"{context}.{member}: expected non-empty normalized member")
    return authority


def require_positive_integer(value: object, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise CheckError(f"{context}: expected positive integer")
    return value


def consumer_witness_is_current(witness_value: object, current_state_value: object) -> bool:
    """Evaluate the closed witness/current-registry equality relation."""
    witness = require_keys(witness_value, "consumer witness", WITNESS_INSTANCE_FIELDS)
    current_state = require_keys(current_state_value, "current registry state", CURRENT_REGISTRY_STATE_FIELDS)
    require_complete_authority(witness["identity_authority"], "consumer witness.identity_authority")
    require_complete_authority(current_state["identity_authority"], "current registry state.identity_authority")
    require_positive_integer(witness["registry_observation_generation"], "consumer witness.registry_observation_generation")
    require_positive_integer(witness["registry_proof_generation"], "consumer witness.registry_proof_generation")
    require_positive_integer(current_state["registry_observation_generation"], "current registry state.registry_observation_generation")
    require_positive_integer(current_state["registry_proof_generation"], "current registry state.registry_proof_generation")
    return (
        witness["observation_provenance"] == "direct_observation"
        and witness["current"] is True
        and witness["immutable"] is True
        and current_state["availability"] == "available"
        and witness["address"] == current_state["address"]
        and witness["identity_authority"] == current_state["identity_authority"]
        and witness["registry_observation_generation"] == current_state["registry_observation_generation"]
        and witness["registry_proof_generation"] == current_state["registry_proof_generation"]
    )


def validate_consumer_witness_fixtures(value: object, context: str) -> None:
    if not isinstance(value, list) or not value:
        raise CheckError(f"{context}: expected non-empty list")
    names: set[str] = set()
    for index, fixture_value in enumerate(value):
        fixture = require_keys(fixture_value, f"{context}[{index}]", WITNESS_FIXTURE_FIELDS)
        name = fixture["name"]
        if not isinstance(name, str) or not name or name in names:
            raise CheckError(f"{context}[{index}].name: expected unique non-empty string")
        names.add(name)
        if type(fixture["current"]) is not bool:
            raise CheckError(f"{context}[{index}].current: expected boolean")
        actual = consumer_witness_is_current(fixture["witness"], fixture["current_registry_state"])
        require_value(actual, fixture["current"], f"{context}[{index}].current")
    if names != CONSUMER_WITNESS_FIXTURE_NAMES:
        missing = sorted(CONSUMER_WITNESS_FIXTURE_NAMES - names)
        unknown = sorted(names - CONSUMER_WITNESS_FIXTURE_NAMES)
        raise CheckError(f"{context}: expected exact fixture names; missing={missing}, unknown={unknown}")


def validate_policy(policy: object, path: pathlib.Path) -> None:
    root = require_keys(
        policy,
        str(path),
        {
            "schema_version",
            "scope",
            "identity",
            "normalization",
            "topology",
            "confirmation",
            "consumer_witness",
            "enrichment",
            "provenance",
        },
    )
    require_value(root["schema_version"], POLICY_VERSION, f"{path}.schema_version")
    require_value(root["scope"], "cross_address_qualified_identity", f"{path}.scope")

    identity = require_keys(
        root["identity"],
        f"{path}.identity",
        {
            "members",
            "match",
            "empty_or_partial",
            "named_sentinel_serials",
            "sentinel_recognition",
            "sentinel_serials",
            "non_qualifying_signals",
        },
    )
    require_value(identity["members"], TRIPLE_MEMBERS, f"{path}.identity.members")
    require_value(identity["match"], "exact_normalized_triple", f"{path}.identity.match")
    require_value(identity["empty_or_partial"], "not_qualified", f"{path}.identity.empty_or_partial")
    require_value(identity["named_sentinel_serials"], SENTINEL_SERIALS, f"{path}.identity.named_sentinel_serials")
    require_value(identity["sentinel_recognition"], SENTINEL_RECOGNITION, f"{path}.identity.sentinel_recognition")
    require_value(identity["sentinel_serials"], "not_qualified", f"{path}.identity.sentinel_serials")
    require_value(
        identity["non_qualifying_signals"],
        ["serial", "mac", "model", "topology", "address_cooccurrence"],
        f"{path}.identity.non_qualifying_signals",
    )

    normalization = require_keys(
        root["normalization"], f"{path}.normalization", {"fixed_width_device_id_decoder", "registry"}
    )
    require_value(
        normalization["fixed_width_device_id_decoder"],
        ["remove_terminal_nul", "remove_terminal_ascii_space"],
        f"{path}.normalization.fixed_width_device_id_decoder",
    )
    registry = require_keys(
        normalization["registry"],
        f"{path}.normalization.registry",
        {"members", "outer_unicode_whitespace", "case", "internal_whitespace", "internal_punctuation", "deviceid_vr_71_vs_vr71"},
    )
    require_value(registry["members"], TRIPLE_MEMBERS, f"{path}.normalization.registry.members")
    require_value(registry["outer_unicode_whitespace"], "trim", f"{path}.normalization.registry.outer_unicode_whitespace")
    require_value(registry["case"], "uppercase", f"{path}.normalization.registry.case")
    require_value(registry["internal_whitespace"], "preserve", f"{path}.normalization.registry.internal_whitespace")
    require_value(registry["internal_punctuation"], "preserve", f"{path}.normalization.registry.internal_punctuation")
    require_value(registry["deviceid_vr_71_vs_vr71"], "distinct", f"{path}.normalization.registry.deviceid_vr_71_vs_vr71")

    topology = require_keys(root["topology"], f"{path}.topology", {"allowed_grouping_evidence", "cross_address_identity_proof"})
    require_value(topology["allowed_grouping_evidence"], ["source_target", "canonical_companion"], f"{path}.topology.allowed_grouping_evidence")
    require_value(topology["cross_address_identity_proof"], False, f"{path}.topology.cross_address_identity_proof")

    confirmation = require_keys(root["confirmation"], f"{path}.confirmation", {"session", "per_face", "active_confirmation"})
    require_value(confirmation["session"], "current", f"{path}.confirmation.session")
    require_value(confirmation["per_face"], True, f"{path}.confirmation.per_face")
    require_value(
        confirmation["active_confirmation"],
        "allowed_without_cross_address_qualification",
        f"{path}.confirmation.active_confirmation",
    )

    consumer_witness = require_keys(
        root["consumer_witness"],
        f"{path}.consumer_witness",
        {
            "kind",
            "required_fields",
            "allowed_values",
            "production",
            "currentness",
            "stale_on",
            "non_witness_inputs",
            "companion_corroboration",
            "validation_fixtures",
        },
    )
    require_value(
        consumer_witness["kind"],
        "qualified_identity_consumer_witness_v1",
        f"{path}.consumer_witness.kind",
    )
    require_value(
        consumer_witness["required_fields"],
        CONSUMER_WITNESS_REQUIRED_FIELDS,
        f"{path}.consumer_witness.required_fields",
    )
    require_value(
        consumer_witness["allowed_values"],
        CONSUMER_WITNESS_ALLOWED_VALUES,
        f"{path}.consumer_witness.allowed_values",
    )
    require_value(
        consumer_witness["production"],
        CONSUMER_WITNESS_PRODUCTION,
        f"{path}.consumer_witness.production",
    )
    require_value(
        consumer_witness["currentness"],
        CONSUMER_WITNESS_CURRENTNESS,
        f"{path}.consumer_witness.currentness",
    )
    require_value(
        consumer_witness["stale_on"],
        ["replacement", "retirement", "conflict"],
        f"{path}.consumer_witness.stale_on",
    )
    require_value(
        consumer_witness["non_witness_inputs"],
        CONSUMER_WITNESS_NON_WITNESS_INPUTS,
        f"{path}.consumer_witness.non_witness_inputs",
    )
    require_value(
        consumer_witness["companion_corroboration"],
        "same_source_positive_ack_plus_current_exact_address_witness",
        f"{path}.consumer_witness.companion_corroboration",
    )
    validate_consumer_witness_fixtures(
        consumer_witness["validation_fixtures"], f"{path}.consumer_witness.validation_fixtures"
    )

    enrichment = require_keys(root["enrichment"], f"{path}.enrichment", {"scope", "last_known_good", "cross_address_identity"})
    require_value(enrichment["scope"], "same_address", f"{path}.enrichment.scope")
    require_value(enrichment["last_known_good"], "retain", f"{path}.enrichment.last_known_good")
    require_value(enrichment["cross_address_identity"], "not_qualified", f"{path}.enrichment.cross_address_identity")

    provenance = require_keys(root["provenance"], f"{path}.provenance", {"per_face", "static_seed", "passive_observed"})
    require_value(provenance["per_face"], "retain", f"{path}.provenance.per_face")
    require_value(provenance["static_seed"], "preserve", f"{path}.provenance.static_seed")
    require_value(provenance["passive_observed"], "preserve", f"{path}.provenance.passive_observed")


def validate_documents(root: pathlib.Path) -> None:
    policy_path = root / POLICY_PATH
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CheckError(f"{policy_path}: invalid JSON: {exc.msg}") from exc
    validate_policy(policy, policy_path)

    for relative, reference in REQUIRED_DOCUMENT_REFERENCES.items():
        path = root / relative
        if reference not in path.read_text(encoding="utf-8"):
            raise CheckError(f"{path}: missing required canonical policy reference: {reference!r}")

    for relative, policy_value in REQUIRED_ATR_SYNCHRONIZATION.items():
        path = root / relative
        marker = f"<!-- qualified-identity-policy: {policy_value} -->"
        if marker not in path.read_text(encoding="utf-8"):
            raise CheckError(f"{path}: missing required qualified-identity synchronization marker: {marker!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        validate_documents(args.root)
    except (CheckError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print("Qualified identity policy and public references passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
