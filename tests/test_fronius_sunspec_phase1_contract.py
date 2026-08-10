from __future__ import annotations

import json
import pathlib
import re
from collections.abc import Iterable
from datetime import datetime


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKET = REPO_ROOT / "docs/platform/fronius-sunspec-evidence-v1.md"
MANIFEST_PATH = REPO_ROOT / "docs/platform/manifests/fronius-sunspec-phase1-v1.json"
FIXTURE_ROOT = REPO_ROOT / "docs/platform/fixtures/fronius-sunspec-phase1/v1"

EXPECTED_SUPPORTED = [1, 101, 102, 103]
EXPECTED_DEFERRED = [111, 112, 113, 120, 121, 122, 123, 124, 160, "20x", "21x", "7xx"]
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
                assert length == -1
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
    assert manifest["m3_02_contract"]["supported_model_ids"] == EXPECTED_SUPPORTED
    assert manifest["m3_02_contract"]["deferred_model_ids"] == EXPECTED_DEFERRED
    overlay = manifest["fronius_overlay"]
    assert overlay == {
        "disposition": "HYPOTHESIS",
        "state": "PENDING_M3_03",
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


def test_synthetic_values_exercise_standard_decode_rules() -> None:
    common = load_json(FIXTURE_ROOT / "positive/common-model-1.json")
    model_101 = load_json(FIXTURE_ROOT / "positive/inverter-101.json")
    model_102 = load_json(FIXTURE_ROOT / "positive/inverter-102-observation.json")
    model_103 = load_json(FIXTURE_ROOT / "positive/inverter-103-unknown-skip.json")
    invalid_scale = load_json(FIXTURE_ROOT / "negative/invalid-scale-sentinel.json")

    for example in common["logical_word_examples"]:
        assert isinstance(example, dict)
        decoded = b"".join(word.to_bytes(2, "big") for word in example["words"])
        assert decoded.rstrip(b"\x00").decode("ascii") == example["expected"]

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
        assert int16(scale_word) == expected_scale
        wh_scale_word = examples["WH_SF"]["words"][0]
        assert int16(wh_scale_word) == 0
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

    scale_examples = invalid_scale["logical_word_examples"]
    decoded_scales = [int16(example["words"][0]) for example in scale_examples]
    assert decoded_scales == [-32768, 11, -11]
    assert invalid_scale["valid_exponent_range"] == {"minimum": -10, "maximum": 10}
    assert scale_examples[0]["expected_error"] == "invalid_scale_factor_sentinel"
    assert {example["expected_error"] for example in scale_examples[1:]} == {
        "scale_factor_out_of_range"
    }


def test_fixture_data_is_sanitized_and_modbus_indexes_cross_link_packet() -> None:
    private_address = re.compile(r"\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b|\b192\.168\.")
    for path in fixture_paths():
        text = path.read_text(encoding="utf-8")
        assert private_address.search(text) is None, path
        assert "credential" not in text.lower(), path
        assert "password" not in text.lower(), path
    required_links = {
        REPO_ROOT / "docs/platform/README.md": "fronius-sunspec-evidence-v1.md",
        REPO_ROOT / "docs/platform/modbus-multivendor-boundaries.md": "fronius-sunspec-evidence-v1.md",
        REPO_ROOT / "protocols/modbus/README.md": "fronius-sunspec-evidence-v1.md",
    }
    for path, fragment in required_links.items():
        assert fragment in path.read_text(encoding="utf-8"), path
    assert "PENDING_M3_03" in PACKET.read_text(encoding="utf-8")
