# Cylinder temperature identity and cutover loss

> License: AGPL-3.0. Helianthus migration contract, not a native wire specification.
> Status: proposed, bounded read-only contract for issue #674. Nothing here is
> stable before Helianthus 1.0. No producer or API change is enabled by this page.

This slice concerns only B524 `OP=0x02, GG=0x05, RR=0x0004` and admission of
its individual cylinder instances. It advances the north-south flow tracked by
gateway issue #952; it does not complete that parent. Boiler temperatures,
outdoor/aggregate temperatures and pressure remain outside this contract.
There is no new pack ID, namespace, write route, credential, principal,
authentication or permission check. eeBUS output binding belongs to the driver
repository and is not specified here.

## Sources and evidence status

The public native [B524 register catalog][catalog] is the first authority for
native claims. Its GG=0x05 section calls the group solar-loaded cylinders,
records `f32` and candidate units, and marks **all four rows** as value-matched
only, with false-positive risk and no ebusd coverage. Its range column is a
historical hint, not qualified input-validation metadata. Float byte order is
profile-dependent; the catalog characterizes the VRC720 family as little-endian.
Neither that family statement nor a matching address proves a particular
installation's GG=0x05 field, unit, sensor position or physical topology.

The [semantic mapping][mapping] documents the legacy cylinder surface and FM5
retention/withdrawal rules. The [gateway implementation][gateway] corroborates
current acquisition and publication behavior; it is not independent native
proof. The [Thermal definitions][thermal] establish available pack vocabulary,
not a qualified cylinder binding.

| Claim | Evidence status | Qualification / runtime admission |
| --- | --- | --- |
| Catalog names, candidate units and ranges below exist | **Proven** as documentation contents | Not native qualification |
| Gateway reads GG=0x05 and gates published entries on a non-null decoded temperature | **Proven** as inspected implementation behavior | Not proof of physical presence or current freshness |
| RR=0x0004 measures cylinder water temperature in Celsius; catalog name identifies a bottom sensor | **Hypothesis** from value matching | Withhold semantic qualification until correlated native evidence supports the exact source/profile/instance |
| Applicability, field existence, unit, range and physical identity for an unqualified profile or instance | **Unknown** | Fail closed; no inferred Celsius quantity or cylinder |

Evidence status, qualification and runtime admission are separate axes. A
documented hypothesis stays a hypothesis even when bytes decode. A matching
Thermal field cannot strengthen it. No current SemReg publication is claimed.

## Finite selector and consumer inventory

Every scoped row uses `PB=0xB5, SB=0x24, OP=0x02, GG=0x05` and the exact
native `II`. The current `readCylinderSnapshots()` loop visits `II=0x00` and
`II=0x01`; this is an implementation bound, not a proven device count or a
license to admit all instances. Do not substitute OP=0x06.

| RR | Catalog name / candidate decoding | Current legacy consumer | Proposed disposition |
| --- | --- | --- | --- |
| `0x0004` | `solar_cylinder_bottom_temperature`; `f32`, candidate °C, historical hint -10..110 | `cylinder_temperature` → `cylinders[].temperatureC`; `[].index` derives from II | Only presence/measurement candidate in this slice; qualification and live per-instance evidence required |
| `0x0001` | `solar_cylinder_temperature_limit_maximum`; `f32`, candidate °C, hint 0..99 | `cylinders[].maxSetpointC` | Context only; cannot create an instance; no Thermal setpoint or write projection |
| `0x0002` | `solar_cylinder_start_temperature_difference_limit`; `f32`, candidate K, hint 2..25 | `cylinders[].chargeHysteresisC` | Context only; retain native identity and unit uncertainty, do not silently reinterpret as Celsius |
| `0x0003` | `solar_cylinder_stop_temperature_difference_limit`; `f32`, candidate K, hint 1..20 | `cylinders[].chargeOffsetC` | Context only; legacy name differs from catalog meaning; no new semantic mapping |

These legacy paths feed `ebus.v1.semantic.cylinders.get` and the gateway's
`graphql.CylinderStatus` objects through `publishFM5Semantic()`. Publication
sorts instances by native II. `refreshFM5Semantic()` supplies the FM5 verdict;
`applyFM5Acquisition()` and `mergeCylinderSnapshotNonDestructive()` retain
previous non-null members during partial acquisition. `readAny` can be true
from configuration reads alone; it is not per-instance temperature admission.
`hasLiveCylinderEvidence()` checks a temperature pointer, including a retained
one; its name is not proof that every publication contains a new live sample.

Distinct legacy sources remain distinct: DHW `OP=0x02, GG=0x01, RR=0x0005`
feeds DHW current temperature (and the boiler DHW mirror); solar-loop values
belong to GG=0x04. System GG=0x00 RR=0x009D/0x009E already have separate top
and bottom fields. None substitutes for GG=0x05, establishes a sensor position
here, or authorizes additional top/bottom fields. Never average these sensors
into a unified temperature or use one source to repair another's absence.

## Proposed observation identity and decoding boundary

The following are future binding obligations, not a new serialized schema.
Keep the full observation beside its interpretation:

- Native selector: PB/SB, opcode, group, instance and register; request source
  and destination, reply direction, complete selector/payload bytes and framing
  outcome. Separate requested identity from returned identity where present;
  a value-only reply requires acquisition correlation, not an invented echo.
- Source binding: opaque source identity and epoch, controller family/profile
  with its actual revision evidence, registry/driver generation, semantic
  mapping revision, evidence reference and coherent FM5 evidence revision.
  Unknown profile/revision is recorded as unknown, not filled from a neighbor.
- Receipt: original wall-clock receipt and monotonic receipt with its clock
  epoch; evaluation time is a separate input. Cache reads, projection, retries
  and retention do not replace receipt or fabricate a new observation.
- Separate asset/service binding and per-instance physical evidence from
  display index. II alone is not a globally unique cylinder identity. A source,
  profile, revision or generation change cannot inherit qualification or merge
  retained values into the new binding. Preserve old evidence as history.

Current `decodeB524Float32FromRaw()` reads the first four bytes little-endian,
rejects fewer than four bytes and rejects NaN/infinities. It accepts exact
zero, finite values outside the catalog hint, and extra bytes after the first
four. `readB524Value()` uses scheduler/cache age policy; its success is not an
independent new receipt. These are implementation observations only.

Proposed admission requires a correlated successful read, coherent FM5
context, qualified profile-specific encoding and unit, and fresh decodable
RR=0x0004 evidence for that same instance. Require exactly four **value** bytes
for the qualified f32 layout, after validated framing/status/selector removal;
do not mistake telegram length for value width or silently truncate extensions.
Reject non-finite input. Apply both the existing pack domain, if mapped, and
independently qualified native validation limits; never promote the catalog's
-10..110 hint into an admission rule. An unresolved native validation policy
is a cutover gap. Zero is a value, not absence, subject to those same gates.
Unknown unit, existence or encoding withholds the quantity while preserving
raw evidence. No enum or sentinel meaning is invented here.

## Proposed Thermal disposition and loss

The existing `helianthus.pack.thermal` defines
`thermal.measurement.water_temperature`, unit `unit.celsius`, dimension
`thermal.dimension.temperature`, and numeric domain -100..200. This is a
**Hypothesis** candidate for RR=0x0004 only after its water-temperature meaning
and unit are qualified. The pack offers system, zone, circuit, DHW and
ventilation services; it does not define a cylinder service. Choosing
`thermal.service.dhw` / `thermal.dimension.dhw` merely from a tank label would
collapse a distinct GG=0x05 identity into GG=0x01 semantics.

This contract therefore **withholds a complete Thermal fact/service/FactKey
binding**. No service, temperature-dimension value or cylinder dimension is
invented. The candidate field/dimension alone is insufficient. Later work must
justify an existing service and collision-free per-instance temperature key
with native and topology evidence, or continue withholding. It must preserve
source/profile/revision and II outside any display label. No changes to pack
definitions are implied.

Loss accounting must expose that withholding, unknown native unit/existence,
unqualified identity, rejected width/value, stale observation, transient
acquisition and coherent structural withdrawal as distinct outcomes using the
accepted projection envelope. These are conceptual distinctions, not new enum
tokens. Legacy configuration companions have no new Thermal projection. Native
bytes and candidate interpretation remain inspectable even when projection is
withheld; a missing quantity must never serialize as zero.

## Proposed retention and transport equivalence

Preserve the [existing FM5 distinction][mapping]: fresh coherent `ABSENT` or
known non-interpretable configuration withdraws the structural instance set;
transient acquisition degradation retains only the last coherent set with the
provider-owned reason/revision and unchanged last coherent mode. With no prior
instance, configuration-only or failed reads leave the array empty. An empty
array alone does not classify absence. No candidate adds an instance until its
own RR=0x0004 meets admission. Partial updates preserve unaffected admitted
instances and members; one missing instance never erases a healthy sibling.

Future freshness evaluation uses original monotonic receipt plus an explicit
qualified age policy and evaluation context. No duration is invented here.
Expired/unknown-age evidence can remain last-known-good history, but cannot
be presented as current, establish a new cylinder or acquire qualification.
Cache restore cannot refresh receipt or revive admission. A newer accepted
same-binding sample can recover freshness; foreign-source evidence cannot.
FM5 structural freshness and per-instance measurement freshness are separate.

Future gateway and HA consumers must preserve existing MCP tool names and
envelopes. MCP and ordinary GraphQL must serialize the same detached,
provider-owned result at an equivalent read/evaluation point: native II and
ordering, present zero, absent value, retained/current distinction, original
receipt, qualification, withheld projection and FM5 mode/reason/revision must
agree. Surface spelling or optional-field conventions must not alter meaning.
Do not recalculate FM5 verdicts from empty arrays, independently average
sensors, or make reads perform acquisition/writes. Existing cylinder objects
are not claimed to expose all this provenance today; the accepted shared
snapshot/projection contract and compatibility review are later integration
seams, not new fields added by this page.

## Synthetic before/after cases

These are manual contract examples, not captures, fixtures, executable tests
or runtime qualification. Let A and B be synthetic sources, i and j distinct
native instances, L an optional last coherent value for A/i, and R its original
receipt. All value bytes below are payload bytes after framing removal. The
legacy column describes the inspected acquisition/decoder/merge path, not
uninspected transport serializers. The proposed column assumes coherent
context and qualified layout/unit/age policy unless the row removes one gate.
The complete Thermal binding remains withheld in **every** case below.

| Input / transition | Before: current implementation evidence | After: proposed contract and intended difference |
| --- | --- | --- |
| A/i RR0004 `00 00 00 00` | Decodes to non-null 0; can pass pointer presence check | Admit zero when all gates hold; preserve 0 on both surfaces, never treat as missing |
| A/i has no RR0004; only RR0001..0003 reply | New instance has nil temperature and is filtered; prior non-null temperature can survive merge | No new cylinder; retain L with R and explicit non-current status when appropriate, never use configuration as new measurement evidence |
| A/i NaN, +infinity or -infinity | Decoder returns nil; prior member can survive | Reject replacement and retain L/R without renewing receipt; expose acquisition/value loss |
| A/i finite 250, correctly encoded | Decoder accepts; no numeric bounds in this helper | Reject as outside candidate pack domain; native qualified bounds may be stricter. No clamping or catalog-hint validation |
| A/i RR0004 three value bytes | Decoder returns nil | Reject width; preserve raw reply and L/R if present, no new instance |
| A/i RR0004 `00 00 00 00 00` | Decoder accepts first four bytes as 0 if read path supplies them | Reject unqualified extra value byte; intended stricter width admission, no truncation |
| A/i L passes its age limit without new receipt | FM5 has evidence-staleness handling; cylinder pointer alone has no per-value age proof | Retain L/R as history, withhold current quantity; preserve mode on transient degradation |
| Only II changes i → j | Reader uses separate map entries for its two polled instances | Never refresh i with j; j needs its own qualification and fresh RR0004; i retains its own receipt |
| Only source changes A → B with same II | Watch key contains target/opcode/group/instance/register; snapshot map itself is keyed by II | Do not reuse A's qualification/value for B; retain A as history, withhold B pending its own admission |
| Only profile/revision/generation changes | FM5 generation checks can reject incoherent acquisition; cylinder member does not itself carry this full identity | Fence old observation; no automatic qualification transfer or new receipt |
| Transient failure after L | Existing FM5 transient reason preserves coherent set and mode | Preserve L/R with the same provider-owned reason/revision; loss is degradation, not proven absence |
| Fresh coherent ABSENT or non-interpretable configuration after L | Structural withdrawal clears instances | Withdraw current set; historical evidence remains separate, no ghost cylinder from configuration |
| Same A/i recovers with new valid RR0004 and coherent evidence | Non-null merge replaces temperature when acquisition is accepted | Re-admit only on new valid receipt and all gates; preserve siblings and recover current status, never from replay of L |
| Unknown native existence or unit for A/i | Legacy candidate name and Celsius-shaped field can still exist | Preserve raw evidence and explicitly withhold physical admission/quantity; no guessed unit, bottom/top split or DHW fallback |

## Cutover prerequisites and remaining work

Manual source review supports the current-behavior descriptions above only.
The proposed stricter width, per-observation identity/freshness, value-domain
handling and loss accounting require later implementation and validation.
Before cutover, gateway work must cover `readCylinderSnapshots()`, acquisition
correlation/decoder boundaries, coherent FM5 commit, non-destructive merge,
cache restoration and projection from one shared result. HA work must inventory
actual cylinder entities, unique IDs and availability/retention handling;
no HA implementation was supplied as evidence and none is asserted here.

Required evidence includes publishable correlated native request/reply bytes,
source/destination and direction, profile/revision and family context, exact
instance, physical correlation and conditions sufficient to falsify field
existence, unit, position, encoding and range. Retain raw evidence beside its
interpretation, with private installation data removed. Matching pack metadata
or legacy labels alone do not qualify any of these claims.

Later checks must independently exercise every identity component, bootstrap,
partial sibling retention, stale/cache transitions, structural withdrawal,
recovery, width/value rejection and MCP/GraphQL parity. They must resolve the
service/FactKey gap before claiming SemReg publication. This page supplies no
profile admission, transport conformance, hardware acceptance, passive/live
smoke result or parent closure. Full committed-head gates and independent
review remain separate acceptance work.

[catalog]: https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md
[mapping]: https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md
[gateway]: https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go
[thermal]: https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go
