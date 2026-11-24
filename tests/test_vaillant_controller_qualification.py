from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "vaillant_controller_qualification",
    ROOT / "scripts/validate_vaillant_controller_qualification.py",
)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def fixture() -> dict[str, object]:
    return json.loads((ROOT / "architecture/fixtures/vaillant-controller-qualification-v1.json").read_text())


def thermal() -> dict[str, object]:
    return json.loads((ROOT / "architecture/fixtures/vaillant-semreg-thermal-map-v1.json").read_text())


def test_record_matches_the_decision() -> None:
    CHECKER.validate_fixture(fixture(), thermal())
    assert b"](" not in CHECKER.receipt_bytes()
    record = fixture()
    assert record["scope"] == "native_controller_qualification"
    assert record["revision"] == "vaillant-controller-qualification-evidence-gap/v1"
    assert record["qualified_use_permitted"] is True
    assert "write_or_operation_authority" not in json.dumps(record)
    pairs = [(row[0], row[1]) for row in CHECKER.load_crosswalk()]
    identities = record["identities"]
    assert [(item["device_id"], item["product_number"]) for item in identities] == pairs
    assert {item["level"] for item in identities} == {"declared"}
    labels = {row[3] for row in CHECKER.load_crosswalk()}
    assert labels.isdisjoint(set(CHECKER._walk_strings(record)))


def test_each_identity_field_rejects_its_mutation() -> None:
    # device_id: a substituted id is not the crosswalk pair.
    # product_number: a substituted number is not the crosswalk pair.
    # level: tested_on_hardware without a record path is refused.
    # evidence_grade: a grade other than the crosswalk Hypothesis grade is refused.
    candidate = deepcopy(fixture())
    candidate["identities"][0]["device_id"] = "ZZZ00"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())

    candidate = deepcopy(fixture())
    candidate["identities"][0]["product_number"] = "0000"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())

    candidate = deepcopy(fixture())
    candidate["identities"][0]["evidence_grade"] = "Proven"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())

    candidate = deepcopy(fixture())
    candidate["identities"][0]["level"] = "tested_on_hardware"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())
    candidate["hardware_test_record"] = "architecture/fixtures/vaillant-controller-qualification-v1.json"
    CHECKER.validate_fixture(candidate, thermal())


def test_pair_missing_or_added_to_the_crosswalk_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = CHECKER.load_crosswalk()
    monkeypatch.setattr(CHECKER, "load_crosswalk", lambda: rows[:-1])
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(fixture(), thermal())

    added = rows + [[rows[0][0], "0000", rows[0][2], rows[0][3]]]
    monkeypatch.setattr(CHECKER, "load_crosswalk", lambda: added)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(fixture(), thermal())


def test_unlisted_matrix_row_and_unknown_family_fail() -> None:
    candidate = deepcopy(fixture())
    extra = deepcopy(candidate["declared_rows"][0])  # type: ignore[index]
    extra["register"] = "0x0096"
    candidate["declared_rows"].append(extra)  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())

    unknown = next(item for item in candidate["vectors"] if item["id"] == "unknown_family")  # type: ignore[union-attr]
    got = CHECKER._run_vector(unknown)
    assert got["outcome"] == "unknown"
    unknown["expect"] = {"outcome": "qualified"}
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())


def test_tampered_digest_fails() -> None:
    candidate = deepcopy(fixture())
    candidate["sources"]["crosswalk_sha256"] = "0" * 64  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())


def test_qualified_use_permitted_stays_true_while_declared() -> None:
    candidate = deepcopy(fixture())
    candidate["qualified_use_permitted"] = False
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())


def test_product_line_name_is_not_a_key() -> None:
    candidate = deepcopy(fixture())
    label = CHECKER.load_crosswalk()[0][3]
    candidate["write_permission"] = str(candidate["write_permission"]) + " " + label
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())


def test_vector_that_contradicts_the_rule_fails() -> None:
    candidate = deepcopy(fixture())
    success = next(item for item in candidate["vectors"] if item["id"] == "exact_success_70000")  # type: ignore[union-attr]
    success["expect"] = {"outcome": "unknown"}
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())


@pytest.mark.parametrize(
    ("field", "value"),
    (("path", "architecture/fixtures/not-the-receipt.json"), ("sha256", "a" * 64), ("sha256_path", "architecture/fixtures/not-the-receipt.sha256")),
)
def test_rejects_hostile_receipt_substitution(field: str, value: str) -> None:
    candidate = deepcopy(fixture())
    candidate["context_receipt"][field] = value  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())


def test_rejects_digest_mismatch_for_the_exact_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(CHECKER, "receipt_bytes", lambda: b"not the pinned receipt")
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(fixture(), thermal())


def test_rejects_receipt_provenance_or_sidecar_substitution(monkeypatch: pytest.MonkeyPatch) -> None:
    original_receipt_bytes = CHECKER.receipt_bytes
    receipt = deepcopy(CHECKER.RECEIPT)
    receipt["canonical_upstream"]["revision"] = "f" * 40
    monkeypatch.setattr(CHECKER, "receipt_bytes", lambda: json.dumps(receipt).encode())
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(fixture(), thermal())

    sidecar = Path(CHECKER.CONTEXT_RECEIPT["sha256_path"])
    original_read_text = Path.read_text

    def bad_sidecar(path: Path, *args: object, **kwargs: object) -> str:
        if path == sidecar:
            return "a" * 64 + "  wrong.json\n"
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", bad_sidecar)
    monkeypatch.setattr(CHECKER, "receipt_bytes", original_receipt_bytes)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(fixture(), thermal())


def test_transition_action_stays_atomic() -> None:
    candidate = deepcopy(fixture())
    candidate["transition_contract"]["valid_direct_conflicting_observation"] = "reject_without_mutation"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())

    changed_thermal = deepcopy(thermal())
    changed_thermal["qualification"]["runtime_qualification_permitted"] = False  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(fixture(), changed_thermal)


def test_declared_thermal_elements_keep_their_subjects() -> None:
    # The public Thermal pack assigns outdoor air and system flow to the
    # thermal system, room air to a zone, circuit flow to a circuit, hot-water
    # measured temperature to DHW and boiler flow to a heat generator.
    expected = {
        ("0x00", "0x0073"): "thermal.measurement.outdoor_air_temperature",
        ("0x00", "0x004B"): "thermal.measurement.system_flow_temperature",
        ("0x01", "0x0005"): "thermal.measurement.dhw_temperature",
        ("0x02", "0x0008"): "thermal.measurement.circuit_flow_temperature",
        ("0x03", "0x000F"): "thermal.measurement.air_temperature",
    }
    rows = {(row[0], row[1]): row[3] for row in CHECKER.DECLARED_PAGE_ROWS}
    assert {key: rows[key] for key in expected} == expected
    declared = {(row["group"], row["register"]): row["semreg_element"] for row in fixture()["declared_rows"]}  # type: ignore[index]
    assert {key: declared[key] for key in expected} == expected
    assert CHECKER.BOILER_TARGET["flow_row"]["semreg_element"] == "thermal.measurement.heat_generator_flow_temperature"
