# B512 selected heat-pump I/O field API

This architecture page defines a **Proven local software contract** for the
heat-pump I/O family. It specifies a prospective pure Go library function; it
makes no claim that the function is implemented here. Candidate family and
behavior results remain **Hypothesis** even when arithmetic is **Proven**.
Physical association, support, freshness, effects, persistence and delivery are
**Unknown**. Every result has `physical="Unknown"` and `qualified=false`.

Native evidence boundary: the public [B512 candidate contract](../protocols/vaillant/ebus-vaillant-B512.md#candidate-sub-commands-op)
is the prerequisite for the candidate OP0F/OP10 correspondence. Its layouts are
unconfirmed on the wire. Logical field arrays below do not assign telegram byte
offsets or assert a device mapping. Additional software flag names and phase
metadata below are local candidate declarations, not stronger native evidence.
The selector is software input, never qualification. The pressure default
conflict remains visible. The inverse byte order and algorithm remain Unknown.

## Signature and JSON envelope

```go
package vaillant

func Ab13Ap13Evaluate(ab13ap13Input json.RawMessage) (json.RawMessage, error)
```

The function uses only the Go standard library. New implementation identifiers
would start with `ab13ap13` or exported `Ab13Ap13`; Go test functions would start
with `TestAb13Ap13`. This page and its fixtures introduce no Go declarations.

Input example (logical arrays, not a wire telegram):

```json
{"context":{"primary":181,"secondary":18,"operation":15,"direction":"request","view":"valve-io","family":"heat-pump","variant":null},"fields":{"output":[0],"valve":[1]},"arguments":{"opaque":false}}
```

Corresponding result shape:

```json
{"context":{"primary":181,"secondary":18,"operation":15,"direction":"request","view":"valve-io","family":"heat-pump","variant":null},"raw":{"output":[0],"valve":[1]},"arguments":{"opaque":false},"state":"complete","fields":{"output":{"raw":[0],"state":"complete","grade":"Hypothesis","flags":{"output0":false,"output1":false},"reserved":0},"valve":{"raw":[1],"state":"complete","grade":"Hypothesis","label":"CH"}},"physical":"Unknown","qualified":false}
```

`context` and `fields` must be objects. Optional `arguments` must be an object;
these views declare no typed or required arguments. All its keys are opaque
extras preserved verbatim, including nested arrays, strings, Booleans and null.
The u8/u16/u32 bounds below apply only to declared typed quantities; they do not
reinterpret opaque keys. No relay vector is declared. Every supplied field value
is a byte array, including unrecognized fields; unrecognized names remain raw
and unmodeled. Missing named fields have no `raw` key in semantic results;
explicit empty arrays retain `raw=[]`. No missing data is filled by defaults.

A successful output retains context unchanged, a deep independent `raw` copy of
fields, arguments exactly when supplied, and semantic `fields`. Errors yield no
successful result. Unsupported selectors yield `state="Unknown"`, semantic
`fields={}`, preserved raw/context/arguments, and no formula application. Selector
comparison is exact and typed; missing keys, explicit null, zero and false remain
distinct in the preserved context. Duplicate keys at any nesting depth are errors.

## Allowed selectors

| primary | secondary | operation | direction | view |
|---|---|---|---|---|
| 181 | 18 | 15 | request | valve-io |
| 181 | 18 | 15 | positive | valve-io |
| 181 | 18 | 16 | request | board-io |
| 181 | 18 | 16 | positive | board-io |

## Field table

`width` is the exact byte-array length. `reserved` is the retained integer mask
of unnamed bits; `flags` contains every named bit as an explicit Boolean.
Unmapped enum values retain raw with `unmodeled=true`, no number or label, and
field state complete as a local representation. Replacement is a label, not a
numeric temperature. The two temperatures branch on bytes `[0,128]` (word
0x8000) **before** signed conversion. LEs16 means `b0+256*b1`, subtract 65536 if
at least 32768, then divide by 16 to obtain Celsius. LEu16 means `b0+256*b1` without narrowing.

| view | direction | field | width | kind | rule | reserved |
|---|---|---|---|---|---|---|
| valve-io | request | output | 1 | flags | 0:output0,1:output1 | 2..7 |
| valve-io | request | valve | 1 | enum | 0:off,1:CH,2:DHW | - |
| valve-io | positive | temperature1 | 2 | temperature | LEs16/16;[0,128]:replacement | - |
| valve-io | positive | temperature2 | 2 | temperature | LEs16/16;[0,128]:replacement | - |
| valve-io | positive | input | 1 | enum | 0:multipurpose,1:utility-contact | - |
| valve-io | positive | pressure | 1 | pressure | u8/10;range=0..25.5;default=255.0;conflict=true | - |
| valve-io | positive | backup | 1 | enum | 0:off,1:step1,2:step2,3:step3,255:replacement | - |
| board-io | request | actuator1 | 1 | flags | 0:cooling-valve,1:passive-mixer1,2:passive-mixer2,3:cooling-active,4:well-pump,5:backup-safety,6:backup1,7:backup2 | - |
| board-io | request | actuator2 | 1 | flags | 0:backup3,1:external-valve,2:external-backup | 3..7 |
| board-io | request | inverse | 2 | opaque | order=Unknown;algorithm=Unknown | - |
| board-io | positive | status | 1 | flags | 0:anode1,1:anode2,2:smart-grid,3:well,4:safety-limiter,5:safety | 6..7 |
| board-io | positive | phase1 | 1 | phase | raw-u8-percent;single-phase~50;three-phase~0/33/66/100;selection=Unknown | - |
| board-io | positive | phase2 | 1 | phase | raw-u8-percent;single-phase~50;three-phase~0/33/66/100;selection=Unknown | - |
| board-io | positive | adc0 | 2 | adc | LEu16;range=0..65535 | - |
| board-io | positive | adc1 | 2 | adc | LEu16;range=0..65535 | - |
| board-io | positive | adc2 | 2 | adc | LEu16;range=0..65535 | - |
| board-io | positive | adc3 | 2 | adc | LEu16;range=0..65535 | - |
| board-io | positive | adc4 | 2 | adc | LEu16;range=0..65535 | - |
| board-io | positive | adc5 | 2 | adc | LEu16;range=0..65535 | - |
| board-io | positive | board | 1 | enum | 0:opaque-code-0,1:opaque-code-1,2:opaque-code-2,3:opaque-code-3,11:opaque-code-11,12:opaque-code-12 | - |

Pressure is exactly byte/10 bar across 0..25.5. Its candidate unset value 255.0
is outside both the byte-derived quantity range and the physical candidate
domain. Preserve `alternatives={"candidate_default":255.0,
"default_in_byte_domain":false,"default_agrees":false}`. Raw FF calculates 25.5,
never 255.0; do not truncate the candidate default to byte 255 and call it an
agreement. Pressure arithmetic has `calculation="Proven"`, while its family grade
stays Hypothesis. Any explicitly declared calculation outside its candidate
domain is retained with `candidate_domain=false`; this does not create a new
calculation for an unknown branch. Valid byte pressure calculations have
`candidate_domain=true`; the conflicting default does not.

Temperatures and ADC calculations likewise carry `calculation="Proven"` without
upgrading their family grade. Backup FF is replacement; FE is unmapped. Inverse
`[18,52]` remains those two bytes, with `unmodeled=true`: no complement, endian
interpretation, or comparison with actuator bytes. Phase numbers are raw u8
percent values. Their `alternatives` retain approximate single-phase 50 and
three-phase 0/33/66/100 metadata with no tolerance and no selected kind. Raw 50
and 33 never choose a phase type. Board codes are named opaque codes; 13 is
unmapped. ADC FFFF is 65535, never clamped to 1023 from another family.

## Representation and transition rules

The following table is normative alongside the field table.

| key | contract |
|---|---|
| signature | package vaillant; Ab13Ap13Evaluate(ab13ap13Input json.RawMessage) (json.RawMessage, error) |
| input | object; context:object; fields:object; arguments?:object |
| arguments | no declared typed arguments or required arguments for these views; opaque extra keys preserved |
| bytes | arrays of integral numbers 0..255; no Boolean, null, string, fraction, float-syntax literal such as 0.0, or coercion |
| validation | malformed JSON, duplicate keys anywhere, wrong container/byte kinds or out-of-range bytes: error; no successful result |
| width | missing, short or overlong named arrays: incomplete; preserve raw and independent complete siblings |
| selector | exact typed tuple; unsupported or missing/null selector: Unknown, raw-only, no formulas |
| context | preserve opaque family, variant and other keys; absent, null, zero and false remain distinct |
| result | context; raw; arguments if supplied; state; fields; physical=Unknown; qualified=false |
| field-result | raw if present; state; grade=Hypothesis; applicable number,label,flags,reserved,unmodeled,candidate_domain,alternatives |
| state | partial if supported and any required field incomplete; otherwise complete; unsupported Unknown |
| grade | family/behavior Hypothesis; exact arithmetic calculation=Proven; physical Unknown; qualified=false |
| unknown | missing/unmapped/incomplete quantities have no number or label; unresolved candidate sibling does not force partial |
| domain | explicit calculation outside candidate domain is retained with candidate_domain=false |
| copy | context, fields, arguments and returned nested storage detached from input, other results and later calls |
| roundtrip | JSON round trips preserve context/raw/state and absent/null/zero distinctions |
| isolation | pure library; no initialization side effect, persistent cache, generic catalog, listing API or runtime caller |
| integers | u8=0..255; u16=0..65535; u32=0..4294967295; integral JSON numbers only when typed; never Boolean |
| defaults | no missing data filled by 0 or false; no relay vector declared in selected views |
| native | selector is software input; no wire offsets, automatic phase selection, ADC10bit narrowing or native qualification |

For supported selectors, a missing/short/overlong independent field produces
`state="incomplete"` for that field and aggregate `state="partial"`. Valid
siblings remain available. This is a per-call last-known-good sibling boundary;
there is no persistent cache or recovery of values from prior calls. Malformed
byte values fail admission for the whole input rather than being reclassified
as incomplete. An unresolved candidate branch can coexist with complete siblings
and aggregate complete. No number or label is invented for missing, incomplete
or unmapped quantities. Raw distinctions and all state/grade distinctions survive
JSON serialization and parsing. Every nested result is independently owned;
mutating input or a returned object cannot change another result or later call.

## Synthetic validation and compatibility

[Owned scenarios](fixtures/ap14_b512_heatpump_io.json) use synthetic logical
fields only. In the scenario tuple records, null `raw` denotes absence and
null `number`/`label` denotes omission from a semantic result; these tuple
placeholders are not the output envelope. The `channels` vectors vary each ADC
independently with zero-valued siblings. [Standard-library tests](../tests/test_ap14_b512_heatpump_io.py)
compare complete page tables with independent constants and exercise bounded
field, admission, selector and partial-state oracles. They validate documentation
and synthetic scenarios; they do not execute a Go runtime implementation or
establish production copy/error behavior. No runtime Python API is provided.

Run the supplemental command explicitly:
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_ap14_b512_heatpump_io.py -v`.
The fixed full Docs gate does not automatically discover this suite. Full CI,
publication checks and fresh independent committed-change review remain later
ship requirements. The public-domain boundary checker also applies.

No transport, eBUS MCP method, GraphQL schema or runtime caller changes here.
MCP compatibility and GraphQL parity remain intact; any later exposure must
preserve identical raw, partial, grade and qualification distinctions. No active
executor, method registration, scan-default change or automatic qualification
follows. Nothing is stable before Helianthus 1.0; no new major or experimental
namespace is introduced. This is a partial slice: Refs #736, which stays open.
