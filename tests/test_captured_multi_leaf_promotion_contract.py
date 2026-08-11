from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/platform/captured-multi-leaf-promotion-v1.md"
README = ROOT / "docs/platform/README.md"
SCHEMA_ROOT = ROOT / "docs/platform/schemas"
PRIVATE_SCHEMA = SCHEMA_ROOT / "leaf-promotion-captured-multi-leaf-v1.schema.json"
PUBLIC_SCHEMA = SCHEMA_ROOT / "leaf-promotion-captured-multi-leaf-result-v1.schema.json"
REGISTRY = SCHEMA_ROOT / "leaf-promotion-captured-multi-leaf-registry-v1.json"
FIXTURE = ROOT / "docs/platform/fixtures/leaf-promotion-captured-multi-leaf/v1"
PRIVATE = FIXTURE / "positive/private-campaign.json"
PUBLIC = FIXTURE / "positive/public-result.json"
NEGATIVE = FIXTURE / "negative"
VALIDATOR = ROOT / "scripts/validate_captured_multi_leaf_promotion.py"
GENERATOR = ROOT / "scripts/generate_captured_multi_leaf_promotion_fixture.py"
REGISTRY_SHA256 = "854eb51398c949f14bc905d1d26c906f37243e4a218b7e990734064944621f59"


EXPECTED_NEGATIVE = {
    "granularity-substitution.json": ("GRANULARITY_SUBSTITUTION", "comparator.invalid"),
    "missing-granularity.json": ("MISSING_GRANULARITY", "schema.private"),
    "identity-mismatch.json": ("IDENTITY_MISMATCH", "identity.binding"),
    "generation-change.json": ("GENERATION_CHANGE", "sample.invalid"),
    "skew-exceeded.json": ("SKEW_EXCEEDED", "sample.invalid"),
    "stale-sample.json": ("STALE_SAMPLE", "sample.invalid"),
    "missing-sample.json": ("MISSING_SAMPLE", "comparator.invalid"),
    "conflict-as-match.json": ("CONFLICT_AS_MATCH", "state.invalid"),
    "replay-drift.json": ("REPLAY_DRIFT", "hash.replay"),
    "public-identity-leak.json": ("PUBLIC_IDENTITY_LEAK", "schema.public"),
    "public-secret-leak.json": ("PUBLIC_SECRET_LEAK", "schema.public"),
}


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def module():
    spec = importlib.util.spec_from_file_location("multi_leaf_validator_test", VALIDATOR)
    assert spec is not None and spec.loader is not None
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def write(path: pathlib.Path, value: object) -> pathlib.Path:
    path.write_text(json.dumps(value, separators=(",", ":")), encoding="utf-8")
    return path


def run(
    command: str,
    path: pathlib.Path,
    *,
    private_campaign: pathlib.Path | None = None,
    registry: pathlib.Path = REGISTRY,
) -> subprocess.CompletedProcess[str]:
    args = [
        sys.executable,
        str(VALIDATOR),
        command,
        "--input",
        str(path),
        "--registry",
        str(registry),
    ]
    if private_campaign is not None:
        args.extend(("--private-campaign", str(private_campaign)))
    return subprocess.run(
        args,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONHASHSEED": "random"},
    )


def candidate(campaign: dict, candidate_id: str) -> dict:
    return next(item for item in campaign["candidates"] if item["candidate_id"] == candidate_id)


def promoted(campaign: dict) -> dict:
    return next(item for item in campaign["candidates"] if item["decision"] == "PROMOTED")


def rehash_campaign(validator, campaign: dict) -> None:
    for leaf in campaign["candidates"]:
        if leaf["decision"] == "PROMOTED":
            leaf["dossier_hash"] = validator.digest(
                validator.DOSSIER_DOMAIN, validator._candidate_payload(leaf)
            )
    campaign["source_bindings"]["replay_hash"] = validator.replay_hash(campaign)
    campaign["campaign_hash"] = validator.digest(
        validator.CAMPAIGN_DOMAIN,
        {key: value for key, value in campaign.items() if key != "campaign_hash"},
    )


def rehash_public(validator, public: dict) -> None:
    public["result_hash"] = validator.digest(
        validator.RESULT_DOMAIN,
        {key: value for key, value in public.items() if key != "result_hash"},
    )


def rehash_ebus_identity(validator, identity: dict) -> None:
    identity["selector_hash"] = validator.digest(
        validator.EBUS_SELECTOR_DOMAIN,
        {key: value for key, value in identity.items() if key != "selector_hash"},
    )


def rehash_eebus_identity(validator, identity: dict) -> None:
    identity["identity_hash"] = validator.digest(
        validator.EEBUS_IDENTITY_DOMAIN,
        {key: value for key, value in identity.items() if key != "identity_hash"},
    )


def rehash_raw(validator, sample: dict) -> None:
    sample["raw_hash"] = validator.digest(validator.RAW_VALUE_DOMAIN, sample["raw_value"])


def live_campaign(validator) -> dict:
    campaign = load(PRIVATE)
    campaign["evidence_mode"] = "LIVE_CAPTURE"
    campaign["provenance"] = {
        "class": "LIVE_CAPTURE",
        "fixture_id": None,
        "generator": None,
        "capture_receipts": ["sha256:" + "e" * 64, "sha256:" + "f" * 64],
        "deployment_source_commit": "1" * 40,
        "deployment_binary_hash": "sha256:" + "9" * 64,
    }
    rehash_campaign(validator, campaign)
    return campaign


def promote_mapped_candidate(validator, campaign: dict, candidate_id: str) -> dict:
    registry = load(REGISTRY)
    expected = next(item for item in registry["candidate_catalog"] if item["candidate_id"] == candidate_id)
    leaf = candidate(campaign, candidate_id)
    templates = copy.deepcopy(candidate(campaign, "m7-candidate-0018")["assessments"])
    leaf.update(
        {
            "decision": "PROMOTED",
            "terminal_state": None,
            "visibility": "LOCKED_NOT_EXPOSED",
            "assessments": [],
        }
    )
    is_enum = expected["comparator_class"] == "ENUM_EXACT_MAPPING"
    for window, template in zip(campaign["windows"], templates, strict=True):
        assessment = copy.deepcopy(template)
        assessment["window_id"] = window["window_id"]
        if is_enum:
            ebus_raw = {"kind": "NUMERIC", "decimal": {"number": 0, "scale": 0}, "enum": None, "boolean": None}
            eebus_raw = {"kind": "NUMERIC", "decimal": {"number": 2, "scale": 0}, "enum": None, "boolean": None}
            decoded = {"kind": "ENUM", "decimal": None, "enum": "off", "boolean": None}
        else:
            ebus_raw = {"kind": "NUMERIC", "decimal": {"number": 0, "scale": 0}, "enum": None, "boolean": None}
            eebus_raw = {"kind": "BOOLEAN", "decimal": None, "enum": None, "boolean": False}
            decoded = {"kind": "BOOLEAN", "decimal": None, "enum": None, "boolean": False}
        assessment["ebus_sample"]["raw_value"] = ebus_raw
        assessment["eebus_sample"]["raw_value"] = eebus_raw
        for key in ("ebus_sample", "eebus_sample"):
            assessment[key]["value"] = copy.deepcopy(decoded)
            assessment[key]["unit"] = None
            rehash_raw(validator, assessment[key])
        assessment["comparator"] = {
            "class": expected["comparator_class"],
            "declared_spine_step": None,
            "delta": None,
            "conversion": None,
            "mapping_hash": validator.digest(
                validator.MAPPING_DOMAIN, expected["eebus_source"]["mapping_profile"]
            ),
            "outcome": "MATCH",
        }
        leaf["assessments"].append(assessment)
    return leaf


def test_inventory_and_normative_boundaries() -> None:
    for path in (PAGE, PRIVATE_SCHEMA, PUBLIC_SCHEMA, REGISTRY, PRIVATE, PUBLIC, VALIDATOR, GENERATOR):
        assert path.is_file()
    assert "captured-multi-leaf-promotion-v1.md" in README.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")
    for phrase in (
        "CAPTURED_RUNTIME_MULTI_LEAF_V1",
        "18 M7 VR940 facts",
        "11 protocol-comparable observations",
        "NUMERIC_DECLARED_GRANULARITY",
        "abs(convert(eBUS) - eeBUS) <= declared SPINE step",
        "PRE_RESTART",
        "POST_RESTART",
        "PRIVATE_OPERATOR",
        "PUBLIC_REDACTED",
        "SANITIZED_CONFORMANCE",
        "LIVE_CAPTURE",
        "private_campaign_bytes_hash",
        "registry_sha256",
        "first non-`MATCH` outcome",
        "657a36d07e52570326384b757a5382a6789f641b",
    ):
        assert phrase in page


def test_registry_is_exact_and_contains_full_source_and_selector_profiles() -> None:
    validator = module()
    registry = load(REGISTRY)
    catalog = registry["candidate_catalog"]
    assert hashlib.sha256(REGISTRY.read_bytes()).hexdigest() == REGISTRY_SHA256
    assert validator.PINNED_REGISTRY_SHA256 == "sha256:" + REGISTRY_SHA256
    assert [item["candidate_id"] for item in catalog] == [f"m7-candidate-{index:04d}" for index in range(1, 19)]
    assert sum(item["protocol_eligibility"] == "TERMINAL" for item in catalog) == 4
    assert sum(item["protocol_eligibility"] == "ELIGIBLE" for item in catalog) == 11
    assert sum(item["protocol_eligibility"] == "WITHHOLD_NO_EBUS_CAPABILITY_SOURCE" for item in catalog) == 3
    source_keys = {
        "entity_slot",
        "entity_type",
        "feature_type",
        "feature_role",
        "description_functions",
        "constraints_function",
        "value_functions",
        "field_path",
        "descriptor",
        "unit",
        "declared_constraints",
        "conversion",
        "exact_mapping",
        "mapping_profile",
    }
    active = [item for item in catalog if item["eebus_source"] is not None]
    assert len(active) == 14
    assert all(set(item["eebus_source"]) == source_keys for item in active)
    eligible = [item for item in catalog if item["protocol_eligibility"] == "ELIGIBLE"]
    assert all(item["ebus_selector"]["family"] == "B524" for item in eligible)
    assert all(item["ebus_selector"]["target_address"] == 0x15 for item in eligible)
    assert all(item["ebus_selector"] is None for item in catalog if item["protocol_eligibility"] != "ELIGIBLE")
    assert catalog[6]["eebus_source"]["description_functions"] == [
        "hvacSystemFunctionDescriptionListData",
        "hvacOperationModeDescriptionListData",
        "hvacSystemFunctionOperationModeRelationListData",
    ]
    assert catalog[8]["eebus_source"]["value_functions"] == [
        "hvacSystemFunctionListData",
        "hvacOverrunListData",
    ]
    assert catalog[-1]["eebus_source"]["descriptor"]["scope_type"] == "outsideAirTemperature"


def test_registry_argument_accepts_only_canonical_bytes(tmp_path: pathlib.Path) -> None:
    exact = tmp_path / "exact-registry.json"
    exact.write_bytes(REGISTRY.read_bytes())
    result = run("verify-private", PRIVATE, registry=exact)
    assert (result.returncode, result.stdout) == (0, "PASS\n")

    substituted = load(REGISTRY)
    substituted["capture_limits"]["max_skew_ns"] *= 2
    result = run("verify-private", PRIVATE, registry=write(tmp_path / "substitute.json", substituted))
    assert (result.returncode, result.stdout) == (1, "registry.binding\n")


def test_positive_subset_fixture_verifies_and_derives_byte_identically() -> None:
    private = run("verify-private", PRIVATE)
    assert (private.returncode, private.stdout, private.stderr) == (0, "PASS\n", "")
    derived = run("derive-public", PRIVATE)
    assert derived.returncode == 0 and derived.stderr == ""
    assert derived.stdout.encode("utf-8") == PUBLIC.read_bytes()
    public = run("verify-public", PUBLIC)
    assert (public.returncode, public.stdout, public.stderr) == (0, "PASS\n", "")
    bound = run("verify-public", PUBLIC, private_campaign=PRIVATE)
    assert (bound.returncode, bound.stdout, bound.stderr) == (0, "PASS\n", "")
    result = load(PUBLIC)
    assert result["source_bindings"]["private_campaign_bytes_hash"] == "sha256:" + hashlib.sha256(PRIVATE.read_bytes()).hexdigest()
    assert result["counts"] == {"total": 18, "promoted": 1, "withheld": 17}
    assert result["m9_consumer_gate"] == "BLOCKED_CONFORMANCE_ONLY"


def test_live_public_requires_validated_byte_identical_private_campaign(tmp_path: pathlib.Path) -> None:
    validator = module()
    private_path = write(tmp_path / "live-private.json", live_campaign(validator))
    derived = run("derive-public", private_path)
    assert derived.returncode == 0
    public_path = tmp_path / "live-public.json"
    public_path.write_text(derived.stdout, encoding="utf-8")

    standalone = run("verify-public", public_path)
    assert (standalone.returncode, standalone.stdout) == (1, "private.required\n")
    bound = run("verify-public", public_path, private_campaign=private_path)
    assert (bound.returncode, bound.stdout) == (0, "PASS\n")

    byte_variant = tmp_path / "live-private-byte-variant.json"
    byte_variant.write_bytes(private_path.read_bytes() + b"\n")
    mismatch = run("verify-public", public_path, private_campaign=byte_variant)
    assert (mismatch.returncode, mismatch.stdout) == (1, "private.binding\n")


def test_relabelled_public_cannot_open_m9(tmp_path: pathlib.Path) -> None:
    validator = module()
    public = load(PUBLIC)
    public["evidence_mode"] = "LIVE_CAPTURE"
    public["provenance"]["class"] = "LIVE_CAPTURE"
    public["m9_consumer_gate"] = "READY_FOR_M9_PLANNING"
    public["verdict"] = "VALID_PROMOTION_LOCK"
    rehash_public(validator, public)
    path = write(tmp_path / "relabelled-public.json", public)
    standalone = run("verify-public", path)
    assert (standalone.returncode, standalone.stdout) == (1, "private.required\n")
    rebound = run("verify-public", path, private_campaign=PRIVATE)
    assert (rebound.returncode, rebound.stdout) == (1, "private.binding\n")


def test_eligible_terminal_state_is_derived_from_two_ordered_windows(tmp_path: pathlib.Path) -> None:
    validator = module()
    campaign = load(PRIVATE)
    registry = load(REGISTRY)
    for leaf, expected in zip(campaign["candidates"], registry["candidate_catalog"], strict=True):
        if expected["protocol_eligibility"] == "ELIGIBLE":
            assert [item["window_id"] for item in leaf["assessments"]] == [
                "window-pre-restart",
                "window-post-restart",
            ]
        else:
            assert leaf["assessments"] == []

    wrong_terminal = load(PRIVATE)
    candidate(wrong_terminal, "m7-candidate-0005")["terminal_state"] = "MISMATCH"
    rehash_campaign(validator, wrong_terminal)
    result = run("verify-private", write(tmp_path / "wrong-terminal.json", wrong_terminal))
    assert (result.returncode, result.stdout) == (1, "state.invalid\n")

    missing_window = load(PRIVATE)
    candidate(missing_window, "m7-candidate-0005")["assessments"].pop()
    rehash_campaign(validator, missing_window)
    result = run("verify-private", write(tmp_path / "missing-window.json", missing_window))
    assert (result.returncode, result.stdout) == (1, "state.invalid\n")


def test_catalog_terminal_and_capability_exceptions_remain_exact(tmp_path: pathlib.Path) -> None:
    validator = module()
    public = load(PUBLIC)
    terminal = public["candidate_results"][0]
    terminal.update({"terminal_state": "MISSING", "window_outcomes": ["MISSING", "MISSING"]})
    rehash_public(validator, public)
    result = run("verify-public", write(tmp_path / "terminal-relabel.json", public))
    assert (result.returncode, result.stdout) == (1, "candidate.catalog\n")

    public = load(PUBLIC)
    capability = next(item for item in public["candidate_results"] if item["candidate_id"] == "m7-candidate-0008")
    capability.update(
        {
            "decision": "PROMOTED",
            "terminal_state": None,
            "visibility": "LOCKED_NOT_EXPOSED",
            "dossier_hash": "sha256:" + "e" * 64,
            "window_outcomes": ["MATCH", "MATCH"],
        }
    )
    public["counts"] = {"total": 18, "promoted": 2, "withheld": 16}
    rehash_public(validator, public)
    result = run("verify-public", write(tmp_path / "capability-promoted.json", public))
    assert (result.returncode, result.stdout) == (1, "candidate.catalog\n")


def test_b524_selector_family_and_catalog_tuple_are_bound(tmp_path: pathlib.Path) -> None:
    validator = module()
    campaign = load(PRIVATE)
    identity = candidate(campaign, "m7-candidate-0005")["ebus_identity"]
    identity["RR"] += 1
    rehash_ebus_identity(validator, identity)
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "selector-substitution.json", campaign))
    assert (result.returncode, result.stdout) == (1, "identity.binding\n")

    campaign = load(PRIVATE)
    identity = candidate(campaign, "m7-candidate-0005")["ebus_identity"]
    identity["family"] = "B509"
    rehash_ebus_identity(validator, identity)
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "family-substitution.json", campaign))
    assert (result.returncode, result.stdout) == (1, "schema.private\n")


def test_full_eebus_source_profile_and_identity_hash_are_bound(tmp_path: pathlib.Path) -> None:
    validator = module()
    registry = load(REGISTRY)
    campaign = load(PRIVATE)
    leaf = candidate(campaign, "m7-candidate-0007")
    identity = leaf["eebus_identity"]
    identity["description_functions"] = ["hvacSystemFunctionDescriptionListData"]
    source_keys = registry["candidate_catalog"][6]["eebus_source"].keys()
    substituted_source = {key: identity[key] for key in source_keys}
    identity["source_profile_hash"] = validator.digest(
        validator.SOURCE_PROFILE_DOMAIN, substituted_source
    )
    rehash_eebus_identity(validator, identity)
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "source-profile-substitution.json", campaign))
    assert (result.returncode, result.stdout) == (1, "identity.binding\n")

    campaign = load(PRIVATE)
    candidate(campaign, "m7-candidate-0007")["eebus_identity"]["feature_address"] += 1
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "native-identity-substitution.json", campaign))
    assert (result.returncode, result.stdout) == (1, "identity.binding\n")


def test_raw_hash_and_numeric_raw_to_decoded_identity_are_bound(tmp_path: pathlib.Path) -> None:
    validator = module()
    campaign = load(PRIVATE)
    sample = promoted(campaign)["assessments"][0]["ebus_sample"]
    sample["raw_value"]["decimal"] = {"number": 126, "scale": -1}
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "raw-hash-substitution.json", campaign))
    assert (result.returncode, result.stdout) == (1, "raw.binding\n")

    campaign = load(PRIVATE)
    sample = promoted(campaign)["assessments"][0]["ebus_sample"]
    sample["raw_value"]["decimal"] = {"number": 126, "scale": -1}
    rehash_raw(validator, sample)
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "raw-decoded-substitution.json", campaign))
    assert (result.returncode, result.stdout) == (1, "raw.binding\n")


def test_enum_and_boolean_raw_pairs_are_catalog_mapped(tmp_path: pathlib.Path) -> None:
    validator = module()
    for candidate_id in ("m7-candidate-0007", "m7-candidate-0009"):
        campaign = load(PRIVATE)
        leaf = promote_mapped_candidate(validator, campaign, candidate_id)
        rehash_campaign(validator, campaign)
        passing = run("verify-private", write(tmp_path / f"{candidate_id}-valid.json", campaign))
        assert (passing.returncode, passing.stdout) == (0, "PASS\n")

        raw = leaf["assessments"][0]["eebus_sample"]["raw_value"]
        if raw["kind"] == "NUMERIC":
            raw["decimal"] = {"number": 1, "scale": 0}
        else:
            raw["boolean"] = True
        rehash_raw(validator, leaf["assessments"][0]["eebus_sample"])
        rehash_campaign(validator, campaign)
        result = run("verify-private", write(tmp_path / f"{candidate_id}-raw-substitution.json", campaign))
        assert (result.returncode, result.stdout) == (1, "comparator.invalid\n")

    campaign = load(PRIVATE)
    sample = candidate(campaign, "m7-candidate-0007")["assessments"][0]["eebus_sample"]
    sample["raw_value"]["decimal"] = {"number": 1, "scale": 0}
    rehash_raw(validator, sample)
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "missing-peer-raw-substitution.json", campaign))
    assert (result.returncode, result.stdout) == (1, "comparator.invalid\n")


def test_numeric_rule_is_inclusive_and_catalog_owned(tmp_path: pathlib.Path) -> None:
    validator = module()
    campaign = load(PRIVATE)
    comparators = [item["comparator"] for item in promoted(campaign)["assessments"]]
    assert all(item["delta"] == item["declared_spine_step"] for item in comparators)
    comparators[0]["declared_spine_step"] = {"number": 99, "scale": 0}
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "inflated-step.json", campaign))
    assert (result.returncode, result.stdout) == (1, "comparator.invalid\n")


def test_mismatch_is_recomputed_from_bound_values(tmp_path: pathlib.Path) -> None:
    validator = module()
    campaign = load(PRIVATE)
    leaf = promoted(campaign)
    for assessment in leaf["assessments"]:
        assessment["comparator"]["outcome"] = "MISMATCH"
    leaf.update(
        decision="WITHHELD",
        terminal_state="MISMATCH",
        visibility="RAW_DEBUG_ONLY",
        dossier_hash=None,
    )
    rehash_campaign(validator, campaign)
    fabricated = run(
        "verify-private", write(tmp_path / "fabricated-mismatch.json", campaign)
    )
    assert (fabricated.returncode, fabricated.stdout) == (
        1,
        "comparator.invalid\n",
    )

    campaign = load(PRIVATE)
    leaf = promoted(campaign)
    for position, assessment in enumerate(leaf["assessments"]):
        sample = assessment["eebus_sample"]
        sample["raw_value"]["decimal"] = {"number": 14, "scale": 0}
        sample["value"]["decimal"] = {"number": 14, "scale": 0}
        rehash_raw(validator, sample)
        assessment["comparator"]["delta"] = (
            {"number": 15, "scale": -1}
            if position == 0
            else {"number": 1, "scale": 0}
        )
        assessment["comparator"]["outcome"] = "MISMATCH"
    leaf.update(
        decision="WITHHELD",
        terminal_state="MISMATCH",
        visibility="RAW_DEBUG_ONLY",
        dossier_hash=None,
    )
    rehash_campaign(validator, campaign)
    observed = run("verify-private", write(tmp_path / "observed-mismatch.json", campaign))
    assert (observed.returncode, observed.stdout) == (0, "PASS\n")


def test_capture_limits_and_restart_generation_are_bound(tmp_path: pathlib.Path) -> None:
    validator = module()
    campaign = load(PRIVATE)
    promoted(campaign)["assessments"][0]["max_skew_ns"] *= 2
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "widened-limit.json", campaign))
    assert (result.returncode, result.stdout) == (1, "sample.invalid\n")

    campaign = load(PRIVATE)
    promoted(campaign)["assessments"][0]["eebus_sample"]["capture_generation"] = "wrong"
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "wrong-generation.json", campaign))
    assert (result.returncode, result.stdout) == (1, "sample.invalid\n")


def test_existing_zero_profile_canonical_bytes_are_unchanged() -> None:
    expected = {
        "leaf-promotion-registry-v1.json": "ad33736c00aa2c3ecaac981606d25c064088c80cb72ca5389b83c5d9df40f6a3",
        "../fixtures/leaf-promotion-dossier/v1/positive/dossier.json": "3b12e3b6f625f6efb28fced19d679ab73b974fc4369e0dba9f61f1a2d104ec64",
        "../fixtures/leaf-promotion-dossier/v1/positive/result.json": "a4e5deb1027e337e917304addfa1aebaaf8f04659d7de38b36083c78525d1a04",
    }
    for relative, expected_hash in expected.items():
        assert hashlib.sha256((SCHEMA_ROOT / relative).resolve().read_bytes()).hexdigest() == expected_hash


def mutate(campaign: dict, public: dict, mutation: str) -> tuple[str, dict]:
    leaf = promoted(campaign)
    if mutation == "GRANULARITY_SUBSTITUTION":
        leaf["assessments"][0]["comparator"]["declared_spine_step"] = {"number": 1, "scale": -1}
    elif mutation == "MISSING_GRANULARITY":
        leaf["assessments"][0]["comparator"]["declared_spine_step"] = None
    elif mutation == "IDENTITY_MISMATCH":
        leaf["ebus_identity"]["source_address"] = 126
    elif mutation == "GENERATION_CHANGE":
        leaf["assessments"][0]["eebus_sample"]["connection_generation"] += 1
    elif mutation == "SKEW_EXCEEDED":
        leaf["assessments"][0]["max_skew_ns"] = 1
    elif mutation == "STALE_SAMPLE":
        leaf["assessments"][0]["max_age_ns"] = 1
    elif mutation == "MISSING_SAMPLE":
        leaf["assessments"][0]["ebus_sample"] = None
    elif mutation == "CONFLICT_AS_MATCH":
        leaf["assessments"][0]["comparator"]["outcome"] = "CONFLICT"
    elif mutation == "REPLAY_DRIFT":
        campaign["source_bindings"]["replay_hash"] = "sha256:" + "f" * 64
    elif mutation == "PUBLIC_IDENTITY_LEAK":
        public["device_address"] = "forbidden"
        return "verify-public", public
    elif mutation == "PUBLIC_SECRET_LEAK":
        public["private_key"] = "forbidden"
        return "verify-public", public
    else:
        raise AssertionError(mutation)
    return "verify-private", campaign


def test_negative_vectors_are_closed_and_fail_in_declared_category(tmp_path: pathlib.Path) -> None:
    assert {path.name for path in NEGATIVE.glob("*.json")} == set(EXPECTED_NEGATIVE)
    baseline_private = load(PRIVATE)
    baseline_public = load(PUBLIC)
    for name, (mutation, category) in EXPECTED_NEGATIVE.items():
        assert load(NEGATIVE / name) == {
            "contract": "helianthus.platform.leaf-promotion-captured-multi-leaf-negative.v1",
            "mutation": mutation,
            "expected_category": category,
        }
        command, value = mutate(copy.deepcopy(baseline_private), copy.deepcopy(baseline_public), mutation)
        result = run(command, write(tmp_path / name, value))
        assert (result.returncode, result.stdout, result.stderr) == (1, category + "\n", ""), name


def test_public_redaction_and_private_schema_fail_closed(tmp_path: pathlib.Path) -> None:
    for path in (PRIVATE, PUBLIC):
        serialized = path.read_text(encoding="utf-8").lower()
        for forbidden in ("private_key", "trust_store", "candidate_ref", "ship_id", "ski", "token"):
            assert forbidden not in serialized
    campaign = load(PRIVATE)
    campaign["private_key"] = "forbidden"
    result = run("verify-private", write(tmp_path / "private-secret.json", campaign))
    assert (result.returncode, result.stdout) == (1, "schema.private\n")


def test_canonical_json_emits_unicode_as_utf8() -> None:
    validator = module()
    assert validator.canonical({"text": "é"}) == '{"text":"é"}'.encode("utf-8")


def test_generator_is_deterministic() -> None:
    before = {path: path.read_bytes() for path in (PRIVATE, PUBLIC)}
    result = subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    assert before == {path: path.read_bytes() for path in (PRIVATE, PUBLIC)}
