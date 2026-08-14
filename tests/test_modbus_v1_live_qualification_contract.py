import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "api" / "modbus-v1-addon-runtime.md"
RECORD_HEADING = "### Normative Contract Record\n\n"


def normative_record() -> dict:
    text = CONTRACT.read_text(encoding="utf-8")
    section = text.split(RECORD_HEADING, 1)[1].split(
        "### Activation And Acquisition\n", 1
    )[0]
    if section.count("```json\n") != 1:
        raise AssertionError("normative contract record must contain one JSON block")
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


if __name__ == "__main__":
    unittest.main()
