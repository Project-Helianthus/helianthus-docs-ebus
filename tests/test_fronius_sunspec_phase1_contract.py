from __future__ import annotations

import json
import ipaddress
import pathlib
import re
import sys
from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_platform_contracts import (  # noqa: E402
    IPV4_LITERAL,
    M625_RESTRICTED_MATERIAL,
    _private_network_literals,
)


PACKET = REPO_ROOT / "docs/platform/fronius-sunspec-evidence-v1.md"
MANIFEST_PATH = REPO_ROOT / "docs/platform/manifests/fronius-sunspec-phase1-v1.json"
FIXTURE_ROOT = REPO_ROOT / "docs/platform/fixtures/fronius-sunspec-phase1/v1"

EXPECTED_SUPPORTED = [1, 101, 102, 103]
EXPECTED_DEFERRED = [111, 112, 113, 120, 121, 122, 123, 124, 160, "20x", "21x", "7xx"]
EXPECTED_FORBIDDEN = [
    "write_or_control_operation",
    "fixed_vendor_table_addresses",
    "implicit_support_for_deferred_models",
    "fronius_assumptions_inside_standard_profile",
]
EXPECTED_COVERAGE = {
    "signature",
    "base_normalization",
    "dynamic_chain",
    "common_model_1",
    "model_101",
    "model_102",
    "model_103",
    "signed_int16",
    "acc32_high_word_first",
    "sunssf",
    "unknown_model_skip",
    "end_sentinel",
    "malformed_length",
    "extent_overrun",
    "missing_end_sentinel",
    "invalid_scale_sentinel",
    "sunssf_range_enforcement",
    "raw_sample_identity",
    "single_generation_coherence",
    "complete_source_observation_envelope",
    "bounded_multi_response",
    "provenance",
    "transport_neutrality",
    "unsupported_profile_version",
}
SENSITIVE_FIXTURE_KEYS = {
    "access_token",
    "api_key",
    "api_keys",
    "auth_header",
    "auth_token",
    "authorization",
    "bearer_token",
    "client_secret",
    "command_payload",
    "control_payload",
    "credential",
    "credentials",
    "device_id",
    "host",
    "hostname",
    "mac",
    "packet_capture",
    "password",
    "private_key",
    "raw_packet",
    "refresh_token",
    "secret",
    "serial",
    "serial_number",
    "serial_numbers",
    "session_token",
    "ski",
    "token",
    "tokens",
    "wire_transcript",
    "write_payload",
}
PLACEHOLDER_IDENTITY_KEYS = {
    "dependency_set_id",
    "endpoint_identity",
    "identity",
    "logical_view_id",
    "poll_generation_id",
    "sample_id",
    "unit_identity",
    "wire_response_id",
}


def load_json(path: pathlib.Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict), path
    return value


def fixture_paths() -> list[pathlib.Path]:
    return sorted(FIXTURE_ROOT.rglob("*.json"))


def fixture_words(value: dict[str, object]) -> Iterable[int]:
    for example in value.get("logical_word_examples", []):
        assert isinstance(example, dict)
        words = example.get("words", [])
        assert isinstance(words, list)
        yield from words


def is_sensitive_fixture_key(normalized_key: str) -> bool:
    key_parts = normalized_key.split("_")
    for sensitive in SENSITIVE_FIXTURE_KEYS:
        sensitive_parts = sensitive.split("_")
        width = len(sensitive_parts)
        if any(
            key_parts[index : index + width] == sensitive_parts
            for index in range(len(key_parts) - width + 1)
        ):
            return True
    return False


def fixture_sanitization_errors(value: object, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        if value.get("field") == "SN" and value.get("expected") != "PLACEHOLDER":
            errors.append(f"{path}.SN")
        for key, item in value.items():
            normalized_key = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key).lower()
            normalized_key = re.sub(r"[^a-z0-9]+", "_", normalized_key).strip("_")
            if is_sensitive_fixture_key(normalized_key):
                errors.append(f"{path}.{key}:sensitive-key")
            if normalized_key in PLACEHOLDER_IDENTITY_KEYS:
                if not isinstance(item, str) or not item.startswith(
                    ("fixture-", "runtime-supplied-")
                ):
                    errors.append(f"{path}.{key}:non-placeholder-identity")
            errors.extend(fixture_sanitization_errors(item, f"{path}.{key}"))
        return errors
    if isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(fixture_sanitization_errors(item, f"{path}[{index}]"))
        return errors
    if not isinstance(value, str):
        return errors

    if _private_network_literals(value):
        errors.append(f"{path}:private-network")
    for match in IPV4_LITERAL.finditer(value):
        address = ipaddress.ip_address(match.group(0))
        if not address.is_global or address.is_multicast:
            errors.append(f"{path}:non-public-ipv4")
    if M625_RESTRICTED_MATERIAL.search(value):
        errors.append(f"{path}:restricted-material")
    return errors


def test_all_phase_one_json_is_parseable_and_bounded() -> None:
    manifest = load_json(MANIFEST_PATH)
    paths = fixture_paths()
    assert 1 <= len(paths) <= 12
    fixtures = [load_json(path) for path in paths]
    assert manifest["fixture_root"] == "docs/platform/fixtures/fronius-sunspec-phase1/v1"
    assert len(paths) == len(manifest["fixtures"])

    for path, fixture in zip(paths, fixtures, strict=True):
        assert fixture["kind"] in {"positive", "negative"}, path
        provenance = fixture["provenance"]
        assert isinstance(provenance, dict)
        assert provenance == {
            "synthetic": True,
            "license": "AGPL-3.0",
            "capture": "not_a_live_capture",
            "identity": "fixture-placeholder",
        }
        for word in fixture_words(fixture):
            assert isinstance(word, int)
            assert 0 <= word <= 0xFFFF
        for model in fixture.get("chain", []):
            assert isinstance(model, dict)
            length = model["length_words"]
            if fixture["fixture_id"] == "FSS-N-001":
                assert model["model_id"] != 0xFFFF
                assert length == 0
            else:
                assert isinstance(length, int) and 0 <= length <= 128


def test_source_pins_scope_and_dispositions_are_exact() -> None:
    manifest = load_json(MANIFEST_PATH)
    sources = manifest["sources"]
    assert isinstance(sources, list)
    by_id = {source["source_id"]: source for source in sources if isinstance(source, dict)}
    assert set(by_id) == {
        "fronius-manual-4204102649",
        "fronius-register-package-1.2.7-2",
        "sunspec-models-7abdf898",
        "sunspec-device-information-model-v1.1",
    }
    assert by_id["fronius-manual-4204102649"]["edition"] == "033-24022026"
    assert by_id["fronius-manual-4204102649"]["url"] == "https://manuals.fronius.com/html/4204102649/en-US.html"
    assert by_id["fronius-register-package-1.2.7-2"]["package_version"] == "1.2.7-2"
    assert by_id["sunspec-models-7abdf898"]["commit"] == "7abdf8982d5364f8ae916deee18aac86c11be36d"
    assert by_id["sunspec-models-7abdf898"]["revision_date"] == "2026-04-22"
    assert by_id["sunspec-device-information-model-v1.1"]["version"] == "1.1"
    assert manifest["documentation"]["authorization"] == "no_document_hash_or_manifest_field_authorizes_execution"
    assert manifest["phase_one"]["read_only"] is True
    assert manifest["phase_one"]["allowed_function_codes"] == ["FC03"]
    assert "tcp_unit_id" not in manifest["phase_one"]
    assert manifest["fronius_acquisition_evidence"] == {
        "tcp_unit_id": "0x01",
        "scope": "vendor_tcp_acquisition_only",
        "standard_profile_input": False,
        "m3_02_fixture_unit_identity": "runtime_supplied_abstract_identity",
        "retained_for": "future_gateway_acquisition_outside_current_hard_stop",
    }
    assert manifest["m3_02_contract"]["supported_model_ids"] == EXPECTED_SUPPORTED
    assert manifest["m3_02_contract"]["deferred_model_ids"] == EXPECTED_DEFERRED
    assert manifest["m3_02_contract"]["forbidden_behavior"] == EXPECTED_FORBIDDEN
    overlay = manifest["fronius_overlay"]
    assert overlay == {
        "disposition": "HYPOTHESIS",
        "state": "PENDING_M3_03",
        "m3_03_terminal_dispositions": ["STANDARD_ONLY", "OVERLAY_REQUIRED"],
        "terminal_rule": "exactly_one_no_third_state",
        "standard_only_effect": "no_production_fronius_overlay",
        "overlay_required_limit": "evidence_supported_transport_neutral_read_only_profile_logic",
        "candidate_gates": ["manufacturer", "model", "firmware", "package"],
        "production_detector": "not_present",
        "standard_only": False,
    }

    applicability = manifest["applicability"]
    assert isinstance(applicability, list)
    by_applicability = {
        item["applicability_id"]: item for item in applicability if isinstance(item, dict)
    }
    assert by_applicability["gen24-primo-symo-row-int-sf-1.2.7-2"]["disposition"] == "PROVEN"
    assert by_applicability["verto-tauro"]["disposition"] == "UNKNOWN"
    assert by_applicability["older-datamanager-snapinverter-live-hardware"]["disposition"] == "UNKNOWN"


def test_claim_fixture_and_coverage_references_are_closed() -> None:
    manifest = load_json(MANIFEST_PATH)
    fixtures = manifest["fixtures"]
    claims = manifest["claims"]
    sources = manifest["sources"]
    applicability = manifest["applicability"]
    assert isinstance(fixtures, list)
    assert isinstance(claims, list)
    assert isinstance(sources, list)
    assert isinstance(applicability, list)
    fixture_ids = [item["fixture_id"] for item in fixtures if isinstance(item, dict)]
    claim_ids = [item["claim_id"] for item in claims if isinstance(item, dict)]
    source_ids = {item["source_id"] for item in sources if isinstance(item, dict)}
    applicability_ids = {item["applicability_id"] for item in applicability if isinstance(item, dict)}
    assert len(fixture_ids) == len(set(fixture_ids))
    assert len(claim_ids) == len(set(claim_ids))
    fixture_id_set = set(fixture_ids)
    coverage = set()
    for fixture in fixtures:
        assert isinstance(fixture, dict)
        path = FIXTURE_ROOT / fixture["path"]
        assert path.is_file()
        assert load_json(path)["fixture_id"] == fixture["fixture_id"]
        coverage.update(fixture["covers"])
    assert EXPECTED_COVERAGE <= coverage
    for claim in claims:
        assert isinstance(claim, dict)
        assert claim["disposition"] in {"PROVEN", "HYPOTHESIS", "UNKNOWN"}
        assert set(claim["source_ids"]) <= source_ids
        assert set(claim["fixture_ids"]) <= fixture_id_set
        assert set(claim["applicability_ids"]) <= applicability_ids
        assert set(claim["downstream_use"]) <= {"M3-02", "M3-03"}
    assert {"M3-02", "M3-03"} <= {use for claim in claims for use in claim["downstream_use"]}
    m3_02_claims = [claim for claim in claims if "M3-02" in claim["downstream_use"]]
    assert all("unit ID 0x01" not in claim["statement"] for claim in m3_02_claims)
    acquisition_claim = next(claim for claim in claims if claim["claim_id"] == "FSS-C-008")
    assert acquisition_claim["downstream_use"] == []

    signature = load_json(FIXTURE_ROOT / "positive/signature-chain.json")
    assert signature["request"]["unit_identity"] == "runtime-supplied-unit"
    assert "unit_id" not in signature["request"]


def test_synthetic_values_exercise_standard_decode_rules() -> None:
    signature = load_json(FIXTURE_ROOT / "positive/signature-chain.json")
    common = load_json(FIXTURE_ROOT / "positive/common-model-1.json")
    model_101 = load_json(FIXTURE_ROOT / "positive/inverter-101.json")
    model_102 = load_json(FIXTURE_ROOT / "positive/inverter-102-observation.json")
    model_103 = load_json(FIXTURE_ROOT / "positive/inverter-103-unknown-skip.json")
    invalid_scale = load_json(FIXTURE_ROOT / "negative/invalid-scale-sentinel.json")

    assert signature["coordinate_origin"] == (
        "pdu_base_word_zero_includes_two_word_sunspec_signature"
    )
    expected_header_offset = len(signature["expected"]["signature_words"])
    for model in signature["chain"]:
        assert model["header_offset_words"] == expected_header_offset
        if model["model_id"] == 0xFFFF:
            break
        expected_header_offset += 2 + model["length_words"]

    for example in common["logical_word_examples"]:
        assert isinstance(example, dict)
        assert len(example["words"]) == example["declared_width_words"]
        raw = b"".join(word.to_bytes(2, "big") for word in example["words"])
        terminator = raw.find(b"\x00")
        decoded = raw if terminator < 0 else raw[:terminator]
        assert decoded.decode("ascii") == example["expected"]
    assert common["expected"] == {
        "fixed_width_strings": True,
        "termination": "first_nul",
        "bytes_after_first_nul": "ignored_not_emitted",
    }

    def int16(word: int) -> int:
        return word - 0x10000 if word & 0x8000 else word

    def acc32(words: list[int]) -> int:
        return (words[0] << 16) | words[1]

    for fixture, expected_power, expected_energy, expected_scale in (
        (model_101, -123, 120000, -1),
        (model_102, 321, 131072, -1),
        (model_103, -10, 4660, -2),
    ):
        examples = {item["field"]: item for item in fixture["logical_word_examples"]}
        assert int16(examples["W"]["words"][0]) == expected_power
        assert acc32(examples["WH"]["words"]) == expected_energy
        assert examples["WH"]["word_order"] == "high_word_first"
        scale_word = examples["W_SF"]["words"][0]
        power_scale = int16(scale_word)
        assert power_scale == expected_scale
        wh_scale_word = examples["WH_SF"]["words"][0]
        energy_scale = int16(wh_scale_word)
        assert energy_scale == 0
        expected = fixture["expected"]
        scaled_power = Decimal(expected_power) * (Decimal(10) ** power_scale)
        scaled_energy = Decimal(expected_energy) * (Decimal(10) ** energy_scale)
        assert scaled_power == Decimal(str(expected["scaled_w"]))
        assert scaled_energy == Decimal(str(expected["scaled_wh"]))
    context = model_102["observation_context"]
    required_context = {
        "profile_version",
        "codec_version",
        "detector_version",
        "normalization_version",
        "coherence_version",
        "qualification_version",
        "sample_id",
        "poll_generation_id",
        "dependency_set_id",
        "source_validity",
        "source_time",
        "local_receipt_time",
        "endpoint_identity",
        "unit_identity",
        "dependencies",
    }
    assert set(context) == required_context
    assert context["poll_generation_id"] == "fixture-poll-generation-7"
    assert context["source_time"] == {
        "state": "available",
        "value": "2026-01-01T00:00:00Z",
    }
    dependencies = context["dependencies"]
    assert [dependency["dependency_id"] for dependency in dependencies] == [
        "model-102-w",
        "model-102-wh",
    ]
    assert [dependency["raw_words"] for dependency in dependencies] == [
        [321, 65535],
        [2, 0, 0],
    ]
    for dependency in dependencies:
        assert dependency["poll_generation_id"] == context["poll_generation_id"]
        assert dependency["normalization_record"]["version"] == 1
        assert dependency["logical_view_id"].startswith("fixture-logical-view-")
        assert dependency["wire_response_id"].startswith("fixture-wire-response-")
        assert dependency["logical_count_words"] == dependency["slice_count_words"]
        assert dependency["slice_offset_words"] == 0
    coherence = model_102["coherence_policy"]
    assert coherence == {
        "version": 1,
        "mode": "bounded_multi_response",
        "ordered_dependency_ids": ["model-102-w", "model-102-wh"],
        "maximum_source_skew_ms": 1000,
        "maximum_receipt_skew_ms": 1000,
        "generation_equality_required": True,
        "retry_set": "all_dependencies",
        "documentary_consistency_marker": "unavailable",
    }
    source_times = [datetime.fromisoformat(item["source_time"]) for item in dependencies]
    receipt_times = [
        datetime.fromisoformat(item["local_receipt_time"]) for item in dependencies
    ]
    source_skew_ms = (max(source_times) - min(source_times)).total_seconds() * 1000
    receipt_skew_ms = (max(receipt_times) - min(receipt_times)).total_seconds() * 1000
    assert source_skew_ms <= coherence["maximum_source_skew_ms"]
    assert receipt_skew_ms <= coherence["maximum_receipt_skew_ms"]
    assert model_102["expected"]["preserve_observation_context_exactly"] is True

    scale_examples = {
        example["field"]: example for example in invalid_scale["logical_word_examples"]
    }
    decoded_scales = {
        field: int16(example["words"][0]) for field, example in scale_examples.items()
    }
    assert decoded_scales == {
        "W_SF_sentinel": -32768,
        "W_SF_above_range": 11,
        "W_SF_below_range": -11,
        "W_SF_minimum_valid": -10,
        "W_SF_maximum_valid": 10,
    }
    assert invalid_scale["valid_exponent_range"] == {"minimum": -10, "maximum": 10}
    assert scale_examples["W_SF_sentinel"]["expected_error"] == "invalid_scale_factor_sentinel"
    assert {
        scale_examples[field]["expected_error"]
        for field in ("W_SF_above_range", "W_SF_below_range")
    } == {
        "scale_factor_out_of_range"
    }
    for field in ("W_SF_minimum_valid", "W_SF_maximum_valid"):
        example = scale_examples[field]
        scaled = Decimal(example["raw_value"]) * (
            Decimal(10) ** decoded_scales[field]
        )
        assert scaled == Decimal(example["expected_scaled"])


def test_negative_fixtures_encode_reachable_failures() -> None:
    malformed = load_json(FIXTURE_ROOT / "negative/malformed-length.json")
    malformed_model = malformed["chain"][0]
    assert malformed_model["model_id"] != 0xFFFF
    assert malformed_model["length_words"] == 0
    assert malformed["expected_error"] == "zero_length_non_end_model"

    overrun = load_json(FIXTURE_ROOT / "negative/extent-overrun.json")
    overrun_model = overrun["chain"][0]
    required_words = 2 + overrun_model["length_words"]
    assert required_words > overrun["bounded_words_available"]
    assert overrun["expected_error"] == "model_extent_overrun"

    missing_end = load_json(FIXTURE_ROOT / "negative/missing-end.json")
    assert all(model["model_id"] != 0xFFFF for model in missing_end["chain"])
    expected_offset = 2
    for model in missing_end["chain"]:
        assert model["header_offset_words"] == expected_offset
        expected_offset += 2 + model["length_words"]
    assert missing_end["expected_error"] == "missing_end_sentinel"

    unsupported = load_json(FIXTURE_ROOT / "negative/unsupported-profile-version.json")
    assert unsupported["profile"]["version"] not in unsupported["supported_profile_versions"]
    assert unsupported["expected_error"] == "unsupported_profile_version"


def test_fixture_data_is_sanitized_and_modbus_indexes_cross_link_packet() -> None:
    for path in fixture_paths():
        assert fixture_sanitization_errors(load_json(path)) == [], path

    sanitizer_canaries = [
        {"debug": "10.0.0.1"},
        {"debug": "127.0.0.1"},
        {"debug": "172.16.0.1"},
        {"debug": "192.168.1.1"},
        {"debug": "100.64.0.1"},
        {"debug": "169.254.1.1"},
        {"debug": "fc00::1"},
        {"debug": "fe80::1"},
        {"serial_number": "REAL-SERIAL"},
        {"hostname": "inverter.local"},
        {"access_token": "fixture-secret"},
        {"api_key": "fixture-secret"},
        {"apiKey": "fixture-secret"},
        {"client_secret": "fixture-secret"},
        {"adminPassword": "bare-value"},
        {"meterSerialNumber": "bare-value"},
        {"apiToken": "bare-value"},
        {"x-api-key": "bare-value"},
        {"control_payload": [1, 2, 3]},
        {"field": "SN", "expected": "REAL-SERIAL"},
    ]
    for canary in sanitizer_canaries:
        assert fixture_sanitization_errors(canary), canary
    required_links = {
        REPO_ROOT / "docs/platform/README.md": "fronius-sunspec-evidence-v1.md",
        REPO_ROOT / "docs/platform/modbus-multivendor-boundaries.md": "fronius-sunspec-evidence-v1.md",
        REPO_ROOT / "protocols/modbus/README.md": "fronius-sunspec-evidence-v1.md",
    }
    for path, fragment in required_links.items():
        assert fragment in path.read_text(encoding="utf-8"), path
    assert "PENDING_M3_03" in PACKET.read_text(encoding="utf-8")
