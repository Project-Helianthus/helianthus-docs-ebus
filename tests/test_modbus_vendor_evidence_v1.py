import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/platform/manifests/modbus-vendor-evidence-v1.json"


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_closed_packet_inventory_and_no_support_claim():
    manifest = load_manifest()
    assert set(manifest) == {
        "contract_id", "milestone", "support_claim", "runtime_allowlist", "packets"
    }
    assert manifest["contract_id"] == "helianthus.modbus-vendor-evidence/v1"
    assert manifest["milestone"] == "FMV3-M7-01"
    assert manifest["support_claim"] is False
    packets = {packet["packet_id"]: packet for packet in manifest["packets"]}
    assert set(packets) == {
        "SUNSPEC-EXPANSION-V1", "GROWATT-CANDIDATE-V1", "HUAWEI-GATEWAYS-V1"
    }


def test_every_detector_pdu_is_read_only_and_allowlisted():
    manifest = load_manifest()
    allowlist = {entry["operation"] for entry in manifest["runtime_allowlist"]}
    assert allowlist == {"FC03", "FC04", "FC2B_MEI_0E"}
    forbidden_codes = {5, 6, 15, 16, 22, 23}
    assert not forbidden_codes.intersection(
        entry["function_code"] for entry in manifest["runtime_allowlist"]
    )

    pdus = []
    for packet in manifest["packets"]:
        pdus.extend(packet.get("detector_pdus", []))
        for candidate in packet.get("candidates", []):
            pdus.extend(candidate.get("detector_pdus", []))
    assert pdus
    for pdu in pdus:
        assert pdu["operation"] in allowlist
        assert pdu["executable"] is False or pdu["purpose"] == "sunspec_signature"
        if pdu["operation"] in {"FC03", "FC04"}:
            assert 0 <= pdu["offset"] <= 65535
            assert 1 <= pdu["quantity"] <= 125
        else:
            assert pdu["read_device_id_code"] == 1
            assert pdu["object_id"] == 0


def test_sources_record_license_transformation_and_redistribution_state():
    for packet in load_manifest()["packets"]:
        assert packet["sources"]
        for source in packet["sources"]:
            assert set(source) == {
                "source_id", "identity", "license", "redistributable", "transformation",
                "applicability", "sanitization", "code_mapping",
            }
            assert source["identity"]
            assert source["license"]
            assert isinstance(source["redistributable"], bool)
            assert source["transformation"]
            assert source["applicability"]
            assert source["sanitization"]
            assert source["code_mapping"]


def test_growatt_is_proprietary_and_not_admitted_as_sunspec():
    growatt = next(
        packet for packet in load_manifest()["packets"]
        if packet["packet_id"] == "GROWATT-CANDIDATE-V1"
    )
    assert growatt["protocol_family"] == "growatt_proprietary_modbus"
    assert growatt["sunspec_claim"] is False
    assert growatt["disposition"] == "HYPOTHESIS"
    assert growatt["address_normalization"] == "documentary_zero_based_hypothesis"
    assert growatt["admission"] == {
        "eligible": False,
        "next_node": "FMV3-M7-03",
        "required_outcome": "PROFILE_ADMITTED_OR_NO_ADMISSIBLE_PROFILE",
    }


def test_huawei_gateways_are_distinct_and_emma_fails_closed():
    huawei = next(
        packet for packet in load_manifest()["packets"]
        if packet["packet_id"] == "HUAWEI-GATEWAYS-V1"
    )
    candidates = {candidate["gateway_kind"]: candidate for candidate in huawei["candidates"]}
    assert set(candidates) == {"SmartLogger", "S-Dongle", "EMMA"}
    assert candidates["SmartLogger"]["detector_pdus"][0]["unit_id"] == 0
    assert candidates["S-Dongle"]["detector_pdus"][0]["unit_id"] == 100
    assert candidates["SmartLogger"]["status"] == "HYPOTHESIS"
    assert candidates["SmartLogger"]["firmware_gate"].startswith("document-revision")
    assert candidates["S-Dongle"]["status"] == "DOCUMENTARY_CANDIDATE"
    assert len(candidates["S-Dongle"]["firmware_gate"]) == 2
    assert candidates["EMMA"]["status"] == "UNKNOWN"
    assert candidates["EMMA"]["firmware_gate"] is None
    assert candidates["EMMA"]["eligible"] is False
    assert candidates["EMMA"]["detector_pdus"] == []
    assert len(candidates["EMMA"]["missing_discriminators"]) == 3
    assert all(candidate["eligible"] is False for candidate in candidates.values())


def test_public_pages_link_packets_and_preserve_safety_boundary():
    platform = " ".join(
        (ROOT / "docs/platform/modbus-vendor-evidence-v1.md").read_text().split()
    )
    growatt = " ".join(
        (ROOT / "protocols/modbus/growatt-candidate-evidence-v1.md").read_text().split()
    )
    huawei = " ".join(
        (ROOT / "protocols/modbus/huawei-gateway-candidate-evidence-v1.md").read_text().split()
    )
    sunspec = " ".join(
        (ROOT / "protocols/sunspec/additional-model-evidence-v1.md").read_text().split()
    )
    assert "does not publish support" in platform
    assert "must not be labeled or decoded as SunSpec" in growatt
    assert "EMMA has no executable detector PDU" in huawei
    assert "FC05, FC06, FC0F, FC10" in sunspec
    assert "registration-key, serial-number, and" in huawei
