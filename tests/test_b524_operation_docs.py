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
    text = (ROOT / "architecture" / "b524-namespace-invariants.md").read_text(encoding="utf-8")
    assert "`--scan-plan` JSON file" in text
    assert "`schema_version: 1`" in text
    assert "Only read selectors and wire-bounded values are accepted" in text
    assert "100000 scalar requests fail before queuing" in text
    assert "`--request-budget`" in text
    assert "partial artifact marked" in text
    assert "`incomplete`, never an absence verdict" in text


def test_scan_plan_synthetic_boundary_vectors_are_consistent() -> None:
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

    assert "`OP=0x06, GG=0x0B` = **Functional\nModules (VR70) FM3**" in register_map
    assert "is not a documented\nB524 selector route" in register_map
    assert "does not establish additional qualified scan targets or bounds;\nexploratory probing remains separately qualified" in register_map
    assert "`OP=0x06, GG=0x0C` is presented as **Functional Modules (VR71) FM5**" in register_map
    assert "outside this characterized discovery profile" in profile
    assert "exploratory\nprobing remains separately qualified. Do not apply the `GG=0x0C` policy" in profile
    assert "`OP=0x06, GG=0x0B`" in architecture
    assert "`OP=0x06, GG=0x0C`" in architecture
    routing = B524.read_text(encoding="utf-8").split("### 3.2 Opcode routing", 1)[1].split(
        "**Unqualified presentation candidate:**", 1
    )[0]
    assert "GG=0x0B" not in routing


def test_op06_presentation_catalog_is_complete_and_cannot_expand_discovery() -> None:
    text = B524.read_text(encoding="utf-8")
    register_map = REGISTER_MAP.read_text(encoding="utf-8")
    profile = (ROOT / "protocols" / "vaillant" / "b524-profile-discovery-and-descriptions.md").read_text(
        encoding="utf-8"
    )

    assert "operator-provided **hypothesis catalog**" in text
    for semantic_name in (
        "boiler",
        "heat_pump",
        "air_recovery_recovair",
        "unused",
        "heat_pump_accessory_vwz_ai",
        "solar_pump_module_auroflow",
        "water_pump_module_aguaflow",
        "solar_module_aurostep",
        "remote_control_regulator",
        "remote_control_thermostat",
        "functional_modules_vr70",
        "functional_modules_vr71",
        "relay_module_vr41",
        "clock_module",
        "base_station",
    ):
        assert f"`{semantic_name}`" in text
    assert "does not establish universal absence or reservation" in text
    assert "[issue #544](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/544)" in text
    assert "| 05 | Wärmepumpe Zubehör Appliance Interface (VWZ-AI) |" in text
    assert "| 06 | Pumpen Module - Solar (VPM-S) auroFLOW |" in text
    assert "| 07 | Pumpen Module - Wasser (VPM-W) aguaFLOW |" in text
    assert "| 08 | Modul Solar (VMS) auroSTEP |" in text
    assert "| 0x06 | 0x01 | Boiler |" in register_map
    assert "| 0x06 | 0x02 | Heat Pump |" in register_map
    assert "| 0x06 | 0x08 | Modul Solar (VMS) auroSTEP |" in register_map
    assert "| 0x06 | 0x09 | Remote Control Regulators (VRC7xx, VRT38x) |" in register_map
    assert "| 0x06 | 0x0A | Remote Control Thermostats (VR9x) |" in register_map
    assert "| 0x06 | 0x0E | Clock Module |" in register_map
    assert "| 0x06 | 0x0F | Base Station |" in register_map
    assert "| 0C | Functional Modules (VR71) FM5 | `functional_modules_vr71` | Hypothesis" in text
    assert "### GG=0x0C — Functional Modules (VR71) FM5" in register_map
    assert "GG0B\nmust not receive GG0C's scan policy or `device_connected` predicate" in text
    assert "`unused` for GG04 does not justify suppressing a probe" in profile


def test_register_catalog_is_strictly_partitioned_by_opcode() -> None:
    text = REGISTER_MAP.read_text(encoding="utf-8")
    op02 = text.split("## OP=0x02 — Local Parameter Registers", 1)[1].split(
        "## OP=0x06 — Controller-Mediated Device Parameters", 1
    )[0]
    op06 = text.split("## OP=0x06 — Controller-Mediated Device Parameters", 1)[1].split(
        "## Constraint Catalog", 1
    )[0]

    assert op02.index("### GG=0x09 — Local Configuration") < op02.index(
        "### GG=0x09 — Ventilation / recoVair Candidates"
    ) < op02.index("### GG=0x0A — Local Parameters")
    assert "(opcode 0x06)" not in op02
    assert "### GG=0x08 — Modul Solar (VMS) auroSTEP" in op06
    assert "### GG=0x09 — Remote Control Regulators (VRC7xx, VRT38x)" in op06
    assert "### GG=0x0A — Remote Control Thermostats (VR9x)" in op06


def test_op02_naming_catalog_matches_exact_operation_group_register_rows() -> None:
    import csv
    import re

    source = ROOT / "protocols" / "vaillant" / "fixtures" / "b524-op02-register-names.csv"
    names = list(csv.DictReader(source.open(encoding="utf-8")))
    assert len({(row["opcode"], row["group"], row["register"]) for row in names}) == len(names)
    text = REGISTER_MAP.read_text(encoding="utf-8").split(
        "## OP=0x02 — Local Parameter Registers", 1
    )[1].split("## OP=0x06 — Controller-Mediated Device Parameters", 1)[0]
    observed: dict[tuple[int, int], str] = {}
    group = None
    for line in text.splitlines():
        header = re.match(r"### GG=0x([0-9A-F]{2})", line)
        if header:
            group = int(header[1], 16)
        row = re.match(r"\| 0x([0-9A-F]{4}) \| ([a-z][a-z0-9_]*) \|", line)
        if row and group is not None:
            observed[group, int(row[1], 16)] = row[2]
    for row in names:
        assert row["opcode"] == "0x02"
        assert re.fullmatch(r"[a-z][a-z0-9_]*", row["name"])
        assert observed[int(row["group"], 0), int(row["register"], 0)] == row["name"]


def test_op06_common_names_are_universal_and_do_not_relabel_op02() -> None:
    import re

    names = {1: "device_connected", 2: "device_class_address", 3: "device_error_code", 4: "device_firmware_version"}
    text = REGISTER_MAP.read_text(encoding="utf-8")
    remote = text.split("## OP=0x06 — Controller-Mediated Device Parameters", 1)[1].split("## Constraint Catalog", 1)[0]
    assert "**every GG**" in remote
    assert "It does not establish register presence" in remote
    for row in re.finditer(r"^\| 0x([0-9A-F]{4}) \| ([^|]+) \|", remote, flags=re.M):
        register = int(row[1], 16)
        if register in names:
            assert row[2].strip() == names[register]
    protocol = B524.read_text(encoding="utf-8")
    for register, name in names.items():
        assert f"| 0x{register:04X} | `{name}` |" in protocol



def test_op02_gg0a_observation_does_not_establish_template_or_device_topology() -> None:
    section = REGISTER_MAP.read_text(encoding="utf-8").split(
        "### GG=0x0A — Local Parameters", 1
    )[1].split("## OP=0x06 — Controller-Mediated Device Parameters", 1)[0]
    assert "physical-device identity, role and topology remain" in section
    assert "**Unknown**" in section
    assert "Repetition does not establish a physical" in section
    assert "template/default purpose" in section
    assert "this is a template/default configuration" not in section
    assert "| Radio sensors VR92. 69 regs/instance." not in REGISTER_MAP.read_text(encoding="utf-8")



def test_protocol_overview_preserves_unknown_role_and_topology_for_op02_gg0a() -> None:
    text = B524.read_text(encoding="utf-8")
    selector_row = next(line for line in text.splitlines() if line.startswith("| `0x02` | Local controller selector family |"))
    assert "`GG=0x0A`" in selector_row
    assert "OP02/GG0A remain Unknown" in selector_row
    assert "per-slot configuration" not in selector_row


def test_op02_gg08_uses_deltat_without_relabelling_remote_family() -> None:
    text = REGISTER_MAP.read_text(encoding="utf-8")
    assert "### GG=0x08 — DeltaT" in text
    assert "| 0x02 | 0x08 | DeltaT (local) |" in text
    assert "### GG=0x08 — Modul Solar (VMS) auroSTEP" in text
    assert "Buffer/Solar Cylinder 2" not in text


def test_local_deltat_does_not_claim_singleton_topology() -> None:
    text = REGISTER_MAP.read_text(encoding="utf-8")
    local = text.split("### GG=0x08 — DeltaT", 1)[1].split("### GG=0x09", 1)[0]
    assert "II=0x00 only" not in local
    assert "profile-dependent" in local
    assert "not a qualified device count" in local
    assert "OP06/GG08 remains a separate instanced selector set" in local
    assert "| 0x02 | 0x08 | DeltaT (local) | Unknown | profile-dependent |" in text
