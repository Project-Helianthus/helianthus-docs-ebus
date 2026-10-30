# B512 OP01 requested values and feedback

**Hypothesis:** The Vaillant B512 family has six independent u8 fields at
logical positions 3..8 on both the request and positive sides of OP01.
Logical positions are not physical offsets. This supplement covers OP01 only;
OP00, OP02, OP04/05 and OP07 retain their separate meanings.

| Logical position | Field | Type | Request grade | Positive grade | Physical offset |
| --- | --- | --- | --- | --- | --- |
| 3 | secondary-heating-pump | u8 | Hypothesis | Hypothesis | Unknown |
| 4 | circulation-pump | u8 | Hypothesis | Hypothesis | Unknown |
| 5 | solar-pump | u8 | Hypothesis | Hypothesis | Unknown |
| 6 | error-relay | u8 | Hypothesis | Hypothesis | Unknown |
| 7 | loading-pump | u8 | Hypothesis | Hypothesis | Unknown |
| 8 | fume-flap | u8 | Hypothesis | Hypothesis | Unknown |

**Hypothesis (candidate token meanings):** Each pump's request FF preserves
that field's previous token. Positive FF instead denotes function unavailable.
Raw tokens and candidate meanings remain independent. Relay and fume-flap
states have no assigned on/off polarity; their polarity association is Unknown.
Other relay/flap values cause no action in this candidate, including 00, 01
and FF. Each field remains independent of the other five fields.

| Fields | Side | Raw token | Candidate meaning | Grade |
| --- | --- | --- | --- | --- |
| secondary-heating-pump, circulation-pump, solar-pump, loading-pump | request | FF | leave-unchanged | Hypothesis |
| secondary-heating-pump, circulation-pump, solar-pump, loading-pump | positive | FF | function-unavailable | Hypothesis |
| error-relay, fume-flap | request and positive | 0F | state-0F | Hypothesis |
| error-relay, fume-flap | request and positive | F0 | state-F0 | Hypothesis |
| error-relay, fume-flap | request and positive | other | no-action | Hypothesis |

**Hypothesis (feedback source):** Without an internal actual signal, feedback
can fall back to setpoint. Feedback equal to setpoint is not sufficient to
classify it as actual. An actual signal can itself equal the setpoint.
The distinction below is conceptual; its wire discriminator is Unknown.
Even the actual-signal candidate does not establish a physical value here.

| Internal actual signal | Feedback source | Physical value | Wire discriminator | Grade |
| --- | --- | --- | --- | --- |
| absent | setpoint-fallback | Unknown | Unknown | Hypothesis |
| present | actual-signal | Unknown | Unknown | Hypothesis |

| Metadata | Value | Grade |
| --- | --- | --- |
| Boolean default | true | Hypothesis |
| Materialized raw default | absent | Unknown |
| Raw default encoding | Unknown | Unknown |
| Relay and fume-flap polarity | Unknown | Unknown |
| Native support | Unknown | Unknown |
| Physical effects | Unknown | Unknown |
| Persistence | Unknown | Unknown |
| Delivery | Unknown | Unknown |

Boolean default true is separate from a materialized raw default. Its byte
encoding is Unknown; raw 01 cannot be inferred from the Boolean default.

## Evidence

[The synthetic cases](fixtures/ak08_b512_feedback_fallback.json) retain raw
logical-field tokens beside candidate interpretations. Request tokens
21, 22, 23, 24, 25, 26 and positive tokens 31, 32, 33, 34, 35, 36 are
synthetic, independent values, not complete telegrams. They carry no source,
destination, capture, firmware or device observation. No physical offset or
wire discriminator is selected by these cases.

**Proven (synthetic representation only):** The cases distinguish all six
positions, direction-specific FF meanings, both declared states, no-action
values, absent/present actual signals, equal feedback and separate default
metadata. This establishes the declared representation only.

**Unknown:** Native support, physical effects, persistence and delivery require
separate qualification. Candidate grades do not imply qualification. No native
capture or specification is established by synthetic consistency.
