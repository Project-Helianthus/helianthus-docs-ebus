from __future__ import annotations

import json
import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("naming_surface", ROOT / "scripts/check_naming_surface_contract.py")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def documents():
    return [(ROOT / path).read_text() for path in (
        "api/graphql.md", "api/mcp.md", "deployment/prometheus-semantic-coverage.md")]


def test_adopted_contract():
    CHECKER.validate(*documents())


@pytest.mark.parametrize("old,new", [
    ("type zone_state", "type ZoneState"),
    ("zone_room_temperature: Float", "currentTempC: Float"),
    ("zone_room_humidity: Float", "currentHumidityPct: Float"),
])
def test_removed_graphql_spelling_rejected(old, new):
    docs = documents()
    assert old in docs[0]
    docs[0] = docs[0].replace(old, new)
    with pytest.raises(ValueError):
        CHECKER.validate(*docs)


@pytest.mark.parametrize("family", CHECKER.SETTER_FAMILIES)
def test_missing_setter_family_rejected(family):
    docs = documents()
    key = CHECKER.SETTER_FAMILIES[family][0]
    assert key in docs[1]
    docs[1] = docs[1].replace(key, "removed_setter")
    with pytest.raises(ValueError, match="setter family"):
        CHECKER.validate(*docs)


@pytest.mark.parametrize("name", ["ebus.invoke", "ebus.devices", "ebus_invoke", "ebus_devices"])
def test_removed_tool_not_reissued(name):
    docs = documents()
    docs[1] = docs[1].replace("| ebus_v1_registry_devices_list |", "| " + name + " |")
    with pytest.raises(ValueError):
        CHECKER.validate(*docs)


def test_undocumented_registration_rejected():
    docs = documents()
    _, rows = CHECKER.mcp.documented_rows(docs[1])
    extra = copy.deepcopy(rows[0])
    extra["name"] = "synthetic_undocumented_tool"
    with pytest.raises(ValueError, match="parity"):
        CHECKER.validate(*docs, registration={"schema_version": 1, "tools": rows + [extra]})


def test_changed_constant_unit_rejected():
    docs = documents()
    old = "| `helianthus_semantic_evidence_age` | `gauge` | `connector, dimension, domain, fact_id, pack, unit` | `seconds` |"
    assert old in docs[2]
    docs[2] = docs[2].replace(old, old.replace("`seconds`", "`milliseconds`"))
    with pytest.raises(ValueError):
        CHECKER.validate(*docs)


def test_m2m_unit_has_six_explicit_exclusions():
    assert len(CHECKER.EXCLUSIONS) == 6
    assert all(reason == "shape differs; docs-ebus#1166" for reason in CHECKER.EXCLUSIONS.values())


@pytest.mark.parametrize("field", CHECKER.mcp.FIELDS)
def test_registration_each_identity_and_attribute_rejected(field):
    # name catches tool replacement; surface and registration_profile catch
    # moves between scopes; availability_condition catches enablement changes;
    # implementation_source catches a changed owner binding.
    docs = documents()
    _, rows = CHECKER.mcp.documented_rows(docs[1])
    changed = copy.deepcopy(rows)
    changed[0][field] = "synthetic_changed_" + field
    with pytest.raises(ValueError):
        CHECKER.validate(*docs, registration={"schema_version": 1, "tools": changed})


@pytest.mark.parametrize("adopted,removed", [
    ("current_temp_c", "currentTempC"),
    ("target_temp_c", "targetTempC"),
    ("operating_mode", "operatingMode"),
    ("semantic_snapshot", "semanticSnapshot"),
    ("asset_ids", "assetIds"),
    ("asset_id", "assetId"),
    ("snapshot_id", "snapshotId"),
    ("pack_id", "packId"),
    ("pack_version", "packVersion"),
    ("fact_id", "factId"),
    ("candidate_id", "candidateId"),
    ("item_id", "itemId"),
    ("source_items", "sourceItems"),
    ("unavailable_reason", "unavailableReason"),
    ("zone_update", "zoneUpdate"),
])
def test_removed_member_rejected_in_additional_example(adopted, removed):
    # Each pair catches a production serializer or schema member reverting
    # that one spelling; value selection and native identity stay unchanged.
    docs = documents()
    example = "\n```graphql\ntype synthetic_example { " + adopted + ": String }\n```\n"
    CHECKER.validate(docs[0] + example, *docs[1:])
    with pytest.raises(ValueError, match="GraphQL"):
        CHECKER.validate(docs[0] + example.replace(adopted, removed), *docs[1:])


@pytest.mark.parametrize("old,adopted", CHECKER.OPERATION_NAMES.items())
@pytest.mark.parametrize("index", (0, 1))
def test_operation_each_member_and_type_rejects_removed_spelling(old, adopted, index):
    # Each row catches the corresponding schema member/type or serializer key
    # reverting independently in either the page or the example assertions.
    docs = [(ROOT / name).read_text() for name in (
        "api/semantic-operation-route.md", "tests/semantic_operation_route_contract.json")]
    CHECKER.validate_operation(*docs)
    assert adopted in docs[index]
    docs[index] = docs[index].replace(adopted, old)
    with pytest.raises(ValueError, match="operation"):
        CHECKER.validate_operation(*docs)


@pytest.mark.parametrize("mutation", [None, "tool", "metric"])
def test_offline_parity_branch(tmp_path, mutation):
    # Independent, fixed synthetic candidate inventory; provenance is not published.
    fixture = json.loads((ROOT / "tests/fixtures/naming_surface_inventory.json").read_text())
    if mutation == "tool":
        fixture["tools"][0]["name"] = "synthetic_changed_tool"
    if mutation == "metric":
        fixture["families"][0]["name"] = "synthetic_changed_metric"
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "mcp-tool-inventory.md").write_text(
        "```json\n" + json.dumps({"schema_version": 1, "tools": fixture["tools"]}) + "\n```\n")
    (docs / "metrics-inventory.json").write_text(json.dumps({"families": fixture["families"]}))
    if mutation is None:
        CHECKER.validate_root(ROOT, tmp_path)
    else:
        with pytest.raises(ValueError, match="parity"):
            CHECKER.validate_root(ROOT, tmp_path)


@pytest.mark.parametrize("adopted,removed", [
    ('heating_mode', 'heatingMode'),
    ('energy_category', 'EnergyCategory'),
    ('energy_bucket', 'EnergyBucket'),
    ('REGULATOR', 'regulator'),
    ('FUNCTION_MODULE', 'function_module'),
    ('zones_update', 'zonesUpdate'),
    ('energy_totals_update', 'energyTotalsUpdate'),
    ('system_update', 'systemUpdate'),
    ('circuits_update', 'circuitsUpdate'),
    ('INTERPRETED', 'interpreted'),
    ('GPIO_ONLY', 'gpio_only'),
    ('ABSENT', 'absent'),
    ('CONTROLLER_UNREACHABLE', 'controller_unreachable'),
    ('CONFIGURATION_UNAVAILABLE', 'configuration_unavailable'),
    ('CONFIGURATION_NOT_INTERPRETABLE', 'configuration_not_interpretable'),
    ('SOLAR_ACQUISITION_FAILED', 'solar_acquisition_failed'),
    ('CYLINDER_ACQUISITION_FAILED', 'cylinder_acquisition_failed'),
    ('EVIDENCE_STALE', 'evidence_stale'),
    ('INCOHERENT_ACQUISITION', 'incoherent_acquisition'),
])
def test_remaining_owned_graphql_names(adopted, removed):
    docs = documents()
    assert adopted in docs[0]
    with pytest.raises(ValueError, match="GraphQL"):
        CHECKER.validate(docs[0].replace(adopted, removed), *docs[1:])


def test_dynamic_builder_start_remains_exported():
    page = documents()[0]
    assert "`Start(ctx)` performs an initial build" in page
    assert "`start(ctx)`" not in page


@pytest.mark.parametrize("text", [
    "```graphql\n{ busSummary { status } }\n```",
    "Invoke `modbus.v1.raw.read`.",
    "```graphql\n{ busSummary_extra { status } }\n```",
    "```graphql\ntype Query { busSummaryExtra: String }\n```",
    "```graphql\ntype Query { busSummary2: String }\n```",
])
def test_remaining_page_injection_rejected(tmp_path, text):
    # Root field catches schema reversion; tool catches registration reversion.
    fixture = tmp_path / "tests/fixtures"
    fixture.mkdir(parents=True)
    (fixture / "remaining_page_name_exemptions.json").write_text("[]")
    (tmp_path / "api").mkdir()
    (tmp_path / "api/portal.md").write_text(text)
    with pytest.raises(ValueError, match="remaining API|partial stale"):
        CHECKER.validate_remaining_pages(tmp_path)


@pytest.mark.parametrize("name", ["current_temp_c_source", "current_temp_cSource"])
def test_adopted_graphql_name_extension_allowed(tmp_path, name):
    fixture = tmp_path / "tests/fixtures"
    fixture.mkdir(parents=True)
    (fixture / "remaining_page_name_exemptions.json").write_text("[]")
    (tmp_path / "api").mkdir()
    (tmp_path / "api/portal.md").write_text(
        "```graphql\ntype Query { " + name + ": String }\n```\n")
    CHECKER.validate_remaining_pages(tmp_path)


def test_remaining_exemptions_exist():
    CHECKER.validate_remaining_pages(ROOT)


@pytest.mark.parametrize("opening,closing", [
    ("```json", "```"),
    ("```json response-example", "```"),
    ("```yaml", "```"),
    ("```", "```"),
    ("```graphql", "```"),
    ("```graphql schema-example", "```"),
    ("~~~~graphql schema-example", "~~~~"),
    ("  ````graphql schema-example", "  `````"),
])
def test_documentary_exemption_cannot_move_into_graphql(tmp_path, opening, closing):
    fixture = tmp_path / "tests/fixtures"
    fixture.mkdir(parents=True)
    (fixture / "remaining_page_name_exemptions.json").write_text(json.dumps([{
        "file": "api/graphql.md", "token": "flowsetHcMaxC",
        "context": "flowsetHcMaxC", "count": 1,
        "reason": "Preserved documentary correspondence.",
    }]))
    (tmp_path / "api").mkdir()
    page = tmp_path / "api/graphql.md"
    page.write_text("Documentary correspondence: `flowsetHcMaxC`.\n")
    CHECKER.validate_remaining_pages(tmp_path)
    body = ('type Query { flowsetHcMaxC: Float }' if "graphql" in opening
            else '{"flowsetHcMaxC": 42}')
    page.write_text(opening + "\n" + body + "\n" + closing + "\n")
    with pytest.raises(ValueError, match="remaining API spelling or stale naming exemption"):
        CHECKER.validate_remaining_pages(tmp_path)


@pytest.mark.parametrize("value", [
    '"busSummaryExtra"',
    '"escaped \\" busSummaryExtra # still string"',
    '"""block busSummaryExtra\nmore data"""',
])
def test_stale_prefix_in_graphql_strings_allowed(tmp_path, value):
    fixture = tmp_path / "tests/fixtures"
    fixture.mkdir(parents=True)
    (fixture / "remaining_page_name_exemptions.json").write_text("[]")
    page = tmp_path / "example.md"
    page.write_text('```graphql schema-example\n{ search(value: ' + value + ') }\n```\n')
    CHECKER.validate_remaining_pages(tmp_path)
    page.write_text('```graphql schema-example\n{ busSummaryExtra(value: ' + value + ') }\n```\n')
    with pytest.raises(ValueError, match="partial stale"):
        CHECKER.validate_remaining_pages(tmp_path)


@pytest.mark.parametrize("body", [
    '{ search(value: "busSummary") }',
    '{ search(value: "escaped \\" busSummary") }',
    '"""busSummary\nblock description"""\ntype Query { search: String }',
    '{ search } # busSummary',
    '{ search(value: "busSummary") } # flowsetHcMaxC',
])
def test_exact_stale_graphql_data_ignored_but_names_checked(tmp_path, body):
    fixture = tmp_path / "tests/fixtures"
    fixture.mkdir(parents=True)
    (fixture / "remaining_page_name_exemptions.json").write_text("[]")
    page = tmp_path / "example.md"
    page.write_text("```graphql schema-example\n" + body + "\n```\n")
    CHECKER.validate_remaining_pages(tmp_path)
    page.write_text("```graphql schema-example\n" + body + "\n{ busSummary }\n```\n")
    with pytest.raises(ValueError, match="remaining API"):
        CHECKER.validate_remaining_pages(tmp_path)


def test_exact_stale_prose_still_checked_beside_graphql_data(tmp_path):
    fixture = tmp_path / "tests/fixtures"
    fixture.mkdir(parents=True)
    (fixture / "remaining_page_name_exemptions.json").write_text("[]")
    (tmp_path / "example.md").write_text(
        '```graphql\n{ search(value: "busSummary") }\n```\nbusSummary\n')
    with pytest.raises(ValueError, match="remaining API"):
        CHECKER.validate_remaining_pages(tmp_path)
