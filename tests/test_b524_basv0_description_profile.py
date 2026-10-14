import json
import subprocess
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "protocols/vaillant/fixtures/b524-basv0-description-profile-v1.json"
SCHEMA = ROOT / "protocols/vaillant/fixtures/b524-basv0-description-profile-schema-v1.json"
REGISTER_FIXTURE = ROOT / "protocols/vaillant/fixtures/b524-basv0-register-observations-v1.json"
REGISTER_SCHEMA = ROOT / "protocols/vaillant/fixtures/b524-basv0-register-observations-schema-v1.json"


def validate(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "scripts/validate_b524_basv0_description_profile.py", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def validate_cross(description: Path, observations: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", "scripts/validate_b524_basv0_description_profile.py", str(description), "--observations", str(observations)], cwd=ROOT, text=True, capture_output=True, check=False)


def test_profile_retains_bounded_native_evidence() -> None:
    profile = json.loads(FIXTURE.read_text())
    assert profile["observation_id"] == "basv0_sw0217_hw8803_api1"
    assert profile["local_profile"] == {
        "eid": "BASV0", "software_raw": "0217", "hardware_raw": "8803", "api_revision": "API1"
    }
    assert len(profile["records"]) == 2093
    assert any(record["name"] is None for record in profile["records"])
    assert sum(record["raw_description_hex"] is None for record in profile["records"]) == 29
    assert validate(FIXTURE).returncode == 0


def test_validator_rejects_length_inferred_codec_promotion(tmp_path: Path) -> None:
    profile = json.loads(FIXTURE.read_text())
    candidate = deepcopy(profile)
    solar = next(record for record in candidate["records"] if record["selector"]["instance"] == "01" and record["selector"]["group"] == "04")
    solar["decoded"] = {"codec": "EXP", "codec_provenance": "length_inferred", "codec_basis": "payload_length_inferred", "qualification": "qualified", "min": 0, "max": 1, "step": 1}
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(candidate))
    result = validate(path)
    assert result.returncode != 0
    assert "length-inferred codec" in result.stderr


def test_schema_accepts_profile() -> None:
    result = subprocess.run(["jv", str(SCHEMA), str(FIXTURE)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr


def test_validator_rejects_qualified_raw_limit_mismatch(tmp_path: Path) -> None:
    profile = json.loads(FIXTURE.read_text())
    candidate = deepcopy(profile)
    candidate["records"][0]["decoded"]["max"] = 999
    path = tmp_path / "bad-limit.json"
    path.write_text(json.dumps(candidate))
    result = validate(path)
    assert result.returncode != 0
    assert "decoded.max disagrees" in result.stderr


def test_register_observations_preserve_nonvalue_outcomes() -> None:
    profile = json.loads(REGISTER_FIXTURE.read_text())
    assert profile["current_values"] == "omitted"
    assert len(profile["records"]) == 6585
    assert sum(record["response_state"] == "echo_payload" for record in profile["records"]) == 5335
    assert sum(record["response_state"] == "status_only" for record in profile["records"]) == 1155
    assert sum(record["response_state"] == "transport_error" for record in profile["records"]) == 95
    assert sum(record["description"] is None for record in profile["records"]) == 4492
    result = subprocess.run(["jv", str(REGISTER_SCHEMA), str(REGISTER_FIXTURE)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    assert validate_cross(FIXTURE, REGISTER_FIXTURE).returncode == 0


def test_cross_fixture_validator_rejects_out_of_bounds_and_swapped_selector(tmp_path: Path) -> None:
    profile = json.loads(REGISTER_FIXTURE.read_text())
    for name, mutate in [
        ("out-of-bounds", lambda candidate: candidate["records"][1]["description"].update({"record_index": 99999})),
        ("swapped", lambda candidate: candidate["records"][1]["description"].update({"record_index": 1})),
    ]:
        candidate = deepcopy(profile)
        mutate(candidate)
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(candidate))
        result = validate_cross(FIXTURE, path)
        assert result.returncode != 0, name


def test_register_observation_schema_rejects_sensitive_or_unknown_fields(tmp_path: Path) -> None:
    profile = json.loads(REGISTER_FIXTURE.read_text())
    mutations = [
        ("root-private", lambda candidate: candidate.update({"private_capture_reference": "forbidden"})),
        ("record-current", lambda candidate: candidate["records"][0].update({"current_value_hex": "00"})),
        ("nested-extra", lambda candidate: candidate["records"][0]["selector"].update({"device_serial": "forbidden"})),
        ("description-extra", lambda candidate: candidate["records"][1]["description"].update({"raw_payload_hex": "0001"})),
    ]
    for name, mutate in mutations:
        candidate = deepcopy(profile)
        mutate(candidate)
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(candidate))
        result = subprocess.run(["jv", str(REGISTER_SCHEMA), str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
        assert result.returncode != 0, name
