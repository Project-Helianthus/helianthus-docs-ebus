"""Contract checks for the B509 OP59 quantity-view helper.

The checks lock the architecture page and the owned fixture. They do not
import an implementation. Numeric expectations are computed here from the
raw octets and compared with literals, so a byte-for-byte file compare is
not the acceptance check.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "architecture" / "an10_b509_quantity_views.md"
FIXTURE = ROOT / "architecture" / "fixtures" / "an10_b509_quantity_views.json"

SELECTION_AXES = ("family", "variant", "operation", "direction")
SLICE_AXES = (
    "temperature",
    "flow",
    "volume",
    "minimum_volume",
    "maximum_volume",
)
CONVERTIBLE = {
    "temperature": ("signed", 16, "°C"),
    "flow": ("unsigned", 100, "L/min"),
    "volume": ("unsigned", 10, "L"),
}
OPAQUE = ("minimum_volume", "maximum_volume")
ADMITTED_DIRECTIONS = ("request", "response")
UNKNOWNS = (
    "absolute positions",
    "omitted family variants",
    "raw sentinels",
    "peer bounds",
    "minimum and maximum conversion",
    "physical support",
    "actuation",
)
REQUIRED_SENTENCES = (
    "view = ab09an09.view_b509_op59_candidate_fields(selection, slices)",
    "The helper does not parse a packet.",
    "The helper does not detect a family from a byte offset or from a slice length.",
    "Nothing in this contract is stable before Helianthus 1.0.",
    "This page creates no namespace.",
    "This page adds no authorization gate.",
    "Roadmap wording remains 0.11.",
    "The helper registers no write builder and no registry method.",
    "This helper adds no GraphQL field and no MCP tool.",
    "Semantic grade remains Hypothesis and native grade remains Unknown on every field, including absent, malformed, raw, and withheld fields.",
    "Omitted family, variant, operation, and direction stay omitted.",
    "Temperature, flow, and volume use little-endian byte order.",
    "Applying a unit label as a second scale is outside this contract.",
    "Dividing temperature by 256 is outside this contract.",
    "Signed flow is outside this contract.",
    "Signed volume is outside this contract.",
    "Converting minimum volume or maximum volume is outside this contract.",
    "Assigning a missing sentinel to temperature 00 80 is outside this contract.",
    "Dropping every field after one malformed field is outside this contract.",
    "An absent or malformed temperature does not erase a valid flow, and the same independence holds for every other slice.",
    "The helper copies each supplied slice before it reads it and returns new raw copies.",
    "Whether a native conversion exists for either field is Unknown.",
)
PARAMETER_HEADER = (
    "field",
    "signedness",
    "endian",
    "width_octets",
    "divisor",
    "unit_label",
    "unit_scale_passes",
    "sentinel",
    "numeric_grade",
    "semantic_grade",
    "native_grade",
)
EXAMPLE_HEADER = (
    "id",
    *SELECTION_AXES,
    *SLICE_AXES,
    "admitted",
    "temperature_outcome",
    "flow_outcome",
    "volume_outcome",
    "minimum_volume_outcome",
    "maximum_volume_outcome",
)
# Each entry names the production mistake that an independent axis blocks.
CAUGHT = {
    "family": "admits a family other than B509 and converts its two-octet slices",
    "variant": "drops the supplied variant, invents one when it is omitted, or collapses alpha and beta",
    "operation": "applies the OP59 conversion to an operation other than 59",
    "direction": "defaults a missing direction or admits a direction outside request and response",
    "temperature": "divides temperature by 256, assigns a sentinel, or drops the other slices when temperature is malformed",
    "flow": "decodes flow as a signed quantity or scales the unit a second time",
    "volume": "decodes volume as a signed quantity or clips full scale",
    "minimum_volume": "converts the raw minimum-volume slice or infers a scalar width",
    "maximum_volume": "converts the raw maximum-volume slice or infers a scalar width",
}
SINGLE_AXIS = {
    "family": "family-b524",
    "variant": "variant-beta",
    "operation": "operation-58",
    "direction": "direction-request",
    "temperature": "temperature-low-magnitude",
    "flow": "flow-distinct",
    "volume": "volume-distinct",
    "minimum_volume": "minimum-narrow",
    "maximum_volume": "maximum-wide",
}
ABSENCE = {
    "family": "family-omitted",
    "variant": "variant-omitted",
    "operation": "operation-omitted",
    "direction": "direction-omitted",
    "temperature": "temperature-omitted",
    "flow": "flow-omitted",
    "volume": "volume-omitted",
    "minimum_volume": "minimum-omitted",
    "maximum_volume": "maximum-omitted",
}
WIDTHS = {
    "temperature": {
        0: "temperature-empty",
        1: "temperature-truncated",
        2: "canonical",
        3: "temperature-wide",
    },
    "flow": {
        0: "flow-empty",
        1: "flow-truncated",
        2: "canonical",
        3: "flow-wide",
    },
    "volume": {
        0: "volume-empty",
        1: "volume-truncated",
        2: "canonical",
        3: "volume-wide",
    },
    "minimum_volume": {
        1: "minimum-narrow",
        2: "canonical",
        3: "minimum-wide",
    },
    "maximum_volume": {
        1: "canonical",
        2: "maximum-wide",
    },
}


class _Omitted:
    def __repr__(self) -> str:
        return "OMITTED"


OMITTED = _Omitted()


def _base(**overrides: object) -> dict[str, object]:
    row = {
        "family": "B509",
        "variant": "alpha",
        "operation": "59",
        "direction": "response",
        "temperature": "F0 FF",
        "flow": "64 00",
        "volume": "0A 00",
        "minimum_volume": "FF FF",
        "maximum_volume": "01",
    }
    row.update(overrides)
    return row


SPECS: tuple[tuple[str, dict[str, object]], ...] = (
    ("canonical", _base()),
    ("temperature-low-magnitude", _base(temperature="00 80")),
    ("flow-full-scale", _base(flow="FF FF")),
    ("volume-full-scale", _base(volume="FF FF")),
    ("temperature-zero", _base(temperature="00 00")),
    ("flow-distinct", _base(flow="65 00")),
    ("volume-distinct", _base(volume="0B 00")),
    ("temperature-as-flow-bytes", _base(temperature="64 00")),
    ("flow-as-volume-bytes", _base(flow="0A 00")),
    ("volume-as-flow-bytes", _base(volume="64 00")),
    ("temperature-omitted", _base(temperature=OMITTED)),
    ("flow-omitted", _base(flow=OMITTED)),
    ("volume-omitted", _base(volume=OMITTED)),
    ("minimum-omitted", _base(minimum_volume=OMITTED)),
    ("maximum-omitted", _base(maximum_volume=OMITTED)),
    ("slices-omitted", _base(
        temperature=OMITTED,
        flow=OMITTED,
        volume=OMITTED,
        minimum_volume=OMITTED,
        maximum_volume=OMITTED,
    )),
    ("temperature-empty", _base(temperature="")),
    ("flow-empty", _base(flow="")),
    ("volume-empty", _base(volume="")),
    ("temperature-truncated", _base(temperature="F0")),
    ("flow-truncated", _base(flow="64")),
    ("volume-truncated", _base(volume="0A")),
    ("temperature-wide", _base(temperature="F0 FF 00")),
    ("flow-wide", _base(flow="64 00 00")),
    ("volume-wide", _base(volume="0A 00 00")),
    ("minimum-narrow", _base(minimum_volume="FF")),
    ("minimum-wide", _base(minimum_volume="FF FF 00")),
    ("maximum-wide", _base(maximum_volume="01 02")),
    ("family-b524", _base(family="B524")),
    ("family-lowercase", _base(family="b509")),
    ("family-omitted", _base(family=OMITTED)),
    ("variant-beta", _base(variant="beta")),
    ("variant-empty", _base(variant="")),
    ("variant-omitted", _base(variant=OMITTED)),
    ("operation-58", _base(operation="58")),
    ("operation-omitted", _base(operation=OMITTED)),
    ("direction-request", _base(direction="request")),
    ("direction-other", _base(direction="other")),
    ("direction-empty", _base(direction="")),
    ("direction-omitted", _base(direction=OMITTED)),
    ("rejected-family-truncated-temperature", _base(family="B524", temperature="F0")),
)


def spec_map() -> dict[str, dict[str, object]]:
    return {name: row for name, row in SPECS}


def parse_hex(text: str) -> bytes:
    if text == "":
        return b""
    parts = text.split(" ")
    if any(len(part) != 2 or any(char not in "0123456789ABCDEF" for char in part) for part in parts):
        raise ValueError(text)
    return bytes(int(part, 16) for part in parts)


def decimal_text(numerator: int, divisor: int) -> str:
    text = format(Decimal(numerator) / Decimal(divisor), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text == "-0":
        return "0"
    return text


def decode(raw_text: str, signed: bool, divisor: int, endian: str = "little") -> str:
    number = int.from_bytes(parse_hex(raw_text), endian, signed=signed)
    return decimal_text(number, divisor)


def _admitted(selection: dict[str, object]) -> bool:
    variant = selection.get("variant", OMITTED)
    return (
        selection.get("family", OMITTED) == "B509"
        and isinstance(variant, str)
        and variant != ""
        and selection.get("operation", OMITTED) == "59"
        and selection.get("direction", OMITTED) in ADMITTED_DIRECTIONS
    )


def _echo(selection: dict[str, object]) -> dict[str, str | None]:
    echoed: dict[str, str | None] = {}
    for key in SELECTION_AXES:
        value = selection.get(key, OMITTED)
        echoed[key] = None if value is OMITTED else str(value)
    return echoed


def _field(state: str, raw: str | None, numeric: str | None, unit: str | None, numeric_grade: str | None) -> dict[str, object]:
    return {
        "state": state,
        "raw": raw,
        "numeric": numeric,
        "unit_label": unit,
        "numeric_grade": numeric_grade,
        "semantic_grade": "Hypothesis",
        "native_grade": "Unknown",
    }


def reference_view(selection: dict[str, object], slices: dict[str, object]) -> dict[str, object]:
    """Independent reference for one call. Inputs are copied before use."""

    selection_copy = _echo(selection)
    admitted = _admitted(selection)
    copied: dict[str, bytes | None] = {}
    for name in SLICE_AXES:
        value = slices.get(name, OMITTED)
        if value is OMITTED or value is None:
            copied[name] = None
        else:
            copied[name] = bytes(parse_hex(str(value)))
    fields: dict[str, dict[str, object]] = {}
    for name in SLICE_AXES:
        raw_bytes = copied[name]
        if raw_bytes is None:
            fields[name] = _field("absent", None, None, None, None)
            continue
        raw_text = " ".join(f"{octet:02X}" for octet in raw_bytes)
        if name in CONVERTIBLE:
            signedness, divisor, unit = CONVERTIBLE[name]
            if len(raw_bytes) != 2:
                fields[name] = _field("malformed", raw_text, None, None, None)
            elif not admitted:
                fields[name] = _field("withheld", raw_text, None, None, None)
            else:
                numeric = decode(raw_text, signedness == "signed", divisor)
                fields[name] = _field("converted", raw_text, numeric, unit, "Proven")
        else:
            fields[name] = _field("raw", raw_text, None, None, None)
    return {
        "admitted": admitted,
        "selection": selection_copy,
        "fields": fields,
        "write_builder": None,
        "registry_method": None,
    }


def reference_view_bytes(selection: dict[str, str], slices: dict[str, bytearray | None]) -> dict[str, object]:
    """Byte-oriented reference. Returned raw values are fresh bytearrays."""

    selection_copy = {key: selection[key] for key in SELECTION_AXES}
    admitted = _admitted(selection_copy)
    copied = {
        name: None if slices.get(name) is None else bytes(slices[name])
        for name in SLICE_AXES
    }
    fields: dict[str, dict[str, object]] = {}
    for name in SLICE_AXES:
        raw_bytes = copied[name]
        if raw_bytes is None:
            fields[name] = _field("absent", None, None, None, None)
            fields[name]["raw_bytes"] = None
            continue
        raw_text = " ".join(f"{octet:02X}" for octet in raw_bytes)
        if name in CONVERTIBLE:
            signedness, divisor, unit = CONVERTIBLE[name]
            if len(raw_bytes) != 2:
                state, numeric, grade, shown_unit = "malformed", None, None, None
            elif not admitted:
                state, numeric, grade, shown_unit = "withheld", None, None, None
            else:
                numeric = decode(raw_text, signedness == "signed", divisor)
                state, grade, shown_unit = "converted", "Proven", unit
        else:
            state, numeric, grade, shown_unit = "raw", None, None, None
        fields[name] = _field(state, raw_text, numeric, shown_unit, grade)
        fields[name]["raw_bytes"] = bytearray(raw_bytes)
    return {
        "admitted": admitted,
        "selection": selection_copy,
        "fields": fields,
    }


def field_parameters() -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for name, (signedness, divisor, unit) in CONVERTIBLE.items():
        rows[name] = {
            "signedness": signedness,
            "endian": "little",
            "width_octets": 2,
            "divisor": divisor,
            "unit_label": unit,
            "unit_scale_passes": 1,
            "sentinel": None,
            "numeric_grade": "Proven",
            "semantic_grade": "Hypothesis",
            "native_grade": "Unknown",
        }
    for name in OPAQUE:
        rows[name] = {
            "signedness": None,
            "endian": None,
            "width_octets": None,
            "divisor": None,
            "unit_label": None,
            "unit_scale_passes": 0,
            "sentinel": None,
            "numeric_grade": None,
            "semantic_grade": "Hypothesis",
            "native_grade": "Unknown",
        }
    return rows


def _slices_of(row: dict[str, object]) -> dict[str, object]:
    return {name: row[name] for name in SLICE_AXES}


def _selection_of(row: dict[str, object]) -> dict[str, object]:
    return {name: row[name] for name in SELECTION_AXES}


def outcome_token(field: dict[str, object]) -> str:
    state = field["state"]
    if state == "absent":
        return "absent"
    raw = "(empty)" if field["raw"] == "" else field["raw"]
    if state == "converted":
        return f"converted:{raw}:{field['numeric']}"
    return f"{state}:{raw}"


def _cell(value: object) -> str:
    if value is OMITTED or value is None:
        return "omitted"
    if value == "":
        return "empty"
    return str(value)


def example_record(name: str, row: dict[str, object]) -> dict[str, object]:
    viewed = reference_view(_selection_of(row), _slices_of(row))
    return {
        "id": name,
        "selection": viewed["selection"],
        "slices": {
            key: None if value is OMITTED else value
            for key, value in _slices_of(row).items()
        },
        "admitted": viewed["admitted"],
        "fields": viewed["fields"],
    }


def expected_examples() -> list[dict[str, object]]:
    return [example_record(name, row) for name, row in SPECS]


def expected_fixture() -> dict[str, object]:
    return {
        "label": "b509-op59-quantity-view",
        "signature": "ab09an09.view_b509_op59_candidate_fields(selection, slices)",
        "stability": "nothing-is-stable-before-helianthus-1.0",
        "namespace": None,
        "authorization_gate": None,
        "write_builder": None,
        "registry_method": None,
        "packet_parser": None,
        "family_detection": "explicit-selection-only",
        "admission": {
            "family": "B509",
            "variant": "explicit-non-empty",
            "operation": "59",
            "direction": list(ADMITTED_DIRECTIONS),
        },
        "fields": field_parameters(),
        "unknowns": list(UNKNOWNS),
        "examples": expected_examples(),
    }


def example_cells(record: dict[str, object]) -> list[str]:
    selection = record["selection"]
    slices = record["slices"]
    fields = record["fields"]
    return [
        str(record["id"]),
        *[_cell(selection[key]) for key in SELECTION_AXES],
        *[_cell(slices[key]) for key in SLICE_AXES],
        "yes" if record["admitted"] else "no",
        *[outcome_token(fields[key]) for key in SLICE_AXES],
    ]


def _param_cell(value: object) -> str:
    if value is None:
        return "none"
    return str(value)


def parameter_cells() -> list[list[str]]:
    rows = []
    parameters = field_parameters()
    for name in SLICE_AXES:
        item = parameters[name]
        rows.append([
            name,
            _param_cell(item["signedness"]),
            _param_cell(item["endian"]),
            _param_cell(item["width_octets"]),
            _param_cell(item["divisor"]),
            _param_cell(item["unit_label"]),
            _param_cell(item["unit_scale_passes"]),
            _param_cell(item["sentinel"]),
            _param_cell(item["numeric_grade"]),
            _param_cell(item["semantic_grade"]),
            _param_cell(item["native_grade"]),
        ])
    return rows


def _markdown_table(header: tuple[str, ...], rows: list[list[str]]) -> str:
    def line(cells: list[str]) -> str:
        return "| " + " | ".join(cells) + " |"

    separator = "| " + " | ".join("---" for _ in header) + " |"
    body = "\n".join(line(row) for row in rows)
    return "\n".join((line(list(header)), separator, body))


def render_parameter_table() -> str:
    return _markdown_table(PARAMETER_HEADER, parameter_cells())


def render_example_table() -> str:
    return _markdown_table(EXAMPLE_HEADER, [example_cells(record) for record in expected_examples()])


def _table_after(text: str, heading: str) -> list[list[str]]:
    parts = text.split(heading, 1)
    if len(parts) != 2:
        raise ValueError(f"missing heading {heading}")
    lines = []
    started = False
    for line in parts[1].splitlines():
        if line.startswith("|"):
            started = True
            lines.append(line)
        elif started:
            break
    if len(lines) < 2:
        raise ValueError(f"missing table under {heading}")
    parsed = []
    for line in lines:
        parsed.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return parsed


def axes_differing(left: dict[str, object], right: dict[str, object]) -> list[str]:
    changed = []
    for key in (*SELECTION_AXES, *SLICE_AXES):
        if left[key] is OMITTED or right[key] is OMITTED:
            if left[key] is not right[key]:
                changed.append(key)
        elif left[key] != right[key]:
            changed.append(key)
    return changed


def slice_width(value: object) -> int | None:
    if value is OMITTED or value is None:
        return None
    return len(parse_hex(str(value)))


def whitespace_errors(text: str, label: str) -> list[str]:
    errors = []
    if "\t" in text:
        errors.append(f"{label} contains a tab")
    if "\r" in text:
        errors.append(f"{label} contains a carriage return")
    for number, line in enumerate(text.splitlines(), 1):
        if line.endswith(" "):
            errors.append(f"{label}:{number} has trailing whitespace")
    return errors


def sentence_errors(page: str) -> list[str]:
    errors = []
    for sentence in REQUIRED_SENTENCES:
        if page.count(sentence) != 1:
            errors.append(f"required sentence count for {sentence!r} is {page.count(sentence)}")
    return errors


def _none_cell(text: str) -> object:
    if text == "omitted" or text == "none":
        return None
    if text == "empty":
        return ""
    return text


def parameter_errors(page: str, fixture: dict[str, object]) -> list[str]:
    errors = []
    try:
        table = _table_after(page, "## Conversion parameters\n")
    except ValueError as exc:
        return [str(exc)]
    header, _separator, *body = table
    if tuple(header) != PARAMETER_HEADER:
        errors.append(f"parameter header {header}")
    expected = {row[0]: row for row in parameter_cells()}
    seen = [row[0] for row in body if row]
    if seen != list(SLICE_AXES):
        errors.append(f"parameter rows {seen}")
    for row in body:
        if not row or row[0] not in expected:
            errors.append(f"unexpected parameter row {row}")
            continue
        if row != expected[row[0]]:
            errors.append(f"parameter mismatch for {row[0]}: {row} != {expected[row[0]]}")
    fields = fixture.get("fields")
    if fields != field_parameters():
        errors.append("fixture field parameters differ from the independent parameter set")
    admission = fixture.get("admission")
    if admission != expected_fixture()["admission"]:
        errors.append("fixture admission differs from the independent admission set")
    for key in ("write_builder", "registry_method", "namespace", "authorization_gate", "packet_parser"):
        if fixture.get(key) is not None:
            errors.append(f"fixture {key} is registered")
    if fixture.get("unknowns") != list(UNKNOWNS):
        errors.append("fixture unknowns differ")
    if fixture.get("family_detection") != "explicit-selection-only":
        errors.append("fixture family detection is not explicit selection")
    if fixture.get("signature") != expected_fixture()["signature"]:
        errors.append("fixture signature differs")
    return errors


def example_errors(page: str, fixture: dict[str, object]) -> list[str]:
    errors = []
    try:
        table = _table_after(page, "## Synthetic examples\n")
    except ValueError as exc:
        return [str(exc)]
    header, _separator, *body = table
    if tuple(header) != EXAMPLE_HEADER:
        errors.append(f"example header {header}")
    expected_records = expected_examples()
    expected_lines = [example_cells(record) for record in expected_records]
    if body != expected_lines:
        errors.append("page example table differs from the independent examples")
    examples = fixture.get("examples")
    if examples != expected_records:
        errors.append("fixture examples differ from the independent examples")
    return errors


def link_errors(page: str, page_path: Path) -> list[str]:
    errors = []
    links = re.findall(r"\]\(([^)\s]+)\)", page)
    if links != ["fixtures/an10_b509_quantity_views.json"]:
        errors.append(f"relative links {links}")
    for target in links:
        if ":" in target or target.startswith("//"):
            errors.append(f"non-local link {target}")
            continue
        resolved = (page_path.parent / target.split("#", 1)[0]).resolve()
        if not resolved.is_file():
            errors.append(f"unresolved link {target}")
    return errors


def literal_errors(page: str, fixture: dict[str, object]) -> list[str]:
    """Ticket literals checked without trusting the generated example builder."""

    errors = []
    required = {
        ("temperature", "F0 FF", True, 16): "-1",
        ("temperature", "00 80", True, 16): "-2048",
        ("temperature", "64 00", True, 16): "6.25",
        ("temperature", "00 00", True, 16): "0",
        ("flow", "64 00", False, 100): "1",
        ("flow", "65 00", False, 100): "1.01",
        ("flow", "FF FF", False, 100): "655.35",
        ("flow", "0A 00", False, 100): "0.1",
        ("volume", "0A 00", False, 10): "1",
        ("volume", "0B 00", False, 10): "1.1",
        ("volume", "FF FF", False, 10): "6553.5",
        ("volume", "64 00", False, 10): "10",
    }
    for (name, raw, signed, divisor), numeric in required.items():
        if decode(raw, signed, divisor) != numeric:
            errors.append(f"oracle {name} {raw} is not {numeric}")
    if decode("F0 FF", True, 16, "big") == "-1":
        errors.append("big-endian temperature unexpectedly matches the little-endian result")
    if decimal_text(-16, 256) == "-1":
        errors.append("divisor 256 unexpectedly matches divisor 16")
    if decode("FF FF", True, 100) == "655.35":
        errors.append("signed flow unexpectedly matches unsigned flow")
    if decode("FF FF", True, 10) == "6553.5":
        errors.append("signed volume unexpectedly matches unsigned volume")
    if decimal_text(1, 100) == "1":
        errors.append("a second flow scale leaves the value unchanged")
    if decimal_text(-1, 16) == "-1":
        errors.append("a second temperature scale leaves the value unchanged")
    if decimal_text(1, 10) == "1":
        errors.append("a second volume scale leaves the value unchanged")
    by_id = {item["id"]: item for item in fixture.get("examples", [])}
    expectations = {
        "canonical": {
            "temperature": ("converted", "F0 FF", "-1"),
            "flow": ("converted", "64 00", "1"),
            "volume": ("converted", "0A 00", "1"),
            "minimum_volume": ("raw", "FF FF", None),
            "maximum_volume": ("raw", "01", None),
        },
        "temperature-low-magnitude": {
            "temperature": ("converted", "00 80", "-2048"),
            "flow": ("converted", "64 00", "1"),
        },
        "flow-full-scale": {"flow": ("converted", "FF FF", "655.35")},
        "volume-full-scale": {"volume": ("converted", "FF FF", "6553.5")},
        "temperature-truncated": {
            "temperature": ("malformed", "F0", None),
            "flow": ("converted", "64 00", "1"),
            "volume": ("converted", "0A 00", "1"),
            "minimum_volume": ("raw", "FF FF", None),
            "maximum_volume": ("raw", "01", None),
        },
        "flow-omitted": {
            "flow": ("absent", None, None),
            "temperature": ("converted", "F0 FF", "-1"),
        },
        "family-b524": {
            "temperature": ("withheld", "F0 FF", None),
            "flow": ("withheld", "64 00", None),
            "volume": ("withheld", "0A 00", None),
            "minimum_volume": ("raw", "FF FF", None),
            "maximum_volume": ("raw", "01", None),
        },
        "rejected-family-truncated-temperature": {
            "temperature": ("malformed", "F0", None),
            "flow": ("withheld", "64 00", None),
            "volume": ("withheld", "0A 00", None),
        },
    }
    for example_id, fields in expectations.items():
        example = by_id.get(example_id)
        if example is None:
            errors.append(f"missing literal example {example_id}")
            continue
        if set(example["fields"]) != set(SLICE_AXES):
            errors.append(f"{example_id} does not retain every field")
        for field_name, (state, raw, numeric) in fields.items():
            actual = example["fields"].get(field_name)
            if actual is None:
                errors.append(f"{example_id}.{field_name} was dropped")
                continue
            if (actual["state"], actual["raw"], actual["numeric"]) != (state, raw, numeric):
                errors.append(
                    f"{example_id}.{field_name} is "
                    f"{(actual['state'], actual['raw'], actual['numeric'])}"
                )
            if actual["semantic_grade"] != "Hypothesis" or actual["native_grade"] != "Unknown":
                errors.append(f"{example_id}.{field_name} grades drifted")
            if state == "converted" and actual["numeric_grade"] != "Proven":
                errors.append(f"{example_id}.{field_name} numeric grade is not Proven")
            if state != "converted" and actual["numeric_grade"] is not None:
                errors.append(f"{example_id}.{field_name} invents a numeric grade")
    low = by_id.get("temperature-low-magnitude")
    if low is not None and low["fields"]["temperature"]["state"] == "absent":
        errors.append("temperature 00 80 was treated as a missing sentinel")
    page_lines = [
        "| canonical | B509 | alpha | 59 | response | F0 FF | 64 00 | 0A 00 | FF FF | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | raw:01 |",
        "| temperature-low-magnitude | B509 | alpha | 59 | response | 00 80 | 64 00 | 0A 00 | FF FF | 01 | yes | converted:00 80:-2048 | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | raw:01 |",
        "| flow-full-scale | B509 | alpha | 59 | response | F0 FF | FF FF | 0A 00 | FF FF | 01 | yes | converted:F0 FF:-1 | converted:FF FF:655.35 | converted:0A 00:1 | raw:FF FF | raw:01 |",
        "| volume-full-scale | B509 | alpha | 59 | response | F0 FF | 64 00 | FF FF | FF FF | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | converted:FF FF:6553.5 | raw:FF FF | raw:01 |",
        "| temperature-truncated | B509 | alpha | 59 | response | F0 | 64 00 | 0A 00 | FF FF | 01 | yes | malformed:F0 | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | raw:01 |",
    ]
    for line in page_lines:
        if line not in page.splitlines():
            errors.append(f"page is missing literal row {line.split('|')[1].strip()}")
    return errors


def unknown_errors(page: str) -> list[str]:
    marker = "## Unknown\n"
    if marker not in page:
        return ["missing Unknown section"]
    bullets = []
    started = False
    for line in page.split(marker, 1)[1].splitlines():
        if line.startswith("- "):
            started = True
            bullets.append(line[2:])
        elif started:
            break
    if tuple(bullets) != UNKNOWNS:
        return [f"unknown list {bullets}"]
    return []


def contract_errors(page: str, fixture: dict[str, object], page_path: Path) -> list[str]:
    return [
        *whitespace_errors(page, "page"),
        *sentence_errors(page),
        *parameter_errors(page, fixture),
        *example_errors(page, fixture),
        *unknown_errors(page),
        *link_errors(page, page_path),
        *literal_errors(page, fixture),
    ]


class B509Op59QuantityViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = PAGE.read_text(encoding="utf-8")
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.errors = contract_errors(cls.page, cls.fixture, PAGE)

    def test_contract_pages_match_independent_results(self) -> None:
        self.assertEqual(self.errors, [])

    def test_ticket_numerics_are_literal(self) -> None:
        self.assertEqual(decode("F0 FF", True, 16), "-1")
        self.assertEqual(decode("00 80", True, 16), "-2048")
        self.assertEqual(decode("64 00", False, 100), "1")
        self.assertEqual(decode("FF FF", False, 100), "655.35")
        self.assertEqual(decode("0A 00", False, 10), "1")
        self.assertEqual(decode("FF FF", False, 10), "6553.5")
        self.assertEqual(decimal_text(-16, 256), "-0.0625")
        self.assertNotEqual(decimal_text(-16, 256), "-1")
        self.assertEqual(decode("FF FF", True, 100), "-0.01")
        self.assertEqual(decode("FF FF", True, 10), "-0.1")
        self.assertNotEqual(decimal_text(1, 100), "1")
        self.assertNotEqual(decimal_text(-1, 16), "-1")
        self.assertNotEqual(decimal_text(1, 10), "1")

    def test_each_identity_axis_varies_alone(self) -> None:
        rows = spec_map()
        canonical = rows["canonical"]
        self.assertEqual(set(CAUGHT), set(SELECTION_AXES + SLICE_AXES))
        for axis, other_id in SINGLE_AXIS.items():
            with self.subTest(axis=axis, other=other_id):
                self.assertEqual(axes_differing(canonical, rows[other_id]), [axis])
                self.assertIn(axis, CAUGHT)
        for axis, other_id in ABSENCE.items():
            with self.subTest(axis=axis, absence=other_id):
                self.assertEqual(axes_differing(canonical, rows[other_id]), [axis])
                self.assertIs(rows[other_id][axis], OMITTED)
        self.assertEqual(
            axes_differing(canonical, rows["rejected-family-truncated-temperature"]),
            ["family", "temperature"],
        )
        self.assertEqual(axes_differing(canonical, rows["variant-beta"]), ["variant"])
        self.assertNotEqual(rows["variant-beta"]["variant"], rows["canonical"]["variant"])
        self.assertEqual(axes_differing(canonical, rows["direction-request"]), ["direction"])
        self.assertNotEqual(rows["direction-request"]["direction"], canonical["direction"])

    def test_each_slice_width_varies(self) -> None:
        rows = spec_map()
        for field_name, widths in WIDTHS.items():
            seen = {}
            for width, example_id in widths.items():
                with self.subTest(field=field_name, width=width):
                    self.assertEqual(slice_width(rows[example_id][field_name]), width)
                    seen[width] = example_id
            self.assertEqual(set(seen), set(widths))

    def test_malformed_temperature_keeps_flow_and_volume(self) -> None:
        example = next(item for item in self.fixture["examples"] if item["id"] == "temperature-truncated")
        self.assertEqual(set(example["fields"]), set(SLICE_AXES))
        self.assertEqual(example["fields"]["temperature"]["state"], "malformed")
        self.assertIn("flow", example["fields"])
        self.assertEqual(example["fields"]["flow"]["numeric"], "1")
        self.assertIn("volume", example["fields"])
        self.assertEqual(example["fields"]["volume"]["numeric"], "1")
        self.assertIn("minimum_volume", example["fields"])
        self.assertEqual(example["fields"]["minimum_volume"]["raw"], "FF FF")
        self.assertIsNone(example["fields"]["minimum_volume"]["numeric"])
        self.assertIn("maximum_volume", example["fields"])
        self.assertEqual(example["fields"]["maximum_volume"]["raw"], "01")
        self.assertIsNone(example["fields"]["maximum_volume"]["numeric"])

    def test_grades_and_non_claims(self) -> None:
        self.assertEqual(self.fixture["fields"]["temperature"]["numeric_grade"], "Proven")
        self.assertEqual(self.fixture["fields"]["temperature"]["semantic_grade"], "Hypothesis")
        self.assertEqual(self.fixture["fields"]["temperature"]["native_grade"], "Unknown")
        self.assertIsNone(self.fixture["fields"]["temperature"]["sentinel"])
        self.assertEqual(self.fixture["fields"]["flow"]["signedness"], "unsigned")
        self.assertEqual(self.fixture["fields"]["volume"]["signedness"], "unsigned")
        self.assertIsNone(self.fixture["fields"]["minimum_volume"]["divisor"])
        self.assertIsNone(self.fixture["fields"]["maximum_volume"]["width_octets"])
        self.assertIsNone(self.fixture["write_builder"])
        self.assertIsNone(self.fixture["registry_method"])
        for example in self.fixture["examples"]:
            for name, field in example["fields"].items():
                with self.subTest(example=example["id"], field=name):
                    self.assertEqual(field["semantic_grade"], "Hypothesis")
                    self.assertEqual(field["native_grade"], "Unknown")
                    if field["state"] != "converted":
                        self.assertIsNone(field["numeric"])
                        self.assertIsNone(field["unit_label"])

    def test_input_and_result_mutation_do_not_alias(self) -> None:
        pristine = {
            "temperature": bytes.fromhex("F0FF"),
            "flow": bytes.fromhex("6400"),
            "volume": bytes.fromhex("0A00"),
            "minimum_volume": bytes.fromhex("FFFF"),
            "maximum_volume": bytes.fromhex("01"),
        }
        selection = {
            "family": "B509",
            "variant": "alpha",
            "operation": "59",
            "direction": "response",
        }
        inputs = {name: bytearray(value) for name, value in pristine.items()}
        first = reference_view_bytes(dict(selection), inputs)
        inputs["temperature"][0] ^= 0xFF
        inputs["flow"][0] ^= 0xFF
        selection["family"] = "B524"
        selection["operation"] = "58"
        self.assertEqual(first["selection"]["family"], "B509")
        self.assertEqual(first["selection"]["operation"], "59")
        self.assertEqual(bytes(first["fields"]["temperature"]["raw_bytes"]), pristine["temperature"])
        self.assertEqual(first["fields"]["flow"]["numeric"], "1")
        self.assertEqual(first["fields"]["volume"]["numeric"], "1")
        first["fields"]["temperature"]["raw_bytes"][0] ^= 0xFF
        first["fields"]["flow"]["numeric"] = "999"
        first["selection"]["variant"] = "mutated"
        second_inputs = {name: bytearray(value) for name, value in pristine.items()}
        second = reference_view_bytes(
            {
                "family": "B509",
                "variant": "alpha",
                "operation": "59",
                "direction": "response",
            },
            second_inputs,
        )
        self.assertEqual(bytes(second["fields"]["temperature"]["raw_bytes"]), pristine["temperature"])
        self.assertEqual(second["fields"]["flow"]["numeric"], "1")
        self.assertEqual(second["fields"]["volume"]["numeric"], "1")
        self.assertEqual(second["fields"]["minimum_volume"]["raw"], "FF FF")
        self.assertEqual(second["fields"]["maximum_volume"]["raw"], "01")
        self.assertEqual(second["selection"]["variant"], "alpha")
        self.assertIsNot(second["fields"]["temperature"]["raw_bytes"], first["fields"]["temperature"]["raw_bytes"])
        self.assertNotEqual(bytes(first["fields"]["temperature"]["raw_bytes"]), pristine["temperature"])

    def test_relative_page_links_resolve_locally(self) -> None:
        self.assertEqual(link_errors(self.page, PAGE), [])
        self.assertEqual(unknown_errors(self.page), [])

    def test_example_count_is_finite_and_nonzero(self) -> None:
        self.assertGreater(len(self.fixture["examples"]), 0)
        self.assertEqual(len(self.fixture["examples"]), len(SPECS))
        self.assertEqual(
            [item["id"] for item in self.fixture["examples"]],
            [name for name, _row in SPECS],
        )


if __name__ == "__main__":
    unittest.main()
