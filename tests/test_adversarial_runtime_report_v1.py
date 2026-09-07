import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs/platform/schemas/adversarial-runtime-report-v1.schema.json"
VALIDATOR = ROOT / "scripts/validate_adversarial_runtime_report_v1.py"
POSITIVE = ROOT / "docs/platform/fixtures/adversarial-runtime/v1/positive/offline-all-pass.json"
EVALUATED_FAIL = ROOT / "docs/platform/fixtures/adversarial-runtime/v1/positive/evaluated-fail.json"
EXECUTION_ERROR = ROOT / "docs/platform/fixtures/adversarial-runtime/v1/positive/execution-error.json"
INFRASTRUCTURE_BLOCK = ROOT / "docs/platform/fixtures/adversarial-runtime/v1/positive/infrastructure-block.json"
NEGATIVE = ROOT / "docs/platform/fixtures/adversarial-runtime/v1/negative-cases.json"
FIXTURE_MANIFEST = ROOT / "docs/platform/fixtures/adversarial-runtime/v1/fixture-input-manifest.json"
sys.path.insert(0, str(ROOT / "scripts"))
import validate_adversarial_runtime_report_v1 as validator  # noqa: E402
from validate_adversarial_runtime_report_v1 import ValidationError, load_report, validate_path, validate_semantics  # noqa: E402


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def mutate(value, operations):
    result = copy.deepcopy(value)
    for operation in operations:
        parent = result
        parts = operation["path"].split("/")[1:]
        for part in parts[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        key = parts[-1]
        if operation["op"] == "remove":
            parent.pop(int(key)) if isinstance(parent, list) else parent.pop(key)
        elif operation["op"] in {"add", "replace"}:
            if isinstance(parent, list) and key == "-":
                parent.append(operation["value"])
            elif isinstance(parent, list):
                parent[int(key)] = operation["value"]
            else:
                parent[key] = operation["value"]
        else:
            raise AssertionError(operation)
    return result


def validate_candidate(tmp_path, value):
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(value, separators=(",", ":")), encoding="utf-8")
    with pytest.raises(ValidationError) as caught:
        validate_path(path)
    return str(caught.value)


def test_schema_is_a_closed_draft_2020_12_v1_contract():
    schema = load(SCHEMA)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == load(POSITIVE)["$schema"]

    def walk(value):
        if isinstance(value, dict):
            if value.get("type") == "object":
                assert value.get("additionalProperties") is False
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(schema)


def test_canonical_offline_report_passes_schema_and_recomputed_semantics():
    result = subprocess.run([sys.executable, str(VALIDATOR), str(POSITIVE)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "adversarial_runtime_report_v1_ok"
    report = load(POSITIVE)
    digest = hashlib.sha256(FIXTURE_MANIFEST.read_bytes()).hexdigest()
    assert report["provenance"]["fixture_set_sha256"] == digest
    assert report["provenance"]["subject"]["artifact_sha256"] == digest
    assert "hypothetical public contract vectors" in load(FIXTURE_MANIFEST)["purpose"]


def test_valid_result_variants_and_mixed_evaluated_failure_recompute_summary():
    for path in (EVALUATED_FAIL, EXECUTION_ERROR, INFRASTRUCTURE_BLOCK):
        validate_path(path)
    mixed = load(EVALUATED_FAIL)
    assert mixed["summary"] == {"total": 4, "passed": 3, "failed": 1, "xfailed": 0, "blocked": 0, "unknown": 0, "verdict": "fail"}
    assert mixed["scenarios"][0]["result_kind"] == "evaluated"
    assert mixed["scenarios"][0]["outcome"] == "fail"


def test_negative_fixture_weakening_mutations_fail_closed(tmp_path):
    base, cases = load(POSITIVE), load(NEGATIVE)["cases"]
    assert len(cases) >= 18
    for case in cases:
        message = validate_candidate(tmp_path, mutate(base, case["mutations"]))
        assert case["expect"] in message, (case["id"], message)


def test_invalid_utf8_duplicate_keys_noninteger_and_oversize_are_rejected(tmp_path):
    invalid_utf8 = tmp_path / "invalid-utf8.json"
    invalid_utf8.write_bytes(b'{"x":"\xff"}')
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"a": 1, "a": 2}', encoding="utf-8")
    decimal = tmp_path / "decimal.json"
    decimal.write_text('{"a": 1.0}', encoding="utf-8")
    oversize = tmp_path / "oversize.json"
    oversize.write_bytes(b" " * (1024 * 1024 + 1))
    for path, token in ((invalid_utf8, "UTF-8"), (duplicate, "duplicate"), (decimal, "non-integer"), (oversize, "exceeds")):
        with pytest.raises(ValidationError, match=token):
            load_report(path)


def test_report_rejects_dirty_provenance_for_a_passing_gate(tmp_path):
    candidate = load(POSITIVE)
    candidate["provenance"]["subject"]["source_tree"] = "dirty"
    assert "dirty_provenance_pass" in validate_candidate(tmp_path, candidate)


def test_serial_scenario_run_binding_and_conservative_timing_uncertainty(tmp_path):
    candidate = load(POSITIVE)
    candidate["scenarios"][1]["timing"]["scenario_started_at"] = "2026-09-07T12:02:59.000Z"
    assert "scenario_sequence" in validate_candidate(tmp_path, candidate)
    candidate = load(POSITIVE)
    candidate["execution"]["completed_at"] = "2026-09-07T12:11:59.000Z"
    assert "scenario_run_containment" in validate_candidate(tmp_path, candidate)

    candidate = load(POSITIVE)
    scenario = candidate["scenarios"][2]
    scenario["action"]["events"][-1].update(offset_ms=150000, at="2026-09-07T12:08:30.000Z", error_bound_ms=1000)
    scenario["timing"].update(recovery_ms=90000, error_bound_ms=1000)
    scenario["evaluation"]["recovery"].update(observed_ms=90000, error_bound_ms=0, passed=True)
    assert "timing_error_bound" in validate_candidate(tmp_path, candidate)

    candidate = load(POSITIVE)
    candidate["provenance"]["fixture_set_sha256"] = "0" * 64
    assert "fixture_subject_binding" in validate_candidate(tmp_path, candidate)


def test_action_sequences_are_bounded_prefixes_and_block_is_pre_action_only(tmp_path):
    candidate = load(POSITIVE)
    candidate["scenarios"][0]["action"]["events"][-1].update(offset_ms=180001, at="2026-09-07T12:03:00.001Z")
    assert "action_bounds" in validate_candidate(tmp_path, candidate)

    candidate = load(POSITIVE)
    scenario = candidate["scenarios"][0]
    scenario.update(result_kind="execution-error", outcome="fail", evaluation=None, errors=[{"phase": "observer", "code": "observer_failed"}])
    scenario["metrics"] = {"baseline": None, "end": None, "delta": None}
    scenario["action"]["events"] = [copy.deepcopy(load(POSITIVE)["scenarios"][1]["action"]["events"][0])]
    candidate["summary"] = {"total": 4, "passed": 3, "failed": 1, "xfailed": 0, "blocked": 0, "unknown": 0, "verdict": "fail"}
    assert "action_prefix" in validate_candidate(tmp_path, candidate)

    candidate = load(INFRASTRUCTURE_BLOCK)
    candidate["scenarios"][0]["errors"] = [{"phase": "observer", "code": "observer_failed"}]
    assert "schema" in validate_candidate(tmp_path, candidate)


def test_action_start_timing_and_result_timing_binding_are_fail_closed(tmp_path):
    candidate = load(POSITIVE)
    candidate["scenarios"][0]["action"]["events"][0].update(offset_ms=179000, at="2026-09-07T12:02:59.000Z")
    assert "action_start" in validate_candidate(tmp_path, candidate)
    candidate = load(EXECUTION_ERROR)
    candidate["scenarios"][0]["timing"]["scenario_ended_at"] = "2026-09-07T12:02:59.998Z"
    assert "timing_binding" in validate_candidate(tmp_path, candidate)


def test_infrastructure_reason_is_scenario_specific(tmp_path):
    candidate = load(INFRASTRUCTURE_BLOCK)
    candidate["scenarios"][0]["infrastructure_reason"] = "adapter_control_unavailable"
    assert "infrastructure_block_precedence" in validate_candidate(tmp_path, candidate)


def test_evaluated_snapshots_cover_full_window_with_declared_uncertainty(tmp_path):
    candidate = load(POSITIVE)
    candidate["scenarios"][0]["metrics"]["baseline"].update(offset_ms=1, captured_at="2026-09-07T12:00:00.001Z")
    assert "snapshot_window" in validate_candidate(tmp_path, candidate)


def test_recovery_uncertainty_sums_anchor_and_observation_bounds(tmp_path):
    candidate = load(POSITIVE)
    scenario = candidate["scenarios"][0]
    scenario["action"]["events"][1]["error_bound_ms"] = 1000
    scenario["action"]["events"][3].update(offset_ms=90000, at="2026-09-07T12:01:30.000Z", error_bound_ms=1000)
    scenario["timing"]["error_bound_ms"] = 1000
    scenario["timing"]["recovery_ms"] = 89000
    scenario["evaluation"]["duration"]["error_bound_ms"] = 1000
    scenario["evaluation"]["recovery"].update(observed_ms=89000, error_bound_ms=2000, passed=True)
    assert "recovery_decision" in validate_candidate(tmp_path, candidate)


def test_partition_uncertainty_sums_its_two_endpoint_bounds(tmp_path):
    candidate = load(POSITIVE)
    scenario = candidate["scenarios"][2]
    scenario["action"]["events"][1]["error_bound_ms"] = 1000
    scenario["action"]["events"][2]["error_bound_ms"] = 1000
    scenario["timing"]["error_bound_ms"] = 1000
    scenario["evaluation"]["duration"]["error_bound_ms"] = 1000
    assert "action_decision" in validate_candidate(tmp_path, candidate)


def test_cli_rejects_safe_integer_offset_without_traceback(tmp_path):
    candidate = load(POSITIVE)
    candidate["scenarios"][0]["action"]["events"][0]["offset_ms"] = 9007199254740991
    path = tmp_path / "huge-offset.json"
    path.write_text(json.dumps(candidate), encoding="utf-8")
    result = subprocess.run([sys.executable, str(VALIDATOR), str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 1
    assert "adversarial_runtime_report_v1_invalid" in result.stderr
    assert "Traceback" not in result.stderr


def test_startup_phase_is_the_documented_closed_fsm_enum(tmp_path):
    candidate = load(POSITIVE)
    candidate["scenarios"][3]["metrics"]["baseline"]["semantic_startup_current_phase"] = "VENDOR_MAGIC"
    assert "schema" in validate_candidate(tmp_path, candidate)


def test_startup_phase_is_bound_to_each_canonical_scenario(tmp_path):
    candidate = load(POSITIVE)
    candidate["scenarios"][3]["metrics"]["baseline"]["semantic_startup_current_phase"] = "LIVE_READY"
    assert "startup_phase" in validate_candidate(tmp_path, candidate)
    candidate = load(POSITIVE)
    candidate["scenarios"][0]["metrics"]["end"]["semantic_startup_current_phase"] = "DEGRADED"
    assert "startup_phase" in validate_candidate(tmp_path, candidate)


def test_cli_normalizes_integer_digit_limit_value_error(tmp_path):
    path = tmp_path / "too-many-digits.json"
    path.write_text('{"value":' + ('9' * 5000) + '}', encoding="utf-8")
    result = subprocess.run([sys.executable, str(VALIDATOR), str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 1
    assert "adversarial_runtime_report_v1_invalid" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_normalizes_deep_nesting_recursion_error(tmp_path):
    path = tmp_path / "deep-nesting.json"
    path.write_text("[" * 2000 + "0" + "]" * 2000, encoding="utf-8")
    result = subprocess.run([sys.executable, str(VALIDATOR), str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 1
    assert "adversarial_runtime_report_v1_invalid" in result.stderr
    assert "Traceback" not in result.stderr


def test_report_read_failures_are_normalized_and_bounded(tmp_path, monkeypatch):
    missing = tmp_path / "missing-report.json"
    result = subprocess.run([sys.executable, str(VALIDATOR), str(missing)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 1
    assert "report read failed" in result.stderr
    assert str(missing) not in result.stderr and "Traceback" not in result.stderr

    directory = tmp_path / "report-directory"
    directory.mkdir()
    result = subprocess.run([sys.executable, str(VALIDATOR), str(directory)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 1
    assert "report read failed" in result.stderr and "Traceback" not in result.stderr

    oversized = tmp_path / "oversized-report.json"
    oversized.write_bytes(b" " * (1024 * 1024 + 1))
    result = subprocess.run([sys.executable, str(VALIDATOR), str(oversized)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 1
    assert "report exceeds" in result.stderr and "Traceback" not in result.stderr

    monkeypatch.setattr(validator.os, "open", lambda *_args, **_kwargs: (_ for _ in ()).throw(PermissionError()))
    with pytest.raises(ValidationError, match="report read failed"):
        validator.read_report_bytes(POSITIVE)


def test_fifo_report_path_rejects_promptly_without_traceback(tmp_path):
    fifo = tmp_path / "report.fifo"
    os.mkfifo(fifo)
    result = subprocess.run([sys.executable, str(VALIDATOR), str(fifo)], cwd=ROOT, text=True, capture_output=True, check=False, timeout=1)
    assert result.returncode == 1
    assert "report read failed" in result.stderr
    assert "Traceback" not in result.stderr


def test_missing_schema_validator_is_normalized(monkeypatch):
    monkeypatch.setattr(validator.subprocess, "run", lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError()))
    with pytest.raises(ValidationError, match="schema validator unavailable"):
        validator.validate_schema_bytes(b"{}")


def test_definition_maximum_recovery_is_canonical_even_if_evaluation_is_forged(tmp_path):
    candidate = load(POSITIVE)
    scenario = candidate["scenarios"][0]
    scenario["definition"]["maximum_recovery_ms"] = 120000
    scenario["evaluation"]["recovery"]["maximum_ms"] = 120000
    assert "scenario_catalog" in validate_candidate(tmp_path, candidate)


def test_counter_epoch_is_opaque_uuidv4_not_serial_shaped(tmp_path):
    candidate = load(POSITIVE)
    for scenario in candidate["scenarios"]:
        scenario["metrics"]["baseline"]["counter_epoch"] = "VR921-SERIAL-1234567890"
        scenario["metrics"]["end"]["counter_epoch"] = "VR921-SERIAL-1234567890"
    assert "schema" in validate_candidate(tmp_path, candidate)


def test_schema_and_semantics_use_one_read_snapshot_despite_path_replacement(tmp_path, monkeypatch):
    path = tmp_path / "report.json"
    path.write_text(POSITIVE.read_text(encoding="utf-8"), encoding="utf-8")
    forged = load(POSITIVE)
    forged["summary"]["passed"] = 3
    real_run = validator.subprocess.run

    def replacing_run(*args, **kwargs):
        path.write_text(json.dumps(forged), encoding="utf-8")
        return real_run(*args, **kwargs)

    monkeypatch.setattr(validator.subprocess, "run", replacing_run)
    validator.validate_path(path)
    assert "summary_accounting" in validator.validate_semantics(load(path))
    candidate = load(POSITIVE)
    candidate["scenarios"][0]["metrics"]["end"].update(offset_ms=179999, captured_at="2026-09-07T12:02:59.999Z")
    assert "snapshot_window" in validate_candidate(tmp_path, candidate)


def test_canonical_identity_cannot_be_bypassed_with_permissive_schema(tmp_path):
    candidate = load(POSITIVE)
    candidate["$schema"] = "https://example.invalid/permissive.json"
    candidate["schema_version"] = 2
    assert "contract_identity" in validate_semantics(candidate)
    report = tmp_path / "version-2.json"
    permissive = tmp_path / "permissive.json"
    report.write_text(json.dumps(candidate), encoding="utf-8")
    permissive.write_text('{"type":"object"}', encoding="utf-8")
    result = subprocess.run([sys.executable, str(VALIDATOR), "--schema", str(permissive), str(report)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode != 0


def test_result_variant_shapes_and_producer_subject_pairings_fail_closed(tmp_path):
    candidate = load(INFRASTRUCTURE_BLOCK)
    candidate["scenarios"][0]["action"]["events"] = load(POSITIVE)["scenarios"][0]["action"]["events"][:1]
    assert "schema" in validate_candidate(tmp_path, candidate)
    candidate = load(POSITIVE)
    candidate["provenance"]["producer"]["repository"] = "Project-Helianthus/helianthus-ha-integration"
    assert "semantic: producer_subject_pairing" in validate_candidate(tmp_path, candidate)
    candidate = load(POSITIVE)
    candidate["scenarios"][0]["action"]["events"][0]["source"] = "observer"
    assert "semantic: producer_subject_pairing" in validate_candidate(tmp_path, candidate)

    ha_offline = load(POSITIVE)
    producer = ha_offline["provenance"]["producer"]
    producer.update(repository="Project-Helianthus/helianthus-ha-integration", component="ha-adversarial-harness", build_kind="ha-harness", input_gateway_report_sha256="3" * 64)
    path = tmp_path / "ha-offline.json"
    path.write_text(json.dumps(ha_offline), encoding="utf-8")
    validate_path(path)
    for scenario in ha_offline["scenarios"]:
        for event in scenario["action"]["events"]:
            event["source"] = "observer"
    assert "semantic: producer_subject_pairing" in validate_candidate(tmp_path, ha_offline)

    ha_live = copy.deepcopy(ha_offline)
    ha_live["execution"]["mode"] = "operator-live"
    ha_live["provenance"]["subject"]["artifact_kind"] = "gateway-binary"
    ha_live["provenance"]["subject"]["artifact_sha256"] = "4" * 64
    ha_live["provenance"]["fixture_set_sha256"] = None
    ha_live["provenance"]["producer"]["input_gateway_report_sha256"] = None
    for scenario in ha_live["scenarios"]:
        for event in scenario["action"]["events"]:
            event["source"] = "observer"
    path = tmp_path / "ha-live.json"
    path.write_text(json.dumps(ha_live), encoding="utf-8")
    validate_path(path)
    ha_live["scenarios"][0]["action"]["events"][0]["source"] = "fixture"
    assert "semantic: producer_subject_pairing" in validate_candidate(tmp_path, ha_live)
