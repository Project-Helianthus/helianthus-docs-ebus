#!/usr/bin/env python3
"""Fail-closed validation for the OPAQUE_RUNTIME_ACQUISITION_V1 companion."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import stat
import sys
from typing import Any

from markdown_it import MarkdownIt


MANIFEST_PATH = pathlib.Path(
    "docs/platform/manifests/opaque-runtime-acquisition-v1.json"
)
POLICY_PATH = pathlib.Path("docs/platform/opaque-runtime-acquisition-v1.md")
PLATFORM_INDEX_PATH = pathlib.Path("docs/platform/README.md")
ROOT_INDEX_PATH = pathlib.Path("README.md")
VALIDATOR_PATH = pathlib.Path("scripts/validate_opaque_runtime_acquisition.py")
EXPECTED_TOP_LEVEL = {
    "bounded_values",
    "companion_for",
    "content_revision",
    "contract_id",
    "contract_version",
    "discoverability",
    "downstream_conformance",
    "execution",
    "licensing",
    "m2_ledger",
    "normalization_record",
    "opaque_capability",
    "policy",
    "policy_sha256",
    "public_authorization",
    "schema",
    "source_kind",
    "version",
    "zero_trust_boundary",
}
EXPECTED_POLICY_SHA256 = "a95e2ec593a6c06584c06f1486b167c917e756d0af48b83896c51f05e58742d8"
EXPECTED_SOURCE_KINDS = ["runtime", "offline_fixture"]
EXPECTED_COMPANIONS = ["FMV3-M1-06", "FMV3-M2-01"]
EXPECTED_DOWNSTREAM_CONFORMANCE = {
    "docs_lock": [
        "merged_docs_commit_sha_full_40",
        "policy_sha256",
        "manifest_sha256",
        "merged_producer_commit_sha_full_40",
    ],
    "required_behavioral_tests": [
        "registration_paused_before_membership_then_close_wins_without_visible_capability",
        "stale_instance_a_cancellation_does_not_affect_same_key_instance_b",
        "cancel_before_publish_commit_yields_publish_failed_without_external_effect",
        "simultaneous_publish_cancel_has_exactly_one_atomic_winner",
        "cancel_after_publish_commit_returns_already_published_without_mutation",
        "dependency_permutation_omission_duplication_extra_and_count_mismatch_reject_before_cas",
        "empty_fixture_only_and_mixed_source_seal_reject",
        "secret_canaries_absent_from_closed_publication_projection_fields_and_bytes",
    ],
}
EXPECTED_NORMALIZATION_FIELDS = [
    "schema_version",
    "source_kind",
    "source_evidence_id",
    "documentary_notation",
    "documentary_address",
    "documentary_address_base",
    "function_code",
    "logical_table",
    "normalized_zero_based_pdu_offset",
    "word_count",
]
EXPECTED_BOUNDED_VALUES = {
    "activation": "finite_positive_checked_nonoverflowing_bounds_before_activation",
    "allocation": "validate_before_decode_copy_hash_intern_or_retain",
    "attempt_key": {
        "encoding": "non_empty_utf8",
        "equality": "exact_encoded_bytes_no_normalization",
        "max": "attempt_key_max_utf8_bytes",
        "source_ledger_agreement": "required",
    },
    "retained_diagnostics": {
        "count_max": "retained_diagnostic_count_per_object_max",
        "form": "ordered_utf8_strings_only",
        "item_max": "retained_diagnostic_max_utf8_bytes",
        "oversize": "reject_without_truncation",
        "tombstone_retention": "forbidden",
    },
}
EXPECTED_OPAQUE_CAPABILITY = {
    "attempt_instance": {
        "capability_binding": "exact_instance_before_capability_visibility",
        "identity": "opaque_unforgeable_nonserializable_per_attempt_incarnation",
        "key_role": "AttemptKey_documentary_only_not_security_identity",
        "membership": {
            "close": "ledger_admission_atomic_open_to_closing_blocks_new_registration",
            "drain": "wait_all_preclose_registrations",
            "freeze": "closed_exact_ordered_member_set",
            "late_registration": (
                "reject_without_visible_capability_or_retained_open_state"
            ),
            "states": ["open", "closing", "closed"],
        },
        "same_key_recreation": "fresh_independent_instance",
    },
    "representation": "opaque_non_serializable",
    "consumption": "one_shot_compare_and_swap",
    "state_owner": "source_owned_shared_capability_state",
    "value_copy_semantics": "shared_state",
    "attempt_binding": {
        "key": "immutable_exact_source_owned_AttemptKey",
        "security_identity": "opaque_AttemptInstance_not_AttemptKey",
        "claim_path_after_m2_admission": "ledger_linearization_required",
        "source_operation": "CancelOpen(AttemptInstance)",
        "cancel_open": {
            "owner": "runtime_source",
            "lookup": (
                "exact_opaque_closed_AttemptInstance_frozen_membership_only"
            ),
            "capability_effect": "still_open_to_cancelled_terminal_unchanged",
            "ledger_mutation": "forbidden",
            "return": (
                "after_preclose_registrations_member_operations_"
                "reclamation_and_no_open_member"
            ),
        },
    },
    "endpoint_recreation": {
        "eligible_new_acquisition": "fresh_independent_capability_state",
        "visible_identity_or_data_match": "irrelevant",
        "forbidden_prior_capability_actions": [
            "alias",
            "remint",
            "reset",
            "merge",
        ],
        "security_identity": (
            "source_issued_acquisition_capability_not_endpoint_identity"
        ),
        "existing_capability_lifecycle": "own_acquisition_or_attempt_only",
    },
    "coalesced_dependents": "independent_capability_per_dependent",
    "copied_view_race": "exactly_one_winner",
    "terminal_reuse": "forbidden",
    "forbidden_issue_conditions": [
        "non_deliverable_runtime_acquisition",
        "offline_fixture",
    ],
    "issued_lifecycle": {
        "initial": "open",
        "legal_transitions": [
            "open_to_claimed",
            "open_to_cancelled",
            "open_to_failed",
            "open_to_expired",
        ],
        "terminal": ["claimed", "cancelled", "failed", "expired"],
        "non_issuance": "no_capability_outside_lifecycle",
        "retry": "forbidden",
        "terminal_immutable": True,
        "reclamation": {
            "mode": "source_deterministic_synchronous_before_terminal_return",
            "order": "admission_reserved_terminal_sequence",
            "caller_terminal_wrappers": (
                "immutable_non_owning_not_source_tracked"
            ),
        },
    },
    "bounded_state": {
        "capabilities": "endpoint_configured_hard_limit",
        "terminal_reclamation": "required",
        "terminal_sequence": {
            "domain": "uint64_1_to_2^64_minus_1",
            "reservation": "one_before_capability_admission_or_allocation",
            "wrap": "forbidden_checked_arithmetic",
            "reuse": (
                "forbidden_within_owner_lifetime_including_after_reclamation"
            ),
            "exhaustion": (
                "reject_new_capability_preserve_existing_termination"
            ),
        },
        "tombstone": {
            "fields": [
                "schema_version",
                "terminal_sequence",
                "terminal_outcome",
            ],
            "schema_version": 1,
            "terminal_sequence": "reserved_uint64_nonzero",
            "terminal_outcome": ["claimed", "cancelled", "failed", "expired"],
            "additional_fields": "forbidden",
            "forbidden_payloads": [
                "raw_attempt_key",
                "source_evidence_id",
                "normalization_record",
                "evidence_payload",
                "capability_representation",
                "free_form_diagnostic",
            ],
            "count_bound": "capability_tombstone_limit_finite_positive",
            "max_encoded_bytes": (
                "capability_tombstone_max_encoded_bytes_finite_positive"
            ),
            "eviction": "lowest_reserved_terminal_sequence_first",
        },
    },
}
EXPECTED_M2_LEDGER = {
    "state_owner": "shared_ledger_owned_pointer",
    "capability_state_ownership": "external_private_runtime_source",
    "attempt_key": {
        "duplicate": "reject_before_any_state_change",
        "source_binding_match": "required_for_every_runtime_capability",
        "validation": "bounded_before_copy_hash_intern_or_allocation",
    },
    "dependency_set": {
        "claim_binding": (
            "every_capability_claim_and_zero_based_ordinal_exact_digest_"
            "and_declared_order"
        ),
        "identity": (
            "sha256_domain_separated_canonical_count_plus_ordered_"
            "dependent_identities"
        ),
        "order": "exact_predecessor_dependency_set_id_order",
        "sequence_reservation": "attempt_then_claims_in_declared_ordinal_order",
        "validation": (
            "nonempty_unique_bounded_count_and_encoded_bytes_before_decode_"
            "allocation_sequence_reservation_or_cas"
        ),
    },
    "claim_entry_lifecycle": {
        "initial": "unresolved",
        "nonterminal": ["unresolved", "claim_in_progress"],
        "legal_transitions": [
            "unresolved_to_claim_in_progress",
            "claim_in_progress_to_claim_succeeded",
            "claim_in_progress_to_capability_cancelled",
            "claim_in_progress_to_capability_failed",
            "claim_in_progress_to_capability_expired",
            "claim_in_progress_to_claim_rejected_terminal",
            "unresolved_to_attempt_cancelled",
        ],
        "admission": (
            "unresolved_to_claim_in_progress_only_while_attempt_open"
        ),
        "finalization": "record_immutable_source_result_before_completion",
        "cancellation": (
            "claim_in_progress_drains_unresolved_only_attempt_cancelled"
        ),
        "source_result_mapping": {
            "open_to_claimed": "claim_succeeded",
            "already_cancelled": "capability_cancelled",
            "already_failed": "capability_failed",
            "already_expired": "capability_expired",
            "already_claimed": "claim_rejected_terminal",
        },
        "terminal": [
            "claim_succeeded",
            "capability_cancelled",
            "capability_failed",
            "capability_expired",
            "claim_rejected_terminal",
            "attempt_cancelled",
        ],
        "terminal_immutable": True,
        "retry": "forbidden",
    },
    "attempt_lifecycle": {
        "initial": "open",
        "legal_transitions": [
            "open_to_sealed",
            "open_to_cancelling",
            "sealed_to_publishing",
            "sealed_to_cancelling",
            "cancelling_to_cancelled",
            "publishing_to_published",
            "publishing_to_publish_failed",
        ],
        "seal_condition": (
            "nonempty_all_runtime_data_bearing_exact_cardinality_"
            "all_claim_succeeded"
        ),
        "seal_forbidden_sets": (
            "empty_fixture_only_mixed_zero_runtime_duplicate_omitted_reordered"
        ),
        "seal_linearization": "success_predicate_and_open_to_sealed_atomic",
        "seal_non_success": (
            "cancellation_and_audit_only_publication_forbidden"
        ),
        "publish": "one_shot_sealed_to_publishing",
        "publish_cancellation_after_admission": (
            "atomic_commit_winner_publish_failed_before_commit_"
            "already_published_after_commit"
        ),
        "publish_commit_linearization": (
            "irreversible_external_effect_and_publishing_to_published_"
            "one_transactional_commit"
        ),
        "terminal": ["published", "publish_failed", "cancelled"],
        "terminal_immutable": True,
    },
    "bounds": {
        "retained_attempts": "consumer_configured_hard_limit_all_states",
        "claim_entries_per_attempt": "dependency_set_hard_limit",
        "dependency_set_encoded_bytes": (
            "finite_positive_checked_before_collection_decode"
        ),
        "retained_claims_total": (
            "checked_attempt_limit_times_claim_limit"
        ),
        "covered_attempt_states": [
            "open",
            "sealed",
            "cancelling",
            "publishing",
            "published",
            "publish_failed",
            "cancelled",
        ],
        "covered_claim_states": [
            "unresolved",
            "claim_in_progress",
            "claim_succeeded",
            "capability_cancelled",
            "capability_failed",
            "capability_expired",
            "claim_rejected_terminal",
            "attempt_cancelled",
        ],
        "terminal_sequence": {
            "domain": "uint64_1_to_2^64_minus_1",
            "reservation": (
                "attempt_plus_all_claim_entries_batch_before_admission"
            ),
            "wrap": "forbidden_checked_arithmetic",
            "reuse": (
                "forbidden_within_owner_lifetime_including_after_reclamation"
            ),
            "exhaustion": (
                "reject_new_attempt_preserve_existing_termination"
            ),
        },
    },
    "cancellation_protocol": {
        "linearization": ["open_to_cancelling", "sealed_to_cancelling"],
        "blocks_after_linearization": ["claim_admission", "seal", "publish"],
        "drain": "wait_for_all_claim_in_progress_finalization",
        "source_operation": (
            "runtime_source_owned_CancelOpen_exact_closed_AttemptInstance"
        ),
        "unresolved_close": "only_remaining_unresolved_to_attempt_cancelled",
        "completion": (
            "cancelling_to_cancelled_after_source_return_and_unresolved_closure"
        ),
        "admitted_claim_wins": True,
    },
    "publish": "sealed_immutable_ledger_state_only",
    "published_projection": {
        "additional_fields": "forbidden",
        "claim_outcome_digest": (
            "domain_separated_ordered_successful_claim_outcomes"
        ),
        "fields": [
            "schema_version",
            "attempt_terminal_sequence",
            "dependency_set_digest",
            "runtime_dependency_count",
            "claim_outcome_digest",
        ],
        "forbidden_payloads": [
            "raw_attempt_key",
            "attempt_instance",
            "dependent_identity",
            "source_evidence_id",
            "normalization_record",
            "unknown_extension_key_or_value",
            "retained_diagnostic",
            "evidence_payload",
            "capability_representation",
            "endpoint_identity",
            "raw_protocol_data",
        ],
        "schema": "published_attempt_v1",
        "schema_version": 1,
    },
    "mutable_dto": "forbidden",
    "reclamation": {
        "mode": "deterministic_synchronous_on_terminal_and_admission",
        "order": "admission_reserved_terminal_sequence",
        "audit_tombstone": {
            "additional_fields": "forbidden",
            "count_bound": "ledger_audit_tombstone_limit_finite_positive",
            "max_encoded_bytes": (
                "ledger_audit_tombstone_max_encoded_bytes_finite_positive"
            ),
            "eviction": "lowest_ledger_reserved_terminal_sequence_first",
            "forbidden_payloads": [
                "raw_attempt_key",
                "attempt_key_digest",
                "source_evidence_id",
                "normalization_record",
                "evidence_payload",
                "capability_representation",
                "free_form_diagnostic",
            ],
            "variants": {
                "attempt": {
                    "fields": [
                        "schema_version",
                        "object_kind",
                        "terminal_sequence",
                        "terminal_outcome",
                    ],
                    "schema_version": 1,
                    "object_kind": "attempt",
                    "terminal_sequence": "reserved_uint64_nonzero",
                    "terminal_outcome": [
                        "published",
                        "publish_failed",
                        "cancelled",
                    ],
                },
                "claim": {
                    "fields": [
                        "schema_version",
                        "object_kind",
                        "terminal_sequence",
                        "attempt_terminal_sequence",
                        "claim_ordinal",
                        "terminal_outcome",
                    ],
                    "schema_version": 1,
                    "object_kind": "claim",
                    "terminal_sequence": "reserved_uint64_nonzero",
                    "attempt_terminal_sequence": "reserved_uint64_nonzero",
                    "claim_ordinal": "uint64_zero_based",
                    "terminal_outcome": [
                        "claim_succeeded",
                        "capability_cancelled",
                        "capability_failed",
                        "capability_expired",
                        "claim_rejected_terminal",
                        "attempt_cancelled",
                    ],
                },
            },
        },
        "caller_terminal_wrappers": (
            "immutable_non_owning_not_retained_ledger_state"
        ),
        "eligibility": (
            "terminal_no_in_progress_operation_"
            "no_retained_nonterminal_reference"
        ),
    },
    "terminal_reclamation": "required",
}
EXPECTED_RUNTIME_SOURCE = {
    "capability": "required_for_delivery",
    "issuer": "runtime_source",
    "issue_condition": "deliverable_runtime_acquisition_only",
    "deliverability": {
        "authority": "runtime_source_owned",
        "production_stage": (
            "post_correlation_successful_dependent_production"
        ),
        "serialization": "forbidden",
        "caller_control": "forbidden",
        "reconstruction": "forbidden",
        "predecessor_contract": (
            "docs/platform/modbus-foundation-profile-contract-v1.md"
            "#physical-and-logical-identity"
        ),
        "required_conditions": [
            "request_bound_wire_response_id",
            "wire_outcome_successful_data",
            "dependent_still_attached",
            "exact_logical_slice_validated",
            "coherent_production",
        ],
        "excluded_outcomes": [
            "detached_dependent",
            "cancelled_dependent",
            "protocol_exception",
            "malformed_response",
            "transport_or_dependent_failure",
            "late_or_abandoned_response",
            "uncorrelated_frame",
            "torn_or_incoherent_production",
            "any_non_success_outcome",
        ],
    },
}
EXPECTED_DISCOVERABILITY = {
    "policy_link": POLICY_PATH.as_posix(),
    "manifest_link": MANIFEST_PATH.as_posix(),
    "platform_index": PLATFORM_INDEX_PATH.as_posix(),
    "root_index": ROOT_INDEX_PATH.as_posix(),
}
EXPECTED_AUTHORIZATION = {
    "gateway": "none",
    "hardware": "none",
    "semantic": "none",
    "vendor": "none",
    "write": "none",
}
EXPECTED_REQUIRED_TERMS = (
    "`source_kind` is a closed enum with exactly two values",
    "The capability is source-issued, opaque, and non-serializable",
    "Deliverability is owned and decided by the runtime source after correlation",
    "exactly post-correlation successful dependent production",
    "predecessor contract's\n[successful dependent production](./modbus-foundation-profile-contract-v1.md#physical-and-logical-identity)\nboundary",
    "outcome `successful_data`",
    "the\ndependent remains attached",
    "its exact logical slice validates",
    "production\nis coherent",
    "MUST NOT be caller-controlled",
    "or\nreconstructed from endpoint identity",
    "A detached or cancelled dependent",
    "protocol exception, malformed response",
    "transport or dependent failure",
    "late/abandoned response, uncorrelated frame",
    "torn/incoherent production",
    "other non-success outcome is not deliverable",
    "one-shot compare-and-swap (CAS)",
    "`source_owned_shared_capability_state`",
    "it is not an M2 ledger pointer",
    "| `open` | `claimed` |",
    "| `open` | `cancelled` |",
    "| `open` | `failed` |",
    "| `open` | `expired` |",
    "There is no transition between terminal states and no return to `open`",
    "exactly one claim wins",
    "every conforming claim through\nany copied view MUST pass through that attempt's ledger claim-admission\nlinearization",
    "attempt-bound operation, `CancelOpen(AttemptInstance)`",
    "An `AttemptInstance` is an opaque, unforgeable, non-serializable source-owned",
    "Instance membership begins `open`. Ledger admission atomically performs",
    "`open -> closing`, blocks every later registration",
    "performs `closing -> closed`",
    "The source owns and executes\nthis operation and all capability CAS state. M2 owns the attempt",
    "atomically performs `open -> cancelled` when the state is still `open`",
    "cannot mutate any ledger entry or attempt state",
    "fresh,\nindependent capability state",
    "MUST NOT alias, remint, reset, or merge an earlier\ncapability",
    "Visible\nendpoint identity and transport generation are provenance, not capability\nsecurity identity",
    "governed only by its own\nacquisition and, where applicable, its own attempt lifecycle",
    "exactly `N` issued capabilities",
    "configured finite hard limit on private\ncapability state",
    "non-issuance is outside the capability lifecycle",
    "synchronously removes terminal capability state from its bounded\nlive tracking set before the terminal operation returns",
    "`capability_tombstone_limit`. Tombstones are\nordered by a source-reserved terminal sequence; insertion that exceeds the\nlimit synchronously evicts the lowest terminal sequence first",
    "Before capability admission or allocation, the source MUST reserve one unique\nterminal sequence",
    "checked, monotonic, non-wrapping",
    "Exhaustion rejects new capability\nissuance",
    "The capability tombstone schema is closed and has exactly these fields",
    "capability tombstone MUST NOT retain a raw `AttemptKey`, `source_evidence_id`,\nnormalization record, evidence payload",
    "`capability_tombstone_max_encoded_bytes`",
    "caller-retained terminal wrapper is an immutable, non-owning view",
    "ledger-owned shared pointer",
    "MUST NOT own, replace,\nserialize, reconstruct, or expose the capability's private source-owned CAS\nstate",
    "Insertion of a duplicate `AttemptKey` MUST be rejected before it\nchanges capability",
    "Each runtime claim entry begins `unresolved`. `claim_in_progress` is a counted\nnonterminal state",
    "| `unresolved` | `claim_in_progress` |",
    "| `claim_in_progress` | `claim_succeeded` |",
    "| `unresolved` | `attempt_cancelled` |",
    "`claim_rejected_terminal`",
    "A terminal claim entry cannot\nreturn to `unresolved`, change outcome, or be retried",
    "Claim admission is the atomic `unresolved -> claim_in_progress` transition",
    "Its finalization MUST record the corresponding immutable source result",
    "`open -> cancelling` or `sealed -> cancelling`",
    "prevents new claim admission, `Seal()`, and `Publish()`",
    "waits\nuntil every already admitted `claim_in_progress` operation has recorded its\nimmutable terminal result",
    "invokes the source-owned\n`CancelOpen(AttemptInstance)` operation",
    "closes only the\nremaining `unresolved` entries as `attempt_cancelled`",
    "an admitted claim wins the ordering race",
    "| `open` | `sealed` |",
    "| `open` | `cancelling` |",
    "| `cancelling` | `cancelled` |",
    "| `sealed` | `publishing` |",
    "| `publishing` | `published` |",
    "| `publishing` | `publish_failed` |",
    "No other attempt transition is legal",
    "`Publish()` MUST consume that sealed immutable ledger state",
    "`Seal()` MUST reject unless the ordered dependency set is non-empty",
    "claim cardinality equals dependency cardinality",
    "fixture-only, mixed fixture/runtime",
    "permanently blocks sealing and publication for that attempt",
    "The success predicate and `open -> sealed` transition MUST linearize as one\natomic decision",
    "`Publish()` is one-shot",
    "atomic publication decision that performs exactly one of",
    "returns exactly `already_published` without state or external-effect change",
    "`Publish()` MUST emit only `published_attempt_v1`",
    "secret canaries into\nevery forbidden source location",
    "predecessor's exact ordered `dependency_set_id`",
    "Before terminal-sequence reservation, ledger allocation, or any capability CAS",
    "all retained attempts across `open`, `sealed`, `cancelling`, `publishing`,",
    "total retained claim entries across `unresolved`, `claim_in_progress`, and",
    "Admission counts every retained state, not only `open`",
    "ledger synchronously reclaims eligible terminal attempt and claim entries",
    "no reference from a\nretained nonterminal attempt",
    "`ledger_audit_tombstone_limit`; insertion beyond the limit synchronously\nevicts the lowest terminal sequence first",
    "reserve one unique attempt terminal sequence and one\nunique claim terminal sequence for every admitted claim entry",
    "reserved all-or-nothing from `1..2^64-1` using checked monotonic unsigned 64-bit\narithmetic",
    "Sequence exhaustion blocks new attempts but cannot prevent any existing\nattempt or claim entry from reaching its terminal outcome",
    "The ledger audit tombstone schema has exactly two closed variants",
    "Audit tombstones MUST\nNOT retain raw `AttemptKey`, an `AttemptKey` digest, `source_evidence_id`,\nnormalization records, evidence payloads",
    "`ledger_audit_tombstone_max_encoded_bytes`",
    "lowest terminal sequence first",
    "caller-retained terminal attempt or claim wrapper is an immutable, non-owning",
    "`shared_ledger_owned_pointer` exists only while the bounded ledger owns the\nattempt/publication state",
    "MUST perform zero capability\nCAS operations",
    "MUST NOT receive a production `sample_id`",
    "Unknown extension fields MUST be preserved losslessly",
    "`source_evidence_id_max_utf8_bytes`",
    "`normalization_record_max_encoded_bytes`",
    "`normalization_extension_count_max`",
    "`normalization_extension_key_max_utf8_bytes`",
    "`normalization_extension_value_max_encoded_bytes`",
    "`retained_diagnostic_count_per_object_max`",
    "The complete encoded-record bound MUST be checked before decoding an encoded\nrecord or allocating its object tree",
    "Retained\ndiagnostics, when present, are an ordered list of UTF-8 strings",
    "exact lossless\nobligation applies only to a record admitted within every V1 bound",
    "exact record equality",
    "## Normative Public API Behavior",
    "## Implementation Examples (Non-Normative)",
    "**no** gateway authorization, vendor authorization,\nsemantic authorization, device authorization, or write authorization",
)
FORBIDDEN_POLICY_TERMS = (
    "source_issued_shared_ledger_pointer",
    "private_source_owned_source_issued_capability_state",
    "claimed, not-issued",
)
EXPECTED_INDEX_LINKS = {
    PLATFORM_INDEX_PATH: (
        "./opaque-runtime-acquisition-v1.md",
        "./manifests/opaque-runtime-acquisition-v1.json",
    ),
    ROOT_INDEX_PATH: (
        "docs/platform/opaque-runtime-acquisition-v1.md",
        "docs/platform/manifests/opaque-runtime-acquisition-v1.json",
    ),
}
NORMATIVE_ARTIFACT_PATHS = (MANIFEST_PATH, POLICY_PATH, VALIDATOR_PATH)


class DuplicateJSONKeyError(ValueError):
    """Raised when a JSON object repeats a member name."""


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateJSONKeyError(f"duplicate JSON key: {key!r}")
        value[key] = item
    return value


def _read_json(
    path: pathlib.Path, errors: list[str], label: str = "manifest"
) -> dict[str, Any] | None:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except (OSError, json.JSONDecodeError, DuplicateJSONKeyError) as exc:
        errors.append(f"{label} unreadable: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label} root must be an object")
        return None
    return value


def _strict_json_equal(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(
            _strict_json_equal(actual[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _strict_json_equal(item, value)
            for item, value in zip(actual, expected)
        )
    return actual == expected


def _require_equal(
    manifest: dict[str, Any], key: str, expected: object, errors: list[str]
) -> None:
    if not _strict_json_equal(manifest.get(key), expected):
        errors.append(f"{key} does not match the closed V1 inventory")


def _validate_closed_object(
    value: object, expected: dict[str, object], label: str, errors: list[str]
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return
    if not _strict_json_equal(value, expected):
        errors.append(f"{label} does not match the closed V1 inventory")


_COMMONMARK = MarkdownIt("commonmark")


def _inline_code_marker(content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"<inline-code:{digest}>"


def _parse_commonmark(text: str) -> list[Any]:
    sanitized = "\n".join(
        "" if line.startswith(("    ", "\t")) else line
        for line in text.splitlines()
    )
    return _COMMONMARK.parse(sanitized)


def _visible_markdown(text: str) -> str:
    visible: list[str] = []
    for token in _parse_commonmark(text):
        if token.type != "inline" or token.children is None:
            continue
        for child in token.children:
            if child.type == "text":
                visible.append(child.content)
            elif child.type in {"softbreak", "hardbreak"}:
                visible.append("\n")
            elif child.type == "code_inline":
                visible.append(_inline_code_marker(child.content))
        visible.append("\n")
    return "".join(visible).rstrip("\n")


def _visible_markdown_link_destinations(text: str) -> set[str]:
    destinations: set[str] = set()
    for token in _parse_commonmark(text):
        if token.type != "inline" or token.children is None:
            continue
        active_links: list[tuple[str, list[str]]] = []
        for child in token.children:
            if child.type == "link_open":
                href = child.attrGet("href") or ""
                active_links.append((href, []))
            elif child.type == "link_close" and active_links:
                href, label = active_links.pop()
                if href and "".join(label).strip():
                    destinations.add(href)
            elif active_links and child.type == "text":
                active_links[-1][1].append(child.content)
            elif active_links and child.type == "code_inline":
                active_links[-1][1].append(child.content)
            elif active_links and child.type in {"softbreak", "hardbreak"}:
                active_links[-1][1].append("\n")
    return destinations


def _regular_in_repo_target(
    root: pathlib.Path,
    index_path: pathlib.Path,
    destination: str,
) -> bool:
    relative = pathlib.PurePosixPath(destination)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or "://" in destination
        or destination.startswith(("#", "~"))
        or "?" in destination
        or "#" in destination
    ):
        return False
    candidate = root / index_path.parent / pathlib.Path(*relative.parts)
    try:
        candidate_relative = candidate.relative_to(root)
    except ValueError:
        return False
    current = root
    for part in candidate_relative.parts:
        current = current / part
        try:
            if stat.S_ISLNK(current.lstat().st_mode):
                return False
        except OSError:
            return False
    try:
        root_resolved = root.resolve(strict=True)
        candidate_resolved = candidate.resolve(strict=True)
        candidate_resolved.relative_to(root_resolved)
    except (OSError, ValueError):
        return False
    try:
        return stat.S_ISREG(candidate_resolved.stat().st_mode)
    except OSError:
        return False


def _validate_discoverability(
    root: pathlib.Path, errors: list[str]
) -> None:
    for index_path, required_destinations in EXPECTED_INDEX_LINKS.items():
        try:
            index_text = (root / index_path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{index_path} unreadable: {exc}")
            continue
        visible_destinations = _visible_markdown_link_destinations(index_text)
        for destination in required_destinations:
            if destination not in visible_destinations:
                errors.append(
                    f"{index_path} missing visible discoverability link: "
                    f"{destination}"
                )
                continue
            if not _regular_in_repo_target(root, index_path, destination):
                errors.append(
                    f"{index_path} discoverability target is not a regular "
                    f"in-repo file: {destination}"
                )


def _has_symlink_component(path: pathlib.Path) -> bool:
    current = pathlib.Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        try:
            if stat.S_ISLNK(current.lstat().st_mode):
                return True
        except OSError:
            return False
    return False


def _validate_prior_revision(
    root: pathlib.Path,
    prior_root: pathlib.Path,
    manifest: dict[str, Any],
    errors: list[str],
) -> None:
    if _has_symlink_component(prior_root):
        errors.append("prior root must be an existing regular directory")
        return
    if not prior_root.is_dir() or prior_root.is_symlink():
        errors.append("prior root must be an existing regular directory")
        return
    if prior_root.resolve() == root.resolve():
        errors.append("prior root must differ from current root")
        return
    prior_manifest_path = prior_root / MANIFEST_PATH
    if _has_symlink_component(prior_manifest_path):
        errors.append("prior opaque manifest must be a regular file")
        return
    if not prior_manifest_path.exists():
        if (
            manifest.get("contract_id") != "OPAQUE_RUNTIME_ACQUISITION_V1"
            or manifest.get("version") != 1
            or manifest.get("contract_version") != 1
            or manifest.get("content_revision") != 1
        ):
            errors.append(
                "an initial opaque runtime acquisition contract must be "
                "OPAQUE_RUNTIME_ACQUISITION_V1 revision 1"
            )
        return
    if (
        not prior_manifest_path.is_file()
    ):
        errors.append("prior opaque manifest must be a regular file")
        return
    prior_manifest = _read_json(
        prior_manifest_path, errors, "prior opaque manifest"
    )
    if prior_manifest is None:
        return
    identity = ("contract_id", "version", "contract_version", "content_revision")
    if any(prior_manifest.get(key) != manifest.get(key) for key in identity):
        errors.append(
            "OPAQUE_RUNTIME_ACQUISITION_V1 identity and revision cannot "
            "change in place; use a new versioned artifact and contract"
        )
        return
    for relative in NORMATIVE_ARTIFACT_PATHS:
        current_path = root / relative
        prior_path = prior_root / relative
        if (
            not current_path.is_file()
            or _has_symlink_component(current_path)
            or not prior_path.is_file()
            or _has_symlink_component(prior_path)
        ):
            errors.append(
                "same-version prior comparison requires regular normative "
                f"artifacts: {relative}"
            )
            continue
        if current_path.read_bytes() != prior_path.read_bytes():
            errors.append(
                "existing OPAQUE_RUNTIME_ACQUISITION_V1 revision 1 must "
                "remain byte-identical; semantic changes require a new "
                f"versioned artifact and contract: {relative}"
            )


def validate(
    root: pathlib.Path,
    prior_root: pathlib.Path | None = None,
    *,
    expected_policy_sha256: str | None = EXPECTED_POLICY_SHA256,
    required_terms: tuple[str, ...] = EXPECTED_REQUIRED_TERMS,
) -> tuple[list[str], str | None]:
    errors: list[str] = []
    if _has_symlink_component(root) or not root.is_dir():
        return ["root must be an existing regular directory"], None
    for relative in NORMATIVE_ARTIFACT_PATHS:
        if _has_symlink_component(root / relative):
            errors.append(
                "current normative artifact must not use symlink components: "
                f"{relative}"
            )
    if errors:
        return errors, None

    manifest_path = root / MANIFEST_PATH
    policy_path = root / POLICY_PATH
    manifest = _read_json(manifest_path, errors)
    if manifest is None:
        return errors, None

    if set(manifest) != EXPECTED_TOP_LEVEL:
        errors.append("manifest top-level keys must match the closed V1 schema")
    _require_equal(
        manifest, "schema", "helianthus.modbus.opaque-runtime-acquisition", errors
    )
    _require_equal(manifest, "version", 1, errors)
    _require_equal(manifest, "contract_id", "OPAQUE_RUNTIME_ACQUISITION_V1", errors)
    _require_equal(manifest, "contract_version", 1, errors)
    _require_equal(manifest, "content_revision", 1, errors)
    _require_equal(manifest, "policy", POLICY_PATH.as_posix(), errors)
    _require_equal(manifest, "companion_for", EXPECTED_COMPANIONS, errors)
    _validate_closed_object(
        manifest.get("downstream_conformance"),
        EXPECTED_DOWNSTREAM_CONFORMANCE,
        "downstream_conformance",
        errors,
    )
    _validate_closed_object(
        manifest.get("discoverability"),
        EXPECTED_DISCOVERABILITY,
        "discoverability",
        errors,
    )
    _require_equal(
        manifest,
        "execution",
        {
            "plan_decision": "D13",
            "plan_issue": "FMV3-M1-05",
            "producer_issue": "FMV3-M1-06",
            "consumer_issue": "FMV3-M2-01",
        },
        errors,
    )
    _require_equal(
        manifest,
        "licensing",
        {
            "policy": "AGPL-3.0",
            "restricted_source_copy": "forbidden",
            "vendor_protocol_facts": "none",
        },
        errors,
    )
    _validate_closed_object(
        manifest.get("bounded_values"),
        EXPECTED_BOUNDED_VALUES,
        "bounded_values",
        errors,
    )
    _require_equal(
        manifest,
        "zero_trust_boundary",
        "no_gateway_vendor_semantic_write_authorization",
        errors,
    )
    _validate_closed_object(
        manifest.get("public_authorization"), EXPECTED_AUTHORIZATION,
        "public_authorization", errors,
    )
    _validate_closed_object(
        manifest.get("opaque_capability"), EXPECTED_OPAQUE_CAPABILITY,
        "opaque_capability", errors,
    )
    _validate_closed_object(
        manifest.get("m2_ledger"), EXPECTED_M2_LEDGER, "m2_ledger", errors
    )

    source_kind = manifest.get("source_kind")
    if not isinstance(source_kind, dict):
        errors.append("source_kind must be an object")
    else:
        if set(source_kind) != {"allowed", "runtime", "offline_fixture"}:
            errors.append("source_kind keys must match the closed V1 schema")
        if not _strict_json_equal(
            source_kind.get("allowed"), EXPECTED_SOURCE_KINDS
        ):
            errors.append("source_kind.allowed must be exactly runtime/offline_fixture")
        _validate_closed_object(
            source_kind.get("runtime"), EXPECTED_RUNTIME_SOURCE,
            "source_kind.runtime",
            errors,
        )
        _validate_closed_object(
            source_kind.get("offline_fixture"),
            {
                "capability": "forbidden",
                "capability_cas_calls": 0,
                "production_sample_id": "forbidden",
                "trust": "untrusted",
            },
            "source_kind.offline_fixture",
            errors,
        )

    normalization = manifest.get("normalization_record")
    if not isinstance(normalization, dict):
        errors.append("normalization_record must be an object")
    elif not _strict_json_equal(normalization, {
        "schema": "versioned",
        "required_fields": EXPECTED_NORMALIZATION_FIELDS,
        "unknown_extension_fields": (
            "preserved_losslessly_without_truncation"
        ),
        "round_trip": "exact_record_equality_within_admitted_bounds",
        "bounds": {
            "encoded_record_max": "normalization_record_max_encoded_bytes",
            "field_count_max": (
                "checked_10_plus_normalization_extension_count_max"
            ),
            "required_string_max": (
                "normalization_required_string_max_utf8_bytes"
            ),
            "source_evidence_id": {
                "encoding": "non_empty_utf8",
                "max": "source_evidence_id_max_utf8_bytes",
            },
            "unknown_extensions": {
                "count_max": "normalization_extension_count_max",
                "key": (
                    "non_empty_utf8_at_most_"
                    "normalization_extension_key_max_utf8_bytes"
                ),
                "value_max": (
                    "normalization_extension_value_max_encoded_bytes"
                ),
            },
            "validation_order": (
                "encoded_total_then_fields_before_owner_allocation"
            ),
        },
    }):
        errors.append("normalization_record does not match the closed V1 inventory")

    try:
        policy_bytes = policy_path.read_bytes()
    except OSError as exc:
        errors.append(f"policy unreadable: {exc}")
        return errors, None
    policy_digest = hashlib.sha256(policy_bytes).hexdigest()
    if manifest.get("policy_sha256") != policy_digest:
        errors.append("policy artifact bytes do not match manifest policy_sha256")
    if (
        expected_policy_sha256 is not None
        and policy_digest != expected_policy_sha256
    ):
        errors.append("policy artifact bytes do not match OPAQUE_RUNTIME_ACQUISITION_V1")

    try:
        policy_text = policy_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"policy is not UTF-8: {exc}")
        return errors, policy_digest
    visible_policy_text = _visible_markdown(policy_text)
    visible_policy_links = _visible_markdown_link_destinations(policy_text)
    for term in required_terms:
        visible_term = _visible_markdown(term)
        required_links = _visible_markdown_link_destinations(term)
        if (
            not visible_term
            or visible_term not in visible_policy_text
            or not required_links.issubset(visible_policy_links)
        ):
            errors.append(f"policy missing required normative term: {term}")
    for term in FORBIDDEN_POLICY_TERMS:
        if term in policy_text:
            errors.append(f"policy contains forbidden legacy term: {term}")

    _validate_discoverability(root, errors)
    if prior_root is not None:
        _validate_prior_revision(root, prior_root, manifest, errors)

    return errors, policy_digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--prior-root", type=pathlib.Path)
    args = parser.parse_args()
    errors, digest = validate(
        args.root.absolute(),
        args.prior_root.absolute() if args.prior_root else None,
    )
    if errors:
        for error in errors:
            print(
                f"opaque_runtime_acquisition_contract_invalid: {error}",
                file=sys.stderr,
            )
        return 1
    print(
        "opaque_runtime_acquisition_contract_ok "
        f"policy_sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
