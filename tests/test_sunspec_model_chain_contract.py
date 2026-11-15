from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUNSPEC_README = ROOT / "architecture/protocol-routing-vendor-sunspec-overview.md"
CHAIN_CONTRACT = ROOT / "architecture/protocol-routing-vendor-sunspec-model-chain-v1.md"
MODBUS_README = ROOT / "architecture/protocol-routing-vendor-modbus-overview.md"
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


def test_application_contract_keeps_neutral_protocol_sources_separate() -> None:
    readme = text(SUNSPEC_README)
    contract = text(CHAIN_CONTRACT)

    assert "AGPL-3.0" in readme
    assert "CC0" in (ROOT / "protocols/sunspec/README.md").read_text()
    assert "implementation-neutral" in (ROOT / "protocols/sunspec/README.md").read_text()
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

    catalog = contract[contract.index("## Model\n") : contract.index("## Model Chain")]
    fixed_lengths: dict[int, set[int]] = {}
    for model_group, length in re.findall(
        r"Models? ((?:`\d+`(?:, and | and |, )?)+).*?`L(\d+)`",
        catalog,
        flags=re.DOTALL,
    ):
        for model_id in re.findall(r"`(\d+)`", model_group):
            fixed_lengths.setdefault(int(model_id), set()).add(int(length))

    assert fixed_lengths == {
        1: {66},
        101: {50},
        102: {50},
        103: {50},
        111: {60},
        112: {60},
        113: {60},
        120: {26},
        121: {30},
        122: {44},
        123: {24},
        124: {24},
    }
    assert re.search(r"Model `1`.*?standard length `L66`", catalog, re.DOTALL)
    assert re.search(r"Model `1`.*?`L65`.*?compatibility", catalog, re.DOTALL)
    assert "(1, 65, schema_revision)" in catalog
    assert "distinct from the standard L66 key" in catalog
    assert "raw-retained unsupported" in catalog
    assert "cannot admit a\n  capability" in catalog
    assert "no model-ID fallback is permitted" in catalog
    assert re.search(r"Model `160`.*?`L = 8 \+ 20 \* N`", catalog, re.DOTALL)

    for required in (
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


def test_three_phase_capability_equivalence_is_semantic_and_fail_closed() -> None:
    contract = text(CHAIN_CONTRACT)
    capability = contract[
        contract.index("## Capability Profile") : contract.index("## Vendor Flavor")
    ]

    assert CAPABILITY_ID in capability
    assert re.search(r"Model `103` or Model `113`", capability)
    assert "complete,\nvalid minimum fact set" in capability
    assert "same profile keys" in capability
    assert "canonical field ID" not in capability
    assert "units" in capability
    assert "three-phase topology" in capability
    assert "distinct decoder keys" in capability
    assert "distinct\nraw encodings and provenance" in capability
    assert "does not assert equal\nprecision or representation" in capability

    for rejected in (
        "wrong model length",
        "invalid encoding",
        "sentinel",
        "non-finite value",
    ):
        assert rejected in capability
    assert "fails admission" in capability
    assert "partial or inferred capability" in capability


def test_model_chain_malformed_grammar_is_explicitly_fail_closed() -> None:
    contract = text(CHAIN_CONTRACT)
    chain = contract[
        contract.index("## Model Chain") : contract.index("## Capability Profile")
    ]

    for rejected in (
        "bad signature",
        "nonterminal zero length",
        "arithmetic overflow",
        "extent overrun",
        "malformed\nor missing end marker",
        "nonzero end-marker length",
        "trailing words after a\nterminal end marker",
    ):
        assert rejected in chain
    assert (
        "do\nnot produce a valid chain, typed observation, capability, or vendor flavor"
        in chain
    )

    assert "exactly one\nCommon Model `1`" in chain
    assert "must be the first occurrence after the\nsignature" in chain
    for rejected in (
        "missing Common Model",
        "out-of-order Common Model",
        "repeated\nCommon Model",
    ):
        assert rejected in chain
    assert "fails semantic admission" in chain
    assert "produces no typed observation,\ncapability, or vendor flavor" in chain


def test_existing_fronius_material_is_legacy_only_and_points_to_registry_selection() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    evidence = text(EVIDENCE)
    boundaries = text(BOUNDARIES)
    qualification = text(QUALIFICATION)
    modbus_readme = text(MODBUS_README)
    package_pin = manifest["sources"][1]["sha256"]

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
    assert package_pin == FRONIUS_PACKAGE_SHA256
    assert FRONIUS_PACKAGE_SHA256 in evidence
    assert FRONIUS_PACKAGE_SHA256 in text(CHAIN_CONTRACT)


ELEMENT_INVENTORY = (
    "https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/main/"
    "api/v1/graph.md#10-element-catalog"
)
DEFERRAL = (
    "Canonical field identity belongs to the common element inventory; this "
    "page keeps native model and point names only."
)
PROFILE_POINTS = {
    "inverter.ac.current.total": "A",
    "inverter.ac.current.phase_a": "AphA",
    "inverter.ac.current.phase_b": "AphB",
    "inverter.ac.current.phase_c": "AphC",
    "inverter.ac.voltage.phase_a": "PhVphA",
    "inverter.ac.voltage.phase_b": "PhVphB",
    "inverter.ac.voltage.phase_c": "PhVphC",
    "inverter.ac.power.active": "W",
    "inverter.ac.frequency": "Hz",
    "inverter.ac.energy_lifetime": "WH",
    "inverter.temperature.cabinet": "TmpCab",
    "inverter.operating_state": "St",
    "inverter.events.1": "Evt1",
    "inverter.events.2": "Evt2",
}
ATTRIBUTION_HEADING = "## Resource attribution of a multi-device chain"
ATTRIBUTION_HEADER = (
    "| Occurrence class | Native models | Resource kind it would describe "
    "| Mapping grade | Mapping source | State | Reason |"
)
WITHHELD_REASON = "MULTI_DEVICE_UNATTRIBUTED"
# Occurrence class -> (native model IDs, resource kinds, state).
# Required clauses of each reason are listed in REASON_CLAUSES.
# Mapping grade per occurrence class, and the artifacts every source cites.
EXPECTED_GRADE = {
    "Inverter": "Proven",
    "Meter": "Hypothesis",
    "Storage control": "Hypothesis",
    "Per-device repeat": "Unknown",
}
SOURCE_CLAUSES = {
    "Inverter": ("`sunspec/models` pin", "element inventory of docs-semantic"),
    "Meter": ("`sunspec/models` pin", "element inventory of docs-semantic"),
    "Storage control": ("`sunspec/models` pin", "element inventory of docs-semantic"),
    "Per-device repeat": ("no exact section", "element inventory names no resource kind"),
}
EXPECTED_ATTRIBUTION = {
    "Inverter": (
        ("101", "102", "103", "111", "112", "113"),
        ("resource.inverter", "resource.phase"),
        "attributed",
    ),
    "Meter": (
        ("201", "202", "203", "204", "211", "212", "213", "214"),
        ("resource.meter",),
        "unsupported",
    ),
    "Storage control": (("124",), ("resource.battery", "resource.storage_system"), "unsupported"),
    "Per-device repeat": (
        ("1",),
        ("resource.inverter", "resource.meter", "resource.equipment"),
        "unsupported",
    ),
}
REASON_CLAUSES = {
    "Inverter": (
        "Attributed only in a single-device chain",
        "one-resource-per-unit rule",
        "contains its phases by position",
    ),
    "Meter": (
        "No decoder of this page admits a meter model",
        "carries no identity of a meter",
        "configured `measures` relation that is not defined for this family",
    ),
    "Storage control": (
        "carries no identity of a battery",
        "configured relation that is not defined for this family",
        "outside the capability profile",
    ),
    "Per-device repeat": (
        "position of a segment in the chain is an address, not an identity",
        "lists no identification scheme for a device of a chain",
    ),
}


def normalize(value: str) -> str:
    return " ".join(value.split())


def attribution_section(contract: str) -> str:
    start = contract.index(ATTRIBUTION_HEADING)
    end = contract.index("\n## ", start + len(ATTRIBUTION_HEADING))
    return contract[start:end]


def attribution_rows(section: str) -> list[list[str]]:
    lines = section.splitlines()
    start = lines.index(ATTRIBUTION_HEADER)
    rows = []
    for line in lines[start + 2 :]:
        if not line.startswith("|"):
            break
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows


def row_errors(row: list[str]) -> list[str]:
    if len(row) != 7:
        return [f"row width {row}"]
    occurrence, models, kinds, grade, source, state, reason = row
    if occurrence not in EXPECTED_ATTRIBUTION:
        return []
    want_models, want_kinds, want_state = EXPECTED_ATTRIBUTION[occurrence]
    errors = []
    got_models = tuple(re.findall(r"`(\d+)(?:/L\d+)?`", models))
    if got_models != want_models:
        errors.append(f"{occurrence}: models {got_models}")
    got_kinds = tuple(re.findall(r"`(resource\.[a-z_]+)`", kinds))
    if got_kinds != want_kinds:
        errors.append(f"{occurrence}: kinds {got_kinds}")
    if state != want_state:
        errors.append(f"{occurrence}: state {state!r}")
    if grade != EXPECTED_GRADE[occurrence]:
        errors.append(f"{occurrence}: grade {grade!r}")
    errors += [
        f"{occurrence}: source lacks {clause!r}"
        for clause in SOURCE_CLAUSES[occurrence]
        if clause not in normalize(source)
    ]
    errors += [
        f"{occurrence}: reason lacks {clause!r}"
        for clause in REASON_CLAUSES[occurrence]
        if clause not in normalize(reason)
    ]
    return errors


def attribution_errors(contract: str) -> list[str]:
    """Return every way the attribution table departs from the contract."""
    try:
        rows = attribution_rows(attribution_section(contract))
    except ValueError as error:
        return [f"attribution table missing: {error}"]
    errors = []
    classes = [row[0] for row in rows]
    if classes != list(EXPECTED_ATTRIBUTION):
        errors.append(f"occurrence classes {classes}")
    for row in rows:
        errors += row_errors(row)
    return errors


def test_field_identity_is_deferred_to_the_common_element_inventory() -> None:
    contract = text(CHAIN_CONTRACT)
    normalized = normalize(contract)
    capability = contract[
        contract.index("## Capability Profile") : contract.index("## Vendor Flavor")
    ]

    assert DEFERRAL in normalized
    assert ELEMENT_INVENTORY in contract
    assert "Canonical field ID" not in contract
    assert "| Profile key | Unit | Native point in Models 103 and 113 |" in capability
    rows = re.findall(r"^\| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \|$", capability, re.MULTILINE)
    assert {key: point for key, _unit, point in rows} == PROFILE_POINTS
    for required in (
        "A profile key names a required fact inside this capability profile only",
        "it is not a field identifier",
        "a phase is a resource of its own, a component of its inverter",
    ):
        assert required in normalized


def test_multi_device_chain_attribution_is_stated_per_occurrence_class() -> None:
    contract = text(CHAIN_CONTRACT)
    assert attribution_errors(contract) == []

    section = normalize(attribution_section(contract))
    for required in (
        "A **multi-device chain** is a terminal-verified chain whose first occurrence "
        "is Common Model `1` and which carries a further Common occurrence;",
        "Nothing of a multi-device chain is published before its row is attributed.",
        "The semantic values of a multi-device chain are withheld with the reason "
        f"`{WITHHELD_REASON}`",
        "a chain with exactly one Common occurrence is a single-device chain",
        "The native provider and the native surface proceed",
        "Attributed only in a single-device chain",
        "is not a catalog disposition",
        "This segmentation rule is a **Hypothesis**",
        "no exact section of it is pinned for the rule",
    ):
        assert required in section
    # The capability decision for a repeated Common occurrence is unchanged.
    assert "`INVALID_CHAIN`" in section


def _mutate(contract: str, old: str, new: str) -> str:
    assert contract.count(old) == 1, old
    return contract.replace(old, new)


def test_attribution_checker_rejects_a_change_of_any_row_field() -> None:
    contract = text(CHAIN_CONTRACT)
    rows = attribution_rows(attribution_section(contract))
    assert len(rows) == len(EXPECTED_ATTRIBUTION)

    for row in rows:
        line = "| " + " | ".join(row) + " |"
        occurrence, models, kinds, grade, source, state, reason = row
        mutations = {
            "occurrence class": [f"{occurrence} occurrence", *row[1:]],
            "native models": [occurrence, models.replace("`", "", 2), *row[2:]],
            "resource kind": [
                occurrence, models, kinds.replace("resource.", "resource.x", 1), *row[3:]
            ],
            "mapping grade": [occurrence, models, kinds, "Proven" if grade != "Proven" else "Unknown", *row[4:]],
            "mapping grade removed": [occurrence, models, kinds, "", *row[4:]],
            "mapping source": [occurrence, models, kinds, grade, "Not stated.", state, reason],
            "state": [
                occurrence,
                models,
                kinds,
                grade,
                source,
                "unsupported" if state == "attributed" else "attributed",
                reason,
            ],
            "reason": [occurrence, models, kinds, grade, source, state, "None."],
            "reason replaced by unrelated text": [
                occurrence,
                models,
                kinds,
                grade,
                source,
                state,
                "The weather forecast for the coming week predicts mild temperatures.",
            ],
        }
        for field, cells in mutations.items():
            mutated = _mutate(contract, line, "| " + " | ".join(cells) + " |")
            assert attribution_errors(mutated), (occurrence, field)

        dropped = _mutate(contract, line + "\n", "")
        assert attribution_errors(dropped), (occurrence, "row removed")
