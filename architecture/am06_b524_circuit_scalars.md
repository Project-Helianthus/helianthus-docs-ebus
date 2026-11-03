# Explicit B524 circuit scalar bindings

**Proven — software contract.** This page specifies a pure, explicitly selected
candidate interpreter for AM06. It defines behavior for companion AM05 and has
no code dependency on it. It is an application contract, not native wire proof.
The [public native contract](../protocols/vaillant/ebus-vaillant-B524.md)
(section 2.2–2.3) owns request correlation, response shapes and raw retention;
the [native catalog](../protocols/vaillant/ebus-vaillant-B524-register-map.md)
owns protocol register evidence. Those contracts come first. The finite
candidate set below does not upgrade their evidence or extend native claims.

**Hypothesis — bindings.** Every row below has opcode `02`, group `02`, dynamic
II, codec `float32_le` and grade `Hypothesis`. Registers are hexadecimal. Each
(family, opcode, group, concrete instance, register) remains distinct.

| Family | Registers | Declared unit |
| --- | --- | --- |
| controller-720 | 0007, 0008, 0010, 0011, 0012, 0014, 001F | °C |
| controller-720 | 000A, 000B | K |
| controller-720 | 000F, 001C | Unknown |
| controller-720 | 001A | % |
| controller-700 | 0007, 0008, 0010, 0011, 0012, 0014, 001F | °C |
| controller-700 | 000A, 000B | K |
| controller-700 | 000F | Unknown |

This is the complete 22-binding set. There is no uint16 binding and no fixed
II00 binding in this area. No family fallback is allowed, including for rows
shared by both families. A family tag selects a candidate; it never qualifies
physical device identity.

## Input and result

The logical input is `(context, owned value bytes, requested_grade)`.
Context contains the independently retained fields in the policy block below.
`software` and `hardware` are caller-supplied nonempty opaque strings;
`api_version` and `api_revision` are caller-supplied nonnegative integers.
No physical software or hardware identity is inferred from these synthetic
fields. Opcode, group and instance are integer bytes; register is an unsigned
16-bit integer. Booleans are not integers for admission. Absent, null, empty,
malformed and explicit zero remain distinguishable; missing required context
returns raw-only. No values are fabricated. Extra context fields are retained
without selecting another binding.

`reply_kind` is supplied by a normalizer, not inferred from width. Its known
values are `echo_payload`, `empty`, `status_only`, `short`, `header_only`,
`nack_or_crc`, `timeout`, and `transport_error`. Unknown kinds are raw-only.
`returned_group` and `returned_register` carry independently supplied echo
fields, or absent/null partial fields. Their ranges match group and register.
II is request context, never an echoed field. Dynamic II requires a concrete
byte, including 00 or 01; this does not enumerate installed instances or import
bounds. The generic fixed II00 rule accepts only 00, but adds no binding here.

The logical output contains a deep copy of **all** caller context, an independent
raw byte buffer, `value`, `grade`, and `unit`. Raw-only means value and grade
are null. Unit retains a selected binding's declaration independently of decode
success; an unselected binding has unit `Unknown`. Selection follows complete
context validation, so partial context is unselected and has unit `Unknown`. A declared `Unknown` supplies
no semantic unit. Requested grade is retained separately and cannot promote
an interpretation. Matching echo fields survive even a failed decode, and
partial/failed fields survive independently. A malformed byte container is an
input type error, never a successful decode; bytes, bytearray and memoryview
are the supported byte containers.

Admission is fail-closed in this order: validate complete caller context;
select only the exact family/opcode/group/register row with an accepted II
rule; require codec grade `Hypothesis` or `Proven`; require normalized `echo_payload`;
require matching returned GG and RR; require the selected codec's exact width;
then decode. Unknown or missing codec grade is raw-only. A supplied `Proven` codec grade
still produces only `Hypothesis`; caller confidence cannot promote the binding. The explicit
candidate cannot be chosen by width, a display name or another family's row.
Status-only, short, failed, mismatched, partial, extra-width or unknown replies
keep their bytes with no interpreted value. Changing software, hardware, API
version or API revision need not change candidate arithmetic, but the changed
context must be visible. Missing each of these fields still blocks admission.

## Representation and grade

**Hypothesis — representation.** `float32_le` means exactly four little-endian
IEEE binary32 bytes. Only finite results qualify as candidate values: do not
clip, add 273.15, or invent a sentinel. `uint16_le`, where separately selected,
means exactly two little-endian unsigned bytes; `34 12` is 4660 and `FF FF` is
65535 without sentinel inference. That generic representation does not admit
a uint16 circuit selector. A successful result always remains `Hypothesis`,
including when `requested_grade` is `Proven`; `Unknown` or missing codec grade
returns raw-only. Evidence grade is independent of physical qualification.

For **every** listed row, `00 00 C0 3F` gives 1.5, `00 00 80 BF` gives -1,
and binary32 bits `7F800000`, materialized little-endian as `00 00 80 7F`,
are non-finite and raw-only. Width minus/plus one is raw-only. Changing the
returned GG or RR, switching to OP06, or choosing an unlisted neighboring RR
is raw-only. Dynamic II00 and II01 both retain their concrete request value.
Changing a row to a family without that selector is raw-only. Shared-family
rows remain explicit selections with independently retained family context.

The following machine-readable policy is normative alongside the table;
[the synthetic example package](fixtures/am06_b524_circuit_scalars.json)
expands every table tuple and all three float controls. Its `edge_scenarios`
apply to every tuple: overlay `patch` on a complete base input, remove the
`absent` keys, and supply `raw_hex`. Each scenario states `expected_value`;
grade is null for raw-only and otherwise `Hypothesis`. The same context and
unit-retention rules apply. The tests also vary families, malformed fields,
non-finite bit patterns and raw-memory mutation independently.

```json
{
  "context_fields": ["family", "software", "hardware", "api_version", "api_revision", "opcode", "group", "instance", "register", "reply_kind", "returned_group", "returned_register", "codec_grade"],
  "reply_kind": "echo_payload",
  "grade": "Hypothesis",
  "unknown_unit": "Unknown",
  "finite_only": true,
  "exact_width": true,
  "match_returned_group": true,
  "match_returned_register": true,
  "own_raw": true,
  "explicit_selection": true
}
```

## Limits and verification

**Unknown — native qualification.** Physical support, installed instances,
presence, freshness, effects, persistence and delivery remain Unknown. These
synthetic examples are neither captures nor device observations. They establish
only the specified software/page contract. Nothing is stable before Helianthus
1.0. No new namespace or authorization gate is introduced.

This pure interpretation adds no route, poll, writer, profile change,
cached-value replacement, bounds import or presence assertion. Partial failure
cannot replace useful last-known-good state; state admission remains the
consumer's existing responsibility. Explicit codec helpers, name annotations,
codebooks, calendar groups, special scalar alternatives, command roles and
numeric edit candidates retain their responsibilities. eBUS MCP compatibility
and GraphQL parity are preserved; no transport or API surface is changed.

The [focused standard-library tests](../tests/test_am06_b524_circuit_scalars.py)
compare table, policy and examples with independent constants and arithmetic.
They exercise a local reference model of this prose, not companion production
code. Every binding varies every context/key axis independently, including
absent versus zero, reply kinds, malformed selectors, extra width and owned
memory. Generic uint16 and fixed-II00 checks cannot create bindings. Full
repository CI, Gate D, independent committed-change review, publication checks
and applicable transport classification remain later ship requirements; the
focused command does not claim automatic Gate D discovery.
