import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "protocols" / "vaillant" / "fixtures"


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


def test_artifact_keeps_raw_event_boundary() -> None:
    artifact = json.loads((FIXTURES / "b524-operation-reads-artifact-synthetic-v1.json").read_text())
    first, vr91, event, unattempted = artifact["b524_operation_reads"]
    assert artifact["schema_version"] == "2.3"
    assert first["selector_correlation"] == "request_context"
    assert vr91["decoded"]["binding_zone"] == 0
    assert "parameter_config" not in vr91["decoded"]
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
    text = (ROOT / "protocols" / "vaillant" / "b524-operation-reads.md").read_text()
    assert "defaults to an offline preview and diff" in text
    assert "Event execution stays disabled pending a qualified native Event contract" in text
    qualification = json.loads((FIXTURES / "b524-native-write-qualification-schema-v1.json").read_text())
    assert qualification["properties"]["manufacturer"]["const"] == 181
    assert "profile" in qualification["required"]
    assert qualification["properties"]["software_raw_hex"]["pattern"] == "^[0-9A-Fa-f]{4}$"
    assert qualification["properties"]["scope"]["enum"] == [
        "timer_write_op04", "event_write_op0a", "event_setpoint_write_op0c"
    ]
