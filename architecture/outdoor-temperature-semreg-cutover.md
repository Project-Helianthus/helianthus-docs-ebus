# Outdoor temperature SemReg cutover contract

> **License:** AGPL-3.0. Proposed Helianthus read-only cutover requirements;
> this page does not enable a producer or qualify a controller.

This is the instantaneous `state.outdoor_temperature` slice of gateway #952,
Project #2 INT-08. The parent remains open. The rolling
`state.outdoor_temperature_avg24h` is explicitly excluded from instantaneous
publication. This slice is distinct from the M14/M15 boiler group and changes
no shared mapping, fixture, native fact, admission rule or qualification rule.
The contract is evolving; nothing is stable before Helianthus 1.0.

## Public authority and current boundary

Start with the native [B524 wire contract](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524.md)
and [register catalog](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md).
The catalog distinguishes read-only outdoor temperature at `RR=0x0073` from
the rounded average at `RR=0x0095`, updated every three hours. A register name
or implementation label alone does not qualify an installation.

The existing [semantic mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md)
and [typed Thermal map](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/fixtures/vaillant-semreg-thermal-map-v1.json)
define the candidate mapping below, including the aggregate loss disposition.
They document the current legacy MCP system fields, but describe the SemReg
binding as future and qualified. The public [GraphQL contract](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/api/graphql.md)
separately declares `SystemState.outdoorTemperature` and
`SystemState.outdoorTemperatureAvg24h` as nullable floats.

**Proven — document agreement:** these public contracts distinguish the two
selectors and exclude the aggregate from the instantaneous fact.
**Hypothesis — application to a target:** the exact read-only candidate still
requires its qualified runtime binding. **Unknown — current qualification:**
the [qualification evidence-gap record](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/fixtures/vaillant-controller-qualification-v1.json)
has `evidence_status=Unknown` and `qualified_use_permitted=false`; the typed
map has `runtime_qualification_permitted=false`. No admitted SemReg outdoor
observation follows from those artifacts today. Proven/Hypothesis/Unknown are
evidence conclusions, separate from runtime qualification, acquisition,
validity, freshness and admission. The conditional qualified cases below are
requirements for future acceptance, not new qualification or runtime proof.

## Exact mapping and source join

| Field | Existing native contract | Proposed cutover result |
| --- | --- | --- |
| Instantaneous `state.outdoor_temperature` | VRC720-family controller; `PB=0xB5`, `SB=0x24`, `OP=0x02`, `GG=0x00`, `II=0x00`, `RR=0x0073`, destination `0x15`; qualified initiator to target request, target to the same initiator value reply; profile-scoped IEEE-754 `f32` little-endian, `degC` | `thermal.measurement.air_temperature`, quantity `unit.celsius`, exactly `thermal.dimension.temperature=temperature:outdoor_air`; read-only exact numeric candidate, admitted only after existing binding and lifecycle requirements succeed |
| Aggregate `state.outdoor_temperature_avg24h` | Same service, operation, group, instance, destination, family and directions, but `RR=0x0095`; `f32` little-endian, `degC`; rounded rolling average | No SemReg fact, value or dimensions; existing disposition `withheld`, loss `rolling_average_window_unrepresentable` |

The initiator address is binding evidence, not a constant selected here.
Destination alone never chooses byte order. Other controller families,
heat-pump codecs, `OP=0x06` namespaces, B509, system-flow, circuit and boiler
temperatures do not substitute for this exact observation. Do not infer a
write route or a full service capability from this read-only mapping.

Join each native observation to the **same current binding** using all of:

| Join member | Requirement |
| --- | --- |
| Asset and service | Exact qualified asset and `thermal.service.system` identity; no join through a public display, zone or GraphQL ID |
| Native route | Request initiator, response target and directions, destination, family/profile, PB, SB, opcode, group, instance and register must match the binding and correlated response |
| Runtime source | Exact source identity, source epoch and driver generation; replacement or a generation change cannot inherit old source evidence |
| Interpretation and proof | Codec/unit, evidence reference, qualification and semantic revision belong to that observation and binding; a newer registry snapshot must not lend proof to an older unrelated sample |
| Time and policy | Original receipt clocks and applicable freshness/retention policy must be available and compatible at evaluation |

These are binding metadata, not extra FactKey dimensions.
`thermal.dimension.system` is not added. An incomplete or mismatched join
withholds the candidate. Preserve raw request/reply evidence and the retained
interpretation separately; never merge the average into the instantaneous
observation because the unit, route or displayed value agrees.

## Value and lifecycle requirements

All requirements in this section are proposed cutover behavior. No new
implementation behavior is asserted from documentation inspection.

| Input or event | Required transition |
| --- | --- |
| Complete, correlated, admitted finite value | Decode with the exact existing codec/unit; replace only this binding's instantaneous observation after all existing validity and freshness requirements succeed |
| Valid zero | Four value bytes `00 00 00 00` mean `0 °C`; zero is present, not missing or false. Keep the raw bytes; use no truthiness test |
| Replacement/no-data or nonfinite | The native page documents `00 00 C0 7F` as one NaN/no-data example. Withhold any decoded NaN or positive/negative infinity as a semantic measurement; retain raw evidence. This finite-value requirement does not claim native meaning for every NaN pattern or infinity, which remains open. Apply only evidenced profile-specific replacement rules; invent no finite replacement sentinel |
| Short, mismatched, failed or otherwise invalid reply | No measurement update; preserve the prior field-local last-known-good observation and its original identity/time within its existing policy. Failure is not zero and not a new receipt of the retained value |
| Source/controller replacement or qualification conflict | Withhold immediately; keep old evidence separately, but never relabel the old value as belonging to the replacement. Follow existing qualification retirement rules; do not redesign recovery |
| Delayed evaluation, cache hit or repeated publication | Reuse original observation metadata; no new acquisition, qualification, receipt or age reset |
| Stale or expired observation | Retained evidence may remain available diagnostically. It cannot be presented as a fresh instantaneous measurement. At retention expiry remove its consumer value; never borrow the aggregate |

Do not round to display precision, clamp invalid values, or synthesize defaults
to obtain parity. Any existing semantic value validation must also succeed;
this page creates neither numeric bounds nor a new validator.

Preserve `received_at` and `receipt_monotonic` from the retained native
observation. Keep `evaluated_at` and `evaluate_monotonic` separate, as in the
typed map's distinct receipt/evaluation vector. For a known compatible
monotonic epoch, age is evaluation minus original receipt. Negative elapsed
time, missing clocks or incompatible epochs cannot prove freshness. Unknown
source/phenomenon time stays unknown, never filled from publication time.

No numeric outdoor freshness or retention duration is established by these
anchors. Use only an accepted policy with known identity and deadlines;
unknown policy, clock or qualifier withholds admission. A stale last-known-good
may be exposed only if the existing surface can carry the accepted stale
disposition, original age and remaining retention; a bare float cannot prove
that distinction and must be withheld. Retaining native evidence is separate
from consumer admission.

A value-only legacy cache cannot reconstruct a qualified observation. Restart
must not reset its receipt or promote it to fresh. Restored evidence requires
the complete source join and an already accepted clock-continuity/age policy;
when the old monotonic epoch cannot be compared, withhold until an accepted
evaluation or a new qualified observation establishes freshness. This page
introduces no cache schema, persistence guarantee or recovery mechanism.

## MCP and GraphQL equivalence or withholding

The existing names remain MCP `ebus.v1.semantic.system.get`
`state.outdoor_temperature` and GraphQL `SystemState.outdoorTemperature`.
The separate average names remain `state.outdoor_temperature_avg24h` and
`SystemState.outdoorTemperatureAvg24h`. Their legacy presence is not SemReg
admission, and this contract does not remove or reinterpret the average field.

For cutover acceptance, both instantaneous projections must select the same
admitted observation at an equivalent evaluation context: value, Celsius unit,
binding identity, evidence, original receipt/age, qualification, validity,
freshness and retention decision must agree. Numeric equality alone does not
establish equivalence. A scalar projection loses identity, provenance, time
and policy unless those are conveyed by the existing surface; account for that
loss without changing MCP envelopes or inventing GraphQL fields. If required
meaning cannot be represented, withhold both instantaneous values consistently
using the existing unavailable representation (MCP absent member, GraphQL
null), and retain diagnostic evidence separately. Do not substitute a stale
legacy cache or a populated average on either surface. Downstream execution
must verify those representations and parity; no running surface was checked
for this contract.

## Conditional acceptance matrix

All values, value bytes and elapsed intervals below are synthetic. They are
not telegram captures or target qualification evidence. Assume a hypothetical
already accepted policy only in rows that explicitly say so; no duration is
prescribed here.

| Case | Minimal condition | Required SemReg and consumer outcome |
| --- | --- | --- |
| Qualified fresh | Exact joined `0x0073`, value bytes `00 00 20 41` (`10 °C`), existing qualified binding and accepted policy, receipt monotonic 1 s, evaluation 6 s in the same epoch and within the policy's fresh interval | Conditional exact outdoor-air value, original age 5 s; MCP/GraphQL agree or both withhold if required meaning cannot be represented. Not reachable from today's qualification-gap record |
| Unknown qualification | Same finite value and clocks, but qualifier absent/unknown or current evidence-gap fixture | Withheld; successful decoding or acquisition cannot qualify it |
| Partial failure | Prior accepted `10 °C` at receipt 1 s; next outdoor read fails while an unrelated system field succeeds | Keep prior outdoor evidence/receipt; reevaluate its original age. Other fields may advance independently; no snapshot-wide age refresh |
| Stale retention | Prior accepted outdoor value crosses the accepted fresh deadline, still inside retention | Stale evidence retained; consumer value only with accepted explicit stale semantics, otherwise withheld on both surfaces. At retention expiry consumer value withdrawn |
| Restart | Cache contains `10 °C`, but clock continuity, source generation, qualifier or policy cannot be established | Withheld; cache load is no acquisition. Complete evidence remains separate pending accepted reevaluation or a new qualified observation |
| Valid zero | Exact joined `0x0073`, value bytes `00 00 00 00`, all existing admission requirements satisfied | Conditional `0 °C` on both surfaces; not omission, default or loss |
| Aggregate-only | `0x0095` finite `10 °C`, no accepted instantaneous observation | Aggregate withheld from the instantaneous fact with `rolling_average_window_unrepresentable`; instantaneous MCP/GraphQL unavailable even when aggregate legacy fields are populated |

Review the join members independently: changing any one must prevent the old
observation from acquiring the changed binding's authority. Review failure,
replacement, nonfinite, stale, expiry and restart transitions against the
original retained record. These are reasoned acceptance cases, not executed
mutation tests or hardware evidence.

Remaining gateway acceptance includes producer implementation, policy selection,
qualified native evidence, cache/restart behavior, actual cross-surface parity
and focused/full validation. G5 D1-D5/O8 remain separately owned under
J01-J17. This read-only temperature contract leaves those wider gateway
requirements unchanged. Transport, hardware, release and parent acceptance
remain outstanding.
