# B50F selected field and integrity results

This architecture API companion defines the bounded software contract for
`Ab09Ao09Interpret` in package `vaillant`:

```go
func Ab09Ao09Interpret(ab09ao09Input json.RawMessage) (json.RawMessage, error)
```

It uses the standard library. This is a pure library API: no global cache,
metadata listing, generic catalog, Entries/Lookup API, registration, pending API
import, or runtime call site. New Go declarations, fields, locals, helpers and
fixture IDs use `ab09ao09` or exported `Ab09Ao09`; Go tests begin `TestAb09Ao09`.
Literal JSON keys and existing library symbols retain their spelling.

Refs #931; partial companion to #736. This page has no dependency on AO09 or a
code merge. The local unittest checks documentation and finite expected data;
it does not execute the Go interpreter. Production invocation, aliasing and
production mutation checks require the implementation companion.

## Evidence and selection

The public native starting point is [B50F candidate layouts](../protocols/vaillant/ebus-vaillant.md#b50f-safety-relevant-temperature-status-and-demand).
Those candidate layouts do not establish native support. This software view
uses separately isolated fields and never cuts a physical packet. Absolute
scalar positions, physical support, effects and persistence remain **Unknown**.
Integrity positions below are logical labels, not packet slicing instructions.
All family semantics stay **Hypothesis**; exact arithmetic may additionally
carry `calculation: "Proven"`. Neither a successful call nor an opaque family
or variant nor a view token qualifies a family. Every result has
`physical: "Unknown"` and `qualified: false`.

Selection requires `primary: 181`, `secondary: 15`, integer `operation`,
`direction: "positive"`, and an explicit `view`:

| Operation | View | Selected semantic fields |
| --- | --- | --- |
| 0 | `thermal-fields` | temperature_one/two/three and error_one/two/three |
| 1 | `thermal-fields` | temperature_one/two, stack_voltage and error_one/two/three |
| 2 | `integrity-only` | integrity_one/two only |
| 3 | `demand` | demand and feedback |

Every selected operation may carry optional isolated integrity_one/two. OP02
never borrows thermal semantics. Unknown primary, secondary, operation,
direction, view or an unsupported operation/view combination produces raw-only
`state: "Unknown"`, `fields: {}`. No selection follows from a name, family,
payload length or unmodelled field. An unknown sibling does not erase selected
independent results.

## JSON, validation and ownership

Input is an object with required object `context`, required object `fields`,
and optional object `arguments`. Context requires the five selector keys above;
all extra context keys, including arbitrary JSON family/variant values, survive
unchanged. Primary, secondary and operation must be JSON integers, not booleans
or fractional numbers. Unknown well-typed selectors are successful raw-only
results; malformed selectors are errors. Every fields value is an array of
JSON integers 0..255, including unknown field names and unmodelled tails.

No argument flag or integer is defined by this view: absent arguments and `{}`
are distinct and preserved; nonempty arguments are rejected. No defaults are
injected. Reject malformed JSON, trailing JSON, duplicate object keys at every
depth (including opaque context and arguments), invalid bytes and wrong kinds
with an error and no successful result. Validate even a raw-only branch; JSON
null is not an object, array, byte or integer.

The output object has `context`, `raw`, `state`, `fields`, `physical` and
`qualified`, plus `arguments` exactly when supplied. Context, raw fields and
arguments are independent deep copies. Preserve every byte, even unused tails
and unknown fields. Missing keys remain missing; empty arrays remain empty;
zero remains present. Each emitted result field has its own `raw` and `state`.
For a missing selected field emit `state: "incomplete"` without `raw`; for an
empty supplied field retain `raw: []`. This preserves absence across JSON
round trips. Optional integrity fields are emitted only if supplied.

Consume only the selected isolated field's required prefix, preserving its
entire supplied array in both raw locations. Too few bytes means `incomplete`;
unmodelled tail bytes cannot select another view. Incompleteness of required
selected fields or supplied optional integrity fields makes top-level state
`partial`, while retaining all complete siblings. A selected complete result
has top-level `Hypothesis`; unit-conflict and unknown-order are explicit known
limitations and do not alone mean truncated input. Raw-only Unknown stays
Unknown. No number appears for incomplete, unmapped, unit-conflict,
unknown-order or Unknown fields. The generic optional `candidate_domain`
member does not define a new domain here; no outside-domain carrier is
specified by this view.

## Result fields

| Field | Width | Complete result | Grade boundary |
| --- | --- | --- | --- |
| temperature_one/two/three | 2 | signed LE16 divided by 16, label Celsius; number -1/0/1 for F0 FF / 00 00 / 10 00 | state Hypothesis, calculation Proven |
| error_one/two/three | 1 | raw u8, independent of every adjacent temperature and error; no inferred diagnosis | state Hypothesis; no suppression of temperatures |
| stack_voltage (OP01 only) | 2 | state unit-conflict, label stack-voltage; no voltage number | grade Hypothesis; conflicting temperature conversion metadata unresolved |
| demand | 1 | flags for set bits 0..4, reserved contains bits 5..7 in original bit positions | state Hypothesis; demand is not actuation |
| feedback | 1 | label accepted exactly for 1, otherwise rejected | state Hypothesis; independent of demand and integrity |
| integrity_one/two | 1 each | state unknown-order; independent raw bytes | grade Hypothesis; word order, CRC algorithm and validity Unknown |

Demand flag order is burner, reformer-gas-valve, gas-flow, fan-power, valve.
Reserved masks for 00/01/1F/E0/FF are 0/0/0/224/224; corresponding flag sets
are empty / burner / all five / empty / all five. Feedback rejection is an
interpretation, not an input-validation error. Integrity logical positions are
12/13 for OP00/01, 11/12 for OP02 and 4/5 for OP03. `[12]` and `[34]` remain
two decimal raw byte arrays, never a validated CRC or ordered number.

For example, this partial input:

```json
{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family"},"fields":{"temperature_one":[240,255],"temperature_two":[16],"error_one":[0]},"arguments":{}}
```

retains temperature_one as
`{"raw":[240,255],"state":"Hypothesis","number":-1,"label":"Celsius","calculation":"Proven"}`;
temperature_two is `{"raw":[16],"state":"incomplete"}`; error_one is
`{"raw":[0],"state":"Hypothesis"}`. Other required selected fields have
`{"state":"incomplete"}`. Top-level state is partial, raw/context/arguments
are preserved, physical is Unknown and qualified is false. A temperature error
byte never removes that temperature's independent number.

No active request, executor, UI, scan default, authorization gate or native
qualification is introduced. No permission follows from a candidate label.
The library contract adds no MCP or GraphQL endpoint; existing eBUS MCP
compatibility and GraphQL parity remain required of any future integration.
Nothing is stable before Helianthus 1.0. This introduces no major or experimental
namespace.

## Finite contract table

The JSON block is the machine-readable finite contract table. Its `cases`
contain synthetic inputs and expected **projections**, not complete serialized
outputs: `numbers` maps result field names to exact numbers; `errors` and
`changed_error` identify independent raw u8 values; `integrity` is the two
independent raw arrays; `stack_state` is absent applicability (null) for OP00
or unit-conflict for OP01. `flags`, `reserved` and `feedback` project demand
and feedback results. `incomplete` lists the supplied short fields.
`field_axes` varies each named field's missing/empty/zero/complete/tail and,
for two-byte fields, short condition independently against a complete sibling
control. The missing rows deliberately omit raw; all other rows preserve it.
They specify field-level results, not additional packet layouts.

The fixture repeats this table. The standard-library unittest checks both
against independent numeric and structural constants, rejects changed tables,
and exercises disposable table mutations. It is a documentation ship check;
a passing result does not establish interpreter conformance. Production tests
must call the named Go API and independently vary the same axes, every
operation/view pairing, error bytes, feedback versus integrity, input/result
nested memory, and missing versus empty arguments. No second interpreter is
implemented here. Neither software arithmetic nor these synthetic cases are
native qualification evidence.

<!-- ab09ao09-contract:start -->
```json
{
"contract":{"api":"func Ab09Ao09Interpret(ab09ao09Input json.RawMessage) (json.RawMessage, error)","package":"vaillant","dependencies":"standard library only","selection":[[181,15,0,"positive","thermal-fields"],[181,15,1,"positive","thermal-fields"],[181,15,2,"positive","integrity-only"],[181,15,3,"positive","demand"]],"output_keys":["context","raw","state","fields","physical","qualified"],"optional_output_keys":["arguments"],"physical":"Unknown","qualified":false,"semantic_grade":"Hypothesis","calculation_grade":"Proven","states":["Hypothesis","partial","Unknown"],"field_states":["Hypothesis","incomplete","unit-conflict","unknown-order"],"arguments":{},"thermal_fields":{"0":["temperature_one","temperature_two","temperature_three"],"1":["temperature_one","temperature_two","stack_voltage"]},"error_fields":["error_one","error_two","error_three"],"widths":{"temperature_one":2,"temperature_two":2,"temperature_three":2,"stack_voltage":2,"error_one":1,"error_two":1,"error_three":1,"demand":1,"feedback":1,"integrity_one":1,"integrity_two":1},"temperature_cases":[[[240,255],-1],[[0,0],0],[[16,0],1]],"demand_flags":["burner","reformer-gas-valve","gas-flow","fan-power","valve"],"demand_cases":[[0,[],0],[1,["burner"],0],[31,["burner","reformer-gas-valve","gas-flow","fan-power","valve"],0],[224,[],224],[255,["burner","reformer-gas-valve","gas-flow","fan-power","valve"],224]],"feedback_cases":[[0,"rejected"],[1,"accepted"],[2,"rejected"],[255,"rejected"]],"integrity_positions":{"0":[12,13],"1":[12,13],"2":[11,12],"3":[4,5]},"integrity_cases":[[12],[34]],"integrity_word_order":"Unknown","crc_algorithm":"Unknown","crc_validity":"Unknown","absolute_scalar_positions":"Unknown","unknown_selection":"raw-only Unknown; fields={}; no guessed selection","validation":["malformed JSON","duplicate keys at every object depth","wrong JSON kinds","non-integer or out-of-range bytes","non-integer context primary/secondary/operation","missing required context selectors","nonempty arguments"],"preservation":["every context key","every field byte including tails and unmodelled fields","arguments if supplied","missing versus empty versus explicit zero","independent deep copies","complete independent siblings"],"numeric_forbidden_states":["incomplete","unit-conflict","unknown-order","Unknown"],"forbidden_inferences":["native qualification","actuation","effects","persistence","validated CRC","voltage number","family applicability from view"]},
"cases":[
{"id":"ab09ao09_op0_thermal","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"temperature_three":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0,"temperature_three":1},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":null,"integrity":[[12],[34]]}},
{"id":"ab09ao09_op1_thermal","input":{"context":{"primary":181,"secondary":15,"operation":1,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"stack_voltage":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":"unit-conflict","integrity":[[12],[34]]}},
{"id":"ab09ao09_temperature_-1","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255]}},"expected":{"state":"partial","numbers":{"temperature_one":-1}}},
{"id":"ab09ao09_temperature_0","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[0,0]}},"expected":{"state":"partial","numbers":{"temperature_one":0}}},
{"id":"ab09ao09_temperature_1","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[16,0]}},"expected":{"state":"partial","numbers":{"temperature_one":1}}},
{"id":"ab09ao09_demand_0","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[0],"feedback":[1]}},"expected":{"state":"Hypothesis","flags":[],"reserved":0,"feedback":"accepted","actuation":"Unknown"}},
{"id":"ab09ao09_demand_1","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[1],"feedback":[1]}},"expected":{"state":"Hypothesis","flags":["burner"],"reserved":0,"feedback":"accepted","actuation":"Unknown"}},
{"id":"ab09ao09_demand_31","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[31],"feedback":[1]}},"expected":{"state":"Hypothesis","flags":["burner","reformer-gas-valve","gas-flow","fan-power","valve"],"reserved":0,"feedback":"accepted","actuation":"Unknown"}},
{"id":"ab09ao09_demand_224","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[224],"feedback":[1]}},"expected":{"state":"Hypothesis","flags":[],"reserved":224,"feedback":"accepted","actuation":"Unknown"}},
{"id":"ab09ao09_demand_255","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[255],"feedback":[1]}},"expected":{"state":"Hypothesis","flags":["burner","reformer-gas-valve","gas-flow","fan-power","valve"],"reserved":224,"feedback":"accepted","actuation":"Unknown"}},
{"id":"ab09ao09_feedback_0","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[31],"feedback":[0]}},"expected":{"state":"Hypothesis","flags":["burner","reformer-gas-valve","gas-flow","fan-power","valve"],"feedback":"rejected"}},
{"id":"ab09ao09_feedback_1","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[31],"feedback":[1]}},"expected":{"state":"Hypothesis","flags":["burner","reformer-gas-valve","gas-flow","fan-power","valve"],"feedback":"accepted"}},
{"id":"ab09ao09_feedback_2","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[31],"feedback":[2]}},"expected":{"state":"Hypothesis","flags":["burner","reformer-gas-valve","gas-flow","fan-power","valve"],"feedback":"rejected"}},
{"id":"ab09ao09_feedback_255","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[31],"feedback":[255]}},"expected":{"state":"Hypothesis","flags":["burner","reformer-gas-valve","gas-flow","fan-power","valve"],"feedback":"rejected"}},
{"id":"ab09ao09_integrity_only","input":{"context":{"primary":181,"secondary":15,"operation":2,"direction":"positive","view":"integrity-only","family":"synthetic-family","variant":{"opaque":0}},"fields":{"integrity_one":[12],"integrity_two":[34],"temperature_one":[240,255]}},"expected":{"state":"Hypothesis","integrity":[[12],[34]],"numbers":{},"crc_validity":"Unknown"}},
{"id":"ab09ao09_short_sibling","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240],"temperature_two":[16,0],"error_one":[],"error_two":[9]}},"expected":{"state":"partial","numbers":{"temperature_two":1},"errors":{"error_two":9},"incomplete":["temperature_one","error_one"]}},
{"id":"ab09ao09_unknown_primary","input":{"context":{"primary":180,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"unmodelled":[0,255]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_unknown_secondary","input":{"context":{"primary":181,"secondary":14,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"unmodelled":[0,255]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_unknown_operation","input":{"context":{"primary":181,"secondary":15,"operation":4,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"unmodelled":[0,255]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_unknown_direction","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"negative","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"unmodelled":[0,255]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_unknown_view","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"unrecognised","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"unmodelled":[0,255]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_opaque_family","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":{"opaque":[1]},"variant":{"opaque":0}},"fields":{"temperature_one":[240,255]}},"expected":{"state":"partial","numbers":{"temperature_one":-1},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_opaque_variant","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":["other",0]},"fields":{"temperature_one":[240,255]}},"expected":{"state":"partial","numbers":{"temperature_one":-1},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_vary_error_one","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"temperature_three":[16,0],"error_one":[255],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0,"temperature_three":1},"changed_error":{"error_one":255}}},
{"id":"ab09ao09_vary_error_two","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"temperature_three":[16,0],"error_one":[0],"error_two":[255],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0,"temperature_three":1},"changed_error":{"error_two":255}}},
{"id":"ab09ao09_vary_error_three","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"temperature_three":[16,0],"error_one":[0],"error_two":[1],"error_three":[255],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0,"temperature_three":1},"changed_error":{"error_three":255}}},
{"id":"ab09ao09_bit_2","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[2],"feedback":[1]}},"expected":{"state":"Hypothesis","flags":["reformer-gas-valve"],"reserved":0,"feedback":"accepted","actuation":"Unknown"}},
{"id":"ab09ao09_bit_4","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[4],"feedback":[1]}},"expected":{"state":"Hypothesis","flags":["gas-flow"],"reserved":0,"feedback":"accepted","actuation":"Unknown"}},
{"id":"ab09ao09_bit_8","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[8],"feedback":[1]}},"expected":{"state":"Hypothesis","flags":["fan-power"],"reserved":0,"feedback":"accepted","actuation":"Unknown"}},
{"id":"ab09ao09_bit_16","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[16],"feedback":[1]}},"expected":{"state":"Hypothesis","flags":["valve"],"reserved":0,"feedback":"accepted","actuation":"Unknown"}},
{"id":"ab09ao09_bit_32","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[32],"feedback":[1]}},"expected":{"state":"Hypothesis","flags":[],"reserved":32,"feedback":"accepted","actuation":"Unknown"}},
{"id":"ab09ao09_bit_64","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[64],"feedback":[1]}},"expected":{"state":"Hypothesis","flags":[],"reserved":64,"feedback":"accepted","actuation":"Unknown"}},
{"id":"ab09ao09_bit_128","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[128],"feedback":[1]}},"expected":{"state":"Hypothesis","flags":[],"reserved":128,"feedback":"accepted","actuation":"Unknown"}},
{"id":"ab09ao09_feedback_integrity_0","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[31],"feedback":[1],"integrity_one":[0],"integrity_two":[34]}},"expected":{"state":"Hypothesis","feedback":"accepted","integrity":[[0],[34]],"crc_validity":"Unknown"}},
{"id":"ab09ao09_feedback_integrity_255","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[31],"feedback":[1],"integrity_one":[255],"integrity_two":[34]}},"expected":{"state":"Hypothesis","feedback":"accepted","integrity":[[255],[34]],"crc_validity":"Unknown"}},
{"id":"ab09ao09_pair_0_demand","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"demand":[31]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_pair_0_integrity-only","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"integrity-only","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"demand":[31]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_pair_1_demand","input":{"context":{"primary":181,"secondary":15,"operation":1,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"demand":[31]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_pair_1_integrity-only","input":{"context":{"primary":181,"secondary":15,"operation":1,"direction":"positive","view":"integrity-only","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"demand":[31]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_pair_2_demand","input":{"context":{"primary":181,"secondary":15,"operation":2,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"demand":[31]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_pair_2_thermal-fields","input":{"context":{"primary":181,"secondary":15,"operation":2,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"demand":[31]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_pair_3_thermal-fields","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"demand":[31]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_pair_3_integrity-only","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"integrity-only","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"demand":[31]}},"expected":{"state":"Unknown","fields":{},"physical":"Unknown","qualified":false}},
{"id":"ab09ao09_arguments_absent","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[0],"feedback":[1]}},"expected":{"state":"Hypothesis","arguments_present":false}},
{"id":"ab09ao09_arguments_empty","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[0],"feedback":[1]},"arguments":{}},"expected":{"state":"Hypothesis","arguments_present":true,"arguments":{}}},
{"id":"ab09ao09_op0_temperature_one_negative","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"temperature_three":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0,"temperature_three":1},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":null,"integrity":[[12],[34]]}},
{"id":"ab09ao09_op0_temperature_one_zero","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[0,0],"temperature_two":[0,0],"temperature_three":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":0,"temperature_two":0,"temperature_three":1},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":null,"integrity":[[12],[34]]}},
{"id":"ab09ao09_op0_temperature_one_positive","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[16,0],"temperature_two":[0,0],"temperature_three":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":1,"temperature_two":0,"temperature_three":1},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":null,"integrity":[[12],[34]]}},
{"id":"ab09ao09_op0_temperature_two_negative","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[240,255],"temperature_three":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":-1,"temperature_three":1},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":null,"integrity":[[12],[34]]}},
{"id":"ab09ao09_op0_temperature_two_zero","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"temperature_three":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0,"temperature_three":1},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":null,"integrity":[[12],[34]]}},
{"id":"ab09ao09_op0_temperature_two_positive","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[16,0],"temperature_three":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":1,"temperature_three":1},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":null,"integrity":[[12],[34]]}},
{"id":"ab09ao09_op0_temperature_three_negative","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"temperature_three":[240,255],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0,"temperature_three":-1},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":null,"integrity":[[12],[34]]}},
{"id":"ab09ao09_op0_temperature_three_zero","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"temperature_three":[0,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0,"temperature_three":0},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":null,"integrity":[[12],[34]]}},
{"id":"ab09ao09_op0_temperature_three_positive","input":{"context":{"primary":181,"secondary":15,"operation":0,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"temperature_three":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0,"temperature_three":1},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":null,"integrity":[[12],[34]]}},
{"id":"ab09ao09_op1_temperature_one_negative","input":{"context":{"primary":181,"secondary":15,"operation":1,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"stack_voltage":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":"unit-conflict","integrity":[[12],[34]]}},
{"id":"ab09ao09_op1_temperature_one_zero","input":{"context":{"primary":181,"secondary":15,"operation":1,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[0,0],"temperature_two":[0,0],"stack_voltage":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":0,"temperature_two":0},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":"unit-conflict","integrity":[[12],[34]]}},
{"id":"ab09ao09_op1_temperature_one_positive","input":{"context":{"primary":181,"secondary":15,"operation":1,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[16,0],"temperature_two":[0,0],"stack_voltage":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":1,"temperature_two":0},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":"unit-conflict","integrity":[[12],[34]]}},
{"id":"ab09ao09_op1_temperature_two_negative","input":{"context":{"primary":181,"secondary":15,"operation":1,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[240,255],"stack_voltage":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":-1},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":"unit-conflict","integrity":[[12],[34]]}},
{"id":"ab09ao09_op1_temperature_two_zero","input":{"context":{"primary":181,"secondary":15,"operation":1,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"stack_voltage":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":"unit-conflict","integrity":[[12],[34]]}},
{"id":"ab09ao09_op1_temperature_two_positive","input":{"context":{"primary":181,"secondary":15,"operation":1,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[16,0],"stack_voltage":[16,0],"error_one":[0],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":1},"errors":{"error_one":0,"error_two":1,"error_three":2},"stack_state":"unit-conflict","integrity":[[12],[34]]}},
{"id":"ab09ao09_op1_vary_error_one","input":{"context":{"primary":181,"secondary":15,"operation":1,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"stack_voltage":[16,0],"error_one":[255],"error_two":[1],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0},"errors":{"error_one":255,"error_two":1,"error_three":2},"stack_state":"unit-conflict","integrity":[[12],[34]]}},
{"id":"ab09ao09_op1_vary_error_two","input":{"context":{"primary":181,"secondary":15,"operation":1,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"stack_voltage":[16,0],"error_one":[0],"error_two":[255],"error_three":[2],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0},"errors":{"error_one":0,"error_two":255,"error_three":2},"stack_state":"unit-conflict","integrity":[[12],[34]]}},
{"id":"ab09ao09_op1_vary_error_three","input":{"context":{"primary":181,"secondary":15,"operation":1,"direction":"positive","view":"thermal-fields","family":"synthetic-family","variant":{"opaque":0}},"fields":{"temperature_one":[240,255],"temperature_two":[0,0],"stack_voltage":[16,0],"error_one":[0],"error_two":[1],"error_three":[255],"integrity_one":[12],"integrity_two":[34]}},"expected":{"state":"Hypothesis","numbers":{"temperature_one":-1,"temperature_two":0},"errors":{"error_one":0,"error_two":1,"error_three":255},"stack_state":"unit-conflict","integrity":[[12],[34]]}},
{"id":"ab09ao09_feedback_integrity_two_0","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[31],"feedback":[1],"integrity_one":[12],"integrity_two":[0]}},"expected":{"state":"Hypothesis","feedback":"accepted","integrity":[[12],[0]],"crc_validity":"Unknown"}},
{"id":"ab09ao09_feedback_integrity_two_255","input":{"context":{"primary":181,"secondary":15,"operation":3,"direction":"positive","view":"demand","family":"synthetic-family","variant":{"opaque":0}},"fields":{"demand":[31],"feedback":[1],"integrity_one":[12],"integrity_two":[255]}},"expected":{"state":"Hypothesis","feedback":"accepted","integrity":[[12],[255]],"crc_validity":"Unknown"}}
],
"invalid_json":[
{"id":"ab09ao09_malformed","json":"{","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_duplicate_root","json":"{\"context\":{},\"context\":{},\"fields\":{}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_duplicate_context","json":"{\"context\":{\"primary\":181,\"primary\":181},\"fields\":{}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_duplicate_field","json":"{\"context\":{},\"fields\":{\"demand\":[1],\"demand\":[1]}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_duplicate_opaque","json":"{\"context\":{\"variant\":{\"x\":1,\"x\":2}},\"fields\":{}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_array_root","json":"[]","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_null_root","json":"null","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_negative","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":0,\"direction\":\"positive\",\"view\":\"thermal-fields\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{\"temperature_one\":[-1]}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_overflow","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":0,\"direction\":\"positive\",\"view\":\"thermal-fields\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{\"temperature_one\":[256]}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_fraction","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":0,\"direction\":\"positive\",\"view\":\"thermal-fields\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{\"temperature_one\":[1.5]}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_boolean","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":0,\"direction\":\"positive\",\"view\":\"thermal-fields\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{\"temperature_one\":[true]}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_string","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":0,\"direction\":\"positive\",\"view\":\"thermal-fields\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{\"temperature_one\":[\"1\"]}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_null_element","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":0,\"direction\":\"positive\",\"view\":\"thermal-fields\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{\"temperature_one\":[null]}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_nonarray","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":0,\"direction\":\"positive\",\"view\":\"thermal-fields\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{\"temperature_one\":1}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_null_array","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":0,\"direction\":\"positive\",\"view\":\"thermal-fields\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{\"temperature_one\":null}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_selector_primary_missing","json":"{\"context\":{\"secondary\":15,\"operation\":3,\"direction\":\"positive\",\"view\":\"demand\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_selector_primary_wrong-kind","json":"{\"context\":{\"primary\":true,\"secondary\":15,\"operation\":3,\"direction\":\"positive\",\"view\":\"demand\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_selector_secondary_missing","json":"{\"context\":{\"primary\":181,\"operation\":3,\"direction\":\"positive\",\"view\":\"demand\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_selector_secondary_wrong-kind","json":"{\"context\":{\"primary\":181,\"secondary\":true,\"operation\":3,\"direction\":\"positive\",\"view\":\"demand\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_selector_operation_missing","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"direction\":\"positive\",\"view\":\"demand\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_selector_operation_wrong-kind","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":true,\"direction\":\"positive\",\"view\":\"demand\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_selector_direction_missing","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":3,\"view\":\"demand\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_selector_direction_wrong-kind","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":3,\"direction\":true,\"view\":\"demand\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_selector_view_missing","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":3,\"direction\":\"positive\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_selector_view_wrong-kind","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":3,\"direction\":\"positive\",\"view\":true,\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_kind_context","json":"{\"context\":null,\"fields\":{}}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_kind_fields","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":3,\"direction\":\"positive\",\"view\":\"demand\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":[]}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_kind_arguments","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":3,\"direction\":\"positive\",\"view\":\"demand\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{},\"arguments\":null}","expected":{"error":true,"successful_result":false}},
{"id":"ab09ao09_kind_arguments_nonempty","json":"{\"context\":{\"primary\":181,\"secondary\":15,\"operation\":3,\"direction\":\"positive\",\"view\":\"demand\",\"family\":\"synthetic-family\",\"variant\":{\"opaque\":0}},\"fields\":{},\"arguments\":{\"flag\":1}}","expected":{"error":true,"successful_result":false}}
],
"field_axes":[
{"id":"ab09ao09_temperature_one_missing","field":"temperature_one","presence":"missing","state":"incomplete"},
{"id":"ab09ao09_temperature_one_empty","field":"temperature_one","presence":"empty","state":"incomplete","raw":[]},
{"id":"ab09ao09_temperature_one_zero","field":"temperature_one","presence":"zero","state":"Hypothesis","raw":[0,0],"number":0},
{"id":"ab09ao09_temperature_one_complete","field":"temperature_one","presence":"complete","state":"Hypothesis","raw":[16,0],"number":1},
{"id":"ab09ao09_temperature_one_tail","field":"temperature_one","presence":"tail","state":"Hypothesis","raw":[16,0,255],"number":1},
{"id":"ab09ao09_temperature_one_short","field":"temperature_one","presence":"short","state":"incomplete","raw":[16]},
{"id":"ab09ao09_temperature_two_missing","field":"temperature_two","presence":"missing","state":"incomplete"},
{"id":"ab09ao09_temperature_two_empty","field":"temperature_two","presence":"empty","state":"incomplete","raw":[]},
{"id":"ab09ao09_temperature_two_zero","field":"temperature_two","presence":"zero","state":"Hypothesis","raw":[0,0],"number":0},
{"id":"ab09ao09_temperature_two_complete","field":"temperature_two","presence":"complete","state":"Hypothesis","raw":[16,0],"number":1},
{"id":"ab09ao09_temperature_two_tail","field":"temperature_two","presence":"tail","state":"Hypothesis","raw":[16,0,255],"number":1},
{"id":"ab09ao09_temperature_two_short","field":"temperature_two","presence":"short","state":"incomplete","raw":[16]},
{"id":"ab09ao09_temperature_three_missing","field":"temperature_three","presence":"missing","state":"incomplete"},
{"id":"ab09ao09_temperature_three_empty","field":"temperature_three","presence":"empty","state":"incomplete","raw":[]},
{"id":"ab09ao09_temperature_three_zero","field":"temperature_three","presence":"zero","state":"Hypothesis","raw":[0,0],"number":0},
{"id":"ab09ao09_temperature_three_complete","field":"temperature_three","presence":"complete","state":"Hypothesis","raw":[16,0],"number":1},
{"id":"ab09ao09_temperature_three_tail","field":"temperature_three","presence":"tail","state":"Hypothesis","raw":[16,0,255],"number":1},
{"id":"ab09ao09_temperature_three_short","field":"temperature_three","presence":"short","state":"incomplete","raw":[16]},
{"id":"ab09ao09_stack_voltage_missing","field":"stack_voltage","presence":"missing","state":"incomplete"},
{"id":"ab09ao09_stack_voltage_empty","field":"stack_voltage","presence":"empty","state":"incomplete","raw":[]},
{"id":"ab09ao09_stack_voltage_zero","field":"stack_voltage","presence":"zero","state":"unit-conflict","raw":[0,0]},
{"id":"ab09ao09_stack_voltage_complete","field":"stack_voltage","presence":"complete","state":"unit-conflict","raw":[16,0]},
{"id":"ab09ao09_stack_voltage_tail","field":"stack_voltage","presence":"tail","state":"unit-conflict","raw":[16,0,255]},
{"id":"ab09ao09_stack_voltage_short","field":"stack_voltage","presence":"short","state":"incomplete","raw":[16]},
{"id":"ab09ao09_error_one_missing","field":"error_one","presence":"missing","state":"incomplete"},
{"id":"ab09ao09_error_one_empty","field":"error_one","presence":"empty","state":"incomplete","raw":[]},
{"id":"ab09ao09_error_one_zero","field":"error_one","presence":"zero","state":"Hypothesis","raw":[0]},
{"id":"ab09ao09_error_one_complete","field":"error_one","presence":"complete","state":"Hypothesis","raw":[7]},
{"id":"ab09ao09_error_one_tail","field":"error_one","presence":"tail","state":"Hypothesis","raw":[7,255]},
{"id":"ab09ao09_error_two_missing","field":"error_two","presence":"missing","state":"incomplete"},
{"id":"ab09ao09_error_two_empty","field":"error_two","presence":"empty","state":"incomplete","raw":[]},
{"id":"ab09ao09_error_two_zero","field":"error_two","presence":"zero","state":"Hypothesis","raw":[0]},
{"id":"ab09ao09_error_two_complete","field":"error_two","presence":"complete","state":"Hypothesis","raw":[7]},
{"id":"ab09ao09_error_two_tail","field":"error_two","presence":"tail","state":"Hypothesis","raw":[7,255]},
{"id":"ab09ao09_error_three_missing","field":"error_three","presence":"missing","state":"incomplete"},
{"id":"ab09ao09_error_three_empty","field":"error_three","presence":"empty","state":"incomplete","raw":[]},
{"id":"ab09ao09_error_three_zero","field":"error_three","presence":"zero","state":"Hypothesis","raw":[0]},
{"id":"ab09ao09_error_three_complete","field":"error_three","presence":"complete","state":"Hypothesis","raw":[7]},
{"id":"ab09ao09_error_three_tail","field":"error_three","presence":"tail","state":"Hypothesis","raw":[7,255]},
{"id":"ab09ao09_demand_missing","field":"demand","presence":"missing","state":"incomplete"},
{"id":"ab09ao09_demand_empty","field":"demand","presence":"empty","state":"incomplete","raw":[]},
{"id":"ab09ao09_demand_zero","field":"demand","presence":"zero","state":"Hypothesis","raw":[0]},
{"id":"ab09ao09_demand_complete","field":"demand","presence":"complete","state":"Hypothesis","raw":[7]},
{"id":"ab09ao09_demand_tail","field":"demand","presence":"tail","state":"Hypothesis","raw":[7,255]},
{"id":"ab09ao09_feedback_missing","field":"feedback","presence":"missing","state":"incomplete"},
{"id":"ab09ao09_feedback_empty","field":"feedback","presence":"empty","state":"incomplete","raw":[]},
{"id":"ab09ao09_feedback_zero","field":"feedback","presence":"zero","state":"Hypothesis","raw":[0]},
{"id":"ab09ao09_feedback_complete","field":"feedback","presence":"complete","state":"Hypothesis","raw":[7]},
{"id":"ab09ao09_feedback_tail","field":"feedback","presence":"tail","state":"Hypothesis","raw":[7,255]},
{"id":"ab09ao09_integrity_one_missing","field":"integrity_one","presence":"missing","state":"incomplete"},
{"id":"ab09ao09_integrity_one_empty","field":"integrity_one","presence":"empty","state":"incomplete","raw":[]},
{"id":"ab09ao09_integrity_one_zero","field":"integrity_one","presence":"zero","state":"unknown-order","raw":[0]},
{"id":"ab09ao09_integrity_one_complete","field":"integrity_one","presence":"complete","state":"unknown-order","raw":[7]},
{"id":"ab09ao09_integrity_one_tail","field":"integrity_one","presence":"tail","state":"unknown-order","raw":[7,255]},
{"id":"ab09ao09_integrity_two_missing","field":"integrity_two","presence":"missing","state":"incomplete"},
{"id":"ab09ao09_integrity_two_empty","field":"integrity_two","presence":"empty","state":"incomplete","raw":[]},
{"id":"ab09ao09_integrity_two_zero","field":"integrity_two","presence":"zero","state":"unknown-order","raw":[0]},
{"id":"ab09ao09_integrity_two_complete","field":"integrity_two","presence":"complete","state":"unknown-order","raw":[7]},
{"id":"ab09ao09_integrity_two_tail","field":"integrity_two","presence":"tail","state":"unknown-order","raw":[7,255]}
]
}
```
<!-- ab09ao09-contract:end -->
