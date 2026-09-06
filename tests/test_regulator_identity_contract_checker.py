from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / "scripts/check_regulator_identity_contract.py"
POLICY_RELATIVE = pathlib.Path("architecture/regulator-qualified-identity-policy.json")


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
        pathlib.Path("architecture/atr/03-ack-nack-insertion-rules.md"),
        pathlib.Path("architecture/atr/04-sn-merge-gate.md"),
        pathlib.Path("architecture/overview.md"),
        pathlib.Path("api/graphql.md"),
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, target)


def read_policy(root: pathlib.Path) -> dict[str, object]:
    return json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))


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
    assert policy["consumer_witness"] == {
        "kind": "qualified_identity_consumer_witness_v1",
        "required_fields": [
            "address",
            "identity_authority",
            "observation_provenance",
            "current",
            "immutable",
            "registry_observation_generation",
            "registry_proof_generation",
        ],
        "allowed_values": {
            "address": ["exact_address"],
            "identity_authority": ["current_qualified_identity"],
            "observation_provenance": ["direct_observation"],
            "current": [True],
            "immutable": [True],
            "registry_observation_generation": ["positive_integer"],
            "registry_proof_generation": ["positive_integer"],
        },
        "stale_on": ["replacement", "retirement", "conflict"],
        "non_witness_inputs": [
            "observable_nonempty_fields",
            "identity_confirmed",
            "topology_alias",
            "topology_propagated_confirmation",
            "static_seed",
            "passive_observed",
            "caller_assertion",
            "last_known_good",
            "directed_07_04_reply",
        ],
        "companion_corroboration": "same_source_positive_ack_plus_current_exact_address_witness",
    }
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
        pathlib.Path("architecture/atr/03-ack-nack-insertion-rules.md"),
        pathlib.Path("architecture/atr/04-sn-merge-gate.md"),
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


def test_qualified_identity_policy_rejects_invalid_json(tmp_path: pathlib.Path) -> None:
    checker = load_checker()
    copy_contract_material(tmp_path)
    (tmp_path / POLICY_RELATIVE).write_text("{", encoding="utf-8")

    with pytest.raises(checker.CheckError, match="invalid JSON"):
        checker.validate_documents(tmp_path)
