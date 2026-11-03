# Five-field burner candidate views

## Evidence and scope

Read the [native service contract](../protocols/ebus-services/ebus-service-05h.md)
first, especially its candidate-variant section. Its standard contract remains
authoritative. The standard ranges and outside replacement must not be imported
into this explicitly selected candidate. The native page records the candidate
ranges, widths and signedness as unconfirmed on the wire. The finite contract
below introduces no additional native evidence.

**Hypothesis:** a pure, explicitly selected five-field candidate-body interpreter
for `05/01`. This page specifies an application interpretation API, not a wire
encoder or a deployed implementation. **Proven:** this documentation adds an
explicit interpretation API contract without changing the earlier metadata
catalog, provider or command route. Candidate meanings stay Hypothesis;
qualification stays Unknown. This contract is not stable before Helianthus 1.0.

## Explicit inputs and admission

The input is `identity` plus `body`. All five identity keys are required, matched
exactly and independently; no defaults, aliases, discovery or auto-selection:

| Axis | Selected value |
|---|---|
| family | burner |
| variant | vaillant-candidate |
| operation | 05/01 |
| direction | request |
| selector | burner-five-field |

These are application selection tokens, not a new native namespace. `direction`
is the API request/response form; the selected request represents the
controller-to-burner candidate. The caller supplies already isolated body bytes,
with no prefix, framing, address, length or checksum bytes. The selector does not
strip a prefix. `body` is an owned byte sequence; the JSON examples represent it
as an array of integers 0..255. A Boolean, fraction, string, null or out-of-byte
integer is malformed, including anywhere after the fifth position. No partial
coercion is allowed. JSON identity must be an object; malformed identity or body
returns `malformed` with no interpreted fields. Unknown, absent or null identity
values, extra identity keys, unknown family/variant, a non-request form or an
unselected selector return `raw-only` for a valid body. Admission fails closed.

`05/04` retains its separate identity and is raw-only here. A positive `05/01`
declaration is prefix-only: it establishes no five-value body, positive result,
ACK, command acceptance or empty wire response. Even five bytes in a positive
form remain raw-only. A request body containing `05 01` is merely a short
isolated body; it is never recognized as a positive declaration automatically.

## Fields and outputs

Offsets are zero based within the isolated body. Domains are candidate domains,
not observed device limits. Conversion is identity for all five fields: never
add 273.15 or apply 0.01 from unit metadata.

| Field | Offset | Codec | Unit | Candidate domain | Metadata default | Conversion |
|---|---:|---|---|---|---|---|
| heat_state | 0 | u8 | none | 00,55,AA,CC,EE | shutdown (00) | identity |
| boiler_target | 1 | u8 | Celsius | 0..90 | 0 | identity |
| dhw_target | 2 | u8 | Celsius | 0..90 | 0 | identity |
| outside_temperature | 3 | i8 | Celsius | -128..127 | 0 | identity |
| setting | 4 | u8 | percent | 0..255 | 0 | identity |

| Raw heat state | Candidate name |
|---|---|
| 00 | shutdown |
| 55 | DHW |
| AA | heating |
| CC | emission-check |
| EE | controller-stop |

`DD` is a separate unresolved check alternative, never a named value in this
table. `DD` and `01` are unmapped. No unavailable replacement is established:
raw outside `3F` remains 63. Setting 255 remains 255, without clipping to 100.
Defaults are metadata only; every missing position remains absent, never zero.

Each result contains an owned `identity` snapshot, exact owned `raw_body`,
`status`, `complete`, ordered `fields`, `remainder`, `grade: Hypothesis` and
`qualification: Unknown`. Each of the five candidate field records contains
`name`, `raw` (unsigned byte integer or null), `interpretation` (candidate name,
numeric value or null) and `domain_state`. Missing positions use null for raw
and interpretation and `absent`; an unmapped heat byte preserves raw, has null
interpretation and `unmapped`. Numeric values outside a candidate domain remain
numeric with raw preserved and `out-of-candidate-domain`; all other present
values use `in-candidate-domain`. Signed interpretation preserves the unsigned
raw byte, so raw 255 can coexist with interpretation -1.

A selected well-formed body returns `candidate` even with an unmapped or
out-of-domain field. Return all independently useful fields: do not erase a
valid neighbour on partial failure. `complete` is true exactly when a selected,
well-formed body has five bytes, regardless of domain state. Five is only a
normalized representation boundary, not an established physical length. Short
bodies retain all available fields; extra bodies retain the first five and put
all bytes from offset five into `remainder`; both have `complete: false`.

Raw-only and malformed results have `complete: false`, `fields: []` and the
entire input body as `remainder`. Malformed JSON input is preserved as supplied,
without claiming it is wire evidence. All snapshots are independent of caller
storage and each other: mutating the caller, raw body, remainder or an earlier
result cannot alter another result or its fields. The operation is pure and
has no history. It cannot overwrite partial last-known-good consumer state;
consumers retain previous evidence beside the current absent/unmapped/error
result without filling missing bytes or relabelling old values as current.

## Synthetic cases

The [example package](fixtures/am22_standard05_candidate_views.json) contains
inputs and full result records; the table below agrees on every case. Identity
changes are named by case ID and specified explicitly in the package. Values
are in field order; null means absent or unmapped as distinguished by domain
state. An empty values array means no candidate interpretation. Raw bytes for
each field are retained in the package. Remainders use JSON byte integers.

| Case | Input body | Status | Complete | Interpretations | Domain states | Remainder |
|---|---|---|---|---|---|---|
| valid | `AA 5A 23 FF FF` | candidate | true | `["heating",90,35,-1,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| explicit-zero | `00 00 00 00 00` | candidate | true | `["shutdown",0,0,0,0]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| outside-3F | `00 00 00 3F 00` | candidate | true | `["shutdown",0,0,63,0]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| short-0 | `` | candidate | false | `[null,null,null,null,null]` | absent,absent,absent,absent,absent | `[]` |
| short-1 | `AA` | candidate | false | `["heating",null,null,null,null]` | in-candidate-domain,absent,absent,absent,absent | `[]` |
| short-2 | `AA 5A` | candidate | false | `["heating",90,null,null,null]` | in-candidate-domain,in-candidate-domain,absent,absent,absent | `[]` |
| short-3 | `AA 5A 23` | candidate | false | `["heating",90,35,null,null]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,absent,absent | `[]` |
| short-4 | `AA 5A 23 FF` | candidate | false | `["heating",90,35,-1,null]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,absent | `[]` |
| extra | `AA 5A 23 FF FF 11 22` | candidate | false | `["heating",90,35,-1,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[17,34]` |
| heat-00 | `00 5A 23 FF FF` | candidate | true | `["shutdown",90,35,-1,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| heat-55 | `55 5A 23 FF FF` | candidate | true | `["DHW",90,35,-1,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| heat-AA | `AA 5A 23 FF FF` | candidate | true | `["heating",90,35,-1,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| heat-CC | `CC 5A 23 FF FF` | candidate | true | `["emission-check",90,35,-1,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| heat-EE | `EE 5A 23 FF FF` | candidate | true | `["controller-stop",90,35,-1,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| heat-DD | `DD 5A 23 FF FF` | candidate | true | `[null,90,35,-1,255]` | unmapped,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| heat-01 | `01 5A 23 FF FF` | candidate | true | `[null,90,35,-1,255]` | unmapped,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| boiler-0 | `AA 00 23 FF FF` | candidate | true | `["heating",0,35,-1,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| boiler-90 | `AA 5A 23 FF FF` | candidate | true | `["heating",90,35,-1,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| boiler-91 | `AA 5B 23 FF FF` | candidate | true | `["heating",91,35,-1,255]` | in-candidate-domain,out-of-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| boiler-100 | `AA 64 23 FF FF` | candidate | true | `["heating",100,35,-1,255]` | in-candidate-domain,out-of-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| boiler-255 | `AA FF 23 FF FF` | candidate | true | `["heating",255,35,-1,255]` | in-candidate-domain,out-of-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| dhw-0 | `AA 2D 00 FF FF` | candidate | true | `["heating",45,0,-1,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| dhw-90 | `AA 2D 5A FF FF` | candidate | true | `["heating",45,90,-1,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| dhw-91 | `AA 2D 5B FF FF` | candidate | true | `["heating",45,91,-1,255]` | in-candidate-domain,in-candidate-domain,out-of-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| dhw-100 | `AA 2D 64 FF FF` | candidate | true | `["heating",45,100,-1,255]` | in-candidate-domain,in-candidate-domain,out-of-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| dhw-255 | `AA 2D FF FF FF` | candidate | true | `["heating",45,255,-1,255]` | in-candidate-domain,in-candidate-domain,out-of-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| outside-0 | `AA 5A 23 00 FF` | candidate | true | `["heating",90,35,0,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| outside-63 | `AA 5A 23 3F FF` | candidate | true | `["heating",90,35,63,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| outside-127 | `AA 5A 23 7F FF` | candidate | true | `["heating",90,35,127,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| outside-128 | `AA 5A 23 80 FF` | candidate | true | `["heating",90,35,-128,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| outside-255 | `AA 5A 23 FF FF` | candidate | true | `["heating",90,35,-1,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| setting-0 | `AA 5A 23 FF 00` | candidate | true | `["heating",90,35,-1,0]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| setting-100 | `AA 5A 23 FF 64` | candidate | true | `["heating",90,35,-1,100]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| setting-101 | `AA 5A 23 FF 65` | candidate | true | `["heating",90,35,-1,101]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| setting-255 | `AA 5A 23 FF FF` | candidate | true | `["heating",90,35,-1,255]` | in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain,in-candidate-domain | `[]` |
| wrong-family-other | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| wrong-variant-standard | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| wrong-operation-06-01 | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| wrong-operation-05-04 | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| wrong-direction-response | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| wrong-direction-positive | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| wrong-selector-automatic | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| positive-prefix | `05 01` | raw-only | false | `[]` | none | `[5,1]` |
| absent-family | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| null-family | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| absent-variant | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| null-variant | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| absent-operation | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| null-operation | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| absent-direction | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| null-direction | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| absent-selector | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| null-selector | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| extra-identity-key | `AA 5A 23 FF FF` | raw-only | false | `[]` | none | `[170,90,35,255,255]` |
| malformed-identity | `AA 5A 23 FF FF` | malformed | false | `[]` | none | `[170,90,35,255,255]` |
| request-prefix | `05 01` | candidate | false | `[null,1,null,null,null]` | unmapped,in-candidate-domain,absent,absent,absent | `[]` |
| malformed-extra | `[170,90,35,255,255,256]` | malformed | false | `[]` | none | `[170,90,35,255,255,256]` |
| malformed-negative | `[-1]` | malformed | false | `[]` | none | `[-1]` |
| malformed-overflow | `[256]` | malformed | false | `[]` | none | `[256]` |
| malformed-bool | `[true]` | malformed | false | `[]` | none | `[true]` |
| malformed-text-byte | `["AA"]` | malformed | false | `[]` | none | `["AA"]` |
| malformed-fraction | `[1.5]` | malformed | false | `[]` | none | `[1.5]` |
| malformed-null | `null` | malformed | false | `[]` | none | `null` |
| malformed-text-body | `"AA 5A 23 FF FF"` | malformed | false | `[]` | none | `"AA 5A 23 FF FF"` |

## Limits and companion

Physical support, presence, freshness, effects, persistence, delivery, execution,
acknowledgement, command acceptance, physical length and empty wire response
remain **Unknown**, independently of grade and completeness. There are no
captures, product models, automatic native qualification, live writes, scan
default changes, transmit routes or active executors in this contract. Existing
eBUS MCP compatibility and GraphQL parity remain unchanged; this page adds no
provider, projection, transport endpoint or command authorization.

AM21 in the registry is the companion implementation slice. This page has no
code dependency; the companion code build holds its merge for this page.
Refs #873 and #736; this is a partial parent slice and does not close the parent.
The [focused contract test](../tests/test_am22_standard05_candidate_views.py)
checks only these declarations and synthetic results with independent expected
numbers. It neither qualifies hardware nor establishes runtime implementation
coverage. Full repository CI and Gate D remain later ship requirements; focused
tests do not claim automatic Gate D discovery. Independent committed-change
review, publication checks and applicable transport classification remain due.
