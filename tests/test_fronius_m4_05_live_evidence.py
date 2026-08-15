from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "docs/platform/live/fronius-m4-04-0.6.46"
README = LIVE / "README.md"
EVIDENCE = LIVE / "evidence.json"
PLATFORM_INDEX = ROOT / "docs/platform/README.md"

EXPECTED_CHAIN = [
    (1, 65),
    (113, 60),
    (120, 26),
    (121, 30),
    (122, 44),
    (123, 24),
    (160, 88),
    (124, 24),
    (65535, 0),
]


def load_evidence() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_live_evidence_keeps_internal_go_separate_from_terminal_stop() -> None:
    evidence = load_evidence()

    assert evidence["contract"] == "helianthus.fronius-sunspec-m4-04-evidence.v1"
    assert evidence["evidence_class"] == "LIVE_RUNTIME_EVIDENCE"
    assert evidence["export_tier"] == "PUBLIC_REDACTED"
    assert evidence["phase"] == "FMV3-M4-04"
    assert evidence["publication_phase"] == "FMV3-M4-05"
    assert evidence["outcome"] == "STOP_ENVIRONMENTAL"

    qualification = evidence["qualification"]
    assert qualification["internal_decision"] == "GO"
    assert qualification["category"] == "registry_match"
    assert qualification["capability_id"] == (
        "sunspec.inverter.three_phase.monitoring@1.0.0"
    )
    assert qualification["capability_reason"] == "ADMITTED"
    assert qualification["flavor_id"] == (
        "sunspec.flavor.fronius.gen24.float.observed@1.1.0"
    )
    assert qualification["flavor_reason"] == "MATCHED"
    assert qualification["support_claim"] is False
    assert evidence["acceptance"]["final_decision"] == "STOP_ENVIRONMENTAL"
    assert evidence["next_gate"]["m5"] == "BLOCKED_UNTIL_DEPLOYED_EXACT_GO"


def test_runtime_identity_chain_and_read_only_boundary_are_exact() -> None:
    evidence = load_evidence()
    assert evidence["runtime"] == {
        "addon_release": "0.6.46",
        "addon_merge": "eff3f910c5a96c1fc2a9d10a7eb9f618162340c7",
        "gateway_merge": "53fe86d1beb656c8453a6213127ddddef83c887b",
        "modbusreg_version": "v0.2.1",
        "modbusreg_merge": "16a7dfbf8016750613d086fb98d10364953ea915",
        "image_digest": (
            "sha256:9169f41b1d15ccf989d182ad125239df682602d87f74c1665b42802b96cabfca"
        ),
    }
    assert evidence["target"] == {
        "endpoint_ref": "sha256:cc2d63775c6f0074",
        "manufacturer": "Fronius",
        "model": "Symo GEN24 10.0",
        "firmware": "1.41.11-1",
    }
    acquisition = evidence["acquisition"]
    assert acquisition["unit_id"] == 1
    assert acquisition["function_code"] == 3
    assert acquisition["writes_permitted"] is False
    assert acquisition["qualification_attempts_per_gateway_start"] == 1
    assert acquisition["gateway_start_attempts"] == 3
    assert acquisition["modbus_reconnect_attempted"] is False
    assert acquisition["recovered"] is False
    chain = [
        (entry["model_id"], entry["model_length"])
        for entry in evidence["qualification"]["chain"]
    ]
    assert chain == EXPECTED_CHAIN
    assert evidence["qualification"]["unknown_blocks_publication"] == (
        "WITHHELD_UNPROVEN"
    )
    assert evidence["qualification"]["unknown_field_publication"] == (
        "WITHHELD_UNPROVEN"
    )


def test_environmental_stop_and_rollback_are_closed() -> None:
    evidence = load_evidence()
    window = evidence["observation_window"]
    assert window["modbus_health"] == {
        "state": "RUNNING",
        "reason": "STARTUP_WINDOW_PASSED",
        "attempt": 3,
        "max_attempts": 3,
    }
    assert window["listeners"] == {
        "eebus": "REACHABLE",
        "gateway_http": "NOT_LISTENING",
        "adapter_proxy": "NOT_LISTENING",
    }
    assert window["dependency_observation"] == {
        "role": "adapter_direct_dependency",
        "route_present": True,
        "neighbor_state": "UNRESOLVED",
        "tcp_result": "TIMEOUT",
        "physical_device_state": "NOT_CONCLUDED",
    }
    assert evidence["acceptance"] == {
        "qualified_opt_in_detection": "PASS_INTERNAL",
        "bounded_polling": "PASS_INTERNAL",
        "raw_mcp_parity": "NOT_OBSERVED",
        "retained_profile_observation": "NOT_RETRIEVED",
        "disconnect_reconnect_generation_integrity": "NOT_EXERCISED",
        "no_writes": "PASS",
        "no_gateway_regression": "NOT_PROVEN",
        "final_decision": "STOP_ENVIRONMENTAL",
    }
    assert evidence["rollback"]["modbus_tcp_enabled"] is False
    assert evidence["rollback"]["endpoint_present"] is False
    assert evidence["rollback"]["health_state"] == "DISABLED"
    assert evidence["rollback"]["health_reason"] == "EXPLICIT_DISABLE"


def test_follow_ups_are_separate_from_sunspec() -> None:
    evidence = load_evidence()
    follow_ups = {item["id"]: item for item in evidence["follow_ups"]}
    assert set(follow_ups) == {
        "HEALTH_READINESS_MISMATCH",
        "ENDPOINT_REDACTION_MISCLASSIFICATION",
    }
    assert all(item["attributed_to_sunspec"] is False for item in follow_ups.values())

    readme = README.read_text(encoding="utf-8")
    assert "The internal `GO` is only the registry-owned qualification result" in readme
    assert "It is not\nthe final M4-04 decision" in readme
    assert "does not establish that the\nphysical adapter was down" in readme
    assert "M5 remains `BLOCKED_UNTIL_DEPLOYED_EXACT_GO`" in readme
    assert "[REDACTED_MODBUS_ENDPOINT]" in readme
    assert "fronius-m4-04-0.6.46" in PLATFORM_INDEX.read_text(encoding="utf-8")


def test_public_evidence_contains_no_private_operational_identifiers() -> None:
    corpus = README.read_text(encoding="utf-8") + EVIDENCE.read_text(encoding="utf-8")
    forbidden_literals = (
        "b930e982",
        "10dcdb3f590d",
        "392fd3ec2440",
        "117206",
    )
    assert not any(value in corpus for value in forbidden_literals)
    assert not re.search(
        r"\b(?:10|127|169\.254|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b",
        corpus,
    )
    assert not re.search(r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b", corpus)
    for forbidden_word in ("password", "credential", "serial_number", "raw_words"):
        assert f'"{forbidden_word}"' not in corpus
