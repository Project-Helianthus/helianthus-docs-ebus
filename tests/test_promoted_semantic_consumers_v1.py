import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/platform/manifests/promoted-semantic-consumers-v1.json"
REGISTRY = ROOT / "docs/platform/schemas/leaf-promotion-captured-multi-leaf-registry-v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_m9_manifest_matches_exact_locked_leaf_catalog() -> None:
    manifest = _load(MANIFEST)
    registry = _load(REGISTRY)

    leaves = manifest["leaves"]
    assert manifest["contract"] == "helianthus.platform.promoted-semantic-consumers.v1"
    assert manifest["projection_policy"] == "FILL_MISSING_ONLY"
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
        assert set(leaf) == {
            "semantic_path",
            "value_kind",
            "unit",
            "graphql_path",
            "producer_class",
        }
        assert not (set(leaf) & forbidden)

