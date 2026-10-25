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
    SIDECAR_FILE,
    SIDECAR_LINK,
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
SIDECAR = RECORD_DIR / SIDECAR_FILE
# The packet holds exactly these files: the README, the record, and one
# sidecar of Common block register words.
PACKET_FILES = sorted(["README.md", "evidence.json", SIDECAR_FILE])

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


# The one sidecar: the sanitized Common block (Model 1) register words, from
# the SunSpec signature through the device-address register. The layout is the
# standard Common block: two signature words, the two-word model header, then
# the data registers in this order.
SIDECAR_TYPE_SCHEMA = {
    "label": str,
    "function_code": int,
    "unit_id": int,
    "base_offset": int,
    "redaction": str,
    "registers": [int],
}
SIDECAR_REDACTION = (
    "model 1 serial-number field (16 registers) zeroed; "
    "no endpoint, date, time or digest"
)
SIGNATURE_WORDS = [0x5375, 0x6E53]  # "SunS"
HEADER_WORDS = len(SIGNATURE_WORDS) + 2
COMMON_FIELD_WIDTHS = {"Mn": 16, "Md": 16, "Opt": 8, "Vr": 8, "SN": 16, "DA": 1}
SIDECAR_WORDS = HEADER_WORDS + sum(COMMON_FIELD_WIDTHS.values())


def common_layout() -> dict[str, slice]:
    layout: dict[str, slice] = {}
    start = HEADER_WORDS
    for field, width in COMMON_FIELD_WIDTHS.items():
        layout[field] = slice(start, start + width)
        start += width
    return layout


LAYOUT = common_layout()


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


def load_sidecar() -> dict[str, object]:
    return parse_public_evidence(SIDECAR.read_text(encoding="utf-8"))


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


def decode_text_field(words: list[int]) -> str:
    """Decode big-endian ASCII; only NUL padding may follow the text."""
    raw = b"".join(word.to_bytes(2, "big") for word in words)
    head, *rest = raw.split(b"\x00", 1)
    assert not rest or rest[0].strip(b"\x00") == b"", "bytes follow the NUL padding"
    assert all(0x20 <= byte < 0x7F for byte in head), "non-printable text"
    return head.decode("ascii")


def assert_sidecar_contract(sidecar: dict[str, object], record: dict[str, object]) -> None:
    assert_recursive_type_shape(sidecar, SIDECAR_TYPE_SCHEMA)
    acquisition = record["acquisition"]
    target = record["target"]
    first_model_id, first_length = (
        record["observation"]["chain"][0]["model_id"],
        record["observation"]["chain"][0]["model_length"],
    )

    # Provenance: the packet's own label, no other reference.
    assert sidecar["label"] == RECORD_DIR.name
    assert sidecar["label"] == ARTIFACT_DIR.rsplit("/", 1)[-1]
    assert sidecar["redaction"] == SIDECAR_REDACTION
    # The acquisition parameters are those of the record.
    assert sidecar["function_code"] == acquisition["function_code"] == 3
    assert sidecar["unit_id"] == acquisition["unit_id"] == 1
    assert sidecar["base_offset"] == acquisition["signature_pdu_offset"] == 40000

    words = sidecar["registers"]
    # Bounds: the signature, the Model 1 header, and exactly the Model 1 data
    # registers the first chain entry declares. Nothing of any later model.
    assert (first_model_id, first_length) == (1, 65)
    assert SIDECAR_WORDS == HEADER_WORDS + first_length
    assert len(words) == SIDECAR_WORDS
    assert all(0 <= word <= 0xFFFF for word in words)
    assert words[: len(SIGNATURE_WORDS)] == SIGNATURE_WORDS
    assert words[len(SIGNATURE_WORDS) : HEADER_WORDS] == [first_model_id, first_length]

    # The firmware decoding is checkable against the words.
    assert decode_text_field(words[LAYOUT["Mn"]]) == target["manufacturer"]
    assert decode_text_field(words[LAYOUT["Md"]]) == target["model"]
    assert decode_text_field(words[LAYOUT["Vr"]]) == target["firmware"]
    # The serial-number field is zeroed; no other field carries a value.
    assert all(word == 0 for word in words[LAYOUT["SN"]])
    assert all(word == 0 for word in words[LAYOUT["Opt"]])
    assert words[LAYOUT["DA"]] == [acquisition["unit_id"]]


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


def assert_readme_matches(
    readme: str, record: dict[str, object], sidecar: dict[str, object]
) -> None:
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

    # The sidecar: cited, bounded, and checkable against the tuple.
    words = sidecar["registers"]
    base = sidecar["base_offset"]
    assert f"[`{SIDECAR_FILE}`](./{SIDECAR_FILE})" in squashed
    assert f"`{sidecar['label']}`" in squashed
    assert f"{len(words)} words" in squashed
    first_length = record["observation"]["chain"][0]["model_length"]
    assert f"and the {first_length} Model 1 data registers" in squashed
    assert f"function code `{sidecar['function_code']}`" in squashed
    assert f"base offset `{base}`" in squashed
    assert (
        f"through the Common device-address register at offset `{base + len(words) - 1}`"
        in squashed
    )
    assert f"the word at offset `{base + len(words)}`" in squashed
    assert "is not published" in squashed
    serial = LAYOUT["SN"]
    assert (
        f"offsets `{base + serial.start}` through `{base + serial.stop - 1}`, are zeroed"
        in squashed
    )
    for field in ("Mn", "Md", "Vr"):
        span = LAYOUT[field]
        assert (
            f"offsets `{base + span.start}` through `{base + span.stop - 1}` (`{field}`) "
            f"decode to `{decode_text_field(words[span])}`"
        ) in squashed
    assert (
        f"offsets `{base + 2}` and `{base + 3}` hold model ID `{words[2]}` "
        f"and length `{words[3]}`"
    ) in squashed
    assert (
        f"the device-address register, offset `{base + LAYOUT['DA'].start}`, "
        f"holds `{words[LAYOUT['DA']][0]}`"
    ) in squashed
    assert "The sidecar covers Model 1 only" in squashed

    links = RELATIVE_LINK.findall(readme)
    assert [(RECORD_DIR / link).resolve() for link in links if link.endswith(".md")] == [
        FLAVOR_V12.resolve()
    ]
    assert all((RECORD_DIR / link).resolve().exists() for link in links)
    assert any("fronius-m4-04-0.6.51" in link for link in links)
    assert f"./{SIDECAR_FILE}" in links
    assert "./evidence.json" in links


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


def assert_packet_files(names: list[str]) -> None:
    assert sorted(names) == PACKET_FILES


def test_record_directory_holds_exactly_the_readme_the_record_and_one_sidecar() -> None:
    entries = list(RECORD_DIR.iterdir())
    assert all(path.is_file() for path in entries)
    assert_packet_files([path.name for path in entries])


@pytest.mark.parametrize(
    "names",
    [
        pytest.param(["README.md", "evidence.json"], id="sidecar-missing"),
        pytest.param(["README.md", SIDECAR_FILE], id="record-missing"),
        pytest.param([*PACKET_FILES, "common-block-2.json"], id="second-sidecar"),
        pytest.param([*PACKET_FILES, "walk-words.json"], id="other-file"),
        pytest.param([*PACKET_FILES, "raw"], id="extra-entry"),
        pytest.param(["README.md", "evidence.json", "common_block.json"], id="sidecar-renamed"),
    ],
)
def test_packet_directory_allows_exactly_one_sidecar(names: list[str]) -> None:
    with pytest.raises(AssertionError):
        assert_packet_files(names)


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


def test_sidecar_publication_is_redacted() -> None:
    assert_public_redaction(load_sidecar(), SIDECAR.read_text(encoding="utf-8"))


def redaction_probes() -> dict[str, str]:
    digest = "0123456789abcdef"
    return {
        "network-address": "reachable at 192.0.2.7",
        "host-and-port": "gateway.invalid:502",
        "private-path": "see /Users/operator/walk.json",
        "capture-date": "captured 2026-10-24",
        "capture-time": "captured at 13:57",
        "forty-hex-id": digest * 2 + digest[:8],
        "sixty-four-hex-digest": digest * 4,
    }


def test_redaction_guard_rejects_each_class_of_withheld_value() -> None:
    record = load_evidence()
    readme = README.read_text(encoding="utf-8")
    for name, probe in redaction_probes().items():
        with pytest.raises(AssertionError):
            assert_public_redaction(record, readme + "\n" + probe + "\n")
    keyed = copy.deepcopy(record)
    keyed["target"]["serial_number"] = "x"
    with pytest.raises(AssertionError):
        assert_public_redaction(keyed, readme)


@pytest.mark.parametrize("name", sorted(redaction_probes()))
def test_redaction_guard_rejects_each_class_of_withheld_value_in_the_sidecar(name: str) -> None:
    sidecar = load_sidecar()
    document = SIDECAR.read_text(encoding="utf-8")
    with pytest.raises(AssertionError):
        assert_public_redaction(sidecar, document + "\n" + redaction_probes()[name] + "\n")
    spoken = copy.deepcopy(sidecar)
    spoken["redaction"] = f"{SIDECAR_REDACTION}; {redaction_probes()[name]}"
    with pytest.raises(AssertionError):
        assert_public_redaction(spoken, json.dumps(spoken))
    keyed = copy.deepcopy(sidecar)
    keyed["serial_number"] = "x"
    with pytest.raises(AssertionError):
        assert_public_redaction(keyed, document)


def test_readme_states_the_record_and_links_the_flavor_page() -> None:
    assert_readme_matches(README.read_text(encoding="utf-8"), load_evidence(), load_sidecar())


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
        pytest.param("(./common-block.json)", "(./evidence.json)", id="sidecar-link"),
        pytest.param("(./common-block.json)", "(./removed.json)", id="sidecar-link-dangling"),
        pytest.param(
            "`fronius-observed-flavor-1.2.0`",
            "`fronius-observed-flavor-1.1.0`",
            id="sidecar-provenance-label",
        ),
        pytest.param("69 words", "70 words", id="sidecar-word-count"),
        pytest.param(
            "the 65 Model 1 data registers",
            "the 64 Model 1 data registers",
            id="sidecar-data-register-count",
        ),
        pytest.param("function code `3`", "function code `4`", id="sidecar-function-code"),
        pytest.param("base offset `40000`", "base offset `40001`", id="sidecar-base-offset"),
        pytest.param(
            "at offset `40068`: 69", "at offset `40069`: 69", id="sidecar-last-register"
        ),
        pytest.param("the word at offset\n`40069`", "the word at offset\n`40070`", id="sidecar-first-withheld-word"),
        pytest.param(
            "offsets `40052` through `40067`",
            "offsets `40052` through `40066`",
            id="sidecar-serial-range",
        ),
        pytest.param("through `40019` (`Mn`) decode to `Fronius`", "through `40019` (`Mn`) decode to `Fronius AG`", id="sidecar-manufacturer-decoding"),
        pytest.param("(`Md`) decode to `Symo GEN24 10.0`", "(`Md`) decode to `Symo GEN24 8.0`", id="sidecar-model-decoding"),
        pytest.param("(`Vr`) decode to `1.42.9-1`", "(`Vr`) decode to `1.41.11-1`", id="sidecar-firmware-decoding"),
        pytest.param("model ID `1` and length `65`", "model ID `1` and length `66`", id="sidecar-header"),
        pytest.param("offset `40068`, holds `1`", "offset `40068`, holds `2`", id="sidecar-device-address"),
        pytest.param("The sidecar covers Model 1 only", "The sidecar covers every model", id="sidecar-scope"),
    ],
)
def test_readme_rejects_a_changed_statement(before: str, after: str) -> None:
    readme = README.read_text(encoding="utf-8")
    assert before in readme
    weakened = readme.replace(before, after)
    assert weakened != readme
    with pytest.raises(AssertionError):
        assert_readme_matches(weakened, load_evidence(), load_sidecar())


def test_record_is_indexed_and_cited_by_the_flavor_page() -> None:
    assert PLATFORM_ENTRY_LINK in PLATFORM_INDEX.read_text(encoding="utf-8")
    page = text(FLAVOR_V12)
    assert f"](../{ARTIFACT_DIR}/)" in page
    assert SIDECAR_LINK in page
    assert CONTROLS_CHAIN in page


# The sidecar: the Common block words only, serial field zeroed, nothing beyond
# the device-address register, and no register word anywhere in evidence.json.


def test_sidecar_matches_the_closed_shape_the_record_and_the_tuple() -> None:
    sidecar = load_sidecar()
    assert_sidecar_contract(sidecar, load_evidence())
    assert len(sidecar["registers"]) == SIDECAR_WORDS == 69
    assert LAYOUT["DA"].stop == SIDECAR_WORDS


def test_every_field_of_the_sidecar_is_pinned() -> None:
    sidecar = load_sidecar()
    record = load_evidence()
    paths = leaf_paths(sidecar)
    assert len(paths) == 5 + SIDECAR_WORDS
    for path in paths:
        weakened = copy.deepcopy(sidecar)
        parent = walk(weakened, path[:-1])
        parent[path[-1]] = other_value(parent[path[-1]])
        with pytest.raises(AssertionError):
            assert_sidecar_contract(weakened, record)


def test_every_field_of_the_sidecar_is_required() -> None:
    sidecar = load_sidecar()
    record = load_evidence()
    for key in sidecar:
        weakened = copy.deepcopy(sidecar)
        del weakened[key]
        with pytest.raises(AssertionError):
            assert_sidecar_contract(weakened, record)


@pytest.mark.parametrize(
    "key",
    [
        "additional_field",
        "endpoint",
        "serial_number",
        "captured_at",
        "digest",
        "model_113",
        "register_words",
    ],
)
def test_sidecar_accepts_no_extra_field(key: str) -> None:
    weakened = copy.deepcopy(load_sidecar())
    weakened[key] = "x"
    with pytest.raises(AssertionError):
        assert_sidecar_contract(weakened, load_evidence())


NEXT_MODEL_HEADER = [113, 60]


@pytest.mark.parametrize(
    "extension",
    [
        pytest.param([0], id="one-word"),
        pytest.param(NEXT_MODEL_HEADER, id="next-model-header"),
        pytest.param(NEXT_MODEL_HEADER + [0] * 60, id="whole-next-model"),
        pytest.param(NEXT_MODEL_HEADER + [0] * 60 + [65535, 0], id="through-the-terminal"),
    ],
)
def test_sidecar_cannot_extend_past_the_common_block(extension: list[int]) -> None:
    weakened = copy.deepcopy(load_sidecar())
    weakened["registers"] += extension
    with pytest.raises(AssertionError):
        assert_sidecar_contract(weakened, load_evidence())


def test_sidecar_cannot_stop_short_of_the_device_address_register() -> None:
    record = load_evidence()
    for cut in (slice(0, -1), slice(1, None)):
        weakened = copy.deepcopy(load_sidecar())
        weakened["registers"] = weakened["registers"][cut]
        with pytest.raises(AssertionError):
            assert_sidecar_contract(weakened, record)
    empty = copy.deepcopy(load_sidecar())
    empty["registers"] = []
    with pytest.raises(AssertionError):
        assert_sidecar_contract(empty, record)


@pytest.mark.parametrize("index", range(LAYOUT["SN"].start, LAYOUT["SN"].stop))
@pytest.mark.parametrize("value", [1, 0x4142, 0xFFFF])
def test_sidecar_serial_number_field_must_stay_zeroed(index: int, value: int) -> None:
    weakened = copy.deepcopy(load_sidecar())
    weakened["registers"][index] = value
    with pytest.raises(AssertionError):
        assert_sidecar_contract(weakened, load_evidence())


@pytest.mark.parametrize("index", range(LAYOUT["Opt"].start, LAYOUT["Opt"].stop))
def test_sidecar_option_field_carries_no_value(index: int) -> None:
    weakened = copy.deepcopy(load_sidecar())
    weakened["registers"][index] = 0x4142
    with pytest.raises(AssertionError):
        assert_sidecar_contract(weakened, load_evidence())


@pytest.mark.parametrize("field", ["Mn", "Md", "Vr"])
def test_sidecar_identity_words_must_decode_to_the_tuple(field: str) -> None:
    span = LAYOUT[field]
    key = {"Mn": "manufacturer", "Md": "model", "Vr": "firmware"}[field]
    sidecar = load_sidecar()
    record = load_evidence()

    # The record names a different value than the words decode to.
    other = copy.deepcopy(record)
    other["target"][key] = other["target"][key] + "x"
    with pytest.raises(AssertionError):
        assert_sidecar_contract(sidecar, other)

    # A flipped case bit on the first character.
    folded = copy.deepcopy(sidecar)
    folded["registers"][span.start] ^= 0x2000
    with pytest.raises(AssertionError):
        assert_sidecar_contract(folded, record)

    # A space where the NUL padding starts.
    padded = copy.deepcopy(sidecar)
    first_pad = next(
        index
        for index in range(span.start, span.stop)
        if padded["registers"][index] & 0xFF == 0
    )
    padded["registers"][first_pad] |= 0x0020
    with pytest.raises(AssertionError):
        assert_sidecar_contract(padded, record)

    # Text after the padding.
    trailing = copy.deepcopy(sidecar)
    trailing["registers"][span.stop - 1] = 0x0041
    with pytest.raises(AssertionError):
        assert_sidecar_contract(trailing, record)


def test_sidecar_provenance_must_be_the_packet_label() -> None:
    record = load_evidence()
    assert load_sidecar()["label"] == RECORD_DIR.name
    for label in ("", "fronius-observed-flavor-1.1.0", RECORD_DIR.name + "x", RECORD_DIR.name.upper()):
        weakened = copy.deepcopy(load_sidecar())
        weakened["label"] = label
        with pytest.raises(AssertionError):
            assert_sidecar_contract(weakened, record)


def test_sidecar_acquisition_must_agree_with_the_record() -> None:
    sidecar = load_sidecar()
    record = load_evidence()
    for key, value in (("unit_id", 2), ("function_code", 4), ("base_offset", 40001)):
        weakened = copy.deepcopy(sidecar)
        weakened[key] = value
        with pytest.raises(AssertionError):
            assert_sidecar_contract(weakened, record)
    for key, value in (("unit_id", 2), ("function_code", 4), ("signature_pdu_offset", 40001)):
        other = copy.deepcopy(record)
        other["acquisition"][key] = value
        with pytest.raises(AssertionError):
            assert_sidecar_contract(sidecar, other)


def test_sidecar_header_must_be_the_first_chain_entry_of_the_record() -> None:
    sidecar = load_sidecar()
    for key, value in (("model_id", 113), ("model_length", 66), ("model_length", 64)):
        other = copy.deepcopy(load_evidence())
        other["observation"]["chain"][0][key] = value
        with pytest.raises(AssertionError):
            assert_sidecar_contract(sidecar, other)


@pytest.mark.parametrize("index", [0, 2, 3, 4, 52, 67, 68])
@pytest.mark.parametrize("value", [-1, 65536, True, False, 1.0, "1", None])
def test_sidecar_words_must_be_unsigned_16_bit_integers(index: int, value: object) -> None:
    weakened = copy.deepcopy(load_sidecar())
    weakened["registers"][index] = value
    with pytest.raises(AssertionError):
        assert_sidecar_contract(weakened, load_evidence())


def test_sidecar_registers_must_be_a_flat_list_of_words() -> None:
    sidecar = load_sidecar()
    nested = copy.deepcopy(sidecar)
    nested["registers"] = [nested["registers"]]
    with pytest.raises(AssertionError):
        assert_sidecar_contract(nested, load_evidence())
    keyed = copy.deepcopy(sidecar)
    keyed["registers"] = {"40000": 21365}
    with pytest.raises(AssertionError):
        assert_sidecar_contract(keyed, load_evidence())


def test_sidecar_parser_rejects_a_duplicate_key_bypass() -> None:
    original = SIDECAR.read_text(encoding="utf-8")
    duplicate = original.replace(
        '  "registers": [', '  "registers": [0],\n  "registers": [', 1
    )
    assert duplicate != original
    with pytest.raises(ValueError, match=r"duplicate JSON key: registers"):
        parse_public_evidence(duplicate)


@pytest.mark.parametrize("key", ["registers", "register_words", "common_block", "model_1"])
def test_record_rejects_register_words_in_any_section(key: str) -> None:
    words = load_sidecar()["registers"]
    record = load_evidence()
    for path in container_paths(record):
        weakened = copy.deepcopy(record)
        walk(weakened, path)[key] = list(words)
        with pytest.raises(AssertionError):
            assert_record_contract(weakened)


def test_record_rejects_the_whole_sidecar_and_a_word_list_in_place_of_a_value() -> None:
    sidecar = load_sidecar()
    embedded = copy.deepcopy(load_evidence())
    embedded["common_block"] = copy.deepcopy(sidecar)
    with pytest.raises(AssertionError):
        assert_record_contract(embedded)
    for path in leaf_paths(load_evidence()):
        weakened = copy.deepcopy(load_evidence())
        walk(weakened, path[:-1])[path[-1]] = list(sidecar["registers"])
        with pytest.raises(AssertionError):
            assert_record_contract(weakened)


def test_the_record_file_holds_no_run_of_register_words() -> None:
    document = EVIDENCE.read_text(encoding="utf-8")
    runs = re.findall(r"\[\s*\d+(?:\s*,\s*\d+){3,}\s*\]", document)
    assert runs == []
    assert "common-block" not in document
    assert "SunS" not in document
