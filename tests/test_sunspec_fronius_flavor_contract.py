from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAIN = ROOT / "protocols/sunspec/sunspec-model-chain-v1.md"
FLAVOR = ROOT / "protocols/sunspec/fronius-observed-flavor-v1.md"
SUNSPEC_README = ROOT / "protocols/sunspec/README.md"
MODBUS_README = ROOT / "protocols/modbus/README.md"

CAPABILITY_ID = "sunspec.inverter.three_phase.monitoring@1.0.0"
FLAVOR_ID = "sunspec.flavor.fronius.gen24.float.observed@1.0.0"
EXPECTED_FACTS = {
    "inverter.ac.current.total|A",
    "inverter.ac.current.phase_a|A",
    "inverter.ac.current.phase_b|A",
    "inverter.ac.current.phase_c|A",
    "inverter.ac.voltage.phase_a|V",
    "inverter.ac.voltage.phase_b|V",
    "inverter.ac.voltage.phase_c|V",
    "inverter.ac.power.active|W",
    "inverter.ac.frequency|Hz",
    "inverter.ac.energy_lifetime|Wh",
    "inverter.temperature.cabinet|C",
    "inverter.operating_state|none",
    "inverter.events.1|none",
    "inverter.events.2|none",
}


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_three_phase_monitoring_fact_set_and_source_selection_are_exact() -> None:
    contract = text(CHAIN)
    capability = contract[
        contract.index("## Capability Profile") : contract.index("## Vendor Flavor")
    ]

    assert CAPABILITY_ID in capability
    rows = re.findall(r"\| `([^`]+)` \| `([^`]+)` \|", capability)
    assert {f"{field}|{unit}" for field, unit in rows} == EXPECTED_FACTS
    assert "exactly one qualifying source occurrence" in capability
    assert re.search(r"(?:either )?`103/L50`\s+or `113/L60`", capability)
    assert "duplicate source occurrence" in capability
    assert "both encodings" in capability
    assert "ambiguous" in capability
    assert "unknown required enum symbol" in capability
    assert "unknown required bitfield bits" in capability
    assert "sunspec.phase1@1.0.0" in capability
    assert "must not widen" in capability.lower()


def test_observed_fronius_flavor_is_exact_evidence_bounded_and_read_only() -> None:
    flavor = text(FLAVOR)
    normalized = " ".join(flavor.lower().split())

    for value in (
        FLAVOR_ID,
        CAPABILITY_ID,
        "Fronius",
        "Symo GEN24 10.0",
        "1.41.11-1",
        "1/65, 113/60, 120/26, 121/30, 122/44, 160/88, 124/24, FFFF/0",
        "Project-Helianthus/helianthus-ebusgateway#807",
        "FC03",
        "unit ID `1`",
        "PDU offset `40000`",
    ):
        assert value in flavor

    for required in (
        "exact string match",
        "exact ordered chain match",
        "capability must already be admitted",
        "experimental",
        "no write authority",
        "not a product-family support claim",
        "no semantic override",
        "no documented quirk",
        "serial",
        "endpoint",
    ):
        assert required in normalized


def test_flavor_mismatch_outcomes_are_fail_closed_and_indexed() -> None:
    flavor = text(FLAVOR)
    chain = text(CHAIN)
    for reason in (
        "CAPABILITY_NOT_ADMITTED",
        "COMMON_IDENTITY_MISMATCH",
        "FIRMWARE_MISMATCH",
        "CHAIN_MISMATCH",
        "AMBIGUOUS_SOURCE",
    ):
        assert reason in flavor

    assert "fronius-observed-flavor-v1.md" in text(SUNSPEC_README)
    assert "fronius-observed-flavor-v1.md" in text(MODBUS_README)
    assert "fronius-observed-flavor-v1.md" in chain
    assert "not an active\nFronius flavor" not in chain
