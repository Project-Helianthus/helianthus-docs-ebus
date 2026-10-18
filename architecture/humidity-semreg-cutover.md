# Humidity provenance and SemReg cutover

This AGPL-3.0 architecture contract covers controller-zone, remote-room and
circuit relative-humidity observations, and the separate maximum-room-humidity
configuration threshold. It is the bounded migration acceptance slice for
[docs issue #698](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/698),
advancing [gateway #952](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/952)
and Project #2 without closing the parent. It is distinct from the broad Matter
source inventory and temperature cutovers. Nothing here is stable before
Helianthus 1.0. This page specifies proposed acceptance, not an implemented cutover.

## Evidence and source boundary

The public native contract comes first: the [B524 register catalog][native],
sections **Table Legend**, **Group Topology**, **OP=0x02 — Local Parameter
Registers** (System, Circuits, Zones), **OP=0x06 — Controller-Mediated Device
Parameters** (remote-regulator and remote-thermostat families), and **zmapping —
Zone room temperature sensor mapping**. Its category C means configuration
candidate; FLAGS and historical access labels do not prove writable support.
Family-dependent codecs, presence and mapping remain independently qualified.

The [semantic mapping][mapping], sections `ebus.v1.semantic.system.get`,
`ebus.v1.semantic.circuits.get` and `ebus.v1.semantic.zones.get`, documents legacy
field associations. The [gateway source][gateway] proves implementation behavior
only. The [Thermal definitions][thermal], tables `fields`, `services`,
`capabilities` and function `Metadata`, establish available definitions, not a
native source binding. The [existing thermal fixture][fixture], `qualification`
and `mappings`, is temperature-only and explicitly disallows runtime
qualification under its evidence-gap revision; it supplies no humidity binding.

- **Proven:** the cited public catalog records the selectors, types, units and
  sensor descriptions below; source inspection establishes the code paths
  described here. This does not claim newly reproduced native observations.
- **Hypothesis:** an exact qualified humidity sensor could project through the
  existing relative-humidity quantity with the service associations below.
  Raw zone mapping labels are not independent proof of physical sensor identity.
- **Unknown:** complete humidity FactKey role values, collision-free source/service
  bindings, exact family/profile qualification witnesses and accepted lifecycle
  policy for this cutover. Acquisition, qualification, freshness and admission
  are independent of these evidence labels.

## Native selectors and current legacy behavior

All tuples are `(opcode, group, instance, register)` under `PB=0xB5, SB=0x24`.
The initiator requests from the selected controller target; values return from
that target. OP06 is controller-mediated: target identity and remote-slot sensor
identity are both required. `z`, `c` and `r` below denote separately qualified
zone, circuit and remote instances, not interchangeable indices.

| Observation | Exact selector and native interpretation | Current legacy implementation |
|---|---|---|
| Controller-zone relative humidity | `(0x02,0x03,z,0x0028)`, f32 percent; catalog says from room sensor | `refreshZoneSlowConfigFields` reads `zone_current_humidity` into `HumidityPct`; `publishZones` exposes `Zone.State.CurrentHumidityPct`, the semantic mapping's `zones[].state.current_humidity_pct`. A controller-mediated zone field does not establish a physical sensor inside the controller. |
| Remote-room relative humidity | `(0x06,0x09,r,0x0007)` or `(0x06,0x0A,r,0x0007)`, f32 percent; remote-family catalog describes installed humidity sensor and NaN when absent | `refreshRadioDevices` reads `device_slot_room_humidity` for connected slots with `readB524F32`; `publishRadioDevices` exposes `RoomHumidityPct`. `mappedRadioRoomStateForZoneLocked` may supply a zone fallback. GG09 and GG0A remain different native sources. |
| Circuit room relative humidity | `(0x02,0x02,c,0x0022)`, f32 percent; catalog says from room sensor | `refreshCircuits` populates `HumidityPct`; `publishCircuits` exposes `Circuit.State.Humidity`. The semantic mapping names this `circuits[].state.current_humidity_pct`; spelling does not imply identical serialized field names in every API. |
| Maximum-room-humidity configuration threshold | `(0x02,0x00,0x00,0x000E)`, u16 percent, configuration candidate | `refreshSystem` reads `system_max_room_humidity`; `publishSystem` exposes `Config.MaxRoomHumidity`, corresponding to `system.config.max_room_humidity`. This is not an observed humidity sample. |

`readB524Float32LE` requires at least four value bytes, decodes the first four
little-endian, rejects NaN/infinity and accepts finite out-of-range values; it
does not impose 0..100 or reject trailing bytes. `readB524F32` wraps this reader.
This is decoder behavior, not proof that every family uses that codec or reply
shape. The native catalog's Table Legend requires profile-qualified byte order.
The remote section describes a response header before the value; header bytes
must never be decoded as the measurement. Exact response correlation and shape
must be qualified rather than inferred from a permissive helper.

`mergeCircuitSnapshotNonDestructive` updates humidity only for non-nil incoming
humidity, retaining prior humidity on a failed member read. `refreshSystem` and
`mergeSystemSnapshotNonDestructive` similarly preserve a non-nil threshold.
Do not generalize these member rules into a claim that every zone or remote
refresh retains all failed members. Zone config merges use
`mergeZoneSnapshotFields` and an explicit field set. `refreshRadioDevices` can
retain a prior slot when its connection read fails after phase-one activity,
returns without replacing the map on an entirely unobserved pass, and otherwise
replaces the radio map; a newly built snapshot can have nil humidity. These
paths do not implement the proposed per-source freshness policy below.

## Legacy selection must remain visible

`publishZones` chooses the stored controller-zone humidity whenever non-nil.
It asks for remote state when temperature or humidity is nil, but fills each
member independently only when that member is nil. Thus controller humidity
wins even if a remote reading differs or is newer; valid zero is non-nil.
There is no averaging, newest-wins rule or threshold fallback.

The following are **Proven implementation rules**, not native enum qualification:

1. `mappedRadioRoomStateForZoneLocked` uses raw zone binding
   `(0x02,0x03,z,0x0013)`. Only a nil binding invokes inference. Explicit zero,
   `0xFFFF`, or a value rejected by `decodeRoomTemperatureZoneMapping` supplies
   no fallback; the decoder also rejects `0x00FF`.
2. Mapping 1 selects the lowest connected instance in OP06 GG09 using
   `firstConnectedRadioDeviceLocked`. Other accepted mappings up to `0x0100`
   select GG0A instance `mapping-1`. A decoded integer is not evidence that the
   corresponding slot exists or its family supports that bound.
3. `inferRadioRoomMappingForZoneLocked` requires exactly one connected GG0A
   snapshot with non-nil `ZoneAssignment == z+1`, then returns `instance+1`.
   Zero or multiple matches returns nil. The resulting integer passes through
   the same mapping rules, including the special mapping-1 GG09 path. Do not
   silently repair this edge case into a direct GG0A selection.
4. `radioDeviceConnected` requires a non-nil true connection pointer.
   `refreshRadioDevices` interprets RR0001 raw 1 as connected. Missing connection
   is not false; false is a known disconnected observation. The mapping helper
   does not separately require pairing or assignment when a binding is explicit.

Preserve `(0x06,GG,r,0x0001)` connection, RR0019 remote address, RR0025 zone
assignment, and raw RR0013 binding as distinct evidence; paired status RR001E
is context, not a newly added selection condition. Missing assignment blocks
inference, but cannot be described as universally blocking an explicit legacy
binding. Family enum candidate labels and slot numbers do not establish physical
identity. A future stricter qualification refusal must be reported as loss,
not disguised as an unchanged selected source.

## Proposed SemReg mapping and withholding

`thermal.measurement.humidity_relative` is an existing quantity in `unit.percent`
with field dimension `thermal.dimension.ratio`, inclusive bounds 0 and 100
(`bound("0",0)` and `bound("1",2)`). Use percent magnitude: 50 percent remains
50, not 0.5. These are pack validation bounds, not device qualification.

| Native role | Candidate service / capability | Cutover disposition against the supplied pack evidence |
|---|---|---|
| Controller-zone measurement | `thermal.service.zone`, `thermal.capability.read.zone`; service identity dimension `thermal.dimension.zone` | Candidate humidity field only. Withhold the complete FactKey and runtime publication until exact sensor role, ratio-dimension value and per-zone/source binding are evidenced. |
| Remote-room measurement | Qualified destination zone may associate with `thermal.service.zone` and its read capability | Keep the remote identity even when projected into a zone. No dedicated remote-room service/binding is established here. Unassigned remote can remain native evidence but has no inferred zone service. Withhold unresolved FactKey or service. |
| Circuit measurement | `thermal.service.circuit`, `thermal.capability.read.circuit`; service identity dimension `thermal.dimension.circuit` | Candidate humidity field only, with separate circuit sensor identity and exact ratio-dimension binding unresolved. Never reuse a zone key because values match. |
| Configuration threshold | No matching humidity-threshold field or operation in `fields` / `operations` | Withhold universal projection: configuration threshold is unrepresentable by the measurement definition. Keep the native/legacy config value; do not repurpose demand level, a temperature setpoint or measured humidity. |

The service identity dimensions are not permission to insert extra zone/circuit
or source dimensions into the humidity FactKey. `Metadata` establishes a field
ratio dimension, but these sources supply no exact humidity role value or
collision-free binding. This page invents none. Until that gap is closed, no
complete humidity FactKey is admitted by this contract. Percent representability
alone cannot qualify a role, sensor, or service. No universal definition, new
namespace, writable route or inferred write support is added.

## Proposed provenance and lifecycle acceptance

Retain raw request/reply and decoded candidate together. A retained observation
must identify the source/controller and actual sensor where established; family,
firmware/profile evidence; initiator/target roles; PB/SB; opcode, group, instance,
register; direction; response status/shape; raw bytes, codec and source unit;
source epoch, driver generation, sequence when available; mapping revision and
raw binding/assignment/connection evidence; original receipt and monotonic clock
epoch; evidence reference and qualification decision. Unknown phenomenon time
stays unknown. Evaluation, publication and cache loading cannot become receipt.
These are provenance requirements, not invented FactKey dimensions.

Proposed current-value admission requires exact source/role qualification,
accepted complete FactKey/service binding, valid finite 0..100 input, correlated
native response, freshness and existing trust/admission checks. No principal,
credential or permission gate is added; authentication/authorization remains
0.11 work. G5 D1-D5/O8 remain unchanged; eeBUS output binding remains driver-owned.

| Transition | Required future disposition and consumer loss |
|---|---|
| Valid fresh member, same qualified identity | Admit only that member; preserve independent failed members. Zero is a value. Connection false is a value about connection, not humidity zero. |
| Missing read, malformed bytes, NaN/infinity or range failure | Record acquisition/validation outcome separately. Never create zero or a receipt for retained data. Keep partial last-known-good evidence under its original source identity and receipt; current use requires an already accepted retention/freshness policy. |
| Stale observation | Label stale; never advertise as fresh. Withhold current measurement when its accepted policy expires. No humidity TTL is invented here; absent policy cannot grant retention admission. |
| Decodable but unqualified or binding unresolved | Retain candidate and explicit withheld/loss explanation; no newly qualified last-known-good value. Plausibility and legacy visibility cannot bootstrap admission. |
| Controller value becomes nil | Preserve legacy remote eligibility and mapping rules; a qualified remote fallback is a different source observation, not continuity of the controller value. If no eligible qualified remote exists, report fallback loss. Do not substitute the threshold. |
| Remote disconnects, disappears or loses inferred assignment | Remove its eligibility for the affected current zone binding; retain attributable history only. Do not carry its previous scalar into another sensor or zone. Explicit mapping eligibility follows the legacy rules above; semantic qualification may still be missing. |
| Binding, source identity, source epoch, profile, mapping revision or driver generation changes | Fence the old binding and evidence. Requalify the new source/role; do not relabel old last-known-good state or reset its receipt. A source at the same slot is not necessarily the same sensor. |
| Conflicting candidates | Record all candidates and the legacy selection result. Controller non-nil still takes precedence in compatibility output; do not average or select by recency. Conflicting identity/role evidence blocks the proposed binding pending resolution. |
| Cache restore or delayed evaluation | Retain original identity, receipt and clock epoch. A value-only cache cannot reconstruct qualification or age; withhold admission where those are unknown. |

## Consumer equivalence and loss accounting

MCP compatibility and GraphQL parity require the same selected source, value,
unit, native provenance, receipt/freshness, qualification and loss explanation
for corresponding fields. Preserve existing deterministic envelopes. This is an
acceptance requirement; the source file's GraphQL constructions and the semantic
mapping are not proof that both transports already implement the proposed
provenance/dispositions. No adapter implementation is claimed here.

A future projection reports exactly one disposition per requested `(kind,item_id)`.
For the shared humidity definition, aggregate all matching complete FactKeys in
`source_keys` before deciding the item outcome. A projected qualified circuit or
zone fact must not be overwritten as withheld because a different remote source
is absent. Report per-source loss separately. If no matching fact can be admitted,
withhold with the applicable binding, qualification, validity or freshness loss.
An absent threshold mapping is legacy-field/config loss, not a second humidity
measurement disposition. No complete humidity keys are currently established by
this page; the aggregation rule is conditional acceptance for their later binding.

Source-specific equivalence requires equality of qualified sensor identity,
native selector, role/service binding, unit/value and lifecycle context, not just
the scalar. Controller-zone versus remote or circuit equality is not source
equivalence. An explicit legacy fallback can be value-equivalent after qualification
but must expose the source change. Withholding unresolved bindings or the
threshold is intentional semantic loss, not evidence of a transport defect.

## Synthetic acceptance cases

These are manual contract examples, not executed tests, captures or hardware
qualification. A and B are synthetic source identities; z and c are independent
zone/circuit instances. Four-byte examples are LE value payloads only, conditional
on a qualified matching codec and reply correlation. Every admitted outcome below
also requires the unresolved binding and lifecycle evidence above to be supplied.

| Case | Current code distinction | Proposed acceptance / forbidden substitution |
|---|---|---|
| `00 00 00 00` = 0 percent; `00 00 C8 42` = 100 percent | Both finite and non-nil; zone zero prevents remote fallback | Both inclusive endpoints valid; do not treat zero as missing or convert percent to a fraction. |
| `00 00 80 BF` = -1; `00 00 CA 42` = 101 | Float helper accepts both finite values | Reject range; preserve prior attributable evidence without new receipt. Do not fall back merely because a non-nil controller value fails new semantic admission. |
| `00 00 C0 7F` NaN; either infinity; only three value bytes | Helper rejects nonfinite or short values | Invalid input differs from missing, stale and unqualified. Remote NaN is documented as no sensor, never a measured zero. Trailing bytes require shape qualification, not automatic acceptance. |
| Controller A = 40; mapped remote B = 60, including newer B | Non-nil controller wins | Keep compatibility selection A; preserve conflict and B provenance. No averaging to 50 or newest-wins change. |
| Controller nil; explicit mapping 2; connected GG0A instance 1 = 60 | Remote supplies humidity independently of temperature | Conditional equivalence at 60 with exact remote/source role qualified; do not label it a controller sensor. |
| Same mapping; connected=false, connection missing, or slot absent | No eligible fallback | Distinguish known false, unknown and absent; report loss. Prior humidity cannot assert current connected measurement. |
| Binding nil; no assignment or two connected GG0A assignments match z+1 | Inference returns nil | Withhold fallback, retaining candidates; neither recency nor equal values resolves ambiguous assignment. |
| Explicit mapping 2; RR0025 missing | Helper may still select connected GG0A instance 1 | Do not claim legacy requires assignment here. Qualification of the physical zone role remains independently required. |
| Binding nil; unique matching GG0A instance 0 | Inference returns mapping 1, then helper selects lowest connected GG09 instance | Preserve this implementation edge; withhold semantic role if native evidence cannot support the resulting source. No silent direct-GG0A correction. |
| Raw binding 2 changes to 3 | Selected remote slot changes from GG0A instance 1 to 2 | Fence old source/binding, require new qualification and receipt; never relabel old 60 as the new sensor's measurement. |
| Explicit 0, 0x00FF, 0xFFFF or above 0x0100 | No remote fallback under helper rules | Report unavailable binding; integer decoding alone does not qualify other slot values. |
| Circuit c = 40 and zone z = 40 | Separate GG02 RR0022 and GG03 RR0028 reads | Separate sensor/service identities; no alias, even if an associated circuit exists. |
| Source A replaced by B at same tuple; or only epoch/generation changes | A scalar or slot key alone cannot prove continuity | Requalify B; retain A as history, never transfer admission or refresh receipt. |
| Missing/invalid circuit member after a prior valid value; other members succeed | Non-destructive circuit merge preserves prior humidity | Preserve partial last-known-good with original receipt, distinct failed member outcome, and policy-governed current admission. |
| Same valid scalar becomes stale, or qualification becomes unknown | Finite decoding alone cannot express these states | Distinct stale versus unqualified loss; no claim that a successful decode proves either freshness or qualification. |
| Threshold = 60 while every measurement is absent | System config remains distinct | No humidity fact from threshold, including when threshold is zero or 100. |
| One future qualified humidity key projects; another requested source absent | Proposed aggregation, not proven by legacy poller | One definition disposition stays projected with matching `source_keys`; per-source absence cannot overwrite it. |

## Acceptance boundary and remaining evidence

Manual review must check each selector, function claim, transition, loss case,
example and public link against the sources above. Readability is not semantic
validation or runtime proof. No new prose tests, fixtures, validators or schemas
are required or introduced. This contract closes only the documentation slice.

Implementation acceptance still needs reviewed exact humidity FactKey role values
and source/service bindings; family-qualified native sensor/mapping/codec evidence;
accepted lifecycle policy and runtime qualification; per-source retention and
loss handling; and MCP/GraphQL equivalence evidence. Those downstream changes do
not block authoring this bounded contract and do not close gateway #952. Full
committed-head gates, independent review and any separately authorized physical
acceptance remain separate from this page's manual contract review.

[native]: https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md
[mapping]: https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md
[gateway]: https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go
[thermal]: https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go
[fixture]: https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/fixtures/vaillant-semreg-thermal-map-v1.json
