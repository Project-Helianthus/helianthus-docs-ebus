# Zone valve and derived-action cutover

> License: AGPL-3.0. Proposed gateway-to-SemReg migration acceptance for
> [docs-ebus #704](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/704).
> This is one partial slice of
> [gateway #952](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/952);
> it does not close the parent.

This contract covers only the raw zone valve status and the legacy
`deriveZoneHvacAction` result. It is distinct from temperature-field migration
and the broad Matter source inventory. It defines acceptance for a future
implementation against the current pack; it does not claim that integration
exists. Nothing here is stable before Helianthus 1.0.

## Evidence and source boundary

**Proven (source inspection only):** the implementation behavior below is present
in [gateway semantic_vaillant.go][gateway], specifically `refreshState`,
`cachedZoneDerivationInputs`, `publishZones`, `decodeValvePositionPct`,
`deriveZoneHvacAction`, `readB524Uint16`, `decodeB524Uint16`,
`buildB524ReadSelector` and `readB524ValueLive`. This is code evidence, not
independent proof of valve movement or delivered heat.

The public native contract comes first: the [B524 framing reference][wire],
[zone register catalog][zones] and [circuit type catalog][circuit-type].
The zone catalog describes `RR=0x0012` as a read-only u16 status with
`0=closed, 1=open`. That catalog claim does not establish measured percentage
travel or heat delivery. **Unknown:** hardware correlation, family/firmware
applicability and representability of an observed zone heat-delivery action
are not established by these inputs. **Hypothesis:** valve-open plus circuit
context could support a source-specific activity indication after independent
qualification; it is not an admitted measured-action mapping.

The [semantic mapping, zones section][semantic] establishes the legacy zones
surface, but its Zone Mode Derivation discussion is about mode and preset,
not proof of `deriveZoneHvacAction`. In particular, its cooling-enabled input
must not be attributed to the action function. The [thermal mapping fixture][fixture]
contains only temperature mappings and explicitly disallows runtime
qualification under its evidence-gap profile. It supplies no qualified
valve/action binding.

Evidence grade (`Proven`, `Hypothesis`, `Unknown`), qualification, acquisition
success, freshness and admission are separate axes. A readable code or a
successful read does not promote any of the others.

## Exact source identity and current behavior

For a local zone instance `II=z`, retain the complete native selector:

| Role | PB/SB; opcode, operation, group, instance, register | Read payload |
| --- | --- | --- |
| Valve status | B5/24; 02, 00, 03, z, 0012 | `02 00 03 z 12 00` |
| Native zone/circuit association evidence | B5/24; 02, 00, 03, z, 001C | `02 00 03 z 1C 00` |
| Legacy room-sensor mapping input | B5/24; 02, 00, 03, z, 0013 | `02 00 03 z 13 00` |
| Circuit type context | B5/24; 02, 00, 02, c, 0002 | `02 00 02 c 02 00` |

Here `z` and `c` are native instance bytes, not display numbering. Requests
are initiator-to-target and values target-to-initiator; retain both endpoints
as native provenance, without publishing private installation details.
`readB524ValueLive` uses the configured source and selected controller target,
not a universally fixed destination. Do not substitute OP=0x06 for OP=0x02
or merge their identities.

Retain original response bytes alongside decoding, type/width, acquisition
origin (live/cache/import), controller-family and firmware qualification
context when known, receipt/age context, source identity and lifecycle
generation, zone identity and association revision. These are proposed
retention requirements, not a claim that this function already records every
axis. Evaluation must not replace original receipt evidence. The catalog's
valve representation is u16; the implementation decoder accepts a single byte,
otherwise reads the first two bytes little-endian and does not itself reject
trailing bytes. Decoder permissiveness is not native width qualification.

Current code behavior:

- `refreshState` reads `zone_valve_status`, passes that value and cached
  circuit context to `deriveZoneHvacAction`, and supplies
  `StateValveStatusRaw` and `HvacAction` to the zone snapshot merge.
- The action helper returns empty string for nil or codes other than 0/1;
  0 returns `idle`; 1 returns `cooling` only when
  `hasCircuitType && circuitType != nil && *circuitType == 2`.
  Every other open case, including missing circuit context, returns `heating`.
  Demand, flow, temperature and delivered-power observations are not inputs.
- `cachedZoneDerivationInputs` prefers a zone's cached circuit type, otherwise
  its stored associated circuit when byte-representable, otherwise the
  same-numbered circuit. This helper performs no component-age or association
  requalification check. This does not describe every upstream admission check.
- The configuration refresh uses `resolveAssociatedCircuitInstance` on
  room-sensor mapping RR0013: nil, 0, FF, FFFF and out-of-range values fall
  back to the zone instance; 1..20 hexadecimal map to value minus one.
  `refreshZoneDiscovery` separately probes RR001C for presence.
  Neither the resolver nor equal instance numbers prove hydraulic association.
  The native catalog describes RR001C as raw association evidence with
  family-scoped observations and an unconfirmed signed interpretation; do
  not apply the RR0013 subtraction to that raw evidence.
- `publishZones` exposes the stored action and
  `decodeValvePositionPct(StateValveStatusRaw)` in the GraphQL zone state.
  The latter returns nil for nil, otherwise raw / 655.35. Thus raw 0 yields
  0%, raw 1 yields approximately 0.0015259%, and raw 65535 yields 100%.
  This numeric conversion is legacy behavior, not a qualified travel scale.
  Retaining it for compatibility must not label it measured valve position.

There is a material conflict: the public circuit catalog calls type 2
fixed-value control, not cooling. Type 1 is heating; cooling capability is
discussed separately in the semantic mapping's Circuit Type Layer B.
Neither cooling capability nor a configured circuit type proves present
cooling delivery. Preserve the legacy derivation and its inputs as source
evidence; do not silently repair it and call the result equivalent.

## Proposed field-group disposition

The [thermal pack][pack] `fields` table defines `thermal.action.state` as a
symbol with `thermal.dimension.system`. Its `services` and `Metadata`
assign `thermal.service.zone` a `thermal.dimension.zone` FactKey dimension
and `thermal.service.system` a system dimension. The pack has no valve
status/travel field or zone-dimensional action field.

| Source member | Proposed FactKey / service / qualification disposition | Consumer loss |
| --- | --- | --- |
| Raw RR0012 status | Withhold a SemReg fact: no current pack field represents this native zone status. No admitted FactKey or service binding. Retain raw evidence and catalog interpretation separately. A future zone read association would need qualified zone identity and native enum meaning. | A SemReg-only consumer cannot reconstruct closed/open or unknown raw codes from the current pack. |
| Legacy valve percentage | Withhold: no travel field and no native proof of the legacy scale. Do not put it in `thermal.demand.level`, whose percentage is demand. | Legacy percentage presentation has no asserted semantic equivalent. |
| Legacy zone action | Withhold `thermal.action.state` for this source: system dimension cannot be rewritten to zone, and a zone cannot be renamed as a system to fit it. No admitted zone FactKey or system-service binding. | Legacy idle/heating/cooling labels and their fallback behavior remain available only as identified legacy evidence, not a measured-action fact. |
| Valve/action operation | No per-zone operation is established. The pack's set-mode and set-temperature operations do not establish valve or action writes. | No writable support or new control route follows from read compatibility. |

These are proposed cutover decisions, not new schema values or universal
definitions. `thermal.status.operation` is also system-dimensional; it is
not a workaround. A shared symbol spelling such as `heating` is insufficient
for equivalence. No current source-specific case below admits these withheld
facts, even after the association alone is qualified.

Before reconsidering withholding, require a supported pack representation and
a binding that qualifies all of: source/controller family and firmware scope,
native selector and width/enum, zone identity, independently supported
zone-to-circuit association, association revision and lifecycle generation,
and freshness/validity of every derivation component. A claim of observed heat
delivery additionally needs native delivery evidence and a documented
source-specific derivation. Demand, valve opening, circuit configuration and
actual delivery remain separate. Missing evidence leaves admission closed;
it does not authorize a new field or operation.

## Proposed transitions and consumer acceptance

Preserve partial last-known-good state by source and association generation.
A missing or bad component must not erase unrelated valid facts, manufacture
false/zero, refresh an old receipt, or make retained history current.
Stale prior evidence may remain diagnostic with its age and old association;
it cannot be admitted as a fresh action. Source replacement or reassignment
invalidates reuse under the new identity until it is independently qualified.

Return exactly one final disposition for each requested `(kind,item_id)`.
First collect source-specific outcomes, then resolve the requested item once.
If another qualified source has already projected a shared definition, absence
of this zone source cannot overwrite that disposition with absence/withholding.
Keep this source's loss in its provenance explanation. Conflicting candidates
require an established source-selection rule and qualified equivalence;
without one, withhold the contested value and preserve both candidates.
Ordering of source iteration must not change the final disposition.

The following are synthetic acceptance cases, not captures, executed tests or
hardware qualification. “Legacy” describes the helper or decoder for those
inputs, not the final merged snapshot after an acquisition failure.

| Case | Legacy result / evidence | Proposed acceptance and equivalence |
| --- | --- | --- |
| Valve 1, circuit type 1, no delivery evidence | `heating`; scaled valve percentage | Preserve open-code evidence; no measured heating or demand fact. Only the source-specific helper result is reproducible. |
| Valve 0, valid closed/false | `idle`, 0% | Keep valid zero/closed distinct from absence. Closed does not prove zero residual heat delivery or system idle. |
| Valve 7, unknown enum | Empty action; decoder still produces a percentage | Retain raw 7; semantic meaning Unknown, not idle/false and not qualified travel. |
| Valve 1, type 2 | `cooling` | Catalog says fixed-value: record conflict, withhold cooling semantics. |
| Valve 1, circuit has cooling enabled | Helper still branches only on type 2 | Capability is not observed cooling. Retain context without substituting it as an input. |
| Valve 1, missing circuit/type | `heating` fallback | Association/context unqualified; no inferred heating delivery. |
| Missing valve | Empty helper result; nil percentage | Missing is not valid zero; retain prior evidence with its original age. |
| Malformed payload or unsupported width | Acquisition/decoder failure, or permissive decoding where accepted | Distinguish invalid from missing; permissive decoding alone cannot qualify it. |
| Fresh valve, stale circuit component | Helper has no age input | Withhold composite admission; preserve fresh raw evidence and stale context separately. |
| Reassigned zone, old cached type | Helper can receive old type | Fence derivation by association revision; do not transplant the old action to the new circuit. |
| Replacement source, same native instance | Same helper inputs can yield the same label | Not identity equivalence. Requalify replacement; retain old source history separately. |
| Two candidates disagree on type or valve | No candidate arbitration in the helper | Preserve conflict; no iteration-order winner or averaging of codes. |
| Acquisition succeeds but binding unqualified | Helper can still produce a label | Success and evidence grade do not satisfy qualification or representability. |
| Qualified native 0 versus absent source | 0 is a real code; absence is no observation | Do not coalesce them; neither admits a zone fact in the current pack. |
| Another source projects a shared requested definition; this source is absent | Per-source absence | Preserve the shared projected disposition; one result per requested key, with per-source loss retained. |

Exact equivalence is limited to replaying the same source identity, raw
selector/value, circuit inputs and derivation rule for legacy compatibility.
It does not equate a binary valve code with percentage travel, demand with
action, circuit action with zone delivery, or a legacy zone label with a
system action. Changed source, association, rule or stale input defeats that
equivalence even if the label happens to match.

Both MCP and GraphQL must preserve the same accepted facts, withholding
reasons, native provenance and source-specific losses through their existing
envelopes. Keep eBUS MCP compatibility; do not silently change legacy action
or percentage semantics during migration. Retain legacy/source evidence
until consumers can handle the explicit loss. This contract does not assert
that the shown GraphQL publisher proves MCP parity; downstream parity needs
independent implementation evidence.

## Acceptance boundary and remaining evidence

Manual review of the cited source claims, transition rules, consumer losses
and synthetic cases establishes this bounded documentation contract only.
Readability checks establish readable text, not semantics or runtime behavior.
No new fixture, validator, universal definition or pack extension is introduced.
Hardware correlation, qualified association, any future representation and
downstream integration/parity remain separate acceptance work.

G5 D1-D5/O8 and current trust/admission checks remain unchanged. This slice
adds no principal, credential or permission gate: authorization is not a
pre-0.9 gate; authentication/authorization remain 0.11 work. The eeBUS output
binding remains driver-owned. No new major or experimental namespace, device
write, deployment, transport behavior or hardware acceptance follows.

[wire]: https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524.md
[zones]: https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md#gg0x03--zones-multi-instance
[circuit-type]: https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md#mctype--circuit-type
[semantic]: https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md
[fixture]: https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/fixtures/vaillant-semreg-thermal-map-v1.json
[gateway]: https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go
[pack]: https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go
