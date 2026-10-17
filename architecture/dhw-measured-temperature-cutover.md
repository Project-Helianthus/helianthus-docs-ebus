# DHW measured-temperature cutover contract

Status: proposed application migration contract, AGPL-3.0. This page is the
bounded contract slice for docs-ebus #672, advancing
[gateway #952](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/952).
It neither implements cutover nor closes the parent. Nothing here is stable
before Helianthus 1.0. All new admission and projection behavior below is future
work; no current SemReg publication is claimed.

## Sources and evidence levels

The public native contract comes first:

- [Native B524 register catalog](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md):
  Table Legend, Group Topology and “GG=0x01 — Native Domestic Hot Water”
  establish the documented selector, representation, unit and presence rule.
  Float byte order remains profile-dependent. Historical range hints are not
  qualified validation bounds.
- [Existing semantic mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md):
  the DHW and boiler-status sections inventory legacy consumers; the system
  section distinguishes cylinder-top/bottom readings and bivalence bounds.
- [Gateway semantic implementation](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go):
  `localDHW`, `dhwInstance`, `refreshDHW`, `readDhwFloat`,
  `readB524Float32LE`, `parseB524ReadPayload`, `matchesB524ReplyInstance`,
  `expireDHWIfStaleLocked`, `publishDHW` and
  `mergeBoilerDHWFieldsFromSnapshot` corroborate implementation behavior only.
- [Existing Thermal definitions](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go):
  `fields`, `services`, `dimensions` and `Metadata` establish available pack
  vocabulary, not native DHW identity or qualified publication.

**Proven** here means established by the cited source at its stated layer:
documented native contract, implementation behavior, or pack vocabulary.
**Hypothesis** labels the proposed DHW-to-Thermal binding. **Unknown** covers
missing profile-specific evidence and uninspected consumer behavior. These
labels are independent of device-family qualification and runtime admission:
a documented selector and compatible field do not admit an observation.
No raw capture or device qualification is supplied by this page.

## Finite selector and consumer inventory

All entries are B5/24 reads. Tuples are `(OP, GG, II, RR)`; only the first row
is an in-scope measured-temperature input. Controller-family applicability
must remain attached to the native contract, never inferred from a destination
address. OP02 and OP06 namespaces remain separate.

| Tuple | Documented meaning and representation | Current consumer / disposition |
| --- | --- | --- |
| `(0x02, 0x01, 0x00, 0x0005)` | `dhw_temperature`, f32, °C; community name `HwcStorageTemp`; gated by RR0001 | `dhw_current_temp` → `CurrentTempC` → GraphQL `DhwStatus.State.CurrentTempC`; documented MCP `ebus.v1.semantic.dhw.get` `current_temp_c`; controller mirror in boiler status `state.dhwTemperatureC`. Sole measured input in this contract. |
| `(0x02, 0x01, 0x00, 0x0001)` | Exact two-byte UIN nonzero establishes family-qualified presence; zero means not present; malformed/unmatched means unknown | Admission evidence only. The candidate circuit-type enum is not established by the presence test. No temperature fact. |
| `(0x02, 0x01, 0x00, 0x0004)` | `dhw_temperature_setpoint`, f32, °C | Legacy `target_temp_c` / boiler `dhwTargetTemperatureC`; excluded target, never a replacement for missing measured temperature. |
| `(0x02, 0x01, 0x00, 0x0008)` | `dhw_flow_temperature_setpoint`, f32, °C | Excluded flow target; no new read or projection proposed. |
| `(0x02, 0x01, 0x00, 0x0003)` | Operating mode, u16 | Legacy operating-mode derivation; excluded enum. |
| `(0x02, 0x01, 0x00, 0x000D)` | Native catalog says special-function mode, u8; gateway reads it through `readDhwUint16` | Legacy `state`/special-function derivation; width discrepancy remains unresolved and cannot establish charging state from temperature. |
| `(0x02, 0x01, 0x00, 0x000F)` | Special-function state, u16; candidate loading interpretation remains unconfirmed | Excluded charging/state semantics; do not infer enum meanings. |
| `(0x02, 0x00, 0x00, 0x0001)` | DHW outdoor bivalence temperature limit | Excluded system configuration; derived bivalence bound is not a measured register value. |
| `(0x02, 0x00, 0x00, 0x009D/0x009E)` | DHW cylinder top/bottom temperatures | Separate system consumers, excluded; neither is an alias or fallback for GG01 RR0005. |
| `(0x02, 0x05, II, 0x0004)` | Solar-loaded cylinder temperature in a distinct group | Separate cylinder consumer, excluded; instance qualification is not inherited from GG01. |

The supplied gateway source reads RR0005 with OP02/GG01/II00 and explicitly
does not fall back to OP06/GG01. `publishDHW` sends the merged object through
the provider and update hub. `mergeBoilerDHWFieldsFromSnapshot` copies a
non-null current temperature into the boiler snapshot: this is a controller
mirror, not an independent boiler sensor. The semantic mapping documents MCP
field names; the cited poller alone does not prove all MCP adapters or HA
consumer behavior. Those consumer paths still need later inspection.

## Proposed observation boundary

This is a logical input contract, not a new artifact schema, API route or pack
ID. Before decoding, preserve the raw request/reply alongside:

- PB/SB, read direction/operation, requested `(opcode, group, instance,
  register)` and the actual returned selector/header when present;
- initiating source and responding target, transport/provenance kind, admitted
  controller asset and family/profile identity, profile revision and decoder
  revision; address equality alone is insufficient;
- a receipt identifier and receipt ordering, original observation/receipt age,
  and the receipt used for the last accepted value. Re-reading cache must not
  create a new observation or reset freshness;
- exact value bytes and width, reply outcome, decoded value/unit when known,
  presence evidence and its correlation, qualification decision and rejection
  reason. Unknown metadata stays unknown, never synthesized as proof.

The admission key includes every selector component and source/profile/revision
binding. Receipt identifies an individual observation within that key, not a
replacement identity. Reject unmatched, duplicate-as-new, older or ambiguously
correlated input without replacing a newer accepted receipt. A source, profile
or revision change requires a separately qualified binding; retained history
must not be relabeled as evidence for it. Preserve the rejected native evidence
for diagnosis without exposing private identifiers in public examples.

The current reply parser accepts both headers with and without an instance;
`matchesB524ReplyInstance` also accepts requested instance plus one. This is
implementation compatibility, not proof that II01 is another DHW instance.
Future admission must preserve raw versus normalized identity and require
profile-qualified correlation for any compatible header normalization. It must
not turn an unrelated II01/source observation into II00 evidence. The exact
correlation/normalization proof is **Unknown** here; ambiguous replies withhold
the new projection rather than changing the existing parser in this ticket.

## Decoding and proposed Thermal binding

For a qualified little-endian f32 profile, decode exactly four value bytes
after validated framing, preserve finite exact zero, and report °C as
`unit.celsius`. Other byte orders require independent native qualification;
do not try both and select the plausible number. Empty, short, over-length,
non-finite and unsupported-profile observations cannot yield a new fact.
This exact-width rule is proposed: the current helper accepts at least four
bytes and decodes the first four; it rejects NaN and infinities but performs
no numeric range check.

Candidate binding, **Hypothesis**, within existing `helianthus.pack.thermal`:

| Component | Existing vocabulary / proposed use |
| --- | --- |
| Field | `thermal.measurement.water_temperature` |
| Quantity unit and dimension | `unit.celsius`, `thermal.dimension.temperature` |
| Service and service key dimension | `thermal.service.dhw`, `thermal.dimension.dhw` |
| Read capability | Existing `thermal.capability.read.dhw`, subject to later binding qualification |
| Concrete fact/service identity | **Withheld** until the qualified controller/DHW binding fixes the exact fact-key dimensions and values and proves collision-free identity. No new dimension value is invented here. |

The existing water-temperature field permits -100 through 200 °C. These are
pack representability limits, not sensor qualification. The native RR0005
`0..99` entry is a historical short-probe hint, not a universal physical bound.
Proposed admission rejects values outside the pack interval and any narrower
independently qualified profile interval; no clamping or sentinel-to-zero
conversion. A profile without sufficient unit/decoding/validity evidence stays
withheld even when its number lies inside both printed ranges. No target
setpoint field, action/charging enum, writable capability or output binding
is inferred. Any eeBUS output binding belongs in the driver repository.

## Retention, freshness and equivalent projections

Current behavior: a valid `readDhwFloat` result includes zero; a failed read
returns nil. `refreshDHW` merges successful fields and may succeed because
special-function data succeeded while current temperature did not. It then
updates a DHW-wide receipt time. Cache-source publication expires the whole
DHW object at age greater than or equal to the configured TTL, provided the
TTL is positive and the last update exists. Otherwise partial last-known
values survive. Successful fallback hydration can be classified live; that
classification alone does not prove native selector provenance.

Proposed measured-field behavior:

1. With no accepted value, absence/rejection keeps the measured fact absent.
2. A new qualified receipt updates only this measurement, its native evidence
   and its own freshness. Unrelated successful DHW fields cannot rejuvenate it.
3. Failure or an unknown presence result retains its last-known-good value and
   original receipt, marks the current attempt unavailable/unverified and lets
   age advance. It does not erase other valid DHW fields.
4. At measured-field expiry, retain historical evidence but withhold the fresh
   measured projection. A qualified not-present result also withholds active
   publication; unknown is not proof of absence. Neither outcome resets age.
5. A later valid, newer receipt for the admitted identity recovers publication;
   profile loss/change cannot recover through a cached value or a foreign key.

Per-field freshness policy, TTL selection, and representation of retained stale
values in existing envelopes remain implementation decisions requiring tests
and review before cutover. This page does not silently replace the current
whole-object TTL lifecycle or specify HA entity removal.

MCP and GraphQL must derive from the same accepted snapshot/receipt and agree
on value, Celsius unit, absence, retained-versus-fresh classification and
recovery. Preserve MCP method names and deterministic envelopes, metadata and
error conventions. Do not change a retained value's observation timestamp or
hash merely because it was served again. Where the current schemas cannot
express per-field provenance/freshness, withhold new publication/cutover until
an explicit compatible representation is reviewed; do not label an old
measurement live because another field advanced the stream. Null versus
omission must follow each existing schema while representing the same absence.
The boiler mirror must retain controller provenance and the same freshness,
not mint a second independent fact. HA must consume the same qualified value
without truthiness filters that drop zero or target/charging substitutions.

## Synthetic before/after cases

These are review examples, not captures, tests or runtime results. Value bytes
below are only the extracted value, not a complete reply. Unless varied, assume
a hypothetically qualified little-endian profile, present RR0001, matching
identity and newer receipt. `L=45 °C` denotes previously accepted local state;
`T` is a later-agreed positive field TTL, not a new default. “Current” describes
the cited direct helper/poller; fallback outcomes are not assumed.

| Input / prior state | Current implementation expectation | Proposed result / intended difference |
| --- | --- | --- |
| `00 00 00 00`, no prior value | Helper returns valid 0 | Accept 0 °C if qualified; never treat numeric zero as absent. Actual SemReg fact still withheld pending concrete binding. |
| No value, no prior value | Helper fails; fallback may be attempted | No measured value/fact; no fabricated zero. |
| No value, `L` | Failed temperature read can leave merged value intact | Retain L and its receipt; no freshness reset from another field or cache. |
| `00 00 C0 7F` (NaN), or `00 00 80 7F` (+infinity), `L` | Helper rejects; no new temperature | Retain L, record invalid attempt; withhold fresh replacement. No native sentinel meaning inferred. |
| Finite 201 °C or -101 °C, `L` | Helper accepts finite f32; no range validation there | Reject outside pack limits; retain L. Native profile bounds still require evidence. |
| Three bytes `00 00 34`, `L` | Helper rejects short value | Retain L; malformed evidence cannot refresh receipt. |
| Five bytes `00 00 34 42 00`, `L` | Helper decodes first four as 45 °C | Reject over-length value; retain L without refreshing it. |
| L has age `T` or older; special-function refresh succeeds | DHW-wide timestamp can advance; cache-only whole-object expiry need not run | Measured field expires independently; withhold fresh fact, preserve history and other fields. |
| RR0005 from II01 rather than requested II00, or another source, `L` | Parser permits plus-one instance in one header form; source qualification is not established by that helper | Reject foreign input; compatible header normalization needs separate profile correlation proof. Never overwrite L under another identity. |
| Same selector/source but changed profile or decoder revision, `L` | No such new binding contract is demonstrated by the helper | Withhold new binding until qualified; do not transfer L's receipt into it. |
| RR0001 exact two-byte zero; then malformed presence reply | Native contract distinguishes not-present from unknown | Neither admits a fresh measured fact; unknown cannot erase evidence or become not-present proof. |
| New matching receipt, `00 00 34 42` (45 °C), after gap/expiry | Valid direct read can repopulate/update DHW | Recover only after current presence/profile admission; MCP/GraphQL agree on 45 and receipt. Unrelated fields remain intact. |

## Later implementation and acceptance

Gateway work must inspect direct reads, cache/fallback hydration, field merge
and receipt tracking, persistence, TTL expiry, provider/update publication,
boiler mirroring and both MCP/GraphQL adapters. HA work must inspect the DHW
measured-value consumer and its handling of zero, absence, stale retention and
recovery. This is not a specification for `number.py`, configuration bounds,
W09 re-probe or W23 entity lifecycle. M14/M15 boiler temperatures, W27
outdoor/aggregate work and W30 pressure remain excluded. No unmerged W
specification, J/M implementation or other X contract is a dependency here.

Before cutover, supply public family/profile-qualified native evidence for
RR0001 presence and RR0005 identity, full framing/correlation, byte order,
unit, invalid/sentinel behavior and applicable bounds. Keep raw evidence next
to interpretation, including firmware context when known and falsifiable
read conditions, after publication redaction. Resolve the concrete fact key,
fallback provenance and field-level freshness representation. Demonstrate
synthetic boundary and identity-isolation tests across every identity field,
partial merge, persistence, expiry and recovery, and MCP/GraphQL/HA parity.
Pack validation alone cannot replace this evidence or device qualification.

This ticket changes no fixture, producer, pack definition, write route or shared
mapping page. It adds no credential, principal, authentication or permission
check; authorization is not a cutover gate here. No major or experimental
namespace is introduced. Review and document readability are contract evidence
only, not semantic validation, transport conformance, passive/live smoke,
hardware acceptance or profile admission. Parent #952's remaining north-south
implementation and acceptance stay open.
