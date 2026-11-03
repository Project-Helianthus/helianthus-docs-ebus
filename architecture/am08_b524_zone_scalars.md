# AM08: Explicit B524 zone scalar bindings

Status: application API and synthetic-contract page. Candidate meaning is
**Hypothesis**; native support, presence, freshness, writability, persistence
and effects are **Unknown**. Nothing here is stable before Helianthus 1.0.
Refs [#736](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/736);
this is a partial Release 0.7 child. The synthetic example package is
[`fixtures/am08_b524_zone_scalars.json`](fixtures/am08_b524_zone_scalars.json)
and the focused check is
[`../tests/test_am08_b524_zone_scalars.py`](../tests/test_am08_b524_zone_scalars.py).
Neighbouring responsibilities stay where they are:
[B524 namespace invariants](b524-namespace-invariants.md) and
[B524 semantic mapping](b524-semantic-mapping.md).

## Grades

| Statement | Grade |
| --- | --- |
| The pure interpreter contract below (inputs, outputs, raw-only behavior) | Proven (software contract) |
| The finite bindings below carry the listed type and unit | Hypothesis |
| Uint16 and float32 byte representations as candidate codecs | Hypothesis |
| Physical support, presence, freshness, writability, persistence, effects | Unknown |
| Family label equals qualified device identity | Not claimed; a family label is an explicit candidate selection |

A successful interpretation is always graded Hypothesis. This page adds no
route, poll, writer, profile change, cached-value replacement, bounds import
or presence assertion. Existing explicit codec helpers, name annotations,
codebooks, calendar groups, special scalar alternatives, command roles and
numeric edit candidates keep their responsibilities.

## Finite bindings (Hypothesis)

All bindings are selected by the tuple (family, opcode OP02, group GG03,
instance rule dynamic, register RR). Registers are hexadecimal. Each tuple is
distinct; the same register under a different family, or under OP06, is a
different (unlisted) selector.

| Family | Codec | Unit | Registers |
| --- | --- | --- | --- |
| controller-720 | float32 little-endian | °C | 0002, 0005, 0009, 000F, 0014, 0015, 0023 |
| controller-720 | float32 little-endian | % | 0028 |
| controller-700 | float32 little-endian | °C | 0002, 0005, 0009, 000F, 0014, 0015 |
| controller-700 | float32 little-endian | % | 0028 |

Register 0023 exists only for controller-720. A unit of Unknown would supply no
semantic unit; units are preserved separately from values and never converted.
No binding in this set uses uint16.

## Representations (Hypothesis)

- uint16: two little-endian unsigned bytes. `34 12` is 4660; `FF FF` is 65535
  with no sentinel inference.
- float32: four little-endian IEEE binary32 bytes. `00 00 C0 3F` is 1.5;
  `00 00 80 BF` is -1. Only finite values are decoded. Infinities and NaN
  (for example 7F800000 materialized little-endian) yield raw-only. There is
  no clipping, no added 273.15 offset and no invented sentinel.

A codec is chosen only by the matched binding, never by value width, register
name or another family.

## Interpreter API

A pure function, selected explicitly by the caller. It performs no I/O.

Inputs, each retained independently and never fabricated or inferred:

| Input | Rule |
| --- | --- |
| family | Explicit tag; must equal a listed family exactly. |
| software, hardware, api_version, api_revision | Caller context; each must be supplied (explicit zero is supplied; absent is not). |
| opcode | Must be 02 for a binding; OP06 with an otherwise identical selector is unlisted. |
| group | Must be 03. |
| instance | Concrete byte 00..FF supplied by the caller (dynamic rule). It is request context only, never an echoed value, and is not enumerated. A fixed II00 rule would accept only 00. |
| register | Two-byte RR from the table for the family. |
| reply_kind | Normalized kind; only `echo_payload` is eligible. |
| returned group, returned register | The GG/RR echoed in the reply; must equal the requested group and register. |
| value bytes | Owned value bytes of the reply, exact width of the codec (4 for float32). |
| codec grade | `Hypothesis` or a stronger request is accepted but does not promote; `Unknown` or missing is raw-only. |

Output (always returned, never an exception for data problems):

- `status`: `interpreted` or `raw-only`;
- `grade`: `Hypothesis` when interpreted, otherwise none;
- `value`, `unit`, `codec`: only when interpreted; the unit is kept separate;
- `raw`: an owned copy of the value bytes, always retained;
- `context`: exactly the caller-supplied family, software, hardware, API
  version, API revision, opcode, group, instance, register, reply kind,
  returned group, returned register and codec grade, even when the binding and
  arithmetic are unchanged by a context change;
- `reason`: short text for raw-only results.

Raw-only (bytes and context kept, no value) is returned for: unknown family,
any missing context field, unlisted selector (neighbouring register, other
opcode, other group, register of another family), instance missing or out of
byte range, any reply kind other than `echo_payload` (status-only, short,
failed, mismatched, unrecognized), returned GG/RR different from the request,
width minus or plus one, non-finite float, and unknown or missing codec grade.

Returned results own their memory: mutating the caller's input buffer after
the call, or the result's buffer, never changes the other.

## Limits

Retained context matches the caller exactly and is not physical qualification.
Interpreting a value says nothing about support, presence, freshness,
writability or effects (all Unknown). No bounds, defaults or sentinels are
imported. Companion code lives in the Helianthus register registry (AM07) and
holds its merge for this page.
