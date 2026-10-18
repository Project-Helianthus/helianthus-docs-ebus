# Zone room-temperature cutover contract

> **License:** AGPL-3.0. Helianthus application migration contract.
> **Status:** Proposed, read-only, partial contract for issue #671. Nothing here
> is stable before Helianthus 1.0. This page enables no runtime publication.

This slice covers B524 `OP=0x02, GG=0x03` room-temperature observations and
their separately evidenced sensor-binding identity. It advances
`helianthus-ebusgateway#952` without completing its north-south flow or closing
the parent. Effective, manual, comfort and other setpoints, control operations,
humidity, M14/M15 boiler temperatures, W27 outdoor/aggregate work and W30
pressure are excluded. No producer, pack definition, shared mapping, fixture,
write route or eeBUS output binding is introduced. The latter belongs in the
driver repository.

## Evidence and current consumers

The public native contract comes first:

- [B524 register catalog](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md):
  Table Legend, GG=0x03 Zones, and `zmapping` distinguish observed values,
  candidate widths and family-dependent labels. Historic FLAGS access labels
  do not establish writability.
- [B524 semantic mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md):
  `ebus.v1.semantic.zones.get` names `[].state.current_temp_c`; the existing
  SemReg thermal mapping section covers system observations, not this zone
  cutover. Its receipt/evaluation separation is useful lifecycle precedent.
- [Gateway semantic poller](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go):
  `refreshState`, `refreshZoneDiscovery`, `refreshZoneSlowConfigFields`,
  `publishZones`, `mappedRadioRoomStateForZoneLocked`,
  `inferRadioRoomMappingForZoneLocked`, `cacheZonesLocked` and
  `readB524Float32LE` show implementation behavior. They cannot qualify a
  native sensor identity.
- [Thermal pack definitions](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go):
  `fields`, `services` and `Metadata` establish existing definitions and
  dimensions, not a device binding or current gateway publication.

**Proven** here means supported within the cited public evidence's stated
scope, or directly visible implementation behavior when explicitly labeled.
**Hypothesis** denotes a proposed mapping or candidate interpretation.
**Unknown** denotes missing evidence. These labels are independent of device
qualification and runtime admission: even a documented selector needs an
exact qualified source/profile binding before projection.

The finite inventory below uses `PB=0xB5, SB=0x24`, local read operation
`OP=0x02` (read `OT=0x00`), and `GG=0x03`. Each row includes its own concrete
instance `II`; there is no wildcard observation or cross-instance join.

| Field or association | Native selector | Native evidence and decoding | Current consumer / proposed disposition |
| --- | --- | --- | --- |
| Current room temperature | `(0x02, 0x03, II, 0x000F)` | Catalog: `zone_room_temperature`, `f32`, °C, `Zone{z}RoomTemp`, from room sensor. **Proven** catalog correspondence; little-endian only within characterized VRC720-family context. No catalog numeric range. Other profile byte order **Unknown** until qualified. | `zone_current_temp` → `refreshState` → `CurrentTempC`; mapping names MCP `[].state.current_temp_c`, `publishZones` fills GraphQL `Zone.State.CurrentTempC`. Proposed Thermal candidate below is **Hypothesis**, withheld pending binding evidence. |
| Sensor-binding observation, separate from temperature | `(0x02, 0x03, II, 0x0013)` | Catalog: `zone_room_sensor_binding_mode`, raw integer authoritative; `u16` enum catalog entry, exact two-byte little-endian reply is a **Hypothesis** explicitly unconfirmed on wire. Family labels conflict/extend beyond the alias table. Preserve bytes and raw value; no new enum meaning or physical identity. | `zone_room_temperature_zone_mapping_raw` → configuration snapshot → `RoomTemperatureZoneMapping`; radio fallback can infer mapping. Proposed: evidence metadata only, no Thermal measurement, mode or remote-control identity. |
| Zone/circuit association context only | `(0x02, 0x03, II, 0x001C)` | Catalog: `zone_circuit_assignment`, raw bytes. Profile-scoped VRC720-family observations II00=`00`, II01=`01`, II02+=`FF`; no +1 remap. Signed interpretation and universal topology **Unknown**. | `zone_index` feeds discovery. Proposed: retain exact evidence for zone presence/association; neither a temperature nor sensor binding. No new projection. |

The catalog lists zone instances II00..0A; current `refreshZoneDiscovery`
probes II00..08, checks the first returned byte against `FF`, and can recover
discovery from `ebusd` grab data. That difference is not permission to widen
discovery. `refreshState` reads each discovered instance, builds an optional
temperature pointer and passes it to `mergeZoneSnapshotFields`.
`readB524Float32LE` accepts at least four value bytes, decodes the first four,
rejects NaN/infinity, and has no finite range check. Exact zero is a valid
pointer value. These are **Proven implementation behaviors**, not proof of
native invalid-value encodings or exact native reply length.

`publishZones` uses cached temperature first, then mapped radio temperature
when missing; it can infer a room mapping from a uniquely matching radio
zone assignment. Configuration refresh also derives associated circuit via
`resolveAssociatedCircuitInstance`; the publication path can do likewise.
`cacheZonesLocked` copies cached fields back into GraphQL zone objects.
These associations and fallback paths are legacy behavior, not native proof
that RR0013 identifies a remote-control endpoint or a circuit. Display IDs
such as `zone-1`, equal numeric values and common source labels cannot merge
zones. The supplied sources do not establish HA adapter behavior, the full
merge helper's retention policy, or MCP serialization parity; those remain
**Unknown** and require later inspection and tests.

## Proposed observation boundary and projection

All requirements below are **future work**, not claims about the current
gateway. Preserve a native observation before interpretation: complete
`PB/SB, OP, OT, GG, II, RR`, request initiator/source and controller target,
reply direction/source, exact value bytes and response outcome, evidence
reference and provenance. Associate it with the asset/service binding,
controller family/profile and profile revision, source epoch, driver generation,
decoder/mapping revision and qualification result. Unknown identity or revision
is not a match. Profile matching is an evidence check, not an authentication,
principal or permission check; this slice adds none.

Record original receipt (`received_at`, `receipt_monotonic`) separately from
evaluation (`evaluated_at`, `evaluate_monotonic`). Keep the monotonic clock
epoch explicit; a restart cannot compare unrelated epochs. Re-reading a
snapshot, evaluating it later, an unrelated successful field or a rejected
reply must not renew receipt. Replies require correlation to the exact request
and source; OP06/GG03 is a different namespace even with matching II/RR.

Decode temperature only after the profile's byte order, exact value width and
unit are qualified. Proposed acceptance is exactly four value bytes for the
characterized `f32` candidate, after envelope extraction, not four bytes of a
whole telegram. Reject short and over-length values; never truncate. Retain
malformed evidence without assigning it a numeric value. Do not guess another
codec, substitute a setpoint or reinterpret an invalid value as zero. The
two-byte sensor-binding decoder remains conditional on independent width
qualification; until then retain its bytes with interpretation withheld.

| Existing definition | Proposed use and remaining boundary |
| --- | --- |
| `helianthus.pack.thermal` / `thermal.measurement.air_temperature` / `unit.celsius` | **Hypothesis** for RR000F only. Existing pack quantity bounds are -100..200 °C, derived from decimal coefficients/exponents in `fields`; they are pack validation limits, not a native sensor range. Require finite input within these limits and any separately evidenced narrower profile limit; do not clamp. Decimal conversion/rounding policy and its loss evidence must be agreed and tested before cutover. |
| `thermal.service.zone`, service identity dimension `thermal.dimension.zone` | Candidate service association must identify the qualified zone separately from sensor source. The pack's service dimension does not by itself add a zone dimension to a temperature FactKey. No full read capability is inferred. |
| Field dimension `thermal.dimension.temperature` | The supplied definitions establish the dimension ID, but no supported zone-room dimension value/binding in these sources. **Unknown** exact FactKey dimension value: withhold publication until an existing compatible value and per-zone collision-free binding are evidenced. This page invents no value or pack ID. |
| RR0013 and RR001C | Withheld from Thermal facts. Keep as distinct native association evidence. A matching temperature definition or plausible enum alias does not qualify sensor identity, topology or publication. |

Thus this contract selects an existing candidate field/service and explicitly
withholds its final FactKey and runtime publication. It does not claim a
current SemReg zone fact. Qualification must preserve the complete native
selector and source independently of semantic key dimensions.

## Proposed retention and transitions

Retain last-known-good temperature and sensor-binding evidence independently,
under their exact identities. An absent/malformed/non-finite/out-of-range
attempt records its failure and cannot overwrite the accepted value or receipt.
With no prior accepted value, expose unavailable/withheld rather than zero.
With a prior value, preserve it as retained evidence, mark the failed attempt
and withhold a current qualified projection until a valid recovery. Unrelated
zone/configuration fields retain their own state; no whole-zone clearing.

Freshness is a separate decision based on elapsed monotonic time since the
accepted receipt and a future explicitly configured, qualified freshness
policy. No timeout is established by these sources. Stale retained evidence
remains available as stale history, never silently current. Missing freshness
policy or clock continuity withholds current projection. Out-of-order or
duplicate old evidence cannot advance the accepted receipt.

A different instance/source/profile/revision/epoch is a separate identity:
quarantine the new attempt from the old slot, preserve the old history, and
require qualification for the new binding. A changed RR0013 binding retains
both raw observations but invalidates trust in the old association; it must
not relabel retained temperature as belonging to a new sensor. Requalify the
association and obtain a new correlated temperature before recovery. A valid
same-identity reply can recover the field independently of failed neighboring
fields, with its new original receipt. None of these transitions admits an
otherwise unqualified profile or unknown FactKey.

## Synthetic before/after review cases

These are design examples, not captures, fixtures, executed tests or device
qualification. `A` and `B` denote different synthetic source identities;
`P`/`Q` profiles, `r`/`s` revisions and `R`/`E` receipt/evaluation positions
are symbolic. Unless stated otherwise, use OP02/GG03/II00/RR000F, source A,
profile P/revision r, a characterized little-endian decoder, and previously
accepted 20 °C with receipt R0. “After” is the future candidate behavior
conditional on all qualification and FactKey gaps above being resolved.

| Case / input | Before: visible current behavior or gap | After: proposed result / intended difference |
| --- | --- | --- |
| Exact zero: `00 00 00 00` | Float helper accepts 0 and `refreshState` creates a non-nil pointer. | Accept 0 °C, new receipt R1; no truthiness omission, missing-value substitution or setpoint fallback. |
| Absent value / failed read, including first observation | Helper returns no accepted float; publication can use cached/radio paths. Exact merge retention not established here. | No accepted value initially → unavailable. Otherwise keep 20 °C at R0 as retained evidence with failed-attempt status; no source substitution or renewed freshness. |
| Non-finite: `00 00 C0 7F` (NaN), `00 00 80 7F` (+infinity), `00 00 80 FF` (-infinity) | Helper rejects each. | Preserve failure/raw bytes, retain R0, withhold current projection; no invented sentinel meaning. |
| Finite 201 °C (also -101 °C) | Helper has no finite range guard; downstream acceptance is not established here. | Reject against existing pack bounds; retain R0, no clamp. A profile-specific native range remains Unknown. |
| Short `00 00 00`; over-length `00 00 A0 41 00` | Helper rejects short input; decodes first four over-length bytes as 20 °C. | Reject both exact-width mismatches, retain complete bytes and R0. Strict over-length rejection is an intended difference, conditional on qualified width. |
| Stale: accepted receipt R0, evaluation E beyond agreed freshness policy | These sources do not establish equivalent per-field receipt-based freshness across MCP/GraphQL. | Keep retained 20 °C at R0, explicitly stale/unavailable as current; E never becomes receipt. No timeout fabricated here. |
| Foreign instance II01, otherwise identical | Polling uses per-instance slots; display numbering exists. Full runtime admission is not proved here. | Never update II00; retain II00 history. II01 requires its own qualified binding, even for equal 20 °C. |
| Foreign source B, otherwise identical | Read request uses poller source/target; full end-to-end source admission is not proved by this file. | Reject from A's slot; independently qualify B. No radio fallback or same display ID join. |
| Same source, profile Q; separately revision s; separately OP06; separately different GG/RR | No complete future observation admission shown. | Each changed identity component independently prevents updating the original slot; preserve raw evidence and old receipt. |
| RR0013 raw `02 00`; then changed `03 00` or malformed `02` / `02 00 00` | Catalog width is candidate; publication may decode/infer mapping and use radio fallback. | Retain raw binding separately. No remote-control label inferred. Changed binding withholds association until requalified; malformed width cannot replace last good binding. Temperature evidence is not erased or reassigned. |
| Recovery after failure/staleness: same identity, new valid `00 00 A8 41` (21 °C) at R2 | `refreshState` accepts finite float; full future lifecycle is absent. | Independently replace temperature with 21 °C at R2; current only if fresh and still qualified. Other failed fields remain failed; a binding change additionally needs requalification. |

## MCP/GraphQL equivalence and later cutover evidence

Proposed adapters must project one accepted observation/evaluation decision.
For the existing MCP zones read and GraphQL zone state, compare zone identity,
numeric value (including zero), unit, source/provenance, semantic revision,
original receipt, freshness, qualification and withheld/loss disposition.
Document omission versus GraphQL null explicitly before implementation; neither
may serialize missing as zero, stale as fresh, or a retained value without its
status. A schema unable to express these distinctions must withhold the new
projection pending a reviewed compatible design. No new namespace is proposed.
Preserve existing eBUS MCP request/response compatibility; no surface may switch
to inferred identity while the other keeps native evidence. Legacy display
aliases remain presentation only, never keys or authoritative binding enums.

Later gateway work must inspect the snapshot merge/retention helpers, B524
reply correlation and parsing, discovery/config/state polling, radio fallback,
SemReg publisher binding, and both MCP/GraphQL serialization/update paths.
It needs native public evidence for concrete profile/revision/instance,
request/reply direction, raw bytes, width/byte order/unit, binding correlation
and device-family applicability; conflicting enum evidence remains explicit.
It also needs the existing supported temperature dimension value, qualified
asset/service association, receipt/freshness policy and conversion loss policy.

Later HA work must inspect the actual zone/climate consumer and prove that
measurement identity, unavailable/stale state, exact zero and partial recovery
survive adapter translation without changing setpoints or control operations.
No supplied HA source establishes that behavior now. Deterministic adapter
tests must vary every claimed identity field separately and compare MCP and
GraphQL outcomes for all cases above, including sensor reassociation and clock
epoch changes. Offline tests cannot establish device or installation
qualification; any later physical acceptance is separately authorized work.

Every interface, transition and example above is a source-reviewed proposal.
Document readability and manual review are not semantic/runtime validation.
No unmerged W specification, J/M implementation or other X contract is a
dependency. Full committed-head gates, independent review, runtime admission,
transport/hardware acceptance and the rest of parent #952 remain outstanding.
