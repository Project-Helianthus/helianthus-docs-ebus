# Standard 07 candidate field views

This pre-1.0 local API contract defines a pure field evaluator for the
`ebus_standard_catalog` package. It is an ordinary companion to AQ15, with no
code-merge dependency or unmerged registry entry. Refs
[the parent scope](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/736)
and [the bounded page scope](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/989).
Nothing here is stable before Helianthus 1.0.

The public [native service contract](../protocols/ebus-services/ebus-service-07h.md),
especially its Vaillant variants and open questions, supplies the evidence
boundary. Its standard descriptions do not fill gaps in these candidate views.
The finite local meanings below are **Hypothesis**, unconfirmed on the wire;
the callable API contract is **Proven** as a local specification, not a claim
that an implementation or physical family has passed qualification.

## Callable and admission

```go
func Ab15Aq15Evaluate(ab15Aq15Input json.RawMessage) (json.RawMessage, error)
```

The evaluator uses only the Go standard library. Retain the existing package
spelling. This page adds no Go file or package: the conditional `catalog/vaillant`
package fallback does not expand its scope. This is a callable field evaluator,
not an Entries/Lookup catalog or another schema. No pending helper, sibling
checkout, initialization side effect, persistent cache, provider registration
or automatic caller is required. Any future Go declarations, parameters,
locals, fields, helpers and fixture IDs use `ab15aq15` or exported `Ab15Aq15`;
test functions use `TestAb15Aq15`. Literal JSON/protocol labels and existing
package/library symbols retain their spelling. The compound stem is distinct
from earlier `abNN` names.

Input is one JSON object:

```json
{
  "context": {"primary": 7, "secondary": 2, "direction": "request", "view": "field-candidates", "family": "candidate-family", "variant": "candidate-variant"},
  "fields": {"temperature": [0, 50], "duration": [0]},
  "arguments": {},
  "extra": {"note": null, "enabled": false, "count": 0, "opaque": []}
}
```

`context` and `fields` are objects; `arguments` is optional and, when present,
an object. `primary`, `secondary` and `operation`, where present, are integers
0..255. Missing `operation` selects these views; explicit zero does not.
Explicit null is a wrong kind, not absence. `direction` and `view` are string
selectors; family/variant keys are opaque and confer no family qualification.
Absent selectors cannot select a supported view. Fields are named arrays of
integer bytes 0..255; an explicitly opaque empty array is valid and differs
from a missing field. No view below declares a typed argument, so none is
required and no argument supplies a block selector or conversion. Unknown extra
keys at every depth are retained unchanged and are not interpreted as arguments.
For any declared typed argument, missing required values, fractions and values
outside its integer range are errors; no additional typed arguments are defined
by this page.

Reject malformed or trailing JSON, duplicate keys at any depth, wrong kinds,
nonfinite numbers, fractional/out-of-range bytes or integer arguments, and
missing required arguments: return an error and no successful JSON result.
Never coerce strings, null or Booleans to numbers. Valid unknown context is a
successful raw-only `Unknown`, not an admission error. Admission is fail-closed:
an error cannot expose a newly successful result or overwrite a caller's
previous last-known-good result.

## Finite selection and fields

All candidate rows require `primary=7`, operation **absent**, and
`view="field-candidates"`. Secondary numbers below are decimal JSON integers;
0700, 0702, 0703 and 0705 denote the corresponding service pairs. Request and
positive directions are independent. Named fields are supplied by the caller;
this API neither selects nor parses physical packets.

| Secondary | Direction | Named fields and exact widths | Local interpretation |
|---|---|---|---|
| 0 | `request` | `temperature`: 2; `weekday`: 1; `second`, `minute`, `hour`, `day`, `month`, `year`: 1 each | Temperature and weekday candidates; calendar raw domains only |
| 2 | `request` | `temperature`: 2; `duration`: 1 | Temperature candidate and raw u8 minutes |
| 3 | `request` | `block`: 1 | Raw block byte only |
| 5 | `request` | `secondary_block`: 1; `primary_block`: 1 | Two independent raw block bytes |
| 3 | `positive` | `version`: 1; `revision`: 1; `bitmap`: 8 | Separate version/revision bytes and raw bitmap vector |
| 5 | `positive` | `version`: 1; `revision`: 1; `bitmap`: 8 | Separate version/revision bytes and raw bitmap vector |

The positive directions for secondary 0 and 2 have no modeled fields here and
remain raw-only `Unknown`. Every other combination also returns raw-only
`Unknown`, without applying a formula: different primary, secondary, operation,
direction or view cannot fall through to a nearby candidate. This includes
0701, 0704 and 07FE/FF. AQ excludes identity parsing, scanning and all command
invocation. AK17/18 retains residual metadata; AE25/26 retains 0704.

| Candidate field | Representation or domain | Semantic limit |
|---|---|---|
| `temperature` (0700/0702 request) | Signed LE16 divided by 256, Celsius | Exact arithmetic may carry `calculation="Proven"`; candidate grade stays `Hypothesis` |
| `temperature` (0702 request) | Signed raw domain -12800..12800, inclusive, yielding -50..50 Celsius | Outside it keep the calculated number and `candidate_domain=false`; never clip, replace or label unavailable |
| `weekday` (0700 request) | Raw u8: 0 Monday, 1 Tuesday, 2 Wednesday, 3 Thursday, 4 Friday, 5 Saturday, 6 Sunday | 7..255 unmapped; arithmetic/raw completeness does not resolve a label |
| `second`, `minute`, `hour` | Candidate domains 0..59, 0..59, 0..23 | Retain raw; complete decimal algorithm `Unknown` |
| `day`, `month`, `year` | Candidate domains 1..31, 1..12, 0..99 | Retain raw; complete decimal algorithm `Unknown` |
| `duration` (0702 request) | Raw u8 minutes, including zero | Zero means only 0 minutes in this view; permanence `Unknown` |
| `block`, `secondary_block`, `primary_block` | Raw u8 | Block-selection meaning and effects `Unknown` |
| `version`, `revision` | Separate raw bytes | Decimal/BCD conversion and combined number `Unknown` |
| `bitmap` | Exactly eight raw bytes, all bits retained | Bit-selection algorithm and executable capability `Unknown` |

Calendar domains are candidate annotations, not a decimal conversion or a
calendar-validity check. Do not apply packed BCD to calendar, version or revision
bytes. The unassociated default literals 6 (0700) and 1 (0702) have no known
field association and are not attached to a field. Responder defaults,
identification, physical availability and timekeeping effects remain `Unknown`.

## Result and partial-state boundaries

Return one JSON object retaining `context`, raw `fields`, optional `arguments`
and extra keys independently, with `state`, `results`, `physical="Unknown"` and
`qualified=false`. Preserve absence, null, zero, false and explicit empty values
where their input kinds permit them. In particular, do not synthesize an absent
arguments object. Input and output storage cannot alter a later result or
another call.

Each named result retains `raw` and `state`, plus applicable `number`, `label`,
`flags`, `reserved`, `unmodeled`, `candidate_domain` or `alternatives`. Only emit
semantic members supported here; no flags, reserved-bit partition or alternative
conversion is assigned to the bitmap. Candidate meanings keep
`grade="Hypothesis"`; an exact calculation can additionally carry
`calculation="Proven"`. Physical support remains `Unknown` regardless of grade.

For supported views, `state="complete"` means local representation only. A
missing, short or overlong fixed-width field yields that field's
`state="incomplete"` and overall `state="partial"`; retain its original raw
array, including an empty or overlong array, with no invented number. Missing
fields remain absent in `fields` and omit `raw` in their incomplete result;
absence must not become null or an empty array. Complete independent siblings
remain available. An empty opaque field stays present as `[]`. An unresolved
label or conversion can coexist with complete raw representation: omit the
unknown number/label and mark the unresolved meaning `Unknown`. For unsupported
context use `state="Unknown"`, preserve all raw input, and produce no interpreted
results (`results={}`). No formula or guessed qualification applies.

## Synthetic results

The complete input above yields this complete local result. All JSON bytes are
decimal; hexadecimal spellings in the examples below are explanatory only.

```json
{
  "context": {"primary": 7, "secondary": 2, "direction": "request", "view": "field-candidates", "family": "candidate-family", "variant": "candidate-variant"},
  "fields": {"temperature": [0, 50], "duration": [0]},
  "arguments": {},
  "extra": {"note": null, "enabled": false, "count": 0, "opaque": []},
  "state": "complete",
  "results": {
    "temperature": {"raw": [0, 50], "state": "complete", "number": 50, "unit": "Celsius", "candidate_domain": true, "grade": "Hypothesis", "calculation": "Proven"},
    "duration": {"raw": [0], "state": "complete", "number": 0, "unit": "minutes", "grade": "Hypothesis", "calculation": "Proven"}
  },
  "physical": "Unknown",
  "qualified": false
}
```

An independent partial example keeps duration useful despite a short temperature:

```json
{
  "context": {"primary": 7, "secondary": 2, "direction": "request", "view": "field-candidates"},
  "fields": {"temperature": [0], "duration": [0]},
  "state": "partial",
  "results": {
    "temperature": {"raw": [0], "state": "incomplete", "grade": "Hypothesis"},
    "duration": {"raw": [0], "state": "complete", "number": 0, "unit": "minutes", "grade": "Hypothesis", "calculation": "Proven"}
  },
  "physical": "Unknown",
  "qualified": false
}
```

An independent unsupported-context result retains an explicitly empty opaque
field and explicit operation zero without interpreting the temperature:

```json
{
  "context": {"primary": 7, "secondary": 2, "operation": 0, "direction": "request", "view": "field-candidates"},
  "fields": {"temperature": [0, 50], "opaque": []},
  "state": "Unknown",
  "results": {},
  "physical": "Unknown",
  "qualified": false
}
```

Additional finite result assertions:

| View/input | Required result |
|---|---|
| 0702 request temperature `00 32` / `[0,50]` | 50 Celsius, domain true |
| 0702 request temperature `00 CE` / `[0,206]` | -50 Celsius, domain true |
| 0702 request temperature `00 80` / `[0,128]` | -128 Celsius, domain false, no unavailable label |
| 0700 request weekday `[6]`, `[7]`, `[255]` (`FF`) | Sunday; unmapped; unmapped, respectively; all raw bytes complete |
| 0702 request duration `[0]` | 0 minutes; permanence remains Unknown |
| 0703 or 0705 positive: version `[18]` (`12` hex), revision `[52]` (`34` hex), bitmap `[128,1,2,4,8,16,32,255]` | Three independent complete raw results; retain `80` and every other bitmap bit; no combined version number |
| 0705 request: secondary `[1]`, primary `[2]` | `secondary_block=[1]`, `primary_block=[2]`; changing secondary to `[3]` keeps primary `[2]`; changing primary to `[4]` keeps secondary `[1]` |
| 0705 request: missing primary, secondary `[1]` | Overall partial; primary incomplete without raw; secondary complete with raw `[1]` |
| 0703 positive: version `[18]`, revision `[52]`, bitmap `[128]` | Overall partial; bitmap incomplete with raw `[128]`; version and revision remain independently complete |

The divisor is **256**, never `/16`. The weekday mapping is **0..6**, never an
import of standard weekday BCD 1..7. Duration zero does not establish permanence.
No unstated calendar or version decoding is permitted. The one-block 0703
request and two-block 0705 request must not merge. A bitmap supplies no executable
capability, authorization or permission to send a command.

This contract adds no production behavior and changes no eBUS MCP or GraphQL
surface; compatibility and parity remain constraints on any later implementation.
It introduces no active executor, scan default or automatic qualification.
Freshness, physical support, effects, persistence and delivery remain `Unknown`;
raw completeness is no native-family completeness claim.
