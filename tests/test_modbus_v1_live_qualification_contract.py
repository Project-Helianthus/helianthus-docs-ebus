import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "api" / "modbus-v1-addon-runtime.md"
RECORD_HEADING = "### Normative Contract Record\n\n"
V2_RECORD_HEADING = "### Registry-Selected V2 Contract Record\n\n"


def normative_record() -> dict:
    text = CONTRACT.read_text(encoding="utf-8")
    section = text.split(RECORD_HEADING, 1)[1].split(
        "### Activation And Acquisition\n", 1
    )[0]
    if section.count("```json\n") != 1:
        raise AssertionError("normative contract record must contain one JSON block")
    payload = section.split("```json\n", 1)[1].split("\n```", 1)[0]
    return json.loads(payload)


def registry_selected_v2_record() -> dict:
    text = CONTRACT.read_text(encoding="utf-8")
    section = text.split(V2_RECORD_HEADING, 1)[1].split(
        "### V2 Activation, Recovery, And Evidence Boundary\n", 1
    )[0]
    if section.count("```json\n") != 1:
        raise AssertionError("V2 contract record must contain one JSON block")
    payload = section.split("```json\n", 1)[1].split("\n```", 1)[0]
    return json.loads(payload)


class ModbusV1LiveQualificationContractTest(unittest.TestCase):
    def test_page_is_a_legacy_harness_not_a_fronius_or_live_support_claim(self) -> None:
        text = CONTRACT.read_text(encoding="utf-8")

        self.assertIn("legacy qualification harness", text.lower())
        self.assertIn("does not claim Fronius support", text)
        self.assertIn("future registry-selected outcome", text.lower())
        self.assertIn("suspended gateway #808", text)

    def test_record_freezes_opt_in_read_only_bounds_and_recovery(self) -> None:
        record = normative_record()
        self.assertEqual(
            record["contract"], "helianthus.modbus-sunspec-live-qualification.v1"
        )
        self.assertEqual(record["phase"], "FMV3-M4-04")
        self.assertEqual(
            record["activation"],
            {
                "disabled_by_default": True,
                "worker_start_condition": "complete_explicit_modbus_opt_in",
            },
        )
        self.assertEqual(
            record["acquisition"],
            {
                "transport": "modbus_tcp",
                "unit_id": 1,
                "function_code": 3,
                "writes_permitted": False,
                "profile_id": "sunspec.phase1",
                "profile_version": "1.0.0",
                "chain_qualification": "dynamic_bounded_existing_profile_contracts",
                "qualifications_per_attempt": 1,
                "per_read_timeout_seconds": 2,
                "attempt_timeout_seconds": 30,
            },
        )
        self.assertEqual(
            record["recovery"],
            {
                "max_qualification_attempts": 2,
                "retry_trigger": ["transport_error", "endpoint_reconnect_required"],
                "endpoint_owned_backoff_reconnect_max": 1,
                "final_attempt_requires_new": [
                    "poll_generation_id",
                    "deadline_identity",
                ],
                "periodic_retries": False,
            },
        )

    def test_record_freezes_decisions_redaction_shutdown_and_m4_05_owner(self) -> None:
        record = normative_record()
        self.assertEqual(
            record["decision_map"],
            {
                "supported": {
                    "decision": "GO",
                    "profile_observation": "RETAINED",
                },
                "unsupported_or_deferred_model": {
                    "includes_model_ids": [113],
                    "decision": "NO_GO",
                    "raw_mcp": "USABLE",
                    "profile_observation": "UNAVAILABLE",
                },
                "incoherent_capture": {"decision": "STOP"},
                "any_error": {"decision": "STOP"},
            },
        )
        self.assertEqual(
            record["result_redaction"],
            {
                "logs_and_results": "categorical_only",
                "forbidden": [
                    "endpoint",
                    "raw_error",
                    "serial_payload",
                    "model_payload",
                    "firmware_payload",
                    "model_chain_payload",
                    "sample_payload",
                ],
            },
        )
        self.assertEqual(
            record["shutdown"]["required_order"],
            ["worker_cancel", "worker_join", "adapter_close"],
        )
        self.assertEqual(
            record["rollback"],
            {
                "trigger": "explicit_operator_controlled_post_qualification_procedure",
                "disable_modbus_endpoint": True,
                "restore": "operator_selected_prior_gateway_addon_pair",
                "automatic_on_stop_or_no_go": False,
                "separate_from_startup_fallback": True,
                "startup_fallback_parity": "not_guaranteed",
            },
        )
        self.assertEqual(
            record["live_evidence"],
            {
                "owner_phase": "FMV3-M4-05",
                "prerequisite_phase": "FMV3-M4-04",
                "required_tuple": [
                    "endpoint_ref",
                    "model",
                    "firmware",
                    "model_chain",
                    "outcome",
                ],
                "published_here": False,
            },
        )

    def test_v2_uses_registry_capability_and_flavor_without_model_id_rules(self) -> None:
        record = registry_selected_v2_record()
        self.assertEqual(
            record["contract"], "helianthus.modbus-sunspec-live-qualification.v2"
        )
        self.assertEqual(record["supersedes_for_new_runs"], record["legacy_contract"])
        self.assertEqual(
            record["registry_dependency"],
            {
                "module": "github.com/Project-Helianthus/helianthus-modbusreg",
                "version": "v0.1.0",
                "merge": "0567cac9db3749086c46f05b2c4c0a24c2371763",
            },
        )
        self.assertEqual(
            record["selection"],
            {
                "input": "complete_terminal_verified_SunSpecChainSnapshot",
                "decoder_dispatch": "exact_registry_key",
                "capability": "sunspec.inverter.three_phase.monitoring@1.0.0",
                "required_flavor": "sunspec.flavor.fronius.gen24.float.observed@1.0.0",
                "hardcoded_model_id_rules": False,
            },
        )
        self.assertNotIn("includes_model_ids", json.dumps(record))

    def test_v2_has_closed_registry_reason_to_decision_mapping(self) -> None:
        record = registry_selected_v2_record()
        self.assertEqual(
            record["decision_map"],
            {
                "INVALID_CHAIN": "STOP",
                "AMBIGUOUS_SOURCE": "NO_GO",
                "SOURCE_ABSENT": "NO_GO",
                "SOURCE_UNSUPPORTED": "NO_GO",
                "INVALID_REQUIRED_FACT": "NO_GO",
                "ADMITTED+MATCHED": "GO",
                "ADMITTED+COMMON_IDENTITY_MISMATCH": "NO_GO",
                "ADMITTED+FIRMWARE_MISMATCH": "NO_GO",
                "ADMITTED+CHAIN_MISMATCH": "NO_GO",
                "runtime_or_transport_error": "STOP",
            },
        )
        self.assertEqual(record["go_authority"], "qualification_evidence_only")
        self.assertFalse(record["support_claim"])
        self.assertFalse(record["live_result_published_here"])
        self.assertFalse(record["writes_permitted"])


if __name__ == "__main__":
    unittest.main()
