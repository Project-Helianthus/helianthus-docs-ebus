# DHW target and limit role preservation

> Proposed gateway-to-SemReg migration acceptance contract; AGPL-3.0.
> This is a bounded read projection for requested DHW temperature, its limits
> and its legacy boiler presentation. It is not an implemented cutover or a
> universal device definition. Nothing here establishes stability before
> Helianthus 1.0.

This slice advances [gateway #952](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/952)
and [docs #701](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/701).
Observed DHW temperature and operating mode are excluded. This contract does
not replace the broad Matter source inventory or earlier temperature contracts.

## Evidence and authority

The following public sources identify the reviewed sections and functions.
Links use the public main branch; they are navigation references, not immutable
execution evidence. Code establishes implementation behavior, never native
source equivalence by itself.

- [Native B524 catalog](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md):
  “Table Legend”, “Group Topology”, “GG=0x01 — Native Domestic Hot Water”,
  “GG=0x00 — System” rows RR=0x0046 and RR=0x00FC, and
  “GG=0x05 — Solar Loaded Cylinder”. This is the native contract prerequisite.
  Its constraint column is a historical short-probe hint, not a universal
  operating domain; matching complete OP01/OP07 descriptions are required
  before using such hints to validate edits. Byte order is profile-qualified.
- [Legacy mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md):
  `ebus.v1.semantic.dhw.get`, `ebus.v1.semantic.boiler_status.get`,
  `ebus.v1.semantic.cylinders.get`, and the system mapping.
- [Gateway implementation](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go):
  `refreshDHWSlowConfig`, `readDhwFloat`, `readB524Float32LE`,
  `expireDHWIfStaleLocked`, `publishDHW`, `refreshBoilerStatusTier`,
  `mergeBoilerDHWFieldsFromSnapshot`, `refreshBoilerStatusB509`,
  `mergeBoilerSnapshotNonDestructive`, and `publishBoilerStatus`.
- [Existing thermal mapping fixture](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/fixtures/vaillant-semreg-thermal-map-v1.json):
  `scope`, `qualification`, `mappings`, `lifecycle`, and `nonclaims`.
  It maps system temperature fields, contains no DHW target row, and records
  an evidence gap with runtime qualification disallowed. It does not qualify
  this proposed DHW binding.
- [Thermal pack](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go):
  `fields`, `services`, `capabilities`, `operations`, and `Metadata`.
- [SemReg types](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/types.go):
  `FactKey`, `Dimension`, `Times`, `Quality`;
  [projection types](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/projection/types.go):
  `RequestedItem`, `ProjectionDisposition`, `LossDetail`, `ProjectionReport`.

**Proven** below means supported within the stated public source scope, not
qualified on every controller. **Hypothesis** marks proposed equivalence or a
candidate interpretation. **Unknown** marks absent native evidence or an
unresolved binding. These evidence labels remain separate from SemReg
`qualification`, acquisition success, validity, freshness, promotion and
admission. A readable float or matching name does not qualify a source.

## Native roles and current behavior

| Role | Native identity and unit | Current behavior and evidence boundary |
|---|---|---|
| Controller requested DHW target | PB/SB B5/24; `(OP=0x02, GG=0x01, II=0x00, RR=0x0004)`; catalog `dhw_temperature_setpoint`, f32 °C | Proven catalog assignment within the documented controller families. `refreshDHWSlowConfig` reads this selector via `readDhwFloat`; `publishDHW` exposes `Config.TargetTempC`, corresponding to MCP `target_temp_c`. The native read role is a requested target, not an observed temperature. |
| Target range context | Same target selector; historical hint 35..70 °C | These are not two sampled facts. No separate native minimum/maximum target selector or complete description is established by the supplied DHW row. Actual per-source limits remain Unknown until qualified. Do not install 35/70 as global defaults. |
| Boiler target mirror | Same controller selector and original acquisition; no new wire source | `mergeBoilerDHWFieldsFromSnapshot` clones non-nil `p.dhw.TargetTempC` into `DhwTargetTemperatureC`; `publishBoilerStatus` exposes `state.dhwTargetTemperatureC`. This is Proven code behavior, not proof of a boiler-owned requested target. |
| Boiler-direct desired temperature candidate | B509 register `0xEA03`, boiler target; decoder DATA2c in code | `refreshBoilerStatusB509` medium tier populates `DhwTempDesiredC`, published as `state.dhwTempDesiredC`. Proven implementation assignment only; native requested-versus-effective role, unit semantics, domain and equivalence to controller RR=0x0004 remain Unknown in this evidence set. Withhold its canonical target binding. |
| DHW flow ceiling | B524 `(0x02, 0x00, 0x00, 0x0046)`, f32 °C | Catalog names a DHW **flow** maximum; legacy system `config.hwc_max_flow_temp_desired`. Its TSP note 15..80 is not a tank-target minimum/maximum. Preserve separately as context, not `thermal.setpoint.dhw_temperature`. |
| Other apparent maximums | B524 `(0x02, 0x00, 0x00, 0x00FC)` f32 °C; `(0x02, 0x05, cylinder instance, 0x0001)` f32 °C | RR=0x00FC is described as likely maximum heat-pump flow temperature. GG=0x05 has CSV-only naming with false-positive risk; legacy `maxSetpointC` does not establish requested tapping-target identity. Hypothesis/context only; no substitution. |
| Boiler configuration ceiling | B509 boiler configuration field `flowsetHwcMaxC`; implementation references: `refreshBoilerStatusB509` and `readB509BoilerConfigFloat` | Proven implementation behavior only; native controller target-limit applicability remains Unknown. Preserve boiler configuration identity. Applying this ceiling to a controller target requires qualified native evidence of that relationship. |

For controller reads, preserve initiator and controller destination binding,
PB/SB, opcode, group, instance, register, request/reply direction, raw reply,
codec/profile, decoded value and unit, evidence reference and acquisition
identity. Requests go initiator-to-controller; values return
controller-to-initiator. Keep family and firmware qualification context when
known; unknown context stays unknown. No fixed destination address establishes
byte order. OP=0x06/GG=0x01 is a distinct namespace and is never a fallback for
OP=0x02/GG=0x01. The catalog's singleton II=0x00 does not authorize II=0x01.

`readB524Float32LE` accepts at least four bytes, uses the first four, rejects
NaN/infinity and does not enforce the catalog hint. This describes current
code, not a newly qualified native reply-width rule. Partial successful DHW
refreshes merge attempted fields; the snapshot-level stale expiry can clear
`p.dhw`. `mergeBoilerDHWFieldsFromSnapshot` itself checks neither target age nor
controller ownership. Boiler partial merges retain non-nil prior fields.
Consequently a retained boiler number alone cannot prove a fresh target.
Do not borrow the age check for the system-flow mirror as evidence that the
DHW target mirror has the same check.

## Proposed canonical binding and explicit losses

For a qualified controller requested-target source only, propose:

- `FactKey.PackID = helianthus.pack.thermal`, `PackVersion = 1.0.0`
  (the existing pack reference), `FactID = thermal.setpoint.dhw_temperature`.
- Dimensions: `thermal.dimension.temperature` with text value
  `temperature:dhw_requested`, and `thermal.dimension.dhw` with a stable,
  source-bound DHW service identity such as synthetic `dhw:alpha`.
- Service definition `thermal.service.dhw`, instance bound to that same DHW
  identity; read capability `thermal.capability.read.dhw` only when admitted.
  Values are quantities in `unit.celsius`, using exact decimal conversion of
  the decoded native value without silent rounding or clamping.

This is a **Hypothesis** for migration acceptance, not a new definition or a
claim that these sources are qualified today. The current pack can express a
DHW requested temperature, with numeric bounds -50..150 °C; those pack bounds
are representation limits, not equipment safety limits. The source binding
must establish requested role, unit, profile, service owner, native domain and
freshness. Absent that evidence, retain a candidate with `qualification`
`candidate`/`unknown` as appropriate and withhold consumer admission. Do not
relabel it `qualified` because the pack accepts the number.

The current pack has no separate DHW minimum/maximum field definitions. Retain
qualified bounds, their native selector or description association, unit,
applicability and evidence as constraints/context on the source binding.
Withhold a standalone bound fact as unrepresentable; do not invent a universal
limit definition, use a measurement field, or emit extra target facts. A limit
without a target remains useful context but cannot synthesize a target.

| Consumer request | Proposed disposition and loss accounting |
|---|---|
| Controller target to same qualified DHW service | `exact` only if value, requested role, service identity, unit, precision and source provenance survive. Otherwise `withheld`; state the specific identity, provenance, range or policy loss. |
| Legacy boiler mirror backed by that same accepted controller observation | Compatibility presentation may retain the same value and original provenance, explicitly labelled controller mirror. It is not another boiler fact or independent corroboration. Recasting it as boiler-owned loses identity/provenance and is withheld. |
| Boiler-direct candidate | `withheld` pending native role and source-specific equivalence evidence, even when numerically equal to the mirror. Preserve both native candidates. |
| Standalone min/max target fact | `unrepresentable` under the existing pack. Preserve the constraint/context; disclose range/identity loss if a consumer cannot carry it. No invented definition ID. |
| DHW write operation/capability | No DHW canonical operation is defined by this pack. The existing `set_temperature` capability belongs to zone service; it cannot be reused for DHW. Report unsupported operation/capability when requested; readability and candidate write templates do not establish support. |

For canonical projection requests, emit exactly one disposition per requested
`(kind,item_id)` using the existing projection envelope, source keys and loss
details. Aggregate per-source decisions before constructing this disposition;
per-source absence must not overwrite an already projected shared definition.
For example, a present alpha target and absent beta target still yield one
`(fact,thermal.setpoint.dhw_temperature)` disposition with the accepted alpha
key, plus explicit beta absence in source-specific context. Never emit duplicate
dispositions or turn beta absence into a global unsupported result. If the
consumer cannot preserve required service identity or represent the partial
result, withhold the aggregate with explicit identity/policy loss instead.
Bounds with no canonical definition are described as contextual losses, not
fabricated requested items. Preserve deterministic ordering and existing
snapshot/revision identity; a projection evaluation never changes receipt time.

MCP and GraphQL must expose equivalent accepted values, owner, availability and
loss/withholding interpretation while retaining their compatibility fields.
No consumer silently converts a missing target to zero or a limit to a target.
No eeBUS output binding is defined here; that binding remains driver-owned.
Existing trust/admission checks and G5 D1-D5/O8 are unchanged. No new principal,
credential or permission gate is introduced; authentication/authorization
remain Helianthus 0.11 work.

## Proposed transitions and synthetic acceptance cases

These are manual contract cases, not executed tests or native observations.
Alpha/beta identify synthetic services; values carry no capture metadata.
Every case preserves raw evidence separately from the canonical interpretation.

| Case | Required result |
|---|---|
| Qualified controller target 50 °C, qualified source domain 35..70 | Project requested target 50 for alpha, not a measurement; keep bounds as context. Mirror equivalence holds only for this same observation, service and owner. |
| Exact zero where native domain permits it | Conditional synthetic source whose complete qualified domain includes 0: decode `00 00 00 00` as exactly 0 °C and admit if all other checks pass. The supplied controller hint does not prove that zero is allowed there. |
| Zero against a qualified 35..70 native domain | 0 is pack-representable but native-invalid; retain raw zero with failed validity and withhold. Never reinterpret as off, missing or a default. |
| Native versus pack range | 80 with qualified native domain 35..70 is native-invalid despite pack acceptance. A hypothetical qualified native domain permitting 160 cannot make 160 representable in the pack: withhold with range loss, retain native value; do not clamp to 150. These domains are synthetic, not discovered equipment limits. |
| Missing target, present maximum 65 | Preserve maximum context and any prior same-owner last-known-good target with its original age; no current target is synthesized from 65 or a fixed default. |
| Missing, invalid, stale, unqualified | Missing reply changes acquisition status, malformed/nonfinite reply changes validity, aged receipt changes freshness, absent qualification blocks admission. They remain distinct; none becomes numeric zero or Boolean false. Last-known-good retention does not renew freshness. |
| Valid false versus absence | This target is a quantity: a Boolean false payload is a type mismatch and is withheld, not converted to 0 °C. Where Boolean presence context is natively defined, a valid false/zero is preserved; RR=0x0001 exact two-byte zero means not-present, unlike wrong width or missing reply (unknown). |
| Two services alpha and beta, 50 and 55 | Distinct `thermal.dimension.dhw` values and service bindings produce distinct keys despite a shared FactID. Do not infer a second GG=0x01 instance; beta requires its own qualified native source. If beta is absent, alpha still projects under the shared definition disposition. |
| Fresh controller target 50, stale mirror 55 | Admit only the qualified fresh controller observation; retain stale mirror evidence without using it for a new fact or extending its age. A legacy cache value alone is insufficient. |
| Controller target 50, boiler-direct desired 55 | Preserve both candidates and their native identities; no averaging or last-arrival winner. The boiler binding remains withheld. If two qualified candidates claim the same service/role without a qualified owner rule, withhold that contested projection and disclose conflict. |
| Equal values from distinct sources | Numeric equality does not prove equivalence. Controller target 50 and boiler-direct 50 stay distinct until native role, units, service and owner equivalence are qualified. |
| Source replacement or owner change | End the old binding; retain its history under the old owner. Start the replacement unqualified until its own evidence passes. Do not copy target, limits, qualification or receipt history into the new owner, even if the service label and number match. |
| Partial refresh or recovery | A failed limit or target read cannot erase unrelated accepted fields. Retain partial last-known-good state by source, with degraded acquisition/freshness visible; resume admission only after valid, fresh, qualified evidence. No copied history or global fallback. |

The identity review covers pack ID/version, FactID, both dimension IDs and
values, service binding, controller/source owner, PB/SB, opcode, group,
instance, register, codec/profile and receipt epoch/sequence. Collapsing any
of these can misattribute a target or admit stale/foreign evidence. This is a
reasoned review checklist, not an executed mutation claim.

## Acceptance boundary

Manual review must trace every selector, unit, legacy function, proposed
transition, loss and synthetic case to the sources above. Native limit
qualification, boiler-direct equivalence and owner-specific freshness evidence
remain missing; the contract deliberately withholds those mappings. No live
write, hardware acceptance or downstream implementation is required to author
this slice. Independent review and applicable committed implementation gates
remain necessary for actual cutover. Document readability proves neither
semantic validity nor runtime behavior, and this contract closes no parent.
