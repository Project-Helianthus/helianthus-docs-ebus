# Maintenance and system-off cutover contract

This is the proposed, read-only gateway-to-SemReg acceptance slice for
[docs issue #699](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/699),
advancing [gateway #952](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/952).
It covers only controller system-off and source-coded maintenance observations.
It does not implement a projection or close the parent. Nothing is stable before
Helianthus 1.0. This contract adds no authentication, authorization, principal,
credential or permission gate; existing trust and admission checks remain in force.

## Evidence and current behavior

The public native contract comes first:
[B524 register map](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md),
sections **Table Legend**, **Group Topology**, and **GG=0x00 — System**.
The system table documents the VRC720-family singleton OP=0x02, II=0x00;
this scope does not transfer to the VRC700-family ventilation selectors.
The legend withdraws historical FLAGS-derived access labels as public semantics.
Readable data and printed FLAGS establish no writable support here.

| Native observation | Exact selector and documented representation | Native semantic evidence |
| --- | --- | --- |
| Source-specific system switch | PB=0xB5, SB=0x24, OP=0x02, GG=0x00, II=0x00, RR=0x0007; u8, Boolean-shaped, no physical unit | **Unknown** polarity: the row's `0=off 1=on` conflicts with the candidate switch-off interpretation. The name `unknown_11` is provisional. A universal installation-off meaning is not proven. |
| Source-coded maintenance | PB=0xB5, SB=0x24, OP=0x02, GG=0x00, II=0x00, RR=0x0096; u8, bool, no physical unit | The catalog records `maintenance_active`, ebusd `MaintenanceDue`, one-byte observation and FLAGS=0x01. **Hypothesis** for a family-qualified maintenance interpretation; exact due/active meaning and its relationship to diagnosis remain **Unknown** without correlated public evidence. |

**Proven (source inspection only):** the
[legacy mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md),
section `ebus.v1.semantic.system.get`, names `state.system_off` and
`state.maintenance_due`. In the
[gateway implementation](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go),
`localRegulator`, `regulatorInstance`, `system_off`, `system_maintenance_due`,
and `refreshSystem` select the tuples above. `readB524ValueWithMaxAge` uses the
configured initiator source and current controller target, sends an
initiator-to-target request, and correlates the reply through
`parseB524ReadPayload`. These are implementation claims, not independent native
proof or evidence of a fixed installation address.

`refreshSystem` calls `readB524Uint16`, then assigns `*raw != 0` to each Boolean
pointer. Consequently a successfully decoded zero is false and a successfully
decoded nonzero is true, including a code whose native meaning is unknown.
The generic `decodeB524BoolFromRaw` is stricter but is not the reader used here.
Failure or missing payload does not supply a new pointer.
`mergeSystemSnapshotNonDestructive` replaces non-nil values independently and
retains previous values for nil incoming fields. Its controller-change handling
specifically clears system-flow temperature; it does not clear these two Boolean
fields. This retention is not evidence that an old value belongs to a replacement
source. The fields have no dedicated receipt-age members in
`vaillantSystemSnapshot`; cache-age handling is not per-field native freshness
proof for a retained Boolean.

## Proposed native retention and qualification

Retain raw request/reply and value bytes beside the legacy Boolean, with the
complete tuple, actual initiator/controller binding, request/reply direction,
family/profile evidence, source identity and source epoch, driver generation,
asset/service ownership, evidence reference and evidence revision, decoder and
semantic mapping revisions. Retain observed width, decode result and uncertainty;
do not reconstruct raw bytes from a Boolean. OP=0x06, another instance, another
controller, or another PB/SB is independent evidence even if register numbers match.

Separate `Proven` / `Hypothesis` / `Unknown` evidence from qualification,
acquisition, freshness and admission. A decoded false is acquired data; it is not
missing. A plausible interpretation is not qualified. Retain receipt time and
monotonic receipt epoch separately from caller evaluation context; evaluation
cannot refresh receipt. No fixed TTL or clock reconciliation rule is invented
here: unavailable freshness or incompatible clock epochs withhold admission.
Keep partial last-known-good native values with their original provenance and
age; a failed maintenance read must not erase a valid independent switch value.

The existing
[read-only mapping fixture](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/fixtures/vaillant-semreg-thermal-map-v1.json)
covers temperature candidates only. Its qualification revision
`vaillant-controller-qualification-evidence-gap/v1` has evidence status `Unknown`
and `runtime_qualification_permitted=false`. It qualifies neither field here.
A future binding needs its own selector-correlated public evidence revision;
reusing the temperature revision or a display label cannot admit these values.

## Proposed withholding table

The current thermal pack's
[definitions](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go),
`fields`, `services` and `Metadata`, provide the symbols below and associate
`thermal.service.system` with `thermal.dimension.system`. Existence in the pack
is representability, not native equivalence. All rows below are **proposed**;
none adds a field, service, operation, namespace or write route.

| Retained source | Requested canonical field | FactKey / service decision | Disposition and consumer loss |
| --- | --- | --- | --- |
| RR=0x0007 switch, false or true | `thermal.mode.system` (`auto`, `cool`, `heat`, `off`) | No emitted FactKey. Candidate service is `thermal.service.system`; any future key requires a qualified source-owned `thermal.dimension.system` value. No value is assigned by this contract. | Withheld: unresolved polarity and installation scope. False cannot choose auto/heat/cool; true cannot establish every service's off mode. A canonical-only consumer loses the legacy switch indicator. |
| RR=0x0007 switch | `thermal.status.operation` (`active`, `idle`) | No emitted FactKey or service binding from the switch. | Withheld: switch selection does not prove observed activity, idle, or `thermal.action.state`. Canonical consumers cannot infer an action or operation from it. |
| RR=0x0007 switch | `thermal.status.fault` (`clear`, `present`) | No emitted FactKey or service binding from the switch. | Withheld: no fault diagnosis evidence. Off and healthy/faulted are independent. |
| RR=0x0096 maintenance, false or true | `thermal.mode.system` | No emitted FactKey or service binding from maintenance. | Withheld: maintenance state is not a system mode. |
| RR=0x0096 maintenance, false or true | `thermal.status.operation` | No emitted FactKey or service binding from maintenance. | Withheld: `active` means operation in this field, not maintenance-active; maintenance false does not establish idle. |
| RR=0x0096 maintenance, false or true | `thermal.status.fault` | No emitted FactKey or service binding from maintenance. | Withheld: maintenance true must not imply fault.present; maintenance false must not imply fault.clear. The pack has no maintenance field. A canonical-only consumer loses the maintenance indicator; retain it natively and in compatible legacy reads. |

A future **source-specific equivalence candidate** could map the switch's proven
off code to `thermal.mode.system.off` for the exact owned system service, with
an explicit system FactKey dimension, if public evidence resolves polarity,
service scope and qualification. This is **Hypothesis**, currently withheld;
even that evidence would not map the other code to auto/heat/cool, other thermal
services, operation, action or fault. Another independently qualified source may
supply fault or activity observations under its own binding. Neither false
maintenance nor a matching UI label is a substitute for that source. Maintenance
needs an accepted semantic definition before it can become a canonical fact;
this contract creates no universal maintenance definition.

## Transition and synthetic acceptance cases

These are manual contract examples, not captures, executed tests or runtime
qualification. Run each Boolean case independently for each tuple; an update to
one source says nothing about the other. `00`, `01`, and `02` below are synthetic
one-byte value payloads, not complete response telegrams.

| Case | Current legacy behavior / distinction | Proposed retained state and canonical result |
| --- | --- | --- |
| Valid `00` | Successful integer decode yields false, not absence. | Retain zero/false. Maintenance false is not fault.clear; switch false selects no full system mode. Withhold the table's unsupported mappings. |
| Valid `01` | Successful integer decode yields true. | Retain one/true. Maintenance true is not fault.present; switch true alone selects no mode, operation or action. |
| Missing read, never acquired | No new Boolean pointer. | Record missing acquisition, no fabricated false, no canonical fact. |
| Missing read after prior success | Non-destructive merge retains the prior Boolean. | Keep last-known-good bytes, evidence revision and age; record missing new acquisition separately. Do not renew freshness. |
| Unknown raw `02` | If accepted by the integer decoder, nonzero becomes true; that conversion is not Boolean semantic validation. | Retain raw unknown code, withhold semantic admission; never normalize it into a proven maintenance/off assertion. |
| Invalid payload (empty, malformed or wrong correlated selector) | Reader failure produces no new field; a prior Boolean may survive merge. | Retain failure evidence separately from prior valid data; withhold the invalid candidate. It is neither valid zero nor missing by default. |
| Stale prior `00` or `01` | Retained legacy Boolean alone has no per-field receipt-age proof. | Preserve value and original receipt; mark stale and withhold current canonical admission. Stale true is not current true; stale false is not clear. |
| Fresh decodable but unqualified observation | Legacy Boolean may be populated regardless of the proposed mapping qualification. | Keep acquisition success separate from unqualified semantics. No canonical admission. |
| Source replacement A → B, B has no field yet | Merge may retain A's Boolean while replacing the controller identifier. | Keep A's evidence under A's epoch as historical last-known-good; B starts missing and unqualified. Never relabel A's value as B's or inherit admission. |
| Conflicting candidates | These two legacy Boolean readers supply no canonical conflict-resolution proof. | Retain each candidate with independent owner/revision. Withhold unresolved canonical equivalence; never average codes, choose newest across unrelated sources or overwrite a qualified candidate with an unrelated absent fact. |
| Evidence revision changes without new acquisition | A legacy Boolean does not encode the revision. | Re-evaluate qualification under the new revision while preserving original receipt and raw bytes. A withdrawn equivalence revokes admission, not evidence retention. |
| Independent source supplies qualified fault.present while maintenance is missing/false | No equivalence from maintenance is established. | Preserve the independent fault projection and its owner; do not clear or withhold it because maintenance is absent/false. |

## Projection accounting and consumer cutover

Produce one disposition per requested `(kind,item_id)` using the existing
envelope. The table lists source-level reasons; it does not request six duplicate
field dispositions. If these are the only candidates, each of the three
requested field items is withheld once, with source-specific reasons retained.
If an independent admitted source already projects a shared definition item,
missing or withheld maintenance/switch candidates cannot overwrite that item's
projected disposition. Report their losses outside shared definition accounting.
An actual unresolved conflict for the same bound fact requires explicit
conflict handling; a missing unrelated fact is not such a conflict. Keep output
ordering deterministic under the existing envelope contract.

Preserve `state.system_off` and `state.maintenance_due` compatibility until a
separate downstream cutover implements and reviews their retention/removal.
MCP and GraphQL must express the same values, absence, provenance, freshness,
qualification and loss decisions through their existing fields/aliases; neither
surface may silently invent a canonical substitute. Native retention plus
explicit withholding is this slice's acceptance, not a claim of implemented
transport parity. A canonical-only consumer's lost indicators must be disclosed
before legacy removal; missing maintenance representation is not repaired by
relabeling fault or operation.

This bounded gateway-to-SemReg contract is distinct from broad Matter source
inventory and temperature-field migration. It changes neither G5 D1–D5/O8 nor
the driver-owned eeBUS output binding. Downstream implementation, independent
review, committed-head gates, transport/runtime verification and hardware
acceptance remain separate; readable prose is none of those proofs.
