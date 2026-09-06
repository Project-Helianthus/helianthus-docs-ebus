from __future__ import annotations

import importlib.util
import hashlib
import json
import pathlib
import shutil
from copy import deepcopy

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / "scripts/check_regulator_identity_contract.py"
POLICY_RELATIVE = pathlib.Path("architecture/regulator-qualified-identity-policy.json")
HISTORICAL_V1_FIXTURE_RELATIVE = pathlib.Path(
    "tests/fixtures/regulator-qualified-identity-policy/accepted-base-v1.json"
)
ACCEPTED_BASE = "7993385c7f07b37dd7fa1d7dae67a49bddb17443"
ACCEPTED_BASE_V1_BLOB = "46b38fbb7920bed511eeee057a4df9eff3de7d14"
ACCEPTED_BASE_V1_SHA256 = "886dd57e72c46805ac762f0150b9ff8ee59970a594665cb9ea80c9aeb48f97ae"


def load_checker():
    spec = importlib.util.spec_from_file_location("regulator_identity_checker", CHECKER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_contract_material(destination: pathlib.Path) -> None:
    for relative in (
        POLICY_RELATIVE,
        pathlib.Path("architecture/regulator-identity-enrichment.md"),
        pathlib.Path("architecture/atr/01-address-table-model.md"),
        pathlib.Path("architecture/atr/03-ack-nack-insertion-rules.md"),
        pathlib.Path("architecture/atr/04-sn-merge-gate.md"),
        pathlib.Path("architecture/atr/07-live-validation-acceptance.md"),
        pathlib.Path("architecture/overview.md"),
        pathlib.Path("api/graphql.md"),
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, target)


def read_policy(root: pathlib.Path) -> dict[str, object]:
    return json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))


def read_historical_v1_fixture() -> dict[str, object]:
    return json.loads((REPO_ROOT / HISTORICAL_V1_FIXTURE_RELATIVE).read_text(encoding="utf-8"))


def write_policy(root: pathlib.Path, policy: dict[str, object]) -> None:
    (root / POLICY_RELATIVE).write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")


def test_qualified_identity_policy_accepts_current_public_contract(tmp_path: pathlib.Path) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)

    checker.validate_documents(tmp_path)


def test_qualified_identity_policy_preserves_triple_and_normalization_rules(tmp_path: pathlib.Path) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)

    policy = read_policy(tmp_path)
    assert policy["instance"] == checker.CONSUMER_WITNESS_INSTANCE
    assert policy["identity"] == {
        "members": ["Manufacturer", "DeviceID", "SerialNumber"],
        "match": "exact_normalized_triple",
        "empty_or_partial": "not_qualified",
        "named_sentinel_serials": ["0", "0x00000000", "0xFFFFFFFF", "0x7FFFFFFF"],
        "sentinel_recognition": {
            "scope": "named_hexadecimal_sentinels_only",
            "case": "insensitive",
            "prefix": "optional_single_0x",
            "leading_zeros": "ignore",
            "ordinary_serials": "never_parse_or_rewrite",
        },
        "sentinel_serials": "not_qualified",
        "non_qualifying_signals": ["serial", "mac", "model", "topology", "address_cooccurrence"],
    }
    assert policy["normalization"] == {
        "fixed_width_device_id_decoder": ["remove_terminal_nul", "remove_terminal_ascii_space"],
        "registry": {
            "members": ["Manufacturer", "DeviceID", "SerialNumber"],
            "outer_unicode_whitespace": "trim",
            "case": "uppercase",
            "internal_whitespace": "preserve",
            "internal_punctuation": "preserve",
            "deviceid_vr_71_vs_vr71": "distinct",
        },
    }
    witness = policy["consumer_witness"]
    assert witness["kind"] == "qualified_identity_consumer_witness_v2"  # type: ignore[index]
    assert witness["allowed_values"] == checker.CONSUMER_WITNESS_ALLOWED_VALUES  # type: ignore[index]
    assert witness["current_registry_state"] == {  # type: ignore[index]
        "required_fields": checker.CURRENT_REGISTRY_STATE_REQUIRED_FIELDS,
        "allowed_values": checker.CURRENT_REGISTRY_STATE_ALLOWED_VALUES,
    }
    assert witness["production"] == checker.CONSUMER_WITNESS_PRODUCTION  # type: ignore[index]
    assert witness["currentness"] == checker.CONSUMER_WITNESS_CURRENTNESS  # type: ignore[index]
    assert witness["stale_on"] == ["replacement", "retirement", "conflict"]  # type: ignore[index]
    assert witness["companion_corroboration"] == "same_source_positive_ack_plus_current_exact_address_witness"  # type: ignore[index]
    assert witness["companion_insertion"] == "must_insert"  # type: ignore[index]
    fixtures = witness["validation_fixtures"]  # type: ignore[index]
    assert {fixture["name"] for fixture in fixtures} == checker.CONSUMER_WITNESS_FIXTURE_NAMES
    assert [fixture["name"] for fixture in fixtures if fixture["current"]] == ["current_exact_address"]
    checker.validate_documents(tmp_path)


def test_historical_v1_fixture_is_exact_accepted_base_policy() -> None:
    historical_bytes = (REPO_ROOT / HISTORICAL_V1_FIXTURE_RELATIVE).read_bytes()
    git_blob = hashlib.sha1(
        f"blob {len(historical_bytes)}\0".encode("ascii") + historical_bytes,
        usedforsecurity=False,
    ).hexdigest()

    assert ACCEPTED_BASE == "7993385c7f07b37dd7fa1d7dae67a49bddb17443"
    assert git_blob == ACCEPTED_BASE_V1_BLOB
    assert hashlib.sha256(historical_bytes).hexdigest() == ACCEPTED_BASE_V1_SHA256


def test_schema_version_dispatch_accepts_only_its_own_closed_shape() -> None:
    checker = load_checker()
    current_v2 = read_policy(REPO_ROOT)
    historical_v1 = read_historical_v1_fixture()

    checker.validate_policy_versioned(historical_v1, HISTORICAL_V1_FIXTURE_RELATIVE)
    checker.validate_policy_versioned(current_v2, POLICY_RELATIVE)

    with pytest.raises(checker.CheckError, match=r"missing=\['consumer_witness', 'instance'\]"):
        checker.validate_current_v2_policy(historical_v1, HISTORICAL_V1_FIXTURE_RELATIVE)
    with pytest.raises(checker.CheckError, match=r"expected exact fields; missing=\[\], unknown=\['consumer_witness', 'instance'\]"):
        checker.validate_historical_v1_policy(current_v2, POLICY_RELATIVE)


def test_current_v2_checker_rejects_expanded_shape_mislabeled_v1() -> None:
    checker = load_checker()
    expanded_v1 = read_policy(REPO_ROOT)
    expanded_v1["schema_version"] = 1

    with pytest.raises(checker.CheckError, match="expected 2"):
        checker.validate_current_v2_policy(expanded_v1, POLICY_RELATIVE)
    with pytest.raises(checker.CheckError, match=r"unknown=\['consumer_witness', 'instance'\]"):
        checker.validate_policy_versioned(expanded_v1, POLICY_RELATIVE)


def test_current_v2_checker_rejects_historical_shape_mislabeled_v2() -> None:
    checker = load_checker()
    historical_v2 = read_historical_v1_fixture()
    historical_v2["schema_version"] = 2

    with pytest.raises(checker.CheckError, match=r"missing=\['consumer_witness', 'instance'\]"):
        checker.validate_policy_versioned(historical_v2, HISTORICAL_V1_FIXTURE_RELATIVE)


@pytest.mark.parametrize(
    ("schema_version", "error"),
    (
        (0, "unsupported schema version 0"),
        (3, "unsupported schema version 3"),
        (True, "expected integer schema version"),
        ("2", "expected integer schema version"),
        (2.0, "expected integer schema version"),
        (1.5, "expected integer schema version"),
    ),
)
def test_schema_version_dispatch_rejects_unsupported_boolean_and_nonintegral_versions(
    schema_version: object, error: str
) -> None:
    checker = load_checker()
    policy = read_policy(REPO_ROOT)
    policy["schema_version"] = schema_version

    with pytest.raises(checker.CheckError, match=error):
        checker.validate_policy_versioned(policy, POLICY_RELATIVE)


def current_witness_pair() -> tuple[dict[str, object], dict[str, object]]:
    authority: dict[str, object] = {
        "Manufacturer": "ACME",
        "DeviceID": "VR_71",
        "SerialNumber": "SN-1",
    }
    return (
        {
            "address": "0x10",
            "identity_authority": authority,
            "observation_provenance": "direct_observation",
            "current": True,
            "immutable": True,
            "registry_observation_generation": 7,
            "registry_proof_generation": 11,
        },
        {
            "availability": "available",
            "address": "0x10",
            "identity_authority": deepcopy(authority),
            "registry_observation_generation": 7,
            "registry_proof_generation": 11,
        },
    )


@pytest.mark.parametrize(
    "address",
    (
        [],
        16,
        "not-an-ebus-address",
        "0x1",
        "0X10",
        "0x100",
        "0xA9",
        "0xAA",
        "0xFE",
    ),
)
def test_consumer_witness_rejects_noncanonical_or_nonunicast_addresses(address: object) -> None:
    checker = load_checker()
    witness, current_state = current_witness_pair()
    witness["address"] = address
    current_state["address"] = deepcopy(address)

    with pytest.raises(checker.CheckError, match="address"):
        checker.consumer_witness_is_current(witness, current_state)


@pytest.mark.parametrize(
    ("member", "value"),
    (
        ("Manufacturer", "\u2003ACME\u2003"),
        ("Manufacturer", "acme"),
        ("DeviceID", "VR_71 "),
        ("DeviceID", "vr_71"),
        ("DeviceID", "VR_71\x00"),
        ("SerialNumber", "SN-1 "),
        ("SerialNumber", "sn-1"),
    ),
)
def test_consumer_witness_rejects_non_normalized_authority_members(member: str, value: str) -> None:
    checker = load_checker()
    witness, current_state = current_witness_pair()
    witness["identity_authority"][member] = value  # type: ignore[index]
    current_state["identity_authority"][member] = value  # type: ignore[index]

    with pytest.raises(checker.CheckError, match="already-normalized|fixed-width"):
        checker.consumer_witness_is_current(witness, current_state)


def test_consumer_witness_preserves_internal_punctuation_as_distinct_identity() -> None:
    checker = load_checker()
    witness, current_state = current_witness_pair()
    current_state["identity_authority"]["DeviceID"] = "VR71"  # type: ignore[index]

    assert checker.consumer_witness_is_current(witness, current_state) is False


@pytest.mark.parametrize("serial", ("0", "0x00000000", "0xFFFFFFFF", "0x7FFFFFFF"))
def test_consumer_witness_rejects_each_named_sentinel_serial(serial: str) -> None:
    checker = load_checker()
    witness, current_state = current_witness_pair()
    witness["identity_authority"]["SerialNumber"] = serial  # type: ignore[index]
    current_state["identity_authority"]["SerialNumber"] = serial  # type: ignore[index]

    with pytest.raises(checker.CheckError, match="sentinel serial"):
        checker.consumer_witness_is_current(witness, current_state)


@pytest.mark.parametrize(
    "serial",
    (
        "000",
        "0X00000000",
        "ffffffff",
        "00000000FFFFFFFF",
        "0X000000007fffffff",
    ),
)
def test_named_sentinel_recognition_is_case_insensitive_with_optional_prefix_and_leading_zeroes(serial: str) -> None:
    checker = load_checker()

    assert checker.is_named_sentinel_serial(serial) is True


def test_consumer_witness_preserves_ordinary_serial_spelling_without_parsing_or_rewriting() -> None:
    checker = load_checker()
    witness, current_state = current_witness_pair()
    witness["identity_authority"]["SerialNumber"] = "000A1"  # type: ignore[index]
    current_state["identity_authority"]["SerialNumber"] = "000A1"  # type: ignore[index]

    assert checker.consumer_witness_is_current(witness, current_state) is True
    assert witness["identity_authority"]["SerialNumber"] == "000A1"  # type: ignore[index]
    assert current_state["identity_authority"]["SerialNumber"] == "000A1"  # type: ignore[index]


@pytest.mark.parametrize(
    "fixture_name",
    (
        "current_exact_address",
        "cached_after_replacement",
        "cached_after_retirement",
        "cached_after_supplied_triple_conflict",
        "observation_generation_mismatch",
        "proof_generation_mismatch",
        "authority_substitution",
        "address_substitution",
    ),
)
def test_every_fixture_validates_closed_witness_domains_before_currentness(
    tmp_path: pathlib.Path, fixture_name: str
) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)
    policy = read_policy(tmp_path)
    fixtures = policy["consumer_witness"]["validation_fixtures"]  # type: ignore[index]
    fixture = next(item for item in fixtures if item["name"] == fixture_name)
    fixture["witness"]["observation_provenance"] = "caller_assertion"
    write_policy(tmp_path, policy)

    with pytest.raises(checker.CheckError, match="consumer witness.observation_provenance"):
        checker.validate_documents(tmp_path)


def remove_identity_match(policy: dict[str, object]) -> None:
    del policy["identity"]["match"]  # type: ignore[index]


def add_unknown_identity_field(policy: dict[str, object]) -> None:
    policy["identity"]["alternate_match"] = "serial_only"  # type: ignore[index]


def change_members_to_string(policy: dict[str, object]) -> None:
    policy["identity"]["members"] = "Manufacturer,DeviceID,SerialNumber"  # type: ignore[index]


def alter_qualification_rule(policy: dict[str, object]) -> None:
    policy["identity"]["match"] = "serial_only"  # type: ignore[index]


def alter_normalization_rule(policy: dict[str, object]) -> None:
    policy["normalization"]["registry"]["internal_punctuation"] = "remove"  # type: ignore[index]


def alter_sentinel_recognition_rule(policy: dict[str, object]) -> None:
    policy["identity"]["sentinel_recognition"]["ordinary_serials"] = "parse"  # type: ignore[index]


def alter_provenance_rule(policy: dict[str, object]) -> None:
    policy["provenance"]["static_seed"] = "rewrite"  # type: ignore[index]


def remove_consumer_witness_member(policy: dict[str, object]) -> None:
    policy["consumer_witness"]["required_fields"].remove("immutable")  # type: ignore[index]


def change_consumer_witness_closed_value(policy: dict[str, object]) -> None:
    policy["consumer_witness"]["allowed_values"]["observation_provenance"] = ["caller_assertion"]  # type: ignore[index]


def allow_zero_consumer_witness_generation(policy: dict[str, object]) -> None:
    policy["consumer_witness"]["allowed_values"]["registry_observation_generation"] = ["zero_or_positive_integer"]  # type: ignore[index]


def allow_unknown_current_registry_availability(policy: dict[str, object]) -> None:
    policy["consumer_witness"]["current_registry_state"]["allowed_values"]["availability"] = ["available", "unknown"]  # type: ignore[index]


def remove_atomic_currentness(policy: dict[str, object]) -> None:
    del policy["consumer_witness"]["currentness"]  # type: ignore[index]


def alter_registry_production(policy: dict[str, object]) -> None:
    policy["consumer_witness"]["production"]["producer"] = "caller"  # type: ignore[index]


def accept_cached_replacement(policy: dict[str, object]) -> None:
    fixtures = policy["consumer_witness"]["validation_fixtures"]  # type: ignore[index]
    next(fixture for fixture in fixtures if fixture["name"] == "cached_after_replacement")["current"] = True


def remove_retirement_fixture(policy: dict[str, object]) -> None:
    fixtures = policy["consumer_witness"]["validation_fixtures"]  # type: ignore[index]
    fixtures[:] = [fixture for fixture in fixtures if fixture["name"] != "cached_after_retirement"]


def make_one_ack_current_witness_insertion_optional(policy: dict[str, object]) -> None:
    policy["consumer_witness"]["companion_insertion"] = "may_insert"  # type: ignore[index]


@pytest.mark.parametrize("non_witness_input", ("topology_alias", "last_known_good", "directed_07_04_reply"))
def test_qualified_identity_policy_rejects_consumer_witness_input_misuse(
    tmp_path: pathlib.Path, non_witness_input: str
) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)
    policy = read_policy(tmp_path)
    policy["consumer_witness"]["non_witness_inputs"].remove(non_witness_input)  # type: ignore[index]
    write_policy(tmp_path, policy)

    with pytest.raises(checker.CheckError, match="consumer_witness.non_witness_inputs"):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    ("mutate", "error"),
    (
        (remove_identity_match, "identity: expected exact fields"),
        (add_unknown_identity_field, "identity: expected exact fields"),
        (change_members_to_string, "identity.members"),
        (alter_qualification_rule, "identity.match"),
        (alter_normalization_rule, "normalization.registry.internal_punctuation"),
        (alter_sentinel_recognition_rule, "identity.sentinel_recognition"),
        (alter_provenance_rule, "provenance.static_seed"),
        (remove_consumer_witness_member, "consumer_witness.required_fields"),
        (change_consumer_witness_closed_value, "consumer_witness.allowed_values"),
        (allow_zero_consumer_witness_generation, "consumer_witness.allowed_values"),
        (allow_unknown_current_registry_availability, "consumer_witness.current_registry_state.allowed_values"),
        (remove_atomic_currentness, "consumer_witness: expected exact fields"),
        (alter_registry_production, "consumer_witness.production"),
        (make_one_ack_current_witness_insertion_optional, "consumer_witness.companion_insertion"),
        (accept_cached_replacement, "validation_fixtures.*current"),
        (remove_retirement_fixture, "expected exact fixture names"),
    ),
)
def test_qualified_identity_policy_rejects_structured_mutations(
    tmp_path: pathlib.Path, mutate, error: str
) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)
    policy = read_policy(tmp_path)
    mutate(policy)
    write_policy(tmp_path, policy)

    with pytest.raises(checker.CheckError, match=error):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    "relative",
    (
        pathlib.Path("architecture/regulator-identity-enrichment.md"),
        pathlib.Path("architecture/atr/01-address-table-model.md"),
        pathlib.Path("architecture/atr/03-ack-nack-insertion-rules.md"),
        pathlib.Path("architecture/atr/04-sn-merge-gate.md"),
        pathlib.Path("architecture/atr/07-live-validation-acceptance.md"),
        pathlib.Path("architecture/overview.md"),
        pathlib.Path("api/graphql.md"),
    ),
)
def test_qualified_identity_policy_requires_synchronized_public_reference(
    tmp_path: pathlib.Path, relative: pathlib.Path
) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)
    path = tmp_path / relative
    reference = checker.REQUIRED_DOCUMENT_REFERENCES[relative]
    path.write_text(path.read_text(encoding="utf-8").replace(reference, ""), encoding="utf-8")

    with pytest.raises(checker.CheckError, match="missing required canonical policy reference"):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    "relative",
    (
        pathlib.Path("architecture/atr/01-address-table-model.md"),
        pathlib.Path("architecture/atr/03-ack-nack-insertion-rules.md"),
    ),
)
def test_qualified_identity_policy_requires_complete_atr_normative_block(
    tmp_path: pathlib.Path, relative: pathlib.Path
) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)
    path = tmp_path / relative
    policy = read_policy(tmp_path)
    block = checker.required_atr_normative_block(policy["consumer_witness"])
    begin, *body, end = block.splitlines()
    assert body
    path.write_text(path.read_text(encoding="utf-8").replace(block, f"{begin}\n{end}"), encoding="utf-8")

    with pytest.raises(checker.CheckError, match="missing required qualified-identity normative block"):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    "relative",
    (
        pathlib.Path("architecture/atr/01-address-table-model.md"),
        pathlib.Path("architecture/atr/03-ack-nack-insertion-rules.md"),
    ),
)
def test_qualified_identity_policy_rejects_reverted_atr_normative_block(
    tmp_path: pathlib.Path, relative: pathlib.Path
) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)
    path = tmp_path / relative
    policy = read_policy(tmp_path)
    block = checker.required_atr_normative_block(policy["consumer_witness"])
    reverted = block.replace(
        "MUST equal the current registry state.", "MAY rely on cached witness state."
    )
    path.write_text(path.read_text(encoding="utf-8").replace(block, reverted), encoding="utf-8")

    with pytest.raises(checker.CheckError, match="missing required qualified-identity normative block"):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    "relative",
    (
        pathlib.Path("architecture/atr/01-address-table-model.md"),
        pathlib.Path("architecture/atr/03-ack-nack-insertion-rules.md"),
    ),
)
def test_qualified_identity_policy_rejects_optional_one_ack_current_witness_companion_insertion(
    tmp_path: pathlib.Path, relative: pathlib.Path
) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)
    path = tmp_path / relative
    policy = read_policy(tmp_path)
    block = checker.required_atr_normative_block(policy["consumer_witness"])
    required = "then MUST commit `slot[companion(ZZ)]` with passive provenance."
    assert required in block
    text = path.read_text(encoding="utf-8")
    assert block in text
    path.write_text(text.replace(block, block.replace(required, required.replace("MUST", "MAY"))), encoding="utf-8")

    with pytest.raises(checker.CheckError, match="missing required qualified-identity normative block"):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    ("required", "replacement"),
    (
        (
            "`DeviceRegistry.WithCurrentQualifiedIdentityWitness(address, callback)` remains the read-locked operation",
            "`DeviceRegistry.WithCurrentQualifiedIdentityWitness(address, callback)` is the state-changing operation",
        ),
        (
            "`DeviceRegistry.AdmitPassiveCompanionWithCurrentQualifiedIdentityWitness(source, observedAt)` is the state-changing operation",
            "`DeviceRegistry.AdmitPassiveCompanionWithCurrentQualifiedIdentityWitness(source, observedAt)` is a read-only operation",
        ),
        (
            "MUST atomically validate the current exact-source direct complete normalized witness plus passive target companion-slot admission in one write-critical section",
            "validates the witness before a separate companion-slot admission",
        ),
    ),
    ids=("read-locked-witness-role", "state-changing-admission-role", "write-critical-atomicity"),
)
def test_qualified_identity_policy_rejects_registry_api_role_or_atomicity_drift(
    tmp_path: pathlib.Path, required: str, replacement: str
) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)
    policy = read_policy(tmp_path)
    block = checker.required_registry_api_reference_block(policy["consumer_witness"])
    path = tmp_path / "architecture/regulator-identity-enrichment.md"
    text = path.read_text(encoding="utf-8")
    assert block in text
    assert required in block
    path.write_text(text.replace(block, block.replace(required, replacement), 1), encoding="utf-8")

    with pytest.raises(checker.CheckError, match="missing required qualified-identity registry API reference block"):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    ("required", "replacement"),
    (
        (
            "`DeviceRegistry.WithCurrentQualifiedIdentityWitness(address, callback)` remains the read-locked operation",
            "`DeviceRegistry.WithCurrentQualifiedIdentityWitness(address, callback)` may change registry state",
        ),
        (
            "`DeviceRegistry.AdmitPassiveCompanionWithCurrentQualifiedIdentityWitness(source, observedAt)` is the state-changing operation",
            "a caller-supplied companion is the state-changing operation",
        ),
        (
            "in one write-critical section",
            "after an unlock/relock check-then-use sequence",
        ),
    ),
    ids=("read-locked-witness-role", "state-changing-admission-role", "write-critical-atomicity"),
)
@pytest.mark.parametrize(
    "relative",
    (
        pathlib.Path("architecture/atr/01-address-table-model.md"),
        pathlib.Path("architecture/atr/03-ack-nack-insertion-rules.md"),
    ),
)
def test_qualified_identity_policy_rejects_atr_api_role_or_atomicity_drift(
    tmp_path: pathlib.Path, relative: pathlib.Path, required: str, replacement: str
) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)
    policy = read_policy(tmp_path)
    block = checker.required_atr_normative_block(policy["consumer_witness"])
    path = tmp_path / relative
    text = path.read_text(encoding="utf-8")
    assert block in text
    assert required in block
    path.write_text(text.replace(block, block.replace(required, replacement), 1), encoding="utf-8")

    with pytest.raises(checker.CheckError, match="missing required qualified-identity normative block"):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    ("required", "replacement"),
    (
        (
            "no current registry-adjudicated exact-address qualified witness is available",
            "a cached current flag is available",
        ),
        (
            "Expected: the companion `slot[0xF6]` MUST appear under the one-ACK alternative.",
            "Expected: the companion `slot[0xF6]` MAY appear under the one-ACK alternative.",
        ),
        (
            "replaced, retired, conflicted, invalid, or unavailable",
            "replaced only",
        ),
        (
            "The independent two-ACK route remains independent of identity evidence: after the observation window (default 5s) plus a second corroborating positive ACK, `slot[0xF6]` MUST appear without a witness.",
            "The two-ACK route requires identity evidence.",
        ),
        (
            "atomic registry lookup/validation/use current result",
            "cached `current: true` result",
        ),
        (
            "per-face `0x07/0x04` reply without serial",
            "per-face `0x07/0x04` reply with serial",
        ),
    ),
    ids=(
        "no-current-witness-negative",
        "current-qualified-positive",
        "stale-invalid-unavailable-negatives",
        "two-ack-independent",
        "atomic-current-result",
        "per-face-without-serial",
    ),
)
def test_qualified_identity_policy_rejects_atr07_substantive_acceptance_drift(
    tmp_path: pathlib.Path, required: str, replacement: str
) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)
    policy = read_policy(tmp_path)
    block = checker.required_atr07_acceptance_block(policy["consumer_witness"])
    path = tmp_path / "architecture/atr/07-live-validation-acceptance.md"
    text = path.read_text(encoding="utf-8")
    assert block in text
    assert required in block
    path.write_text(text.replace(block, block.replace(required, replacement), 1), encoding="utf-8")

    with pytest.raises(checker.CheckError, match="missing required ATR07 qualified-identity acceptance block"):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    "fixture_name",
    (
        "cached_after_replacement",
        "cached_after_retirement",
        "cached_after_supplied_triple_conflict",
        "observation_generation_mismatch",
        "proof_generation_mismatch",
        "authority_substitution",
        "address_substitution",
    ),
)
def test_qualified_identity_policy_rejects_each_stale_or_substituted_witness_fixture(
    tmp_path: pathlib.Path, fixture_name: str
) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)
    policy = read_policy(tmp_path)
    fixtures = policy["consumer_witness"]["validation_fixtures"]  # type: ignore[index]
    fixture = next(item for item in fixtures if item["name"] == fixture_name)

    assert checker.consumer_witness_is_current(fixture["witness"], fixture["current_registry_state"]) is False


def test_qualified_identity_policy_rejects_invalid_json(tmp_path: pathlib.Path) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)
    (tmp_path / POLICY_RELATIVE).write_text("{", encoding="utf-8")

    with pytest.raises(checker.CheckError, match="invalid JSON"):
        checker.validate_documents(tmp_path)
