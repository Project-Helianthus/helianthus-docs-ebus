"""Tests for the controller's structural relation and identity candidates."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_structural_relation_candidates",
    ROOT / "scripts" / "validate_structural_relation_candidates.py",
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

ZONE_ROOM = "SRC-SD05-zone-room-unit"
ZONE_CIRCUIT = "SRC-SD06-zone-to-circuit"
ZONE_FALLBACK = "SRC-SD07-zone-to-circuit-fallback"
MANAGING = "SRC-SD09-circuit-managing-module"
CONNECTED = "SRC-SD10-connected-device-slot"
MODULE_SLOT = "SRI-functional-module-slot"
DECISIONS = VALIDATOR.DECISIONS_PAGE.as_posix()
MODULES = VALIDATOR.MODULES_PAGE.as_posix()
DISCOVERY = VALIDATOR.DISCOVERY_PAGE.as_posix()
REGISTER_MAP = VALIDATOR.REGISTER_MAP.as_posix()


def load_fixture() -> dict:
    return VALIDATOR.load_json(ROOT / VALIDATOR.FIXTURE)


def load_pages() -> dict:
    return VALIDATOR.read_pages(ROOT)


def row(document: dict, row_id: str) -> dict:
    for section in ("attachments", "relayed_identity"):
        for item in document[section]:
            if item["id"] == row_id:
                return item
    raise AssertionError(f"fixture row {row_id} is missing")


def errors_after(mutate=None, mutate_pages=None) -> list:
    document, pages = copy.deepcopy(load_fixture()), dict(load_pages())
    if mutate is not None:
        mutate(document)
    if mutate_pages is not None:
        mutate_pages(pages)
    return VALIDATOR.validate(document, pages)


def test_published_fixture_and_pages_validate() -> None:
    assert VALIDATOR.validate(load_fixture(), load_pages()) == []
    assert VALIDATOR.main([str(ROOT)]) == 0


def test_duplicate_json_keys_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema": "a", "schema": "b"}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        VALIDATOR.load_json(path)


@pytest.mark.parametrize("key", sorted(VALIDATOR.TOP_KEYS))
def test_every_top_level_key_is_required(key: str) -> None:
    assert errors_after(lambda document: document.pop(key))


@pytest.mark.parametrize(
    ("key", "value"),
    [("schema", "helianthus.docs.ebus.structural-relation-candidates/v2"),
     ("decision_catalog", "architecture/functional-modules.md"),
     ("attachments", []), ("relayed_identity", [])],
)
def test_top_level_values_are_pinned(key: str, value: object) -> None:
    assert errors_after(lambda document: document.__setitem__(key, value))


@pytest.mark.parametrize("key", sorted(VALIDATOR.ROW_KEYS))
def test_every_attachment_key_is_required(key: str) -> None:
    assert errors_after(lambda document: row(document, MANAGING).pop(key))


def test_attachment_rows_reject_any_further_key() -> None:
    assert errors_after(lambda document: row(document, MANAGING).__setitem__("quantity", "flow"))
    assert errors_after(
        lambda document: row(document, MANAGING).__setitem__("relation_definition", "controls")
    )


ATTACHMENT_FIELD_MUTATIONS = [
    ("id", lambda item: item.__setitem__("id", "SD09")),
    ("decisions", lambda item: item.__setitem__("decisions", ["SD-11"])),
    ("decisions", lambda item: item.__setitem__("decisions", ["SD-09", "SD-09"])),
    ("attachment", lambda item: item.__setitem__("attachment", "Circuit Owner")),
    ("published_field", lambda item: item.__setitem__("published_field", "circuits[].owner")),
    ("from.kind", lambda item: item["from"].__setitem__("kind", "heating_circuit")),
    ("from.resolution", lambda item: item["from"].__setitem__("resolution", "guessed")),
    ("from.identity_evidence", lambda item: item["from"].__setitem__("identity_evidence", [])),
    ("to.selector", lambda item: item["to"]["identity_evidence"][0].__setitem__("selector", "0x26")),
    ("to.role", lambda item: item["to"]["identity_evidence"][0].__setitem__("role", "serial")),
    ("to.classification",
     lambda item: item["to"]["identity_evidence"][0].__setitem__("classification", "native_token")),
    ("to.duplicate", lambda item: item["to"]["identity_evidence"].append(
        copy.deepcopy(item["to"]["identity_evidence"][0]))),
    ("evidence_grade", lambda item: item.__setitem__("evidence_grade", "PROVEN")),
    ("validity_scope", lambda item: item.__setitem__("validity_scope", ["SITE"])),
    ("validity_scope", lambda item: item.__setitem__("validity_scope", [])),
    ("disposition", lambda item: item.__setitem__("disposition", "configured")),
    ("native_statements.selector",
     lambda item: item["native_statements"][0].__setitem__("selector", "RR=0x0036")),
    ("native_statements.source",
     lambda item: item["native_statements"][0].__setitem__("source", "README.md")),
    ("native_statements.reading", lambda item: item["native_statements"][0].__setitem__("reading", " ")),
    ("native_statements.scope", lambda item: item["native_statements"][0].__setitem__("scope", "SITE")),
    ("native_statements", lambda item: item.__setitem__("native_statements", [])),
    ("reason", lambda item: item.__setitem__("reason", "")),
    ("pending_review", lambda item: item.__setitem__("pending_review", "review it")),
]


@pytest.mark.parametrize(("field", "mutation"), ATTACHMENT_FIELD_MUTATIONS,
                         ids=[field for field, _ in ATTACHMENT_FIELD_MUTATIONS])
def test_every_attachment_field_is_checked(field: str, mutation) -> None:
    assert errors_after(lambda document: mutation(row(document, MANAGING))), field


@pytest.mark.parametrize("decision", VALIDATOR.REQUIRED_DECISIONS)
def test_every_named_decision_is_covered(decision: str) -> None:
    def drop(document: dict) -> None:
        kept = []
        for item in document["attachments"]:
            item["decisions"] = [name for name in item["decisions"] if name != decision]
            if item["decisions"]:
                kept.append(item)
        document["attachments"] = kept

    assert any(f"no attachment row for {decision}" in error for error in errors_after(drop))


def test_row_identifiers_are_unique() -> None:
    assert errors_after(lambda document: row(document, MANAGING).__setitem__("id", ZONE_ROOM))


def test_relayed_identity_identifiers_are_unique() -> None:
    def clash(document: dict) -> None:
        row(document, MODULE_SLOT)["id"] = "SRI-heat-source-slots"

    assert any("repeat" in error for error in errors_after(clash))


def test_zone_to_circuit_stays_unresolved_with_both_native_statements() -> None:
    selectors = {item["selector"] for item in row(load_fixture(), ZONE_CIRCUIT)["native_statements"]}
    assert VALIDATOR.ZONE_CIRCUIT_SELECTORS <= selectors
    assert errors_after(lambda document: row(document, ZONE_CIRCUIT).__setitem__(
        "disposition", "relation_candidate"))
    assert errors_after(lambda document: row(document, ZONE_FALLBACK).__setitem__(
        "disposition", "relation_candidate"))
    assert errors_after(lambda document: row(document, ZONE_CIRCUIT).__setitem__(
        "evidence_grade", "Proven"))
    assert errors_after(lambda document: row(document, ZONE_CIRCUIT).__setitem__(
        "pending_review", None))
    for selector in VALIDATOR.ZONE_CIRCUIT_SELECTORS:
        def drop(document: dict, selector: str = selector) -> None:
            item = row(document, ZONE_CIRCUIT)
            item["native_statements"] = [
                statement for statement in item["native_statements"] if statement["selector"] != selector
            ]
            item["native_statements"].append(copy.deepcopy(row(document, MANAGING)["native_statements"][0]))

        assert errors_after(drop), selector


def test_relation_candidates_need_native_scope_and_evidence() -> None:
    assert errors_after(lambda document: row(document, CONNECTED).__setitem__(
        "validity_scope", ["PROTOCOL", "GATEWAY_POLICY"]))
    assert errors_after(lambda document: row(document, CONNECTED).__setitem__("evidence_grade", "Unknown"))
    assert errors_after(lambda document: row(document, CONNECTED).__setitem__("native_statements", []))


@pytest.mark.parametrize("key", sorted(VALIDATOR.IDENTITY_KEYS))
def test_every_relayed_identity_key_is_required(key: str) -> None:
    assert errors_after(lambda document: row(document, MODULE_SLOT).pop(key))


IDENTITY_FIELD_MUTATIONS = [
    ("id", lambda item: item.__setitem__("id", "SRC-SD10-module")),
    ("decisions", lambda item: item.__setitem__("decisions", ["SD-12"])),
    ("groups", lambda item: item.__setitem__("groups", ["0C"])),
    ("relaying_end.kind", lambda item: item["relaying_end"].__setitem__("kind", "gateway")),
    ("slot_view.kind", lambda item: item["slot_view"].__setitem__("kind", "direct_bus_entry")),
    ("slot_view.identity_evidence", lambda item: item["slot_view"].__setitem__("identity_evidence", [])),
    ("direct_view.kind", lambda item: item["direct_view"].__setitem__("kind", "device_slot")),
    ("direct_view.status", lambda item: item["direct_view"].__setitem__("status", "same")),
    ("direct_view.classification", lambda item: item["direct_view"]["identity_evidence"][0].__setitem__(
        "classification", "native_token")),
    ("shared_anchor_key_source", lambda item: item.__setitem__("shared_anchor_key_source", "bus_address")),
    ("disposition", lambda item: item.__setitem__("disposition", "merged")),
    ("reason", lambda item: item.__setitem__("reason", "")),
]


@pytest.mark.parametrize(("field", "mutation"), IDENTITY_FIELD_MUTATIONS,
                         ids=[field for field, _ in IDENTITY_FIELD_MUTATIONS])
def test_every_relayed_identity_field_is_checked(field: str, mutation) -> None:
    assert errors_after(lambda document: mutation(row(document, MODULE_SLOT))), field


@pytest.mark.parametrize(
    ("source", "disposition"),
    [("none", "one_resource"), ("native_position", "one_resource"),
     ("native_token", "two_views_unresolved"), ("operator_label", "two_views_unresolved")],
)
def test_shared_anchor_key_source_decides_the_disposition(source: str, disposition: str) -> None:
    def mutate(document: dict) -> None:
        item = row(document, MODULE_SLOT)
        item["shared_anchor_key_source"], item["disposition"] = source, disposition

    assert errors_after(mutate)


def test_published_slot_views_share_no_anchor_key() -> None:
    for item in load_fixture()["relayed_identity"]:
        assert item["shared_anchor_key_source"] == "none"
        assert item["disposition"] == "two_views_unresolved"


def test_relayed_identity_covers_every_device_slot_group_once() -> None:
    assert VALIDATOR.slot_groups(load_pages()) == sorted(
        ["0x01", "0x02", "0x09", "0x0A", "0x0C", "0x0E", "0x0F"]
    )
    assert errors_after(lambda document: row(document, MODULE_SLOT)["groups"].append("0x09"))
    assert errors_after(lambda document: row(document, MODULE_SLOT).__setitem__("groups", ["0x0B"]))


@pytest.mark.parametrize("page", [DECISIONS, MODULES, DISCOVERY])
def test_each_page_references_the_fixture(page: str) -> None:
    def mutate(pages: dict) -> None:
        pages[page] = pages[page].replace(VALIDATOR.FIXTURE_LINK, "fixtures/elsewhere.json")

    assert errors_after(mutate_pages=mutate)


@pytest.mark.parametrize("sentence", VALIDATOR.RETIRED_SENTENCES)
def test_parenting_is_not_handed_back_to_consumers(sentence: str) -> None:
    def mutate(pages: dict) -> None:
        pages[DECISIONS] += f"\n{sentence}\n"

    assert errors_after(mutate_pages=mutate)


@pytest.mark.parametrize("decision", ["SD-10", "SD-15"])
def test_sd10_and_sd15_hand_parenting_to_the_common_model(decision: str) -> None:
    def mutate(pages: dict) -> None:
        head, tail = pages[DECISIONS].split(f"## B524-{decision} ", 1)
        section, rest = tail.split("\n## ", 1)
        pages[DECISIONS] = head + f"## B524-{decision} " + section.replace(
            VALIDATOR.COMMON_MODEL, "consumer") + "\n## " + rest

    assert errors_after(mutate_pages=mutate)


@pytest.mark.parametrize("name", ["zone_room_sensor_binding_mode", "zone_circuit_assignment"])
def test_both_native_zone_statements_exist_in_the_register_map(name: str) -> None:
    def mutate(pages: dict) -> None:
        pages[REGISTER_MAP] = pages[REGISTER_MAP].replace(f" | {name} |", " | renamed |")

    assert errors_after(mutate_pages=mutate)


def test_unreadable_device_slot_groups_fail_closed() -> None:
    def mutate(pages: dict) -> None:
        pages[DECISIONS] = pages[DECISIONS].replace("/0x0E/0x0F RR=0x0001`", "/0x0E/0x0F`")

    assert any("not readable" in error for error in errors_after(mutate_pages=mutate))


@pytest.mark.parametrize("row_id", [ZONE_ROOM, ZONE_CIRCUIT, MANAGING, MODULE_SLOT, "SRC-FM-second-family-slot"])
def test_each_row_is_cited_in_its_primary_decision(row_id: str) -> None:
    def mutate(pages: dict) -> None:
        for page in (DECISIONS, MODULES):
            pages[page] = pages[page].replace(f"`{row_id}`", "`SRC-elsewhere`")

    assert any(f"{row_id}: not cited" in error for error in errors_after(mutate_pages=mutate))


@pytest.mark.parametrize("row_id", sorted(VALIDATOR.REQUIRED_ROW_IDS))
def test_every_catalogued_attachment_row_is_required(row_id: str) -> None:
    def mutate(document: dict) -> None:
        document["attachments"] = [item for item in document["attachments"] if item["id"] != row_id]

    assert any(row_id in error for error in errors_after(mutate))


def test_swapped_identity_groups_are_rejected() -> None:
    def mutate(document: dict) -> None:
        first, second = row(document, "SRI-functional-module-slot"), row(document, "SRI-room-unit-slots")
        first["groups"], second["groups"] = second["groups"], first["groups"]

    assert any(".groups" in error for error in errors_after(mutate))


def test_statement_reassigned_to_an_unrelated_source_is_rejected() -> None:
    def mutate(document: dict) -> None:
        row(document, MANAGING)["native_statements"][0]["source"] = "functional_modules"
        row(document, MANAGING)["native_statements"][0]["selector"] = "OP=0x02 GG=0x00 RR=0x0036"

    def mutate_pages(pages: dict) -> None:
        pages[MODULES] = pages[MODULES].replace("0x0036", "")

    assert any("does not contain" in error for error in errors_after(mutate, mutate_pages))
