# B512 valve and pump field results

Refs Project-Helianthus/helianthus-docs-ebus#994 and
Project-Helianthus/helianthus-docs-ebus#736 (partial parent slice).

The [public native B512 contract](../protocols/vaillant/ebus-vaillant-B512.md)
provides the candidate service context first. It leaves native exchanges and
physical layouts unconfirmed. This architecture page defines a finite pre-1.0
local API; its additional branch declarations are local candidate meanings,
not new native evidence. In particular, the native page's OP03 Celsius wording
does not authorize a temperature conversion of the raw OP03 value here.

## Callable surface and admission

Package `vaillant` exports exactly this pure field evaluator, using only the Go
standard library:

```go
func Ab23Aq23Evaluate(ab23Aq23Input json.RawMessage) (json.RawMessage, error)
```

This is a callable contract, not an Entries/Lookup catalog or schema. It needs
no pending helper, sibling checkout, initialization side effect, persistent
cache, provider registration or automatic caller. This companion has no code
merge dependency or unmerged registry entry. It adds no production execution.
Every new Go declaration, parameter, local, field, helper and fixture ID uses
`ab23aq23` or exported `Ab23Aq23`; test functions use `TestAb23Aq23`. The exact
signature above retains its specified parameter spelling. Literal JSON and
protocol labels, existing package/library symbols and standard-library members
retain their spelling. This compound stem is distinct from earlier abNN stems.

Input is one JSON object with `context`, `fields` and optional `arguments`.
`context` contains `primary`, `secondary`, `operation` when present, `direction`,
`view`, and opaque family/variant keys. Numeric identifiers, when present, are
integers in 0..255. An absent operation is not operation 0; explicit null is not
a number and is rejected, rather than coerced to zero or absence. Family and
variant identifiers retain their opaque identity and never qualify a family.
`fields` maps names to byte arrays whose elements are integers in 0..255.
An explicitly opaque empty field is `[]`, distinct from a missing field.

`arguments` contains exactly the typed values stated for the selected view;
OP05 request requires `external_modes`, an array of exactly three u8 integers.
No other required argument is declared here. Unknown extra input keys remain
unchanged at their original level, independently of recognized data; they do
not become additional typed arguments or fields with inferred meaning.
The root names `state`, `results`, `physical`, `qualified` and `timeout` are
reserved for derived output: an input object containing any of them at its root
is an admission error, never overwritten and never nested. Nested names are not
reserved.

Malformed or trailing JSON, duplicate keys at any depth, wrong kinds,
nonfinite numbers, fractional or out-of-range bytes or integer arguments, and
missing required arguments return an error with no successful result. Strings,
null and Booleans are never coerced to numbers. A missing, short or overlong
fixed-width field instead yields a per-field `incomplete` state: retain its raw
form, emit no invented number, and keep complete independent siblings usable.
A missing field has no fabricated raw array; an explicitly supplied array,
including `[]`, remains present. Unstated argument conversions remain Unknown.

## Finite selection and result envelope

**Hypothesis:** primary 181, secondary 18, view `actuator-fields`, and the
operation/direction pairs in the table below select local candidate views.
Field coordinates are logical names, never physical byte offsets. OP00 is
operation 0; OP02/03/04/05 are operations 2/3/4/5. Both `request` and `positive`
are direction identifiers; only pairs with declared fields below apply a
formula. OP00 positive and OP05 positive have no declared field interpretation.
Any unsupported combination, including another view, operation, direction,
primary or secondary, returns raw-only `Unknown`, with no formula applied.
Family/variant keys are retained without inferring supported hardware.

A successful output is one JSON object retaining `context`, raw `fields`,
`arguments` when supplied, and extra keys independently. It adds `state`,
`results`, `physical: "Unknown"`, and `qualified: false`, plus `timeout` only
for the OP04 request selection described below. Each field result
retains `raw` when present, `state`, and applicable `number`, `label`, `flags`,
`reserved`, `unmodeled`, `candidate_domain` or `alternatives`. These optional
members do not imply unspecified flags, reserved-bit meanings or conversions.
Unknown extra input keys are retained at the root unchanged; because the
derived root names are reserved at admission, no retained key can coincide with
an output member.

Envelope `complete` means all declared fixed-width fields are complete local
representations. `partial` means at least one is missing or wrong-width;
independent complete siblings remain available. Unsupported context is
`Unknown`, with no semantic results. An unmapped label or unresolved feedback
source may coexist with complete raw arithmetic. Neither `complete` nor
`partial` is a freshness or qualification claim.

Candidate results carry `grade: "Hypothesis"`; exact arithmetic may additionally
carry `calculation: "Proven"`. A Proven calculation never replaces the candidate
grade. Unknown conversions have no calculated number. Preserve absent, null,
zero, false and explicit empty values independently wherever permitted, including
unknown extra keys. Input/output storage is independently owned: changing a
returned object or input storage cannot alter another result or a later call.
There is no cross-call last-known-good cache; useful partial state survives in
the returned raw data and independent complete siblings.

## Fields and branches

All meanings below are **Hypothesis**. Widths describe named arrays, not telegram
layout. u8 is one byte; LEu16 and signedLE16 are two bytes, least significant
byte first. Decimal ranges are inclusive; FE and FF denote hexadecimal bytes.

| Operation | Direction | Field and width | Local result branches |
| --- | --- | --- | --- |
| OP00 | request | `setpoint`, u8 | 0 `off`; 1..100 `on-or-speed`; 101..255 `unmapped`. Percent is raw identity, with no clipping. |
| OP02 | request | `valve`, u8 | 0 `CH`; 50 `midpoint`; 100 `DHW`; FE `standby`; FF `unchanged`; other values have Unknown meaning and remain raw. |
| OP02 | positive | `valve`, u8 | Raw numeric identity, with `alternatives` (below); no source selected. |
| OP02 | positive | `contact`, u8 | 0 `open`; 1 `closed`; other values `unmapped`. |
| OP02 | positive | `tank`, signedLE16 | Divide the signed integer by 16 for candidate Celsius; no additional sentinel declared. |
| OP02 | positive | `virtual_error`, LEu16 | FFFF `no-error` in this field only; other values retain the numeric error token, with semantic error labels Unknown. |
| OP03 | request | `selector`, u8 | 0 `valve-temperature-input`; other values have Unknown meaning and remain raw. |
| OP03 | positive | `status`, u8 | 0 `okay`; 1 `disconnected`; 2 `short-circuit`; other values have Unknown meaning and remain raw. |
| OP03 | positive | `value`, LEu16 | Raw unsigned integer only; temperature conversion Unknown. |
| OP04 | request | `setpoint`, u8 | 0 `off`, independent of internal demand; 1..100 `on-or-speed`; FF `replacement/no-remote-control`; 101..254 `unmapped`. |
| OP04 | positive | `feedback`, u8 | 1 `accepted`; every other byte `rejected`. Acceptance is a candidate label, not proof of a physical action or readback. |
| OP05 | request | `channel0`, `channel1`, `channel2`, each u8 | Independently: 0 `off`; 1..100 `on-or-speed`; FF `unchanged`; 101..254 `unmapped`. |

For OP02 positive `valve`, a complete result carries `alternatives` as a JSON
array of exactly two strings in this fixed order: `["actual","setpoint-fallback"]`.
Each string names a candidate source of the number; the array holds no nested
objects, no selection flag and no per-source number. An incomplete `valve`
result has no `alternatives` member. Source selection stays Unknown and is
serialized only by the absence of any selected-source member.

Every supported OP04 request result (complete or partial) additionally carries
the root member `timeout` with exactly
`{"seconds":900,"policy":"reset-on-every-service","grade":"Hypothesis"}`
(`seconds` is the JSON integer 900). No other result, including every OP05
result and every `Unknown` result, has a `timeout` member; its absence means the
timeout is Unknown. This is a declaration only, not a running timer,
observed expiry, persistence promise or admission rule. OP05 timeout is
unspecified (`Unknown`) and serialized only by that absence; it never inherits
900 or the OP04 reset declaration.

For OP05 request, result `channel0.prerequisite` depends only on
`arguments.external_modes[0] == 8`; channel1 uses index 1 and channel2 index 2.
Each is true only for its own mode 8 and false otherwise. This local prerequisite
Boolean adds no physical action, admission or successful readback.

## Synthetic examples

All examples are logical field data, not captures or native telegrams. Arrays
use decimal bytes. The complete OP05 request is:

```json
{
  "context": {"primary":181,"secondary":18,"operation":5,"direction":"request","view":"actuator-fields","family":"candidate-family","variant":"candidate-variant"},
  "fields": {"channel0":[100],"channel1":[0],"channel2":[255]},
  "arguments": {"external_modes":[8,0,8]},
  "extra": {"absent_example":null,"zero":0,"enabled":false,"opaque":[]}
}
```

One corresponding complete result (the unchanged input members are shown) is:

```json
{
  "context": {"primary":181,"secondary":18,"operation":5,"direction":"request","view":"actuator-fields","family":"candidate-family","variant":"candidate-variant"},
  "fields": {"channel0":[100],"channel1":[0],"channel2":[255]},
  "arguments": {"external_modes":[8,0,8]},
  "extra": {"absent_example":null,"zero":0,"enabled":false,"opaque":[]},
  "state":"complete",
  "results": {
    "channel0":{"raw":[100],"state":"complete","number":100,"label":"on-or-speed","prerequisite":true,"grade":"Hypothesis","calculation":"Proven"},
    "channel1":{"raw":[0],"state":"complete","number":0,"label":"off","prerequisite":false,"grade":"Hypothesis","calculation":"Proven"},
    "channel2":{"raw":[255],"state":"complete","number":255,"label":"unchanged","prerequisite":true,"grade":"Hypothesis","calculation":"Proven"}
  },
  "physical":"Unknown",
  "qualified":false
}
```

The absence of a `timeout` member in this OP05 result is deliberate; timeout
remains Unknown. The extra null is retained, not turned into an absent key.

A complete OP04 request with fields `{"setpoint":[255]}`, no arguments and
the same context except operation 4 serializes as:

```json
{
  "context": {"primary":181,"secondary":18,"operation":4,"direction":"request","view":"actuator-fields"},
  "fields": {"setpoint":[255]},
  "state":"complete",
  "results": {
    "setpoint":{"raw":[255],"state":"complete","number":255,"label":"replacement/no-remote-control","grade":"Hypothesis","calculation":"Proven"}
  },
  "timeout": {"seconds":900,"policy":"reset-on-every-service","grade":"Hypothesis"},
  "physical":"Unknown",
  "qualified":false
}
```

A complete OP02 positive object, with all four declared sibling fields, serializes as:

```json
{
  "context": {"primary":181,"secondary":18,"operation":2,"direction":"positive","view":"actuator-fields"},
  "fields": {"valve":[50],"contact":[2],"tank":[240,255],"virtual_error":[255,255]},
  "state":"complete",
  "results": {
    "valve":{"raw":[50],"state":"complete","number":50,"alternatives":["actual","setpoint-fallback"],"grade":"Hypothesis","calculation":"Proven"},
    "contact":{"raw":[2],"state":"complete","number":2,"label":"unmapped","grade":"Hypothesis","calculation":"Proven"},
    "tank":{"raw":[240,255],"state":"complete","number":-1,"signed":-16,"grade":"Hypothesis","calculation":"Proven"},
    "virtual_error":{"raw":[255,255],"state":"complete","number":65535,"label":"no-error","grade":"Hypothesis","calculation":"Proven"}
  },
  "physical":"Unknown",
  "qualified":false
}
```

For tank, `signed` is the signed integer and `number` is the candidate Celsius
value (signed integer divided by 16).

For an independent partial example, use the same context and arguments with
`fields: {"channel0":[100],"channel1":[],"channel2":[255,0]}`. The envelope is
`partial`; channel0 retains its complete result and prerequisite true. Channel1
is `incomplete` with raw `[]`; channel2 is `incomplete` with raw `[255,0]`.
Neither incomplete channel has a number or inferred label. Omitting channel1
instead leaves its raw member absent; it does not synthesize `[]` or zero.

For an independent unknown example, change operation to 1 while retaining the
complete example's fields, arguments and extra data. The envelope is `Unknown`,
`results` is empty, and all input data survives raw, with `physical: "Unknown"`
and `qualified: false`. No OP05 channel formula or mode prerequisite applies.
Omitting operation likewise cannot select OP00; operation null is an admission
error, not either of these successful results.

| Synthetic selection | Bytes or arguments | Expected local result |
| --- | --- | --- |
| OP00 request setpoint | `[100]`; `[101]`; `[255]` | 100 `on-or-speed`; 101 and 255 `unmapped`, each number unchanged. |
| OP02 request valve | `[0]`; `[50]`; `[100]`; `[254]`; `[255]` | Five distinct labels: `CH`, `midpoint`, `DHW`, `standby`, `unchanged`. |
| OP02 positive valve | `[50]` | Number 50; alternatives `actual`, `setpoint-fallback`; selected source Unknown. |
| OP02 positive tank | `[240,255]` (F0FF) | Signed integer -16; candidate Celsius -1; calculation Proven, meaning Hypothesis. |
| OP02 positive virtual_error | `[255,255]` | Number 65535, label `no-error`; no sentinel transferred to another field. |
| OP02 positive contact | `[2]` | Number 2, label `unmapped`. |
| OP03 positive value | `[52,18]` (3412) | Number 4660 raw; no temperature number or unit inferred. |
| OP04 request setpoint | `[255]` | `replacement/no-remote-control`, root `timeout` object as serialized above, declaration only. |
| OP04 positive feedback | `[1]`; `[0]`; `[255]` | `accepted`; `rejected`; `rejected`. |
| OP05 request channel0/1/2 | Each `[255]`, modes `[8,0,8]` | Each `unchanged`; prerequisites true/false/true independently; no `timeout` member (Unknown). |

The individual OP02 and OP03 vectors describe field results; a complete positive
object also needs their other declared sibling fields at the widths above.

## Discriminators and limits

The page contract forbids clipping unknown setpoints, inferring actual feedback,
transferring OP02 virtual_error FFFF to another field, scaling OP03 value as a
temperature, merging OP04/OP05 FF or timeout meanings, or sharing one channel's
external-mode gate across all channels. These are page assertions, not claims
about peer implementation behavior.

AE17/AJ05 retains metadata; AO15/16 owns OP01 and AN13/14 owns OP06. AP11..16
covers other fan/heat-pump views. This slice covers only OP00/02/03/04/05.
Native support, family qualification, freshness, physical effects, persistence,
delivery, wire offsets and unstated properties remain Unknown. Candidate grade,
calculation grade and qualification are separate. Existing eBUS MCP compatibility
and GraphQL parity remain requirements; this page introduces no endpoint,
executor, scan-default change or automatic qualification. Nothing is stable
before Helianthus 1.0; no new major or experimental namespace is introduced.
