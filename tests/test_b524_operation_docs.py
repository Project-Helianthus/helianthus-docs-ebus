"""Regression checks for the corrected public B524 operation contract."""

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
B524 = ROOT / "protocols" / "vaillant" / "ebus-vaillant-B524.md"
REGISTER_MAP = ROOT / "protocols" / "vaillant" / "ebus-vaillant-B524-register-map.md"
SEMANTIC_MAPPING = ROOT / "architecture" / "b524-semantic-mapping.md"
REGULATORS = ROOT / "protocols" / "vaillant" / "ebus-vaillant-regulators.md"


def test_current_topology_and_discovery_profile_instance_bounds_agree() -> None:
    text = REGISTER_MAP.read_text(encoding="utf-8")
    topology = text.split("## Group Topology", 1)[1].split("**GG values", 1)[0]
    # Split on the next section, not the Markdown table's separator row.
    profiles = text.split("### Discovery Profiles", 1)[1].split(
        "## Gate Conditions", 1
    )[0]

    def rows(section: str) -> dict[tuple[int, int], list[str]]:
        result = {}
        for line in section.splitlines():
            columns = [column.strip() for column in line.strip().strip("|").split("|")]
            if len(columns) > 4 and columns[0] in {"0x02", "0x06"}:
                result[(int(columns[0], 16), int(columns[1].split()[0], 16))] = columns
        return result

    top, profile = rows(topology), rows(profiles)
    for key in ((0x02, 0x03), (0x02, 0x04), (0x02, 0x0A)):
        expected_max = int(profile[key][2].split("..")[-1], 16)
        assert int(top[key][4], 16) == expected_max
    assert top[(0x02, 0x0A)][2] == "Unknown"


def test_register_map_uses_op02_read_selectors_not_op01_descriptions() -> None:
    text = REGISTER_MAP.read_text(encoding="utf-8")
    assert "`OP=0x01/0x02" not in text
    assert "`OP=0x01, GG=" not in text
    assert "OP=0x02, OT=0x00, GG=0x00, II=0x00, RR=0x0048" in text
    assert "OP=0x02, OT=0x00, GG=0x02, II=<circuit>, RR=0x001B" in text


def test_circuit_register_prose_preserves_b524_evidence_boundaries() -> None:
    text = REGISTER_MAP.read_text(encoding="utf-8")
    circuits = text.split("### GG=0x02 — Circuits", 1)[1].split(
        "### GG=0x03 — Zones", 1
    )[0]
    circuit_fsm = text.split("### `circuit_state`", 1)[1].split(
        "### `system_quick_mode`", 1
    )[0]

    assert "no presence predicate for this virtual identity" in circuits
    assert "RR0008 and RR0020 must not be\nused to infer it" in circuits
    assert "Observed UCH one-byte raw status (`00`)" in circuits
    assert "It is not a temperature value" in circuits
    for register in ("0x0007", "0x000E", "0x0014", "0x001E"):
        row = next(line for line in circuits.splitlines() if line.startswith(f"| {register} |"))
        assert "Installer-field candidate" in row
    assert "plausible live temperature evidence" not in text
    assert "Values_hcpumpmode" not in text
    assert "tracks circuit_state" not in circuit_fsm
    assert "calculated_flow_temperature" not in circuit_fsm


def test_historical_short_probe_catalog_is_not_validation_authority() -> None:
    text = REGISTER_MAP.read_text(encoding="utf-8")
    assert "Authoritative for value ranges" not in text
    assert "It is unqualified historical evidence only" in text
    assert "authoritatively map a register, validate a value" in text


def test_description_acquisition_is_planner_owned_without_write_authority() -> (
    None
):
    text = (
        ROOT / "development/ebus-vaillant-b524-description-acquisition.md"
    ).read_text(encoding="utf-8")
    assert "zero implicit" in text
    assert "`full` and `research` acquire eligible writable descriptions" in text
    assert "--description-budget" not in text
    assert "neither proves live writability nor" in text
    assert "unknown codec is retained raw" in text
    assert "Generic IIFF descriptions remain class\nmetadata" in text


def test_scan_presets_are_deterministic_bounded_and_operation_scoped() -> None:
    text = (ROOT / "architecture" / "b524-namespace-invariants.md").read_text(
        encoding="utf-8"
    )
    assert "OP=02/GG `00..05,08,09`" in text
    assert "OP=06/GG\n`01,02,03,05,06,07,08,09,0A,0B,0C,0E,0F`" in text
    assert "every declared II slot" in text
    assert "default `0xFF`. OP02/GG00 also\nuses `0xFF`" in text
    assert "`0x1FF`" not in text
    assert "default 256" not in text
    assert "defaults to 10000" not in text
    assert "failed first II=00/RR=0000 probe veto the rest of that group" in text
    assert "100000 scalar requests fail before queuing" not in text


def test_planner_owned_scope_replaces_public_cli_plan_and_budget_contracts() -> None:
    text = (ROOT / "architecture" / "b524-namespace-invariants.md").read_text(
        encoding="utf-8"
    )
    for removed in (
        "--scan-plan",
        "--b524-read-plan",
        "--preview-read-plan",
        "--description-budget",
        "--request-budget",
        "--probe-constraints",
        "100000 scalar requests fail before queuing",
    ):
        assert removed not in text
    assert "Planner configuration owns finite selected scope" in text
    assert "`incomplete`, never an absence" in text


def test_historical_scan_plan_synthetic_vectors_remain_readable() -> None:
    cases = json.loads(
        (ROOT / "tests" / "fixtures" / "b524_scan_plan_v1_cases.json").read_text()
    )
    assert cases["source"] == "synthetic_contract_vectors"
    assert cases["accepted"][0]["normalized"] == cases["accepted"][1]["normalized"]
    assert cases["accepted"][2]["expected_requests"] == 100000
    assert cases["rejected"][0]["name"] == "request_limit_exceeded"


def test_semantic_scan_policy_uses_complete_descriptions_and_unqualified_history() -> (
    None
):
    text = SEMANTIC_MAPPING.read_text(encoding="utf-8")
    assert "probe `0x00` directory sequentially" not in text
    assert "probe `0x01 GG RR`" not in text
    assert "Authoritative for value ranges" not in text
    assert "01 GG II RRlo RRhi" in text
    assert "07 GG II RRlo RRhi" in text
    assert "historical evidence only, not authority" in text


def test_semantic_fallback_and_b509_evidence_links_match_the_op06_catalog() -> None:
    semantic = SEMANTIC_MAPPING.read_text(encoding="utf-8")
    boiler_map = (
        ROOT / "protocols" / "vaillant" / "ebus-vaillant-B509-boiler-register-map.md"
    ).read_text(encoding="utf-8")
    anchor = "#op0x06--controller-mediated-device-parameters"

    assert "0x0C 0x06    0x08         0x002F" in semantic
    assert "0x0C 0x06    0x08         0x003F" not in semantic
    assert anchor in semantic
    assert anchor in boiler_map


def test_device_enumeration_preserves_ii01_and_retained_inventory_contract() -> None:
    text = (ROOT / "development/ebus-vaillant-b524-explorer-discovery.md").read_text()
    section = text.split("## OP06 connected-device discovery", 1)[1].split(
        "### GG0D relay-module predicate", 1
    )[0]
    normalized = " ".join(section.split())
    assert "begin at II01" in normalized
    assert "Unknown results do not stop the next probe" in normalized
    assert (
        "`full` and `research` retain the complete configured audit interval"
        in normalized
    )
    assert "does not erase retained identity evidence" in normalized
    neutral = REGISTER_MAP.read_text()
    assert "**Device slot observations:**" in neutral
    assert "**Device slot enumeration:**" not in neutral


def test_relay_connection_candidate_preserves_unknown_native_qualification() -> None:
    text = (
        ROOT / "development" / "ebus-vaillant-b524-explorer-discovery.md"
    ).read_text(encoding="utf-8")
    section = text.split("### GG0D relay-module predicate", 1)[1].split(
        "## Descriptions for every eligible parameter", 1
    )[0]
    assert "common `device_connected` name" in section
    assert "**Hypothesis; native qualification Unknown:**" in section
    assert "no positive, correlated\nGG0D/RR0001 observation is published" in section
    assert "`source=heuristic_probe`" in section
    assert (
        "not qualified\nnative connection evidence or physical inventory proof"
        in section
    )
    assert "qualified RR0001 predicate" not in text


def test_functional_module_presentation_names_preserve_the_evidence_boundary() -> None:
    register_map = REGISTER_MAP.read_text(encoding="utf-8")
    profile = (
        ROOT / "development" / "ebus-vaillant-b524-explorer-discovery.md"
    ).read_text(encoding="utf-8")
    architecture = (ROOT / "architecture" / "functional-modules.md").read_text(
        encoding="utf-8"
    )

    assert "`OP=0x06, GG=0x0B` = **Functional\nModules (VR70) FM3**" in register_map
    assert "observed scheduling ceiling" in register_map
    assert (
        "| 0x06 | 0x0B | Functional Modules (VR70) FM3 | Yes | 0x08 | 0x002F |"
        in register_map
    )
    assert "is not a documented\nB524 selector route" not in register_map
    assert (
        "`OP=0x06, GG=0x0C` is presented as **Functional Modules (VR71) FM5**"
        in register_map
    )
    assert "`functional_modules_vr70`" in profile
    assert "concrete Boolean required per slot" in profile
    assert "Catalog visibility\ndoes not create a group route" in profile
    assert "`OP=0x06, GG=0x0B`" in architecture
    assert "`OP=0x06, GG=0x0C`" in architecture
    routing = (
        B524.read_text(encoding="utf-8")
        .split("### 3.2 Opcode routing", 1)[1]
        .split("**Unqualified presentation candidate:**", 1)[0]
    )
    assert "GG=0x0B" not in routing


def test_op06_presentation_catalog_is_complete_and_cannot_expand_discovery() -> None:
    text = B524.read_text(encoding="utf-8")
    register_map = REGISTER_MAP.read_text(encoding="utf-8")
    profile = (
        ROOT / "development" / "ebus-vaillant-b524-explorer-discovery.md"
    ).read_text(encoding="utf-8")

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
    assert "publishable correlated wire and identity evidence" in text
    assert "| 05 | Wärmepumpe Zubehör Appliance Interface (VWZ-AI) |" in text
    assert "| 06 | Pumpen Module - Solar (VPM-S) auroFLOW |" in text
    assert "| 07 | Pumpen Module - Wasser (VPM-W) aguaFLOW |" in text
    assert "| 08 | Modul Solar (VMS) auroSTEP |" in text
    assert "| 0x06 | 0x01 | Boiler |" in register_map
    assert "| 0x06 | 0x02 | Heat Pump |" in register_map
    assert "| 0x06 | 0x08 | Modul Solar (VMS) auroSTEP |" in register_map
    assert (
        "| 0x06 | 0x09 | Remote Control Regulators (VRC7xx, VRT38x) |" in register_map
    )
    assert "| 0x06 | 0x0A | Remote Control Thermostats (VR9x) |" in register_map
    assert "| 0x06 | 0x0E | Clock Module |" in register_map
    assert "| 0x06 | 0x0F | Base Station |" in register_map
    assert (
        "| 0C | Functional Modules (VR71) FM5 | `functional_modules_vr71` | Hypothesis"
        in text
    )
    assert "### GG=0x0C — Functional Modules (VR71) FM5" in register_map
    assert (
        "GG0B\nmust not receive GG0C's scan policy or `device_connected` predicate"
        in text
    )
    assert "`unused` for GG04 does not justify suppressing a probe" in profile


def test_register_map_preserves_exact_gg05_and_ventilation_presentation_annotations() -> (
    None
):
    text = REGISTER_MAP.read_text(encoding="utf-8")
    ventilation = text.split("### GG=0x09 — Ventilation", 1)[1].split(
        "### GG=0x0A — Local Parameters", 1
    )[0]
    normalized_ventilation = " ".join(ventilation.split())

    assert text.count("Wärmepumpe Zubehör Appliance Interface (VWZ-AI)") == 2
    assert "Appliance Interface (VWZ-AI)" not in text.replace(
        "Wärmepumpe Zubehör Appliance Interface (VWZ-AI)", ""
    )
    assert "TLI controller" not in text
    assert "**Hypothesis** for a VRC720 controller" in ventilation
    assert ventilation.count("`1=TIME_CONTROLLED 2=NORMAL 3=REDUCED`") == 2
    assert ventilation.count("`0=REGULAR 1=BOOST 7=HOLIDAY 10=SYSTEM_OFF`") == 2
    assert (
        "ventilation_status_special_operating_mode | S | u16 | — | — | 0..10"
        in ventilation
    )
    assert "numeric domain unknown" not in ventilation
    assert "operator-selected presentation annotations" in normalized_ventilation
    assert "not independently native-verified" in normalized_ventilation
    assert "Unknown values remain numeric/unknown" in normalized_ventilation


def test_register_catalog_is_strictly_partitioned_by_opcode() -> None:
    text = REGISTER_MAP.read_text(encoding="utf-8")
    op02 = text.split("## OP=0x02 — Local Parameter Registers", 1)[1].split(
        "## OP=0x06 — Controller-Mediated Device Parameters", 1
    )[0]
    op06 = text.split("## OP=0x06 — Controller-Mediated Device Parameters", 1)[1].split(
        "## Constraint Catalog", 1
    )[0]

    assert (
        op02.index("### GG=0x09 — Ventilation")
        < op02.index("### GG=0x09 — Ventilation / recoVair Candidates")
        < op02.index("### GG=0x0A — Local Parameters")
    )
    assert "(opcode 0x06)" not in op02
    assert "### GG=0x08 — Modul Solar (VMS) auroSTEP" in op06
    assert "### GG=0x09 — Remote Control Regulators (VRC7xx, VRT38x)" in op06
    assert "### GG=0x0A — Remote Control Thermostats (VR9x)" in op06


def test_op02_naming_catalog_matches_exact_operation_group_register_rows() -> None:
    import csv
    import re

    source = (
        ROOT / "protocols" / "vaillant" / "fixtures" / "b524-op02-register-names.csv"
    )
    names = list(csv.DictReader(source.open(encoding="utf-8")))
    assert len(
        {(row["opcode"], row["group"], row["register"]) for row in names}
    ) == len(names)
    text = (
        REGISTER_MAP.read_text(encoding="utf-8")
        .split("## OP=0x02 — Local Parameter Registers", 1)[1]
        .split("## OP=0x06 — Controller-Mediated Device Parameters", 1)[0]
    )
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

    names = {
        1: "device_connected",
        2: "device_class_address",
        3: "device_error_code",
        4: "device_firmware_version",
    }
    text = REGISTER_MAP.read_text(encoding="utf-8")
    remote = text.split("## OP=0x06 — Controller-Mediated Device Parameters", 1)[
        1
    ].split("## Constraint Catalog", 1)[0]
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
    section = (
        REGISTER_MAP.read_text(encoding="utf-8")
        .split("### GG=0x0A — Local Parameters", 1)[1]
        .split("## OP=0x06 — Controller-Mediated Device Parameters", 1)[0]
    )
    assert "physical-device identity, role and topology remain" in section
    assert "**Unknown**" in section
    assert "Repetition does not establish a physical" in section
    assert "template/default purpose" in section
    assert "this is a template/default configuration" not in section
    assert "| Radio sensors VR92. 69 regs/instance." not in REGISTER_MAP.read_text(
        encoding="utf-8"
    )


def test_protocol_overview_preserves_unknown_role_and_topology_for_op02_gg0a() -> None:
    text = B524.read_text(encoding="utf-8")
    selector_row = next(
        line
        for line in text.splitlines()
        if line.startswith("| `0x02` | Local controller selector family |")
    )
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
    assert "not as a current\nprofile bound or a qualified device count" in local
    assert "OP06/GG08 remains a separate instanced selector set" in local
    assert "| 0x02 | 0x08 | DeltaT (local) | Unknown | profile-dependent |" in text
    assert (
        "| 0x02 | 0x08 DeltaT | profile-dependent | 0x0007 | observed scope |" in text
    )
    profiles = text.split("### Discovery Profiles", 1)[1]
    assert profiles.index("| 0x02 | 0x08 DeltaT |") < profiles.index(
        "| 0x06 | 0x08 Modul Solar (VMS) auroSTEP |"
    )
    assert "| 0x08 | 0x02 (local) | 0x00 |" not in text


def test_op06_observed_windows_fixture_preserves_generic_and_concrete_boundaries() -> (
    None
):
    fixture = json.loads(
        (
            ROOT
            / "protocols"
            / "vaillant"
            / "fixtures"
            / "b524-op06-observed-windows-v1.json"
        ).read_text(encoding="utf-8")
    )
    profile = (
        ROOT / "development" / "ebus-vaillant-b524-explorer-discovery.md"
    ).read_text(encoding="utf-8")

    assert fixture["schema_version"] == "b524-op06-observed-windows/v1"
    windows = {
        tuple(row["groups"]): row["rr_through"]
        for row in fixture["observed_scheduling_windows"]
    }
    assert (
        windows[
            ("0x01", "0x02", "0x03", "0x05", "0x06", "0x07", "0x08", "0x0b", "0x0c")
        ]
        == "0x002f"
    )
    assert windows[("0x09", "0x0a")] == "0x0035"
    assert windows[("0x0e", "0x0f")] == "0x0033"
    assert windows[("0x04", "0x0d")] is None

    raw_ceiling_selectors = {
        (sample["selector"]["gg"], sample["selector"]["rr"])
        for sample in fixture["samples"]
        if sample.get("request_payload_hex") and sample.get("reply_payload_hex")
    }
    for window in fixture["observed_scheduling_windows"]:
        if window["rr_through"] is not None:
            for group in window["groups"]:
                assert (group, window["rr_through"]) in raw_ceiling_selectors

    generic = next(
        sample
        for sample in fixture["samples"]
        if sample["kind"] == "generic_description"
    )
    assert generic["selector"]["ii"] == "0xff"
    assert generic["device_identity_verified"] is False
    raw_rr002f = {
        sample["selector"]["gg"]
        for sample in fixture["samples"]
        if sample["kind"] == "generic_description_raw"
        and sample["selector"]["ii"] == "0xff"
        and sample["selector"]["rr"] == "0x002f"
        and sample["qualification"] == "unqualified"
    }
    assert raw_rr002f == {
        "0x01",
        "0x02",
        "0x03",
        "0x05",
        "0x06",
        "0x07",
        "0x08",
        "0x0b",
        "0x0c",
    }
    raw_rr0035 = {
        sample["selector"]["gg"]
        for sample in fixture["samples"]
        if sample["kind"] == "generic_description_raw"
        and sample["selector"]["ii"] == "0xff"
        and sample["selector"]["rr"] == "0x0035"
        and sample["qualification"] == "unqualified"
    }
    assert raw_rr0035 == {"0x09", "0x0a"}
    tails = [
        sample
        for sample in fixture["samples"]
        if sample["kind"] == "concrete_read" and sample["selector"]["rr"] == "0x0033"
    ]
    assert {
        (sample["selector"]["gg"], sample["flags"], sample["classification"])
        for sample in tails
    } == {
        ("0x0e", "0x01", "read_only_visible"),
        ("0x0f", "0x00", "read_only_not_visible"),
    }
    assert "not properties of the generic IIFFh catalog alone" in profile
    assert "never terminal maxima" in profile


def test_op06_observed_window_validator_correlates_every_request_and_reply(
    tmp_path: Path,
) -> None:
    source_path = (
        ROOT
        / "protocols"
        / "vaillant"
        / "fixtures"
        / "b524-op06-observed-windows-v1.json"
    )
    source = json.loads(source_path.read_text(encoding="utf-8"))
    ci = (ROOT / "scripts" / "ci_local.sh").read_text(encoding="utf-8")
    assert "validate_b524_op06_observed_windows.py" in ci

    baseline = subprocess.run(
        ["python3", "scripts/validate_b524_op06_observed_windows.py", str(source_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert baseline.returncode == 0, baseline.stderr

    mutations = (
        (0, "request_payload_hex", "0709ff0100"),
        (1, "reply_payload_hex", "022f00000601"),
        (12, "request_payload_hex", "06000f013300"),
        (13, "reply_payload_hex", "000e330000"),
        (12, "flags", "0x00"),
    )
    for case, (index, field, value) in enumerate(mutations):
        fixture = json.loads(json.dumps(source))
        fixture["samples"][index][field] = value
        candidate = tmp_path / f"mismatched-observed-window-{case}.json"
        candidate.write_text(json.dumps(fixture))
        result = subprocess.run(
            [
                "python3",
                "scripts/validate_b524_op06_observed_windows.py",
                str(candidate),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0, case


def test_current_profile_uses_opcode_scoped_names_and_present_instance_bounds() -> None:
    register_map = REGISTER_MAP.read_text(encoding="utf-8")
    protocol = B524.read_text(encoding="utf-8")
    profile = (
        ROOT / "development" / "ebus-vaillant-b524-explorer-discovery.md"
    ).read_text(encoding="utf-8")
    namespace = (ROOT / "architecture" / "b524-namespace-invariants.md").read_text(
        encoding="utf-8"
    )
    semantic = SEMANTIC_MAPPING.read_text(encoding="utf-8")

    for group, label, name in (
        ("00", "System", "system"),
        ("01", "Native Domestic Hot Water", "native_domestic_hot_water"),
        ("02", "Circuits", "circuits"),
        ("03", "Zones", "zones"),
        ("04", "Solar Circuit", "solar_circuit"),
        ("05", "Solar Loaded Cylinder", "solar_loaded_cylinder"),
        ("06", "Device", "device"),
        ("07", "Generator", "generator"),
        ("08", "DeltaT", "delta_t"),
        ("09", "Ventilation", "ventilation"),
    ):
        assert f"| {group} | {label} | `{name}` |" in protocol

    assert "| 0x02 | 0x02 | Circuits | Yes | 0x09 | 0x25 |" in register_map
    assert "II00..II08 as ordinary heating-circuit candidates and II09 as the virtual" in register_map
    assert "Historical scan records include II0A probes" in register_map
    assert (
        "over II01..II08 for the characterized profile. `II=0x00`, `II=0x09`, and\n`II=0x0A` are outside its current OP06 slot interval"
        in register_map
    )
    assert (
        "every OP06 GG admitted by a scan plan uses the common candidate\nslot interval II01..II08"
        in profile
    )
    assert "does not create a group route" in profile
    assert "Browser tree is a present-instance view" in profile
    assert (
        "`present=true`; a legacy artifact without that field may retain a successful\nobserved raw reply"
        in profile
    )
    assert (
        "not_connected`, empty, timeout, decode failure, and\nunprobed/unknown selectors remain"
        in profile
    )
    assert "does not alter the artifact or create a\nsynthetic slot" in profile
    assert "deselected groups are omitted" in profile
    assert "explicitly selected\nempty group may remain" in profile
    assert (
        "Custom selections enforce the same selector intervals before transport I/O"
        in profile
    )
    assert "OP06 permits II01..II08 and OP02/GG02 permits II00..II09" in profile
    assert (
        "OP06 candidates use II01..II08; OP02/GG02 uses\nII00..II08 for heating candidates plus II09"
        in namespace
    )
    assert "II00 and\nII01 return raw `0100`" in register_map
    assert "zone II00 maps to raw `00` and zone II01 to raw `01`; II02+" in register_map
    assert "0x02 0x02    0x09         0x0025" in semantic
    assert "0x09 0x06    0x08         0x0035" in semantic
    assert "scan planner" not in protocol
    assert "Browser" not in protocol


def test_browser_write_contract_preserves_confirmation_and_native_boundaries() -> None:
    text = (ROOT / "development" / "ebus-vaillant-b524-browser-writes.md").read_text(
        encoding="utf-8"
    )
    for required in (
        "Opening JSON starts an offline Browser session",
        "explicitly confirm the limited exception for an absent or incomplete limit",
        "one write attempt only",
        "Only readback of the exact selector confirms the desired value",
        "Native Event\nwrites remain disabled",
        "zero implicit descriptions",
        "manually share JSON",
    ):
        assert required in text
    assert "every known min/max/STEP violation is rejected" in text
    assert "For absent or incomplete limits there are two\nseparate confirmations, in order" in text
    assert "One combined acknowledgement cannot authorize this path" in text
    assert "invalidates both confirmations" in text
    assert "`--transport`, `--host`, `--port`, `--source-address`, and optional `--preset`" in text
    assert "`browse` accepts no configuration argv" in text
    assert "There are no hidden\nglobal request or description budgets" in text


def test_count_guidance_and_gg0d_predicate_preserve_identity_and_unknowns() -> None:
    profile = (
        ROOT / "development" / "ebus-vaillant-b524-explorer-discovery.md"
    ).read_text(encoding="utf-8")
    architecture = (ROOT / "architecture" / "b524-namespace-invariants.md").read_text(
        encoding="utf-8"
    )

    assert "OP02/GG00 is mandatory" in architecture
    assert "RR0000..00FF" in architecture
    assert "ID04 `device_count` compares all confirmed\nOP06 slots" in architecture
    assert (
        "GG03,\nGG05, GG08, GG0A, GG0D, GG0E, and GG0F have no count mapping"
        in architecture
    )
    assert "OP02/GG09 II00 in `recommended`" in architecture
    assert "OP06/GG04 and OP06/GG0D have Unknown RR maxima" in architecture
    assert "GG0D still receives its dedicated RR0001 presence probe" in architecture
    recommended = architecture.split("### `recommended` (default)", 1)[1].split(
        "### `full`", 1
    )[0]
    assert "OP06/GG0D II01..II08/RR0001" in recommended
    assert "availability-only probe using `device_connected`" in recommended
    assert "II09 is independent" in profile
    assert (
        "supported meaning is capacity, not configured or\npresent-instance cardinality"
        in profile
    )
    assert "| 0 | 0 | 1 | 1 |" in profile
    assert "| 3 | 1 | 8 | 8 |" in profile
    assert "two configured or confirmed circuits with\ncircuit capacity `3`" in profile
    assert "They never construct instances" in profile
    assert (
        "does not by itself make concrete presence qualification\nincomplete" in profile
    )
    assert (
        "Every other mapped OP00 count retains count-guided cardinality semantics"
        in profile
    )
    assert "valid zero suppresses only\nderived default candidates" in profile
    assert "OP00 ID05\ngenerator mapping and no ID17 cooling-group mapping" in profile
    assert "OP02/GG01 uses only II00" in profile
    assert "exact two-byte UIN value\nthat is nonzero" in profile
    assert "GG0D relay-module predicate" in profile
    assert "uses the common `device_connected` name" in profile
    assert "RR maximum is Unknown" in profile


def test_event_and_timer_operations_have_separate_selectors_and_write_boundary() -> (
    None
):
    text = B524.read_text(encoding="utf-8")
    timer = text.split("### 4.4", 1)[1].split("### 4.5", 1)[0]
    events = text.split("### 4.5", 1)[1].split("### 4.6", 1)[0]
    assert "03 GG II ADDRESS WEEKDAY" in timer
    assert "START1 STOP1 START2 STOP2 START3 STOP3" in timer
    assert "`70000` or `B7S00`" in timer
    assert "crosswalk" in timer
    assert "90 90" in timer
    for operation in ("GetEvent", "SetEvent", "GetEventSetPoint", "SetEventSetPoint"):
        assert operation in events
    assert "do not inherit the VRC700-only timer gate" in events
    assert (
        "Event execution stays disabled"
        in (ROOT / "development/ebus-vaillant-b524-operation-reads.md").read_text()
    )
    assert "Neither `II` nor the request selector is echoed" in events
    assert "VALUE1 remains raw" in events


def test_all_public_documents_have_publishable_attribution() -> None:
    from scripts.check_public_domain_boundary import unpublishable_attribution

    assert unpublishable_attribution(ROOT) == []


def test_regulator_crosswalk_is_exact_pair_based_and_keeps_raw_sw_distinct() -> None:
    text = REGULATORS.read_text(encoding="utf-8")
    rows = {
        tuple(cell.strip().strip("`") for cell in line.strip().strip("|").split("|"))
        for line in text.splitlines()
        if line.startswith("| `")
    }
    fixture = json.loads(
        (
            ROOT
            / "tests"
            / "fixtures"
            / "vaillant_regulator_identity_crosswalk_v1.json"
        ).read_text()
    )
    assert fixture["schema_version"] == 1
    expected = {tuple(row) for row in fixture["rows"]}

    assert rows == expected
    assert len(expected) == 39
    assert "EID\nand decoded SW/SPN value match as a pair" in text
    assert "Hypothesis" in text
    assert "native-model evidence pending" in text
    assert (
        "`identity.model_assignment_qualification` to `project_catalog`"
        in (ROOT / "development/ebus-vaillant-regulator-identification.md").read_text()
    )
    assert "Do not interpret raw `04 17` as `0x0417`" in text
    assert "`B7V00` / `0163` VRC700 R4 row" in text
    assert "B7S00" not in text


def test_regulator_and_b524_renames_have_no_stale_paths_or_vrc700_alias() -> None:
    old_paths = (
        ROOT / "protocols" / "vaillant" / "basv.md",
        ROOT / "protocols" / "vaillant" / "b524-profile-discovery-and-descriptions.md",
        ROOT / "protocols" / "vaillant" / "b524-survey-methodology.md",
    )
    assert not any(path.exists() for path in old_paths)
    for path in (
        REGULATORS,
        ROOT / "development" / "ebus-vaillant-b524-explorer-discovery.md",
        ROOT / "protocols" / "vaillant" / "ebus-vaillant-b524-survey-methodology.md",
    ):
        assert path.exists()
    for path in (
        B524,
        ROOT / "protocols" / "vaillant" / "ebus-vaillant-b555-timer-protocol.md",
        ROOT / "protocols" / "vaillant" / "ebus-vaillant.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert "ebus-vaillant-regulators.md" in text


def test_attribution_check_rejects_nonpublic_citations() -> None:
    from scripts.check_public_domain_boundary import UNPUBLISHABLE

    for marker in (
        "private/",
        "restricted static-analysis",
        "UNPUBLISHED-semantic-example.md",
    ):
        assert UNPUBLISHABLE.search(marker)


def test_b524_split_fragment_links_resolve_to_the_owning_contract() -> None:
    references = [
        (
            REGISTER_MAP,
            "ebus-vaillant-b524-profile-discovery-and-descriptions.md",
            "availability-observations",
        ),
        (
            ROOT / "architecture/b524-namespace-invariants.md",
            "../development/ebus-vaillant-b524-explorer-discovery.md",
            "op06-connected-device-discovery",
        ),
        (
            ROOT / "development/ebus-vaillant-b524-description-acquisition.md",
            "../protocols/vaillant/ebus-vaillant-B524-register-map.md",
            "constraint-catalog",
        ),
    ]
    for source, target, fragment in references:
        assert f"]({target}#{fragment})" in source.read_text()
        headings = re.findall(
            r"^#{1,6} (.+)$", (source.parent / target).read_text(), re.M
        )
        anchors = {
            re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-")
            for heading in headings
        }
        assert fragment in anchors
