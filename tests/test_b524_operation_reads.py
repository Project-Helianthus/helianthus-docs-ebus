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
