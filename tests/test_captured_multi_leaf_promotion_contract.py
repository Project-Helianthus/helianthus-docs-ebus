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


EXPECTED_NEGATIVE = {
    "granularity-substitution.json": ("GRANULARITY_SUBSTITUTION", "comparator.invalid"),
    "missing-granularity.json": ("MISSING_GRANULARITY", "comparator.invalid"),
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


def run(command: str, path: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), command, "--input", str(path), "--registry", str(REGISTRY)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONHASHSEED": "random"},
    )


def promoted(campaign: dict) -> dict:
    return next(item for item in campaign["candidates"] if item["decision"] == "PROMOTED")


def rehash_campaign(validator, campaign: dict) -> None:
    leaf = promoted(campaign)
    leaf["dossier_hash"] = validator.digest(validator.DOSSIER_DOMAIN, validator._candidate_payload(leaf))
    campaign["source_bindings"]["replay_hash"] = validator.replay_hash(campaign)
    campaign["campaign_hash"] = validator.digest(
        validator.CAMPAIGN_DOMAIN,
        {key: value for key, value in campaign.items() if key != "campaign_hash"},
    )


def test_inventory_and_normative_boundaries() -> None:
    for path in (PAGE, PRIVATE_SCHEMA, PUBLIC_SCHEMA, REGISTRY, PRIVATE, PUBLIC, VALIDATOR, GENERATOR):
        assert path.is_file()
    assert "captured-multi-leaf-promotion-v1.md" in README.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")
    for phrase in (
        "CAPTURED_RUNTIME_MULTI_LEAF_V1",
        "18 M7 VR940 facts",
        "14 raw eeBUS observations",
        "seven numeric values",
        "three operation-mode enums",
        "four booleans",
        "NUMERIC_DECLARED_GRANULARITY",
        "abs(convert(eBUS) - eeBUS) <= declared SPINE step",
        "LOCKED_NOT_EXPOSED",
        "PRE_RESTART",
        "POST_RESTART",
        "PRIVATE_OPERATOR",
        "PUBLIC_REDACTED",
        "SANITIZED_CONFORMANCE",
        "LIVE_CAPTURE",
        "ea2538bb24f3a13ef8c35624440b4830b618c48a",
    ):
        assert phrase in page


def test_registry_classifies_all_18_actual_candidates() -> None:
    registry = load(REGISTRY)
    catalog = registry["candidate_catalog"]
    assert [item["candidate_id"] for item in catalog] == [f"m7-candidate-{index:04d}" for index in range(1, 19)]
    assert sum(item["source_status"] == "WITHHELD" for item in catalog) == 4
    assert sum(item["source_status"] == "RAW_ONLY" for item in catalog) == 14
    assert sum(item["comparator_class"] == "NUMERIC_DECLARED_GRANULARITY" for item in catalog) == 7
    assert sum(item["comparator_class"] == "ENUM_EXACT_MAPPING" for item in catalog) == 3
    assert sum(item["comparator_class"] == "BOOLEAN_EXACT_MAPPING" for item in catalog) == 4
    assert catalog[-1]["descriptor"] == "outsideAirTemperature"


def test_existing_zero_profile_canonical_bytes_are_unchanged() -> None:
    expected = {
        "leaf-promotion-registry-v1.json": "ad33736c00aa2c3ecaac981606d25c064088c80cb72ca5389b83c5d9df40f6a3",
        "../fixtures/leaf-promotion-dossier/v1/positive/dossier.json": "3b12e3b6f625f6efb28fced19d679ab73b974fc4369e0dba9f61f1a2d104ec64",
        "../fixtures/leaf-promotion-dossier/v1/positive/result.json": "a4e5deb1027e337e917304addfa1aebaaf8f04659d7de38b36083c78525d1a04",
    }
    for relative, digest in expected.items():
        path = SCHEMA_ROOT / relative
        assert hashlib.sha256(path.resolve().read_bytes()).hexdigest() == digest


def test_positive_subset_fixture_verifies_and_derives_byte_identically() -> None:
    private = run("verify-private", PRIVATE)
    assert (private.returncode, private.stdout, private.stderr) == (0, "PASS\n", "")
    derived = run("derive-public", PRIVATE)
    assert derived.returncode == 0 and derived.stderr == ""
    assert derived.stdout.encode("ascii") == PUBLIC.read_bytes()
    public = run("verify-public", PUBLIC)
    assert (public.returncode, public.stdout, public.stderr) == (0, "PASS\n", "")
    result = load(PUBLIC)
    assert result["counts"] == {"total": 18, "promoted": 1, "withheld": 17}
    assert result["m9_consumer_gate"] == "BLOCKED_CONFORMANCE_ONLY"
    assert result["verdict"] == "VALID_SUBSET_PROMOTION_CONFORMANCE"


def test_numeric_rule_is_inclusive_at_the_declared_spine_step(tmp_path: pathlib.Path) -> None:
    validator = module()
    campaign = load(PRIVATE)
    leaf = promoted(campaign)
    for assessment in leaf["assessments"]:
        assessment["ebus_sample"]["value"]["decimal"] = {"number": 125, "scale": -1}
        assessment["eebus_sample"]["value"]["decimal"] = {"number": 13, "scale": 0}
        assessment["comparator"]["delta"] = {"number": 5, "scale": -1}
        assessment["comparator"]["declared_spine_step"] = {"number": 5, "scale": -1}
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "inclusive.json", campaign))
    assert (result.returncode, result.stdout) == (0, "PASS\n")


def test_generator_is_deterministic() -> None:
    before = {path: path.read_bytes() for path in (PRIVATE, PUBLIC)}
    result = subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=False, capture_output=True, text=True)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    assert before == {path: path.read_bytes() for path in (PRIVATE, PUBLIC)}


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
        descriptor = load(NEGATIVE / name)
        assert descriptor == {
            "contract": "helianthus.platform.leaf-promotion-captured-multi-leaf-negative.v1",
            "mutation": mutation,
            "expected_category": category,
        }
        command, value = mutate(copy.deepcopy(baseline_private), copy.deepcopy(baseline_public), mutation)
        result = run(command, write(tmp_path / name, value))
        assert (result.returncode, result.stdout, result.stderr) == (1, category + "\n", ""), name


def test_no_secret_or_candidate_ref_field_exists_in_either_tier(tmp_path: pathlib.Path) -> None:
    for path in (PRIVATE, PUBLIC):
        serialized = path.read_text(encoding="utf-8").lower()
        for forbidden in ("private_key", "trust_store", "candidate_ref", "ship_id", "ski", "token"):
            assert forbidden not in serialized
    campaign = load(PRIVATE)
    campaign["private_key"] = "forbidden"
    result = run("verify-private", write(tmp_path / "private-secret.json", campaign))
    assert (result.returncode, result.stdout) == (1, "schema.private\n")


def test_negative_zero_and_public_gate_substitution_fail_closed(tmp_path: pathlib.Path) -> None:
    raw = PRIVATE.read_text(encoding="utf-8").replace('"scale":0', '"scale":-0', 1)
    negative_zero = tmp_path / "negative-zero.json"
    negative_zero.write_text(raw, encoding="utf-8")
    result = run("verify-private", negative_zero)
    assert (result.returncode, result.stdout) == (1, "json.syntax\n")

    public = load(PUBLIC)
    public["m9_consumer_gate"] = "READY_FOR_M9_PLANNING"
    result = run("verify-public", write(tmp_path / "public-gate.json", public))
    assert (result.returncode, result.stdout) == (1, "state.invalid\n")
