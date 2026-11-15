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


@pytest.mark.parametrize(
    ("row_id", "disposition"),
    [(CONNECTED, "absent"), ("SRC-SD15-controller-zone", "configuration_only"),
     (ZONE_ROOM, "configuration_only"), (MANAGING, "absent"),
     ("SRC-SD10-inventory-device-slot", "configuration_only"),
     ("SRC-FM-second-family-slot", "configuration_only")],
)
def test_each_required_row_keeps_its_catalogued_disposition(row_id: str, disposition: str) -> None:
    def mutate(document: dict) -> None:
        item = row(document, row_id)
        item["disposition"] = disposition
        if not item["native_statements"]:
            item["native_statements"] = copy.deepcopy(row(document, MANAGING)["native_statements"])

    assert any(f"{row_id}.disposition" in error for error in errors_after(mutate))


def test_published_rows_match_the_pinned_dispositions() -> None:
    for item in load_fixture()["attachments"]:
        assert item["disposition"] == VALIDATOR.REQUIRED_ROWS[item["id"]][0], item["id"]


def test_an_uncatalogued_attachment_row_is_rejected() -> None:
    def mutate(document: dict) -> None:
        extra = copy.deepcopy(row(document, MANAGING))
        extra["id"] = "SRC-SD09-second-managing-module"
        document["attachments"].append(extra)

    assert any("not a catalogued attachment row" in error for error in errors_after(mutate))


def retarget(evidence: list, old: str, new: str) -> None:
    for item in evidence:
        item["selector"] = item["selector"].replace(old, new)


@pytest.mark.parametrize(
    ("row_id", "end", "old", "new"),
    [(ZONE_ROOM, "from", "GG=0x03", "GG=0x04"), (ZONE_ROOM, "to", "GG=0x09/0x0A", "GG=0x0E/0x0F"),
     (ZONE_CIRCUIT, "to", "GG=0x02", "GG=0x05"), (MANAGING, "to", "GG=0x0C", "GG=0x0B"),
     ("SRC-SD15-module-cylinder", "to", "GG=0x05", "GG=0x03"),
     ("SRC-SD15-controller-zone", "from", "PB=0xB5 SB=0x24", "PB=0xB5 SB=0x09"),
     ("SRC-FM-second-family-status", "to", "RR=0x0067", "RR=0x0069")],
)
def test_endpoint_selectors_are_bound_to_each_row(row_id: str, end: str, old: str, new: str) -> None:
    def mutate(document: dict) -> None:
        retarget(row(document, row_id)[end]["identity_evidence"], old, new)

    assert any(f"{row_id}.{end}" in error for error in errors_after(mutate))


def test_endpoint_kind_and_role_are_bound_to_each_row() -> None:
    def kind(document: dict) -> None:
        row(document, ZONE_ROOM)["to"]["kind"] = "functional_module"

    def role(document: dict) -> None:
        row(document, ZONE_ROOM)["from"]["identity_evidence"][1].update(role="assignment_value")

    assert any(f"{ZONE_ROOM}.to" in error for error in errors_after(kind))
    assert any(f"{ZONE_ROOM}.from" in error for error in errors_after(role))


@pytest.mark.parametrize(
    ("view", "old", "new"),
    [("relaying_end", "PB=0xB5 SB=0x24", "PB=0xB5 SB=0x09"), ("direct_view", "PB=0x07 SB=0x04", "PB=0x07 SB=0x05")],
)
def test_relayed_identity_ends_are_bound_to_their_native_sources(view: str, old: str, new: str) -> None:
    def mutate(document: dict) -> None:
        retarget(row(document, MODULE_SLOT)[view]["identity_evidence"], old, new)

    assert any(f"{MODULE_SLOT}.{view}" in error for error in errors_after(mutate))


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


@pytest.mark.parametrize(
    ("row_id", "field"),
    [("SRC-SD15-controller-zone", "circuits[]"), (ZONE_ROOM, "zones[]"),
     (MANAGING, None), ("SRC-FM-second-family-slot", "radioDevices[]")],
)
def test_each_row_keeps_its_catalogued_published_field(row_id: str, field) -> None:
    def mutate(document: dict) -> None:
        row(document, row_id)["published_field"] = field

    assert any(f"{row_id}.published_field" in error for error in errors_after(mutate))


@pytest.mark.parametrize(
    ("row_id", "end", "resolution"),
    [("SRC-SD15-controller-zone", "to", "gateway_policy"), (ZONE_CIRCUIT, "to", "native"),
     (ZONE_ROOM, "to", "unresolved"), ("SRC-SD15-module-cylinder", "from", "native"),
     ("SRC-FM-second-family-slot", "from", "gateway_policy")],
)
def test_each_endpoint_keeps_its_catalogued_resolution(row_id: str, end: str, resolution: str) -> None:
    def mutate(document: dict) -> None:
        row(document, row_id)[end]["resolution"] = resolution

    assert any(f"{row_id}.{end}.resolution" in error for error in errors_after(mutate))


def test_relaying_end_keeps_its_catalogued_resolution() -> None:
    def mutate(document: dict) -> None:
        row(document, MODULE_SLOT)["relaying_end"]["resolution"] = "gateway_policy"

    assert any(f"{MODULE_SLOT}.relaying_end.resolution" in error for error in errors_after(mutate))


@pytest.mark.parametrize(
    ("row_id", "grade"),
    [("SRC-SD15-controller-zone", "Hypothesis"), (MANAGING, "Hypothesis"),
     ("SRC-SD10-inventory-device-slot", "Proven"), (ZONE_FALLBACK, "Hypothesis")],
)
def test_each_row_keeps_its_catalogued_evidence_grade(row_id: str, grade: str) -> None:
    def mutate(document: dict) -> None:
        row(document, row_id)["evidence_grade"] = grade

    assert any(f"{row_id}.evidence_grade" in error for error in errors_after(mutate))


@pytest.mark.parametrize(
    ("row_id", "scope"),
    [("SRC-SD15-controller-zone", ["LAB"]), (MANAGING, ["PROTOCOL"]),
     (MANAGING, ["LAB"]), ("SRC-SD15-module-solar-circuit", ["PROTOCOL"])],
)
def test_each_row_keeps_its_catalogued_validity_scope(row_id: str, scope: list) -> None:
    def mutate(document: dict) -> None:
        row(document, row_id)["validity_scope"] = scope

    assert any(f"{row_id}.validity_scope" in error for error in errors_after(mutate))


def test_catalogued_scope_order_is_not_significant() -> None:
    assert errors_after(lambda document: row(document, MANAGING)["validity_scope"].reverse()) == []


def test_published_rows_match_the_pinned_facts() -> None:
    document = load_fixture()
    for item in document["attachments"]:
        field, source, target, grade, scopes = VALIDATOR.REQUIRED_ROW_FACTS[item["id"]]
        assert (item["published_field"], item["from"]["resolution"], item["to"]["resolution"],
                item["evidence_grade"], sorted(item["validity_scope"])) == (
            field, source, target, grade, sorted(scopes)), item["id"]
    assert {item["id"] for item in document["attachments"]} == set(VALIDATOR.REQUIRED_ROW_FACTS)
    for item in document["relayed_identity"]:
        groups, status = VALIDATOR.REQUIRED_IDENTITY[item["id"]]
        assert (sorted(item["groups"]), item["direct_view"]["status"]) == (sorted(groups), status)
    assert {item["id"] for item in document["relayed_identity"]} == set(VALIDATOR.REQUIRED_IDENTITY)


@pytest.mark.parametrize("row_id", sorted(VALIDATOR.REQUIRED_IDENTITY))
def test_every_catalogued_identity_row_is_required(row_id: str) -> None:
    def mutate(document: dict) -> None:
        document["relayed_identity"] = [item for item in document["relayed_identity"] if item["id"] != row_id]

    assert any(row_id in error for error in errors_after(mutate))


def test_repartitioned_identity_groups_are_rejected() -> None:
    def mutate(document: dict) -> None:
        document["relayed_identity"] = [
            item for item in document["relayed_identity"] if item["id"] != MODULE_SLOT
        ]
        heat = row(document, "SRI-heat-source-slots")
        heat["groups"].append("0x0C")
        retarget(heat["slot_view"]["identity_evidence"], "GG=0x01/0x02", "GG=0x01/0x02/0x0C")
        heat["decisions"].append("functional-modules")

    errors = errors_after(mutate)
    assert any(f"{MODULE_SLOT} is missing" in error for error in errors)
    assert any("SRI-heat-source-slots.groups" in error for error in errors)


def test_an_uncatalogued_identity_row_is_rejected() -> None:
    def mutate(document: dict) -> None:
        row(document, "SRI-uncharacterized-slots")["id"] = "SRI-other-slots"

    assert any("not a catalogued relayed-identity row" in error for error in errors_after(mutate))


@pytest.mark.parametrize(
    ("row_id", "status"),
    [(MODULE_SLOT, "not_established"), ("SRI-heat-source-slots", "correlated"),
     ("SRI-room-unit-slots", "correlated")],
)
def test_each_identity_row_keeps_its_direct_view_status(row_id: str, status: str) -> None:
    def mutate(document: dict) -> None:
        row(document, row_id)["direct_view"]["status"] = status

    assert any(f"{row_id}.direct_view.status" in error for error in errors_after(mutate))
