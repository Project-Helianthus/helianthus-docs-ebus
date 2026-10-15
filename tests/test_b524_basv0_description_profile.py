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
SCOPE_OVERLAY = ROOT / "development/fixtures/b524-basv0-validation-scope-v1.json"
SCOPE_SCHEMA = ROOT / "development/fixtures/b524-basv0-validation-scope-schema-v1.json"
_SCOPES = json.loads(SCOPE_OVERLAY.read_text())


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


def scopes() -> dict:
    return deepcopy(_SCOPES)


def set_scope(overlay: dict, selector: dict, value: str) -> None:
    entry = next(e for e in overlay["records"] if e["selector"] == selector)
    entry["validation_scope"] = value


def rejects(message: str, document: dict, observed: dict | None = None, overlay: dict | None = None) -> None:
    with pytest.raises(validator.ValidationError) as caught:
        validator.validate_documents(document, observed, CATALOG, scopes() if overlay is None else overlay)
    assert str(caught.value) == message


def test_unmutated_documents_pass_in_process() -> None:
    validator.validate_documents(descriptions(), observations(), CATALOG, scopes())


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
    def mutated(selector: tuple[str, str, str, str], value: str, mutate=lambda r: None) -> tuple[dict, dict, int]:
        document, overlay = descriptions(), scopes()
        index, record = find(document, *selector)
        mutate(record)
        set_scope(overlay, record["selector"], value)
        return document, overlay, index

    dhw = ("02", "00", "00", "0001")
    document, overlay, index = mutated(("02", "04", "01", "000B"), "format_range_and_step")
    rejects(f"records[{index}] grants range validation without a qualified selector codec", document, overlay=overlay)
    inactive = next(r["selector"] for r in _DESCRIPTIONS["records"]
                    if r["presence_state"] == "observed_inactive"
                    and next(e for e in _SCOPES["records"] if e["selector"] == r["selector"])["validation_scope"] == "display_only")
    document, overlay, index = mutated(tuple(inactive.values()), "format_range_and_step")
    rejects(f"records[{index}] grants range validation without observed presence", document, overlay=overlay)
    document, overlay, index = mutated(("02", "04", "00", "000B"), "format_range_and_step", lambda r: r.update(presence_state="observed_present"))
    rejects(f"records[{index}] grants range validation on a codec basis that is not a local constraint codec", document, overlay=overlay)
    document, overlay, index = mutated(dhw, "display_only")
    rejects(f"records[{index}].validation_scope must be format_range_and_step for this record", document, overlay=overlay)
    document, overlay, index = mutated(tuple(inactive.values()), "raw_evidence_only")
    rejects(f"records[{index}].validation_scope must be display_only for this record", document, overlay=overlay)
    document, overlay, index = mutated(("02", "04", "01", "000B"), "display_only")
    rejects(f"records[{index}].validation_scope must be raw_evidence_only for this record", document, overlay=overlay)
    missing = next(r["selector"] for r in _DESCRIPTIONS["records"] if r["raw_description_hex"] is None)
    document, overlay, index = mutated(tuple(missing.values()), "display_only")
    rejects(f"records[{index}].validation_scope must be raw_evidence_only for this record", document, overlay=overlay)


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
    overlay = scopes()
    overlay["records"] = [e for e in overlay["records"] if e["selector"] != document["records"][index]["selector"]]
    del document["records"][index]
    rejects("fixture must retain exactly one local DHW bivalence record", document, overlay=overlay)

    document = descriptions()
    _, record = find(document, "02", "00", "00", "0001")
    set_spans(record, "0000A0C1", "0000A841", "0000803F")
    record["decoded"]["max"] = 21.0
    rejects("BASV0 DHW maximum must retain raw 20", document)

    document = descriptions()
    _, source = find(document, "02", "04", "00", "000B")
    _, solar = find(document, "02", "04", "01", "000B")
    solar["decoded"] = deepcopy(source["decoded"])
    overlay = scopes()
    set_scope(overlay, solar["selector"], "display_only")
    rejects("solar II01 must not gain a qualified codec", document, overlay=overlay)

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
    overlay = scopes()
    set_scope(overlay, ventilation["selector"], "raw_evidence_only")
    rejects("ventilation II0A RR0001 codec must remain UIN with width 2", document, overlay=overlay)

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


def test_remaining_record_checks_and_non_object_inputs() -> None:
    missing_index = next(i for i, r in enumerate(_DESCRIPTIONS["records"]) if r["raw_description_hex"] is None)
    document = descriptions()
    document["records"][missing_index]["decoded"] = deepcopy(_DESCRIPTIONS["records"][0]["decoded"])
    rejects(f"records[{missing_index}] cannot decode or bound a missing description", document)

    document = descriptions()
    document["records"][missing_index]["response_state"] = "describe_matched"
    rejects(f"records[{missing_index}] missing description has wrong response state", document)

    document = descriptions()
    document["records"][0]["response_state"] = "describe_unavailable"
    rejects("records[0] retained description has wrong response state", document)

    document = descriptions()
    index, record = find(document, "02", "00", "00", "002C")
    record["decoded"]["step"] = "P1D"
    rejects(f"records[{index}].decoded.step must remain unknown", document)

    document = descriptions()
    document["records"][0]["decoded"] = "EXP"
    rejects("records[0].decoded must be an object or null", document)

    remote = next(i for i, r in enumerate(_DESCRIPTIONS["records"]) if r["presence_state"] == "remote_identity_unqualified")
    document = descriptions()
    document["records"][remote]["decoded"] = []
    rejects(f"records[{remote}].decoded must be an object or null", document)

    rows = observations()
    rows["records"][3] = "not-an-object"
    rejects("observation records[3] must be an object with a selector object", descriptions(), rows)


def test_qualified_codec_is_pinned_to_the_selector() -> None:
    document = descriptions()
    index, record = find(document, "02", "00", "00", "0001")
    assert index == 0 and record["decoded"]["codec"] == "EXP"
    for field in ("min", "max", "step"):
        record["decoded"][field] = int.from_bytes(bytes.fromhex(record["raw_limits"][f"{field}_hex"]), "little")
    record["decoded"]["codec"] = "U32"
    rejects("records[0].decoded.codec U32 disagrees with the register-map Wire codec EXP for OP02/GG00/II00/RR0001", document)

    # Same-width relabelling of a record that is not the first one.
    index = next(i for i, r in enumerate(_DESCRIPTIONS["records"])
                 if r["decoded"] and r["decoded"]["codec"] == "EXP" and r["decoded"]["qualification"] == "qualified")
    document = descriptions()
    selector = document["records"][index]["selector"]
    document["records"][index]["decoded"]["codec"] = "U32"
    assert selector["operation"] == "02"
    with pytest.raises(validator.ValidationError, match="disagrees with the register-map Wire codec EXP"):
        validator.validate_documents(document)

    document = descriptions()
    document["records"][0]["selector"]["register"] = "FFFF"
    document["records"][0]["raw_description_hex"] = "00FFFF" + document["records"][0]["raw_description_hex"][6:]
    rejects("records[0].decoded has no register-map Wire entry for OP02/GG00/II00/RRFFFF", document)

    document = descriptions()
    index, record = find(document, "02", "00", "00", "0034")
    record["decoded"].update(codec="HTI", min="01:01:01", max="31:12:99", step=None)
    rejects(f"records[{index}].decoded.codec HTI disagrees with the calendar/clock selector list (HDA:3) for OP02/GG00/II00/RR0034", document)

    document = descriptions()
    index, record = find(document, "02", "00", "00", "002C")
    record["decoded"]["codec"] = "HTI"
    rejects(f"records[{index}].decoded.codec HTI disagrees with the register-map Wire codec HDA:3 for OP02/GG00/II00/RR002C", document)


def test_unqualified_acquisition_state_implies_no_decoded_codec() -> None:
    rows = observations()
    rows["records"][1]["description"]["acquisition_state"] = "unqualified"
    rejects("observation records[1] unqualified description must not carry a decoded codec", descriptions(), rows)


def test_clock_values_must_be_valid_before_qualification() -> None:
    document = descriptions()
    index, record = find(document, "02", "00", "00", "0035")
    set_spans(record, "000000", "FFFFFF", "010000")
    record["decoded"].update(min="00:00:00", max="255:255:255")
    rejects(f"records[{index}].decoded.max is not a valid time (hour 0-23, minute 0-59, second 0-59)", document)

    document = descriptions()
    index, record = find(document, "02", "00", "00", "002C")
    set_spans(record, "010101", "010D63", "010000")
    record["decoded"].update(min="2001-01-01", max="2099-13-01")
    rejects(f"records[{index}].decoded.max is not a valid date (day, month, year offset 0-99 from 2000)", document)

    document = descriptions()
    index, record = find(document, "02", "00", "00", "002C")
    set_spans(record, "010101", "01016E", "010000")
    record["decoded"].update(max="2110-01-01")
    rejects(f"records[{index}].decoded.max is not a valid date (day, month, year offset 0-99 from 2000)", document)


def test_same_width_relabel_of_record_94_is_rejected() -> None:
    document = descriptions()
    record = document["records"][94]
    assert record["decoded"]["codec"] == "EXP"
    record["decoded"]["codec"] = "U32"
    for field in ("min", "max", "step"):
        record["decoded"][field] = int.from_bytes(bytes.fromhex(record["raw_limits"][f"{field}_hex"]), "little")
    rejects("records[94].decoded.codec U32 disagrees with the register-map Wire codec EXP for OP02/GG02/II01/RR0004", document)


def test_unqualified_decoded_values_are_compared_with_raw_spans() -> None:
    document = descriptions()
    record = document["records"][2]
    # Record 2 stays a candidate decoding: relabel it unqualified so only the generic comparison applies.
    record["decoded"].update(codec_provenance="length_inferred", codec_basis="payload_length_inferred",
                             qualification="unqualified")
    record["validation_scope"] = "raw_evidence_only"
    validator.validate_documents(document)
    record["decoded"]["max"] = 999
    rejects("records[2].decoded.max disagrees with raw limits", document)

    document = descriptions()
    unqualified = next(i for i, r in enumerate(_DESCRIPTIONS["records"])
                       if r["decoded"] and r["decoded"]["qualification"] == "unqualified" and r["decoded"]["codec"] == "UIN")
    document["records"][unqualified]["decoded"]["min"] = 999
    rejects(f"records[{unqualified}].decoded.min disagrees with raw limits", document)


def test_plain_byte_clock_candidates_stay_display_only_even_for_bcd_looking_spans() -> None:
    document = descriptions()
    index, record = find(document, "02", "00", "00", "002C")
    set_spans(record, "010101", "150625", "010000")  # valid packed BCD 15.06.25
    record["decoded"].update(min="2001-01-01", max="2037-06-21")  # plain-byte decoding, not BCD
    overlay = scopes()
    assert next(e for e in overlay["records"] if e["selector"] == record["selector"])["validation_scope"] == "display_only"
    validator.validate_documents(document, None, None, overlay)

    set_scope(overlay, record["selector"], "format_range_and_step")
    rejects(f"records[{index}] grants range validation to a plain-byte HDA:3/HTI candidate decoding, which must stay display_only", document, overlay=overlay)

    document, overlay = descriptions(), scopes()
    index, record = find(document, "02", "00", "00", "0035")
    set_scope(overlay, record["selector"], "format_range_and_step")
    rejects(f"records[{index}] grants range validation to a plain-byte HDA:3/HTI candidate decoding, which must stay display_only", document, overlay=overlay)

    document, overlay = descriptions(), scopes()
    index, record = find(document, "02", "00", "00", "0035")
    set_scope(overlay, record["selector"], "raw_evidence_only")
    rejects(f"records[{index}].validation_scope must be display_only for this record", document, overlay=overlay)


def test_duplicate_selectors_are_rejected_in_both_fixtures() -> None:
    document = descriptions()
    document["records"].append(deepcopy(document["records"][0]))
    index = len(document["records"]) - 1
    rejects(f"records[{index}] duplicates a description selector", document)

    rows = observations()
    rows["records"].append(deepcopy(rows["records"][0]))
    index = len(rows["records"]) - 1
    rejects(f"observation records[{index}] duplicates an observation selector", descriptions(), rows)


def test_qualified_range_in_an_instance_divergent_family_is_rejected() -> None:
    document = descriptions()
    _, record = find(document, "02", "03", "01", "0002")  # EXP 15..30 step 0.5, qualified in every instance
    set_spans(record, "0000A040", "0000F041", "0000003F")
    record["decoded"].update(min=5.0, max=30.0, step=0.5)
    rejects("OP02/GG03/RR0002 qualifies a decoded range although its described instances differ; "
            "the instance byte is not echoed, so a qualified range must be identical across every retained instance", document)


def test_missing_description_does_not_make_a_family_divergent() -> None:
    """GG03/RR0002 II04 has no description; that absent evidence must not disqualify its siblings."""
    _, record = find(descriptions(), "02", "03", "04", "0002")
    assert record["raw_description_hex"] is None
    validator.validate_documents(descriptions(), observations(), CATALOG, scopes())


def test_description_without_observation_record_is_rejected() -> None:
    rows = observations()
    selector = descriptions()["records"][0]["selector"]
    rows["records"] = [row for row in rows["records"] if row["selector"] != selector]
    with pytest.raises(validator.ValidationError, match="has no register-observation record"):
        validator.validate_documents(descriptions(), rows, CATALOG)


def test_moving_a_record_to_another_instance_stays_valid_when_the_family_is_invariant() -> None:
    """Moving GG03/RR0002 II00 to IIFF in both fixtures still validates.

    This is harmless under the invariance rule: a qualified range is accepted only
    where every retained described instance of the selector carries identical
    spans, so the instance byte can never carry a decoded claim and reassigning
    it cannot change what the fixture asserts.
    """
    document, rows = descriptions(), observations()
    _, record = find(document, "02", "03", "00", "0002")
    old = deepcopy(record["selector"])
    record["selector"]["instance"] = "FF"
    for row in rows["records"]:
        if row["selector"] == old:
            row["selector"]["instance"] = "FF"
    validator.validate_documents(document, rows, CATALOG)


@pytest.mark.parametrize("field", ["group", "address_raw", "firmware_raw"])
def test_observed_remote_header_requires_each_retained_header_field(field: str, tmp_path: Path) -> None:
    document = descriptions()
    index = next(i for i, r in enumerate(document["records"])
                 if r["remote_identity"] and r["remote_identity"]["qualification"] == "observed_remote_header")
    del document["records"][index]["remote_identity"][field]
    rejects(f"records[{index}].remote_identity.{field} is required for an observed remote header", document)
    path = tmp_path / "bad-header.json"
    path.write_text(json.dumps(document))
    result = subprocess.run(["jv", str(SCHEMA), str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode != 0


@pytest.mark.parametrize("field,value", [("firmware_raw", "FFFFFF"), ("address_raw", "09")])
def test_one_remote_slot_retains_one_identity(field: str, value: str) -> None:
    document = descriptions()
    slots: dict[tuple, list[int]] = {}
    for i, r in enumerate(document["records"]):
        if r["remote_identity"] and r["remote_identity"]["qualification"] == "observed_remote_header":
            s = r["selector"]
            slots.setdefault((s["operation"], s["group"], s["instance"]), []).append(i)
    members = next(v for v in slots.values() if len(v) > 1)
    document["records"][members[-1]]["remote_identity"][field] = value
    rejects(f"records[{members[-1]}] remote identity (address {document['records'][members[-1]]['remote_identity']['address_raw']}, "
            f"firmware {document['records'][members[-1]]['remote_identity']['firmware_raw']}) differs from records[{members[0]}] in slot "
            f"OP{document['records'][members[0]]['selector']['operation']}/GG{document['records'][members[0]]['selector']['group']}"
            f"/II{document['records'][members[0]]['selector']['instance']}; one slot retains one identity", document)


def test_one_remote_slot_retains_one_identity_qualification() -> None:
    document, rows = descriptions(), observations()
    slots: dict[tuple, list[int]] = {}
    for i, r in enumerate(document["records"]):
        if r["remote_identity"] and r["remote_identity"]["qualification"] == "observed_remote_header":
            s = r["selector"]
            slots.setdefault((s["operation"], s["group"], s["instance"]), []).append(i)
    members = next(v for v in slots.values() if len(v) > 2)
    index = members[1]
    record = document["records"][index]
    record["remote_identity"] = {"qualification": "unqualified"}
    record["presence_state"] = "remote_identity_unqualified"
    for row in rows["records"]:
        if row["selector"] == record["selector"]:
            row["presence_state"] = "remote_identity_unqualified"
    selector = record["selector"]
    rejects(f"records[{index}] remote identity qualification unqualified differs from records[{members[0]}] "
            f"observed_remote_header in slot OP{selector['operation']}/GG{selector['group']}/II{selector['instance']}; "
            "one slot retains one qualification", document, rows)


def test_qualified_codec_width_must_match_observed_read_widths() -> None:
    document, rows = descriptions(), observations()
    record = document["records"][0]
    assert record["decoded"]["qualification"] == "qualified" and record["observed_read_payload_width"] == 4
    record["observed_read_payload_width"] = 5
    for row in rows["records"]:
        if row["selector"] == record["selector"]:
            row["observed_payload_width"] = 5
    rejects("records[0].decoded.codec EXP width 4 contradicts observed_read_payload_width 5", document, rows)


def test_one_remote_slot_retains_one_observation_presence_state() -> None:
    document, rows = descriptions(), observations()
    index = [i for i, row in enumerate(rows["records"])
             if row["selector"]["operation"] == "06" and row["description"] is None
             and row["presence_state"] == "remote_identity_unqualified"][-1]
    slot = (rows["records"][index]["selector"]["group"], rows["records"][index]["selector"]["instance"])
    first = next(i for i, row in enumerate(rows["records"])
                 if row["selector"]["operation"] == "06" and (row["selector"]["group"], row["selector"]["instance"]) == slot)
    assert first < index
    rows["records"][index]["presence_state"] = "observed_present"
    selector = rows["records"][index]["selector"]
    rejects(f"observation records[{index}] presence state observed_present differs from observation records[{first}] "
            f"remote_identity_unqualified in slot OP06/GG{selector['group']}/II{selector['instance']}; "
            "one remote slot retains one presence state", document, rows)


def test_boolean_numeric_limit_is_rejected_by_validator_and_schema(tmp_path: Path) -> None:
    document = descriptions()
    assert document["records"][2]["decoded"]["codec"] == "UCH" and document["records"][2]["decoded"]["max"] == 1
    document["records"][2]["decoded"]["max"] = True
    rejects("records[2].decoded.max must be a number for codec UCH, not bool", document)
    path = tmp_path / "bool-limit.json"
    path.write_text(json.dumps(document))
    result = subprocess.run(["jv", str(SCHEMA), str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode != 0


def test_exact_schema_basis_is_pinned_to_its_documented_selectors() -> None:
    document = descriptions()
    document["records"][0]["decoded"]["codec_basis"] = "public_exact_selector_schema"
    overlay = scopes()
    set_scope(overlay, document["records"][0]["selector"], "display_only")
    rejects("records[0].decoded.codec_basis public_exact_selector_schema is not documented for OP02/GG00/II00/RR0001", document, overlay=overlay)

    exact = [r for r in descriptions()["records"] if r["decoded"] and r["decoded"]["codec_basis"] == "public_exact_selector_schema"]
    assert len(exact) == 14
    assert {(r["selector"]["operation"], r["selector"]["group"], r["selector"]["instance"], r["selector"]["register"]) for r in exact} \
        == validator.EXACT_SCHEMA_SELECTORS
    validator.validate_documents(descriptions(), observations(), CATALOG, scopes())


def test_claimed_selector_provenance_is_validated_even_when_unqualified() -> None:
    document = descriptions()
    index, record = find(document, "02", "03", "00", "0025")
    assert record["decoded"]["qualification"] == "unqualified" and record["decoded"]["codec_provenance"] == "length_inferred"
    record["decoded"].update(codec_provenance="selector_qualified", codec_basis="public_local_constraint_codec")
    rejects(f"records[{index}].decoded has no register-map Wire entry for OP02/GG03/II00/RR0025", document)
    assert not [r for r in _DESCRIPTIONS["records"] if r["decoded"] and r["decoded"]["qualification"] == "unqualified"
                and r["decoded"]["codec_provenance"] == "selector_qualified"]


def test_documented_exact_schema_selectors_must_keep_their_basis() -> None:
    document = descriptions()
    index, record = find(document, "02", "04", "00", "000B")
    assert record["decoded"]["codec"] == "U32" and record["decoded"]["codec_basis"] == "public_exact_selector_schema"
    record["decoded"]["codec_basis"] = "public_local_constraint_codec"
    rejects(f"records[{index}].decoded.codec_basis must be public_exact_selector_schema for the documented "
            "exact-schema selector OP02/GG04/II00/RR000B", document)
    validator.validate_documents(descriptions(), observations(), CATALOG, scopes())


def test_application_overlay_matches_the_cc0_records_and_its_schema() -> None:
    result = subprocess.run(["jv", str(SCOPE_SCHEMA), str(SCOPE_OVERLAY)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    assert len(_SCOPES["records"]) == len(_DESCRIPTIONS["records"]) == 2093
    assert all("validation_scope" not in record for record in _DESCRIPTIONS["records"])
    assert "validation_scope" not in SCHEMA.read_text()

    overlay = scopes()
    overlay["records"].append(deepcopy(overlay["records"][0]))
    rejects(f"validation-scope overlay records[{len(overlay['records']) - 1}] duplicates a selector", descriptions(), overlay=overlay)

    overlay = scopes()
    overlay["records"][0]["selector"]["instance"] = "FF"
    rejects("validation-scope overlay records[0] matches no description record", descriptions(), overlay=overlay)

    overlay = scopes()
    del overlay["records"][5]
    rejects("records[5] has no validation-scope overlay entry", descriptions(), overlay=overlay)


def test_every_catalog_record_needs_an_observation_row_including_unavailable_ones() -> None:
    document, rows = descriptions(), observations()
    index, record = next((i, r) for i, r in enumerate(document["records"]) if r["response_state"] == "describe_unavailable")
    rows["records"] = [row for row in rows["records"] if row["selector"] != record["selector"]]
    with pytest.raises(validator.ValidationError, match="has no register-observation record"):
        validator.validate_documents(document, rows, CATALOG, scopes())
    validator.validate_documents(descriptions(), observations(), CATALOG, scopes())


def test_reversed_temporal_ranges_are_rejected() -> None:
    document = descriptions()
    _, record = find(document, "02", "00", "00", "002C")
    assert document["records"][27] is record and record["decoded"]["codec"] == "HDA:3"
    set_spans(record, "1F0C63", "010101", "010000")
    record["decoded"].update(min="2099-12-31", max="2001-01-01")
    rejects("records[27].decoded HDA:3 min 2099-12-31 is later than max 2001-01-01", document)

    document = descriptions()
    index, record = find(document, "02", "00", "00", "0035")
    assert record["decoded"]["codec"] == "HTI"
    set_spans(record, "173B3B", "000000", "010000")
    record["decoded"].update(min="23:59:59", max="00:00:00")
    rejects(f"records[{index}].decoded HTI min 23:59:59 is later than max 00:00:00", document)

    validator.validate_documents(descriptions(), observations(), CATALOG, scopes())


@pytest.mark.parametrize("value,got", [("00", 1), ("06070000", 4)])
def test_observed_remote_firmware_must_be_three_bytes(value: str, got: int, tmp_path: Path) -> None:
    document = descriptions()
    members = [i for i, r in enumerate(document["records"])
               if r["remote_identity"] and r["remote_identity"]["qualification"] == "observed_remote_header"
               and (r["selector"]["group"], r["selector"]["instance"]) == ("02", "01")]
    assert len(members) > 1
    for i in members:
        document["records"][i]["remote_identity"]["firmware_raw"] = value
    rejects(f"records[{members[0]}].remote_identity.firmware_raw must be 3 bytes (6 hex digits), not {got}", document)
    path = tmp_path / "firmware-width.json"
    path.write_text(json.dumps(document))
    result = subprocess.run(["jv", str(SCHEMA), str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode != 0
    validator.validate_documents(descriptions(), observations(), CATALOG, scopes())
