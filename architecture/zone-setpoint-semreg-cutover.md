# Zone setpoint role preservation before SemReg cutover

This is the proposed, bounded gateway-to-SemReg acceptance contract for zone
manual, computed effective, quick-veto override and holiday temperatures.
It advances [gateway #952](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/952)
and [docs #700](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/700)
without closing the parent. It is distinct from Matter source inventory and
other temperature-field cutovers. Nothing here establishes stability before
Helianthus 1.0, a universal setpoint definition, or a new namespace.

## Evidence and current implementation

The following public sources are the claim anchors; sections and function names
identify the reviewed material. Links use public `blob/main` paths, which may
move after review.

- [Native B524 catalog](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md):
  “GG=0x03 — Zones”, “Zone Mode Derivation” and “Open questions”. This is the
  native documentation contract first; naming and catalog constraints do not
  constitute installation qualification or prove a write route.
- [B524 semantic mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md):
  `ebus.v1.semantic.zones.get` and “SemReg thermal v1 read-only Vaillant mapping”.
- [Existing typed thermal mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/fixtures/vaillant-semreg-thermal-map-v1.json):
  `qualification`, `mappings`, `lifecycle`, `nonclaims`. It covers system
  outdoor/flow temperatures, not zones; its qualification is Unknown and
  `runtime_qualification_permitted` is false. It cannot qualify this slice.
- [Gateway implementation](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go):
  zone constants, `localZones`, `refreshZoneSlowConfigFields`, `refreshConfig`,
  `publishZones`, `readB524ValueWithMaxAge`, `readB524Float32LE`,
  `resolveAssociatedCircuitInstance`, `deriveZoneModeAndPreset`.
- [Thermal pack definitions](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go):
  `fields`, `services`, `capabilities`, `operations`, `Metadata`.

**Proven (source inspection only):** `refreshZoneSlowConfigFields` tries
`zone_target_temp` at RR=0x0022 first, and tries
`zone_fallback_manual_temp` at RR=0x0014 only if the first read produces no
pointer. Both become `TargetTempC`. The fallback constant's “manual” comment
conflicts with the native catalog's computed effective role. The driver name
is not native proof. Neither successful decode nor equal numbers proves these
roles equivalent. `readB524Float32LE` requires at least four bytes, decodes the
first four little-endian bytes and rejects NaN/infinity; it does not establish
units or installation bounds. A valid zero produces a pointer and prevents
fallback. `readB524ValueWithMaxAge` can use age-bounded scheduler data, so read
success alone does not prove a new acquisition.

**Proven (source inspection only):** quick-veto temperature/duration/end fields
and holiday setpoint/date/time fields are read separately and copied to the
zone snapshot. `publishZones` exposes `TargetTempC`, `QuickVetoSetpointC`,
`QuickVetoDurationH`, `QuickVetoExpiry`, `HolidaySetpointC` and holiday interval
fields in GraphQL zone config. Its quick-veto Boolean is derived from
`Preset == "quickveto"`; expiry is assembled only when that preset and both
end components are present. This assembly does not perform an expiry check.
`refreshConfig` merges via `mergeZoneSnapshotFields`; this contract does not
claim that helper already provides the proposed role history below. Cooling
manual/effective selectors are not read by this slow-config function.

**Hypothesis / Unknown (native evidence):** the catalog identifies manual and
effective roles below, including RO effective values. Correlated behavior for
a target family/installation is still required for admission. The catalog's
Open questions explicitly leave quick-veto and holiday units and date codecs
unestablished, despite °C/time labels in rows. Family mode-code conflicts and
special-function interpretation remain unresolved. UI modes, C categories,
flags and candidate write bytes do not qualify writes. These gaps must remain
visible alongside each candidate, rather than becoming Proven through code.

## Native selectors and retained provenance

Every row uses `PB=0xB5, SB=0x24, OP=0x02, GG=0x03, II=<native zone instance>`
and the RR shown. II is retained without display-ID renumbering. Requests run
from the binding's initiator to its controller destination; replies run from
target to initiator. Neither endpoint is inferred from `zone-1`. Preserve the
actual selector/payload bytes, direction, endpoints, decoded type, unit and
codec evidence, family context and firmware context when known, and evidence
reference. OP=0x06 and other groups/instances never substitute implicitly.

| Role | RR and catalog interpretation | Current legacy behavior | Proposed disposition |
| --- | --- | --- | --- |
| Heating manual | 0x0022, f32, °C catalog label | Primary `TargetTempC`; catalog gives 15..30 step 0.5 per ebusd | Read-only candidate only after exact role/binding qualification and representability decision below |
| Heating computed effective | 0x0014, f32, °C, stable RO computed output | Fallback `TargetTempC`, despite constant name | Separate effective candidate; never relabel manual or advertise `set_temperature` |
| Cooling manual | 0x0023, f32, °C; cooling applicability | Not read by the reviewed function | Withheld until independently qualified and role representable; 0x0002 cooling setpoint is another selector, not an alias |
| Cooling computed effective | 0x0015, f32, °C, stable RO; cooling applicability | Not read by the reviewed function | Separate read-only candidate, withheld pending qualification/representation |
| Quick-veto override | 0x0008, f32; unit unresolved | Separate `QuickVetoTempC`, with duration 0x0026 and end time/date 0x001E/0x0024 | Withheld: unit, applicability/expiry semantics and role representation need owner evidence |
| Holiday target | 0x0005, f32; °C candidate, unresolved | Separate `HolidaySetpointC`; dates 0x0003/0x0004 and times 0x0021/0x0020 | Withheld: unit, interval semantics and role representation need owner evidence |

Zone modes at 0x0006/0x000E, special-function state at 0x001B, and heating/
cooling schedule flags at 0x0019/0x001A are separate contextual observations.
Do not substitute their meanings, or infer heating versus cooling ownership
from a display label. `resolveAssociatedCircuitInstance` is an implementation
heuristic, not proof of native topology. The zone catalog's raw assignment at
0x001C remains separate evidence. System holiday GG=0x00 selectors and other
families' comfort selectors cannot replace the zone holiday/manual rows.

## Proposed FactKey and service decision

The existing pack defines `thermal.setpoint.temperature` as a quantity in
`unit.celsius`, dimension `thermal.dimension.temperature`, with numeric bounds
-50..150. It defines `thermal.service.zone` with service FactKey dimension
`thermal.dimension.zone`, plus `thermal.capability.read.zone`.
The service zone identity and the temperature field dimension are distinct.
`thermal.capability.set_temperature` belongs to the zone service and
`thermal.operation.set_temperature` uses this field as argument; their presence
in pack metadata does not advertise either for a particular observation.

A proposed fact may use the existing field only if an owner-approved mapping
assigns an unambiguous temperature-dimension value identifying the exact zone,
heating/cooling role and manual/effective/override/holiday meaning without
collision, and the existing pack validates that complete FactKey and value.
The field reference and its semantic revision, exact dimension set/value,
asset binding and separate zone service identity must all be explicit. A zone
service dimension alone is not the temperature FactKey. Native source identity
remains provenance, not an invented extra FactKey axis. This document allocates
no role tokens, definitions, aliases, or service IDs.

The supplied pack tables have no explicit role selector or override/holiday
interval fact. They do not establish an approved encoding of those meanings
in a temperature dimension. Therefore **no complete role-preserving zone
FactKey is admitted by this slice today**. Each role remains withheld pending
the owner decision and qualified mapping; do not overload one key with several
roles or mint a universal role definition. Even manual heating is conditional,
not an already accepted mapping. If an existing key can preserve one exact
meaning but cannot represent another, admit only the qualified representable
meaning and retain the other outside current projection accounting.

Qualification, acquisition and admission are independent from Proven,
Hypothesis and Unknown. Admission additionally requires known canonical unit,
finite valid value, coherent source-specific bounds within pack bounds,
qualified topology/role, current source epoch/generation and freshness, and
accepted semantic revision. Unknown unit, reversed bounds, empty intersection,
or a value outside accepted bounds withholds the candidate; never clamp it or
substitute a different role. Zero/false are valid when their own typed contract
and bounds allow them; neither means missing. No new principal, credential or
permission gate is added. Existing trust/admission checks remain intact;
authentication/authorization remain 0.11 work, with no authorization gate
before 0.9.

## Proposed selection, retention and loss contract

Retain observations independently per native selector and role, including
asset, service, source, source epoch, driver generation, evidence reference,
semantic revision, qualification and receipt/freshness context. Preserve original
receipt information separately from evaluation context as in the existing
thermal lifecycle contract; evaluation never refreshes acquisition age.

Selected means currently admitted for a single exact meaning. Retained means
last-known-good evidence/history with explicit non-current status, not a current
selected value. A missing, malformed, stale or unqualified update cannot erase
unaffected admitted roles or refresh retained data. Retain rejected raw evidence
and reasons separately from last-known-good values. Do not carry admission
across source replacement, generation or service changes at the same display
ID. Retain old history under its old identity; requalify the new binding.
Conflicting qualified candidates for the same meaning cause withholding of that
selection until an explicit source policy resolves them, even at equal numbers.
Different roles at equal numbers coexist in history and never resolve conflict
by numeric equality.

Legacy primary/fallback selection remains documented compatibility behavior,
not the proposed semantic policy. An absent primary with a present fallback
may still populate legacy `target_temp_c`, but cannot populate the manual
FactKey. Do not use invalid/stale/unqualified manual data as permission to
relabel effective data. Independently qualified effective data can be selected
only under its own representable key. An expired override retains its target
and interval history but is not a current override selection; an uncertain
expiry remains Unknown. Holiday history likewise survives inactivity. This
contract designs no calendar execution, changes no G5 D1-D5/O8 rule or native
write path, and infers no active role from stored dates alone.

For each requested `(kind,item_id)`, emit one deterministic projection
disposition after aggregating all matching candidates. Source-specific losses
and role qualification remain attached to their evidence; they are not extra
shared-definition dispositions. If a representable fact projects for
`thermal.setpoint.temperature`, an absent holiday/cooling source must not later
overwrite that shared field disposition as withheld. If none projects, the one
item disposition explains withholding and the distinct role losses. Preserve
existing deterministic envelopes and identical MCP/GraphQL selection,
availability, provenance and loss semantics. Legacy names/aliases and partial
last-known-good behavior remain compatibility obligations until a downstream
cutover explicitly resolves each loss. eeBUS output binding remains driver-owned.

## Synthetic acceptance cases (proposed, not executed runtime evidence)

All values and labels below are invented. They establish review expectations,
not native proof or qualification. “Eligible” always includes the owner mapping
and admission conditions above; present-day role projection remains withheld.

| Case | Expected selection, retained history and consumer loss |
| --- | --- |
| Manual heating, effective heating, manual cooling, override and holiday each equal 20 °C | Keep five distinct roles/selectors; no equality-based merge. A one-number legacy target cannot preserve them. Each unrepresentable role is withheld with its own loss reason. |
| RR=0x0022 absent, RR=0x0014 eligible at 20 °C | Legacy fallback target may be 20; manual is missing, effective alone is eligible under its own approved key. Record loss of manual-target equivalence. |
| Override target 21, expiry known elapsed | Retain override history and expiry evidence; no current override selection and no synthetic manual/effective replacement. A stored override value does not imply active override. |
| Holiday/override value 20, unit unknown | Retain raw/decoded evidence; withhold canonical Celsius quantity despite legacy C-suffixed names. |
| Bounds minimum 25, maximum 15, or non-overlapping source/pack bounds | Withhold with invalid-bound reason, retain prior valid history; no widening or clamping. |
| Service A becomes service B; every other axis/value stays fixed | Treat as independent binding change. A's retained evidence cannot qualify B; no service-identity omission from admission comparison. |
| Missing read; malformed/NaN read; stale value; unqualified source | Four distinct reasons, each preserving unaffected roles and old non-current history. None is a zero or fallback authorization. |
| Eligible effective 0 °C; schedule flag false | Accept zero if qualified bounds allow it; preserve typed false as context, not missing and not a temperature. Manual policy may reject zero independently. |
| Same display zone, replacement source/epoch/generation | Fence old admission and retain old provenance; new source requires qualification even at the same value. |
| Two candidates disagree, or agree numerically but lack equivalence evidence | Withhold ambiguous selection; retain both candidates. Do not choose newest receipt or equate sources solely by value. |
| One approved field projects; cooling/holiday facts absent | Exactly one requested field disposition stays projected; list missing source losses separately. |

Source-specific equivalence requires matching native meaning, selector scope,
unit/codec, asset and zone service, semantic revision and lifecycle treatment,
not only equal Celsius values. RR=0x0022 to a qualified manual-only key can be
conditionally lossless for that read. RR=0x0014 to that key is a role loss;
RR=0x0014 to its own approved effective key can preserve a read but loses any
legacy implication of writability. Neither effective selector advertises
`set_temperature`, its capability, operation or effect. Quick-veto/holiday
flattening loses interval/activation meaning; cooling-to-heating flattening
loses thermal role. Those losses block equivalence, not native evidence retention.

## Acceptance boundary

Manual source/claim, transition, loss, synthetic-case and link-path review is
the contract gate. Readability is not semantic validation, runtime proof or
hardware acceptance. Downstream work must resolve owner representation choices,
qualify family-specific native semantics and units, and demonstrate compatibility
and MCP/GraphQL parity before replacing legacy projections. Cutover also requires
a reviewed route, write-authority and compatibility decision for Home Assistant
`set_temperature`: the [documented zone write path](../development/ha-integration.md#zone-writes-group-0x03)
lists both RR=0x0022 and RR=0x0014. Resolve that consumer's behavior explicitly
before cutover; RR=0x0014 remains a read-only effective value, and this contract
qualifies neither selector for writes. This prose introduces no fixture, schema
or validator, no new transport behavior and no writable support.
Independent review, committed-head gates and hardware acceptance remain separate.
