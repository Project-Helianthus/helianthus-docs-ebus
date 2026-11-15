import copy
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/platform/manifests/promoted-semantic-consumers-v1.json"
REGISTRY = ROOT / "docs/platform/schemas/leaf-promotion-captured-multi-leaf-registry-v1.json"

ACCEPTED_BASES = ("operator_declaration", "shared_native_anchor_key")
UNRESOLVED = "unresolved"
BASIS_MEMBERS = {
    "operator_declaration": {"class", "parent", "slot"},
    "shared_native_anchor_key": {"class", "scheme", "issuer", "key"},
    UNRESOLVED: {"class", "reason"},
}
REQUIRED_NONEMPTY = {
    "operator_declaration": ("parent", "slot"),
    "shared_native_anchor_key": ("scheme", "key"),
    UNRESOLVED: ("reason",),
}
MERGE_BY_BASIS = {
    "operator_declaration": "candidates_of_one_resource",
    "shared_native_anchor_key": "candidates_of_one_resource",
    UNRESOLVED: "not_merged",
}
PROTOCOLS = {"ebus", "eebus"}
MAPPING_MEMBERS = {
    "target",
    "resource_kind",
    "resource_kind_reason",
    "candidates",
    "identity_basis",
    "merge",
}
CANDIDATE_MEMBERS = {"protocol", "native_resource", "provenance"}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _target_of(graphql_path: str) -> str:
    if graphql_path.startswith("zones["):
        return graphql_path[: graphql_path.index("]") + 1]
    return graphql_path.split(".", 1)[0]


def validate_identity_basis(basis: object) -> str:
    if not isinstance(basis, dict) or "class" not in basis:
        raise ValueError("identity basis is not recorded")
    basis_class = basis["class"]
    if basis_class not in BASIS_MEMBERS:
        raise ValueError(f"identity basis {basis_class!r} is not an accepted basis")
    if set(basis) != BASIS_MEMBERS[basis_class]:
        raise ValueError(f"identity basis {basis_class!r} has members {sorted(basis)}")
    for member in REQUIRED_NONEMPTY[basis_class]:
        value = basis[member]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"identity basis {basis_class!r} lacks {member}")
    if basis_class == "shared_native_anchor_key" and not isinstance(basis["issuer"], str):
        raise ValueError("shared native anchor key issuer must be a code or empty text")
    return basis_class


def _validate_resource_kind(kind: object, reason: object) -> None:
    if kind is None:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("an undecided resource kind states its reason")
    elif not (isinstance(kind, str) and kind.startswith("resource.")) or reason is not None:
        raise ValueError(f"resource kind {kind!r} is not a common kind identifier")


def _validate_candidate(candidate: dict) -> None:
    if set(candidate) != CANDIDATE_MEMBERS:
        raise ValueError(f"candidate members {sorted(candidate)}")
    if candidate["protocol"] not in PROTOCOLS:
        raise ValueError(f"candidate protocol {candidate['protocol']!r}")
    if not candidate["native_resource"].strip():
        raise ValueError("candidate names no native resource")
    provenance = candidate["provenance"]
    recorded = isinstance(provenance, dict) and {"repository", "document"} <= set(provenance)
    if not recorded or not all(
        isinstance(value, str) and value.strip() for value in provenance.values()
    ):
        raise ValueError("candidate provenance is not recorded")


def validate_resource_mapping(mapping: dict) -> str:
    if set(mapping) != MAPPING_MEMBERS:
        raise ValueError(f"resource mapping members {sorted(mapping)}")
    basis_class = validate_identity_basis(mapping["identity_basis"])
    if mapping["merge"] != MERGE_BY_BASIS[basis_class]:
        raise ValueError(
            f"merge {mapping['merge']!r} does not follow identity basis {basis_class!r}"
        )
    _validate_resource_kind(mapping["resource_kind"], mapping["resource_kind_reason"])
    candidates = mapping["candidates"]
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("resource mapping has no candidates")
    for candidate in candidates:
        _validate_candidate(candidate)
    if {candidate["protocol"] for candidate in candidates} != PROTOCOLS:
        raise ValueError("resource mapping lacks a candidate from each protocol")
    return basis_class


def validate_manifest(manifest: dict) -> None:
    mappings = manifest.get("resources", [])
    targets = [mapping["target"] for mapping in mappings]
    if targets != sorted(set(targets)):
        raise ValueError("resource mappings are not unique and in target order")
    basis_by_target = {
        mapping["target"]: validate_resource_mapping(mapping) for mapping in mappings
    }
    for leaf in manifest["leaves"]:
        target = _target_of(leaf["graphql_path"])
        if target not in basis_by_target:
            raise ValueError(f"leaf {leaf['semantic_path']} has no resource mapping")
        if leaf.get("identity_basis") != basis_by_target[target]:
            raise ValueError(
                f"leaf {leaf['semantic_path']} does not carry the identity basis of {target}"
            )
    used = {_target_of(leaf["graphql_path"]) for leaf in manifest["leaves"]}
    if used != set(basis_by_target):
        raise ValueError("a resource mapping has no leaf")


def test_m9_manifest_matches_exact_locked_leaf_catalog() -> None:
    manifest = _load(MANIFEST)
    registry = _load(REGISTRY)

    leaves = manifest["leaves"]
    assert manifest["contract"] == "helianthus.platform.promoted-semantic-consumers.v1"
    assert manifest["projection_policy"] == "FILL_MISSING_ONLY"
    assert manifest["projection_policy_target"] == "graphql_roots"
    assert manifest["projection_policy_scope"] == "candidates_of_one_resource"
    assert len(leaves) == 18
    assert [leaf["semantic_path"] for leaf in leaves] == sorted(
        leaf["semantic_path"] for leaf in leaves
    )

    catalog = [row for row in registry["candidate_catalog"] if row["semantic_path"]]
    assert {leaf["semantic_path"] for leaf in leaves} == {
        row["semantic_path"] for row in catalog
    }

    kind_by_comparator = {
        "NUMERIC_DECLARED_GRANULARITY": "NUMERIC",
        "ENUM_EXACT_MAPPING": "ENUM",
        "BOOLEAN_EXACT_MAPPING": "BOOLEAN",
        "STRING_EXACT_STABILITY": "STRING",
    }
    by_path = {leaf["semantic_path"]: leaf for leaf in leaves}
    for row in catalog:
        leaf = by_path[row["semantic_path"]]
        assert leaf["value_kind"] == kind_by_comparator[row["comparator_class"]]
        assert leaf["unit"] == row["eebus_source"]["unit"]
        expected_class = (
            "EEBUS_NATIVE"
            if row["protocol_eligibility"] == "EEBUS_NATIVE"
            else "CROSS_PROTOCOL_EQUIVALENCE"
        )
        assert leaf["producer_class"] == expected_class


def test_m9_manifest_public_surface_is_semantic_only() -> None:
    manifest = _load(MANIFEST)
    forbidden = set(manifest["forbidden_public_fields"])
    assert "candidate_ref" in forbidden
    assert "remote_ski" in forbidden
    assert "private_key" in forbidden

    for leaf in manifest["leaves"]:
        expected = {
            "semantic_path",
            "value_kind",
            "unit",
            "graphql_path",
            "producer_class",
            "identity_basis",
        }
        if leaf["semantic_path"].endswith("/name"):
            expected.add("public_transform")
            assert leaf["public_transform"] == "STABLE_ZONE_PSEUDONYM"
        assert set(leaf) == expected
        assert not (set(leaf) & forbidden)


def test_m9_every_target_maps_to_one_resource_with_recorded_identity_basis() -> None:
    manifest = _load(MANIFEST)
    validate_manifest(manifest)

    mappings = {mapping["target"]: mapping for mapping in manifest.get("resources", [])}
    assert sorted(mappings) == ["dhw", "system", "zones[id=zone-1]", "zones[id=zone-2]"]
    assert manifest["identity_bases"] == {
        "accepted": list(ACCEPTED_BASES),
        "unresolved": UNRESOLVED,
    }
    assert mappings["zones[id=zone-1]"]["resource_kind"] == "resource.zone"
    assert mappings["zones[id=zone-2]"]["resource_kind"] == "resource.zone"
    assert mappings["system"]["resource_kind"] == "resource.thermal_system"
    assert mappings["dhw"]["resource_kind"] is None

    # No published evidence holds a shared native anchor key for the two views,
    # and an operator declaration belongs to one installation, so every
    # mapping in this manifest is unresolved and nothing is merged.
    for mapping in mappings.values():
        assert mapping["identity_basis"]["class"] == UNRESOLVED
        assert mapping["merge"] == "not_merged"


def test_m9_zone_leaves_carry_the_basis_of_their_zone_mapping() -> None:
    manifest = _load(MANIFEST)
    mappings = {mapping["target"]: mapping for mapping in manifest["resources"]}
    zone_leaves = [
        leaf for leaf in manifest["leaves"] if leaf["semantic_path"].startswith("/zones/")
    ]
    assert len(zone_leaves) == 10
    for leaf in zone_leaves:
        target = _target_of(leaf["graphql_path"])
        assert target in {"zones[id=zone-1]", "zones[id=zone-2]"}
        assert leaf["identity_basis"] == mappings[target]["identity_basis"]["class"]

    for graphql_id in ("zone-1", "zone-2"):
        labels = [
            leaf
            for leaf in zone_leaves
            if leaf["graphql_path"] == f"zones[id={graphql_id}].config.source_label"
        ]
        assert len(labels) == 1
        assert labels[0]["public_transform"] == "STABLE_ZONE_PSEUDONYM"
        assert all(leaf["graphql_path"] != f"zones[id={graphql_id}].name" for leaf in zone_leaves)


def _zone_mapping() -> dict:
    manifest = _load(MANIFEST)
    return copy.deepcopy(
        next(m for m in manifest["resources"] if m["target"] == "zones[id=zone-1]")
    )


def test_m9_ordinal_zone_join_without_basis_is_rejected() -> None:
    manifest = _load(MANIFEST)
    ordinal_only = copy.deepcopy(manifest)
    for leaf in ordinal_only["leaves"]:
        leaf.pop("identity_basis")
    with pytest.raises(ValueError, match="does not carry the identity basis"):
        validate_manifest(ordinal_only)

    unmapped = copy.deepcopy(manifest)
    unmapped["resources"] = [
        m for m in unmapped["resources"] if m["target"] != "zones[id=zone-2]"
    ]
    with pytest.raises(ValueError, match="has no resource mapping"):
        validate_manifest(unmapped)

    for basis in (None, {}, {"class": "ordinal"}, {"class": "slot_label"},
                  {"class": "name_similarity"}, {"class": "bus_address"}):
        mapping = _zone_mapping()
        mapping["identity_basis"] = basis
        with pytest.raises(ValueError, match="identity basis"):
            validate_resource_mapping(mapping)


@pytest.mark.parametrize(
    "basis",
    [
        {"class": "operator_declaration", "parent": "thermal system A", "slot": "zone east"},
        {"class": "shared_native_anchor_key", "scheme": "scheme.synthetic", "issuer": "", "key": "key-synthetic-1"},
        {"class": "shared_native_anchor_key", "scheme": "scheme.synthetic", "issuer": "X1", "key": "key-synthetic-1"},
    ],
)
def test_m9_accepted_basis_merges_candidates_of_one_resource(basis: dict) -> None:
    mapping = _zone_mapping()
    mapping["identity_basis"] = basis
    mapping["merge"] = "candidates_of_one_resource"
    assert validate_resource_mapping(mapping) == basis["class"]

    mapping["merge"] = "not_merged"
    with pytest.raises(ValueError, match="does not follow identity basis"):
        validate_resource_mapping(mapping)


@pytest.mark.parametrize(
    "basis_class,member",
    [
        ("operator_declaration", "parent"),
        ("operator_declaration", "slot"),
        ("shared_native_anchor_key", "scheme"),
        ("shared_native_anchor_key", "key"),
        ("unresolved", "reason"),
    ],
)
def test_m9_each_basis_member_is_required(basis_class: str, member: str) -> None:
    complete = {
        "operator_declaration": {
            "class": "operator_declaration", "parent": "thermal system A", "slot": "zone east",
        },
        "shared_native_anchor_key": {
            "class": "shared_native_anchor_key", "scheme": "scheme.synthetic", "issuer": "",
            "key": "key-synthetic-1",
        },
        "unresolved": {"class": "unresolved", "reason": "no shared key"},
    }[basis_class]
    assert validate_identity_basis(complete) == basis_class

    blank = dict(complete, **{member: "  "})
    with pytest.raises(ValueError, match=f"lacks {member}"):
        validate_identity_basis(blank)
    missing = {key: value for key, value in complete.items() if key != member}
    with pytest.raises(ValueError, match="has members"):
        validate_identity_basis(missing)


def test_m9_unresolved_mapping_is_never_merged() -> None:
    mapping = _zone_mapping()
    assert mapping["identity_basis"]["class"] == UNRESOLVED
    mapping["merge"] = "candidates_of_one_resource"
    with pytest.raises(ValueError, match="does not follow identity basis"):
        validate_resource_mapping(mapping)


def test_m9_mapping_needs_candidates_from_both_protocols_with_provenance() -> None:
    for protocol in sorted(PROTOCOLS):
        mapping = _zone_mapping()
        mapping["candidates"] = [c for c in mapping["candidates"] if c["protocol"] != protocol]
        with pytest.raises(ValueError, match="candidate from each protocol"):
            validate_resource_mapping(mapping)

    for member in ("repository", "document"):
        mapping = _zone_mapping()
        mapping["candidates"][0]["provenance"].pop(member)
        with pytest.raises(ValueError, match="provenance is not recorded"):
            validate_resource_mapping(mapping)

    mapping = _zone_mapping()
    mapping["candidates"][0]["native_resource"] = " "
    with pytest.raises(ValueError, match="names no native resource"):
        validate_resource_mapping(mapping)


def test_m9_undecided_resource_kind_states_its_reason() -> None:
    mapping = _zone_mapping()
    mapping["resource_kind"] = None
    with pytest.raises(ValueError, match="undecided resource kind"):
        validate_resource_mapping(mapping)

    mapping = _zone_mapping()
    mapping["resource_kind"] = "zone"
    with pytest.raises(ValueError, match="not a common kind identifier"):
        validate_resource_mapping(mapping)


def test_m9_shared_native_anchor_key_issuer_is_a_code_or_empty() -> None:
    complete = {"class": "shared_native_anchor_key", "scheme": "scheme.synthetic", "issuer": "", "key": "key-synthetic-1"}
    missing = {key: value for key, value in complete.items() if key != "issuer"}
    with pytest.raises(ValueError, match="has members"):
        validate_identity_basis(missing)
    with pytest.raises(ValueError, match="issuer must be a code or empty text"):
        validate_identity_basis(dict(complete, issuer=None))


def test_m9_decided_resource_kind_carries_no_reason() -> None:
    mapping = _zone_mapping()
    mapping["resource_kind_reason"] = "kind is undecided"
    with pytest.raises(ValueError, match="not a common kind identifier"):
        validate_resource_mapping(mapping)


def test_m9_leaf_basis_must_equal_its_mapping_basis() -> None:
    manifest = _load(MANIFEST)
    mismatched = copy.deepcopy(manifest)
    zone_leaf = next(
        leaf for leaf in mismatched["leaves"] if leaf["graphql_path"].startswith("zones[id=zone-2]")
    )
    zone_leaf["identity_basis"] = "operator_declaration"
    with pytest.raises(ValueError, match="does not carry the identity basis of zones"):
        validate_manifest(mismatched)


def test_m9_shared_native_anchor_key_records_the_shared_key() -> None:
    basis = {"class": "shared_native_anchor_key", "scheme": "scheme.synthetic", "issuer": ""}
    with pytest.raises(ValueError, match="has members"):
        validate_identity_basis(basis)
    with pytest.raises(ValueError, match="lacks key"):
        validate_identity_basis(dict(basis, key=""))
    assert validate_identity_basis(dict(basis, key="key-synthetic-1")) == (
        "shared_native_anchor_key"
    )


def test_m9_zone_candidates_name_their_native_instance() -> None:
    mappings = {m["target"]: m for m in _load(MANIFEST)["resources"]}
    for zone_id, instance in (("zone-1", "II=0x00"), ("zone-2", "II=0x01")):
        ebus = [
            c for c in mappings[f"zones[id={zone_id}]"]["candidates"] if c["protocol"] == "ebus"
        ]
        assert len(ebus) == 1
        assert ebus[0]["native_resource"].endswith(instance)


def test_m9_candidate_provenance_points_at_checked_in_entries() -> None:
    registry_text = REGISTRY.read_text(encoding="utf-8")
    for mapping in _load(MANIFEST)["resources"]:
        for candidate in mapping["candidates"]:
            provenance = candidate["provenance"]
            if provenance["repository"] != "helianthus-docs-ebus":
                continue
            assert (ROOT / provenance["document"]).is_file()
            entry = provenance.get("entry", "")
            if entry.startswith("entity_slot="):
                assert f'"entity_slot":"{entry.split("=", 1)[1]}"' in registry_text
