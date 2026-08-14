from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAIN = ROOT / "protocols/sunspec/sunspec-model-chain-v1.md"
FLAVOR_V1 = ROOT / "protocols/sunspec/fronius-observed-flavor-v1.md"
FLAVOR_V11 = ROOT / "protocols/sunspec/fronius-observed-flavor-v1-1.md"
RUNTIME = ROOT / "api/modbus-v1-addon-runtime.md"
README = ROOT / "protocols/sunspec/README.md"

FLAVOR_V1_ID = "sunspec.flavor.fronius.gen24.float.observed@1.0.0"
FLAVOR_V11_ID = "sunspec.flavor.fronius.gen24.float.observed@1.1.0"
OLD_CHAIN = "1/65, 113/60, 120/26, 121/30, 122/44, 160/88, 124/24, FFFF/0"
CONTROLS_CHAIN = (
    "1/65, 113/60, 120/26, 121/30, 122/44, 123/24, 160/88, 124/24, FFFF/0"
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def json_record_after(document: str, heading: str) -> dict[str, object]:
    section = document[document.index(heading) :]
    match = re.search(r"```json\n(.*?)\n```", section, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))


def test_model_123_is_standard_exact_read_only_core() -> None:
    contract = text(CHAIN)
    normalized = " ".join(contract.split())

    assert "Model `123`, Immediate Controls: `L24`" in contract
    assert "(123, 24, schema_revision)" in contract
    assert "standard SunSpec core" in normalized
    assert "read-only decoder" in normalized
    assert "RW metadata" in normalized
    assert "creates no write authority" in normalized
    assert "vendor custom model" in normalized


def test_old_flavor_is_immutable_and_new_flavor_is_exact() -> None:
    old = text(FLAVOR_V1)
    new = text(FLAVOR_V11)
    normalized = " ".join(new.lower().split())

    assert FLAVOR_V1_ID in old
    assert OLD_CHAIN in old
    assert CONTROLS_CHAIN not in old

    for value in (
        FLAVOR_V11_ID,
        FLAVOR_V1_ID,
        CONTROLS_CHAIN,
        "Fronius",
        "Symo GEN24 10.0",
        "1.41.11-1",
        "Model `123/L24`",
        "Immediate Controls",
        "81e18e67a1b7d1adff5273c8c43f08243a3e2a0a",
        "CHAIN_MISMATCH",
    ):
        assert value in new
    for phrase in (
        "does not reinterpret",
        "exact ordered chain",
        "standard model",
        "read-only",
        "no write authority",
        "not a product-family support claim",
    ):
        assert phrase in normalized


def test_v3_selects_one_closed_registry_flavor_and_keeps_m5_blocked() -> None:
    record = json_record_after(text(RUNTIME), "### Registry-Selected V3 Contract Record")

    assert record["contract"] == "helianthus.modbus-sunspec-live-qualification.v3"
    assert record["supersedes_for_new_runs"] == (
        "helianthus.modbus-sunspec-live-qualification.v2"
    )
    assert record["selection"] == {
        "input": "complete_terminal_verified_SunSpecChainSnapshot",
        "decoder_dispatch": "exact_registry_key",
        "capability": "sunspec.inverter.three_phase.monitoring@1.0.0",
        "supported_flavors": [FLAVOR_V1_ID, FLAVOR_V11_ID],
        "required_exact_match_count": 1,
        "current_live_target": FLAVOR_V11_ID,
        "hardcoded_model_id_rules": False,
    }
    assert record["model_123"] == {
        "decoder_key": [123, 24, "sunspec.models@7abdf898-v1"],
        "ownership": "standard_sunspec_core",
        "access": "read_only_decode",
        "writes_permitted": False,
    }
    assert record["go_authority"] == "qualification_evidence_only"
    assert record["support_claim"] is False
    assert record["writes_permitted"] is False
    assert record["m5_gate"] == "BLOCKED_UNTIL_DEPLOYED_EXACT_GO"


def test_new_flavor_is_indexed_without_replacing_v1() -> None:
    index = text(README)
    assert "fronius-observed-flavor-v1.md" in index
    assert "fronius-observed-flavor-v1-1.md" in index

