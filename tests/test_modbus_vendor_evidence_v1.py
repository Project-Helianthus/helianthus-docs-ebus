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
        assert pdu["executable"] is False
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
            base_keys = {
                "source_id", "identity", "license", "redistributable", "transformation",
                "applicability", "sanitization", "code_mapping",
            }
            if packet["packet_id"] == "HUAWEI-GATEWAYS-V1":
                assert set(source) == base_keys | {"evidence_class", "provenance"}
                provenance = source["provenance"]
                assert set(provenance) == {
                    "title", "revision", "published", "capture_ref", "sha256",
                    "source_material_sha256", "acquisition",
                }
                assert provenance["title"]
                assert provenance["revision"]
                assert provenance["capture_ref"]
                assert provenance["acquisition"]
                if source["identity"].startswith("sha256:"):
                    assert provenance["sha256"] == source["identity"].removeprefix("sha256:")
            else:
                assert set(source) == base_keys
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


def test_huawei_gateways_are_three_independent_fail_closed_candidates():
    huawei = next(
        packet for packet in load_manifest()["packets"]
        if packet["packet_id"] == "HUAWEI-GATEWAYS-V1"
    )
    assert huawei["disposition"] == "THREE_INDEPENDENT_CANDIDATES"
    assert huawei["mutual_exclusion"] == {
        "required": True,
        "families": ["SmartLogger", "S-Dongle", "EMMA", "DirectInverter"],
        "multiple_positive_outcome": "INSUFFICIENT_EVIDENCE",
        "first_match_priority": False,
    }
    candidates = {candidate["gateway_kind"]: candidate for candidate in huawei["candidates"]}
    assert set(candidates) == {"SmartLogger", "S-Dongle", "EMMA"}
    assert candidates["SmartLogger"]["detector_pdus"][0]["unit_id"] == 0
    assert candidates["S-Dongle"]["detector_pdus"][0]["unit_id"] == 100
    assert all(candidate["status"] == "DOCUMENTARY_CANDIDATE" for candidate in candidates.values())
    assert all(candidate["ambiguity_outcome"] == "NO_ADMISSIBLE_PROFILE" for candidate in candidates.values())
    assert len(candidates["SmartLogger"]["firmware_gates"]) == 8
    assert len(candidates["S-Dongle"]["firmware_gates"]) == 5
    assert len(candidates["EMMA"]["firmware_gates"]) == 2
    assert candidates["EMMA"]["protocol_gate"]["admission_use"] is False
    emma_purposes = {pdu["purpose"] for pdu in candidates["EMMA"]["detector_pdus"]}
    assert emma_purposes == {"offering_name", "model", "software_version", "basic_identity"}
    assert "serial_number_30015" in candidates["EMMA"]["detection_tuple"]["forbidden_identity"]
    assert len(candidates["EMMA"]["missing_discriminators"]) == 3
    assert all(candidate["eligible"] is False for candidate in candidates.values())


def test_huawei_fc03_addresses_are_explicitly_normalized_and_sensitive_reads_absent():
    huawei = next(
        packet for packet in load_manifest()["packets"]
        if packet["packet_id"] == "HUAWEI-GATEWAYS-V1"
    )
    fc03_pdus = [
        pdu
        for candidate in huawei["candidates"]
        for pdu in candidate["detector_pdus"]
        if pdu["operation"] == "FC03"
    ]
    assert {pdu["offset"] for pdu in fc03_pdus} == {65521, 30068, 37410, 30000, 30222, 30035}
    assert not {30015, 40713, 65524}.intersection(pdu["offset"] for pdu in fc03_pdus)
    for pdu in fc03_pdus:
        normalization = pdu["address_normalization"]
        assert normalization == {
            "table": "holding_registers",
            "document_notation": "zero_based_register_address",
            "document_base": 0,
            "formula": "pdu_offset=document_address",
            "document_address": pdu["offset"],
            "pdu_offset": pdu["offset"],
        }
        assert pdu["encoding"]


def test_huawei_version_gates_and_provenance_are_structured():
    huawei = next(
        packet for packet in load_manifest()["packets"]
        if packet["packet_id"] == "HUAWEI-GATEWAYS-V1"
    )
    source_map = {source["source_id"]: source for source in huawei["sources"]}
    assert source_map["emma-r024"]["provenance"]["sha256"] == (
        "7a989d2b8d031582ce1fad5766c0168b47b5a4ba2cf96dbd65085590d3308a5e"
    )
    assert source_map["emma-r025"]["provenance"]["sha256"] == (
        "89bafd5f74ef7516daeb4d5de0d4212245080d1d6d1b03d7482854d0fe5244ce"
    )
    assert all(
        source_map[source_id]["provenance"]["acquisition"]
        == "third_party_mirror_of_huawei_authored_pdf"
        for source_id in ("emma-r024", "emma-r025")
    )
    for candidate in huawei["candidates"]:
        assert candidate["firmware_gates"]
        for gate in candidate["firmware_gates"]:
            assert set(gate) == {
                "gate_id", "model_families", "release_branch", "comparator", "minimum", "status",
            }
            assert gate["gate_id"]
            assert gate["model_families"]
            assert gate["release_branch"]
            assert gate["comparator"]
            assert gate["status"]
        assert candidate["evidence_sources"]["authoritative"]


def test_huawei_child_inventory_and_transport_prerequisites_are_bounded():
    huawei = next(
        packet for packet in load_manifest()["packets"]
        if packet["packet_id"] == "HUAWEI-GATEWAYS-V1"
    )
    prerequisites = {item["requirement_id"]: item for item in huawei["transport_prerequisites"]}
    assert set(prerequisites) == {
        "modbus.unit-id-zero.v1", "modbus.mei-vendor-cursor.v1", "modbus.mei-object-wrap.v1"
    }
    assert all(item["owner"] == "helianthus-modbus" for item in prerequisites.values())
    assert all(item["status"] == "BLOCKED" for item in prerequisites.values())

    candidates = {candidate["gateway_kind"]: candidate for candidate in huawei["candidates"]}
    for family in ("SmartLogger", "EMMA"):
        inventory = candidates[family]["child_enumeration"]
        assert inventory["unit_id"] == 0
        assert inventory["read_device_id_code"] == 3
        assert inventory["start_object_id"] == 0x87
        assert inventory["wrap_after_object_id"] == 0xFF
        assert inventory["wrap_to_object_id"] == 0
        assert inventory["max_children"] == 247
        assert "cursor_loop" in inventory["reject"]
        assert "count_mismatch" in inventory["reject"]

    sdongle = candidates["S-Dongle"]["child_enumeration"]
    assert sdongle["required_live_fixture"] == "unit100_plus_object135_through_modbus_tcp"
    assert "unit_target_ambiguous" in sdongle["reject"]


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
    assert "EMMA is first-class" in huawei
    assert "unit_id=0" in huawei
    assert "0xFF -> 0x00" in huawei
    assert "FC05, FC06, FC0F, FC10" in sunspec
    assert "registration-key, serial-number, credential, and device-search writes" in huawei
