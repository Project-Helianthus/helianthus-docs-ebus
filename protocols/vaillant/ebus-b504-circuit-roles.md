# B504 circuit temperatures and solar calculations

**Hypothesis:** For the Vaillant B504 family (`PB=0xB5`, `SB=0x04`),
operation, direction, field and circuit role jointly constrain interpretation.
The [public native family contract](ebus-vaillant-b504.md#candidate-op-catalogue)
and [candidate field catalogue](fixtures/b504-b505-candidate-fields.csv)
provide the existing selector context. They are candidate evidence rather than
native qualification. This supplement adds only the finite semantic associations
below; it does not adopt their offsets, widths or conversions as wire proof.

## Candidate relationships

| Operation | Direction | Field | Context | Candidate role | Grade |
| --- | --- | --- | --- | --- | --- |
| 0B | response | reload-delay | solar-storage | solar-storage-charging | Hypothesis |
| 0B | response | parallel-tank-filling | mixer | global-mixer-circuits | Hypothesis |
| 2D | response | room-setpoint | inverter-indoor | indoor-room-setpoint | Hypothesis |
| 2D | response | room-temperature | inverter-indoor | regulation-input | Hypothesis |
| 0D | request | system-support | system | cooling-support-bit-0 | Hypothesis |
| 0D | request | system-generation | system | separate-byte-generation-unknown | Hypothesis |
| 0D | response | dhw-request | dhw | dhw-circuit-request | Hypothesis |
| 0D | response | circuit-temperature | burner | common-sensor-temperature | Hypothesis |
| 0D | response | circuit-temperature | mixer | flow-temperature | Hypothesis |
| 0D | response | circuit-temperature | dhw | tank-temperature | Hypothesis |
| 0D | response | desired-temperature | burner | desired-common-sensor-temperature | Hypothesis |
| 0D | response | desired-temperature | mixer | desired-flow-temperature | Hypothesis |
| 0D | response | desired-temperature | dhw | desired-tank-temperature | Hypothesis |
| 18 | response | unsuppressed-desired-flow | heating | unsuppressed-demand | Hypothesis |
| 18 | response | suppressed-flow | tank-charging | suppressed-zero | Hypothesis |
| 01 | response | drying-day | circuit | nonzero-program-indication | Hypothesis |
| 33 | response | averaged-outside-temperature | system | correction-included | Hypothesis |
| 21 | response | maximum-solar-temperature | solar | all-solar-circuits | Hypothesis |
| 21 | response | tank-state | solar | temperature-to-maximum-percentage | Hypothesis |
| 21 | response | solar-yield | solar | collector-to-tank-switching-ratio | Hypothesis |

**Hypothesis:** OP0D request bit 0 expresses system cooling support. A different
byte carries system generation; neither that byte's position nor its generation
values are selected here. The DHW request has a DHW interpretation only in a DHW
circuit. The circuit temperature and desired temperature follow their own role:
common sensor for burner, flow for mixer and tank for DHW.

**Hypothesis:** OP18 retains an unsuppressed desired-flow demand independently
of a suppressed zero during tank charging. No suppression algorithm is selected.
OP01 drying day 0 has no nonzero-program indication; day 1 has such an indication.
That test does not establish the absence of other programs when day is zero.
OP33's averaged outside temperature includes configured correction; the averaging
window and correction arithmetic are Unknown.

**Hypothesis:** OP21 maximum solar temperature spans solar circuits. Tank state
may express temperature relative to maximum as a percentage; solar yield may
express a collector-to-tank switching ratio. They are different calculated
quantities even when their numeric tokens coincide. Exact formulas are Unknown.
The switching-ratio candidate is not an energy quantity in this supplement.

## Synthetic distinctions

Tokens are logical numeric labels, not encoded telegram bytes or measurements.
No temperature conversion or unit encoding is selected. Each cell retains its
raw token independently of its candidate meaning.

| Cell | Operation | Context | Raw token | Candidate role | Grade |
| --- | --- | --- | --- | --- | --- |
| burner-temperature | 0D | burner | 40 | common-sensor-temperature | Hypothesis |
| mixer-temperature | 0D | mixer | 40 | flow-temperature | Hypothesis |
| dhw-temperature | 0D | dhw | 40 | tank-temperature | Hypothesis |
| burner-desired | 0D | burner | 40 | desired-common-sensor-temperature | Hypothesis |
| mixer-desired | 0D | mixer | 40 | desired-flow-temperature | Hypothesis |
| dhw-desired | 0D | dhw | 40 | desired-tank-temperature | Hypothesis |
| unsuppressed-demand | 18 | heating | 45 | unsuppressed-demand | Hypothesis |
| suppressed-flow | 18 | tank-charging | 0 | suppressed-zero | Hypothesis |
| tank-percentage | 21 | solar | 50 | temperature-to-maximum-percentage | Hypothesis |
| switching-ratio | 21 | solar | 50 | collector-to-tank-switching-ratio | Hypothesis |

| Operation | Context or field | Raw token | Candidate result | Grade |
| --- | --- | --- | --- | --- |
| 0D | dhw | 1 | dhw-circuit-request | Hypothesis |
| 0D | mixer | 1 | no-dhw-interpretation | Hypothesis |
| 0D | burner | 1 | no-dhw-interpretation | Hypothesis |
| 01 | drying-day | 0 | no-nonzero-program-indication | Hypothesis |
| 01 | drying-day | 1 | nonzero-program-indication | Hypothesis |
| 33 | averaged-outside-temperature | 17 | correction-included; arithmetic Unknown | Hypothesis |
| 21 | tank-state | 50 | temperature-to-maximum-percentage; formula Unknown | Hypothesis |
| 21 | solar-yield | 50 | collector-to-tank-switching-ratio; formula Unknown | Hypothesis |

**Unknown:** Unprovided byte positions, widths, generation values, suppression
algorithm, percentage formula, switching-ratio formula, averaging window,
correction arithmetic and wire/unit encodings remain unresolved. Unclassified
circuit roles retain their raw token with Unknown interpretation; a familiar
number cannot select a circuit role. No OP16 conversion, OP20/21 sentinel table,
solar scalar enumeration or preheat-domain table is added.

| Qualification | Value |
| --- | --- |
| Native support | Unknown |
| Physical effects | Unknown |
| Persistence | Unknown |
| Delivery | Unknown |

## Evidence

[The synthetic cases](fixtures/ak02_b504_circuit_roles.json) preserve the equal
40 temperature tokens, independent 45 and 0 flow cells, and equal 50 solar
calculation tokens. Every role cell is varied alone with the others held fixed;
candidate roles remain attached to context rather than numeric equality.
The support and generation tokens are also varied separately. Correction
metadata is retained without arithmetic, and an unclassified circuit retains
its raw token without borrowing another role's interpretation.
Reload delay, mixer filling, room setpoint, room regulation input and maximum
solar temperature also vary independently. The outside-average and configured
correction tokens vary separately with correction-included metadata retained.

**Proven (synthetic representation only):** These distinctions establish the
declared representation. **Hypothesis:** The semantic associations remain
candidates. **Unknown:** Native support, physical effects, persistence and
delivery require separate qualification. These cases provide no native capture,
source/destination pair, firmware context or device observation.
