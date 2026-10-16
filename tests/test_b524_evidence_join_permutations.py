"""Exercise the published BASV0 bundle through its public validation boundary."""

import importlib.util
import itertools
import json
import random
import re
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "protocols/vaillant/fixtures"
APPLICATION = ROOT / "development/fixtures"
CATALOG = "b524-basv0-description-profile-v1.json"
FIXTURES = (
    NATIVE / CATALOG,
    NATIVE / "b524-basv0-register-observations-v1.json",
    APPLICATION / "b524-basv0-validation-scope-v1.json",
)
SCHEMAS = (
    NATIVE / "b524-basv0-description-profile-schema-v1.json",
    NATIVE / "b524-basv0-register-observations-schema-v1.json",
    APPLICATION / "b524-basv0-validation-scope-schema-v1.json",
)
SELECTOR_FIELDS = ("operation", "group", "instance", "register")
SPEC = importlib.util.spec_from_file_location(
    "evidence_join_validator",
    ROOT / "scripts/validate_b524_basv0_description_profile.py",
)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def selector_key(selector: dict) -> tuple[str, ...]:
    return tuple(selector[field] for field in SELECTOR_FIELDS)


@pytest.fixture
def published_bundle():
    # Compare bytes, including the schemas, without pinning a literal digest.
    originals = {path: path.read_bytes() for path in (*FIXTURES, *SCHEMAS)}
    yield tuple(json.loads(originals[path]) for path in FIXTURES)
    for path, original in originals.items():
        assert path.read_bytes() == original, path.name


def permute_bundle(bundle: tuple, reordered: tuple[bool, ...]) -> tuple:
    candidate = deepcopy(bundle)
    for seed, document, enabled in zip((604, 605, 606), candidate, reordered):
        if enabled:
            previous = document["records"][:]
            random.Random(seed).shuffle(document["records"])
            assert document["records"] != previous

    # record_index is a public schema field. Resolve it from the complete
    # selector after permutation, never from a fixture's historical row number.
    descriptions, observations, _ = candidate
    indices = {
        selector_key(record["selector"]): index
        for index, record in enumerate(descriptions["records"])
    }
    for row in observations["records"]:
        if row["description"] is not None:
            row["description"]["record_index"] = indices[selector_key(row["selector"])]
    return candidate


def content_by_selector(document: dict) -> dict:
    """Normalize only the public positional reference; retain all evidence."""
    result = deepcopy(document)
    records = result.pop("records")
    keyed = {}
    for record in records:
        reference = record.get("description")
        if reference is not None:
            reference.pop("record_index")
        key = selector_key(record["selector"])
        assert key not in keyed
        keyed[key] = record
    return {"metadata": result, "records": keyed}


def validate_schemas(bundle: tuple, tmp_path: Path) -> None:
    for document, fixture, schema in zip(bundle, FIXTURES, SCHEMAS):
        path = tmp_path / fixture.name
        path.write_text(json.dumps(document), encoding="utf-8")
        result = subprocess.run(
            ["jv", str(schema), str(path)],
            cwd=ROOT, capture_output=True, text=True, check=False, timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("reordered", list(itertools.product((False, True), repeat=3)))
def test_complete_bundle_accepts_independent_record_orders(
    published_bundle: tuple, tmp_path: Path, reordered: tuple[bool, ...],
) -> None:
    candidate = permute_bundle(published_bundle, reordered)
    for original, permuted in zip(published_bundle, candidate):
        # This includes raw spans, nulls, qualification, omission markers and
        # nonclaims; serialization order is deliberately not authenticated.
        assert content_by_selector(permuted) == content_by_selector(original)
        assert len(permuted["records"]) == len(original["records"])
    validate_schemas(candidate, tmp_path)
    descriptions, observations, overlay = candidate
    validator.validate_documents(descriptions, observations, CATALOG, overlay)


def differing_pair(records: list[dict], field: str) -> tuple[dict, dict]:
    """Find two published selectors differing in exactly the named component."""
    seen = {}
    for record in records:
        if record["description"] is None:
            continue
        selector = record["selector"]
        remaining = tuple(selector[name] for name in SELECTOR_FIELDS if name != field)
        previous = seen.get(remaining)
        if previous is not None and previous["selector"][field] != selector[field]:
            return previous, record
        seen[remaining] = record
    raise AssertionError(f"published fixture has no pair differing only in {field}")


@pytest.mark.parametrize("field", SELECTOR_FIELDS)
def test_same_size_cross_link_rejected_by_full_selector_invariant(
    published_bundle: tuple, tmp_path: Path, field: str,
) -> None:
    candidate = permute_bundle(published_bundle, (True, True, True))
    descriptions, observations, overlay = candidate
    validator.validate_documents(descriptions, observations, CATALOG, overlay)
    before = deepcopy(candidate)
    left, right = differing_pair(observations["records"], field)
    assert [name for name in SELECTOR_FIELDS
            if left["selector"][name] != right["selector"][name]] == [field]
    left_ref, right_ref = left["description"], right["description"]
    left_ref["record_index"], right_ref["record_index"] = (
        right_ref["record_index"], left_ref["record_index"],
    )
    for original, corrupted in zip(before, candidate):
        assert len(corrupted["records"]) == len(original["records"])
        assert content_by_selector(corrupted) == content_by_selector(original)
    validate_schemas(candidate, tmp_path)
    with pytest.raises(validator.ValidationError) as caught:
        validator.validate_documents(descriptions, observations, CATALOG, overlay)
    assert re.fullmatch(
        r"observation records\[\d+\] description selector mismatch; "
        r"records\[\d+\] request opcode corroboration failed "
        r"\(linked observation must match operation, group, instance and register\)",
        str(caught.value),
    )
