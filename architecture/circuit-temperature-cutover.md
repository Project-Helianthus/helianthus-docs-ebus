# Heating-circuit temperature cutover contract

> License: AGPL-3.0. Proposed application migration contract for issue #673;
> no producer, pack, API, fixture, write route or runtime behavior changes here.

This is a partial contract slice advancing
[ebusgateway#952](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/952).
The parent remains open. All transitions below marked **proposed** are future
work. Nothing described here is stable before the Helianthus 1.0 release.

## Sources and authority

Read the native contract before considering the implementation or pack:

- **N:** [B524 register catalog, circuit selectors](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md#gg0x02--heating-circuits-multi-instance).
  Its Wire legend makes float byte order profile-dependent. Its circuit section
  supplies the selector scope, units and the one-byte RR0020 correction.
- **L:** [legacy semantic mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md).
  The circuit table describes existing MCP paths; its separate system thermal
  mapping supplies lifecycle precedents, not qualification for circuits.
- **G:** [gateway semantic poller](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go),
  specifically `refreshCircuits`, `readB524Float32LE`,
  `mergeCircuitSnapshotNonDestructive`, `publishCircuits`, and
  `readDhwPseudoCircuitEvidence`. This proves implementation behavior only.
- **T:** [existing Thermal pack definitions](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go),
  specifically `fields`, `services`, `capabilities`, and `Metadata`.
  Definitions establish available semantic vocabulary, not native equivalence.

**Proven** below means supported within the cited source's stated context:
source inspection can prove a code path, but cannot prove a wire meaning.
**Hypothesis** identifies a proposed semantic equivalence awaiting evidence.
**Unknown** identifies unresolved native meaning, applicability or binding.
These labels are independent of qualification and runtime admission. No row
qualifies an installation or establishes current SemReg publication.

## Finite inventory

All three rows use `PB=0xB5, SB=0x24, OP=0x02, OT=0x00, GG=0x02` (reads), a
separately qualified circuit instance `II`, and register `RR` as shown. OP=0x06
is a different namespace and cannot substitute. N scopes ordinary heating-circuit
candidates to II00..II08 for the VRC720 family; candidates are not presence
proof. Other families require their own qualification. II09 is virtual
native-water identity with no public presence predicate and is excluded from
this heating-circuit binding. Retain its evidence separately. RR0008 or RR0020
must not be used as a virtual-circuit presence test, even though G currently
has temperature-based pseudo-circuit discovery logic. II0A observations do not
extend the documented scope. No public zone ID establishes circuit identity.

| RR | Native contract (N) | Current legacy consumers (L; G) | Proposed semantic disposition (T) |
| --- | --- | --- | --- |
| `0x0008` | `circuit_flow_temperature`; read-only VF[x] circuit flow sensor; `f32`, °C; byte order qualified by profile. Catalog-supported measured quantity; broader applicability Unknown. | MCP `ebus.v1.semantic.circuits.get`: `[].state.current_circuit_flow_temperature`; G reads `FlowTemperatureC`, publishes `CircuitState.FlowTemperatureC` (GraphQL `flowTemperatureC`). | Hypothesis: `thermal.measurement.water_temperature`, `unit.celsius`, field dimension `thermal.dimension.temperature`, service `thermal.service.circuit`. Withhold until exact temperature-role FactKey value and runtime circuit binding are qualified. Never reuse `temperature:system_flow`. |
| `0x0007` | `circuit_flow_temperature_setpoint`; `f32`, °C; installer-field candidate; physical menu correspondence requires corroboration. Requested and measured flow are distinct. | MCP `[].state.heating_circuit_flow_setpoint`; G `FlowSetpointC`, GraphQL `flowSetpointC`. | Withheld. `thermal.setpoint.temperature` exists, but no cited definition establishes it as the circuit's read-only requested-flow observation. Its set-temperature capability is zone-scoped. No operation or write capability follows from this value. |
| `0x0020` | `circuit_unknown_10`; observed UCH one-byte raw `00`. N explicitly says it is not a temperature; enum/status meaning Unknown. | MCP `[].state.calculated_flow_temperature` is documented as `f32`; G reads `CalcFlowTempC`, GraphQL `calcFlowTempC`. This conflicts with N. | Withheld, including numerically plausible four-byte values. No matching computed-flow definition exists in T. Preserve raw evidence; assign neither °C nor an enum interpretation. |

The table inventories direct consumers visible in L and G. G publishes sorted
instance-indexed circuit snapshots through its provider and update hub; it does
not establish any HA entity mapping. HA source is outside this evidence set:
its actual consumer paths and migration behavior remain Unknown. Names such as
`Hc{hc}FlowTempCalc` corroborate naming only and cannot overrule N.

T defines `thermal.service.circuit` with service identity dimension
`thermal.dimension.circuit`. That service binding is separate from the
measurement's `thermal.dimension.temperature` FactKey dimension. The exact
qualified asset/service identity and temperature-role text value are unresolved
here; no new dimension token, pack ID or full circuit capability is introduced.
T's water-temperature quantity bounds are -100..200 °C inclusive. They are
semantic validation bounds, not native physical limits or qualification.
The existing generic temperature setpoint bounds do not qualify RR0007.

System-flow/boiler-flow aliases, M14/M15 boiler temperatures, W27 outdoor and
aggregate values, W30 pressure, pump status, parameters and writes are excluded.
No unmerged W specification, J/M implementation or other X contract is needed.
The eeBUS output binding remains driver-owned; this page defines none.

## Proposed observation and admission boundary

The following are logical requirements for later implementation, not a new
serialized schema or endpoint (N native selectors; L lifecycle precedent; T
semantic vocabulary):

1. Keep the full `(PB, SB, opcode, operation type, group, instance, register)`
   with initiator and responder, direction, request/reply association, raw
   payload and value bytes. Bind it to source identity and source epoch, device
   family/profile, profile revision and decoder/semantic revision, qualified
   asset/service,
   driver generation, and evidence reference. Retain available firmware context
   without inventing it. An address alone is not a profile or source identity.
   Retain `OT=0x00` for these read observations; `OT=0x01` write-attempt evidence
   belongs to a separate binding and cannot update or refresh retained reads
   (see [B524 wire format](../protocols/vaillant/ebus-vaillant-B524.md#1-scope-and-framing)).
2. Record original wall-clock receipt and monotonic receipt with its clock
   epoch. Evaluation time is separate. Cache retrieval, projection and another
   field's success must not replace receipt. Missing provenance or unknown
   qualification withholds projection; preserve the observation for diagnosis.
3. Validate request/reply association and exact selector/source/profile binding
   before decoding. For qualified RR0008/RR0007 float profiles require exactly
   four value bytes, then IEEE-754 decoding using that profile's byte order.
   Frame/envelope bytes are not value bytes. Do not pad short values, truncate
   extra bytes, guess byte order or decode RR0020 as float. The catalog supports
   little-endian for the characterized VRC720 family, not all controllers.
4. A decoded exact zero is present. Reject NaN and either infinity. For the
   RR0008 candidate, reject values outside T's inclusive -100..200 °C interval
   before semantic conversion; never clamp. Native evidence remains intact.
   This page assigns no new native sentinel or RR0007/RR0020 numeric range.
   Finite RR0007 values still remain withheld from SemReg.
5. Admission requires independently qualified native meaning, profile, active
   physical circuit identity, exact service/FactKey binding, decoding and
   semantic bounds. A matching field name is insufficient. If any requirement
   is unresolved, withhold; do not seek a substitute source or alias.

No credential, principal or permission check is added. Qualification here is
an evidence/data-admission condition, not an authorization feature.

## Proposed retention and recovery

G currently rejects float values shorter than four bytes and non-finite
floats, but reads the first four bytes of longer values. Its partial merge
retains non-nil temperature pointers across failed reads. The scoped pointers
have no individual receipt timestamp in that merge/publication path; a live
publication can contain retained fields. This is code behavior, not proof of
freshness. Controller-change handling in that merge explicitly clears certain
status fields, without equivalent temperature clearing (G).

Proposed: keep independent last-known-good value, receipt and evidence for each
full binding and selector. A missing, invalid or rejected attempt updates its
own diagnostic disposition, never overwrites a retained value with zero/null
and never refreshes its receipt. Valid sibling fields can advance independently.
No retained value means explicitly unavailable. A retained value remains
historical evidence when no longer usable as a current observation.

Freshness must be evaluated from original monotonic receipt against a declared
binding freshness budget. This page does not invent a duration. Missing budget,
clock-epoch mismatch or missing receipt means freshness Unknown and no current
projection. Once the budget expires, retain last-known-good evidence as stale
and expose current unavailability; do not replay it as fresh. Restored cache
cannot establish qualification or monotonic continuity by itself.

A foreign instance/source/profile/revision or driver generation cannot update
another binding. A source replacement at the same address creates a separate
binding pending qualification; old evidence stays attributable to the old
binding. Recovery requires a new valid observation for the same qualified
binding, with a new receipt; then only that field becomes current. Out-of-order
older receipts do not displace newer accepted evidence. There is no cross-field
fallback or automatic promotion of a previously rejected observation.

## Synthetic before/after review cases

These are manual contract examples, not captures, executable tests or runtime
results. Assume an independently qualified ordinary circuit binding A at II00
and a second binding B at II01. For proposed positive RR0008 cases only, assume
its unresolved FactKey binding has subsequently been approved. Without that
approval every candidate remains withheld. Each row starts independently with
A's RR0008 last-known-good 40 °C at receipt R, unless stated otherwise.
Bytes below are value bytes in the qualified little-endian example profile.
“Before” describes G's float helper/merge, not an end-to-end API guarantee.

| Case / input | Before: current G behavior | After: proposed contract |
| --- | --- | --- |
| Exact zero RR0008, `00 00 00 00`, newer receipt | Accepts 0; replaces retained pointer. | Accept 0 °C as present; preserve new receipt/evidence. No truthiness-based absence. |
| Absent value / failed read | No new float; partial merge retains 40. Empty reply does not establish inactive circuit. | Keep 40/R; record failed attempt. Unavailable if no prior value; do not infer absence or inactivity. |
| NaN `00 00 C0 7F`, +infinity `00 00 80 7F`, -infinity `00 00 80 FF` | Helper rejects; retains 40. | Reject each; keep 40/R and raw evidence with invalid disposition. |
| Finite out-of-range RR0008, 201 °C (`00 00 49 43`) | Helper accepts finite 201; no T range check there. | Reject semantic candidate against T; retain 40/R without clamping. |
| Short RR0008, `00 00 20` | Helper rejects; retains 40. | Reject malformed value length; retain 40/R. |
| Over-length RR0008, `00 00 20 42 00` | Helper accepts first four bytes as 40. | Reject extra byte; retain 40/R. Intentional stricter boundary. |
| Stale R, no new observation | Merge can retain 40; publication does not prove individual freshness. | Keep historical 40/R; current value unavailable with stale disposition after declared budget. |
| B/II01 sends valid 45 °C while A is queried | G keys snapshots by instance; full binding isolation is not proved by that alone. | Never update A; process B only under B's separately qualified binding. |
| Foreign source or changed profile/revision at A's address | Temperature merge does not establish full provenance isolation. | Withhold new binding; preserve A's old evidence separately, never relabel it. |
| Recovery: valid RR0008 45 °C (`00 00 34 42`), newer receipt for A | Helper accepts; merge replaces pointer. | Replace only A/RR0008, record new receipt; current only if all admission conditions still hold. |
| Partial recovery: RR0008 valid, RR0007 absent | Merge can update measured field independently. | Advance measured field only; retain request evidence unchanged and withheld. |
| RR0007 valid float 45 °C or exact zero | G can publish request through FlowSetpointC. | Preserve request evidence separately; no measurement substitution and no SemReg projection. |
| RR0020 native `00`, or hypothetical four-byte `00 00 34 42` | One byte fails float helper; four bytes could publish CalcFlowTempC. | Both withheld from temperature projection; retain one-byte raw evidence or flag conflicting layout. No invented status meaning. |

## Future cutover seams and remaining acceptance

Gateway work must join qualified native observations before semantic conversion,
carry per-field receipts through partial merge/cache restore, enforce exact
length and bounds, and isolate source epochs/instances in retained state.
`refreshCircuits`, its decoder/merge and `publishCircuits` are visible seams (G),
not authorization to modify them in this slice. Removing the RR0020 float
assumption and the pseudo-circuit temperature presence heuristic needs a
separate compatibility implementation and review against N.

Preserve `ebus.v1.semantic.circuits.get` compatibility and the corresponding
GraphQL circuit fields. A later migration must explicitly document any change
to legacy nullable/omitted values, especially retained CalcFlowTempC data;
this contract does not silently redefine those responses. On any proposed
semantic projection, MCP and GraphQL must read the same detached coherent
snapshot with deterministic instance ordering and equivalent value/unit,
identity, receipt, freshness, qualification, loss and withholding dispositions.
MCP omission and GraphQL null may differ in representation, never in admission
or freshness meaning. If an existing envelope cannot express a disposition,
record explicit projection loss in a separately reviewed interface contract;
do not fabricate a numeric value. No new namespace is introduced here.

HA follow-up must identify the actual entity/coordinator consumers, preserve
measured versus requested fields and circuit identity, and agree unavailable
versus retained-display behavior with gateway parity tests. No HA behavior is
verified by these sources. Equivalent MCP/GraphQL and HA recovery tests,
including every identity component and individual partial failures, remain
implementation acceptance, not completed evidence.

Before cutover, obtain publishable native request/reply evidence for the exact
family/profile/revision and physical circuit, including correlated measured
and requested values and RR0020 width/meaning conflicts. Complete the missing
FactKey/service binding, freshness policy, qualification/admission review and
legacy compatibility decision. Do not promote hypotheses using UI labels,
pack matches or synthetic cases. Hardware qualification requires separately
authorized observations; this page performs none and authorizes no live writes.

This page changes no producer, shared mapping, pack or output binding. Source,
claim, table and example review plus document readability are documentation
evidence only. They do not validate semantics at runtime, transport, hardware,
profile admission or the remaining parent acceptance. Full committed-head gates,
publication audit and independent review remain required before publication.
