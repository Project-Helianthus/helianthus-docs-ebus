"""Regression checks for the corrected public B524 operation contract."""

import json
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
    assert "unknown codec is retained raw" in text
    assert "`eligible`, `attempted`, `matched`, `unavailable`, `unqualified`, and" in text


def test_scan_presets_are_deterministic_bounded_and_operation_scoped() -> None:
    text = (ROOT / "architecture" / "b524-namespace-invariants.md").read_text(encoding="utf-8")
    assert "OP=02/GG `00..05,08,09`" in text
    assert "OP=06/GG\n`01,02,08,09,0A,0C,0E,0F`" in text
    assert "every declared II slot" in text
    assert "default `0xFF`, and OP02/GG00 at\nleast `0x1FF`" in text
    assert "failed first II=00/RR=0000 probe veto the rest of that group" in text
    assert "100000 scalar requests fail before queuing" in text


def test_scan_plan_and_budgets_remain_partial_read_only_contracts() -> None:
    text = B524.read_text(encoding="utf-8")
    assert "`--scan-plan <path.json>`" in text
    assert '"schema_version": 1' in text
    assert "only OP=02h and OP=06h read selectors" in text
    assert "100000 planned scalar requests" in text
    assert "`--request-budget`" in text
    assert "partial\nartifact marked `incomplete`" in text


def test_custom_plan_grammar_and_synthetic_boundary_vectors_are_documented() -> None:
    text = B524.read_text(encoding="utf-8")
    assert "Both endpoints are included" in text
    assert "Identical normalized duplicate rows" in text
    assert "len(unique_instances) * len(unique_registers)" in text
    assert "Booleans and floating-point" in text
    cases = json.loads((ROOT / "tests" / "fixtures" / "b524_scan_plan_v1_cases.json").read_text())
    assert cases["source"] == "synthetic_contract_vectors"
    assert cases["accepted"][0]["normalized"] == cases["accepted"][1]["normalized"]
    assert cases["accepted"][2]["expected_requests"] == 100000
    assert cases["rejected"][0]["name"] == "request_limit_exceeded"


def test_semantic_scan_policy_uses_complete_descriptions_and_unqualified_history() -> None:
    text = SEMANTIC_MAPPING.read_text(encoding="utf-8")
    assert "probe `0x00` directory sequentially" not in text
    assert "probe `0x01 GG RR`" not in text
    assert "Authoritative for value ranges" not in text
    assert "01 GG II RRlo RRhi" in text
    assert "07 GG II RRlo RRhi" in text
    assert "historical evidence only, not authority" in text


def test_device_enumeration_preserves_ii01_and_retained_inventory_contract() -> None:
    text = REGISTER_MAP.read_text(encoding="utf-8")
    section = text.split("**Device slot enumeration:**", 1)[1].split("**ebusd baseline:**", 1)[0]
    assert "II=0x00 through" not in section
    assert "If =1, read" not in section
    assert "starts at **II=0x01**" in section
    assert "Unknown results do not stop" in section
    assert "Full/research audit every" in section
    assert "must not suppress\nretained inventory evidence" in section


def test_functional_module_presentation_names_preserve_the_evidence_boundary() -> None:
    register_map = REGISTER_MAP.read_text(encoding="utf-8")
    profile = (ROOT / "protocols" / "vaillant" / "b524-profile-discovery-and-descriptions.md").read_text(encoding="utf-8")
    architecture = (ROOT / "architecture" / "functional-modules.md").read_text(encoding="utf-8")

    assert "`OP=0x06, GG=0x0B` = **Functional\nModules (VR70)**" in register_map
    assert "is not a documented\nB524 selector route" in register_map
    assert "must not be added to a scan plan" in register_map
    assert "`OP=0x06, GG=0x0C` is presented as **Functional Modules (VR71)**" in register_map
    assert "outside this characterized discovery profile" in profile
    assert "Do not add\nit to a scan plan or apply the `GG=0x0C` policy" in profile
    assert "`OP=0x06, GG=0x0B`" in architecture
    assert "`OP=0x06, GG=0x0C`" in architecture
    routing = B524.read_text(encoding="utf-8").split("### 3.2 Opcode routing", 1)[1].split(
        "**Unqualified presentation candidate:**", 1
    )[0]
    assert "GG=0x0B" not in routing
