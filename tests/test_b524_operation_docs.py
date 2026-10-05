"""Regression checks for the corrected public B524 operation contract."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
B524 = ROOT / "protocols" / "vaillant" / "ebus-vaillant-B524.md"
REGISTER_MAP = ROOT / "protocols" / "vaillant" / "ebus-vaillant-B524-register-map.md"
SEMANTIC_MAPPING = ROOT / "architecture" / "b524-semantic-mapping.md"


def test_register_map_uses_op02_read_selectors_not_op01_descriptions() -> None:
    text = REGISTER_MAP.read_text(encoding="utf-8")
    assert "`OP=0x01/0x02" not in text
    assert "`OP=0x01, GG=" not in text
    assert "OP=0x02, OT=0x00, GG=0x00, II=0x00, RR=0x0048" in text
    assert "OP=0x02, OT=0x00, GG=0x02, II=<circuit>, RR=0x001B" in text


def test_historical_short_probe_catalog_is_not_validation_authority() -> None:
    text = REGISTER_MAP.read_text(encoding="utf-8")
    assert "Authoritative for value ranges" not in text
    assert "It is unqualified historical evidence only" in text
    assert "authoritatively map a register, validate a value" in text


def test_description_budget_is_writable_candidate_scoped_without_write_authority() -> None:
    text = B524.read_text(encoding="utf-8")
    assert "at most 256" in text
    assert "observed writable candidates" in text
    assert "neither proves live writability nor" in text


def test_semantic_scan_policy_uses_complete_descriptions_and_unqualified_history() -> None:
    text = SEMANTIC_MAPPING.read_text(encoding="utf-8")
    assert "probe `0x00` directory sequentially" not in text
    assert "probe `0x01 GG RR`" not in text
    assert "Authoritative for value ranges" not in text
    assert "01 GG II RRlo RRhi" in text
    assert "07 GG II RRlo RRhi" in text
    assert "historical evidence only, not authority" in text
