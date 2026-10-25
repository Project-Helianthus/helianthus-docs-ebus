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
SIDECAR_FILE = "common-block.json"
SIDECAR_LINK = f"](../{ARTIFACT_DIR}/{SIDECAR_FILE})"
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
    # The one sidecar: Common block words only, serial field zeroed, cited and
    # bounded on the page.
    assert SIDECAR_LINK in page
    assert (FLAVOR_V12.parent / f"../{ARTIFACT_DIR}/{SIDECAR_FILE}").resolve().is_file()
    assert "this page carries no register word" in status
    assert "with no register words in `evidence.json`" in status
    assert (
        "lists the sanitized register words of the Common block (Model 1) alone, "
        "from the SunSpec signature through the device-address register, with "
        "the serial-number field zeroed and no word of any other model"
    ) in status
    assert "it names the packet's own label as its provenance reference" in status
    assert (
        "The sidecar covers Model 1 only: the other chain entries and the "
        "capability outcome are recorded as headers and outcomes without "
        "register words."
    ) in status
    assert (
        "The sanitized Common block register words in the sidecar decode to the "
        "same three strings and carry the Model 1 header `1/65`"
    ) in evidence
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


V2_HEADING = "### Registry-Selected V2 Contract Record"
V3_SUCCESSOR_HEADING = "## Registry-Selected V3 Successor"
V3_HEADING = "### Registry-Selected V3 Contract Record"
V4_SUCCESSOR_HEADING = "## Registry-Selected V4 Successor"
V4_HEADING = "### Registry-Selected V4 Contract Record"
FOLLOWING_HEADING = "## Multi-Endpoint Successor"


def runtime_sections(runtime: str) -> tuple[str, str]:
    lines = runtime.split("\n")
    v3 = lines.index(V3_SUCCESSOR_HEADING)
    v4 = lines.index(V4_SUCCESSOR_HEADING)
    following = lines.index(FOLLOWING_HEADING)
    assert v3 < v4 < following
    return "\n".join(lines[v3:v4]), "\n".join(lines[v4:following])


def test_v12_is_not_added_to_the_registry_selected_v3_record() -> None:
    runtime = text(RUNTIME)
    v3_section, v4_section = runtime_sections(runtime)
    record = json_record_after(runtime, V3_HEADING)

    # The V3 record stays closed on the two earlier identifiers; the flavor
    # 1.2.0 identifier is published only by the V4 successor record.
    assert FLAVOR_V12_ID not in v3_section
    assert record["selection"]["supported_flavors"] == [FLAVOR_V1_ID, FLAVOR_V11_ID]
    assert record["selection"]["current_live_target"] == FLAVOR_V11_ID
    assert v4_section.count(FLAVOR_V12_ID) >= 2
    assert runtime.count(FLAVOR_V12_ID) == v4_section.count(FLAVOR_V12_ID)


# Registry-selected V4 record. It pins the registry and gateway merges as bare
# commit ids, which the publication audit permits only between the
# machine-checked-record markers. These tests therefore repeat no pin: they
# read the pins from the record, check their form, their placement and their
# agreement, and derive every weakening from the parsed record.

V2_CONTRACT = "helianthus.modbus-sunspec-live-qualification.v2"
V3_CONTRACT = "helianthus.modbus-sunspec-live-qualification.v3"
V4_CONTRACT = "helianthus.modbus-sunspec-live-qualification.v4"
MARKER_START = "<!-- publication-audit: machine-checked-record start -->"
MARKER_END = "<!-- publication-audit: machine-checked-record end -->"
REGISTRY_MODULE = "github.com/Project-Helianthus/helianthus-modbusreg"
GATEWAY_MODULE = "github.com/Project-Helianthus/helianthus-ebusgateway"
COMMIT_ID = re.compile(r"[0-9a-f]{40}")
PSEUDO_VERSION = re.compile(r"v\d+\.\d+\.\d+-0\.\d{14}-(?P<revision>[0-9a-f]{12})")
V4_FLAVORS = [FLAVOR_V1_ID, FLAVOR_V11_ID, FLAVOR_V12_ID]
V4_REPLACED = ("contract", "supersedes_for_new_runs", "selection")
V4_INHERITED = [
    "activation",
    "acquisition",
    "model_123",
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
    "m5_gate",
]
V4_PROSE = [
    "adds no model-ID rule, changes no decision map",
    "V4 requires exactly one of the three closed flavor contracts to match.",
    "Zero matches is `NO_GO`; more than one match is incoherent and `STOP`.",
    "differ only in the exact Common version string, so one snapshot cannot match both.",
    "V4 does not broaden any flavor, choose one by preference order, or treat a "
    "firmware string as ordered or compatible.",
    "Both pins are bare record fields: they are not links, and no other text of "
    "this page repeats them.",
    "It publishes no live result.",
    "is not a product-family support claim",
    "does not authorize writes, automatic activation, or canonical PV publication.",
    "M5 remains blocked until the deployed exact gateway and registry combination "
    "returns `GO`.",
]


def marked_blocks(document: str) -> list[tuple[int, int]]:
    """Line pairs of the marker comments, read the way the publication audit reads them."""
    lines = document.split("\n")
    blocks: list[tuple[int, int]] = []
    start = None
    for number, raw in enumerate(lines):
        marker = raw.strip()
        if marker == MARKER_START:
            assert start is None, "nested start marker"
            start = number
        elif marker == MARKER_END:
            assert start is not None, "end marker without a start marker"
            blocks.append((start, number))
            start = None
    assert start is None, "start marker without an end marker"
    spelled = sum("machine-checked-record" in raw for raw in lines)
    assert spelled == 2 * len(blocks), "misspelled or embedded marker"
    return blocks


def record_in_block(document: str, heading: str) -> tuple[dict[str, object], int, int]:
    """The record of the first marked fence after one heading, with its marker lines."""
    lines = document.split("\n")
    assert lines.count(heading) == 1
    at = lines.index(heading)
    after = [block for block in marked_blocks(document) if block[0] > at]
    assert after
    start, end = after[0]
    assert lines[start + 1] == "```json"
    assert lines[end - 1] == "```"
    assert not any(raw.startswith("#") for raw in lines[at + 1 : end])
    assert "```" not in "\n".join(lines[at:start])
    return json.loads("\n".join(lines[start + 2 : end - 1])), start, end


def assert_v4_record(
    record: dict[str, object], v3: dict[str, object], v2: dict[str, object]
) -> None:
    keys = list(v3)
    assert keys[:3] == ["contract", "phase", "supersedes_for_new_runs"]
    assert list(record) == keys[:3] + ["registry_dependency", "gateway_dependency"] + keys[3:]
    assert record["contract"] == V4_CONTRACT
    assert record["phase"] == v3["phase"]
    assert record["supersedes_for_new_runs"] == V3_CONTRACT

    registry = record["registry_dependency"]
    assert list(registry) == ["module", "version", "merge"]
    assert registry["module"] == REGISTRY_MODULE
    assert COMMIT_ID.fullmatch(registry["merge"])
    version = PSEUDO_VERSION.fullmatch(registry["version"])
    assert version is not None
    assert version.group("revision") == registry["merge"][:12]

    gateway = record["gateway_dependency"]
    assert list(gateway) == ["module", "merge"]
    assert gateway["module"] == GATEWAY_MODULE
    assert COMMIT_ID.fullmatch(gateway["merge"])
    assert len({registry["merge"], gateway["merge"], v2["registry_dependency"]["merge"]}) == 3

    assert record["selection"] == {
        "input": "complete_terminal_verified_SunSpecChainSnapshot",
        "decoder_dispatch": "exact_registry_key",
        "capability": "sunspec.inverter.three_phase.monitoring@1.0.0",
        "supported_flavors": V4_FLAVORS,
        "required_exact_match_count": 1,
        "current_live_target": FLAVOR_V12_ID,
        "hardcoded_model_id_rules": False,
    }
    for key in keys:
        if key not in V4_REPLACED and key != "phase":
            assert record[key] == v3[key], key
    assert V4_INHERITED == [key for key in keys if key not in V4_REPLACED and key != "phase"]


def assert_v4_placement(runtime: str) -> None:
    lines = runtime.split("\n")
    blocks = marked_blocks(runtime)
    record, start, end = record_in_block(runtime, V4_HEADING)
    assert (start, end) in blocks

    order = []
    for heading in (V2_HEADING, V3_HEADING, V4_SUCCESSOR_HEADING, V4_HEADING, FOLLOWING_HEADING):
        assert lines.count(heading) == 1, heading
        order.append(lines.index(heading))
    assert order == sorted(order)
    successor = order[2]
    following = order[4]
    assert end < following

    # A commit id may appear only between markers, and each V4 pin appears
    # exactly once, in its own record, in no abbreviated form elsewhere.
    inside = {number for first, last in blocks for number in range(first + 1, last)}
    for number, raw in enumerate(lines):
        if HEX_40.search(raw):
            assert number in inside, raw
    assert not HEX_64.search(runtime)
    outside = "\n".join(lines[:start] + lines[end + 1 :])
    fence = "\n".join(lines[start + 2 : end - 1])
    revision = PSEUDO_VERSION.fullmatch(record["registry_dependency"]["version"])
    assert revision is not None
    for pin in (
        record["registry_dependency"]["merge"],
        record["gateway_dependency"]["merge"],
        revision.group("revision"),
    ):
        assert pin in fence
        assert pin not in outside

    prose = "\n".join(lines[successor:start] + lines[end + 1 : following])
    assert_publication_clean(prose)
    normalized = squash(prose)
    for phrase in V4_PROSE:
        assert phrase in normalized, phrase


def assert_v4_page(runtime: str) -> None:
    record, _, _ = record_in_block(runtime, V4_HEADING)
    assert_v4_record(
        record, json_record_after(runtime, V3_HEADING), json_record_after(runtime, V2_HEADING)
    )
    assert_v4_placement(runtime)


def test_v4_is_the_closed_successor_record_of_v3() -> None:
    runtime = text(RUNTIME)
    record, _, _ = record_in_block(runtime, V4_HEADING)
    v3 = json_record_after(runtime, V3_HEADING)

    assert_v4_page(runtime)
    assert record["selection"]["supported_flavors"] == v3["selection"]["supported_flavors"] + [
        FLAVOR_V12_ID
    ]
    assert record["support_claim"] is False
    assert record["live_result_published_here"] is False
    assert record["writes_permitted"] is False
    assert record["m5_gate"] == "BLOCKED_UNTIL_DEPLOYED_EXACT_GO"


def test_earlier_records_keep_their_form_beside_v4() -> None:
    runtime = text(RUNTIME)
    v2 = json_record_after(runtime, V2_HEADING)
    v3 = json_record_after(runtime, V3_HEADING)

    v3_section, _ = runtime_sections(runtime)
    marked_v2, _, _ = record_in_block(runtime, V2_HEADING)

    assert v2 == marked_v2
    assert v2["contract"] == V2_CONTRACT
    assert v3["contract"] == V3_CONTRACT
    assert "registry_dependency" in v2 and "registry_dependency" not in v3
    assert "gateway_dependency" not in v2 and "gateway_dependency" not in v3
    assert not HEX_40.search(v3_section)


def pin_edit(path: tuple[str, ...], change):
    def edit(record: dict[str, object], v2: dict[str, object]) -> None:
        target = record
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = change(target.get(path[-1]), record, v2)

    return edit


def drop_edit(*path: str):
    def edit(record: dict[str, object], v2: dict[str, object]) -> None:
        target = record
        for key in path[:-1]:
            target = target[key]
        del target[path[-1]]

    return edit


def value_edit(*path: str, value):
    return pin_edit(path, lambda old, record, v2: value)


def flip_last_digit(value: str) -> str:
    return value[:-1] + ("0" if value[-1] != "0" else "1")


def flip_first_digit(value: str) -> str:
    return ("0" if value[0] != "0" else "1") + value[1:]


def adopt_revision(version: str, merge: str) -> str:
    return re.sub(r"[0-9a-f]{12}$", merge[:12], version)


def reorder_edit(*keys: str):
    def edit(record: dict[str, object], v2: dict[str, object]) -> None:
        first = {key: record.pop(key) for key in keys}
        rest = dict(record)
        record.clear()
        record.update(first)
        record.update(rest)

    return edit


def registry_takes(source):
    def edit(record: dict[str, object], v2: dict[str, object]) -> None:
        merge = source(record, v2)
        registry = record["registry_dependency"]
        registry["merge"] = merge
        registry["version"] = adopt_revision(registry["version"], merge)

    return edit


def flavors_edit(change):
    return pin_edit(("selection", "supported_flavors"), lambda old, record, v2: change(list(old)))


def swapped(values: list[str], first: int, second: int) -> list[str]:
    values[first], values[second] = values[second], values[first]
    return values


V4_RECORD_EDITS = [
    # contract, supersession and phase
    pytest.param(value_edit("contract", value=V3_CONTRACT), id="contract-reuses-v3"),
    pytest.param(
        value_edit("contract", value=V4_CONTRACT[:-1] + "5"), id="contract-skips-a-version"
    ),
    pytest.param(drop_edit("contract"), id="contract-dropped"),
    pytest.param(
        value_edit("supersedes_for_new_runs", value=V2_CONTRACT), id="supersedes-v2"
    ),
    pytest.param(
        value_edit("supersedes_for_new_runs", value=V4_CONTRACT), id="supersedes-itself"
    ),
    pytest.param(value_edit("phase", value="FMV3-M4-05"), id="phase-changed"),
    # registry pin: module, version, merge
    pytest.param(drop_edit("registry_dependency"), id="registry-dependency-dropped"),
    pytest.param(
        value_edit(
            "registry_dependency", "module", value="github.com/Project-Helianthus/helianthus-modbus"
        ),
        id="registry-module-is-the-transport-library",
    ),
    pytest.param(drop_edit("registry_dependency", "module"), id="registry-module-dropped"),
    pytest.param(drop_edit("registry_dependency", "version"), id="registry-version-dropped"),
    pytest.param(
        value_edit("registry_dependency", "version", value="v0.6.7"), id="registry-version-is-a-tag"
    ),
    pytest.param(
        pin_edit(
            ("registry_dependency", "version"), lambda old, record, v2: flip_last_digit(old)
        ),
        id="registry-version-names-another-revision",
    ),
    pytest.param(
        pin_edit(
            ("registry_dependency", "version"),
            lambda old, record, v2: re.sub(r"-0\.\d{14}-", "-", old),
        ),
        id="registry-version-without-timestamp",
    ),
    pytest.param(drop_edit("registry_dependency", "merge"), id="registry-merge-dropped"),
    pytest.param(
        pin_edit(("registry_dependency", "merge"), lambda old, record, v2: old[:-1]),
        id="registry-merge-39-digits",
    ),
    pytest.param(
        pin_edit(("registry_dependency", "merge"), lambda old, record, v2: old.upper()),
        id="registry-merge-upper-case",
    ),
    pytest.param(
        pin_edit(("registry_dependency", "merge"), lambda old, record, v2: flip_first_digit(old)),
        id="registry-merge-prefix-disagrees-with-version",
    ),
    pytest.param(
        registry_takes(lambda record, v2: record["gateway_dependency"]["merge"]),
        id="registry-merge-is-the-gateway-pin",
    ),
    pytest.param(
        registry_takes(lambda record, v2: v2["registry_dependency"]["merge"]),
        id="registry-merge-is-the-v2-pin",
    ),
    pytest.param(
        value_edit("registry_dependency", "tag", value="v0.6.7"), id="registry-extra-field"
    ),
    pytest.param(
        pin_edit(
            ("registry_dependency",),
            lambda old, record, v2: {key: old[key] for key in ("merge", "version", "module")},
        ),
        id="registry-fields-reordered",
    ),
    # gateway pin: module, merge
    pytest.param(drop_edit("gateway_dependency"), id="gateway-dependency-dropped"),
    pytest.param(
        value_edit(
            "gateway_dependency", "module", value="github.com/Project-Helianthus/helianthus-ebusreg"
        ),
        id="gateway-module-is-another-repository",
    ),
    pytest.param(drop_edit("gateway_dependency", "module"), id="gateway-module-dropped"),
    pytest.param(drop_edit("gateway_dependency", "merge"), id="gateway-merge-dropped"),
    pytest.param(
        pin_edit(("gateway_dependency", "merge"), lambda old, record, v2: old[:-1]),
        id="gateway-merge-39-digits",
    ),
    pytest.param(
        pin_edit(("gateway_dependency", "merge"), lambda old, record, v2: old.upper()),
        id="gateway-merge-upper-case",
    ),
    pytest.param(
        pin_edit(("gateway_dependency", "merge"), lambda old, record, v2: "g" + old[1:]),
        id="gateway-merge-not-hex",
    ),
    pytest.param(
        pin_edit(
            ("gateway_dependency", "merge"),
            lambda old, record, v2: record["registry_dependency"]["merge"],
        ),
        id="gateway-merge-is-the-registry-pin",
    ),
    pytest.param(
        pin_edit(
            ("gateway_dependency", "merge"),
            lambda old, record, v2: v2["registry_dependency"]["merge"],
        ),
        id="gateway-merge-is-the-v2-pin",
    ),
    pytest.param(
        value_edit("gateway_dependency", "version", value="v0.6.32"), id="gateway-extra-field"
    ),
    pytest.param(
        pin_edit(
            ("gateway_dependency",),
            lambda old, record, v2: {key: old[key] for key in ("merge", "module")},
        ),
        id="gateway-fields-reordered",
    ),
    pytest.param(
        reorder_edit("gateway_dependency", "registry_dependency"), id="pins-swapped"
    ),
    pytest.param(value_edit("support_flavors", value=[]), id="unknown-top-level-field"),
    pytest.param(reorder_edit("selection"), id="selection-moved-before-the-pins"),
    # selection: every field, and each member of the closed flavor list
    pytest.param(
        value_edit("selection", "input", value="partial_snapshot"), id="selection-input-changed"
    ),
    pytest.param(
        value_edit("selection", "decoder_dispatch", value="model_id_range"),
        id="selection-dispatch-changed",
    ),
    pytest.param(
        value_edit(
            "selection", "capability", value="sunspec.inverter.three_phase.monitoring@1.1.0"
        ),
        id="selection-capability-changed",
    ),
    pytest.param(flavors_edit(lambda values: values[1:]), id="flavors-drop-1.0.0"),
    pytest.param(flavors_edit(lambda values: values[:1] + values[2:]), id="flavors-drop-1.1.0"),
    pytest.param(flavors_edit(lambda values: values[:2]), id="flavors-drop-1.2.0"),
    pytest.param(flavors_edit(lambda values: values[::-1]), id="flavors-reversed"),
    pytest.param(
        flavors_edit(lambda values: swapped(values, 0, 1)), id="flavors-first-two-swapped"
    ),
    pytest.param(flavors_edit(lambda values: values + values[-1:]), id="flavors-duplicate"),
    pytest.param(
        flavors_edit(
            lambda values: values + ["sunspec.flavor.fronius.gen24.float.observed@1.3.0"]
        ),
        id="flavors-unlisted-identifier-added",
    ),
    pytest.param(
        flavors_edit(lambda values: values[:2] + [FLAVOR_V12_ID[:-1] + "*"]),
        id="flavors-wildcard",
    ),
    pytest.param(
        flavors_edit(lambda values: values[:2] + [FLAVOR_V12_ID.upper()]),
        id="flavors-upper-case",
    ),
    pytest.param(flavors_edit(lambda values: values[2:]), id="flavors-only-1.2.0"),
    pytest.param(
        value_edit("selection", "required_exact_match_count", value=0), id="match-count-zero"
    ),
    pytest.param(
        value_edit("selection", "required_exact_match_count", value=2), id="match-count-two"
    ),
    pytest.param(
        value_edit("selection", "current_live_target", value=FLAVOR_V11_ID),
        id="live-target-stays-1.1.0",
    ),
    pytest.param(
        value_edit("selection", "current_live_target", value=FLAVOR_V1_ID),
        id="live-target-is-1.0.0",
    ),
    pytest.param(
        value_edit(
            "selection",
            "current_live_target",
            value="sunspec.flavor.fronius.gen24.float.observed@1.3.0",
        ),
        id="live-target-is-unlisted",
    ),
    pytest.param(
        value_edit("selection", "hardcoded_model_id_rules", value=True),
        id="model-id-rules-enabled",
    ),
    pytest.param(
        value_edit("selection", "fallback_flavor", value=FLAVOR_V11_ID),
        id="selection-extra-field",
    ),
    # inherited safety fields, each changed and each dropped
    *[
        pytest.param(value_edit(key, value="changed"), id=f"{key}-changed")
        for key in V4_INHERITED
    ],
    *[pytest.param(drop_edit(key), id=f"{key}-dropped") for key in V4_INHERITED],
]


@pytest.mark.parametrize("edit", V4_RECORD_EDITS)
def test_v4_record_rejects_a_weakened_record(edit) -> None:
    runtime = text(RUNTIME)
    v2 = json_record_after(runtime, V2_HEADING)
    v3 = json_record_after(runtime, V3_HEADING)
    record, _, _ = record_in_block(runtime, V4_HEADING)
    assert_v4_record(record, v3, v2)

    weakened = json.loads(json.dumps(record))
    edit(weakened, v2)
    assert json.dumps(weakened) != json.dumps(record)
    with pytest.raises(AssertionError):
        assert_v4_record(weakened, v3, v2)


def loose(phrase: str) -> re.Pattern[str]:
    return re.compile(r"\s+".join(re.escape(word) for word in phrase.split()))


def with_lines(runtime: str, change) -> str:
    lines = runtime.split("\n")
    record, start, end = record_in_block(runtime, V4_HEADING)
    change(lines, start, end, record)
    return "\n".join(lines)


def insert_after_successor_heading(extra: str):
    def change(lines: list[str], start: int, end: int, record: dict[str, object]) -> None:
        lines.insert(lines.index(V4_SUCCESSOR_HEADING) + 1, extra.format(**pins(record)))

    return change


def pins(record: dict[str, object]) -> dict[str, str]:
    registry = record["registry_dependency"]
    return {
        "registry": registry["merge"],
        "gateway": record["gateway_dependency"]["merge"],
        "revision": registry["merge"][:12],
    }


def move_following_heading(lines: list[str], start: int, end: int, record: dict) -> None:
    lines.remove(FOLLOWING_HEADING)
    lines.insert(lines.index(V4_SUCCESSOR_HEADING), FOLLOWING_HEADING)


def stray_end_marker(lines: list[str], start: int, end: int, record: dict) -> None:
    lines.insert(0, MARKER_END)


def stray_second_start(lines: list[str], start: int, end: int, record: dict) -> None:
    lines.insert(start + 1, MARKER_START)


def fence_before_marker(lines: list[str], start: int, end: int, record: dict) -> None:
    lines[start], lines[start + 1] = lines[start + 1], lines[start]


def misspell_start(lines: list[str], start: int, end: int, record: dict) -> None:
    lines[start] = lines[start].replace("record start", "records start")


def embed_start(lines: list[str], start: int, end: int, record: dict) -> None:
    lines[start] = "prose " + lines[start]


def embed_extra_end(lines: list[str], start: int, end: int, record: dict) -> None:
    lines.insert(end + 2, "prose " + MARKER_END)


def drop_line(which: str):
    def change(lines: list[str], start: int, end: int, record: dict) -> None:
        targets = {"start": [start], "end": [end], "both": [start, end]}[which]
        for number in sorted(targets, reverse=True):
            del lines[number]

    return change


def pin_in_heading(lines: list[str], start: int, end: int, record: dict) -> None:
    lines.insert(end + 2, f"### Pin {pins(record)['gateway']}")


V4_PAGE_EDITS = [
    pytest.param(drop_line("start"), id="start-marker-dropped"),
    pytest.param(drop_line("end"), id="end-marker-dropped"),
    pytest.param(drop_line("both"), id="markers-dropped-pins-unprotected"),
    pytest.param(stray_second_start, id="start-marker-nested"),
    pytest.param(stray_end_marker, id="end-marker-without-start"),
    pytest.param(misspell_start, id="marker-misspelled"),
    pytest.param(embed_start, id="marker-embedded-in-prose"),
    pytest.param(embed_extra_end, id="extra-marker-embedded-after-the-record"),
    pytest.param(fence_before_marker, id="marker-not-adjacent-to-the-fence"),
    pytest.param(move_following_heading, id="record-after-the-next-section"),
    pytest.param(pin_in_heading, id="pin-in-a-heading"),
    pytest.param(
        insert_after_successor_heading("\nThe registry merge is {registry}."),
        id="registry-pin-in-prose",
    ),
    pytest.param(
        insert_after_successor_heading("\nThe gateway merge is {gateway}."),
        id="gateway-pin-in-prose",
    ),
    pytest.param(
        insert_after_successor_heading("\nThe registry revision is {revision}."),
        id="abbreviated-pin-in-prose",
    ),
    pytest.param(
        insert_after_successor_heading(
            "\n[merge](https://example.invalid/helianthus/commit/{gateway})"
        ),
        id="pin-in-a-link",
    ),
]


@pytest.mark.parametrize("change", V4_PAGE_EDITS)
def test_v4_record_rejects_a_weakened_page(change) -> None:
    runtime = text(RUNTIME)
    assert_v4_page(runtime)
    weakened = with_lines(runtime, change)
    assert weakened != runtime
    with pytest.raises(AssertionError):
        assert_v4_page(weakened)


def edit_v4_section(runtime: str, pattern: re.Pattern[str], replacement: str) -> str:
    _, section_v4 = runtime_sections(runtime)
    assert len(pattern.findall(section_v4)) == 1
    assert runtime.count(section_v4) == 1
    return runtime.replace(section_v4, pattern.sub(replacement, section_v4))


@pytest.mark.parametrize("phrase", V4_PROSE)
def test_v4_record_rejects_a_dropped_prose_clause(phrase: str) -> None:
    runtime = text(RUNTIME)
    weakened = edit_v4_section(runtime, loose(phrase), "")
    assert weakened != runtime
    with pytest.raises(AssertionError):
        assert_v4_page(weakened)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("exactly one of the three closed flavor contracts", "at least one of the three closed flavor contracts"),
        ("Zero matches is `NO_GO`", "Zero matches is `GO`"),
        ("more than one match is incoherent and `STOP`", "more than one match is incoherent and `GO`"),
        ("is not a product-family support claim", "is a product-family support claim"),
        ("M5 remains blocked until", "M5 is open once"),
        ("It publishes no live result.", "It publishes the live result."),
        ("so one snapshot cannot match both", "so one snapshot can match both"),
    ],
)
def test_v4_record_rejects_a_reversed_prose_clause(before: str, after: str) -> None:
    runtime = text(RUNTIME)
    weakened = edit_v4_section(runtime, loose(before), after)
    assert weakened != runtime
    with pytest.raises(AssertionError):
        assert_v4_page(weakened)


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
    [
        "overview",
        "chain_doc",
        "platform_index",
        "page_link",
        "page_claim",
        "sidecar_link",
        "sidecar_scope",
        "sidecar_serial",
        "sidecar_decoding",
    ],
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
    elif field == "sidecar_link":
        weakened = docs._replace(
            page=replace_once(docs.page, SIDECAR_LINK, "](../docs/platform/live/removed.json)")
        )
    elif field == "sidecar_scope":
        weakened = docs._replace(
            page=re.sub(r"\s+and\s+no\s+word\s+of\s+any\s+other\s+model", "", docs.page, count=1)
        )
    elif field == "sidecar_serial":
        weakened = docs._replace(
            page=re.sub(r"with\s+the\s+serial-number\s+field\s+zeroed", "as captured", docs.page, count=1)
        )
    elif field == "sidecar_decoding":
        weakened = docs._replace(
            page=re.sub(
                r"The\s+sanitized\s+Common\s+block\s+register\s+words\s+in\s+the\s+sidecar",
                "A summary of the sidecar",
                docs.page,
                count=1,
            )
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
