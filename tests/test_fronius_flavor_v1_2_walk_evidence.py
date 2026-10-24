from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

from test_fronius_m4_05_live_evidence import (
    contains_endpoint_value,
    contains_private_path,
    evidence_keys,
    evidence_strings,
    sensitive_key,
)
from test_sunspec_model_123_fronius_v3_contract import (
    ARTIFACT_DIR,
    CONTROLS_CHAIN,
    FLAVOR_V1,
    FLAVOR_V1_ID,
    FLAVOR_V11,
    FLAVOR_V11_ID,
    FLAVOR_V12,
    FLAVOR_V12_ID,
    PLATFORM_ENTRY_LINK,
    PLATFORM_INDEX,
    V1_FIRMWARE,
    V12_CHAIN_ENTRIES,
    V12_FIRMWARE,
    admission_gates,
    assert_publication_clean,
    text,
)


ROOT = Path(__file__).resolve().parents[1]
RECORD_DIR = ROOT / ARTIFACT_DIR
README = RECORD_DIR / "README.md"
EVIDENCE = RECORD_DIR / "evidence.json"

CONTRACT_ID = "helianthus.fronius-sunspec-observed-walk-evidence.v1"
CAPABILITY_ID = "sunspec.inverter.three_phase.monitoring@1.0.0"
KNOWN_IDENTIFIERS = (
    CONTRACT_ID,
    CAPABILITY_ID,
    FLAVOR_V1_ID,
    FLAVOR_V11_ID,
    FLAVOR_V12_ID,
)
TERMINAL = 0xFFFF
CLOCK_TIME = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
CALENDAR_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
RELATIVE_LINK = re.compile(r"\]\((?!https?:|#)([^)]+)\)")

# The closed public shape. It is the subset of the Fronius live packet shape
# that a read-only walk supports; the live packets are checked in
# test_fronius_m4_05_0651_go.py.
PUBLIC_TYPE_SCHEMA = {
    "contract": str,
    "evidence_class": str,
    "export_tier": str,
    "outcome": str,
    "target": {
        "manufacturer": str,
        "model": str,
        "firmware": str,
    },
    "acquisition": {
        "transport": str,
        "unit_id": int,
        "function_code": int,
        "signature_pdu_offset": int,
        "writes_permitted": bool,
    },
    "observation": {
        "source_validity": str,
        "chain": [{"model_id": int, "model_length": int}],
        "extent_words": int,
        "field_value_retention": str,
    },
    "registry_evaluation": {
        "capability_id": str,
        "capability_reason": str,
        "flavor_results": [{"flavor_id": str, "flavor_reason": str}],
        "qualification_evidence_only": bool,
        "support_claim": bool,
    },
}


def reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_public_evidence(raw: str) -> dict[str, object]:
    return json.loads(raw, object_pairs_hook=reject_duplicate_pairs)


def load_evidence() -> dict[str, object]:
    return parse_public_evidence(EVIDENCE.read_text(encoding="utf-8"))


def assert_recursive_type_shape(value: object, schema: object) -> None:
    if isinstance(schema, type):
        assert type(value) is schema
        return
    if isinstance(schema, dict):
        assert type(value) is dict
        assert set(value) == set(schema)
        for key, child_schema in schema.items():
            assert_recursive_type_shape(value[key], child_schema)
        return
    if isinstance(schema, list):
        assert type(schema) is list and len(schema) == 1
        assert type(value) is list
        for child in value:
            assert_recursive_type_shape(child, schema[0])
        return
    raise AssertionError(f"unsupported public schema node: {schema!r}")


def evaluate_flavor(
    flavor_page: str, target: dict[str, str], chain: list[tuple[int, int]]
) -> str:
    """Apply a flavor page's published gates in its published precedence."""
    gates = admission_gates(flavor_page)
    if (target["manufacturer"], target["model"]) != (gates["manufacturer"], gates["model"]):
        return "COMMON_IDENTITY_MISMATCH"
    if target["firmware"] != gates["firmware"]:
        return "FIRMWARE_MISMATCH"
    if chain != gates["entries"]:
        return "CHAIN_MISMATCH"
    return "MATCHED"


def assert_record_contract(record: dict[str, object]) -> None:
    assert_recursive_type_shape(record, PUBLIC_TYPE_SCHEMA)
    assert record["contract"] == CONTRACT_ID
    assert record["evidence_class"] == "READ_ONLY_WALK_OBSERVATION"
    assert record["export_tier"] == "PUBLIC_REDACTED"
    assert record["outcome"] == "OBSERVED"

    page = text(FLAVOR_V12)
    gates = admission_gates(page)
    target = record["target"]
    assert target == {
        "manufacturer": "Fronius",
        "model": "Symo GEN24 10.0",
        "firmware": V12_FIRMWARE,
    }
    assert target == {
        "manufacturer": gates["manufacturer"],
        "model": gates["model"],
        "firmware": gates["firmware"],
    }
    assert record["acquisition"] == {
        "transport": "modbus_tcp",
        "unit_id": 1,
        "function_code": 3,
        "signature_pdu_offset": 40000,
        "writes_permitted": False,
    }

    observation = record["observation"]
    chain = [(item["model_id"], item["model_length"]) for item in observation["chain"]]
    assert chain == V12_CHAIN_ENTRIES
    assert chain == gates["entries"]
    assert [model_id for model_id, _ in chain].count(TERMINAL) == 1
    assert chain[-1] == (TERMINAL, 0)
    assert [item for item in chain if item == (113, 60)] == [(113, 60)]
    assert observation["source_validity"] == "terminal_verified"
    # Two signature words, then a two-word header plus the length of every
    # model, the terminal header included.
    assert observation["extent_words"] == 2 + sum(2 + length for _, length in chain)
    assert observation["field_value_retention"] == "PRESERVED_PRIVATE_NOT_PROMOTED"

    evaluation = record["registry_evaluation"]
    assert evaluation["capability_id"] == CAPABILITY_ID
    assert evaluation["capability_reason"] == "ADMITTED"
    assert evaluation["flavor_results"] == [
        {
            "flavor_id": FLAVOR_V1_ID,
            "flavor_reason": evaluate_flavor(text(FLAVOR_V1), target, chain),
        },
        {
            "flavor_id": FLAVOR_V11_ID,
            "flavor_reason": evaluate_flavor(text(FLAVOR_V11), target, chain),
        },
    ]
    assert [item["flavor_reason"] for item in evaluation["flavor_results"]] == [
        "FIRMWARE_MISMATCH",
        "FIRMWARE_MISMATCH",
    ]
    assert evaluation["qualification_evidence_only"] is True
    assert evaluation["support_claim"] is False
    # The walk satisfies the V1.2 gates and no earlier flavor's gates.
    assert evaluate_flavor(page, target, chain) == "MATCHED"


def scrub(value: str) -> str:
    for identifier in KNOWN_IDENTIFIERS:
        value = value.replace(identifier, "")
    return value


def assert_public_redaction(record: dict[str, object], *documents: str) -> None:
    for document in documents:
        public = scrub(document)
        assert not contains_endpoint_value(public)
        assert not contains_private_path(public)
        assert not CLOCK_TIME.search(public)
        assert not CALENDAR_DATE.search(public)
        assert_publication_clean(document)
    assert not any(sensitive_key(key) for key in evidence_keys(record))
    for value in evidence_strings(record):
        assert not contains_endpoint_value(scrub(value))
        assert not contains_private_path(scrub(value))


def format_chain(chain: list[dict[str, int]]) -> str:
    return ", ".join(
        f"{'FFFF' if item['model_id'] == TERMINAL else item['model_id']}/{item['model_length']}"
        for item in chain
    )


def assert_readme_matches(readme: str, record: dict[str, object]) -> None:
    target = record["target"]
    observation = record["observation"]
    acquisition = record["acquisition"]
    squashed = " ".join(readme.split())
    for value in target.values():
        assert f"`{value}`" in squashed
    assert f"`{format_chain(observation['chain'])}`" in squashed
    assert f"`{observation['extent_words']}`" in squashed
    assert f"unit ID `{acquisition['unit_id']}`" in squashed
    assert f"FC0{acquisition['function_code']}" in squashed
    assert f"normalized PDU offset `{acquisition['signature_pdu_offset']}`" in squashed
    assert "`ADMITTED`" in squashed
    assert squashed.count("`FIRMWARE_MISMATCH`") == 1
    assert "holds no `MATCHED` result" in squashed
    assert "PRESERVED_PRIVATE_NOT_PROMOTED" in squashed
    links = RELATIVE_LINK.findall(readme)
    assert [(RECORD_DIR / link).resolve() for link in links if link.endswith(".md")] == [
        FLAVOR_V12.resolve()
    ]
    assert all((RECORD_DIR / link).resolve().exists() for link in links)
    assert any("fronius-m4-04-0.6.51" in link for link in links)


def leaf_paths(value: object, prefix: tuple = ()) -> list[tuple]:
    if isinstance(value, dict):
        return [p for key, child in value.items() for p in leaf_paths(child, prefix + (key,))]
    if isinstance(value, list):
        return [p for index, child in enumerate(value) for p in leaf_paths(child, prefix + (index,))]
    return [prefix]


def container_paths(value: object, prefix: tuple = ()) -> list[tuple]:
    if isinstance(value, dict):
        found = [prefix]
        for key, child in value.items():
            found += container_paths(child, prefix + (key,))
        return found
    if isinstance(value, list):
        return [p for index, child in enumerate(value) for p in container_paths(child, prefix + (index,))]
    return []


def walk(record: dict[str, object], path: tuple) -> object:
    node: object = record
    for step in path:
        node = node[step]
    return node


def other_value(value: object) -> object:
    if type(value) is bool:
        return not value
    if type(value) is int:
        return value + 1
    return f"{value}x"


def test_record_matches_the_closed_shape_and_the_flavor_pages() -> None:
    assert_record_contract(load_evidence())


def test_record_directory_holds_exactly_the_readme_and_the_record() -> None:
    assert sorted(path.name for path in RECORD_DIR.iterdir()) == ["README.md", "evidence.json"]


def test_every_field_of_the_record_is_pinned() -> None:
    record = load_evidence()
    paths = leaf_paths(record)
    assert len(paths) == 41
    for path in paths:
        weakened = copy.deepcopy(record)
        parent = walk(weakened, path[:-1])
        parent[path[-1]] = other_value(parent[path[-1]])
        with pytest.raises(AssertionError):
            assert_record_contract(weakened)


def test_every_field_of_the_record_is_required() -> None:
    record = load_evidence()
    for path in leaf_paths(record):
        if not isinstance(path[-1], str):
            continue
        weakened = copy.deepcopy(record)
        del walk(weakened, path[:-1])[path[-1]]
        with pytest.raises(AssertionError):
            assert_record_contract(weakened)


def test_no_section_accepts_an_extra_field() -> None:
    record = load_evidence()
    for path in container_paths(record):
        weakened = copy.deepcopy(record)
        walk(weakened, path)["additional_field"] = "x"
        with pytest.raises(AssertionError):
            assert_record_contract(weakened)


@pytest.mark.parametrize("index", range(len(V12_CHAIN_ENTRIES)))
def test_chain_entries_cannot_be_dropped_or_reordered(index: int) -> None:
    record = load_evidence()
    chain = record["observation"]["chain"]

    dropped = copy.deepcopy(record)
    del dropped["observation"]["chain"][index]
    with pytest.raises(AssertionError):
        assert_record_contract(dropped)

    if index + 1 < len(chain):
        swapped = copy.deepcopy(record)
        items = swapped["observation"]["chain"]
        items[index], items[index + 1] = items[index + 1], items[index]
        with pytest.raises(AssertionError):
            assert_record_contract(swapped)


def test_chain_cannot_gain_an_entry_or_lose_the_terminal() -> None:
    record = load_evidence()

    longer = copy.deepcopy(record)
    longer["observation"]["chain"].append({"model_id": 999, "model_length": 1})
    with pytest.raises(AssertionError):
        assert_record_contract(longer)

    unterminated = copy.deepcopy(record)
    unterminated["observation"]["chain"].pop()
    unterminated["observation"]["extent_words"] -= 2
    with pytest.raises(AssertionError):
        assert_record_contract(unterminated)


def test_flavor_results_cannot_be_reordered_or_dropped() -> None:
    record = load_evidence()

    reordered = copy.deepcopy(record)
    reordered["registry_evaluation"]["flavor_results"].reverse()
    with pytest.raises(AssertionError):
        assert_record_contract(reordered)

    dropped = copy.deepcopy(record)
    dropped["registry_evaluation"]["flavor_results"].pop()
    with pytest.raises(AssertionError):
        assert_record_contract(dropped)


def test_record_firmware_must_stay_the_v12_string_not_an_earlier_flavor_string() -> None:
    record = load_evidence()
    record["target"]["firmware"] = V1_FIRMWARE
    with pytest.raises(AssertionError):
        assert_record_contract(record)


@pytest.mark.parametrize(
    ("section", "field"),
    [
        ("observation", "model_headers"),
        ("observation", "register_words"),
        ("acquisition", "raw_registers"),
        ("target", "serial_number"),
    ],
)
def test_closed_shape_rejects_numeric_raw_and_identifying_fields(section: str, field: str) -> None:
    mutated = copy.deepcopy(load_evidence())
    mutated[section][field] = [1, 65, 113, 60]
    with pytest.raises(AssertionError):
        assert_record_contract(mutated)


def test_closed_shape_rejects_numeric_raw_in_allowed_scalars() -> None:
    for path in (("target", "firmware"), ("target", "model"), ("observation", "source_validity")):
        mutated = copy.deepcopy(load_evidence())
        walk(mutated, path[:-1])[path[-1]] = [1, 65, 113, 60]
        with pytest.raises(AssertionError):
            assert_record_contract(mutated)


def test_parser_rejects_a_duplicate_key_bypass() -> None:
    original = EVIDENCE.read_text(encoding="utf-8")
    duplicate = original.replace(
        '  "observation": {',
        '  "observation": {"register_words": [1, 65, 113, 60]},\n  "observation": {',
        1,
    )
    assert duplicate != original
    with pytest.raises(ValueError, match=r"duplicate JSON key: observation"):
        parse_public_evidence(duplicate)


def test_publication_is_redacted_and_carries_no_register_words() -> None:
    record = load_evidence()
    assert_public_redaction(
        record,
        README.read_text(encoding="utf-8"),
        EVIDENCE.read_text(encoding="utf-8"),
    )


def test_redaction_guard_rejects_each_class_of_withheld_value() -> None:
    record = load_evidence()
    readme = README.read_text(encoding="utf-8")
    digest = "0123456789abcdef"
    probes = {
        "network-address": "reachable at 192.0.2.7",
        "host-and-port": "gateway.invalid:502",
        "private-path": "see /Users/operator/walk.json",
        "capture-date": "captured 2026-10-24",
        "capture-time": "captured at 13:57",
        "forty-hex-id": digest * 2 + digest[:8],
        "sixty-four-hex-digest": digest * 4,
    }
    for name, probe in probes.items():
        with pytest.raises(AssertionError):
            assert_public_redaction(record, readme + "\n" + probe + "\n")
    keyed = copy.deepcopy(record)
    keyed["target"]["serial_number"] = "x"
    with pytest.raises(AssertionError):
        assert_public_redaction(keyed, readme)


def test_readme_states_the_record_and_links_the_flavor_page() -> None:
    assert_readme_matches(README.read_text(encoding="utf-8"), load_evidence())


@pytest.mark.parametrize(
    ("before", "after"),
    [
        pytest.param("`Fronius`", "`fronius`", id="manufacturer"),
        pytest.param("`Symo GEN24 10.0`", "`Symo GEN24 8.0`", id="model"),
        pytest.param("`1.42.9-1`", "`1.41.11-1`", id="firmware"),
        pytest.param("113/60, 120/26", "113/60", id="chain-drops-an-entry"),
        pytest.param("113/60, 120/26", "120/26, 113/60", id="chain-reorders-entries"),
        pytest.param("`381`", "`380`", id="extent"),
        pytest.param("unit ID `1`", "unit ID `2`", id="unit-id"),
        pytest.param("FC03 only", "FC04 only", id="function-code"),
        pytest.param("`40000`", "`40001`", id="signature-offset"),
        pytest.param("holds no `MATCHED` result", "holds a `MATCHED` result", id="matched-claimed"),
        pytest.param("../fronius-m4-04-0.6.51/", "../removed/", id="packet-link"),
        pytest.param(
            "architecture/protocol-routing-vendor-fronius-observed-flavor-v1-2.md",
            "architecture/protocol-routing-vendor-fronius-observed-flavor-v1-1.md",
            id="flavor-page-link",
        ),
    ],
)
def test_readme_rejects_a_changed_statement(before: str, after: str) -> None:
    readme = README.read_text(encoding="utf-8")
    assert before in readme
    weakened = readme.replace(before, after)
    assert weakened != readme
    with pytest.raises(AssertionError):
        assert_readme_matches(weakened, load_evidence())


def test_record_is_indexed_and_cited_by_the_flavor_page() -> None:
    assert PLATFORM_ENTRY_LINK in PLATFORM_INDEX.read_text(encoding="utf-8")
    page = text(FLAVOR_V12)
    assert f"](../{ARTIFACT_DIR}/)" in page
    assert CONTROLS_CHAIN in page
