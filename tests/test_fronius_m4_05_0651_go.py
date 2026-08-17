from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "docs/platform/live/fronius-m4-04-0.6.51"
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


def all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for child in value.values() for key in all_keys(child)}
    if isinstance(value, list):
        return {key for child in value for key in all_keys(child)}
    return set()


def test_0651_exact_runtime_and_terminal_go() -> None:
    evidence = load_evidence()
    assert evidence["outcome"] == "GO"
    assert evidence["runtime"] == {
        "addon_release": "0.6.51",
        "addon_merge": "8be32bc7f49f3000eba6074f12ca782e10425093",
        "gateway_merge": "6f4aaa7a08eeffb655e5da0f6f6c2053e399a45b",
        "modbusreg_version": "v0.2.1",
        "modbusreg_merge": "16a7dfbf8016750613d086fb98d10364953ea915",
        "image_digest": (
            "sha256:876098e26a6b5f698d0f992f61a0784af8f677f4e3b96a424869fda9609eec6e"
        ),
    }
    assert evidence["acceptance"]["final_decision"] == "GO"
    assert evidence["next_gate"] == {
        "m5": "READY_FOR_FMV3-M5-02",
        "semantic_implementation_requires": "FMV3-M5-02_MERGED",
    }


def test_0651_chain_unknown_retention_and_read_only_boundary() -> None:
    evidence = load_evidence()
    qualification = evidence["qualification"]
    assert qualification["capability_id"] == (
        "sunspec.inverter.three_phase.monitoring@1.0.0"
    )
    assert qualification["capability_reason"] == "ADMITTED"
    assert qualification["flavor_id"] == (
        "sunspec.flavor.fronius.gen24.float.observed@1.1.0"
    )
    assert qualification["flavor_reason"] == "MATCHED"
    assert [
        (item["model_id"], item["model_length"])
        for item in qualification["chain"]
    ] == EXPECTED_CHAIN
    assert qualification["admitted_occurrences"] == 8
    assert qualification["structural_unknown_blocks"] == []
    assert qualification["field_unknown_retention"] == (
        "PRESERVED_PRIVATE_NOT_PROMOTED"
    )
    assert evidence["acquisition"]["function_code"] == 3
    assert evidence["acquisition"]["writes_permitted"] is False


def test_0651_recovery_is_endpoint_free_and_generation_advancing() -> None:
    recovery = load_evidence()["recovery"]
    assert recovery["fault_scope"] == "TARGET_MODBUS_TCP_ONLY"
    assert recovery["blocked_request"] == {
        "code": "UNAVAILABLE",
        "message": "modbus provider unavailable",
        "retriable": True,
        "endpoint_free": True,
    }
    assert recovery["initial_connection_generation"] == 1
    assert recovery["recovered_connection_generation"] == 2
    assert recovery["initial_transport_generation"] == 1
    assert recovery["recovered_transport_generation"] == 2
    assert recovery["same_signature_after_recovery"] is True
    assert recovery["retained_observation_byte_identical"] is True
    assert recovery["whole_gateway_restart"] is False
    assert recovery["fallback_started"] is False


def test_0651_acceptance_contract_is_complete() -> None:
    evidence = load_evidence()
    assert evidence["acquisition"] == {
        "transport": "modbus_tcp",
        "unit_id": 1,
        "function_code": 3,
        "writes_permitted": False,
        "bounded_raw_read_max_words": 125,
        "raw_reads_per_window": 4,
        "raw_read_window_milliseconds": 1000,
    }
    assert evidence["acceptance"] == {
        "qualified_opt_in_detection": "PASS",
        "bounded_polling": "PASS",
        "raw_mcp_parity": "PASS",
        "retained_profile_observation": "PASS",
        "disconnect_reconnect_generation_integrity": "PASS",
        "coherent_provenance": "PASS",
        "no_writes": "PASS",
        "gateway_http_ready": "PASS",
        "adapter_proxy_ready": "PASS",
        "no_gateway_regression": "PASS",
        "final_decision": "GO",
    }


def test_0651_publication_is_redacted_and_indexed() -> None:
    evidence = load_evidence()
    corpus = README.read_text(encoding="utf-8") + EVIDENCE.read_text(encoding="utf-8")
    assert not re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", corpus)
    assert "tcp://" not in corpus.lower()
    assert "private-evidence" not in corpus.lower()
    forbidden_keys = {
        "address",
        "backup_id",
        "backup_slug",
        "container_id",
        "endpoint",
        "password",
        "pid",
        "process_id",
        "raw_words",
        "serial",
        "source_views",
    }
    assert not (all_keys(evidence) & forbidden_keys)
    assert "fronius-m4-04-0.6.51" in PLATFORM_INDEX.read_text(encoding="utf-8")
