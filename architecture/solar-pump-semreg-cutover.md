# Solar pump and runtime-counter SemReg cutover

This is the proposed, read-only migration acceptance contract for solar-loop
pump-active, operating-hours and starts observations. It is a partial slice of
[gateway #952](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/952)
and implements the documentation scope of
[docs-ebus #703](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/703).
It does not implement the cutover or close the parent. Solar temperature
contract X27 is unchanged. The broad Matter source inventory is a separate
contract. Nothing here establishes stability before Helianthus 1.0.

## Evidence and current behavior

The public native contract comes first:

- [B524 register map, Table Legend and GG=0x04 Solar Circuit](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md)
  records status at RR=0x0008 (`u8`, `0=off 1=on`) and cumulative runtime at
  RR=0x000B (`u32`, `hrs`). Both have the `fm5_config <= 2` condition and the
  dagger annotation: CSV value-matched only, without independent confirmation,
  with false-positive risk. These semantic names are **Hypothesis**, not proof
  of physical pump behavior or runtime qualification. Multi-byte integers are
  little-endian per the Table Legend. No solar starts selector is established.
- The map's Group Topology lists a profile interval II00..01, with presence
  probed separately, while its detailed solar section describes II00. The
  current reader below uses only II00. II01 is not silently admitted or merged;
  its applicability and ownership remain **Unknown** for this slice.
- [B524 semantic mapping, `ebus.v1.semantic.solar.get`](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md)
  describes the FM5 non-null empty/retained-object compatibility behavior.
- [Gateway `semantic_vaillant.go`](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go),
  specifically `localSolar`, `solarInstance`, `readSolarSnapshot`,
  `decodeB524BoolFromRaw`, `decodeB524Uint32FromRaw`,
  `mergeSolarSnapshotNonDestructive`, `refreshFM5Semantic`,
  `commitFM5Acquisition`, `applyFM5Acquisition`, `isFM5StructuralWithdrawal`,
  `publishFM5Semantic`, `readB524ValueWithMaxAge` and
  `semanticReadB524SolarDescriptorPolicy`, supports the implementation claims
  below. **Proven** here means established by source inspection only; code is
  corroborating implementation evidence, not native wire proof or hardware
  acceptance.

| Observation | Exact current native selector | Legacy behavior established by source |
| --- | --- | --- |
| Solar pump-active | PB=0xB5, SB=0x24, OP=0x02, GG=0x04, II=0x00, RR=0x0008 | `readSolarSnapshot` decodes `PumpActive`; `publishFM5Semantic` copies it to `SolarStatus.PumpActive`. `00` is false, `01` true; empty payload, `FF` or a first byte greater than 1 decodes to nil. The decoder checks the first byte, not exact width. |
| Solar pump operating hours | PB=0xB5, SB=0x24, OP=0x02, GG=0x04, II=0x00, RR=0x000B | Reads `PumpHours` as little-endian uint32, then publishes it through `decodeUint32Float64`. Fewer than four bytes or the all-ones sentinel decodes to nil; otherwise the first four bytes are used. Zero is valid. The native candidate unit remains hours, not energy or a derived rate. |
| Solar pump starts | Unknown: no selector, wire type or native unit established | No solar starts read, snapshot member or publication in the inspected solar functions. Circuit `PumpStarts` is a different source, not a solar fallback. No starts value is synthesized. |

The request goes from the bound initiator to the selected controller and the
value returns from target to initiator (`readB524ValueWithMaxAge`). Neither a
fixed initiator address nor another controller's reply qualifies this binding.
`localSolar` is OP02/GG04; equal register numbers in OP06 are a separate
namespace. Circuit pumps (OP02/GG02) and boiler pump observations have separate
owners and meanings even when the visible value is identical.

`readSolarSnapshot` reports readable when any of its reads succeeds, including
a payload whose scalar decoder returns nil. Readability is not validity of
every field. An interpreted acquisition merges only non-nil fields; a valid
false or zero replaces the previous value, while a nil field leaves that
field's previous value intact. The solar status descriptor uses the fast
state policy; hours uses the slow state policy. No numeric TTL is introduced
here, and one field's read must not renew another field's freshness.

`refreshFM5Semantic` checks controller reachability, module configuration,
evidence age and coherence before reading. Its interpretation also depends on
solar and cylinder acquisition. `commitFM5Acquisition` fences the commit
against changed registry/poller evidence. Transient acquisition degradation
retains the last coherent snapshot with the FM5 degraded reason/revision;
fresh structural absence or a known non-interpretable configuration withdraws
it. `publishFM5Semantic` publishes an empty typed solar object on structural
withdrawal or when no snapshots exist. Empty does not mean false or zero.
These are current implementation rules, not proof of a physical solar service.

## Proposed admission and loss contract

[Thermal pack `definitions.go`](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go),
tables `fields`, `dimensions`, `services`, `capabilities` and `operations`, has
no pump-active, pump-hours, pump-starts or solar-loop service definition.
`thermal.status.operation` and `thermal.action.state` are system-dimensional;
neither defines a solar pump or a source-specific counter. A generic circuit
service does not establish that a solar loop is a heating circuit.
The existing
[thermal mapping fixture](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/fixtures/vaillant-semreg-thermal-map-v1.json)
contains system temperatures and a withheld rolling average, not these pump
observations. Its qualification block reports `Unknown` and does not permit
runtime qualification; it supplies no solar qualification or mapping.

| Requested legacy observation | Proposed SemReg FactKey / service | Qualification and disposition | Consumer loss |
| --- | --- | --- | --- |
| Pump-active | None under the current pack | Native meaning is a candidate; runtime qualification not established. Withhold semantic projection even for valid `00`/`01`. | A SemReg-only consumer cannot recover the legacy solar Boolean. Preserve its source-specific compatibility value and evidence separately. |
| Operating hours | None under the current pack | Candidate cumulative hours; runtime qualification not established. Withhold semantic projection even for valid zero. | No canonical solar runtime counter, delta or rate is available. Preserve the native absolute counter in hours. |
| Starts | None under the current pack | Native selector, meaning, unit and qualification are Unknown; withhold for both missing source and missing definition. | The inspected legacy solar plane has no starts field to preserve. This is unavailable coverage, not a lost formerly supported value or a zero. |

No new definition ID, dimension, service, capability, namespace or universal
metric is created. A future representable mapping would need a separately
accepted pack contract, native selector and unit evidence, qualified loop-owner
binding and lifecycle policy. This document supplies no speculative FactKey.
Pack representability, evidence grade (`Proven` / `Hypothesis` / `Unknown`),
binding qualification, acquisition result, freshness and admission must remain
independent. Valid decoding cannot supply missing qualification or definitions.

Retain each raw request/reply and decoded candidate together with PB/SB,
opcode/group/instance/register, direction, bound source and target, controller
family and firmware context when known, solar-loop owner, asset/service binding
identity when established, source epoch, driver generation, receipt provenance,
evidence reference, qualification and semantic revision. Unknown context stays
unknown. Preserve original receipt and monotonic clock-epoch information;
evaluation or cache replay must not become a new receipt. This is a proposed
retention requirement, not a claim that the legacy scalar snapshot stores all
of these fields. Public examples contain only synthetic value payloads.

Retain partial last-known-good fields under their original owner and receipt
provenance. Record a failed/new invalid observation beside the retained value;
never relabel the retained value as current, valid or qualified because a
different field succeeded. A source/owner replacement starts a separate
lineage. Historical evidence may remain, but it is not the replacement's value.
Do not merge conflicting candidates or choose the newest candidate merely by
arrival order when ownership or qualification is unresolved.

Projection accounting remains exactly one disposition per requested
`(kind,item_id)` in the existing deterministic envelope. These legacy field
names do not become invented registry item IDs. For a requested existing
definition such as `thermal.status.operation`, solar pump evidence contributes
no fact and a source-specific loss reason; it cannot establish active/idle.
If another qualified source already projects that shared definition, keep its
single projected disposition: absent solar facts must not append a second
disposition or overwrite it with withheld. If nothing admissible can satisfy a
requested definition, report the existing withheld/unavailable disposition
with its loss evidence. A request for an undefined item follows existing
unknown-item handling; do not register a placeholder to make it requestable.

MCP `ebus.v1.semantic.solar.get` and GraphQL must preserve the same legacy
source meaning, false/zero/null distinction, partial retention and FM5
degradation/withdrawal semantics. The code shows common `SolarStatus`
publication; complete serialization parity is downstream acceptance, not
proven by these functions. A SemReg-only cutover that removes pump-active or
hours without declaring these losses is not equivalent. Compatibility may
retain the legacy path; it must not disguise it as a SemReg fact.

## Synthetic acceptance cases

These are manual contract examples, not executed tests, captures or hardware
observations. Hex bytes are value payloads after selector-correlated extraction,
not complete telegrams. All cases retain the current pack's withholding above.
Letters identify synthetic owner/source lineages, not device identities.

| Case | Observation / transition | Required disposition and equivalence boundary |
| --- | --- | --- |
| Valid false and zero | Owner A, status `00`, hours `00 00 00 00` | Preserve false and zero hours, not missing. Equivalent legacy values require the same selector, lineage and admitted lifecycle context. Still no SemReg pump/counter fact. |
| Valid on and hours | Same owner, status `01`, hours `2A 00 00 00` | Retain true and 42 hours independently. Neither proves thermal energy delivered, solar yield, system heating/action, demand or a writable operation. |
| Unknown status | Status `02` or `FF` following a valid `00` | Legacy decoder returns nil; retain prior false with its old receipt, plus the rejected bytes/reason. Unknown is not off. No new current status is admitted. |
| Malformed values | Empty status, or hours `2A 00` | Decode failure is distinct from a missing reply. Retain any prior good field without renewing it. Extra bytes require framing/codec qualification: the legacy decoders' prefix acceptance is not native width proof. |
| Missing reply | Hours read unavailable after a good 42-hour reading | Preserve the prior 42-hour evidence and missing-acquisition state; do not publish a fresh zero or infer a reset. |
| Stale status, newer counter | Prior `01` has expired under its policy; new hours `2B 00 00 00` is usable | Keep status stale, hours 43 independently fresh. Do not renew status from the counter or manufacture a coherent current on-state. Legacy non-nil merge alone does not prove field-level freshness. |
| Counter decrease / rollover candidate | Same owner, `FE FF FF FF` then `00 00 00 00` | Preserve 4294967294 hours then zero as separate raw observations. `FF FF FF FF` is a legacy invalid sentinel, not a valid maximum. Rollover versus reset is Unknown; do not unwrap, calculate a delta or assert continued runtime. |
| Reset candidate | Same owner, `2A 00 00 00` then `00 00 00 00` | Preserve the decrease. The catalog's RR=0x0001 reset-command name does not prove a reset occurred or authorize one. Reset cause and counter continuity stay Unknown. |
| Unqualified source | Decodable `01` and zero hours without a qualified loop binding | Acquisition may have succeeded; retain candidate evidence while semantic admission stays withheld. No service presence inferred from the payload alone. |
| Absent solar service | Fresh coherent FM5 absence or known non-interpretable configuration | Withdraw live structural projection under current FM5 rules; preserve history outside the live view. Empty solar object is not false, zero hours or zero starts. Transient degradation instead retains last coherent data with reason/revision. |
| Owner changes | Same selector and apparent loop index, owner A replaced by B; B reports zero | A's status/hours remain A's history. B's zero is a separate candidate, not A's reset or continuation. Recheck binding/qualification; an in-flight evidence-generation change must not commit mixed ownership. |
| Source replacement | Logical loop owner remains A, but the bound source epoch or driver generation changes; replacement reports the same 42 hours | Numeric equality does not transfer the old receipt or qualification. Preserve both lineages, re-evaluate the replacement binding and do not infer counter continuity across them. |
| Conflicting candidates | Owners A and B both claim the loop, or two sources disagree | Keep both raw candidates and conflict evidence. Withhold unresolved semantic use; do not average hours, OR status or use a boiler/circuit pump as a tiebreaker. |
| Starts absent | Status/hours readable, no native starts selector | Starts remains Unknown and unavailable. Status edges, circuit starts or boiler starts do not create a solar counter, even if numeric values coincide. |
| Shared requested definition | Qualified non-solar evidence already projects `thermal.status.operation`; solar status is missing | Keep the one projected `(kind,item_id)` disposition. Record solar source loss separately; no absent-source overwrite and no extra field disposition. |

Source-specific equivalence requires equal native selector, loop owner, source
epoch, binding/driver generation, raw-to-scalar interpretation, native unit,
receipt/freshness and qualification/admission context. Equal displayed values
across different owners, OP namespaces, circuit/boiler pumps or counters do not
establish equivalence. There is presently no equivalent SemReg pump/counter
projection for any of these cases.

## Acceptance boundary

Manual source/claim/transition/example/link review is the contract gate.
Readability checks establish only that this document exists and is nonempty;
they do not validate semantics or prove runtime behavior. No new prose tests,
fixtures, schema or validator are required by this slice. Downstream integration,
serialization parity, independent review, committed-head gates and hardware
qualification remain separate acceptance work for the parent.

No writable support follows from any read or catalog label. Existing trust and
admission checks remain; this adds no principal, credential or permission gate.
Authentication/authorization remains 0.11 work, with no new authorization gate
before 0.9. G5 D1-D5/O8 are unchanged; eeBUS output binding remains driver-owned.
