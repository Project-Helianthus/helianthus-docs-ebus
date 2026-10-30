# AN02: candidate B524 calendar views

This architecture contract specifies the hypothetical ab01an01 pure helper API
for AN01, independently of its implementation. Refs #856; partial child of #736.
Nothing here is stable before Helianthus 1.0.

The [public native B524 contract](../protocols/vaillant/ebus-vaillant-B524.md)
comes first: matching GG/RR, retained requested II, independent OP02 and OP06
namespaces and raw status are prerequisites, not native codec qualification.
Its calendar sections describe unresolved codecs, including a candidate century
offset and scalar BCD interpretations. This software view deliberately selects
plain unsigned bytes and leaves century Unknown; it resolves neither conflict.
The [synthetic example table](fixtures/an02_b524_calendar_views.json) is software
evidence only, never a capture or new native family qualification.

## Hypothetical signature and input

`interpret_calendar_field(context, alternative, reply, cells) -> CalendarResult`

**Proven — software design:** the function is pure, performs no I/O, and returns
fresh owned buffers with no aliases to input or other results. No production
helper is imported by the example checks. `context` requires explicit family,
software, hardware, API version, API revision, opcode, group, instance and
register. These are supplied context, not a firmware qualification registry.
Family/software/hardware/API fields are nonempty opaque strings; the family
string must match a listed candidate. Software/hardware/API changes remain
distinct output identities; no value is
inferred for an omitted field. `alternative` is exactly `date` or `time`.

Selectors use integer opcode/group/instance bytes and a 16-bit register. GG03
accepts a caller-supplied byte II; there is no inferred physical instance ceiling.
All other listed rows require II00. Missing/invalid context, unknown family,
unlisted selector, wrong alternative or OP06 produces raw-only present cells.
Family is never inferred from a route or payload length.

`reply` has explicit state `echo-payload`, `status`, `transport-error`, or
`unknown`; it retains raw bytes and returned group/register independently from
requested group/register. II remains requested context, never a returned echo.
Only `echo-payload` with matching GG/RR permits interpretation. One-byte status,
transport error and echo mismatch retain raw/Unknown meaning.

`cells` is an ordered list of exactly three objects, each with `state` equal to
`present`, `missing`, or `failed`, and `raw` equal to a byte or null. A present
cell requires a byte. Missing/failed cells may retain a byte as evidence without
using it as a value. Invalid list length, invalid state or invalid byte is a
malformed input: return retained input, three raw-only components with null
values, complete-candidate false and semantic grade Unknown. Never pad a list.

## Output and grades

`CalendarResult` retains copied context, alternative, reply and `input_cells`, plus ordered
`components`, `complete_candidate`, and separate numeric/semantic/native grades.
Each component returns `raw`, `state` and nullable `value`. The states are
`candidate`, `out-of-domain`, `missing`, `failed`, or `raw-only`. A valid eligible
present byte becomes a candidate only within its independent domain. An
out-of-domain byte keeps its raw value; useful other cells remain candidates.
Missing never becomes zero. A cell failure does not erase siblings or any
caller's prior last-known-good evidence; this stateless helper does not merge
history. Complete-candidate is true exactly when all three are candidates.
Admission remains fail-closed and outside this helper.

**Proven — numeric software result:** plain unsigned byte conversion; hexadecimal
`12` is decimal 18. **Hypothesis — semantic meaning:** selected date components
are day/month/year with independent domains 1..31, 1..12, 0..99. Selected time
components are hour/minute/second plain bytes, without extra native time domains.
**Unknown — native support:** neither successful conversion nor completeness
proves support, presence, freshness, execution or physical qualification. These
are independent axes and are not upgraded by this helper.

Thus [31,12,99] yields candidate 31/12/99; [23,59,58] preserves each time byte.
Missing month preserves day/year and clears completeness. Day0, month13 and
year100 remain raw/out-of-domain; 31/02/99 passes these independent domains.
No joint date rule is introduced.

## Finite candidate selection

All rows below are **Hypothesis** and OP02. Registers are hexadecimal; II is
00 except GG03, where it is caller-supplied. There are exactly 26 family/selector
rows, each with a positive synthetic control in the fixture.

| Family | GG | Date RR | Time RR |
| --- | --- | --- | --- |
| controller-700 | 00 | 0034, 0071, 0072 | 0035 |
| controller-700 | 01 | 0009, 000A | — |
| controller-700 | 03 | 0003, 0004 | — |
| controller-720 | 00 | 0034, 00DA, 00DB | 0035 |
| controller-720 | 01 | 0009, 000A | 0010, 0011 |
| controller-720 | 03 | 0003, 0004, 0024 | 001E, 0020, 0021 |
| controller-720 | 09 | 0007, 0009 | 0008, 000A |

Family-700 DA and family-720 71 remain unmatched; no other family-700
counterparts follow from this table.

## Executable policy declaration

The following fields are normative inputs to the focused contract checks.
Their behavior is checked against independent numeric and state expectations,
not only against the fixture's spelling.

```json
{
  "encoding": "unsigned-byte",
  "family_fallback": false,
  "opcode": 2,
  "echo_match_required": true,
  "context_fields": [
    "family",
    "software",
    "hardware",
    "api_version",
    "api_revision",
    "opcode",
    "group",
    "instance",
    "register"
  ],
  "missing_fill": null,
  "timestamp": false,
  "edit_permission": false,
  "joint_date_validation": false,
  "date_domains": [
    [
      1,
      31
    ],
    [
      1,
      12
    ],
    [
      0,
      99
    ]
  ],
  "time_domains": [
    [
      0,
      255
    ],
    [
      0,
      255
    ],
    [
      0,
      255
    ]
  ],
  "numeric_grade": "Proven",
  "semantic_grade": "Hypothesis",
  "native_grade": "Unknown"
}
```

## Unknowns and boundary

Century, timezone, combined timestamp, native support, physical offsets,
string-name pieces and edit validation are **Unknown**. No frame builder,
automatic value-admission integration, timestamp synthesis or calendar edit
permission is provided. The page changes no eBUS MCP or GraphQL surface; any
later projection must preserve parity and the same raw/partial evidence.
AN01 is an ordinary companion, not a dependency. Broader native/runtime
obligations remain open under #736.
