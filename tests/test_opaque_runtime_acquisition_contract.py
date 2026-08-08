from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import subprocess
from collections.abc import Callable

import pytest
from scripts import validate_opaque_runtime_acquisition as contract_validator


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR = pathlib.Path("scripts/validate_opaque_runtime_acquisition.py")
MANIFEST = pathlib.Path(
    "docs/platform/manifests/opaque-runtime-acquisition-v1.json"
)
POLICY = pathlib.Path("docs/platform/opaque-runtime-acquisition-v1.md")
PLATFORM_INDEX = pathlib.Path("docs/platform/README.md")
ROOT_INDEX = pathlib.Path("README.md")


def run_validator(
    root: pathlib.Path,
    *,
    prior_root: pathlib.Path | None = None,
) -> subprocess.CompletedProcess[str]:
    command = ["python3", str(root / VALIDATOR), "--root", str(root)]
    if prior_root is not None:
        command.extend(("--prior-root", str(prior_root)))
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )


def materialize_fixture(tmp_path: pathlib.Path) -> pathlib.Path:
    for relative in (VALIDATOR, MANIFEST, POLICY, PLATFORM_INDEX, ROOT_INDEX):
        source = REPO_ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return tmp_path


def load_manifest(root: pathlib.Path) -> dict[str, object]:
    return json.loads((root / MANIFEST).read_text(encoding="utf-8"))


def write_manifest(root: pathlib.Path, manifest: dict[str, object]) -> None:
    (root / MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_raw_manifest(root: pathlib.Path, raw_manifest: str) -> None:
    (root / MANIFEST).write_text(raw_manifest, encoding="utf-8")


def refresh_policy_hash(root: pathlib.Path, manifest: dict[str, object]) -> None:
    manifest["policy_sha256"] = hashlib.sha256(
        (root / POLICY).read_bytes()
    ).hexdigest()


def test_repository_opaque_runtime_acquisition_contract_is_valid() -> None:
    result = run_validator(REPO_ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "opaque_runtime_acquisition_contract_ok" in result.stdout


def test_empty_manifest_fails_closed(tmp_path: pathlib.Path) -> None:
    root = materialize_fixture(tmp_path)
    (root / MANIFEST).write_text("{}\n", encoding="utf-8")
    result = run_validator(root)
    assert result.returncode != 0
    assert "opaque_runtime_acquisition_contract_invalid" in result.stderr


@pytest.mark.parametrize(
    ("key", "expected_key_first"),
    (
        ("version", True),
        ("version", False),
        ("policy_link", True),
        ("policy_link", False),
    ),
)
def test_duplicate_json_keys_fail_closed_regardless_of_order(
    tmp_path: pathlib.Path, key: str, expected_key_first: bool
) -> None:
    root = materialize_fixture(tmp_path)
    manifest_path = root / MANIFEST
    raw_manifest = manifest_path.read_text(encoding="utf-8")
    if key == "version":
        expected = '  "version": 1,'
        unexpected = '  "version": 2,'
    else:
        expected = (
            '    "policy_link": '
            '"docs/platform/opaque-runtime-acquisition-v1.md",'
        )
        unexpected = '    "policy_link": "unexpected-policy.md",'
    assert raw_manifest.count(expected) == 1
    members = (expected, unexpected) if expected_key_first else (unexpected, expected)
    write_raw_manifest(root, raw_manifest.replace(expected, "\n".join(members)))

    result = run_validator(root)

    assert result.returncode != 0
    assert f"duplicate JSON key: '{key}'" in result.stderr


def test_ledger_eviction_sentinel_is_ledger_specific() -> None:
    manifest = load_manifest(REPO_ROOT)
    capability = manifest["opaque_capability"]
    ledger = manifest["m2_ledger"]
    assert isinstance(capability, dict)
    assert isinstance(ledger, dict)
    capability_state = capability["bounded_state"]
    ledger_reclamation = ledger["reclamation"]
    assert isinstance(capability_state, dict)
    assert isinstance(ledger_reclamation, dict)
    capability_tombstone = capability_state["tombstone"]
    ledger_tombstone = ledger_reclamation["audit_tombstone"]
    assert isinstance(capability_tombstone, dict)
    assert isinstance(ledger_tombstone, dict)
    assert ledger_tombstone["eviction"] == (
        "lowest_ledger_reserved_terminal_sequence_first"
    )
    assert ledger_tombstone["eviction"] != capability_tombstone["eviction"]


def test_ledger_eviction_required_term_cannot_use_capability_occurrence(
    tmp_path: pathlib.Path,
) -> None:
    root = materialize_fixture(tmp_path)
    policy = root / POLICY
    policy_text = policy.read_text(encoding="utf-8")
    ledger_term = (
        "`ledger_audit_tombstone_limit`; insertion beyond the limit synchronously\n"
        "evicts the lowest terminal sequence first"
    )
    assert ledger_term in policy_text
    policy.write_text(policy_text.replace(ledger_term, "removed"), encoding="utf-8")
    manifest = load_manifest(root)
    refresh_policy_hash(root, manifest)
    write_manifest(root, manifest)
    digest = hashlib.sha256(policy.read_bytes()).hexdigest()
    errors, _ = contract_validator.validate(
        root.resolve(),
        expected_policy_sha256=digest,
        required_terms=(ledger_term,),
    )
    assert errors == [f"policy missing required normative term: {ledger_term}"]


def test_capability_eviction_required_term_cannot_use_ledger_occurrence(
    tmp_path: pathlib.Path,
) -> None:
    root = materialize_fixture(tmp_path)
    policy = root / POLICY
    capability_term = (
        "`capability_tombstone_limit`. Tombstones are\n"
        "ordered by a source-reserved terminal sequence; insertion that exceeds the\n"
        "limit synchronously evicts the lowest terminal sequence first"
    )
    policy_text = policy.read_text(encoding="utf-8")
    assert capability_term in policy_text
    policy.write_text(
        policy_text.replace(capability_term, "removed"),
        encoding="utf-8",
    )
    manifest = load_manifest(root)
    refresh_policy_hash(root, manifest)
    write_manifest(root, manifest)
    digest = hashlib.sha256(policy.read_bytes()).hexdigest()
    errors, _ = contract_validator.validate(
        root.resolve(),
        expected_policy_sha256=digest,
        required_terms=(capability_term,),
    )
    assert errors == [f"policy missing required normative term: {capability_term}"]


@pytest.mark.parametrize(
    "mutation",
    (
        lambda manifest: manifest.__setitem__("version", True),
        lambda manifest: manifest["opaque_capability"]["bounded_state"][
            "tombstone"
        ].__setitem__("schema_version", True),
    ),
)
def test_boolean_cannot_satisfy_numeric_json_sentinel(
    tmp_path: pathlib.Path, mutation: Callable[[dict[str, object]], None]
) -> None:
    root = materialize_fixture(tmp_path)
    manifest = load_manifest(root)
    mutation(manifest)
    write_manifest(root, manifest)
    result = run_validator(root)
    assert result.returncode != 0
    assert "opaque_runtime_acquisition_contract_invalid" in result.stderr


def mutate_extra_source_kind(root: pathlib.Path, manifest: dict[str, object]) -> None:
    source_kind = manifest["source_kind"]
    assert isinstance(source_kind, dict)
    allowed = source_kind["allowed"]
    assert isinstance(allowed, list)
    allowed.append("replay")


def mutate_runtime_issuance(root: pathlib.Path, manifest: dict[str, object]) -> None:
    source_kind = manifest["source_kind"]
    assert isinstance(source_kind, dict)
    runtime = source_kind["runtime"]
    assert isinstance(runtime, dict)
    runtime["issue_condition"] = "any_runtime_acquisition"


def mutate_deliverability_exclusion(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    source_kind = manifest["source_kind"]
    assert isinstance(source_kind, dict)
    runtime = source_kind["runtime"]
    assert isinstance(runtime, dict)
    deliverability = runtime["deliverability"]
    assert isinstance(deliverability, dict)
    excluded = deliverability["excluded_outcomes"]
    assert isinstance(excluded, list)
    excluded.remove("torn_or_incoherent_production")


def mutate_fixture_capability(root: pathlib.Path, manifest: dict[str, object]) -> None:
    source_kind = manifest["source_kind"]
    assert isinstance(source_kind, dict)
    fixture = source_kind["offline_fixture"]
    assert isinstance(fixture, dict)
    fixture["capability"] = "allowed"


def mutate_fixture_cas(root: pathlib.Path, manifest: dict[str, object]) -> None:
    source_kind = manifest["source_kind"]
    assert isinstance(source_kind, dict)
    fixture = source_kind["offline_fixture"]
    assert isinstance(fixture, dict)
    fixture["capability_cas_calls"] = 1


def mutate_fixture_sample(root: pathlib.Path, manifest: dict[str, object]) -> None:
    source_kind = manifest["source_kind"]
    assert isinstance(source_kind, dict)
    fixture = source_kind["offline_fixture"]
    assert isinstance(fixture, dict)
    fixture["production_sample_id"] = "allowed"


def mutate_copy_semantics(root: pathlib.Path, manifest: dict[str, object]) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    capability["value_copy_semantics"] = "independent_state"


def mutate_capability_state_owner(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    capability["state_owner"] = "shared_ledger_owned_pointer"


def mutate_ledger_state_owner(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    ledger["state_owner"] = "source_owned_shared_capability_state"


def mutate_recreation(root: pathlib.Path, manifest: dict[str, object]) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    capability["endpoint_recreation"] = "reuse_matching_state"


def mutate_endpoint_security_identity(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    recreation = capability["endpoint_recreation"]
    assert isinstance(recreation, dict)
    recreation["security_identity"] = "endpoint_generation_and_string"


def mutate_issued_lifecycle(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    lifecycle = capability["issued_lifecycle"]
    assert isinstance(lifecycle, dict)
    terminal = lifecycle["terminal"]
    assert isinstance(terminal, list)
    terminal.append("not-issued")


def mutate_capability_transition(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    lifecycle = capability["issued_lifecycle"]
    assert isinstance(lifecycle, dict)
    transitions = lifecycle["legal_transitions"]
    assert isinstance(transitions, list)
    transitions.append("claimed_to_open")


def mutate_capability_reclamation(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    lifecycle = capability["issued_lifecycle"]
    assert isinstance(lifecycle, dict)
    reclamation = lifecycle["reclamation"]
    assert isinstance(reclamation, dict)
    reclamation["mode"] = "caller_driven_eventually"


def mutate_coalesced_cardinality(root: pathlib.Path, manifest: dict[str, object]) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    capability["coalesced_dependents"] = "one_capability_per_physical_read"


def mutate_race(root: pathlib.Path, manifest: dict[str, object]) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    capability["copied_view_race"] = "multiple_winners_allowed"


def mutate_cancel_open_owner(root: pathlib.Path, manifest: dict[str, object]) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    binding = capability["attempt_binding"]
    assert isinstance(binding, dict)
    cancel_open = binding["cancel_open"]
    assert isinstance(cancel_open, dict)
    cancel_open["owner"] = "m2_ledger"


def mutate_capability_terminal_sequence(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    bounds = capability["bounded_state"]
    assert isinstance(bounds, dict)
    sequence = bounds["terminal_sequence"]
    assert isinstance(sequence, dict)
    sequence["wrap"] = "allowed"


def mutate_capability_tombstone_schema(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    bounds = capability["bounded_state"]
    assert isinstance(bounds, dict)
    tombstone = bounds["tombstone"]
    assert isinstance(tombstone, dict)
    fields = tombstone["fields"]
    assert isinstance(fields, list)
    fields.append("source_evidence_id")


def mutate_capability_tombstone_byte_bound(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    bounds = capability["bounded_state"]
    assert isinstance(bounds, dict)
    tombstone = bounds["tombstone"]
    assert isinstance(tombstone, dict)
    tombstone["max_encoded_bytes"] = "unbounded"


def mutate_reclamation(root: pathlib.Path, manifest: dict[str, object]) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    bounds = capability["bounded_state"]
    assert isinstance(bounds, dict)
    bounds["terminal_reclamation"] = "optional"


def mutate_duplicate_attempt(root: pathlib.Path, manifest: dict[str, object]) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    ledger["attempt_key"] = "last_writer_wins"


def mutate_attempt_key_bound(root: pathlib.Path, manifest: dict[str, object]) -> None:
    bounded = manifest["bounded_values"]
    assert isinstance(bounded, dict)
    attempt_key = bounded["attempt_key"]
    assert isinstance(attempt_key, dict)
    attempt_key["max"] = "unbounded"


def mutate_diagnostic_bound(root: pathlib.Path, manifest: dict[str, object]) -> None:
    bounded = manifest["bounded_values"]
    assert isinstance(bounded, dict)
    diagnostics = bounded["retained_diagnostics"]
    assert isinstance(diagnostics, dict)
    diagnostics["count_max"] = "unbounded"


def mutate_publish(root: pathlib.Path, manifest: dict[str, object]) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    ledger["publish"] = "mutable_dto_allowed"


def mutate_claim_lifecycle(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    lifecycle = ledger["claim_entry_lifecycle"]
    assert isinstance(lifecycle, dict)
    lifecycle["retry"] = "allowed"


def mutate_claim_admission(root: pathlib.Path, manifest: dict[str, object]) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    lifecycle = ledger["claim_entry_lifecycle"]
    assert isinstance(lifecycle, dict)
    lifecycle["admission"] = "claim_without_attempt_state_check"


def mutate_claim_finalization(root: pathlib.Path, manifest: dict[str, object]) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    lifecycle = ledger["claim_entry_lifecycle"]
    assert isinstance(lifecycle, dict)
    lifecycle["finalization"] = "attempt_cancellation_may_overwrite"


def mutate_cancellation_protocol(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    cancellation = ledger["cancellation_protocol"]
    assert isinstance(cancellation, dict)
    cancellation["drain"] = "cancel_without_waiting_for_claims"


def mutate_attempt_transition(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    lifecycle = ledger["attempt_lifecycle"]
    assert isinstance(lifecycle, dict)
    transitions = lifecycle["legal_transitions"]
    assert isinstance(transitions, list)
    transitions.append("publish_failed_to_publishing")


def mutate_publish_one_shot(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    lifecycle = ledger["attempt_lifecycle"]
    assert isinstance(lifecycle, dict)
    lifecycle["publish"] = "retryable"


def mutate_seal_condition(root: pathlib.Path, manifest: dict[str, object]) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    lifecycle = ledger["attempt_lifecycle"]
    assert isinstance(lifecycle, dict)
    lifecycle["seal_condition"] = "all_claim_entries_terminal"


def mutate_retained_bounds(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    bounds = ledger["bounds"]
    assert isinstance(bounds, dict)
    covered = bounds["covered_attempt_states"]
    assert isinstance(covered, list)
    covered.remove("publish_failed")


def mutate_cancelling_attempt_bound(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    bounds = ledger["bounds"]
    assert isinstance(bounds, dict)
    covered = bounds["covered_attempt_states"]
    assert isinstance(covered, list)
    covered.remove("cancelling")


def mutate_in_progress_claim_bound(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    bounds = ledger["bounds"]
    assert isinstance(bounds, dict)
    covered = bounds["covered_claim_states"]
    assert isinstance(covered, list)
    covered.remove("claim_in_progress")


def mutate_ledger_terminal_sequence(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    bounds = ledger["bounds"]
    assert isinstance(bounds, dict)
    sequence = bounds["terminal_sequence"]
    assert isinstance(sequence, dict)
    sequence["exhaustion"] = "wrap_to_one"


def mutate_ledger_reclamation(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    reclamation = ledger["reclamation"]
    assert isinstance(reclamation, dict)
    tombstone = reclamation["audit_tombstone"]
    assert isinstance(tombstone, dict)
    tombstone["eviction"] = "random"


def mutate_ledger_tombstone_schema(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    reclamation = ledger["reclamation"]
    assert isinstance(reclamation, dict)
    tombstone = reclamation["audit_tombstone"]
    assert isinstance(tombstone, dict)
    variants = tombstone["variants"]
    assert isinstance(variants, dict)
    claim = variants["claim"]
    assert isinstance(claim, dict)
    fields = claim["fields"]
    assert isinstance(fields, list)
    fields.append("normalization_record")


def mutate_ledger_tombstone_attempt_key_digest_ban(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    reclamation = ledger["reclamation"]
    assert isinstance(reclamation, dict)
    tombstone = reclamation["audit_tombstone"]
    assert isinstance(tombstone, dict)
    forbidden_payloads = tombstone["forbidden_payloads"]
    assert isinstance(forbidden_payloads, list)
    forbidden_payloads.remove("attempt_key_digest")


def mutate_ledger_tombstone_byte_bound(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    reclamation = ledger["reclamation"]
    assert isinstance(reclamation, dict)
    tombstone = reclamation["audit_tombstone"]
    assert isinstance(tombstone, dict)
    tombstone["max_encoded_bytes"] = "unbounded"


def mutate_normalization_field(root: pathlib.Path, manifest: dict[str, object]) -> None:
    record = manifest["normalization_record"]
    assert isinstance(record, dict)
    fields = record["required_fields"]
    assert isinstance(fields, list)
    fields.remove("source_evidence_id")


def mutate_normalization_loss(root: pathlib.Path, manifest: dict[str, object]) -> None:
    record = manifest["normalization_record"]
    assert isinstance(record, dict)
    record["unknown_extension_fields"] = "discarded"


def mutate_source_evidence_bound(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    record = manifest["normalization_record"]
    assert isinstance(record, dict)
    bounds = record["bounds"]
    assert isinstance(bounds, dict)
    source_evidence = bounds["source_evidence_id"]
    assert isinstance(source_evidence, dict)
    source_evidence["max"] = "unbounded"


def mutate_normalization_encoded_bound(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    record = manifest["normalization_record"]
    assert isinstance(record, dict)
    bounds = record["bounds"]
    assert isinstance(bounds, dict)
    bounds["encoded_record_max"] = "unbounded"


def mutate_extension_count_bound(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    record = manifest["normalization_record"]
    assert isinstance(record, dict)
    bounds = record["bounds"]
    assert isinstance(bounds, dict)
    extensions = bounds["unknown_extensions"]
    assert isinstance(extensions, dict)
    extensions["count_max"] = "unbounded"


def mutate_extension_key_bound(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    record = manifest["normalization_record"]
    assert isinstance(record, dict)
    bounds = record["bounds"]
    assert isinstance(bounds, dict)
    extensions = bounds["unknown_extensions"]
    assert isinstance(extensions, dict)
    extensions["key"] = "unbounded_utf8"


def mutate_extension_value_bound(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    record = manifest["normalization_record"]
    assert isinstance(record, dict)
    bounds = record["bounds"]
    assert isinstance(bounds, dict)
    extensions = bounds["unknown_extensions"]
    assert isinstance(extensions, dict)
    extensions["value_max"] = "unbounded"


def mutate_downstream_docs_lock(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    conformance = manifest["downstream_conformance"]
    assert isinstance(conformance, dict)
    lock = conformance["docs_lock"]
    assert isinstance(lock, list)
    lock.remove("manifest_sha256")


def mutate_attempt_instance_identity(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    instance = capability["attempt_instance"]
    assert isinstance(instance, dict)
    instance["identity"] = "reusable_AttemptKey"


def mutate_attempt_membership_close(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    instance = capability["attempt_instance"]
    assert isinstance(instance, dict)
    membership = instance["membership"]
    assert isinstance(membership, dict)
    membership["close"] = "scan_without_blocking_registration"


def mutate_cancel_instance_lookup(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    capability = manifest["opaque_capability"]
    assert isinstance(capability, dict)
    binding = capability["attempt_binding"]
    assert isinstance(binding, dict)
    cancel_open = binding["cancel_open"]
    assert isinstance(cancel_open, dict)
    cancel_open["lookup"] = "AttemptKey_only"


def mutate_dependency_set_order(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    dependency_set = ledger["dependency_set"]
    assert isinstance(dependency_set, dict)
    dependency_set["order"] = "unordered_map_iteration"


def mutate_dependency_set_byte_bound(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    bounds = ledger["bounds"]
    assert isinstance(bounds, dict)
    bounds["dependency_set_encoded_bytes"] = "unbounded"


def mutate_seal_forbidden_sets(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    lifecycle = ledger["attempt_lifecycle"]
    assert isinstance(lifecycle, dict)
    lifecycle["seal_forbidden_sets"] = "empty_and_fixture_allowed"


def mutate_publish_commit_linearization(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    lifecycle = ledger["attempt_lifecycle"]
    assert isinstance(lifecycle, dict)
    lifecycle["publish_commit_linearization"] = "external_effect_before_state"


def mutate_published_projection_leak(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    ledger = manifest["m2_ledger"]
    assert isinstance(ledger, dict)
    projection = ledger["published_projection"]
    assert isinstance(projection, dict)
    fields = projection["fields"]
    assert isinstance(fields, list)
    fields.append("source_evidence_id")


Mutation = Callable[[pathlib.Path, dict[str, object]], None]


@pytest.mark.parametrize(
    "mutation",
    (
        mutate_extra_source_kind,
        mutate_runtime_issuance,
        mutate_deliverability_exclusion,
        mutate_fixture_capability,
        mutate_fixture_cas,
        mutate_fixture_sample,
        mutate_copy_semantics,
        mutate_capability_state_owner,
        mutate_ledger_state_owner,
        mutate_recreation,
        mutate_endpoint_security_identity,
        mutate_issued_lifecycle,
        mutate_capability_transition,
        mutate_capability_reclamation,
        mutate_coalesced_cardinality,
        mutate_race,
        mutate_cancel_open_owner,
        mutate_capability_terminal_sequence,
        mutate_capability_tombstone_schema,
        mutate_capability_tombstone_byte_bound,
        mutate_reclamation,
        mutate_duplicate_attempt,
        mutate_attempt_key_bound,
        mutate_diagnostic_bound,
        mutate_publish,
        mutate_claim_lifecycle,
        mutate_claim_admission,
        mutate_claim_finalization,
        mutate_cancellation_protocol,
        mutate_attempt_transition,
        mutate_publish_one_shot,
        mutate_seal_condition,
        mutate_retained_bounds,
        mutate_cancelling_attempt_bound,
        mutate_in_progress_claim_bound,
        mutate_ledger_terminal_sequence,
        mutate_ledger_reclamation,
        mutate_ledger_tombstone_schema,
        mutate_ledger_tombstone_attempt_key_digest_ban,
        mutate_ledger_tombstone_byte_bound,
        mutate_normalization_field,
        mutate_normalization_loss,
        mutate_source_evidence_bound,
        mutate_normalization_encoded_bound,
        mutate_extension_count_bound,
        mutate_extension_key_bound,
        mutate_extension_value_bound,
        mutate_downstream_docs_lock,
        mutate_attempt_instance_identity,
        mutate_attempt_membership_close,
        mutate_cancel_instance_lookup,
        mutate_dependency_set_order,
        mutate_dependency_set_byte_bound,
        mutate_seal_forbidden_sets,
        mutate_publish_commit_linearization,
        mutate_published_projection_leak,
    ),
)
def test_closed_manifest_mutations_fail(
    tmp_path: pathlib.Path, mutation: Mutation
) -> None:
    root = materialize_fixture(tmp_path)
    manifest = load_manifest(root)
    mutation(root, manifest)
    write_manifest(root, manifest)
    result = run_validator(root)
    assert result.returncode != 0
    assert "opaque_runtime_acquisition_contract_invalid" in result.stderr


def test_policy_alteration_fails_even_when_manifest_hash_is_refreshed(
    tmp_path: pathlib.Path,
) -> None:
    root = materialize_fixture(tmp_path)
    policy = root / POLICY
    policy.write_text(
        policy.read_text(encoding="utf-8") + "\nWeakened wording.\n",
        encoding="utf-8",
    )
    manifest = load_manifest(root)
    refresh_policy_hash(root, manifest)
    write_manifest(root, manifest)
    result = run_validator(root)
    assert result.returncode != 0
    assert "policy artifact bytes do not match OPAQUE_RUNTIME_ACQUISITION_V1" in result.stderr


@pytest.mark.parametrize("term", contract_validator.EXPECTED_REQUIRED_TERMS)
def test_each_required_normative_term_has_independent_diagnostic(
    tmp_path: pathlib.Path, term: str
) -> None:
    root = materialize_fixture(tmp_path)
    policy = root / POLICY
    policy_text = policy.read_text(encoding="utf-8")
    assert term in policy_text
    policy.write_text(policy_text.replace(term, "removed"), encoding="utf-8")
    manifest = load_manifest(root)
    refresh_policy_hash(root, manifest)
    write_manifest(root, manifest)
    digest = hashlib.sha256(policy.read_bytes()).hexdigest()
    errors, _ = contract_validator.validate(
        root.resolve(),
        expected_policy_sha256=digest,
        required_terms=(term,),
    )
    assert errors == [f"policy missing required normative term: {term}"]


def test_required_term_loop_canary_fails_when_term_is_absent(
    tmp_path: pathlib.Path,
) -> None:
    root = materialize_fixture(tmp_path)
    digest = hashlib.sha256((root / POLICY).read_bytes()).hexdigest()
    canary = "required-term-loop-canary-that-is-not-in-policy"
    errors, _ = contract_validator.validate(
        root.resolve(),
        expected_policy_sha256=digest,
        required_terms=(canary,),
    )
    assert errors == [f"policy missing required normative term: {canary}"]


@pytest.mark.parametrize(
    "hidden_wrapper",
    (
        "<!-- {term} -->",
        "```markdown\n{term}\n```",
        "`{term}`",
        "    {term}",
        '[hidden](./x "{term}")',
        '[hidden](./x "prefix \\"{term}\\" suffix")',
        '[hidden\\]](./x "{term}")',
        '[hidden](<./hidden target> "{term}")',
        '[hidden](<{term}>)',
        '![{term}](./hidden.png)',
        '[hidden]: ./x "{term}"',
        '[hidden\\]]: ./x "{term}"',
        '[hidden]: ./x\n  "{term}"',
    ),
)
def test_required_terms_in_nonvisible_markdown_do_not_satisfy_contract(
    tmp_path: pathlib.Path, hidden_wrapper: str
) -> None:
    root = materialize_fixture(tmp_path)
    policy = root / POLICY
    term = "The capability is source-issued, opaque, and non-serializable"
    policy_text = policy.read_text(encoding="utf-8")
    assert term in policy_text
    policy.write_text(
        policy_text.replace(term, "removed") + "\n" + hidden_wrapper.format(term=term),
        encoding="utf-8",
    )
    manifest = load_manifest(root)
    refresh_policy_hash(root, manifest)
    write_manifest(root, manifest)
    digest = hashlib.sha256(policy.read_bytes()).hexdigest()
    errors, _ = contract_validator.validate(
        root.resolve(),
        expected_policy_sha256=digest,
        required_terms=(term,),
    )
    assert errors == [f"policy missing required normative term: {term}"]


@pytest.mark.parametrize(
    ("index_path", "destination"),
    (
        (PLATFORM_INDEX, "./opaque-runtime-acquisition-v1.md"),
        (
            PLATFORM_INDEX,
            "./manifests/opaque-runtime-acquisition-v1.json",
        ),
        (ROOT_INDEX, "docs/platform/opaque-runtime-acquisition-v1.md"),
        (
            ROOT_INDEX,
            "docs/platform/manifests/opaque-runtime-acquisition-v1.json",
        ),
    ),
)
def test_discoverability_link_removal_fails_closed(
    tmp_path: pathlib.Path, index_path: pathlib.Path, destination: str
) -> None:
    root = materialize_fixture(tmp_path)
    index = root / index_path
    text = index.read_text(encoding="utf-8")
    assert destination in text
    index.write_text(text.replace(destination, "removed"), encoding="utf-8")
    result = run_validator(root)
    assert result.returncode != 0
    assert "missing visible discoverability link" in result.stderr


@pytest.mark.parametrize(
    "hidden_wrapper",
    (
        "<!-- [hidden]({destination}) -->",
        "```markdown\n[hidden]({destination})\n```",
        "`[hidden]({destination})`",
        "    [hidden]({destination})",
    ),
)
def test_hidden_or_code_only_discoverability_link_fails_closed(
    tmp_path: pathlib.Path, hidden_wrapper: str
) -> None:
    root = materialize_fixture(tmp_path)
    index = root / PLATFORM_INDEX
    destination = "./opaque-runtime-acquisition-v1.md"
    text = index.read_text(encoding="utf-8")
    visible_link = (
        "[`opaque-runtime-acquisition-v1.md`]"
        "(./opaque-runtime-acquisition-v1.md)"
    )
    assert visible_link in text
    replacement = hidden_wrapper.format(destination=destination)
    rewritten_lines = [
        replacement if visible_link in line else line
        for line in text.splitlines()
    ]
    index.write_text(
        "\n".join(rewritten_lines) + "\n",
        encoding="utf-8",
    )
    result = run_validator(root)
    assert result.returncode != 0
    assert (
        "missing visible discoverability link: "
        "./opaque-runtime-acquisition-v1.md"
    ) in result.stderr


def test_empty_discoverability_link_label_fails_closed(
    tmp_path: pathlib.Path,
) -> None:
    root = materialize_fixture(tmp_path)
    index = root / PLATFORM_INDEX
    destination = "./opaque-runtime-acquisition-v1.md"
    visible_link = (
        "[`opaque-runtime-acquisition-v1.md`]"
        "(./opaque-runtime-acquisition-v1.md)"
    )
    text = index.read_text(encoding="utf-8")
    assert visible_link in text
    index.write_text(
        text.replace(visible_link, f"[]({destination})"),
        encoding="utf-8",
    )
    result = run_validator(root)
    assert result.returncode != 0
    assert (
        "missing visible discoverability link: "
        "./opaque-runtime-acquisition-v1.md"
    ) in result.stderr


def test_wrong_discoverability_target_fails_closed(
    tmp_path: pathlib.Path,
) -> None:
    root = materialize_fixture(tmp_path)
    index = root / PLATFORM_INDEX
    expected = "./opaque-runtime-acquisition-v1.md"
    wrong = "./manifests/opaque-runtime-acquisition-v1.json"
    text = index.read_text(encoding="utf-8")
    index.write_text(text.replace(expected, wrong), encoding="utf-8")
    result = run_validator(root)
    assert result.returncode != 0
    assert f"missing visible discoverability link: {expected}" in result.stderr


def test_missing_discoverability_target_fails_closed(
    tmp_path: pathlib.Path,
) -> None:
    root = materialize_fixture(tmp_path)
    (root / POLICY).unlink()
    errors: list[str] = []
    contract_validator._validate_discoverability(root.resolve(), errors)
    assert (
        "docs/platform/README.md discoverability target is not a regular "
        "in-repo file: ./opaque-runtime-acquisition-v1.md"
    ) in errors
    assert (
        "README.md discoverability target is not a regular in-repo file: "
        "docs/platform/opaque-runtime-acquisition-v1.md"
    ) in errors


def test_symlinked_discoverability_target_fails_closed(
    tmp_path: pathlib.Path,
) -> None:
    root = materialize_fixture(tmp_path)
    manifest = root / MANIFEST
    replacement = manifest.with_name("replacement.json")
    replacement.write_bytes(manifest.read_bytes())
    manifest.unlink()
    manifest.symlink_to(replacement.name)
    errors: list[str] = []
    contract_validator._validate_discoverability(root.resolve(), errors)
    assert (
        "docs/platform/README.md discoverability target is not a regular "
        "in-repo file: ./manifests/opaque-runtime-acquisition-v1.json"
    ) in errors
    assert (
        "README.md discoverability target is not a regular in-repo file: "
        "docs/platform/manifests/opaque-runtime-acquisition-v1.json"
    ) in errors


def test_initial_v1_allows_prior_root_without_artifact(
    tmp_path: pathlib.Path,
) -> None:
    current = materialize_fixture(tmp_path / "current")
    prior = tmp_path / "prior"
    prior.mkdir()
    result = run_validator(current, prior_root=prior)
    assert result.returncode == 0, result.stdout + result.stderr


def test_missing_prior_root_fails_closed(tmp_path: pathlib.Path) -> None:
    current = materialize_fixture(tmp_path / "current")
    result = run_validator(current, prior_root=tmp_path / "missing-prior")
    assert result.returncode != 0
    assert "prior root must be an existing regular directory" in result.stderr


def test_symlinked_prior_root_fails_closed(tmp_path: pathlib.Path) -> None:
    current = materialize_fixture(tmp_path / "current")
    prior = materialize_fixture(tmp_path / "prior")
    prior_link = tmp_path / "prior-link"
    prior_link.symlink_to(prior, target_is_directory=True)
    result = run_validator(current, prior_root=prior_link)
    assert result.returncode != 0
    assert "prior root must be an existing regular directory" in result.stderr


def test_current_root_cannot_be_its_own_prior_root(
    tmp_path: pathlib.Path,
) -> None:
    current = materialize_fixture(tmp_path / "current")
    result = run_validator(current, prior_root=current)
    assert result.returncode != 0
    assert "prior root must differ from current root" in result.stderr


def test_symlinked_prior_root_ancestor_fails_closed(
    tmp_path: pathlib.Path,
) -> None:
    current = materialize_fixture(tmp_path / "current")
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    result = run_validator(current, prior_root=alias / "current")
    assert result.returncode != 0
    assert "prior root must be an existing regular directory" in result.stderr


def test_symlinked_prior_artifact_ancestor_fails_closed(
    tmp_path: pathlib.Path,
) -> None:
    current = materialize_fixture(tmp_path / "current")
    prior = materialize_fixture(tmp_path / "prior")
    prior_platform = prior / "docs/platform"
    shutil.rmtree(prior_platform)
    prior_platform.symlink_to(
        current / "docs/platform",
        target_is_directory=True,
    )
    result = run_validator(current, prior_root=prior)
    assert result.returncode != 0
    assert "prior opaque manifest must be a regular file" in result.stderr


def test_dangling_prior_manifest_symlink_fails_closed(
    tmp_path: pathlib.Path,
) -> None:
    current = materialize_fixture(tmp_path / "current")
    prior = tmp_path / "prior"
    prior_manifest = prior / MANIFEST
    prior_manifest.parent.mkdir(parents=True)
    prior_manifest.symlink_to(prior / "missing-manifest.json")
    result = run_validator(current, prior_root=prior)
    assert result.returncode != 0
    assert "prior opaque manifest must be a regular file" in result.stderr


def test_prior_root_without_artifact_rejects_noninitial_revision(
    tmp_path: pathlib.Path,
) -> None:
    current = materialize_fixture(tmp_path / "current")
    prior = tmp_path / "prior"
    prior.mkdir()
    manifest = load_manifest(current)
    manifest["content_revision"] = 2
    write_manifest(current, manifest)
    result = run_validator(current, prior_root=prior)
    assert result.returncode != 0
    assert (
        "an initial opaque runtime acquisition contract must be "
        "OPAQUE_RUNTIME_ACQUISITION_V1 revision 1"
    ) in result.stderr


def test_same_v1_revision_is_byte_identical_against_prior(
    tmp_path: pathlib.Path,
) -> None:
    current = materialize_fixture(tmp_path / "current")
    prior = materialize_fixture(tmp_path / "prior")
    result = run_validator(current, prior_root=prior)
    assert result.returncode == 0, result.stdout + result.stderr


def test_coordinated_v1_policy_manifest_validator_edit_fails_against_prior(
    tmp_path: pathlib.Path,
) -> None:
    prior = materialize_fixture(tmp_path / "prior")
    current = materialize_fixture(tmp_path / "current")
    policy = current / POLICY
    policy.write_text(
        policy.read_text(encoding="utf-8") + "\nCoordinated semantic edit.\n",
        encoding="utf-8",
    )
    manifest = load_manifest(current)
    refresh_policy_hash(current, manifest)
    write_manifest(current, manifest)
    validator_path = current / VALIDATOR
    validator_text = validator_path.read_text(encoding="utf-8")
    old_digest = contract_validator.EXPECTED_POLICY_SHA256
    new_digest = hashlib.sha256(policy.read_bytes()).hexdigest()
    assert old_digest in validator_text
    validator_path.write_text(
        validator_text.replace(old_digest, new_digest),
        encoding="utf-8",
    )
    result = run_validator(current, prior_root=prior)
    assert result.returncode != 0
    assert (
        "existing OPAQUE_RUNTIME_ACQUISITION_V1 revision 1 must remain "
        "byte-identical; semantic changes require a new versioned artifact "
        "and contract"
    ) in result.stderr


def test_validator_only_edit_fails_against_same_prior_revision(
    tmp_path: pathlib.Path,
) -> None:
    prior = materialize_fixture(tmp_path / "prior")
    current = materialize_fixture(tmp_path / "current")
    validator_path = current / VALIDATOR
    validator_path.write_text(
        validator_path.read_text(encoding="utf-8")
        + "\n# semantic validator edit\n",
        encoding="utf-8",
    )
    result = run_validator(current, prior_root=prior)
    assert result.returncode != 0
    assert str(VALIDATOR) in result.stderr
