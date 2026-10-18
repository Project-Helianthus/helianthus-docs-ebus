# Zone mode and preset: bounded SemReg cutover contract

> AGPL-3.0. Proposed gateway migration acceptance for one read-only field
> group; no runtime implementation or native write authority is established.

This slice covers zone `config.operating_mode`, `config.preset` and their
associated-circuit derivation context. It advances gateway north-south
projection work without closing that parent. Temperature fields, broad Matter
source inventory, schedules and operation commands are outside this contract.
Nothing here declares an API stable before Helianthus 1.0, creates a namespace,
or adds an authentication, authorization, principal or credential gate.
Existing trust and admission checks, G5 D1–D5/O8 and driver ownership of eeBUS
output binding remain unchanged.

## Sources and evidence status

The following public links identify the supplied source sections/functions;
the comparison below is against the supplied source views, not a live check of
remote main. Moving links do not attest a deployed revision.

- [Native register catalog][native]: `GG=0x03 — Zones`, `opmode — Operation
  mode`, `sfmode — Special function`, `mctype — Circuit type`, `zmapping —
  Zone room temperature sensor mapping`, and `Enumerations that differ by family`.
- [Public semantic mapping][mapping]: `Zone Mode Derivation`, `Circuit Type
  Layer B — Derived Projections`, `Sources & FLAGS Verification`, and
  `SemReg thermal v1 read-only Vaillant mapping`.
- [Current gateway implementation][gateway]: `refreshZoneSlowConfigFields`,
  `cachedZoneDerivationInputs`, `refreshState`, `resolveAssociatedCircuitInstance`,
  `deriveZoneModeAndPreset`, `derivePresetFromSpecialFunctionAndOpMode`,
  `normalizeSpecialFunctionToken`, `deriveManualOperatingMode`,
  `deriveZoneAllowedModes`, and `publishZones`.
- [Existing typed thermal mapping][thermal-map]: `mappings`, `qualification`,
  `lifecycle`, and `nonclaims`.
- [Thermal pack definitions][pack]: `fields`, `dimensions`, `services`,
  `capabilities` and `operations`.

**Proven (source inspection only):** the code branches and declared symbols
reported below exist in these inputs. This is implementation evidence, not
proof of a native enum or installation behavior. **Hypothesis:** source-specific
native interpretations and the proposed auto/off equivalences below.
**Unknown:** installation-qualified equivalence, disputed family labels,
override precedence and a qualified zone-to-circuit binding. Evidence grade is
separate from qualification, acquisition validity, freshness and admission.
The typed thermal mapping covers two system temperatures and withholds an
average; it contains no accepted zone-mode row. Its qualification block is
`Unknown`, requires a qualified binding and does not permit runtime
qualification. It cannot qualify this new field group by association.

## Native selectors and retained derivation inputs

Every row uses `PB=0xB5, SB=0x24, OP=0x02`, request initiator to qualified
controller target, response target to initiator. Preserve actual initiator and
target identities in binding evidence without publishing installation network
details. `z` is the native zone instance; `c` is an independently qualified
associated circuit instance. Neither is a display ordinal.

| Input | Exact remaining selector | Catalog representation; interpretation limit |
| --- | --- | --- |
| Heating operating mode O | `GG=0x03, II=z, RR=0x0006` | u16 enum, no unit; common 0 off, 1 auto, 2 manual. Family candidate labels and value 3 conflict; retain raw bytes. |
| Special function S | `GG=0x03, II=z, RR=0x000E` | u8 enum, no unit; gateway uses `readB524Uint16`. Catalog Zones usage and family candidate quick-veto labels disagree. Do not normalize the evidence to the gateway string. |
| Room sensor binding R | `GG=0x03, II=z, RR=0x0013` | u16 enum, no unit; room sensor assignment, not proven circuit identity. |
| Zone circuit assignment A | `GG=0x03, II=z, RR=0x001C` | raw bytes; profile-scoped native zero-based values, no +1 remapping. Signed/not-bound interpretation remains unconfirmed. |
| Circuit type T | `GG=0x02, II=c, RR=0x0002` | u16 enum; type 2 is fixed-value, not native cooling mode. |
| Circuit cooling-enabled C | `GG=0x02, II=c, RR=0x0006` | catalog/public mapping Boolean u8; gateway reads uint16 and decodes a Boolean. A qualified false is evidence, not absence. |
| Quick-veto context | `GG=0x03, II=z, RR=0x0008/0x0026/0x001E/0x0024` | Catalog setpoint f32 °C, duration f32 hours, end time/date; family candidate units/encodings remain disputed. |
| Holiday context | `GG=0x03, II=z, RR=0x0003/0x0004/0x0005/0x0020/0x0021` | Catalog start/end date, setpoint f32 °C, end/start time; configuration alone does not establish an active holiday. |

Preserve each component's raw request and reply, selector, direction, decode
result, units if known, family/firmware context when qualified, evidence
reference, source identity and epoch, binding identity, driver generation,
semantic revision, acquisition outcome and original receipt clocks. Missing
context remains explicitly unknown. Keep original receipt time distinct from
evaluation time; freshness uses elapsed monotonic time under the accepted
policy. No fixed duration is invented here. Never substitute OP=0x06, another
zone, another circuit, a UI label or a successful unrelated read.

The catalog separately names cooling operating mode at `GG=0x03, II=z,
RR=0x0001`, special-function state at `RR=0x001B` and zone cooling-enabled at
`RR=0x0029`. None is a substitute for the rows above. This slice does not add
acquisition or claim their unresolved formats solve the interpretation gaps.
FLAGS, readable values and candidate write encodings establish no writable
support in this contract.

## Current implementation versus public mapping

The public mapping and catalog's Zone Mode Derivation describe cooling-enabled
as heat/cool capability context. The inspected code does **not** pass C to
`deriveZoneModeAndPreset` or `deriveZoneAllowedModes`; both use T. With O=2,
T=2 returns `cool`; any other or missing T returns `heat`. Allowed modes are
`[off]` for T=0, `[off,auto,cool]` for T=2, and `[off,auto,heat]` for all other
or missing T. Thus O=2/T=0 can yield `heat` while allowed modes contain only
`off`. Neither branch proves native capability. Changing C alone changes
neither derived result. The public catalog explicitly describes T=2 as
fixed-value and cooling as a separate function: these sources conflict with
the code heuristic and are not interchangeable proofs.

`resolveAssociatedCircuitInstance` uses R: nil, 0, 0xFF, 0xFFFF and out-of-range
values fall back to z; values 1..0x20 become value minus one. Slow config reads
T at that result and stores an associated circuit only when R was non-nil.
Cached derivation prefers stored zone T, then stored associated circuit, then
same-instance circuit. In contrast, the native catalog calls R a room sensor
binding and A the zone circuit assignment, with raw indices retained. Neither
subtracting one from R nor assuming c=z establishes native association. A
qualified binding must resolve this before circuit-dependent equivalence.

The following table describes the pure helper result, not unconditional field
publication. `refreshZoneSlowConfigFields` only assigns operating mode when O
was read, and preset when O or cached S exists. `refreshState` uses cached O
and fresh S, falling back to cached S, and derives only if cached O exists or
S is recognized as meaningful. It assigns operating mode only with cached O.
These paths can combine observations from different acquisitions. The helper
itself carries no per-component freshness or qualification proof.

| Input to helper | Current operating mode | Current preset |
| --- | --- | --- |
| O=0, S nil/0/unrecognized | `off` | `manual` (fallback despite off) |
| O=1, S nil/0/unrecognized | `auto` | `schedule` |
| O=2, S nil/0/unrecognized | `cool` if T=2; otherwise `heat` | `manual` |
| O nil | `auto` default | `schedule`, unless recognized S overrides |
| O outside 0..2 | `auto` default | `schedule`, unless recognized S overrides |
| Any O, S=2 | Mode still depends on O/T | `quickveto` |
| Any O, S=3 or 4 | Mode still depends on O/T | `away` |

S=1, 5, 6 and other values are not recognized by
`normalizeSpecialFunctionToken`; they fall back as above. The catalog names
ventilation/home/load for some of them, so unrecognized does not mean inactive.
The code does not consult holiday dates to arbitrate presets. `publishZones`
sets quick-veto Boolean solely from preset `quickveto`, and concatenates expiry
only when both end date and end time are present. It exposes holiday fields
separately; their presence is not a holiday-active decision. MCP semantic
paths and the GraphQL Zone fields remain compatibility surfaces; this source
inspection does not validate their transports at runtime.

## Proposed bounded binding and exact loss decisions

The only proposed target is a read-only candidate FactKey:

- `PackID = helianthus.pack.thermal`, `PackVersion = 1.0.0` (existing pack
  identifier, not a claim of platform stability).
- `FactID = thermal.mode.zone`.
- Exactly one dimension: `thermal.dimension.zone`, text value `zone:alpha`
  in the synthetic cases. Production uses its qualified stable zone identity;
  never infer it from `zone-1`, z+1, R or a display name.
- Separate binding metadata identifies the qualified asset and
  `thermal.service.zone` service, native source, epoch and driver generation.
  They are not additional FactKey dimensions.

This is a **proposed**, unpromoted candidate mapping, not an implemented fact
producer. A candidate is not an admitted projection. Auto/off equivalence
requires source-specific evidence establishing that the native heating-mode
observation represents the requested zone-mode meaning, including override
and heating/cooling scope. A syntactically valid symbol alone is insufficient.
For this slice, all O/S components and the qualified zone/circuit context T/C
must be valid, fresh, coherent and qualified; missing association withholds
the composite rather than assuming a heating-only zone. Any meaningful or
unresolved override withholds the composite until precedence is qualified.
This conservative admission requirement is a proposal, not a new security gate.

| Current derived symbol | Candidate or withheld result under the current pack | Consumer loss / equivalence condition |
| --- | --- | --- |
| Operating `auto` | Candidate `thermal.mode.zone.auto` only for explicit O=1, qualified normal S and coherent context; otherwise withheld. | Preserves source-specific automatic zone operation only after equivalence qualification. Defaulted nil/unknown O never qualifies. No schedule contents or timing represented. |
| Operating `off` | Candidate `thermal.mode.zone.off` only for explicit O=0 under the same conditions; otherwise withheld. | Preserves qualified zone mode only; does not assert system shutdown, zero heat flow, disabled frost protection or command support. |
| Operating `heat` | Withheld; no zone heat symbol. | Manual heating identity is unrepresentable. Do not use system heat at a zone key or call it comfort. |
| Operating `cool` | Withheld; no zone cool symbol. | Manual cooling identity is unrepresentable; T=2 code heuristic also conflicts with native fixed-value meaning. |
| Preset `schedule` | Withheld as a preset; no preset field/service mapping is established. | O=1 may independently qualify auto, but auto does not encode the schedule preset or its contents. |
| Preset `manual` | Withheld; no manual zone symbol or preset fact. | Includes the code's off-mode fallback; manual is not comfort. |
| Preset `quickveto` | Withheld; no override/preset fact. | Preserve S and veto context; timing, target and override activity are not encoded by auto/comfort. |
| Preset `away` | Withheld; no away/preset fact. | Preserve S=3 versus S=4 and holiday context. Away is not eco; neither a holiday nor its precedence is proven by this collapsed string. |
| Allowed-mode lists; quick-veto Boolean/expiry | Withheld from this FactKey. | A single zone-mode symbol cannot encode capability sets, override activity or expiry. Keep legacy fields and raw evidence with explicit loss. |

`thermal.mode.zone.comfort` and `.eco` exist in the pack but have no justified
source equivalence here. There is no default-to-comfort or away-to-eco mapping.
The pack also contains system heat/cool symbols and system set-mode operations;
they do not supply missing zone/preset semantics, zone command support or
write qualification. No new fact, capability, operation or universal enum is
introduced to hide loss.

## Lifecycle, conflicts and projection accounting (proposal)

Validate and retain every component independently. Missing means no component;
invalid means malformed bytes or unsupported codec/enum; stale means retained
but outside the accepted freshness policy; unqualified means usable bytes
without qualified interpretation/binding. Valid O=0, S=0, T=0, C=false and
native assignment zero remain observations, not absent values. T=0 still
requires resolving inactive-circuit scope; it is not ordinary heating context.
Unknown S is not evidence of normal operation. A qualified S=0 can establish
normal operation only within its qualified family interpretation.

A failure updates that component's state without erasing unrelated last-known-good
components or rewriting their receipt times. Retain the last coherent derived
result with its original provenance and degraded/stale status under the existing
retention policy; it must not masquerade as a new fresh candidate. If there is
no prior coherent result, withhold. Do not regenerate a fresh result from stale
O plus fresh S, or stale association plus a new C. Source replacement changes
binding/epoch/generation: retain old evidence as history, but do not splice its
components into the replacement source or transfer qualification by address or
zone display ID. Re-establish coherent association and equivalence first.

For concurrent conflicting candidates at the same FactKey, preserve each source
and its evidence. Apply existing source/admission policy; unresolved conflict
withholds a new projection. Neither arrival order nor matching display labels
establishes equivalence. Different qualified native zones stay different keys.
Use deterministic envelope ordering and existing reason/disposition vocabulary;
the descriptions here are loss explanations, not new wire reason codes.

Keep exactly one projection disposition per requested `(kind,item_id)`.
Aggregate qualified candidate outcomes before deciding the requested shared
`thermal.mode.zone` definition's disposition. If an eligible source/zone fact
is projected, an absent or unrepresentable fact from another source/zone must
not overwrite that shared item with `withheld` or append a duplicate item.
Record those per-source losses separately. If none projects, return the existing
applicable withheld/unavailable disposition with the supporting losses. Preset
loss must not fabricate a second definition or a duplicate disposition for the
mode definition. Requests for service/capability definitions retain their own
item identities; field projection alone does not establish complete service
support.

MCP and GraphQL must consume the same accepted derivation and loss decisions,
with their existing field names, omission/null conventions and deterministic
envelopes. Preserve legacy raw/derived distinctions and partial last-known-good
state during cutover. Do not silently replace legacy strings with narrower
SemReg symbols. Contract acceptance requires an explicit consumer loss decision;
this document does not implement downstream adapters or change eBUS MCP.

## Synthetic transition review matrix

All values below are invented examples for one controller family and native
zone, not observations or executable tests. Unless changed in a row, assume
explicit O=1, S=0, qualified associated T=1/C=false, coherent fresh components,
and source-specific auto/off equivalence already qualified. Those assumptions
are deliberately stronger than the available evidence. “Candidate” still
requires existing admission; preset remains withheld throughout.

| Case / changed component | Current helper or publication behavior | Proposed outcome and loss |
| --- | --- | --- |
| Normal O=1 | `auto/schedule` | Auto candidate; schedule preset loss. |
| O: 1 → 0 | `off/manual` | Off candidate; preserve raw zero, no manual preset equivalence. |
| O: 1 → 2, T=1 | `heat/manual` | Withhold new mode: manual heating unrepresentable. |
| O=2, T: 1 → 2 | `cool/manual` | Withhold; fixed-value type is not cooling proof. |
| C: false → true, T=1 | No helper change, including O=2 remaining heat | Reevaluate scope/equivalence; withhold if combined heating/cooling meaning is unresolved. C=true does not prove active cooling. |
| C: true → false | No helper change | Preserve valid false; auto/off candidate only after heating-only equivalence/context requalification. No forced heat/comfort value. |
| Association absent or R-only heuristic | Fallback can use same-instance circuit | Withhold composite; no qualified c. Retain unaffected inputs. |
| A raw zero, R raw zero | Code falls back to z from R | Preserve two different zero observations; only qualified A interpretation can support association, never the R fallback itself. |
| T=0 | Helper allowed list `[off]`; O=2 still heat | Withhold unresolved inactive-circuit scope; no invented comfort/default. |
| O=1, S: 0 → 2 | `auto/quickveto`; quick-veto Boolean true | Withhold composite during override; no representable veto fact. Retain raw expiry/target separately. |
| O=1, S=3 or 4 | `auto/away` | Withhold composite; preserve distinct codes and unresolved family meaning, no eco. |
| S=2 plus holiday configuration claiming overlap | Helper remains quickveto; no date arbitration | Withhold conflicting/unqualified override interpretation; dates alone do not prove an active holiday. |
| S=3 plus veto context, or competing source S=2 | Helper follows S for each invocation | Withhold unresolved conflict; no inferred priority between away, veto or holiday. |
| O=9; S=0 | Helper defaults `auto/schedule` | Invalid/unknown enum: withhold, never auto by default. |
| O missing; S=2 | Helper auto/quickveto, callers do not assign mode without O | Withhold mode; preserve override observation. |
| S=9, or catalog-labeled S=1/5/6 | Helper ignores S and falls back | Withhold unresolved special function; no normal/comfort assumption. |
| S missing versus S=0 | Helper may treat both alike | Missing withholds; qualified zero can satisfy normal-operation condition. |
| O bytes malformed, or C undecodable | No accepted decoded component for that read | Invalid, not off/false; preserve prior coherent state with degradation only. |
| O fresh, S stale; or O stale, S fresh | Cached fallback/helper has no freshness argument | Withhold new composite; retain prior result with original age. |
| T/C or association stale, other components fresh | May still use cached T; C is unused | Withhold new composite; no freshness inheritance from zone reads. |
| All bytes valid/fresh, binding unqualified | Helper can still derive strings | Unqualified: no admitted projection. Evidence grade and acquisition remain separately recorded. |
| Source replaced at same public zone ID | Helpers alone do not fence replacement identity | Fence old epoch/generation; rebuild coherent qualified context. |
| Two sources disagree auto/off for same qualified key | No arbitration in helper | Preserve both; withhold new projection until existing policy resolves conflict. |
| One qualified auto fact projects; another source/zone lacks mode | Per-source absence is distinct from shared item | One projected definition disposition; attach separate loss, never overwrite with withheld. |

## Acceptance boundary and remaining evidence

Manual review must trace each selector and source claim to the sections above,
each code branch to its named function, and each transition to both its legacy
result and proposed loss. In particular, auto/off are conditional candidates;
no current pack symbol covers heat/cool/manual/away/quick-veto zone semantics.
Missing public evidence includes family-specific enum reconciliation, scalar
width qualification, actual circuit association, override precedence and the
heating-versus-whole-zone equivalence. Native raw evidence must precede any
future qualification; no live writes are authorized to obtain it.

This is canonical acceptance for this bounded migration field group, distinct
from temperature contracts and Matter inventories. Readability and manual
source review do not prove semantic validation, runtime projection, transport
parity or hardware behavior. Downstream implementation, independent review,
committed-head gates and any authorized hardware acceptance remain separate.

[native]: https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md
[mapping]: https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md
[gateway]: https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go
[thermal-map]: https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/fixtures/vaillant-semreg-thermal-map-v1.json
[pack]: https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go
