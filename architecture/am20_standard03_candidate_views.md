# Standard 03 candidate-body views

Refs helianthus-docs-ebus#870 and helianthus-docs-ebus#736 (partial child;
the parent remains open). Companion AM19 belongs to ebusreg and holds its code
merge for this page; this page has no code dependency on that companion.

## Evidence and scope

The [public native service contract](../protocols/ebus-services/ebus-service-03h.md)
is the protocol authority. Its standard response layouts and candidate request
placements remain distinct. In particular, the standard 03/05 response is not
the three-component alternative below. No new native fact is established here.

**Hypothesis:** these are pure, bounded candidate-body interpretations for the
Vaillant burner family, not a provider decoder. **Proven:** the software contract
adds actual bounded component interpretation beyond metadata tables; existing
metadata, commands and provider behavior stay unchanged. The synthetic checks
prove only this local contract. **Unknown:** physical support, presence,
freshness, execution, physical length, physical request/response placement,
native units, effects, persistence and delivery. Grade is independent of all
qualification and lifecycle states; a syntactically complete result remains
Hypothesis and does not qualify a device or authorize execution.

## Inputs and selection

`view(family, variant, operation, function, direction, selector, body)` takes
explicit software selections and an already isolated body. The executable
contract block below defines the exact, case-sensitive strings. `operation`
is the service identifier, independent of `function`. `family` is a family,
not a product model. No header stripping, direction inference by byte count,
physical-side selection or transport adaptation occurs.

`body` is bytes or bytearray, copied on entry. Other types raise TypeError
before interpretation. The JSON package uses arrays of integers 0..255;
booleans, floats, strings, negative values and values above 255 are malformed
and must raise ValueError at the example-package boundary, without coercion.
Missing, unknown or wrong-typed selection values return raw-only. Absent
selection and explicit zero are both unrecognized and neither selects a mode.

The only admitted selector/direction pairs are candidate/request and
standard/positive for 03/04 and 03/06, and candidate/request for the distinct
03/05 alternative. These labels qualify software interpretation only and make
no physical-side claim. The candidate request placement and standard response
placement stay separate choices even when their components agree. Unknown
functions, variants, families, operations, directions or selectors retain
raw-only. 03/07, 03/08 and 03/10 stay raw-only in this slice, regardless of the
broader native catalog. Nothing selects a layout by body size.

## Bounded components and outputs

Each field is one unsigned byte. 03/04 has three independent decimal chunks
c0, c1 and c2, each 0..99, width 1 and default 0, not packed BCD. The local
display formula is `c0 + 100*c1 + 10000*c2`. The default is metadata only:
an absent byte stays absent and is never filled with zero.

The 03/05 alternative has minutes, hundreds_of_hours and
ten_thousands_of_hours, each 0..59. There is no units-of-hours component,
no units-hour field and no aggregate or total-hours projection. Preserve all
three components independently. Do not import the standard four-byte 03/05
response into this alternative.

The 03/06 alternative has minutes 0..59 and hour chunks h0, h1 and h2, each
0..99. Its optional local display is minutes plus
`h0 + 100*h1 + 10000*h2` local hours; these remain separate from native units.
The block records explicit unsigned-decimal encoding for 03/04 and unspecified
native encoding for the two alternatives. Unspecified encoding does not prevent
a bounded u8 component view, and must not be silently relabeled explicit.

Every successful call returns a fresh object with:

- `raw`: an independently owned list containing every supplied byte, in order.
- `fields`: all selected field names, each with `state`, `raw` and `value`.
  A valid byte has state valid and its integer value; an invalid byte has state
  invalid, its raw integer and null value; an absent byte has state absent,
  null raw and null value. One invalid field never erases another valid field.
- `remainder`: a separate list of bytes beyond the candidate size, or the whole
  body for raw-only. Mutating it must not mutate raw or any other result.
- `complete`: true only for an exact-size body with every component valid.
  The candidate sizes are 3/3/4; these do not establish physical length.
  Short bodies are incomplete; extra bytes remain raw remainder and are
  incomplete even if the prefix is valid. Invalid components are incomplete.
- `projection`: an empty object unless complete; then local_count for 03/04,
  no projection for 03/05, or minutes and local_hours for 03/06. No invalid,
  short or extra body can fabricate a full valid projection.
- `status`: raw-only for unknown selection, incomplete for an admitted but
  incomplete body, or complete. Raw-only has no fields or projection and
  complete false. `encoding` is unspecified for raw-only.
- `grade`: Hypothesis and `native_support`: Unknown, independently of status.

The pure view does not own a cache. Consumers retain partial fields and any
prior last-known-good result under its original identity and provenance;
a new incomplete result cannot overwrite it as a fresh complete value.
Admission remains fail-closed: no result grants a transmit route, scan default,
active executor, automatic native qualification or transport adaptation.
Existing eBUS MCP compatibility and GraphQL parity remain unchanged: no new
endpoint, schema, route or publication behavior is assigned. These selections
are local example-package policy, not a new API namespace. Nothing is stable
before Helianthus 1.0.

## Executable example-package contract

The [synthetic package](fixtures/am20_standard03_candidate_views.json) contains
inputs and expected outputs. The following block must equal its contract.
The [focused unittest](../tests/test_am20_standard03_candidate_views.py) contains
an illustrative pure interpreter only; it is not a production provider.

```json
{
  "family": "vaillant-burner",
  "operation": "03",
  "layouts": {
    "04": {
      "variant": "explicit",
      "encoding": "unsigned-decimal-chunks",
      "fields": [
        [
          "c0",
          99
        ],
        [
          "c1",
          99
        ],
        [
          "c2",
          99
        ]
      ],
      "default": 0,
      "width": 1,
      "projection": "local_count"
    },
    "05": {
      "variant": "alternative",
      "encoding": "unspecified",
      "fields": [
        [
          "minutes",
          59
        ],
        [
          "hundreds_of_hours",
          59
        ],
        [
          "ten_thousands_of_hours",
          59
        ]
      ],
      "default": null,
      "width": 1,
      "projection": null
    },
    "06": {
      "variant": "alternative",
      "encoding": "unspecified",
      "fields": [
        [
          "minutes",
          59
        ],
        [
          "h0",
          99
        ],
        [
          "h1",
          99
        ],
        [
          "h2",
          99
        ]
      ],
      "default": null,
      "width": 1,
      "projection": "local_hours"
    }
  },
  "modes": {
    "04": [
      [
        "candidate",
        "request"
      ],
      [
        "standard",
        "positive"
      ]
    ],
    "05": [
      [
        "candidate",
        "request"
      ]
    ],
    "06": [
      [
        "candidate",
        "request"
      ],
      [
        "standard",
        "positive"
      ]
    ]
  },
  "grade": "Hypothesis",
  "native_support": "Unknown",
  "physical_length": "Unknown",
  "effects": "Unknown",
  "persistence": "Unknown",
  "delivery": "Unknown"
}
```

## Independent controls and limits

| Case | Body hex | Components | Local projection |
|---|---|---|---|
| 03/04 explicit | 63 01 02 | 99/1/2 | 20199 |
| 03/05 alternative | 01 02 03 | 1/2/3 | none |
| 03/06 alternative | 3B 01 02 03 | 59/1/2/3 | minutes 59; hours 30201 |

The package covers each short length including empty, one extra byte, each
field's explicit zero, each independent 99/100 or 59/60 boundary, and absent
and wrong selections on every identity axis. The unittest additionally varies
wrong types, cross-variant choices, selectors, directions and buffer ownership.
These are synthetic software controls, not observations from equipment.

Focused offline tests do not establish automatic discovery by the full docs
gate. Full repository CI, Gate D, publication checks, independent review and
applicable transport classification remain later ship requirements. There is
no transport change or hardware smoke claim in this slice.
