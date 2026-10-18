# Circuit pump observations and withheld SemReg projection

This is the canonical, proposed gateway-to-SemReg cutover acceptance contract
for circuit pump status, operating hours and starts in the Vaillant controller
and functional-module families. It is a bounded read-only slice of
[gateway north-south work](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/952),
tracked by [documentation issue 695](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/695).
It does not close the parent, implement downstream integration, or replace a
broad Matter source inventory or temperature-field contract. Nothing here is a
stability promise before Helianthus 1.0.

## Source contract and evidence status

Native interpretation starts with the public
[B524 register map, GG=0x02 — Circuits](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md#gg0x02--circuits)
and its
[Circuit State Enum evidence discussion](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md#circuit-state-enum).
The public
[semantic mapping, `ebus.v1.semantic.circuits.get`](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md)
records the legacy paths and selector-assignment correction. These sources
describe only a zero-valued idle observation for RR=0x001B. There is no known
observed nonzero raw code for that selector in this evidence set. A nonzero
cloud state or RR=0x001E enum candidate is not such an observation.

**Proven — software behavior** below means inspected implementation, not a
native wire codebook. **Hypothesis — native meaning:** RR=0x001B is named as
pump status; interpreting every nonzero value as active is unqualified. The
documented zero observation is consistent with off/idle but does not resolve
the competing state-enumeration interpretation. **Unknown:** nonzero codebook,
cross-family applicability, physical on-state correlation, counter reset and
rollover semantics. Evidence grade is separate from acquisition success,
qualification, freshness and admission: even a successful raw read cannot
supply the missing qualification.

Implementation sources are
[`semantic_vaillant.go`](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go)
(`localCircuits`, `refreshCircuits`, `publishCircuits`,
`mergeCircuitSnapshotNonDestructive`, the read/decoder helpers named below),
the Thermal pack's
[`definitions.go`](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go)
(`fields`, `dimensions`, `services`, `capabilities`, `Metadata`), and
[boiler pump evidence](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/docs/boiler-pump-provenance.md).
The existing
[typed thermal mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/fixtures/vaillant-semreg-thermal-map-v1.json)
contains temperature mappings and their qualification/lifecycle boundary; it
does not map these pump fields. This document does not extend that fixture.

## Exact native identity and current legacy behavior

Each row is a controller-side B524 read: `PB=0xB5, SB=0x24, OP=0x02,
OT=0x00, GG=0x02, II=<qualified circuit instance>`. The request selector
bytes are `02 00 02 II RRlo RRhi`. Source is the binding's admitted eBUS
initiator, destination is that binding's controller target; retain both actual
addresses in runtime evidence rather than inferring them from a display ID.
Request direction is initiator to target; the value returns target to
initiator. `readB524ValueWithMaxAge` and `buildB524ReadSelector` establish this
software request shape. The register map supplies the native catalog context;
software decoding alone does not prove widths or semantics across families.

| Native register / read suffix | Catalog representation | Retained snapshot | Legacy presentation |
| --- | --- | --- | --- |
| RR=0x001B / `1B 00` | `circuit_pump_unknown_8`, u16 raw | `PumpStatusRaw`, `PumpStatusLiveAt` | Mapping path `[].state.pump_status`; `publishCircuits` sets GraphQL `CircuitState.PumpActive` using `decodeUint16Bool` |
| RR=0x0024 / `24 00` | `circuit_pump_operating_time_total`, u32, hrs | `PumpHoursRaw` | Mapping path `[].state.pump_operating_hours`; GraphQL `CircuitState.PumpHours`, via `decodeUint32Float64` |
| RR=0x0025 / `25 00` | `circuit_pump_start_count_total`, u32, count | `PumpStartsRaw` | Mapping path `[].state.pump_starts_count`; GraphQL `CircuitState.PumpStarts`, via `decodeUint32Int` |

**Proven — software:** `readB524Uint16` accepts a nonempty decoded value;
`decodeB524Uint16` accepts one byte, or decodes the first two little-endian
bytes. It does not reject an unmapped nonzero status. `decodeUint16Bool`
returns nil for nil, false for zero, true for every nonzero raw value. This is
the current compatibility interpretation, explicitly a **Hypothesis** about
native meaning, not an accepted Boolean codebook. The u32 reader requires at
least four bytes, decodes the first four little-endian bytes and rejects
`0xFFFFFFFF`; the numeric presentation helpers return nil for nil and convert
present values, including zero. Sentinel rejection is implementation evidence,
not a newly established universal native rule.

`refreshCircuits` discovers active circuit candidates using RR=0x0002 before
reading these fields; empty responses alone do not prove absence or physical
topology. `publishCircuits` sorts instances and publishes active snapshots.
`mergeCircuitSnapshotNonDestructive` retains a same-controller prior field on
an omitted/failed update and replaces it on a non-nil incoming value, including
zero. On controller change it explicitly clears missing pump status and its
live time. It has no equivalent counter-specific controller-change clearing
or counter receipt timestamps. `semanticReadB524CircuitDescriptorPolicy`
assigns fast policy to status and slow policy to the counters. A live aggregate
publication or fast refresh therefore does not prove each counter is fresh.
The per-field lifecycle required below is a proposal, not a claim that this
legacy snapshot already supplies it.

RR=0x001E is the separate `circuit_state` candidate, not RR=0x001B. Its
standby/heating/cooling/DHW candidate enum cannot qualify a pump Boolean.
OP=0x06 with matching numbers remains a separate namespace. Circuit instance
zero does not identify a boiler pump. As documented in boiler pump evidence,
`mergeBoilerMirrorFieldsFromSnapshots` leaves pump state absent; independent
`refreshBoilerStatusB509` evidence supplies the boiler field. The dormant
circuit-zero entry in `boilerStatusRegisterDefinitionsForTier` is not an
active source-equivalence rule. Its cleanup remains with the separately owned
M13/M15 work; this contract changes no implementation branch.

## Proposed cutover: retain native, withhold universal facts

The current Thermal `fields` table has no pump-specific status, operating-time
or starts definition. `thermal.status.operation` describes system activity;
`thermal.action.state` is also system-scoped. Neither is a substitute for a
circuit pump. A quantity with an hours/count label does not create a missing
field definition.

| Field group member | Proposed universal FactKey | Service and qualification disposition | Consumer loss |
| --- | --- | --- | --- |
| Pump status | Withheld; no field definition or FactKey allocated | Existing `thermal.service.circuit` and `thermal.dimension.circuit` can identify circuit service scope, but cannot supply a missing pump field. Native codebook and circuit-specific correlation remain unqualified. | A universal-only consumer cannot obtain pump active/idle; retain raw status plus the labeled legacy interpretation. |
| Operating hours | Withheld; no field definition or FactKey allocated | Circuit service is a possible future owner, conditional on an owned field definition, qualified source binding, unit and reset semantics. | No universal pump runtime counter, delta or rate. Retain native total and its own receipt context. |
| Starts | Withheld; no field definition or FactKey allocated | Same circuit ownership requirement, separately qualified count semantics and continuity. | No universal starts counter, delta or rate. Retain native count and its own receipt context. |

This is explicit withholding, not a proposal to add universal definitions.
`thermal.capability.read.circuit` does not itself establish these facts. A
future mapping must be owned and qualified before allocating a FactKey; do not
invent field IDs, overload system status or attach an unsupported field to the
circuit dimension. The eeBUS output binding stays driver-owned. G5 D1–D5/O8,
existing trust/admission checks and deterministic envelopes remain unchanged.
This slice adds no principal, credential or permission gate; authentication
and authorization remain 0.11 work, with no new authorization gate before 0.9.
Reading these fields establishes no writable support or operation route.

For each retained native member, the proposed binding preserves asset and
circuit service identity separately from source identity, source epoch,
driver generation, full selector, source/target and direction, raw response
bytes, decoded value/type/unit, evidence reference, semantic revision,
qualification and receipt context. Record family/firmware applicability when
known; leave it Unknown when unavailable. Preserve acquisition origin (fresh
wire versus cache), original receipt time and monotonic clock epoch. Evaluation
time is separate and cannot rewrite receipt time. Freshness is per source,
instance and register; one successful read cannot renew a sibling's age.
This is a proposed retention requirement, not a new artifact schema or an
assertion that all metadata exists in today's circuit snapshot.

Missing means no observation for that identity; invalid means an acquired
response failed decoding/validation; stale means an old retained observation
fails its freshness policy; unqualified means the semantic binding lacks
required evidence. Preserve these separately from a valid numeric zero or a
legacy false. Keep last-known-good raw state on same-source partial failure,
with its original age and failure reason; never present retention as a new
successful acquisition. Preserve malformed bytes beside the prior good value
where available. Withholding due to the missing pack definition applies even
to fresh, decodable raw zero; it does not turn zero into missing.

On source replacement, invalidate current semantic eligibility for all three
members, start a distinct source epoch and retain old evidence under its old
identity. Never carry old counters into the replacement's current state or
claim continuity from equal circuit indices. Conflicting candidates retain
separate evidence and a conflict reason; do not select by arrival order, value
agreement or a boiler alias. Independent, nonconflicting members may continue
as native observations. No universal pump fact is admitted in any case here.

Projection accounting has exactly one disposition per requested
`(kind,item_id)`, not one per native source or circuit. The three legacy-field
loss reasons above are source-specific explanation, not invented projection
items: no pump definition exists to request as a supported field today. If a
consumer requests an existing shared definition and another qualified source
projects it, keep that item's projected disposition. An absent circuit-pump
candidate cannot overwrite it with withheld. If nothing projects the requested
supported item, return its single applicable unavailable/withheld disposition
under the existing envelope contract, with source loss detail separately. Do
not duplicate, reorder nondeterministically or silently drop requested items.

## Synthetic equivalence and transition review

These are manual acceptance vectors for the proposed contract, not executed
runtime tests or physical observations. A and B are two synthetic admitted
circuit identities with II=0x00 and II=0x01 under one synthetic controller
binding. All payloads below are synthetic value bytes, excluding any response
framing. No example qualifies a native code or a device family.

| Case / input or transition | Current code consequence | Proposed native result and universal disposition |
| --- | --- | --- |
| A status `00 00`, B status `01 00` | A false; B true from nonzero decoding | Keep A raw zero and B raw one separately. B is a synthetic nonzero, not an observed known code. Active meaning remains Unknown/unqualified; both universal projections withheld. |
| B status `01 00` becomes `02 00` | Both produce true; legacy Boolean hides the difference | Preserve the changed raw code and provenance. `02 00` is a synthetic unknown code, not active by default; no universal equivalence between the two codes. |
| Required known observed nonzero comparison | No public nonzero observation for RR=0x001B is supplied | Evidence gap remains open. Substitute neither the RR=0x001E enum nor cloud states. Future acceptance must compare the actual observed nonzero with zero and an unknown code using the circuit's own evidence; this case is not satisfied by synthetic one. |
| A zero status remains present while B has no status response | Same-source merge can retain B's old status; nil with no prior value stays nil | A zero/legacy false remains valid raw evidence, B is missing or retained with failure detail and old age. No cross-circuit fill or universal fact. |
| A hours `00 00 00 00`, starts `00 00 00 00` | Present numeric zero for both | Retain two valid zeros with distinct register identities; neither is unknown or missing. Universal counters withheld. |
| A hours `0A 00 00 00` becomes `03 00 00 00`; starts unchanged | Replaces the hours value; no reset classification in these helpers | Keep old and new totals; record a discontinuity with cause Unknown (reset, rollover or replacement not proven). Do not derive a negative delta or fabricate rollover; starts retains its independent state. |
| B counter `FF FF FF FF`, or fewer than four bytes | u32 reader rejects; partial merge retains any old value | Invalid/implementation sentinel rejection, never zero; retain prior good total and age without claiming a fresh sample. Native reset/sentinel meaning remains Unknown. |
| A status acquired at abstract receipt R1; hours at R0; only status refresh succeeds at R2 | Status time updates; aggregate publication may be live while counters remain retained | At evaluation E, stale hours remain stale; fresh status does not renew hours or starts, nor any B field. Original receipt differs from evaluation. Universal withholding unchanged. |
| Fresh raw status but no qualified codebook or binding | Legacy decoder can still return true/false | Acquisition success and freshness do not imply qualification. Retain raw, label unqualified, withhold universal status. |
| Controller source S is replaced by T at A's same II; T supplies only status | Legacy merge replaces supplied status but does not clear omitted counters on controller change | Preserve S's old counters only as historical S evidence. T counters are missing, not zero or inherited; require new qualification and receipt context. |
| Two candidates claim A with contradictory raw status or totals | These helpers do not establish a multi-candidate admission rule | Keep each source/epoch and conflict visible; no averaging or latest-arrival winner. B's independent good observations survive. |
| A/B circuit status changes while independent boiler pump is false | Active boiler mirror does not copy circuit pump | Boiler false survives circuit updates and partial failures. B509 boiler evidence cannot qualify A/B or populate their counters. |
| Requested shared field has one qualified projected source; a second source lacks a pump-related candidate | Per-source absence cannot decide shared projection accounting | Keep the single projected `(kind,item_id)` result; attach source absence separately. Do not replace it with withheld or append a duplicate. |

Source-specific equivalence is deliberately limited: the same admitted asset,
circuit service, source, epoch, driver generation and complete native selector
(including source/target, PB/SB, opcode, operation type, group, instance,
register and direction) with the same valid raw value preserves its native
value, subject to independent freshness and qualification. Legacy
zero-to-false and nonzero-to-true
are reproducible software conversions only. A and B, RR=0x001B and RR=0x001E,
OP=0x02 and OP=0x06, status and counters, or circuit and boiler sources are not
interchangeable. Equal values do not prove identity or physical equivalence.

MCP `ebus.v1.semantic.circuits.get` field names and GraphQL aliases remain the
compatibility boundary: retain the existing surfaces and clearly label their
interpretation while exposing native evidence through their supported
provenance/envelope mechanisms. Do not promise lossless reconstruction from a
universal-only consumer or silently substitute system/boiler status. Any later
cutover must preserve the same source selection, withholding reasons, values
and independent freshness across MCP and GraphQL; formatting differences cannot
change admission. This document does not implement that integration.

## Acceptance boundary

Review must compare each native claim to the register-map sections, each legacy
claim to the named functions, each withholding decision to Thermal's field and
service tables, and every transition/loss row to the proposed rules above.
The synthetic table can detect a design that collapses nonzero codes, circuit
instances, sources, epochs, selectors or independent ages when reviewed; it
does not execute or kill a production mutation. No new prose-token tests,
fixture/schema changes or validator ownership are required for this document.

Readability checks prove only that the owned document is present and readable.
Missing on-state native evidence, pump-specific definitions and downstream
integration remain explicit; this contract slice does not require implementing
them to be reviewable. Independent review, applicable committed-head gates and
any separately authorized hardware qualification remain outside this offline
authoring evidence. No device reads or writes are acceptance evidence here.
