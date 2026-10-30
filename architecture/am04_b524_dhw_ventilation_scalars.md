# Explicit B524 DHW and ventilation scalar bindings

## Evidence and scope

The public [native B524 contract](../protocols/vaillant/ebus-vaillant-B524.md)
is the wire authority: OP02 and OP06 have separate identities; returned GG/RR
must correlate; II belongs to the request and is never an echoed value.
The [native register catalog](../protocols/vaillant/ebus-vaillant-B524-register-map.md)
provides candidate DHW and ventilation context. This page defines an application
contract, not additional wire evidence. It is a partial child of issue #859,
Refs #736; the parent remains open. The companion AM03 interpreter in ebusreg
holds its merge for this page; this page has no code dependency on AM03.

**Proven software contract:** an explicitly selected, pure interpreter admits
only the finite candidates below. **Hypothesis:** their codecs and declared
units. **Unknown:** physical support, presence, freshness, effects, persistence,
delivery, native bounds, sentinel meanings and device qualification. These
properties are independent of successful arithmetic or a software contract grade.
A family tag selects a candidate; it is never qualified device identity.

## Complete candidate set

All numbers in this table are hexadecimal. Every row is a separate binding.
No other selector or family is admitted, including OP06 with identical GG/II/RR.

| Family | Opcode | Group | II rule | Register | Codec | Declared unit | Grade |
| --- | --- | --- | --- | --- | --- | --- | --- |
| controller-720 | 02 | 01 | 00 | 0004 | float32 LE | °C | Hypothesis |
| controller-720 | 02 | 01 | 00 | 0005 | float32 LE | °C | Hypothesis |
| controller-720 | 02 | 09 | 00 | 000D | uint16 LE | Unknown | Hypothesis |
| controller-720 | 02 | 09 | 00 | 000E | uint16 LE | Unknown | Hypothesis |
| controller-700 | 02 | 01 | 00 | 0004 | float32 LE | °C | Hypothesis |
| controller-700 | 02 | 01 | 00 | 0005 | float32 LE | °C | Hypothesis |

## Inputs, output and admission

`interpret(context, reply, codec_grade)` below is a normative executable example,
not a runtime registration, API endpoint or transport parser. Inputs are mappings
and owned bytes from an already normalized reply. The JSON
[example package](fixtures/am04_b524_dhw_ventilation_scalars.json) serializes bytes
as hexadecimal and omits missing keys; its adapter converts only `value_hex` to
`value_bytes`. There are no captured frames or physical observations here.

Context requires independent `family`, `software`, `hardware`, `api_version`,
`api_revision`, `opcode`, `group`, `instance`, and `register` fields. Software,
hardware and API fields are opaque nonempty strings or nonnegative integers,
including explicit zero; no field is inferred from another. Selectors are integers
excluding booleans: opcode/group/instance are bytes and register is a 16-bit
unsigned integer. Missing differs from explicit zero. Fixed II00 accepts only
00. A dynamic II rule, if separately defined elsewhere, requires a caller's
concrete byte and does not enumerate installed instances; none is admitted here.

Reply requires `kind`, `returned_group`, `returned_register`, and `value_bytes`
(bytes or bytearray). Only `echo_payload` with matching integer GG/RR and exact
codec width admits interpretation. The normalized non-echo kinds are `empty`,
`status_only`, `short`, `header_only`, `nack`, `timeout`, `transport_error`,
`decode_failed`, and `mismatched`; every other kind also fails closed. The caller
owns normalization and original framing evidence; the helper retains the entire
supplied reply metadata and the supplied bytes, not a fabricated header.

`codec_grade` must be Hypothesis or Proven; Unknown, missing (`None`) and
unrecognized grades produce raw-only. A stronger requested grade never promotes
a candidate. Output always includes independent copies of all supplied context
and reply metadata, `raw`, the original `codec_grade`, `value`, `value_grade`,
`declared_unit`, and `unit_grade`. Raw-only means value is None and value_grade is
Unknown. A selected binding retains its declared unit even if reply admission fails.
The unit_grade is Hypothesis for °C and Unknown for an Unknown unit; an
unselected binding uses Unknown for both.
Unknown unit supplies no semantic unit, even after successful uint16 arithmetic.
Malformed byte input is retained as supplied and cannot decode. Extra metadata is
retained but cannot select a codec. Results never alias mutable input or other
results, including nested metadata and raw memory.

A uint16 is exactly two little-endian unsigned bytes. A float32 is exactly four
little-endian IEEE binary32 bytes and must be finite. There is no clipping,
Celsius offset of 273.15, sentinel inference or selection by width/name/another
family. The executable example is the complete finite admission behavior:

```python
from copy import deepcopy
import math
import struct

BINDINGS = {
    ("controller-720", 2, 1, 0, 4): ("float32", "°C"),
    ("controller-720", 2, 1, 0, 5): ("float32", "°C"),
    ("controller-720", 2, 9, 0, 13): ("uint16", "Unknown"),
    ("controller-720", 2, 9, 0, 14): ("uint16", "Unknown"),
    ("controller-700", 2, 1, 0, 4): ("float32", "°C"),
    ("controller-700", 2, 1, 0, 5): ("float32", "°C"),
}


def integer(value, maximum):
    return type(value) is int and 0 <= value <= maximum


def interpret(context, reply, codec_grade=None):
    raw = reply.get("value_bytes")
    result = {
        "context": deepcopy(context),
        "reply": deepcopy({k: v for k, v in reply.items() if k != "value_bytes"}),
        "raw": bytearray(raw) if isinstance(raw, (bytes, bytearray)) else deepcopy(raw),
        "codec_grade": deepcopy(codec_grade),
        "value": None, "value_grade": "Unknown",
        "declared_unit": "Unknown", "unit_grade": "Unknown",
    }
    for field in ("software", "hardware", "api_version", "api_revision"):
        value = context.get(field)
        if not ((type(value) is str and bool(value)) or integer(value, float("inf"))):
            return result
    for field, maximum in (("opcode", 255), ("group", 255),
                           ("instance", 255), ("register", 65535)):
        if not integer(context.get(field), maximum):
            return result
    if type(context.get("family")) is not str:
        return result
    key = tuple(context.get(f) for f in ("family", "opcode", "group", "instance", "register"))
    binding = BINDINGS.get(key)
    if binding is None:
        return result
    codec, unit = binding
    result.update(declared_unit=unit, unit_grade="Unknown" if unit == "Unknown" else "Hypothesis")
    if codec_grade not in ("Hypothesis", "Proven"):
        return result
    if reply.get("kind") != "echo_payload":
        return result
    for field, requested, maximum in (("returned_group", "group", 255),
                                      ("returned_register", "register", 65535)):
        if not integer(reply.get(field), maximum) or reply[field] != context[requested]:
            return result
    width = 4 if codec == "float32" else 2
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != width:
        return result
    value = struct.unpack("<f", bytes(raw))[0] if codec == "float32" else int.from_bytes(raw, "little")
    if codec == "float32" and not math.isfinite(value):
        return result
    result.update(value=value, value_grade="Hypothesis")
    return result
```

## Synthetic controls and integration limits

Every table tuple has its own controls in the example package. For every float
binding `00 00 C0 3F` gives 1.5 and `00 00 80 BF` gives -1;
IEEE positive infinity encoded little-endian as `00 00 80 7F` is raw-only.
For every uint16 binding `34 12` gives 4660 and `FF FF` gives 65535 without a
sentinel interpretation. Width minus/plus one, neighboring unlisted RR, OP06,
unknown family, II01, mismatched returned GG/RR, all non-echo kinds, unknown or
missing grade, malformed/partial/extra inputs and separate context variations
are covered by the [focused standard-library tests](../tests/test_am04_b524_dhw_ventilation_scalars.py).
The tests use independent literal values plus struct/int arithmetic, verify the
page table and fixture selector set, and execute the page example. They establish
only this software/page contract, not automatic full Gate D discovery or native
qualification.

No route, poll, writer, profile change, cached-value replacement, bounds import
or presence assertion is added. Partial failure preserves raw and independently
useful fields; prior per-field last-known-good state is not replaced by this
stateless helper. Existing explicit codec helpers, name annotations, codebooks,
calendar groups, special scalar alternatives, command roles and numeric edit
candidates retain their responsibilities. eBUS MCP compatibility and GraphQL
parity are unchanged; neither transport nor an active executor is introduced.
Nothing is declared stable before Helianthus 1.0; no new major or experimental
namespace or authorization gate is introduced.
