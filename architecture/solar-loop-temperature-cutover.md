# Solar-loop temperature identity and cutover loss

This is a bounded, proposed migration contract for issue #675. It advances
[the north-south flow parent](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/952)
as a partial contract slice; it neither implements publication nor satisfies or
closes the parent. Nothing here is stable before the Helianthus 1.0 release.

Only measured solar temperatures already represented in the native catalog and
current gateway readers are considered. Collector and putative return observations
are separate. Cylinder observations are described solely to prevent substitution
across groups. This page changes no native mapping, producer, pack, fixture, write
route or API. Every requirement described as proposed below is future work.

## Sources and authority

- **N — native contract first:** [B524 register map](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md),
  table legend, Group Topology, GG=0x04 Solar Circuit and GG=0x05 Solar Loaded
  Cylinder. Its `†` rows are CSV value matches with false-positive risk, not
  independently confirmed semantics. Catalog ranges are historical probe hints.
- **L — legacy public contract:** [B524 semantic mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md),
  `ebus.v1.semantic.solar.get` and `ebus.v1.semantic.cylinders.get`.
- **G — corroborating implementation:** [gateway semantic reader](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go),
  solar selector constants, `readSolarSnapshot`, `readCylinderSnapshots`,
  `decodeB524Float32FromRaw`, `readB524ValueWithMaxAge`, `commitFM5Acquisition`,
  `applyFM5Acquisition`, non-destructive merges and `publishFM5Semantic`.
- **T — vocabulary only:** [existing Thermal definitions](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go),
  `fields`, `services`, `dimensions` and `Metadata`.

**Proven** below means a directly inspectable documentation or code fact, with
that evidence scope stated. **Hypothesis** means a candidate physical meaning;
**Unknown** means the supplied sources do not settle it. These labels are separate
from device/profile qualification and runtime admission. No row is newly qualified
by this document. An implementation label, a decoded number or a matching Thermal
field cannot prove sensor location, medium, unit or topology.

## Finite selector and consumer inventory

All rows use PB/SB `B5/24`, read opcode `0x02`; OP=0x06 is a different namespace.
The measured GG=0x04 set is exactly RR=0x0003 and RR=0x0007 at current reader
II=0x00. N's group topology lists a profile interval II=0x00..0x01, while its
GG=0x04 detail says II=0x00 and G reads only that instance. This discrepancy does
not qualify II=0x01; no automatic instance expansion is proposed.

| Observation | Native selector (OP/GG/II/RR) | N row / interpretation status | Current G/L consumer | Proposed disposition |
|---|---|---|---|---|
| Collector candidate | `02/04/00/0003` | `solar_collector_temperature`, f32, °C, hint -40..155; **Hypothesis** (`†`) | `CollectorTemperatureC` in `readSolarSnapshot` → GraphQL `SolarStatus`; legacy MCP solar family in L | Keep exact native observation; canonical fact withheld pending medium, sensor and profile evidence |
| Return candidate | `02/04/00/0007` | `solar_yield_temperature`, f32, °C; no range hint; **Hypothesis** (`†`); physical return location **Unknown** | `solar_return_temp` → `ReturnTemperatureC` through same solar reader/publication | Preserve naming conflict; withhold canonical return projection rather than equating yield and return |
| Separate cylinder boundary, not a GG=0x04 field | `02/05/00/0004` and `02/05/01/0004` | `solar_cylinder_bottom_temperature`, f32, °C, hint -10..110; **Hypothesis** (`†`) | `readCylinderSnapshots` → indexed `CylinderStatus.TemperatureC`; legacy MCP cylinders family in L | No cylinder migration here; never fill collector/return from these observations or create a cylinder from config alone |

N and G's selector/name differences above are **Proven as source differences**,
not proof of physical sensor placement. G's decoder uses little-endian IEEE f32,
rejects fewer than four bytes and non-finite values, accepts a longer buffer's
first four bytes, and does not apply a temperature range. It preserves exact
zero via a non-nil pointer. N explicitly makes f32 byte order profile-dependent;
the characterized controller-family byte order must not be generalized to an
unknown family. Proposed canonical decoding requires a qualified profile's exact
value width, byte order, unit and invalid-value rules. The four-byte examples
below describe the current reader's candidate f32 path, not a new wire contract.

Explicitly excluded: GG=0x04 RR=0x0004 (a candidate K limit, not cylinder or
measured temperature), RR=0x0005/0x0006 protection limits, pump flags/hours,
RR=0x0009 (`CurrentYield` in G but raw flow-rate candidate in N), solar energy
counters, total-energy conversion and calendar changes. No enum interpretation
is added. M14/M15 boiler temperatures, W27 outdoor/aggregate scope and W30
pressure remain outside this contract.

## Proposed input and admission boundary

An input observation must retain the following independently, before any mapping:

| Part | Required content and matching rule |
|---|---|
| Native identity | Opcode, group, instance and little-endian register number; all four match exactly. Preserve request/response bytes, PB/SB, direction and response state beside interpretation. |
| Source | Producing runtime identity and generation plus correlated initiator/target and responder identity; a bus address alone is insufficient across replacement or restart. Public examples use opaque source labels only. |
| Profile | Controller/module family evidence, decoder profile identity and profile revision, with evidence references; missing or conflicting profile evidence withholds canonical projection. |
| Mapping revision | Selected semantic binding revision, kept distinct from profile revision and FM5 evidence revision. A revision change requires revalidation, never relabeling a retained sample. |
| Receipt | Original receipt token/order and original receipt age basis, acquisition versus cache/restore origin, and evidence reference. Cache reads/publications do not mint a new observation or refresh its receipt. |
| Outcome | Bytes and decode outcome, qualified unit if available, per-field validity/freshness and qualification/admission decision, alongside structural FM5 mode/reason/revision. |

These are logical requirements, not a new serialized envelope or field schema.
Use the existing deterministic envelope in later implementation; do not invent a
parallel namespace. A later design must resolve exact API representation before
cutover. Evidence revisions describe evidence changes, not measurement freshness.
Receipt ordering must reject delayed/duplicate samples for an existing identity;
unknown receipt age cannot count as fresh. No new authentication, principal or
permission check is introduced; authentication/authorization are 0.11 subjects.

Admission is fail-closed: correct full identity, coherent qualified profile,
valid correlated reply, known decoding, finite numeric value, applicable qualified
bounds and current structural interpretation must all hold before a new canonical
sample. N's historical ranges alone cannot establish those bounds. Do not invent
a universal range for RR=0x0007. Missing qualification or policy yields withholding,
not guessed acceptance. Preserve rejected raw evidence and its reason separately
from the last good observation. Readability and qualification do not imply writing.

## Proposed existing-pack projection or withholding

T defines `thermal.measurement.water_temperature` with `unit.celsius` and
`thermal.dimension.temperature`; its decimal bounds are -100..200. Those are
pack constraints, not a solar sensor's native range. T also defines
`thermal.service.circuit` keyed by `thermal.dimension.circuit`, and
`thermal.service.dhw` keyed by `thermal.dimension.dhw`. The field dimension and
service fact-key dimension are different roles.

A possible future **Hypothesis** is a qualified water-loop observation using
`thermal.measurement.water_temperature` on `thermal.service.circuit` with its
qualified circuit key. Collector fluid identity and the yield/return location are
**Unknown** here; a solar loop may not be established as water merely by a °C
label. Consequently both GG=0x04 rows currently have **withheld field/service/key
bindings**. No fact is published by this page. The generic candidate is not an
approved binding. There is no new solar pack ID or invented sensor-role dimension.

In particular, collector and return cannot share one field/service/key and
silently overwrite each other. If existing qualified circuit keys cannot distinguish
the two physical observations, withhold both projections until that modeling gap
is resolved by the owning implementation. Cylinder-to-DHW assignment also requires
independent topology evidence and remains outside this slice. Do not substitute
air temperature, DHW setpoint or an energy field to make a mapping fit.

## Current retention and proposed transitions

**Current, source-scoped (G/L):** solar reads mark acquisition activity even when a
particular decoder returns nil. The non-destructive merges replace only non-nil
fields, including zero. Cylinder publication requires a temperature pointer, not
config-only replies. Transient FM5 acquisition reasons preserve the previous
coherent structural mode and snapshot; fresh coherent absence or known
non-interpretable configuration withdraws structural data. With no prior data,
L describes an empty typed MCP solar object and an empty cylinder list. G routes
cache publication through cache setters. These facts do not establish per-field
freshness metadata or complete MCP/GraphQL serialization parity.

**Proposed, future:** retain each last good value with its original identity,
receipt and decoding evidence. A missing/rejected field cannot erase another good
field, renew any receipt, or become zero. A retained historical value may remain
available as retained, but a stale, unknown-age or unqualified value must not be
projected as a current canonical measurement. A source/profile/revision change
quarantines previous values under the old identity; no cross-identity carry-over.
Structural withdrawal continues to remove active family projections while keeping
historical evidence separate. Recovery requires a new, fully matched valid
observation and coherent structural evidence; it restores only the recovered field.

## Synthetic before/after cases

These are manual contract examples, not executed tests or device observations.
Use opaque source `source-A`, profile `profile-A`, revisions `profile-rA` and
`binding-rA`, instance 00, and receipt `receipt-1` for a hypothetical last good
collector value 25 °C. `receipt-2` is a later receipt; no real capture times are
used. “Current” describes G's helper/merge path, conditional on the surrounding
FM5 verdict and parser admitting the reply. “Proposed” describes future behavior
conditional on qualification; with today's gaps canonical output stays withheld.

| Input / transition | Current source-derived before → after | Proposed before → after / intentional loss |
|---|---|---|
| Exact zero, value bytes `00 00 00 00`, later receipt | Non-nil 25 → non-nil 0 in helper/merge | Valid same-identity 25 → 0 with new receipt; preserve numeric zero on both faces, subject to qualification |
| Absent field/no reply | Incoming nil leaves previous 25; other field success may still merge | Retain 25 and receipt-1; mark missing attempt, never manufacture 0 or refresh age; without prior value remain absent |
| NaN `00 00 C0 7F`, +Inf `00 00 80 7F`, -Inf `00 00 80 FF` | Decoder nil → prior 25 retained | Reject each, preserve raw outcome and prior receipt; no current replacement |
| Finite 250, bytes `00 00 7A 43` | Helper accepts 250; merge can replace 25 | Withhold canonical replacement: exceeds existing pack maximum 200; native qualification still needed. No clipping or unit conversion |
| Three-byte value `00 00 C8` | Decoder nil → prior 25 retained | Reject short value; preserve last good and original receipt |
| Five-byte value `00 00 C8 41 00` | Helper decodes first four as 25 if parser supplies it | Require exact qualified four-byte value; reject excess byte. Deliberate stricter future admission; full telegram length is separate |
| Old receipt exceeds future qualified freshness policy | Helpers/merges have no per-field receipt; FM5 evidence staleness may retain snapshot | Retain history at 25; withhold current canonical measurement. No fabricated TTL; unknown policy/age also withholds |
| Foreign II=01 for a GG04/II00 observation | Solar reader requests only II00; helper itself has no identity input | Never update II00. II01 remains unqualified here; receipt-1 and value remain unchanged |
| Foreign source-B, otherwise same selector | Watch key includes target and selector; full proposed source/profile identity is not established by this path | Reject for source-A state; no freshness transfer, even at the same bus address |
| Changed opcode, group or register; changed profile or either revision; replayed receipt | Decoder alone checks none of these; request/parser and FM5 checks provide separate safeguards | Each change independently prevents replacement under the old binding; revalidate a new binding or reject replay, never merge by display name |
| Collector rejected, independently good return update | Non-destructive merge can preserve collector and replace return in interpreted mode | Preserve partial last good state and separate receipts; return's unresolved meaning still withholds its canonical projection |
| Transient FM5 loss → coherent absence/non-interpretable configuration | Prior coherent snapshot retained on transient loss → structural withdrawal on coherent negative evidence | Preserve same distinction; retained 25 is not live, active projections withdrawn on structural negative; archive native evidence |
| Recovery with valid same-identity 26, `00 00 D0 41`, receipt-2 | Interpreted acquisition merges 26; other fields can remain retained | Replace only qualified recovered field, attach new receipt; other fields keep their own age. No recovery from config-only replies or borrowed cylinder value |

No intended change turns an uncertain legacy label into a qualified fact. The
explicit cutover losses are canonical withholding for unresolved identity/unit/
medium/topology, stricter value-length and pack-bound rejection, and loss of
“current” status for retained or unknown-age values. Existing legacy compatibility
must be preserved until an independently accepted cutover proves these differences.

## MCP/GraphQL and later acceptance

A future implementation must project the same admitted observation set and
snapshot revision onto legacy eBUS MCP and GraphQL: same field/source/instance,
value/unit, evidence lineage, retained/fresh decision, structural mode/reason and
withholding decision. Adapt absence to the established face conventions; do not
promise byte-identical serialization. Empty object, omitted optional value,
GraphQL null and empty cylinder list must never become numeric zero. Stable instance
ordering must match G's sorted cylinder publication. If either face cannot express
the required retained/withheld distinction, current canonical publication stays
blocked until the face contract is resolved. Do not claim present parity from the
GraphQL constructor alone.

Later gateway work must cover selector/parser/cache correlation, exact profile
and receipt matching, `readSolarSnapshot`, `commitFM5Acquisition`, per-field merge
and retained-age handling, producer binding and both API adapters. Later HA work
must audit solar temperature entity identity, availability and stale-value handling
against those two faces; no HA source was supplied here, so current HA entity IDs
and behavior are **Unknown**. Any eeBUS output binding belongs in the driver
repository, not in this gateway contract.

Before cutover, owners need public, correlated native replies for each selected
family/profile and concrete selector, response-state/length/byte-order/unit and
invalid-sentinel evidence, independent collector/return location and medium evidence,
qualified bounds/freshness policy, coherent FM5 lifecycle evidence and distinct
existing-pack keys or explicit withholding. Preserve sanitized raw evidence beside
interpretation. Then demonstrate identity-field variations, zero/absence/invalid
and partial recovery behavior, retained cache/restore age, structural withdrawal,
MCP compatibility, GraphQL equivalence and HA acceptance with runtime tests and
appropriate separately authorized device evidence. This contract consumes no
unmerged companion specification and adds no test, runtime admission or hardware
qualification. Full committed-head gates, independent review and all remaining
parent acceptance remain open.
