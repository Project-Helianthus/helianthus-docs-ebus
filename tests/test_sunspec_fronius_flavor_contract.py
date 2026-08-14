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
    assert len(rows) == 14
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


def test_capability_input_reasons_and_normalization_are_closed() -> None:
    contract = text(CHAIN)
    capability = contract[
        contract.index("## Capability Profile") : contract.index("## Vendor Flavor")
    ]
    normalized = " ".join(capability.split())

    for reason in (
        "INVALID_CHAIN",
        "AMBIGUOUS_SOURCE",
        "SOURCE_ABSENT",
        "SOURCE_UNSUPPORTED",
        "INVALID_REQUIRED_FACT",
        "ADMITTED",
    ):
        assert reason in capability

    assert "complete `SunSpecChainSnapshot`" in capability
    assert "exactly one consuming `FFFF/0` terminal" in normalized
    assert "before typed decoding" in normalized
    assert "original cloned typed `SunSpecValue`" in normalized
    grammar = r"0|-?[1-9][0-9]*(?:\.[0-9]*[1-9])?|-?0\.[0-9]*[1-9]"
    assert grammar in capability
    for example in (
        "`(12,-1)` and `(120,-2)` both produce `1.2`",
        "`(-5,0)` produces `-5`",
        "any zero coefficient produces `0`",
        "`1.25` produces `1.25`",
        "positive or negative zero produces `0`",
    ):
        assert example in normalized
    assert "Exponent notation" in normalized
    assert "leading zeroes on a nonzero integer part" in normalized
    assert "redundant trailing fractional zeroes are forbidden" in normalized
    assert "ascending bit order" in normalized
    assert "canonical unit string `none`" in normalized
    assert "zero known-bit mask" in normalized
    assert "only a zero value" in normalized


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
        "non-actionable provenance only",
        "must not use them to construct a request",
        "those decisions remain gateway-owned",
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


def test_fronius_flavor_reason_precedence_and_identity_inputs_are_exact() -> None:
    flavor = text(FLAVOR)
    normalized = " ".join(flavor.split())

    ordered = [
        "a capability `AMBIGUOUS_SOURCE` maps first",
        "every other non-admitted capability maps to",
        "Common manufacturer/model mismatch maps to",
        "version mismatch maps to",
        "ordered-chain mismatch maps to",
        "otherwise the result is",
    ]
    positions = [normalized.index(value) for value in ordered]
    assert positions == sorted(positions)
    assert "exactly Common `Mn`, `Md`, and `Vr`" in normalized
    assert "without trimming, case folding, prefixing" in normalized
    assert "Common `SN`, `Opt`, and `DA`" in normalized
    assert "are not flavor matching inputs" in normalized
    assert "cannot be supplied separately to this evaluator" in normalized


def test_r3_flavor_explicitly_supersedes_only_historical_empty_vendor_logic() -> None:
    evidence = text(ROOT / "docs/platform/fronius-sunspec-evidence-v1.md")
    boundaries = text(ROOT / "docs/platform/modbus-multivendor-boundaries.md")
    normalized = " ".join(evidence.split())

    assert "At M3-03, the terminal conclusion was **`STANDARD_ONLY`**." in normalized
    assert "exact historical M3-03 completion record" in normalized
    assert "not a current inventory of later R3 code" in normalized
    assert "supersede only that historical empty-vendor-logic boundary" in normalized
    assert "Project-Helianthus/helianthus-ebusgateway#807" in normalized
    assert "general detector hypothesis remains forbidden from production use" in normalized
    assert "is not implemented by the R3 flavor evaluator" in normalized
    assert "cannot activate or publish a device" in normalized
    assert "historical terminal M3-03" in boundaries
    assert "only after that capability is admitted from the same verified snapshot" in " ".join(
        boundaries.split()
    )
