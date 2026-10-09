import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "development" / "fixtures"


def validate(schema: str, instance: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["jv", str(FIXTURES / schema), str(FIXTURES / instance)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_explicit_read_plan_and_additive_artifact_validate() -> None:
    assert validate("b524-operation-read-plan-schema-v1.json", "b524-operation-read-plan-synthetic-v1.json").returncode == 0
    assert validate("b524-operation-reads-artifact-schema-v1.json", "b524-operation-reads-artifact-synthetic-v1.json").returncode == 0


def test_plan_uses_operation_derived_opcode_and_exact_timer_channels() -> None:
    plan = json.loads((FIXTURES / "b524-operation-read-plan-synthetic-v1.json").read_text())
    assert [item["operation"] for item in plan["requests"]] == [
        "ReadTimer", "ReadVR91", "GetEvent", "GetEventSetPoint"
    ]
    assert all("opcode" not in item for item in plan["requests"])
    assert plan["requests"][0]["channel"] == "ventilation"
    assert plan["requests"][2]["weekday_code"] == 0


def test_plan_rejects_boolean_and_redundant_opcode(tmp_path: Path) -> None:
    plan = json.loads((FIXTURES / "b524-operation-read-plan-synthetic-v1.json").read_text())
    plan["requests"][0]["instance"] = True
    plan["requests"][2]["opcode"] = "0x09"
    candidate = tmp_path / "invalid-plan.json"
    candidate.write_text(json.dumps(plan))
    result = subprocess.run(
        ["jv", str(FIXTURES / "b524-operation-read-plan-schema-v1.json"), str(candidate)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
def test_read_plan_enforces_operation_specific_selector_ranges(tmp_path: Path) -> None:
    source = json.loads((FIXTURES / "b524-operation-read-plan-synthetic-v1.json").read_text())
    rejected = (
        (0, {"instance": 1}),
        (2, {"address": 4}),
        (2, {"profile": "dhw", "address": 3}),
        (3, {"address": 3}),
    )
    for case, (index, mutation) in enumerate(rejected):
        plan = json.loads(json.dumps(source))
        plan["requests"][index].update(mutation)
        candidate = tmp_path / f"invalid-selector-{case}.json"
        candidate.write_text(json.dumps(plan))
        assert subprocess.run(
            ["jv", str(FIXTURES / "b524-operation-read-plan-schema-v1.json"), str(candidate)],
            capture_output=True,
            text=True,
            check=False,
        ).returncode != 0

    source["requests"][2].update({"instance": 255, "address": 3})
    source["requests"][0].update({"channel": "zone-cooling", "instance": 255})
    candidate = tmp_path / "event-instance-remains-u8.json"
    candidate.write_text(json.dumps(source))
    assert subprocess.run(
        ["jv", str(FIXTURES / "b524-operation-read-plan-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0


def test_artifact_keeps_raw_event_boundary() -> None:
    artifact = json.loads((FIXTURES / "b524-operation-reads-artifact-synthetic-v1.json").read_text())
    first, vr91, event, unattempted = artifact["b524_operation_reads"]
    assert artifact["schema_version"] == "2.3"
    assert first["selector_correlation"] == "request_context"
    assert first["decoded"] == {
        "parameter_config": 0,
        "slots": [
            {
                "start_raw": 0,
                "stop_raw": 0,
                "start_minutes": None,
                "stop_minutes": None,
                "unused": False,
            },
            {
                "start_raw": 0,
                "stop_raw": 0,
                "start_minutes": None,
                "stop_minutes": None,
                "unused": False,
            },
            {
                "start_raw": 0,
                "stop_raw": 0,
                "start_minutes": None,
                "stop_minutes": None,
                "unused": False,
            },
        ],
        "raw_hex": "00000000000000",
    }
    assert vr91["decoded"]["binding_zone"] == 0
    assert "parameter_config" not in vr91["decoded"]
    assert vr91["decode_qualification"] == "schema_unqualified"
    assert vr91["trace_seq"] == 12
    assert event["pair_context"] == event["selector"]
    assert event["response_state"] == "value"
    assert event["decoded"]["parameter_config"] == 0
    assert event["decode_qualification"] == "schema_unqualified"
    assert unattempted["response_state"] == "unattempted"
    assert unattempted["request_attempts"] == 0
    assert unattempted["error"] == "request_budget_exhausted"
    assert unattempted["selector"] == {}
    assert unattempted["raw_selector"]["weekday_code"] == 0
    assert unattempted["trace_seq"] == 14


def test_profile_vrc700_decode_requires_matching_resolved_target_identity(
    tmp_path: Path,
) -> None:
    source = json.loads(
        (FIXTURES / "b524-operation-reads-artifact-synthetic-v1.json").read_text()
    )

    for index in (0, 1):
        artifact = json.loads(json.dumps(source))
        artifact["b524_operation_reads"][index]["decode_qualification"] = "profile_vrc700"
        candidate = tmp_path / f"profile-without-identity-{index}.json"
        candidate.write_text(json.dumps(artifact))
        assert subprocess.run(
            ["jv", str(FIXTURES / "b524-operation-reads-artifact-schema-v1.json"), str(candidate)],
            capture_output=True,
            text=True,
            check=False,
        ).returncode != 0
        assert subprocess.run(
            ["python3", "scripts/validate_b524_operation_reads_artifact.py", str(candidate)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).returncode != 0

    qualified = json.loads(json.dumps(source))
    qualified["b524_operation_reads"][1]["decode_qualification"] = "profile_vrc700"
    qualified["meta"] = {
        "resolved_identity": {
            "manufacturer": "0xB5",
            "device_id": "70000",
            "eid": "70000",
        }
    }
    candidate = tmp_path / "qualified-profile.json"
    candidate.write_text(json.dumps(qualified))
    assert subprocess.run(
        ["jv", str(FIXTURES / "b524-operation-reads-artifact-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0
    assert subprocess.run(
        ["python3", "scripts/validate_b524_operation_reads_artifact.py", str(candidate)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0

    for case, identity in enumerate(
        (
            {"manufacturer": "0x50", "device_id": "70000", "eid": "70000"},
            {"manufacturer": "0xB5", "device_id": "70000", "eid": "B7S00"},
        )
    ):
        mismatched = json.loads(json.dumps(qualified))
        mismatched["meta"]["resolved_identity"] = identity
        candidate = tmp_path / f"mismatched-profile-identity-{case}.json"
        candidate.write_text(json.dumps(mismatched))
        assert subprocess.run(
            ["jv", str(FIXTURES / "b524-operation-reads-artifact-schema-v1.json"), str(candidate)],
            capture_output=True,
            text=True,
            check=False,
        ).returncode != 0
        assert subprocess.run(
            ["python3", "scripts/validate_b524_operation_reads_artifact.py", str(candidate)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).returncode != 0


def test_raw_selectors_enforce_operation_specific_day_fields_and_exclude_vr91(
    tmp_path: Path,
) -> None:
    source = json.loads(
        (FIXTURES / "b524-operation-reads-artifact-synthetic-v1.json").read_text()
    )
    cases = []

    event_conflict = json.loads(json.dumps(source))
    event_conflict["b524_operation_reads"][-1]["raw_selector"]["weekday"] = 1
    cases.append(event_conflict)

    event_wrong_field = json.loads(json.dumps(source))
    event_raw = event_wrong_field["b524_operation_reads"][-1]["raw_selector"]
    event_raw["weekday"] = event_raw.pop("weekday_code")
    cases.append(event_wrong_field)

    for timer_raw in (
        {"system_type": 0, "instance": 0, "address": 1, "weekday": 0, "weekday_code": 1},
        {"system_type": 0, "instance": 0, "address": 1, "weekday_code": 0},
    ):
        timer = json.loads(json.dumps(source))
        timer_record = timer["b524_operation_reads"][0]
        timer_record["selector"] = {}
        timer_record["raw_selector"] = timer_raw
        timer_record["decoded"] = None
        cases.append(timer)

    vr91 = json.loads(json.dumps(source))
    vr91["b524_operation_reads"][1]["raw_selector"] = {
        "system_type": 0,
        "instance": 0,
        "address": 1,
        "weekday": 0,
    }
    cases.append(vr91)

    for case, artifact in enumerate(cases):
        candidate = tmp_path / f"invalid-operation-raw-selector-{case}.json"
        candidate.write_text(json.dumps(artifact))
        schema_result = subprocess.run(
            ["jv", str(FIXTURES / "b524-operation-reads-artifact-schema-v1.json"), str(candidate)],
            capture_output=True,
            text=True,
            check=False,
        )
        semantic_result = subprocess.run(
            ["python3", "scripts/validate_b524_operation_reads_artifact.py", str(candidate)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert schema_result.returncode != 0, case
        assert semantic_result.returncode != 0, case


def test_unattempted_cannot_claim_an_attempt(tmp_path: Path) -> None:
    artifact = json.loads((FIXTURES / "b524-operation-reads-artifact-synthetic-v1.json").read_text())
    artifact["b524_operation_reads"][-1]["request_attempts"] = 1
    candidate = tmp_path / "invalid-unattempted.json"
    candidate.write_text(json.dumps(artifact))
    result = subprocess.run(
        ["jv", str(FIXTURES / "b524-operation-reads-artifact-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0


def test_artifact_response_states_require_consistent_attempt_raw_and_decode_evidence(
    tmp_path: Path,
) -> None:
    source = json.loads((FIXTURES / "b524-operation-reads-artifact-synthetic-v1.json").read_text())
    mutations = (
        {"response_state": "value", "request_attempts": 0},
        {"response_state": "value", "response_raw_hex": None},
        {"response_state": "empty", "response_raw_hex": "", "decoded": {}},
        {"response_state": "nack", "response_raw_hex": None, "decoded": {}, "error": "nack"},
        {"response_state": "timeout", "response_raw_hex": None, "decoded": {}, "error": "timeout"},
        {"response_state": "transport_error", "response_raw_hex": None, "decoded": {}, "error": "transport_error"},
        {"response_state": "malformed", "response_raw_hex": "01", "decoded": {}, "error": "malformed_response"},
        {"response_state": "malformed", "response_raw_hex": None, "decoded": None, "error": "malformed_response"},
        {"response_state": "unattempted", "request_attempts": 0, "response_raw_hex": None, "decoded": {}, "error": "request_budget_exhausted"},
    )
    for case, mutation in enumerate(mutations):
        artifact = json.loads(json.dumps(source))
        artifact["b524_operation_reads"][0].update(mutation)
        candidate = tmp_path / f"incoherent-state-{case}.json"
        candidate.write_text(json.dumps(artifact))
        schema_result = subprocess.run(
            ["jv", str(FIXTURES / "b524-operation-reads-artifact-schema-v1.json"), str(candidate)],
            capture_output=True,
            text=True,
            check=False,
        )
        semantic_result = subprocess.run(
            ["python3", "scripts/validate_b524_operation_reads_artifact.py", str(candidate)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert schema_result.returncode != 0, case
        assert semantic_result.returncode != 0, case


def test_artifact_enforces_backend_response_lengths_and_preserves_raw_only_replay(
    tmp_path: Path,
) -> None:
    source = json.loads((FIXTURES / "b524-operation-reads-artifact-synthetic-v1.json").read_text())
    for case, (index, raw_hex) in enumerate(((0, "00" * 8), (1, "00" * 7), (2, "00" * 7))):
        artifact = json.loads(json.dumps(source))
        artifact["b524_operation_reads"][index]["response_raw_hex"] = raw_hex
        candidate = tmp_path / f"wrong-value-length-{case}.json"
        candidate.write_text(json.dumps(artifact))
        assert subprocess.run(
            ["jv", str(FIXTURES / "b524-operation-reads-artifact-schema-v1.json"), str(candidate)],
            capture_output=True,
            text=True,
            check=False,
        ).returncode != 0
        assert subprocess.run(
            ["python3", "scripts/validate_b524_operation_reads_artifact.py", str(candidate)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).returncode != 0

    raw_only = json.loads(json.dumps(source))
    raw_only_record = raw_only["b524_operation_reads"][3]
    raw_only_record.update(
        {
            "response_raw_hex": "0001020304050607",
            "response_state": "value",
            "request_attempts": 1,
        }
    )
    raw_only_record.pop("error")
    candidate = tmp_path / "raw-only-value-replay.json"
    candidate.write_text(json.dumps(raw_only))
    assert subprocess.run(
        ["jv", str(FIXTURES / "b524-operation-reads-artifact-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0
    assert subprocess.run(
        ["python3", "scripts/validate_b524_operation_reads_artifact.py", str(candidate)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0

    malformed = json.loads(json.dumps(source))
    malformed["b524_operation_reads"][0].update(
        {
            "response_raw_hex": "01",
            "response_state": "malformed",
            "decoded": None,
            "error": "malformed_response",
        }
    )
    candidate = tmp_path / "malformed-keeps-raw-evidence.json"
    candidate.write_text(json.dumps(malformed))
    assert subprocess.run(
        ["jv", str(FIXTURES / "b524-operation-reads-artifact-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0
    assert subprocess.run(
        ["python3", "scripts/validate_b524_operation_reads_artifact.py", str(candidate)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0


def _event_setpoint_record(profile: str, raw_hex: str) -> dict:
    raw = bytes.fromhex(raw_hex)
    if profile == "dhw":
        values = [
            {
                "raw": value,
                "temperature_c": None,
                "state": {253: "enable", 254: "disable", 255: "replacement"}.get(value),
            }
            for value in raw[1:]
        ]
        system_type = 1
    else:
        values = [
            {"raw": value, "temperature_c": value / 2.0, "state": None}
            for value in raw[1:]
        ]
        system_type = 0 if profile == "system" else 3
    selector = {"profile": profile, "instance": 255, "address": 1, "weekday_code": 255}
    return {
        "operation": "GetEventSetPoint",
        "opcode_hex": "0x0B",
        "selector": selector,
        "pair_context": dict(selector),
        "request_payload_hex": f"0b{system_type:02x}ff01ff",
        "response_raw_hex": raw_hex,
        "response_state": "value",
        "decoded": {"parameter_config": raw[0], "values": values, "raw_hex": raw_hex},
        "decode_qualification": "schema_unqualified",
        "selector_correlation": "request_context",
        "request_attempts": 1,
    }


def test_decoded_value_schema_requires_complete_backend_shapes(tmp_path: Path) -> None:
    source = json.loads((FIXTURES / "b524-operation-reads-artifact-synthetic-v1.json").read_text())
    cases = []

    timer = json.loads(json.dumps(source))
    timer["b524_operation_reads"][0]["decoded"]["parameter_config"] = "invalid"
    cases.append(("timer", timer))

    event = json.loads(json.dumps(source))
    event["b524_operation_reads"][2]["decoded"]["starts"][0]["minutes"] = "20"
    cases.append(("event", event))

    setpoint = json.loads(json.dumps(source))
    setpoint["b524_operation_reads"][2] = _event_setpoint_record(
        "system", "0001020304050607"
    )
    setpoint["b524_operation_reads"][2]["decoded"]["values"][0]["state"] = "enable"
    cases.append(("event-setpoint", setpoint))

    for name, artifact in cases:
        candidate = tmp_path / f"invalid-{name}-shape.json"
        candidate.write_text(json.dumps(artifact))
        assert subprocess.run(
            ["jv", str(FIXTURES / "b524-operation-reads-artifact-schema-v1.json"), str(candidate)],
            capture_output=True,
            text=True,
            check=False,
        ).returncode != 0, name


def test_semantic_validator_correlates_known_decodes_to_retained_raw_bytes(
    tmp_path: Path,
) -> None:
    source = json.loads((FIXTURES / "b524-operation-reads-artifact-synthetic-v1.json").read_text())
    mutations = (
        (0, lambda decoded: decoded.update({"parameter_config": 1})),
        (0, lambda decoded: decoded["slots"][0].update({"start_raw": 1})),
        (0, lambda decoded: decoded["slots"][0].update({"start_minutes": 0})),
        (0, lambda decoded: decoded["slots"][0].update({"unused": True})),
        (0, lambda decoded: decoded.update({"raw_hex": "01000000000000"})),
        (1, lambda decoded: decoded.update({"binding_zone": 1})),
        (1, lambda decoded: decoded.update({"raw_hex": "0101020304050607"})),
        (2, lambda decoded: decoded.update({"parameter_config": 1})),
        (2, lambda decoded: decoded.update({"start1_raw": 2})),
        (2, lambda decoded: decoded["starts"][0].update({"raw": 3})),
        (2, lambda decoded: decoded["starts"][0].update({"minutes": None})),
        (2, lambda decoded: decoded.update({"raw_hex": "0101020304050607"})),
    )
    for case, (index, mutation) in enumerate(mutations):
        artifact = json.loads(json.dumps(source))
        mutation(artifact["b524_operation_reads"][index]["decoded"])
        candidate = tmp_path / f"decoded-raw-mismatch-{case}.json"
        candidate.write_text(json.dumps(artifact))
        result = subprocess.run(
            ["python3", "scripts/validate_b524_operation_reads_artifact.py", str(candidate)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0, case


def test_event_setpoint_decodes_follow_profile_without_claiming_native_qualification(
    tmp_path: Path,
) -> None:
    source = json.loads((FIXTURES / "b524-operation-reads-artifact-synthetic-v1.json").read_text())
    cases = (
        ("system", "0001020304050607"),
        ("zone", "0001020304050607"),
        ("dhw", "00fdfeff00010203"),
    )
    for profile, raw_hex in cases:
        artifact = json.loads(json.dumps(source))
        artifact["b524_operation_reads"][2] = _event_setpoint_record(profile, raw_hex)
        candidate = tmp_path / f"{profile}-event-setpoint.json"
        candidate.write_text(json.dumps(artifact))
        assert subprocess.run(
            ["jv", str(FIXTURES / "b524-operation-reads-artifact-schema-v1.json"), str(candidate)],
            capture_output=True,
            text=True,
            check=False,
        ).returncode == 0
        result = subprocess.run(
            ["python3", "scripts/validate_b524_operation_reads_artifact.py", str(candidate)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        record = artifact["b524_operation_reads"][2]
        assert record["decode_qualification"] == "schema_unqualified"

        record["decoded"]["values"][0]["temperature_c"] = 99
        candidate.write_text(json.dumps(artifact))
        assert subprocess.run(
            ["python3", "scripts/validate_b524_operation_reads_artifact.py", str(candidate)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).returncode != 0


def test_native_write_qualification_rejects_scope_selector_mismatch_and_boolean(tmp_path: Path) -> None:
    assert validate(
        "b524-native-write-qualification-schema-v1.json",
        "b524-native-write-qualification-synthetic-v1.json",
    ).returncode == 0
    qualification = {
        "schema_version": 1, "scope": "timer_write_op04", "manufacturer": 181,
        "device_id": "70000", "profile": "vrc700", "model": "VRC700",
        "software_raw_hex": "0417", "selector": {
            "channel": "ventilation", "instance": True, "weekday": 0
        },
        "evidence_reference": "synthetic", "native_qualified": True,
    }
    candidate = tmp_path / "invalid-qualification.json"
    candidate.write_text(json.dumps(qualification))
    result = subprocess.run(
        ["jv", str(FIXTURES / "b524-native-write-qualification-schema-v1.json"), str(candidate)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    qualification["scope"] = "event_write_op0a"
    qualification["selector"] = {"channel": "ventilation", "instance": 0, "weekday": 0}
    candidate.write_text(json.dumps(qualification))
    result = subprocess.run(
        ["jv", str(FIXTURES / "b524-native-write-qualification-schema-v1.json"), str(candidate)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0


def test_bundled_synthetic_qualification_is_structural_and_fail_closed(tmp_path: Path) -> None:
    fixture = json.loads(
        (FIXTURES / "b524-native-write-qualification-synthetic-v1.json").read_text()
    )
    schema_path = FIXTURES / "b524-native-write-qualification-schema-v1.json"
    schema = json.loads(schema_path.read_text())
    assert fixture["native_qualified"] is False
    assert fixture["evidence_reference"] == "synthetic-contract-fixture"
    assert schema["properties"]["native_qualified"] == {"type": "boolean"}
    assert subprocess.run(
        ["jv", str(schema_path), str(FIXTURES / "b524-native-write-qualification-synthetic-v1.json")],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0

    structurally_positive = {**fixture, "native_qualified": True}
    candidate = tmp_path / "structurally-positive.json"
    candidate.write_text(json.dumps(structurally_positive))
    assert subprocess.run(
        ["jv", str(schema_path), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0


def test_edit_and_qualification_schemas_share_selector_and_timer_value_bounds(
    tmp_path: Path,
) -> None:
    edit = json.loads((FIXTURES / "b524-operation-edit-plan-synthetic-v1.json").read_text())
    invalid_edits = (
        {"destination_address": True},
        {"destination_address": 256},
        {"selector": {**edit["selector"], "instance": 1}},
        {"values": [[0, 145], None, None]},
        {"values": [[144, 144], None, None]},
    )
    for case, mutation in enumerate(invalid_edits):
        candidate_document = {**edit, **mutation}
        candidate = tmp_path / f"invalid-edit-{case}.json"
        candidate.write_text(json.dumps(candidate_document))
        assert subprocess.run(
            ["jv", str(FIXTURES / "b524-operation-edit-plan-schema-v1.json"), str(candidate)],
            capture_output=True,
            text=True,
            check=False,
        ).returncode != 0

    bounded_edit = {**edit, "values": [[0, 144], None, None]}
    candidate = tmp_path / "bounded-timer-edit.json"
    candidate.write_text(json.dumps(bounded_edit))
    assert subprocess.run(
        ["jv", str(FIXTURES / "b524-operation-edit-plan-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0

    bounded_edit["selector"] = {
        "channel": "zone-heating",
        "instance": 255,
        "weekday": 6,
    }
    candidate.write_text(json.dumps(bounded_edit))
    assert subprocess.run(
        ["jv", str(FIXTURES / "b524-operation-edit-plan-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0

    event_edit = {
        "schema_version": 1,
        "destination_address": 0x26,
        "operation": "SetEvent",
        "selector": {
            "profile": "system",
            "instance": 255,
            "address": 3,
            "weekday_code": 255,
        },
        "values": [0, 1, 2, 3, 4, 5, 6],
        "expected_before_raw_hex": ["00" * 8, "00" * 8],
    }
    candidate = tmp_path / "event-edit-instance-u8.json"
    candidate.write_text(json.dumps(event_edit))
    assert subprocess.run(
        ["jv", str(FIXTURES / "b524-operation-edit-plan-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0
    event_edit["selector"]["address"] = 4
    candidate.write_text(json.dumps(event_edit))
    assert subprocess.run(
        ["jv", str(FIXTURES / "b524-operation-edit-plan-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode != 0

    missing_target = dict(edit)
    del missing_target["destination_address"]
    candidate = tmp_path / "missing-edit-target.json"
    candidate.write_text(json.dumps(missing_target))
    assert subprocess.run(
        ["jv", str(FIXTURES / "b524-operation-edit-plan-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode != 0

    qualification = json.loads(
        (FIXTURES / "b524-native-write-qualification-synthetic-v1.json").read_text()
    )
    qualification["selector"]["instance"] = 1
    candidate = tmp_path / "invalid-timer-qualification.json"
    candidate.write_text(json.dumps(qualification))
    assert subprocess.run(
        ["jv", str(FIXTURES / "b524-native-write-qualification-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode != 0

    qualification.update(
        {
            "scope": "event_write_op0a",
            "selector": {"profile": "system", "instance": 255, "address": 3, "weekday_code": 255},
        }
    )
    candidate = tmp_path / "event-qualification-instance-u8.json"
    candidate.write_text(json.dumps(qualification))
    assert subprocess.run(
        ["jv", str(FIXTURES / "b524-native-write-qualification-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0
    qualification["selector"]["address"] = 4
    candidate.write_text(json.dumps(qualification))
    assert subprocess.run(
        ["jv", str(FIXTURES / "b524-native-write-qualification-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode != 0


def test_artifact_semantic_validator_rejects_wrong_payload_and_event_qualification(
    tmp_path: Path,
) -> None:
    artifact = json.loads((FIXTURES / "b524-operation-reads-artifact-synthetic-v1.json").read_text())
    artifact["b524_operation_reads"][0]["request_payload_hex"] = "0300000200"
    artifact["b524_operation_reads"][2]["decode_qualification"] = "profile_vrc700"
    candidate = tmp_path / "invalid-artifact.json"
    candidate.write_text(json.dumps(artifact))
    result = subprocess.run(
        ["python3", "scripts/validate_b524_operation_reads_artifact.py", str(candidate)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0


def test_artifact_semantic_validator_rejects_unsupported_canonical_selectors_and_raw_decode(
    tmp_path: Path,
) -> None:
    source = json.loads((FIXTURES / "b524-operation-reads-artifact-synthetic-v1.json").read_text())
    cases = (
        ("timer-instance", 0, {"selector": {"channel": "ventilation", "instance": 1, "weekday": 0}, "request_payload_hex": "0300010100"}),
        ("event-address", 2, {"selector": {"profile": "system", "instance": 0, "address": 4, "weekday_code": 255}, "pair_context": {"profile": "system", "instance": 0, "address": 4, "weekday_code": 255}, "request_payload_hex": "09000004ff"}),
        ("raw-decode", 3, {"decoded": {}}),
    )
    for name, index, mutation in cases:
        artifact = json.loads(json.dumps(source))
        artifact["b524_operation_reads"][index].update(mutation)
        candidate = tmp_path / f"{name}.json"
        candidate.write_text(json.dumps(artifact))
        result = subprocess.run(
            ["python3", "scripts/validate_b524_operation_reads_artifact.py", str(candidate)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        assert result.returncode != 0, name


def test_artifact_semantic_validator_allows_explicit_event_instance_without_pair_context(tmp_path: Path) -> None:
    artifact = json.loads((FIXTURES / "b524-operation-reads-artifact-synthetic-v1.json").read_text())
    del artifact["b524_operation_reads"][2]["pair_context"]
    artifact["b524_operation_reads"][2].update({"selector": {"profile": "dhw", "instance": 1, "address": 1, "weekday_code": 255}, "request_payload_hex": "09010101ff"})
    candidate = tmp_path / "event-without-pair-context.json"
    candidate.write_text(json.dumps(artifact))
    result = subprocess.run(
        ["python3", "scripts/validate_b524_operation_reads_artifact.py", str(candidate)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_event_artifact_cannot_claim_profile_qualification(tmp_path: Path) -> None:
    artifact = json.loads((FIXTURES / "b524-operation-reads-artifact-synthetic-v1.json").read_text())
    artifact["b524_operation_reads"][2]["decode_qualification"] = "profile_vrc700"
    candidate = tmp_path / "invalid-event-qualification.json"
    candidate.write_text(json.dumps(artifact))
    assert validate(
        "b524-operation-reads-artifact-schema-v1.json", str(candidate)
    ).returncode != 0


def test_write_edit_plan_is_preview_first_and_native_qualification_is_scoped() -> None:
    plan = FIXTURES / "b524-operation-edit-plan-synthetic-v1.json"
    schema = FIXTURES / "b524-operation-edit-plan-schema-v1.json"
    assert subprocess.run(["jv", str(schema), str(plan)], capture_output=True, text=True).returncode == 0
    text = (ROOT / "development" / "ebus-vaillant-b524-operation-reads.md").read_text()
    assert "offline preview and diff" in text
    assert "Event execution stays disabled pending a qualified native Event contract" in text
    qualification = json.loads((FIXTURES / "b524-native-write-qualification-schema-v1.json").read_text())
    edit_schema = json.loads(schema.read_text())
    assert qualification["properties"]["manufacturer"]["const"] == 181
    assert "profile" in qualification["required"]
    assert qualification["properties"]["software_raw_hex"]["pattern"] == "^[0-9A-Fa-f]{4}$"
    assert qualification["properties"]["scope"]["enum"] == [
        "timer_write_op04", "event_write_op0a", "event_setpoint_write_op0c"
    ]
    assert "does not prove native support or authorize execution" in qualification["description"]
    assert "literal `true`" in text
    assert "bundled synthetic qualification" in text
    slot = edit_schema["oneOf"][0]["properties"]["values"]["items"]["anyOf"][1]
    assert [item["maximum"] for item in slot["prefixItems"]] == [143, 144]
    assert "strictly less than its stop code" in edit_schema["description"]
    assert "strictly lower than stop" in text
    assert "unchanged edit" in text
    assert "before transport opens" in text
