# B521 named-field results (AQ14)

This pre-1.0 architecture contract evaluates explicitly named B521 fields only.
It is an ordinary companion to AQ13 with no code-merge dependency or unmerged
registry entry. AC21/22 retains B521 metadata; AO25/27 and AP21 retain B522/B523.
This page defines local software behavior, not a native wire contract or a
native-family completeness claim. Native protocol claims require the public
native documentation contract first; none is established by these examples.

## Callable contract and admission

Package `vaillant` exports this pure callable evaluator using only the Go
standard library:

```go
func Ab13Aq13Evaluate(ab13Aq13Input json.RawMessage) (json.RawMessage, error)
```

Retain the existing package spelling. This is a field evaluator, not an
Entries/Lookup catalog or schema. No pending helper, sibling checkout,
initialization side effect, persistent cache, provider registration or automatic
caller is required. This page adds no production implementation. New Go
declarations, parameters, locals, fields, helpers and fixture IDs use the
`ab13aq13` or exported `Ab13Aq13` prefix; tests use `TestAb13Aq13`. Literal
JSON/protocol labels and existing package/library symbols retain their spelling.
This compound stem is distinct from earlier `abNN` names.

The input is one JSON object with `context`, `fields` and optional `arguments`.
`context` contains `primary`, `secondary`, `operation` when present, `direction`,
`view` and opaque family/variant keys. Primary, secondary and present operation
are integers in 0..255. Identifiers select a local candidate view; they never
qualify a family. Family/variant values remain opaque and do not grant support.
The following are the entire supported context set:

| primary | secondary | operation | view | direction | meaning grade |
| --- | --- | --- | --- | --- | --- |
| 181 | 33 | absent | module-fields | request | Hypothesis |
| 181 | 33 | absent | module-fields | positive | Hypothesis |

Absent operation differs from explicit `0` and from `null`. Explicit `0` is an
unsupported context; `null` is invalid, not absence. Other well-formed context
combinations return raw-only `Unknown` without applying any formula.

`fields` maps logical names to byte arrays, each element an integer in 0..255.
Names do not imply byte positions. Explicit empty opaque data `[]` differs from
missing opaque data and is retained; it does not invent a conversion. Empty
fixed-width arrays are incomplete. These two views require no typed arguments;
`arguments` may be absent or `{}`. Extra input keys are retained unchanged,
independently of interpreted fields; they are not new supported arguments,
fields or context combinations. Other opaque fields stay raw and `Unknown`.

Reject malformed or trailing JSON, duplicate keys at any depth, wrong kinds,
nonfinite numbers, fractional or out-of-range bytes or integer arguments, and
missing required typed arguments with an error and no successful result.
Strings, `null` and Booleans are never coerced into numbers. No typed arguments
are required by this finite view set. A missing, short or overlong fixed-width
field is instead a per-field incomplete result: preserve the supplied raw form
and retain complete independent siblings. Invalid byte elements remain admission
errors, not partial successes. Malformed input never becomes a successful
raw-only fallback.

## Finite named fields

Every mapping below has candidate meaning `Hypothesis`. Exact identity,
bit extraction and numeric arithmetic may additionally carry
`calculation: "Proven"`; that never replaces the candidate meaning grade.

| direction | field | width (bytes) | local representation |
| --- | --- | --- | --- |
| request | flags | 1 | Independent bits 0..5 named bit0 through bit5; names Unknown; bits 6..7 reserved |
| request | appliance_bits | 1 | Five independent bits 0..4 named bit0 through bit4; names Unknown; bits 5..7 reserved; no composite enum |
| request | noise_percent | 1 | Identity u8, percent metadata |
| request | frost_temperature | 1 | Identity u8, Celsius metadata |
| positive | status0 | 1 | Flags and reserved bits as listed below |
| positive | status1 | 1 | Flags as listed below |
| positive | brine_percent | 1 | Identity u8, percent metadata, full 0..255 |
| positive | fan_percent | 1 | Identity u8, percent metadata, full 0..255 |
| positive | fan_speed | 1 | u8 multiplied by 10, rpm metadata |
| positive | temperature0 | 2 | Signed little-endian 16-bit integer divided by 16, Celsius metadata |
| positive | temperature1 | 2 | Independent signed little-endian 16-bit integer divided by 16, Celsius metadata |

| bit | status0 | status1 |
| --- | --- | --- |
| 0 | ready | heater |
| 1 | deicing-request | relay-output |
| 2 | deicing-active | fan-running |
| 3 | deicing-timeout-error | brine-flow-reverse |
| 4 | deicing-with-heater | fan-error |
| 5 | reserved (no semantic label) | safety-limiter-error |
| 6 | reserved (no semantic label) | hot-summer |
| 7 | cleaning-request | bad-weather |

Walking one set bit at a time through `status0` gives ready at byte `01`,
deicing-request at `02`, deicing-active at `04`, deicing-timeout-error at `08`,
deicing-with-heater at `10`, reserved bit 5 at `20`, reserved bit 6 at `40`, and
cleaning-request at `80` (hexadecimal bytes). Ready is bit 0, cleaning is bit 7;
reserved bits receive no invented semantic labels. `status1` remains a separate
flag byte, even when the same bit number is set in both bytes.

For temperatures, let the unsigned little-endian carrier be `lo + 256*hi`;
subtract 65536 when it is at least 32768, then divide by 16. The entire signed
carrier domain is valid: -2048 through 2047.9375 Celsius. There is no unavailable
sentinel and no BCD conversion. Percentages are not clipped to 100. Fan speed is
multiplied by 10, never divided by 10.

Declared Boolean defaults are disabled and scalar defaults are 0; these are
schema declarations, never substitutions for missing bytes. Abstract full
request/positive extents 7/12 do not locate unprovided scalars or supply missing
fields. Physical offsets, negative forms, endpoint actions, sequence and native
qualification remain `Unknown`.

## Result shape and examples

Return one JSON object retaining `context`, raw `fields`, `arguments` when
present, and extra keys independently, plus `state`, `results`,
`physical: "Unknown"` and `qualified: false`. Each supplied field result retains
`raw`, `state` and applicable `number`, `label`, `flags`, `reserved`, `unmodeled`,
`candidate_domain` or `alternatives`; do not invent inapplicable conversions or
alternatives. `unit` records the metadata above and `grade` records candidate
meaning. Missing raw data stays absent, not `null`, zero or `[]`.

`complete` means local representation only; `partial` means an expected
fixed-width field is missing or has the wrong length. Unsupported context is
`Unknown`. An unresolved semantic label can coexist with complete raw
arithmetic. Unknown opaque fields do not establish additional supported views.
Retain absent, null, zero, false and explicit empty values independently wherever
permitted, including opaque extra keys; typed numeric slots still reject null.
Input or output storage must not alter a later result or another call.

This complete positive example is synthetic; JSON byte values are decimal:

```json
{
  "context": {"primary":181,"secondary":33,"view":"module-fields","direction":"positive"},
  "fields": {"status0":[129],"status1":[0],"brine_percent":[255],"fan_percent":[255],"fan_speed":[255],"temperature0":[254,255],"temperature1":[0,128]},
  "arguments": {},
  "extra": {"null_value":null,"zero":0,"disabled":false,"empty":[]}
}
```

Its result is:

```json
{
  "context": {"primary":181,"secondary":33,"view":"module-fields","direction":"positive"},
  "fields": {"status0":[129],"status1":[0],"brine_percent":[255],"fan_percent":[255],"fan_speed":[255],"temperature0":[254,255],"temperature1":[0,128]},
  "arguments": {},
  "extra": {"null_value":null,"zero":0,"disabled":false,"empty":[]},
  "state":"complete", "physical":"Unknown", "qualified":false,
  "results": {
    "status0":{"raw":[129],"state":"complete","grade":"Hypothesis","calculation":"Proven","flags":{"ready":true,"deicing-request":false,"deicing-active":false,"deicing-timeout-error":false,"deicing-with-heater":false,"cleaning-request":true},"reserved":{"bit5":false,"bit6":false}},
    "status1":{"raw":[0],"state":"complete","grade":"Hypothesis","calculation":"Proven","flags":{"heater":false,"relay-output":false,"fan-running":false,"brine-flow-reverse":false,"fan-error":false,"safety-limiter-error":false,"hot-summer":false,"bad-weather":false}},
    "brine_percent":{"raw":[255],"state":"complete","grade":"Hypothesis","calculation":"Proven","number":255,"unit":"percent"},
    "fan_percent":{"raw":[255],"state":"complete","grade":"Hypothesis","calculation":"Proven","number":255,"unit":"percent"},
    "fan_speed":{"raw":[255],"state":"complete","grade":"Hypothesis","calculation":"Proven","number":2550,"unit":"rpm"},
    "temperature0":{"raw":[254,255],"state":"complete","grade":"Hypothesis","calculation":"Proven","number":-0.125,"unit":"Celsius"},
    "temperature1":{"raw":[0,128],"state":"complete","grade":"Hypothesis","calculation":"Proven","number":-2048,"unit":"Celsius"}
  }
}
```

A complete request has the same supported identifiers with `direction: "request"`
and, for example, `fields` equal to
`{"flags":[0],"appliance_bits":[31],"noise_percent":[0],"frost_temperature":[0]}`.
The appliance result retains `raw: [31]` (`1F` hexadecimal), is `complete`, has
`grade: "Hypothesis"` and `calculation: "Proven"`, and contains
`flags: {"bit0":true,"bit1":true,"bit2":true,"bit3":true,"bit4":true}` plus
`reserved: {"bit5":false,"bit6":false,"bit7":false}`. These are five flags,
not an enum; their semantic names remain `Unknown`. The other three request
results retain their raw bytes: flags has six false flags and two false reserved
bits; noise_percent is 0 percent and frost_temperature is 0 Celsius. These zero
values arise from supplied bytes, not defaults.

For an independent partial example, remove only `temperature1` from the complete
positive input. The result retains that exact remaining input, has
`state: "partial"`, `physical: "Unknown"` and `qualified: false`, and replaces
only the temperature1 result with `{"state":"partial","grade":"Hypothesis"}`.
Its raw member and number are absent. Temperature0 still returns -0.125 and all
other complete sibling results above remain useful and unchanged. Supplying
`temperature1: [0]`, `[]` or `[0,128,0]` instead retains that array as `raw` in
its partial result without a number. No partial field erases last-known-good
independent sibling results; the evaluator itself has no persistent state.

For an independent unsupported-context example:

```json
{"context":{"primary":181,"secondary":33,"operation":0,"view":"module-fields","direction":"positive"},"fields":{"temperature0":[254,255]},"extra":false}
```

returns raw-only:

```json
{"context":{"primary":181,"secondary":33,"operation":0,"view":"module-fields","direction":"positive"},"fields":{"temperature0":[254,255]},"extra":false,"state":"Unknown","results":{},"physical":"Unknown","qualified":false}
```

No temperature calculation runs for that context. By contrast, an operation of
`null`, a duplicate nested key, a byte of `255.5`, or a trailing JSON object
returns an error with no successful result.

## Evidence boundary

These are finite local candidate views, not family qualification. Complete
arithmetic and `calculation: "Proven"` establish no native support, freshness,
physical support or effects, persistence or delivery; those remain `Unknown`.
No active executor, automatic qualification or execution follows. No missing
position, negative form or endpoint action is inferred. Clipping percentages,
dividing fan speed, applying BCD or a sentinel, labeling reserved bits, merging
flag bytes or inventing scalar coordinates violates this contract.

This companion preserves the eBUS MCP compatibility and GraphQL parity boundary;
it specifies no adapter change or new external transport behavior. Gate D with
its prescribed read-only prerequisites, publication checks and fresh independent
committed-change review remain mandatory before a docs merge. Applicable
transport classification and full repository CI remain later shipping gates.
