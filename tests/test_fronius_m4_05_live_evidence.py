from __future__ import annotations

import json
import ipaddress
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "docs/platform/live/fronius-m4-04-0.6.46"
README = LIVE / "README.md"
EVIDENCE = LIVE / "evidence.json"
LIVE_0647 = ROOT / "docs/platform/live/fronius-m4-04-0.6.47"
README_0647 = LIVE_0647 / "README.md"
EVIDENCE_0647 = LIVE_0647 / "evidence.json"
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

IPV4_ADDRESS = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6_CANDIDATE = re.compile(
    r"(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}"
    r"(?![0-9A-Fa-f:])"
)
MAC_ADDRESS = re.compile(
    r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"
    r"|\b(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}\b"
)
ENDPOINT_URI = re.compile(r"\b(?:https?|tcp|udp)://[^\s/]+", re.IGNORECASE)
HOST_PORT = re.compile(r"\b[a-z][a-z0-9.-]*:\d{1,5}\b", re.IGNORECASE)
HOSTNAME = re.compile(
    r"[a-z0-9](?:[a-z0-9-]{0,62}\.)+[a-z]{2,63}", re.IGNORECASE
)
ABSOLUTE_UNIX_PATH = re.compile(
    r"(?<![A-Za-z0-9._-])/(?![/.])(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+"
)
ABSOLUTE_WINDOWS_PATH = re.compile(r"\b[A-Za-z]:\\(?:[^\\\r\n]+\\)*[^\\\r\n]+")
SAFE_DOTTED_IDENTIFIERS = {
    "helianthus.fronius-sunspec-m4-04-evidence.v1",
    "sunspec.inverter.three_phase.monitoring@1.0.0",
    "sunspec.flavor.fronius.gen24.float.observed@1.0.0",
    "sunspec.flavor.fronius.gen24.float.observed@1.1.0",
}
LOCAL_FILE_SUFFIXES = (".json", ".md", ".py", ".sh", ".yaml", ".yml")


def load_evidence() -> dict[str, object]:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def load_evidence_0647() -> dict[str, object]:
    return json.loads(EVIDENCE_0647.read_text(encoding="utf-8"))


def contains_network_identifier(value: str) -> bool:
    if IPV4_ADDRESS.search(value) or MAC_ADDRESS.search(value):
        return True
    for candidate in IPV6_CANDIDATE.findall(value):
        try:
            address = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        return True
    return False


def contains_endpoint_value(value: str) -> bool:
    if contains_network_identifier(value) or ENDPOINT_URI.search(value) or HOST_PORT.search(value):
        return True
    searchable = value
    for identifier in SAFE_DOTTED_IDENTIFIERS:
        searchable = searchable.replace(identifier, "")
    return any(
        not match.group(0).lower().endswith(LOCAL_FILE_SUFFIXES)
        for match in HOSTNAME.finditer(searchable)
    )


def contains_private_path(value: str) -> bool:
    return bool(
        ABSOLUTE_UNIX_PATH.search(value) or ABSOLUTE_WINDOWS_PATH.search(value)
    )


def evidence_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            nested
            for child in value.values()
            for nested in evidence_keys(child)
        }
    if isinstance(value, list):
        return {nested for child in value for nested in evidence_keys(child)}
    return set()


def evidence_strings(value: object) -> list[str]:
    if isinstance(value, dict):
        return [nested for child in value.values() for nested in evidence_strings(child)]
    if isinstance(value, list):
        return [nested for child in value for nested in evidence_strings(child)]
    return [value] if isinstance(value, str) else []


def sensitive_key(key: str) -> bool:
    normalized = key.lower()
    if normalized in {"endpoint_ref", "endpoint_present"}:
        return False
    words = set(re.findall(r"[a-z0-9]+", normalized.replace("_", "-")))
    forbidden_stems = (
        "container",
        "credential",
        "hostname",
        "password",
        "process",
        "secret",
        "serial",
        "token",
    )
    if any(word.startswith(stem) for word in words for stem in forbidden_stems):
        return True
    if words & {"address", "host", "ip", "key", "mac", "pid", "port"}:
        return True
    if "endpoint" in words:
        return True
    identifier_words = {"id", "identifier", "identity", "name", "path", "ref", "slug"}
    if "backup" in words and words & identifier_words:
        return True
    if "raw" in words and words & {
        "bytes",
        "data",
        "frame",
        "payload",
        "register",
        "registers",
        "word",
        "words",
    }:
        return True
    if {"source", "view"} <= words or {"source", "views"} <= words:
        return True
    if words & {"deadline", "poll", "request", "response", "sample"} and words & identifier_words:
        return True
    return False


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
    assert re.fullmatch(r"sha256:[0-9a-f]{16}", evidence["target"]["endpoint_ref"])
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


def test_0647_rerun_keeps_registry_go_separate_from_terminal_stop() -> None:
    evidence = load_evidence_0647()

    assert evidence["contract"] == "helianthus.fronius-sunspec-m4-04-evidence.v1"
    assert evidence["phase"] == "FMV3-M4-04"
    assert evidence["publication_phase"] == "FMV3-M4-05"
    assert evidence["outcome"] == "STOP_ENVIRONMENTAL"
    assert evidence["runtime"] == {
        "addon_release": "0.6.47",
        "addon_merge": "176b00ccdd356514532a893e0eef83f173a68c3a",
        "gateway_merge": "225f3d96fee3422bc565870f946af19fac42d471",
        "modbusreg_version": "v0.2.1",
        "modbusreg_merge": "16a7dfbf8016750613d086fb98d10364953ea915",
        "image_digest": (
            "sha256:9d79fed17e4ea682adae25ae00f667dc7277bf88f4e6635dd8561c74ac8828b6"
        ),
    }

    acquisition = evidence["acquisition"]
    assert acquisition["unit_id"] == 1
    assert acquisition["function_code"] == 3
    assert acquisition["writes_permitted"] is False
    assert acquisition["qualification_attempts_per_gateway_start"] == 1
    assert acquisition["gateway_starts_with_internal_go"] == "MULTIPLE_OBSERVED"
    assert acquisition["modbus_reconnect_attempted"] is False

    qualification = evidence["qualification"]
    assert qualification["internal_decision"] == "GO"
    assert qualification["category"] == "registry_match"
    assert qualification["supported_flavor_ids"] == [
        "sunspec.flavor.fronius.gen24.float.observed@1.0.0",
        "sunspec.flavor.fronius.gen24.float.observed@1.1.0",
    ]
    assert qualification["selected_flavor_publication"] == "WITHHELD_NOT_LOGGED"
    assert qualification["reference_flavor_id"] == (
        "sunspec.flavor.fronius.gen24.float.observed@1.1.0"
    )
    assert qualification["reference_tuple_basis"] == (
        "PRIOR_EXACT_TARGET_EVIDENCE_0_6_46"
    )
    assert qualification["support_claim"] is False
    chain = [
        (entry["model_id"], entry["model_length"])
        for entry in qualification["reference_chain"]
    ]
    assert chain == EXPECTED_CHAIN
    assert evidence["acceptance"]["raw_mcp_parity"] == "NOT_OBSERVED"
    assert evidence["acceptance"]["retained_profile_observation"] == (
        "NOT_RETRIEVED"
    )
    assert evidence["acceptance"]["final_decision"] == "STOP_ENVIRONMENTAL"


def test_0647_readiness_redaction_and_rollback_are_exact() -> None:
    evidence = load_evidence_0647()
    window = evidence["observation_window"]

    assert window["bounded_window_seconds"] == 130
    assert window["readiness"] == {
        "current_runtime": "NOT_READY",
        "current_attempts_exhausted": True,
        "false_running_published": False,
        "fallback_active_published": False,
    }
    assert window["listeners"] == {
        "gateway_http": "NOT_LISTENING",
        "adapter_proxy": "NOT_LISTENING",
    }
    assert window["dependency_observation"]["physical_device_state"] == (
        "NOT_CONCLUDED"
    )

    acceptance = evidence["acceptance"]
    assert acceptance["readiness_regression"] == "PASS"
    assert acceptance["redaction_regression"] == "PASS"
    assert acceptance["no_gateway_regression"] == "NOT_PROVEN"
    rollback = evidence["rollback"]
    assert rollback["modbus_tcp_enabled"] is False
    assert rollback["endpoint_present"] is False
    assert rollback["health_state"] == "DISABLED"
    assert rollback["health_reason"] == "EXPLICIT_DISABLE"

    follow_ups = {item["id"]: item for item in evidence["follow_ups"]}
    assert set(follow_ups) == {
        "HEALTH_READINESS_MISMATCH",
        "ENDPOINT_REDACTION_MISCLASSIFICATION",
    }
    assert all(
        item["status"] == "LIVE_REGRESSION_PASS"
        and item["attributed_to_sunspec"] is False
        for item in follow_ups.values()
    )
    assert evidence["next_gate"]["m5"] == "BLOCKED_UNTIL_DEPLOYED_EXACT_GO"

    readme = README_0647.read_text(encoding="utf-8")
    assert "exact target reference retained" in readme
    assert "public log did not expose which supported flavor" in readme
    assert "did not independently compare\nraw MCP" in readme
    assert "does not establish that the physical adapter was\ndown" in readme
    assert "M5 remains `BLOCKED_UNTIL_DEPLOYED_EXACT_GO`" in readme
    assert "fronius-m4-04-0.6.47" in PLATFORM_INDEX.read_text(encoding="utf-8")


def test_public_evidence_contains_no_private_operational_identifiers() -> None:
    public_files = (
        README,
        EVIDENCE,
        README_0647,
        EVIDENCE_0647,
        PLATFORM_INDEX,
    )
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in public_files)
    assert not contains_endpoint_value(corpus)
    assert not contains_private_path(corpus)
    for evidence in (load_evidence(), load_evidence_0647()):
        assert not any(sensitive_key(key) for key in evidence_keys(evidence))
        assert not any(
            contains_endpoint_value(value) for value in evidence_strings(evidence)
        )
        assert not any(
            contains_private_path(value) for value in evidence_strings(evidence)
        )


def test_redaction_guards_cover_generic_sensitive_variants() -> None:
    for key in (
        "backup_identifier",
        "gateway_container_ref",
        "operator_credential",
        "upstream_endpoint_address",
        "device_mac",
        "owner_password",
        "worker_process_identifier",
        "captured_raw_register_payload",
        "runtime_secret",
        "device_serial",
        "captured_source_view",
        "session_token",
        "api_key",
        "private_key",
        "backup_key",
        "sample_identity",
        "request_id",
        "pid",
    ):
        assert sensitive_key(key), key
    assert not sensitive_key("endpoint_ref")
    assert not sensitive_key("endpoint_present")
    assert not sensitive_key("backup_created")
    assert not sensitive_key("raw_mcp_parity")

    assert contains_endpoint_value("fd00::1")
    assert contains_endpoint_value("fe80::1")
    assert contains_endpoint_value("02-00-00-00-00-01")
    assert contains_endpoint_value("0200.0000.0001")
    assert contains_endpoint_value("tcp://example.invalid:502")
    assert contains_endpoint_value("synthetic docs mention tcp://gateway.example.invalid:502")
    assert contains_endpoint_value("example.invalid")
    assert contains_endpoint_value("synthetic failure at example.invalid")
    assert contains_endpoint_value("host.example.com:502")
    assert not contains_endpoint_value("sunspec.inverter.three_phase.monitoring@1.0.0")
    assert not contains_endpoint_value("[evidence](./evidence.json)")

    assert contains_private_path("/private/var/lib/addons/data")
    assert contains_private_path("captured at /mnt/data/runtime/evidence.json")
    assert contains_private_path(r"C:\Users\operator\evidence.json")
    assert not contains_private_path("DISABLED / EXPLICIT_DISABLE")
    assert not contains_private_path("[evidence](./evidence.json)")
