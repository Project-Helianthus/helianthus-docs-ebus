import importlib.util
import json
import re
import struct
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "protocols/vaillant/fixtures/b524-basv0-description-profile-v1.json"
SCHEMA = ROOT / "protocols/vaillant/fixtures/b524-basv0-description-profile-schema-v1.json"
REGISTER_FIXTURE = ROOT / "protocols/vaillant/fixtures/b524-basv0-register-observations-v1.json"
REGISTER_SCHEMA = ROOT / "protocols/vaillant/fixtures/b524-basv0-register-observations-schema-v1.json"


_SPEC = importlib.util.spec_from_file_location("basv0_validator", ROOT / "scripts/validate_b524_basv0_description_profile.py")
validator = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(validator)
CATALOG = "b524-basv0-description-profile-v1.json"
_DESCRIPTIONS = json.loads(FIXTURE.read_text())
_OBSERVATIONS = json.loads(REGISTER_FIXTURE.read_text())


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
    solar = next(record for record in candidate["records"] if record["selector"] == {"operation": "02", "group": "04", "instance": "01", "register": "000B"})
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


def test_validator_rejects_invalid_qualified_numeric_ranges_even_when_raw_limits_agree(tmp_path: Path) -> None:
    profile = json.loads(FIXTURE.read_text())

    def update_exp_limit(record: dict, field: str, value: float) -> None:
        raw_limits = record["raw_limits"]
        raw_limits[f"{field}_hex"] = struct.pack("<f", value).hex().upper()
        record["raw_description_hex"] = record["raw_description_hex"][:6] + "".join(
            raw_limits[name] for name in ("min_hex", "max_hex", "step_hex")
        )
        record["decoded"][field] = value

    for name, field, value, message in [
        ("nonfinite", "max", float("inf"), "must be finite"),
        ("unordered", "min", 21.0, "must be ordered"),
        ("zero-step", "step", 0.0, "step must be positive"),
    ]:
        candidate = deepcopy(profile)
        update_exp_limit(candidate["records"][0], field, value)
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(candidate))
        result = validate(path)
        assert result.returncode != 0, name
        assert message in result.stderr


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


def test_cross_fixture_validator_rejects_inconsistent_response_states(tmp_path: Path) -> None:
    profile = json.loads(REGISTER_FIXTURE.read_text())
    for name, mutate in [
        ("status-as-echo", lambda candidate: candidate["records"][0].update({"response_state": "echo_payload"})),
        ("echo-missing-width", lambda candidate: candidate["records"][1].update({"observed_payload_width": None})),
        ("transport-has-flags", lambda candidate: candidate["records"][2].update({"access_flags": "00"})),
    ]:
        candidate = deepcopy(profile)
        mutate(candidate)
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(candidate))
        assert validate_cross(FIXTURE, path).returncode != 0, name


def test_cross_fixture_validator_rejects_linked_metadata_contradictions(tmp_path: Path) -> None:
    profile = json.loads(REGISTER_FIXTURE.read_text())
    descriptions = json.loads(FIXTURE.read_text())
    unavailable = next(index for index, row in enumerate(profile["records"]) if row["description"] and row["description"]["acquisition_state"] == "unavailable")
    remote = next(index for index, row in enumerate(descriptions["records"]) if row["remote_identity"] and "group" in row["remote_identity"])
    cases = [
        ("flags", lambda rows, descriptions: rows[1].update({"access_flags": "02"})),
        ("scope", lambda rows, descriptions: rows[1].update({"identity_scope": "remote"})),
        ("index-state", lambda rows, descriptions: rows[unavailable]["description"].update({"acquisition_state": "matched"})),
        ("header-group", lambda rows, descriptions: descriptions[remote]["remote_identity"].update({"group": "FF"})),
    ]
    for name, mutate in cases:
        candidate_rows = deepcopy(profile)
        candidate_descriptions = deepcopy(descriptions)
        mutate(candidate_rows["records"], candidate_descriptions["records"])
        row_path = tmp_path / f"{name}-rows.json"
        description_path = tmp_path / f"{name}-descriptions.json"
        candidate_rows["description_catalog"] = description_path.name
        row_path.write_text(json.dumps(candidate_rows))
        description_path.write_text(json.dumps(candidate_descriptions))
        assert validate_cross(description_path, row_path).returncode != 0, name


def test_cross_fixture_validator_rejects_linked_payload_width_mismatch(tmp_path: Path) -> None:
    observations = json.loads(REGISTER_FIXTURE.read_text())
    candidate = deepcopy(observations)
    candidate["records"][1]["observed_payload_width"] = 99
    path = tmp_path / "payload-width-mismatch.json"
    path.write_text(json.dumps(candidate))
    result = validate_cross(FIXTURE, path)
    assert result.returncode != 0
    assert "payload width disagrees with description" in result.stderr


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


def test_profile_page_cites_current_fixture_digests() -> None:
    import hashlib

    page = (ROOT / "protocols" / "vaillant" / "ebus-vaillant-b524-basv0-profile-v1.md").read_text()
    for fixture in (FIXTURE, REGISTER_FIXTURE):
        digest = hashlib.sha256(fixture.read_bytes()).hexdigest()
        assert digest in page, f"{fixture.name} digest {digest[:12]}… is not cited by the profile page"


# --- Mutation tests: every check must fail with its own message ---------------------

def descriptions() -> dict:
    return deepcopy(_DESCRIPTIONS)


def observations() -> dict:
    return deepcopy(_OBSERVATIONS)


def find(document: dict, operation: str, group: str, instance: str, register: str) -> tuple[int, dict]:
    wanted = {"operation": operation, "group": group, "instance": instance, "register": register}
    for index, record in enumerate(document["records"]):
        if record["selector"] == wanted:
            return index, record
    raise AssertionError(f"selector {wanted} not in fixture")


def set_spans(record: dict, min_hex: str, max_hex: str, step_hex: str) -> None:
    body = min_hex + max_hex + step_hex
    record["raw_description_hex"] = record["raw_description_hex"][:6] + body
    record["description_payload_length"] = len(body) // 2
    record["raw_limits"] = {"min_hex": min_hex, "max_hex": max_hex, "step_hex": step_hex}


def rejects(message: str, document: dict, observed: dict | None = None) -> None:
    with pytest.raises(validator.ValidationError) as caught:
        validator.validate_documents(document, observed, CATALOG)
    assert str(caught.value) == message


def test_unmutated_documents_pass_in_process() -> None:
    validator.validate_documents(descriptions(), observations(), CATALOG)


def test_record_structure_checks_report_their_own_messages() -> None:
    def mutated(mutate, index: int = 0) -> dict:
        document = descriptions()
        mutate(document["records"][index])
        return document

    rejects("records[0].identity_scope does not match native operation",
            mutated(lambda r: r.update(identity_scope="remote")))
    rejects("records[0] must not attach remote identity to a local selector",
            mutated(lambda r: r.update(remote_identity={"qualification": "unqualified"})))
    remote_index = next(i for i, r in enumerate(_DESCRIPTIONS["records"]) if r["selector"]["operation"] == "06")
    rejects(f"records[{remote_index}] must retain remote identity qualification",
            mutated(lambda r: r.update(remote_identity=None), remote_index))
    rejects("records[0].raw_description_hex does not echo GG/RR",
            mutated(lambda r: r.update(raw_description_hex="FF" + r["raw_description_hex"][2:])))
    rejects("records[0].raw_description_hex has unequal limit spans",
            mutated(lambda r: r.update(raw_description_hex=r["raw_description_hex"] + "00")))
    rejects("records[0].description_payload_length does not match raw description",
            mutated(lambda r: r.update(description_payload_length=13)))
    rejects("records[0].raw_limits.min_hex does not match description width",
            mutated(lambda r: r["raw_limits"].update(min_hex="00")))
    rejects("records[0].raw_limits.min_hex does not match raw description",
            mutated(lambda r: r["raw_limits"].update(min_hex="0000A0C2")))
    rejects("records[0].decoded codec basis disagrees with provenance",
            mutated(lambda r: r["decoded"].update(codec_basis="payload_length_inferred")))
    rejects("records[0].decoded.step disagrees with raw limits",
            mutated(lambda r: r["decoded"].update(step=2.0)))


def test_validation_scope_is_derived_both_ways() -> None:
    def mutated(selector: tuple[str, str, str, str], mutate) -> dict:
        document = descriptions()
        index, record = find(document, *selector)
        mutate(record)
        return document, index

    dhw = ("02", "00", "00", "0001")
    document, index = mutated(("02", "04", "01", "000B"), lambda r: r.update(validation_scope="format_range_and_step"))
    rejects(f"records[{index}] grants range validation without a qualified selector codec", document)
    inactive = next(r["selector"] for r in _DESCRIPTIONS["records"]
                    if r["presence_state"] == "observed_inactive" and r["validation_scope"] == "display_only")
    document, index = mutated(tuple(inactive.values()), lambda r: r.update(validation_scope="format_range_and_step"))
    rejects(f"records[{index}] grants range validation without observed presence", document)
    document, index = mutated(("02", "00", "00", "002C"), lambda r: r.update(validation_scope="format_range_and_step"))
    rejects(f"records[{index}] grants range validation on a codec basis that is not a local constraint codec", document)
    document, index = mutated(dhw, lambda r: r.update(validation_scope="display_only"))
    rejects(f"records[{index}].validation_scope must be format_range_and_step for this record", document)
    document, index = mutated(tuple(inactive.values()), lambda r: r.update(validation_scope="raw_evidence_only"))
    rejects(f"records[{index}].validation_scope must be display_only for this record", document)
    document, index = mutated(("02", "04", "01", "000B"), lambda r: r.update(validation_scope="display_only"))
    rejects(f"records[{index}].validation_scope must be raw_evidence_only for this record", document)
    missing = next(r["selector"] for r in _DESCRIPTIONS["records"] if r["raw_description_hex"] is None)
    document, index = mutated(tuple(missing.values()), lambda r: r.update(validation_scope="display_only"))
    rejects(f"records[{index}].validation_scope must be raw_evidence_only for this record", document)


def test_codec_width_and_decode_failures_are_validation_errors() -> None:
    document = descriptions()
    document["records"][0]["decoded"]["codec"] = "UCH"
    rejects("records[0].decoded.codec UCH width disagrees with description span width", document)
    document = descriptions()
    document["records"][0]["decoded"]["codec"] = "XYZ"
    rejects("records[0].decoded.codec is unsupported", document)
    with pytest.raises(validator.ValidationError, match=re.escape("cannot decode EXP limit 00")):
        validator._decode_limit("EXP", "00")
    with pytest.raises(validator.ValidationError, match=re.escape("cannot decode HDA:3 limit 0102")):
        validator._decode_limit("HDA:3", "0102")
    with pytest.raises(validator.ValidationError, match="unsupported qualified codec XYZ"):
        validator._decode_limit("XYZ", "00")


def test_clock_codecs_stay_on_the_hypothesis_basis() -> None:
    document = descriptions()
    _, record = find(document, "02", "00", "00", "002C")
    record["decoded"]["codec_basis"] = "public_local_constraint_codec"
    index, _ = find(document, "02", "00", "00", "002C")
    rejects(f"records[{index}].decoded HDA:3/HTI must use the exact-selector-schema basis, a Hypothesis", document)


def test_remote_identity_and_presence_must_agree() -> None:
    index, record = next((i, r) for i, r in enumerate(_DESCRIPTIONS["records"])
                         if r["presence_state"] == "remote_identity_unqualified" and r["decoded"])
    message = f"records[{index}] unqualified remote identity and remote_identity_unqualified presence must agree"
    document = descriptions()
    document["records"][index]["presence_state"] = "unknown"
    rejects(message, document)
    document = descriptions()
    document["records"][0]["presence_state"] = "remote_identity_unqualified"
    rejects("records[0] unqualified remote identity and remote_identity_unqualified presence must agree", document)
    document = descriptions()
    document["records"][index]["decoded"]["qualification"] = "qualified"
    rejects(f"records[{index}] unqualified remote identity must not carry a qualified codec", document)


def test_dhw_solar_installer_and_ventilation_pins() -> None:
    document = descriptions()
    index, _ = find(document, "02", "00", "00", "0001")
    del document["records"][index]
    rejects("fixture must retain exactly one local DHW bivalence record", document)

    document = descriptions()
    _, record = find(document, "02", "00", "00", "0001")
    set_spans(record, "0000A0C1", "0000A841", "0000803F")
    record["decoded"]["max"] = 21.0
    rejects("BASV0 DHW maximum must retain raw 20", document)

    document = descriptions()
    _, source = find(document, "02", "04", "00", "000B")
    _, solar = find(document, "02", "04", "01", "000B")
    solar["decoded"] = deepcopy(source["decoded"])
    solar["validation_scope"] = "display_only"
    rejects("solar II01 must not gain a qualified codec", document)

    document = descriptions()
    _, installer = find(document, "02", "00", "00", "006C")
    installer["decoded"] = {"codec": "UCH", "codec_provenance": "length_inferred", "codec_basis": "payload_length_inferred",
                            "qualification": "unqualified", "min": 0, "max": 0, "step": 0}
    rejects("installer selector 006C must remain raw", document)

    document = descriptions()
    _, ventilation = find(document, "02", "09", "03", "0001")
    ventilation["observed_read_payload_width"] = 1
    rejects("ventilation II03 RR0001 must retain unknown two-byte evidence", document)

    document = descriptions()
    _, ventilation = find(document, "02", "09", "0A", "0001")
    ventilation["decoded"] = None
    ventilation["validation_scope"] = "raw_evidence_only"
    rejects("ventilation II0A RR0001 codec must remain UIN with width 2", document)

    document = descriptions()
    index, ventilation = find(document, "02", "09", "00", "0001")
    ventilation["decoded"]["codec"] = "UCH"
    rejects(f"records[{index}].decoded.codec UCH width disagrees with description span width", document)


def test_cross_fixture_checks_report_their_own_messages() -> None:
    def mutated_rows(mutate) -> dict:
        rows = observations()
        mutate(rows["records"])
        return rows

    rows = observations()
    rows["observation_id"] = "other"
    rejects("cross-fixture identity mismatch", descriptions(), rows)
    rows = observations()
    rows["description_catalog"] = "other.json"
    rejects("cross-fixture catalog mismatch", descriptions(), rows)
    rejects("observation records[1] description index out of bounds", descriptions(),
            mutated_rows(lambda r: r[1]["description"].update(record_index=99999)))
    rejects("observation records[1] description selector mismatch", descriptions(),
            mutated_rows(lambda r: r[1]["description"].update(record_index=1)))
    rejects("observation records[0] status_only fields are inconsistent", descriptions(),
            mutated_rows(lambda r: r[0].update(observed_payload_width=1)))
    rejects("observation records[0] response state is unsupported", descriptions(),
            mutated_rows(lambda r: r[0].update(response_state="bogus")))
    rejects("observation records[1] unavailable description has raw metadata", descriptions(),
            mutated_rows(lambda r: r[1]["description"].update(acquisition_state="unavailable")))
    unavailable = next(i for i, row in enumerate(_OBSERVATIONS["records"])
                       if row["description"] and row["description"]["acquisition_state"] == "unavailable")
    rejects(f"observation records[{unavailable}] available description lacks raw metadata", descriptions(),
            mutated_rows(lambda r: r[unavailable]["description"].update(acquisition_state="matched")))


def test_cross_fixture_rejects_duplicates_dropped_links_and_disagreements() -> None:
    document = descriptions()
    document["records"].append(deepcopy(document["records"][0]))
    rejects(f"records[{len(document['records']) - 1}] duplicates a description selector", document)

    rows = observations()
    rows["records"].append(deepcopy(rows["records"][0]))
    rejects(f"observation records[{len(rows['records']) - 1}] duplicates an observation selector", descriptions(), rows)

    rows = observations()
    rows["records"][1]["description"] = None
    rejects("observation records[1] drops its description link", descriptions(), rows)

    rows = observations()
    rows["records"][1]["presence_state"] = "unknown"
    rejects("observation records[1] presence state disagrees with description", descriptions(), rows)

    rows = observations()
    rows["records"][1]["name"] = "renamed"
    rejects("observation records[1] name disagrees with description", descriptions(), rows)

    rows = observations()
    rows["records"] = []
    rejects("observations must contain records", descriptions(), rows)
