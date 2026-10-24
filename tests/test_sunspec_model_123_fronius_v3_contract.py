from __future__ import annotations

import json
import re
from pathlib import Path
from typing import NamedTuple

import pytest


ROOT = Path(__file__).resolve().parents[1]
CHAIN = ROOT / "architecture/protocol-routing-vendor-sunspec-model-chain-v1.md"
FLAVOR_V1 = ROOT / "architecture/protocol-routing-vendor-fronius-observed-flavor-v1.md"
FLAVOR_V11 = ROOT / "architecture/protocol-routing-vendor-fronius-observed-flavor-v1-1.md"
FLAVOR_V12 = ROOT / "architecture/protocol-routing-vendor-fronius-observed-flavor-v1-2.md"
PLATFORM_INDEX = ROOT / "docs/platform/README.md"
RUNTIME = ROOT / "api/modbus-v1-addon-runtime.md"
README = ROOT / "architecture/protocol-routing-vendor-sunspec-overview.md"

FLAVOR_V1_ID = "sunspec.flavor.fronius.gen24.float.observed@1.0.0"
FLAVOR_V11_ID = "sunspec.flavor.fronius.gen24.float.observed@1.1.0"
FLAVOR_V12_ID = "sunspec.flavor.fronius.gen24.float.observed@1.2.0"
OLD_CHAIN = "1/65, 113/60, 120/26, 121/30, 122/44, 160/88, 124/24, FFFF/0"
CONTROLS_CHAIN = (
    "1/65, 113/60, 120/26, 121/30, 122/44, 123/24, 160/88, 124/24, FFFF/0"
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def json_record_after(document: str, heading: str) -> dict[str, object]:
    section = document[document.index(heading) :]
    match = re.search(r"```json\n(.*?)\n```", section, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))


def test_model_123_is_standard_exact_read_only_core() -> None:
    contract = text(CHAIN)
    normalized = " ".join(contract.split())

    assert "Model `123`, Immediate Controls: `L24`" in contract
    assert "(123, 24, schema_revision)" in contract
    assert "standard SunSpec core" in normalized
    assert "read-only decoder" in normalized
    assert "RW metadata" in normalized
    assert "creates no write authority" in normalized
    assert "vendor custom model" in normalized


def test_old_flavor_is_immutable_and_new_flavor_is_exact() -> None:
    old = text(FLAVOR_V1)
    new = text(FLAVOR_V11)
    normalized = " ".join(new.lower().split())

    assert FLAVOR_V1_ID in old
    assert OLD_CHAIN in old
    assert CONTROLS_CHAIN not in old

    for value in (
        FLAVOR_V11_ID,
        FLAVOR_V1_ID,
        CONTROLS_CHAIN,
        "Fronius",
        "Symo GEN24 10.0",
        "1.41.11-1",
        "Model `123/L24`",
        "Immediate Controls",
        "81e18e67a1b7d1adff5273c8c43f08243a3e2a0a",
        "CHAIN_MISMATCH",
    ):
        assert value in new
    for phrase in (
        "does not reinterpret",
        "exact ordered chain",
        "standard model",
        "read-only",
        "no write authority",
        "not a product-family support claim",
    ):
        assert phrase in normalized


def test_v3_selects_one_closed_registry_flavor_and_keeps_m5_blocked() -> None:
    runtime = text(RUNTIME)
    v2 = json_record_after(runtime, "### Registry-Selected V2 Contract Record")
    record = json_record_after(runtime, "### Registry-Selected V3 Contract Record")

    assert record["contract"] == "helianthus.modbus-sunspec-live-qualification.v3"
    assert record["supersedes_for_new_runs"] == (
        "helianthus.modbus-sunspec-live-qualification.v2"
    )
    assert record["selection"] == {
        "input": "complete_terminal_verified_SunSpecChainSnapshot",
        "decoder_dispatch": "exact_registry_key",
        "capability": "sunspec.inverter.three_phase.monitoring@1.0.0",
        "supported_flavors": [FLAVOR_V1_ID, FLAVOR_V11_ID],
        "required_exact_match_count": 1,
        "current_live_target": FLAVOR_V11_ID,
        "hardcoded_model_id_rules": False,
    }
    assert record["model_123"] == {
        "decoder_key": [123, 24, "sunspec.models@7abdf898-v1"],
        "ownership": "standard_sunspec_core",
        "access": "read_only_decode",
        "writes_permitted": False,
    }
    assert record["go_authority"] == "qualification_evidence_only"
    assert record["support_claim"] is False
    assert record["writes_permitted"] is False
    assert record["m5_gate"] == "BLOCKED_UNTIL_DEPLOYED_EXACT_GO"

    for inherited in (
        "activation",
        "acquisition",
        "decision_precedence",
        "capability_decision_map",
        "flavor_decision_map",
        "runtime_or_transport_error",
        "recovery",
        "result",
        "shutdown",
        "go_authority",
        "support_claim",
        "live_result_published_here",
        "writes_permitted",
    ):
        assert record[inherited] == v2[inherited]


def test_new_flavor_is_indexed_without_replacing_v1() -> None:
    index = text(README)
    assert "fronius-observed-flavor-v1.md" in index
    assert "fronius-observed-flavor-v1-1.md" in index


# Flavor 1.2.0 contract. The parser reads the exact admission tuple out of a
# flavor page, so one function serves every flavor page and the weakening
# cases below can edit exactly the span that carries each identity field.

V1_FIRMWARE = "1.41.11-1"
V12_FIRMWARE = "1.42.9-1"
V12_CHAIN_ENTRIES = [
    (1, 65),
    (113, 60),
    (120, 26),
    (121, 30),
    (122, 44),
    (123, 24),
    (160, 88),
    (124, 24),
    (0xFFFF, 0),
]
FLAVOR_REASONS = [
    "CAPABILITY_NOT_ADMITTED",
    "COMMON_IDENTITY_MISMATCH",
    "FIRMWARE_MISMATCH",
    "CHAIN_MISMATCH",
    "AMBIGUOUS_SOURCE",
    "MATCHED",
]
FORBIDDEN_COMPARISONS = [
    "case folding",
    "trimming",
    "prefix match",
    "semantic-version range",
    '"at least" or "newer than" comparison',
    "model-ID-only fallback",
    "reordering",
    "subset match",
    "optional insertion",
    "int+SF substitution",
]
MATCH_RULE = "exact string match"
ARTIFACT_DIR = "docs/platform/live/fronius-observed-flavor-1.2.0"
ARTIFACT_LINK = f"](../{ARTIFACT_DIR}/)"
V12_PAGE_LINK = "(protocol-routing-vendor-fronius-observed-flavor-v1-2.md)"
PLATFORM_ENTRY_LINK = "(./live/fronius-observed-flavor-1.2.0/)"

ADMISSION_GATES = re.compile(
    r"^- Common manufacturer: `(?P<manufacturer>[^`]*)`, (?P<manufacturer_rule>[^;]*);\n"
    r"- Common model: `(?P<model>[^`]*)`, (?P<model_rule>[^;]*);\n"
    r"- Common version/firmware: `(?P<firmware>[^`]*)`, (?P<firmware_rule>[^;]*);\n"
    r"- exact ordered chain match:\s+`(?P<chain>[^`]*)`;\n"
    r"- exactly one admitted Model `(?P<source>[^`]*)` source",
    re.MULTILINE,
)
MUTUAL_EXCLUSION = re.compile(
    r"^- (V1(?:\.[12])?) (?:remains|is) exact for firmware `([^`]+)` and\s+"
    r"(`[^`]+`|the same ordered chain as V1\.1)[;.]$",
    re.MULTILINE,
)
COMPARISONS = re.compile(
    r"There is no (?P<kinds>[^.]*)\.\s+Firmware\s+strings\s+are\s+compared,\s+never\s+ordered"
)
REASON_LIST = re.compile(
    r"closed reasons and precedence of V1 and V1\.1:\s+(?P<reasons>[^.]*)\.\s+A snapshot"
)
HEX_40 = re.compile(r"\b[0-9a-f]{40}\b")
HEX_64 = re.compile(r"\b[0-9a-f]{64}\b")
PINNED_LINK = re.compile(r"/(?:blob|tree|commits?)/[0-9a-f]{7,40}\b")
LINE_ANCHOR = re.compile(r"#L\d")
BARRED_WORDS = re.compile(r"\b(?:led" r"ger)\b|-cur" r"rent\b", re.IGNORECASE)


class Docs(NamedTuple):
    page: str
    flavor_v11: str
    overview: str
    chain_doc: str
    platform_index: str


def load_docs() -> Docs:
    return Docs(
        page=text(FLAVOR_V12),
        flavor_v11=text(FLAVOR_V11),
        overview=text(README),
        chain_doc=text(CHAIN),
        platform_index=text(PLATFORM_INDEX),
    )


def parse_chain(chain: str) -> list[tuple[int, int]]:
    entries: list[tuple[int, int]] = []
    for item in chain.split(", "):
        match = re.fullmatch(r"(\d+|FFFF)/(\d+)", item)
        assert match is not None, item
        model_id = 0xFFFF if match.group(1) == "FFFF" else int(match.group(1))
        entries.append((model_id, int(match.group(2))))
    return entries


def section(page: str, heading: str) -> str:
    assert heading in page, heading
    start = page.index(heading)
    following = page.find("\n## ", start + len(heading))
    return page[start : following if following != -1 else len(page)]


def squash(value: str) -> str:
    return " ".join(value.split())


def admission_gates(page: str) -> dict[str, object]:
    match = ADMISSION_GATES.search(section(page, "## Exact admission tuple"))
    assert match is not None
    gates: dict[str, object] = dict(match.groupdict())
    gates["entries"] = parse_chain(match.group("chain"))
    return gates


def assert_publication_clean(value: str) -> None:
    assert not HEX_40.search(value)
    assert not HEX_64.search(value)
    assert not PINNED_LINK.search(value)
    assert not LINE_ANCHOR.search(value)
    assert not BARRED_WORDS.search(value)


def assert_v12_contract(docs: Docs) -> None:
    page = docs.page
    status = squash(section(page, "## Status and evidence boundary"))
    evidence = squash(section(page, "## Evidence status"))
    admission = squash(section(page, "## Exact admission tuple"))
    outcomes = squash(section(page, "## Outcomes and ownership"))
    whole = squash(page)

    # Flavor identifier and lineage.
    assert page.startswith("# Fronius Observed SunSpec Flavor V1.2\n")
    assert (
        f"`{FLAVOR_V12_ID}` is an experimental, read-only successor to "
        f"`{FLAVOR_V11_ID}` and `{FLAVOR_V1_ID}`. It does not reinterpret "
        "either earlier contract."
    ) in status
    assert "Each identifier admits only its own exact Common identity tuple" in status
    assert "It is not a product-family support claim" in status
    assert (
        "correctly returned `FIRMWARE_MISMATCH`: manufacturer and model "
        "matched, and the version string did not."
    ) in status

    # Exact tuple: Common Mn, Md, Vr plus the ordered chain and one 113/L60.
    gates = admission_gates(page)
    assert gates["manufacturer"] == "Fronius"
    assert gates["model"] == "Symo GEN24 10.0"
    assert gates["firmware"] == V12_FIRMWARE
    assert gates["manufacturer_rule"] == MATCH_RULE
    assert gates["model_rule"] == MATCH_RULE
    assert gates["firmware_rule"] == MATCH_RULE
    assert gates["chain"] == CONTROLS_CHAIN
    assert gates["entries"] == V12_CHAIN_ENTRIES
    assert gates["source"] == "113/L60"
    reference = admission_gates(docs.flavor_v11)
    assert reference["firmware"] == V1_FIRMWARE
    assert gates["entries"] == reference["entries"]
    assert gates["manufacturer"] == reference["manufacturer"]
    assert gates["model"] == reference["model"]
    assert gates["firmware"] != reference["firmware"]
    assert "requires all of these independent exact gates" in admission
    assert "The identity tuple contains exactly Common `Mn`, `Md`, and `Vr`." in admission
    assert "Common `SN`, `Opt`, and `DA`" in admission
    assert "are not matching inputs" in admission
    assert "exact core decoder key `(123, 24, schema_revision)`" in admission

    # No range, ordering or fallback.
    comparisons = COMPARISONS.search(admission)
    assert comparisons is not None
    for kind in FORBIDDEN_COMPARISONS:
        assert kind in comparisons.group("kinds"), kind
    assert (
        f"`{V12_FIRMWARE}` is not treated as an upgrade of, or as compatible "
        f"with, `{V1_FIRMWARE}`, and neither string admits the other."
    ) in admission
    assert (
        "A firmware string that a flavor does not list fails closed with "
        "`FIRMWARE_MISMATCH` for that flavor"
    ) in admission

    # The three identifiers stay mutually exclusive.
    assert MUTUAL_EXCLUSION.findall(section(page, "## Exact admission tuple")) == [
        ("V1", V1_FIRMWARE, f"`{OLD_CHAIN}`"),
        ("V1.1", V1_FIRMWARE, f"`{CONTROLS_CHAIN}`"),
        ("V1.2", V12_FIRMWARE, "the same ordered chain as V1.1"),
    ]
    assert (
        "V1.1 and V1.2 share one ordered chain and differ only in the exact "
        "Common version string, so no snapshot can match both."
    ) in admission

    # Evidence labels and the retained detector hypothesis.
    labels = [
        evidence.index(label)
        for label in ("`Proven`, established by", "`Hypothesis`:", "`Unknown`:")
    ]
    assert labels == sorted(labels)
    assert (
        f"Common `Mn`, `Md`, and `Vr` decoded to `Fronius`, `Symo GEN24 10.0`, "
        f"and `{V12_FIRMWARE}`."
    ) in evidence
    assert f"found, in order, `{CONTROLS_CHAIN}`." in evidence
    assert "That chain equals the V1.1 chain entry for entry and in order." in evidence
    assert "from exactly one `113/L60` source" in evidence
    assert (
        "FC03 holding-register reads only, unit ID `1`, and normalized PDU "
        "offset `40000`"
    ) in evidence
    assert "No write of any kind was performed." in evidence
    assert "(`FSS-C-007`)" in evidence
    assert "It stays forbidden from production use" in evidence
    assert "this contract admits one exact tuple, not a detector, a series, or a range" in evidence

    # Closed fail-closed outcomes, in the published precedence order.
    reasons = REASON_LIST.search(outcomes)
    assert reasons is not None
    assert re.findall(r"`([A-Z_]+)`", reasons.group("reasons")) == FLAVOR_REASONS
    assert (
        "A snapshot whose manufacturer and model match but whose version is "
        "any other string yields `FIRMWARE_MISMATCH` before the chain is "
        "compared, without partial flavor facts."
    ) in outcomes
    assert (
        "A mismatch never rewrites or drops raw model occurrences, canonical "
        "capability facts, or acquisition provenance"
    ) in outcomes
    assert "does not select a transport, construct a request" in outcomes
    assert "the flavor has no semantic override, custom model, extension fact, or write path" in outcomes
    assert "It creates no write authority," in outcomes
    assert "or automatic support declaration" in outcomes
    assert "is not a product-family support claim" in outcomes
    assert "This page adds the identifier to no live-qualification record." in outcomes

    # The sanitized observation record and the index links.
    assert "That record is the falsifiable artifact for the `Proven` labels below" in status
    assert ARTIFACT_LINK in page
    assert (FLAVOR_V12.parent / f"../{ARTIFACT_DIR}").resolve().is_dir()
    assert f"]{V12_PAGE_LINK}" in docs.overview
    assert f"]{V12_PAGE_LINK}" in docs.chain_doc
    assert (FLAVOR_V12.parent / V12_PAGE_LINK.strip("()")).is_file()
    assert "does not replace or widen V1 or V1.1" in squash(docs.overview)
    assert "does not reinterpret or widen V1 or V1.1" in squash(docs.chain_doc)
    assert PLATFORM_ENTRY_LINK in docs.platform_index
    assert_publication_clean(whole)


def replace_once(value: str, before: str, after: str) -> str:
    assert value.count(before) == 1, before
    return value.replace(before, after)


def with_chain(page: str, chain: str) -> str:
    return replace_once(
        page,
        f"- exact ordered chain match:\n  `{CONTROLS_CHAIN}`;",
        f"- exact ordered chain match:\n  `{chain}`;",
    )


def chain_variants() -> list[tuple[str, str]]:
    entries = CONTROLS_CHAIN.split(", ")
    variants: list[tuple[str, str]] = []
    for index, entry in enumerate(entries):
        model_id, length = entry.split("/")
        label = f"{index}-{entry.replace('/', 'of')}"
        other_id = "FFFE" if model_id == "FFFF" else str(int(model_id) + 1)
        variants.append((f"id-{label}", ", ".join(
            entries[:index] + [f"{other_id}/{length}"] + entries[index + 1 :]
        )))
        variants.append((f"length-{label}", ", ".join(
            entries[:index] + [f"{model_id}/{int(length) + 1}"] + entries[index + 1 :]
        )))
        variants.append((f"dropped-{label}", ", ".join(entries[:index] + entries[index + 1 :])))
        if index + 1 < len(entries):
            swapped = list(entries)
            swapped[index], swapped[index + 1] = swapped[index + 1], swapped[index]
            variants.append((f"swapped-{label}", ", ".join(swapped)))
    variants.append(("extra-tail-entry", ", ".join(entries + ["999/1"])))
    variants.append(("lower-case-terminal", CONTROLS_CHAIN.replace("FFFF", "ffff")))
    variants.append(("old-chain", OLD_CHAIN))
    return variants


MANUFACTURER_GATE = "- Common manufacturer: `Fronius`, exact string match;"
MODEL_GATE = "- Common model: `Symo GEN24 10.0`, exact string match;"
FIRMWARE_GATE = "- Common version/firmware: `1.42.9-1`, exact string match;"
SOURCE_GATE = "- exactly one admitted Model `113/L60` source for the required capability\n  facts."


def gate_edit(gate: str, before: str, after: str) -> tuple[str, str]:
    assert before in gate
    return gate, gate.replace(before, after)


# Each case edits the one span that carries the named field on the page.
PAGE_EDITS = [
    pytest.param(
        f"`{FLAVOR_V12_ID}` is an experimental",
        f"`{FLAVOR_V11_ID}` is an experimental",
        id="flavor-id-reuses-v1.1",
    ),
    pytest.param(
        FLAVOR_V12_ID, FLAVOR_V12_ID[:-1] + "1", id="flavor-id-patch-changed"
    ),
    pytest.param(
        *gate_edit(MANUFACTURER_GATE, "`Fronius`", "`fronius`"), id="manufacturer-case-folded"
    ),
    pytest.param(
        *gate_edit(MANUFACTURER_GATE, "`Fronius`", "`Fronius AG`"), id="manufacturer-extended"
    ),
    pytest.param(
        *gate_edit(MANUFACTURER_GATE, MATCH_RULE, "prefix match"), id="manufacturer-prefix-rule"
    ),
    pytest.param(
        *gate_edit(MODEL_GATE, "`Symo GEN24 10.0`", "`Symo GEN24 8.0`"), id="model-other-size"
    ),
    pytest.param(*gate_edit(MODEL_GATE, " 10.0`", "`"), id="model-truncated"),
    pytest.param(*gate_edit(MODEL_GATE, MATCH_RULE, "prefix match"), id="model-prefix-rule"),
    pytest.param(
        *gate_edit(FIRMWARE_GATE, "`1.42.9-1`", "`1.41.11-1`"), id="firmware-reverts-to-v1.1"
    ),
    pytest.param(
        *gate_edit(FIRMWARE_GATE, "`1.42.9-1`", "`1.42.9`"), id="firmware-drops-build-suffix"
    ),
    pytest.param(
        *gate_edit(FIRMWARE_GATE, "`1.42.9-1`", "`1.42.9-2`"), id="firmware-bumps-build-suffix"
    ),
    pytest.param(
        *gate_edit(FIRMWARE_GATE, "`1.42.9-1`", "`1.42.*`"), id="firmware-wildcard"
    ),
    pytest.param(
        *gate_edit(FIRMWARE_GATE, "`1.42.9-1`", "`>=1.42.9-1`"), id="firmware-lower-bound"
    ),
    pytest.param(
        *gate_edit(FIRMWARE_GATE, MATCH_RULE, "prefix match"), id="firmware-prefix-rule"
    ),
    pytest.param(
        *gate_edit(SOURCE_GATE, "exactly one", "at least one"), id="source-at-least-one"
    ),
    pytest.param(*gate_edit(SOURCE_GATE, "`113/L60`", "`113/L61`"), id="source-other-length"),
    pytest.param(*gate_edit(SOURCE_GATE, "`113/L60`", "`103/L50`"), id="source-other-model"),
    pytest.param(
        "and\n  `1.42.9-1`. The fixed-width",
        "and\n  `1.41.11-1`. The fixed-width",
        id="proven-firmware-reverts",
    ),
    pytest.param(
        f"found, in order,\n  `{CONTROLS_CHAIN}`.",
        f"found, in order,\n  `{OLD_CHAIN}`.",
        id="proven-chain-drops-model-123",
    ),
    pytest.param(
        f"- V1.1 remains exact for firmware `{V1_FIRMWARE}` and\n  `{CONTROLS_CHAIN}`;",
        f"- V1.1 remains exact for firmware `{V12_FIRMWARE}` and\n  `{CONTROLS_CHAIN}`;",
        id="exclusion-v1.1-firmware-changed",
    ),
    pytest.param(
        f"- V1.1 remains exact for firmware `{V1_FIRMWARE}` and\n  `{CONTROLS_CHAIN}`;",
        f"- V1.1 remains exact for firmware `{V1_FIRMWARE}` and\n  `{OLD_CHAIN}`;",
        id="exclusion-v1.1-chain-changed",
    ),
    pytest.param(
        f"- V1 remains exact for firmware `{V1_FIRMWARE}` and\n  `{OLD_CHAIN}`;",
        f"- V1 remains exact for firmware `{V1_FIRMWARE}` and\n  `{CONTROLS_CHAIN}`;",
        id="exclusion-v1-chain-changed",
    ),
    pytest.param(
        f"- V1.2 is exact for firmware `{V12_FIRMWARE}` and the same",
        f"- V1.2 is exact for firmware `{V1_FIRMWARE}` and the same",
        id="exclusion-v1.2-firmware-changed",
    ),
    pytest.param(
        "so no snapshot can match both", "so a snapshot can match both",
        id="exclusion-claim-reversed",
    ),
    pytest.param(
        "It stays\n  forbidden from production use", "It is\n  allowed in production use",
        id="detector-allowed-in-production",
    ),
    pytest.param(
        "It creates no write authority,", "It creates write authority,",
        id="write-authority-created",
    ),
    pytest.param(
        "is not a\nproduct-family support claim and does not infer",
        "is a\nproduct-family support claim and does not infer",
        id="support-claim-made",
    ),
    pytest.param(
        "This page adds the identifier to no live-qualification record.",
        "This page adds the identifier to the live-qualification record.",
        id="qualification-record-amended",
    ),
]


def drop_reason(reason: str) -> str:
    docs = load_docs()
    match = REASON_LIST.search(docs.page)
    assert match is not None
    kept = [r for r in re.findall(r"`([A-Z_]+)`", match.group("reasons")) if r != reason]
    assert len(kept) == len(FLAVOR_REASONS) - 1
    return (
        docs.page[: match.start("reasons")]
        + ", ".join(f"`{r}`" for r in kept)
        + docs.page[match.end("reasons") :]
    )


def swap_reasons(first: str, second: str) -> str:
    docs = load_docs()
    match = REASON_LIST.search(docs.page)
    assert match is not None
    swapped = [
        second if r == first else first if r == second else r
        for r in re.findall(r"`([A-Z_]+)`", match.group("reasons"))
    ]
    return (
        docs.page[: match.start("reasons")]
        + ", ".join(f"`{r}`" for r in swapped)
        + docs.page[match.end("reasons") :]
    )


def drop_comparison(kind: str) -> str:
    page = load_docs().page
    match = COMPARISONS.search(page)
    assert match is not None
    kinds = squash(match.group("kinds"))
    assert kind in kinds
    return (
        page[: match.start("kinds")]
        + kinds.replace(kind, "")
        + page[match.end("kinds") :]
    )


def test_v12_contract_matches_the_repository_pages() -> None:
    assert_v12_contract(load_docs())


def test_v12_is_not_added_to_the_registry_selected_v3_record() -> None:
    runtime = text(RUNTIME)
    record = json_record_after(runtime, "### Registry-Selected V3 Contract Record")

    assert FLAVOR_V12_ID not in runtime
    assert record["selection"]["supported_flavors"] == [FLAVOR_V1_ID, FLAVOR_V11_ID]


@pytest.mark.parametrize(("before", "after"), PAGE_EDITS)
def test_v12_contract_rejects_a_weakened_page(before: str, after: str) -> None:
    docs = load_docs()
    weakened = docs._replace(page=replace_once(docs.page, before, after))
    assert weakened.page != docs.page
    with pytest.raises(AssertionError):
        assert_v12_contract(weakened)


@pytest.mark.parametrize(
    "chain", [variant for _, variant in chain_variants()],
    ids=[name for name, _ in chain_variants()],
)
def test_v12_contract_rejects_any_edit_of_the_admission_chain(chain: str) -> None:
    docs = load_docs()
    assert chain != CONTROLS_CHAIN
    weakened = docs._replace(page=with_chain(docs.page, chain))
    with pytest.raises(AssertionError):
        assert_v12_contract(weakened)


@pytest.mark.parametrize("reason", FLAVOR_REASONS)
def test_v12_contract_rejects_a_dropped_outcome_reason(reason: str) -> None:
    docs = load_docs()
    weakened = docs._replace(page=drop_reason(reason))
    assert weakened.page != docs.page
    with pytest.raises(AssertionError):
        assert_v12_contract(weakened)


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("FIRMWARE_MISMATCH", "CHAIN_MISMATCH"),
        ("COMMON_IDENTITY_MISMATCH", "FIRMWARE_MISMATCH"),
        ("CAPABILITY_NOT_ADMITTED", "AMBIGUOUS_SOURCE"),
        ("AMBIGUOUS_SOURCE", "MATCHED"),
    ],
)
def test_v12_contract_rejects_reordered_outcome_precedence(first: str, second: str) -> None:
    docs = load_docs()
    weakened = docs._replace(page=swap_reasons(first, second))
    assert weakened.page != docs.page
    with pytest.raises(AssertionError):
        assert_v12_contract(weakened)


def test_v12_contract_rejects_firmware_mismatch_after_the_chain() -> None:
    docs = load_docs()
    reordered = re.sub(
        r"(yields\s+)`FIRMWARE_MISMATCH`(\s+before the chain)",
        r"\1`CHAIN_MISMATCH`\2",
        docs.page,
    )
    assert reordered != docs.page
    with pytest.raises(AssertionError):
        assert_v12_contract(docs._replace(page=reordered))


def test_v12_contract_rejects_partial_flavor_facts() -> None:
    docs = load_docs()
    partial = re.sub(r",\s+without partial flavor facts", "", docs.page)
    assert partial != docs.page
    with pytest.raises(AssertionError):
        assert_v12_contract(docs._replace(page=partial))


@pytest.mark.parametrize("kind", FORBIDDEN_COMPARISONS)
def test_v12_contract_rejects_a_dropped_comparison_prohibition(kind: str) -> None:
    docs = load_docs()
    weakened = docs._replace(page=drop_comparison(kind))
    assert weakened.page != docs.page
    with pytest.raises(AssertionError):
        assert_v12_contract(weakened)


@pytest.mark.parametrize(
    "field",
    ["overview", "chain_doc", "platform_index", "page_link", "page_claim"],
)
def test_v12_contract_rejects_missing_index_links(field: str) -> None:
    docs = load_docs()
    if field == "overview":
        weakened = docs._replace(overview=replace_once(docs.overview, V12_PAGE_LINK, "(removed.md)"))
    elif field == "chain_doc":
        weakened = docs._replace(chain_doc=replace_once(docs.chain_doc, V12_PAGE_LINK, "(removed.md)"))
    elif field == "platform_index":
        weakened = docs._replace(
            platform_index=replace_once(docs.platform_index, PLATFORM_ENTRY_LINK, "(./live/removed/)")
        )
    elif field == "page_link":
        weakened = docs._replace(
            page=replace_once(docs.page, ARTIFACT_LINK, "](../docs/platform/live/removed/)")
        )
    else:
        weakened = docs._replace(
            page=re.sub(r"the\s+falsifiable artifact", "an informal note", docs.page, count=1)
        )
    assert weakened != docs
    with pytest.raises(AssertionError):
        assert_v12_contract(weakened)


def publication_probes() -> dict[str, str]:
    digest = "0123456789abcdef"
    return {
        "forty-hex-id": "reviewed " + digest * 2 + digest[:8],
        "sixty-four-hex-digest": "digest " + digest * 4,
        "pinned-blob-link": "see /blob/" + digest[:12] + "/page.md",
        "line-anchor": "see page.md#L12",
        "barred-word": "the led" + "ger",
        "barred-suffix": "the x-cur" + "rent record",
    }


@pytest.mark.parametrize("name", sorted(publication_probes()))
def test_v12_contract_rejects_unpublishable_text(name: str) -> None:
    docs = load_docs()
    probe = publication_probes()[name]
    weakened = docs._replace(page=docs.page + "\n" + probe + "\n")
    with pytest.raises(AssertionError):
        assert_v12_contract(weakened)
