from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUNSPEC_README = ROOT / "protocols/sunspec/README.md"
CHAIN_CONTRACT = ROOT / "protocols/sunspec/sunspec-model-chain-v1.md"
MODBUS_README = ROOT / "protocols/modbus/README.md"
EVIDENCE = ROOT / "docs/platform/fronius-sunspec-evidence-v1.md"
MANIFEST = ROOT / "docs/platform/manifests/fronius-sunspec-phase1-v1.json"
BOUNDARIES = ROOT / "docs/platform/modbus-multivendor-boundaries.md"
QUALIFICATION = ROOT / "api/modbus-v1-addon-runtime.md"

CAPABILITY_ID = "sunspec.inverter.three_phase.monitoring@1.0.0"
MODELS_PIN = "7abdf8982d5364f8ae916deee18aac86c11be36d"
FRONIUS_PDF_SHA256 = "aa1e69432472ae2f25075c01a651201f747ae0f9e85c8894dfa1f36883d06890"
FRONIUS_PACKAGE_SHA256 = "dc4c5d49362ee0c9721f21886f17fa18497e54c4d92bb5cc2c50472deb266b55"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_sunspec_protocol_pages_define_the_model_chain_contract() -> None:
    readme = text(SUNSPEC_README)
    contract = text(CHAIN_CONTRACT)

    assert "CC0-1.0" in readme
    assert "implementation-neutral" in readme
    assert "independent summary" in contract.lower()
    assert "must not copy" in contract.lower()
    assert MODELS_PIN in contract
    assert "Apache-2.0" in contract
    assert "SunSpec Device Information Model Specification v1.2" in contract
    assert "42,0410,2649" in contract
    assert "033-24022026" in contract
    assert FRONIUS_PDF_SHA256 in contract
    assert "1.2.7-2" in contract
    assert FRONIUS_PACKAGE_SHA256 in contract

    for term in ("Model", "Model Chain", "Capability Profile", "Vendor Flavor"):
        assert f"## {term}" in contract
    assert CAPABILITY_ID in contract
    assert "sunspec.phase1@1.0.0" in contract
    assert "legacy" in contract.lower()
    assert "must not widen" in contract.lower()


def test_contract_freezes_catalog_identity_retention_and_fail_closed_rules() -> None:
    contract = text(CHAIN_CONTRACT)

    for required in (
        "Common",
        "L66",
        "L65",
        "101",
        "102",
        "103",
        "111",
        "112",
        "113",
        "120",
        "121",
        "122",
        "124",
        "160",
        "8 + 20 * N",
        "(model_id, model_length, schema_revision)",
        "ordinal",
        "source span",
        "full acquisition provenance",
        "raw words",
        "known ID with an unsupported length",
        "model-ID-only",
        "sentinel",
        "NaN",
        "scale factor",
        "enum",
        "bitfield",
        "string",
        "accumulator",
        "no write authority",
        "invalid encoding",
        "no capability",
    ):
        assert required in contract

    assert "L65" in contract and "compatibility" in contract.lower()
    assert "current standard" in contract.lower()
    assert "N mismatch" in contract


def test_existing_fronius_material_is_legacy_only_and_points_to_registry_selection() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    evidence = text(EVIDENCE)
    boundaries = text(BOUNDARIES)
    qualification = text(QUALIFICATION)
    modbus_readme = text(MODBUS_README)

    assert manifest["m3_03_completion"]["disposition"] == "STANDARD_ONLY"
    assert "PENDING_M3_03" not in evidence
    assert "PENDING_M3_03" not in boundaries
    assert "legacy qualification harness" in evidence.lower()
    assert "future registry-selected outcome" in evidence.lower()
    assert "not a Fronius support claim" in evidence
    assert "no live result" in evidence.lower()
    assert "sunspec-model-chain-v1.md" in boundaries
    assert CAPABILITY_ID in boundaries
    assert "no write authority" in boundaries
    assert "sunspec-model-chain-v1.md" in modbus_readme
    assert "legacy qualification harness" in qualification.lower()
    assert "does not claim Fronius support" in qualification
    assert "future registry-selected outcome" in qualification.lower()
