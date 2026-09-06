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
HISTORICAL_POLICY_VERSION = 1
CURRENT_POLICY_VERSION = 2
V1_POLICY_FIELDS = {
    "schema_version",
    "scope",
    "identity",
    "normalization",
    "topology",
    "confirmation",
    "enrichment",
    "provenance",
}
V2_POLICY_FIELDS = V1_POLICY_FIELDS | {"instance", "consumer_witness"}
TRIPLE_MEMBERS = ["Manufacturer", "DeviceID", "SerialNumber"]
SENTINEL_SERIALS = ["0", "0x00000000", "0xFFFFFFFF", "0x7FFFFFFF"]
SENTINEL_RECOGNITION = {
    "scope": "named_hexadecimal_sentinels_only",
    "case": "insensitive",
    "prefix": "optional_single_0x",
    "leading_zeros": "ignore",
    "ordinary_serials": "never_parse_or_rewrite",
}
CONSUMER_WITNESS_INSTANCE = {
    "address": {
        "representation": "0xNN_uppercase_hexadecimal_byte",
        "domain": ["AddressClassMaster", "AddressClassSlave"],
        "canonical_source": "architecture/ebus_standard/12-address-table.md#ebus-256-byte-address-taxonomy-v1",
    }
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
CURRENT_REGISTRY_STATE_REQUIRED_FIELDS = [
    "availability",
    "address",
    "identity_authority",
    "registry_observation_generation",
    "registry_proof_generation",
]
CURRENT_REGISTRY_STATE_ALLOWED_VALUES = {
    "availability": ["available", "retired", "conflict"],
    "address": ["exact_address"],
    "identity_authority": ["complete_normalized_triple_authority"],
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
CONSUMER_WITNESS_COMPANION_INSERTION = "must_insert"
TRIPLE_AUTHORITY_FIELDS = {"Manufacturer", "DeviceID", "SerialNumber"}
WITNESS_INSTANCE_FIELDS = set(CONSUMER_WITNESS_REQUIRED_FIELDS)
CURRENT_REGISTRY_STATE_FIELDS = set(CURRENT_REGISTRY_STATE_REQUIRED_FIELDS)
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
    pathlib.Path("architecture/atr/07-live-validation-acceptance.md"): "[qualified-identity policy](../regulator-qualified-identity-policy.json)",
    pathlib.Path("architecture/overview.md"): "[qualified-identity policy](./regulator-qualified-identity-policy.json)",
    pathlib.Path("api/graphql.md"): "[qualified-identity policy](../architecture/regulator-qualified-identity-policy.json)",
}
REQUIRED_ATR_NORMATIVE_BLOCKS = {
    pathlib.Path("architecture/atr/01-address-table-model.md"),
    pathlib.Path("architecture/atr/03-ack-nack-insertion-rules.md"),
}
ATR07_ACCEPTANCE_PATH = pathlib.Path("architecture/atr/07-live-validation-acceptance.md")
VERSION_BOUNDARY_PATH = pathlib.Path("architecture/regulator-identity-enrichment.md")
REGISTRY_API_REFERENCE_PATH = pathlib.Path("architecture/regulator-identity-enrichment.md")
REQUIRED_VERSION_BOUNDARY_WORDING = (
    "The canonical path publishes the expanded **schema version 2** policy.",
    "repository references consume that v2 shape, including its required `instance`\n"
    "and `consumer_witness` sections.",
    "it is never described as v1-compatible.",
    "policy: its closed root has no `instance` or `consumer_witness` section.",
    "A v1\nreader must reject the v2 shape, and the current v2 checker rejects an expanded\nshape labelled v1.",
    "no migration runtime or\ngeneral compatibility engine.",
)


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


def require_supported_schema_version(value: object, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CheckError(f"{context}: expected integer schema version")
    if value not in {HISTORICAL_POLICY_VERSION, CURRENT_POLICY_VERSION}:
        raise CheckError(f"{context}: unsupported schema version {value!r}")
    return value


def require_complete_authority(value: object, context: str) -> dict[str, object]:
    authority = require_keys(value, context, TRIPLE_AUTHORITY_FIELDS)
    for member in TRIPLE_MEMBERS:
        if not isinstance(authority[member], str) or not authority[member]:
            raise CheckError(f"{context}.{member}: expected non-empty normalized member")
    if is_named_sentinel_serial(authority["SerialNumber"]):
        raise CheckError(f"{context}.SerialNumber: sentinel serial is not qualified")
    for member in TRIPLE_MEMBERS:
        if authority[member].strip() != authority[member] or authority[member].upper() != authority[member]:
            raise CheckError(f"{context}.{member}: expected already-normalized registry member")
        if member == "DeviceID" and authority[member].rstrip("\x00 ") != authority[member]:
            raise CheckError(f"{context}.{member}: expected fixed-width padding already removed")
    return authority


def is_named_sentinel_serial(value: str) -> bool:
    """Recognize only the policy's named hexadecimal sentinels without rewriting a serial."""
    candidate = value
    if candidate[:2].casefold() == "0x":
        candidate = candidate[2:]
    if not candidate or any(character not in "0123456789abcdefABCDEF" for character in candidate):
        return False
    canonical_hex = candidate.lstrip("0") or "0"
    return canonical_hex.upper() in {"0", "FFFFFFFF", "7FFFFFFF"}


def require_canonical_ebus_unicast_address(value: object, context: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 4
        or not value.startswith("0x")
        or any(character not in "0123456789ABCDEF" for character in value[2:])
    ):
        raise CheckError(f"{context}: expected canonical eBUS unicast address 0xNN")
    if int(value[2:], 16) in {0xA9, 0xAA, 0xFE}:
        raise CheckError(f"{context}: expected AddressClassMaster or AddressClassSlave")
    return value


def require_positive_integer(value: object, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise CheckError(f"{context}: expected positive integer")
    return value


def validate_consumer_witness_instance(witness_value: object, current_state_value: object) -> tuple[dict[str, object], dict[str, object]]:
    """Validate the complete closed witness/current-registry pair schema and domains."""
    witness = require_keys(witness_value, "consumer witness", WITNESS_INSTANCE_FIELDS)
    current_state = require_keys(current_state_value, "current registry state", CURRENT_REGISTRY_STATE_FIELDS)
    require_canonical_ebus_unicast_address(witness["address"], "consumer witness.address")
    require_canonical_ebus_unicast_address(current_state["address"], "current registry state.address")
    require_complete_authority(witness["identity_authority"], "consumer witness.identity_authority")
    require_complete_authority(current_state["identity_authority"], "current registry state.identity_authority")
    require_positive_integer(witness["registry_observation_generation"], "consumer witness.registry_observation_generation")
    require_positive_integer(witness["registry_proof_generation"], "consumer witness.registry_proof_generation")
    require_positive_integer(current_state["registry_observation_generation"], "current registry state.registry_observation_generation")
    require_positive_integer(current_state["registry_proof_generation"], "current registry state.registry_proof_generation")
    require_value(witness["observation_provenance"], "direct_observation", "consumer witness.observation_provenance")
    require_value(witness["current"], True, "consumer witness.current")
    require_value(witness["immutable"], True, "consumer witness.immutable")
    if current_state["availability"] not in CURRENT_REGISTRY_STATE_ALLOWED_VALUES["availability"]:
        raise CheckError(
            "current registry state.availability: expected one of "
            f"{CURRENT_REGISTRY_STATE_ALLOWED_VALUES['availability']!r}"
        )
    return witness, current_state


def consumer_witness_is_current(witness_value: object, current_state_value: object) -> bool:
    """Evaluate the closed witness/current-registry equality relation."""
    witness, current_state = validate_consumer_witness_instance(witness_value, current_state_value)
    return (
        current_state["availability"] == "available"
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


def validate_current_v2_policy(policy: object, path: pathlib.Path) -> None:
    root = require_keys(
        policy,
        str(path),
        V2_POLICY_FIELDS,
    )
    require_supported_schema_version(root["schema_version"], f"{path}.schema_version")
    require_value(root["schema_version"], CURRENT_POLICY_VERSION, f"{path}.schema_version")
    require_value(root["scope"], "cross_address_qualified_identity", f"{path}.scope")
    require_value(root["instance"], CONSUMER_WITNESS_INSTANCE, f"{path}.instance")

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
            "current_registry_state",
            "production",
            "currentness",
            "stale_on",
            "non_witness_inputs",
            "companion_corroboration",
            "companion_insertion",
            "validation_fixtures",
        },
    )
    require_value(
        consumer_witness["kind"],
        "qualified_identity_consumer_witness_v2",
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
    current_registry_state = require_keys(
        consumer_witness["current_registry_state"],
        f"{path}.consumer_witness.current_registry_state",
        {"required_fields", "allowed_values"},
    )
    require_value(
        current_registry_state["required_fields"],
        CURRENT_REGISTRY_STATE_REQUIRED_FIELDS,
        f"{path}.consumer_witness.current_registry_state.required_fields",
    )
    require_value(
        current_registry_state["allowed_values"],
        CURRENT_REGISTRY_STATE_ALLOWED_VALUES,
        f"{path}.consumer_witness.current_registry_state.allowed_values",
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
    require_value(
        consumer_witness["companion_insertion"],
        CONSUMER_WITNESS_COMPANION_INSERTION,
        f"{path}.consumer_witness.companion_insertion",
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


def validate_historical_v1_policy(policy: object, path: pathlib.Path) -> None:
    """Validate the accepted historical v1 closed shape without v2 additions."""
    root = require_keys(policy, str(path), V1_POLICY_FIELDS)
    require_supported_schema_version(root["schema_version"], f"{path}.schema_version")
    require_value(root["schema_version"], HISTORICAL_POLICY_VERSION, f"{path}.schema_version")
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

    enrichment = require_keys(root["enrichment"], f"{path}.enrichment", {"scope", "last_known_good", "cross_address_identity"})
    require_value(enrichment["scope"], "same_address", f"{path}.enrichment.scope")
    require_value(enrichment["last_known_good"], "retain", f"{path}.enrichment.last_known_good")
    require_value(enrichment["cross_address_identity"], "not_qualified", f"{path}.enrichment.cross_address_identity")

    provenance = require_keys(root["provenance"], f"{path}.provenance", {"per_face", "static_seed", "passive_observed"})
    require_value(provenance["per_face"], "retain", f"{path}.provenance.per_face")
    require_value(provenance["static_seed"], "preserve", f"{path}.provenance.static_seed")
    require_value(provenance["passive_observed"], "preserve", f"{path}.provenance.passive_observed")


def validate_policy_versioned(policy: object, path: pathlib.Path) -> None:
    """Dispatch only between the accepted historical v1 and current v2 shapes."""
    if not isinstance(policy, dict):
        raise CheckError(f"{path}: expected object")
    version = require_supported_schema_version(policy.get("schema_version"), f"{path}.schema_version")
    if version == HISTORICAL_POLICY_VERSION:
        validate_historical_v1_policy(policy, path)
        return
    validate_current_v2_policy(policy, path)


def required_atr_normative_block(consumer_witness: dict[str, object]) -> str:
    """Return the bounded ATR block synchronized to the validated policy selector."""
    selector = consumer_witness["companion_corroboration"]
    return f"""<!-- qualified-identity-policy:begin {selector} -->
For the one-ACK alternative, the registry MUST use only a current consumer witness for that same exact source address. The witness is registry-produced from a direct complete normalized `(Manufacturer, DeviceID, SerialNumber)` observation. At the atomic registry lookup/validation/use boundary, its address, authority, observation generation, and proof generation MUST equal the current registry state.

A positive generation or cached `current: true` flag alone MUST NOT satisfy this gate. Replacement, retirement, or a conflict makes the prior witness unavailable/not-current until a fresh direct complete normalized observation produces a new witness.

A generic coherent identity reply, `identity_confirmed`, a topology alias or propagated confirmation, `static_seed`, `passive_observed`, caller assertion, last-known-good data, visible fields, or a directed `0x07/0x04` reply alone MUST NOT serve as witness authority. Directed `0x07/0x04` remains per-face confirmation without serial, and a witness for another address MUST NOT substitute.

`DeviceRegistry.WithCurrentQualifiedIdentityWitness(address, callback)` remains the read-locked operation for bounded non-registry derived-state commits; its callback MUST NOT call `DeviceRegistry` methods. `DeviceRegistry.AdmitPassiveCompanionWithCurrentQualifiedIdentityWitness(source, observedAt)` is the state-changing operation: the registry MUST derive the canonical companion from `source` and, in one write-critical section, MUST validate the current exact-source direct complete normalized witness and passive target companion-slot admission, then MUST commit `slot[companion(ZZ)]` with passive provenance. No caller-supplied companion, lock upgrade, or unlock/relock check-then-use is permitted; replacement, retirement, or conflict cannot interleave between successful validation and the committed passive slot.
<!-- qualified-identity-policy:end {selector} -->"""


def required_registry_api_reference_block(consumer_witness: dict[str, object]) -> str:
    """Return the public registry API-role boundary for the policy selector."""
    selector = consumer_witness["companion_corroboration"]
    return f"""<!-- qualified-identity-policy:registry-api:begin {selector} -->
`DeviceRegistry.WithCurrentQualifiedIdentityWitness(address, callback)` remains the read-locked operation for bounded non-registry derived-state commits. Its callback MUST NOT call `DeviceRegistry` methods; it cannot lock-upgrade or use an unlock/relock check-then-use sequence.

`DeviceRegistry.AdmitPassiveCompanionWithCurrentQualifiedIdentityWitness(source, observedAt)` is the state-changing operation. The registry MUST derive the canonical companion from `source` and MUST atomically validate the current exact-source direct complete normalized witness plus passive target companion-slot admission in one write-critical section. It MUST NOT accept a caller-supplied companion. Replacement, retirement, or conflict cannot interleave between successful validation and the committed passive slot.

The accepted registry implementation is [`registry/admit_passive_companion.go` at `7971e0ab21c55414beb52ab84d6b38b25e27f37d`](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/7971e0ab21c55414beb52ab84d6b38b25e27f37d/registry/admit_passive_companion.go).

This records one registry admission decision. It does not prove wire identity, create attestation authority, perform I/O, make topology an identity proof, or close gateway, M7, or physical acceptance criteria.
<!-- qualified-identity-policy:registry-api:end {selector} -->"""


def required_atr07_acceptance_block(consumer_witness: dict[str, object]) -> str:
    """Return ATR07's closed deterministic acceptance block for the policy selector."""
    selector = consumer_witness["companion_corroboration"]
    return f"""<!-- qualified-identity-policy:atr07-acceptance:begin {selector} -->
The public schema-v2 [qualified-identity policy](../regulator-qualified-identity-policy.json) is the canonical machine-readable companion for this deterministic acceptance block.

### N5 — Single corroboration does NOT companion-insert without a current witness

Procedure (no-current-witness negative): apply one complete positive-ACK observation for source `0xF1` in the deterministic acceptance fixture while no current registry-adjudicated exact-address qualified witness is available for `0xF1`.
Expected: `slot[0xF6]` remains absent. This is the one-ACK negative; it has no claim about a separately qualified current witness.

Procedure (current-qualified positive): apply one ACK plus a registry-adjudicated current exact-address qualified witness for `0xF1`; the ACK observation is complete and positive for source `0xF1`. The state-changing `DeviceRegistry.AdmitPassiveCompanionWithCurrentQualifiedIdentityWitness(source, observedAt)` MUST derive the companion and MUST atomically validate that witness with passive target companion-slot admission in one write-critical section.
Expected: the companion `slot[0xF6]` MUST appear under the one-ACK alternative.

Procedure (stale/invalid/unavailable negatives): repeat the current-qualified fixture with a frozen witness descriptor that is replaced, retired, conflicted, invalid, or unavailable at the atomic registry lookup/validation/use current result.
Expected: `slot[0xF6]` remains absent in every negative fixture. A frozen descriptor is not itself the current result: no cached `current: true`, topology, `static_seed`, `passive_observed`, caller assertion, last-known-good data, per-face `0x07/0x04` reply without serial, or witness for another address may qualify.

The registry-produced direct complete normalized `(Manufacturer, DeviceID, SerialNumber)` witness must match the exact source address, authority, observation generation, and proof generation in the atomic registry lookup/validation/use current result. `DeviceRegistry.WithCurrentQualifiedIdentityWitness(address, callback)` remains the read-locked operation for bounded non-registry derived-state commits and its callback MUST NOT call `DeviceRegistry` methods. No caller-supplied companion, lock upgrade, or unlock/relock check-then-use may separate successful validation from the committed passive slot. The independent two-ACK route remains independent of identity evidence: after the observation window (default 5s) plus a second corroborating positive ACK, `slot[0xF6]` MUST appear without a witness.
<!-- qualified-identity-policy:atr07-acceptance:end {selector} -->"""


def validate_documents(root: pathlib.Path) -> None:
    policy_path = root / POLICY_PATH
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CheckError(f"{policy_path}: invalid JSON: {exc.msg}") from exc
    validate_current_v2_policy(policy, policy_path)

    for relative, reference in REQUIRED_DOCUMENT_REFERENCES.items():
        path = root / relative
        if reference not in path.read_text(encoding="utf-8"):
            raise CheckError(f"{path}: missing required canonical policy reference: {reference!r}")

    version_boundary = (root / VERSION_BOUNDARY_PATH).read_text(encoding="utf-8")
    for wording in REQUIRED_VERSION_BOUNDARY_WORDING:
        if wording not in version_boundary:
            raise CheckError(f"{root / VERSION_BOUNDARY_PATH}: missing required v2 version-boundary wording")

    consumer_witness = policy["consumer_witness"]
    if not isinstance(consumer_witness, dict):
        raise CheckError(f"{policy_path}.consumer_witness: expected object")
    normative_block = required_atr_normative_block(consumer_witness)
    for relative in REQUIRED_ATR_NORMATIVE_BLOCKS:
        path = root / relative
        if normative_block not in path.read_text(encoding="utf-8"):
            raise CheckError(f"{path}: missing required qualified-identity normative block")

    registry_api_block = required_registry_api_reference_block(consumer_witness)
    registry_api_path = root / REGISTRY_API_REFERENCE_PATH
    if registry_api_block not in registry_api_path.read_text(encoding="utf-8"):
        raise CheckError(f"{registry_api_path}: missing required qualified-identity registry API reference block")

    atr07_block = required_atr07_acceptance_block(consumer_witness)
    atr07_path = root / ATR07_ACCEPTANCE_PATH
    if atr07_block not in atr07_path.read_text(encoding="utf-8"):
        raise CheckError(f"{atr07_path}: missing required ATR07 qualified-identity acceptance block")


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
