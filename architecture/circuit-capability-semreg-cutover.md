# Circuit topology and cooling capability cutover

This is the proposed, bounded gateway-to-SemReg acceptance contract for
helianthus-docs-ebus issue #702, advancing helianthus-ebusgateway#952 and
Project #2. It covers circuit type, cooling-enabled configuration and read-service
presence. Temperatures, pump state, writes and downstream integration are outside
acceptance. It does not close the parent. Nothing here is stable before
Helianthus 1.0.

## Evidence and authority

Read the public native contract before applying the proposed binding:

| Source | Sections or functions used | Authority and limits |
| --- | --- | --- |
| [B524 register catalog](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md) | “GG=0x02 — Circuits”, “mctype — Circuit type”, “Enumerations that differ by family”, unresolved names near the end | Native documentation contract; profile-scoped observations, candidate labels and unresolved evidence retain their stated limits. |
| [Legacy semantic mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md) | `ebus.v1.semantic.circuits.get`, ownership note and consumer note; “SemReg thermal v1 read-only Vaillant mapping” | Application mapping, not native wire proof. |
| [Gateway implementation](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go) | `refreshCircuits`, `readDhwPseudoCircuitEvidence`, `readDhwPseudoCircuitTemperatureEvidence`, `newDhwPseudoCircuitSnapshot`, `isDhwPseudoCircuitTemperatureEvidence`, `allCircuitRefreshInstances`, `circuitRefreshInstancesLocked`, `mergeCircuitSnapshotNonDestructive`, `publishCircuits`, `decodeHeatingCircuitTypeToken`, `decodeUint16Bool`, `readB524Uint16`, `deriveCircuitManagingDevice`, `decodeCircuitType` | **Proven as source behavior** in the reviewed implementation; not proof of installed topology or native semantics. |
| [Thermal definitions](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go) | `fields`, `dimensions`, `services`, `capabilities`, `Metadata` | **Proven as pack vocabulary**: circuit/DHW services and read capabilities exist; circuit type, cooling-enabled and managing-module fields do not. |
| [Existing typed thermal mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/fixtures/vaillant-semreg-thermal-map-v1.json) | `qualification`, `mappings`, `lifecycle`, `nonclaims` | Two temperature candidates only; qualification is Unknown and runtime qualification is not permitted by that fixture. It supplies neither topology qualification nor new circuit facts. |

**Proven**, **Hypothesis** and **Unknown** describe evidence, separately from
qualification, acquisition success, freshness and admission. A successful read
does not qualify a binding. **Hypothesis:** the proposed cutover can preserve a
qualified read-service identity while explicitly losing unrepresentable fields.
**Unknown:** an installation-qualified presence/role predicate for the virtual
native-water identity; this contract does not supply one. Public `main` links
are navigation references; the claims above were reviewed against the supplied
source snapshot, not a live runtime.

## Native selectors and current legacy behavior

Both field selectors are reads with `PB=0xB5, SB=0x24, OP=0x02, OT=0x00,
GG=0x02, II=<native circuit instance>`. Register bytes are little-endian:
RR `0x0002` is `02 00`; RR `0x0006` is `06 00`. Preserve the qualified
initiator QQ and controller destination ZZ, request direction initiator-to-target
and value direction target-to-initiator. Neither address nor instance alone
identifies a physical device. OP=0x06 is a separate namespace and cannot
substitute for these OP=0x02 observations.

| Requested native information | Public contract | Current implementation and loss risk |
| --- | --- | --- |
| Type: `(0x02,0x02,II,0x0002)` | `u16`, unitless enumeration. VRC720-family profile: 0 inactive, 1 heating, 2 fixed value, 3 DHW, 4 return increase. Raw `01 00` and `00 00` are documented profile observations. Labels remain subject to the catalog's candidate/conflict notes. | `refreshCircuits` treats decoded 0, 255 and 65535 as inactive candidates, subject to the pseudo-circuit exception. Other decoded codes become active snapshots. `decodeHeatingCircuitTypeToken` emits heating/fixed_value/dhw/return_increase for 1–4, otherwise `unknown_<raw>`. Unknown nonzero codes can therefore appear in the legacy list. |
| Cooling-enabled: `(0x02,0x02,II,0x0006)` | `u8`, unitless Boolean, 0 off / 1 on. This is separate from type and from actual cooling operation. | The poller calls `readB524Uint16`, then `decodeUint16Bool`: nil remains nil; zero is false and any decoded nonzero is true. Retain raw width and bytes: permissive legacy Boolean conversion does not validate the native 0/1 domain. |
| Service presence / managing role | VRC720-family II00–II08 are ordinary candidates; II09 is virtual native-water, not a physical heating circuit. Other/unknown families require separate qualification. Empty/null is not a valid value and cannot distinguish absence, inactivity and unsupported addressing. | Full scans probe II00–II0A; partial scans use sorted active cached instances. This requester range is broader than the current public profile. `deriveCircuitManagingDevice` assigns a functional-module identity only for system scheme 1, module configuration 2 and interpreted FM5 mode; otherwise role Unknown. It is a derived topology rule, not an individual circuit ownership telegram. |

The module rule's native inputs are OP=0x02, GG=0x00, II=0x00,
RR=0x0036 (system scheme) and RR=0x002F (module configuration), plus the
separate FM5 interpretation context. Keep them separate from circuit selectors
and retain the rule's evidence and revision. The mapping describes this narrow
topology as proven; this does not qualify other installations or reassignments.

`refreshCircuits` skips failed type reads; total probe failure returns without
publishing replacement data. Confirmed inactive entries are deleted, while
updates merge non-destructively. Missing cooling reads preserve the prior raw
flag; a new snapshot has no flag. A controller change updates controller identity
but the merge does not clear a missing cooling flag. Thus the legacy cache alone
cannot prove fresh, same-source cooling capability.

Do not substitute the zone-side `decodeCircuitType` labels (radiator,
underfloor, mixed for 0–2) for `decodeHeatingCircuitTypeToken`. They are
different implementation interpretations; neither establishes physical emitter
identity. The semantic mapping's zone derivation prose mentions the cooling
flag, while this contract's implementation claims are limited to the circuit
polling/publication functions above.

At II09, the legacy inactive path accepts decoded RR0008 or RR0020 values in
the range 5–95 and synthesizes type 3. If neither succeeds, two known results
permit inactive deletion; an unknown result preserves uncertainty. The public
native contract explicitly supplies **no** temperature/status presence predicate
for II09, and identifies RR0020 as raw status rather than a temperature. This is
a documented implementation/native-contract conflict. Preserve its raw evidence
and synthetic derivation marker; never promote that heuristic into qualification.
No temperature field is migrated by this contract.

## Proposed disposition and binding contract

These are migration requirements, not claims of implemented gateway integration.
The current Thermal pack cannot encode circuit type, cooling-enabled status,
physical equipment identity, managing module or an explicit presence Boolean as
field facts. Do not map them onto `thermal.action.state`, `thermal.mode.system`
or `thermal.status.operation`: action, mode and operation status do not express
those concepts. Do not invent a universal field or a new namespace.

| Item | Proposed FactKey / service / qualification | Consumer loss |
| --- | --- | --- |
| Native circuit type | No corresponding field, hence no FactKey; withhold semantic field projection even for qualified known codes. Retain selector, raw code, source and interpretation in native evidence. | SemReg-only consumers cannot reconstruct the legacy type token, emitter kind, mixer or physical equipment identity. |
| Native cooling-enabled | No corresponding field, hence no FactKey; withhold semantic field projection even for qualified 0/false or 1/true. | SemReg-only consumers lose the independent configuration flag and cannot safely offer cooling based on type, mode or action. False is valid evidence, not missing. |
| Ordinary circuit read service | Candidate `thermal.service.circuit` with `thermal.capability.read.circuit`; `Metadata` associates the service with `thermal.dimension.circuit`. Service binding is metadata, not a fabricated presence FactKey. Require independently qualified presence, circuit role, source and read binding. | Qualified service presence may survive; it proves neither physical-device identity, type nor cooling. A service definition existing in the pack does not mean this source implements it. |
| Virtual native-water read service | Candidate `thermal.service.dhw` with `thermal.capability.read.dhw`, dimension `thermal.dimension.dhw`, only after independent presence and DHW-role qualification. No presence FactKey exists. Until then, withhold this source's service binding. | A legacy pseudo-circuit list entry can disappear from the semantic projection; it must not become a physical circuit or an automatically duplicated DHW service. |
| Managing-module relation | No corresponding field or FactKey; retain qualified native role/ownership evidence separately. Module assignment is a binding prerequisite, not a Thermal topology fact. | No SemReg reconstruction of the legacy managing-device relation. |

Use an opaque, source-qualified service identity and dimension value associated
with the independently identified circuit or DHW role. A display index, zone
number, number of circuits or temperature cannot create an asset, dimension
identity or physical device. Neither type 1 nor type 3 supplies physical identity.
The type code is not the cooling flag; a read capability is not writable support.
No operation binding is added.

Before admitting either candidate service, require qualified asset/service and
role evidence, an existing supported read binding, exact native selector and
family applicability, valid decoding, freshness under the accepted lifecycle
policy, and unambiguous source ownership. Preserve current trust/admission
checks. No new principal, credential, permission or authorization gate is added;
authentication/authorization remain 0.11 work, with no authorization gate before
0.9. This contract supplies no missing qualification evidence.

Retain source identity and epoch, controller identity/context, driver generation,
binding revision, qualification reference, evidence reference, raw payload and
decode outcome. Keep receipt time and monotonic receipt context separate from
evaluation time; re-evaluation cannot refresh an observation. Preserve each
candidate and its selector, direction and provenance when candidates conflict.

## Proposed transitions and aggregate loss accounting

Missing, malformed/invalid, stale and unqualified evidence are distinct loss
reasons, never zero or false. A valid inactive type 0 is native evidence of
inactivity in its qualified ordinary-circuit context, not a transport failure.
The legacy sentinel treatment of 255/65535 is not an additional native enum.
Do not infer presence from either sentinel or any unknown code.

On a failed read, preserve partial last-known-good native state and its original
freshness/source metadata. It may remain historical evidence but cannot renew
admission. Independently qualified unaffected services remain available; a
missing cooling flag alone neither creates cooling support nor removes an
otherwise qualified circuit service. A qualified inactive transition withdraws
that source's active binding. Sparse missing instances remain unresolved until
qualified evidence distinguishes removal from read loss. Reappearance requires
fresh presence and role qualification; never compact or renumber surviving IDs.

Source replacement, controller replacement at the same address, driver-generation
change and module reassignment fence old evidence from the new binding. Retain
the former source's last-known-good evidence as historical, withhold the new
binding until its presence/role/ownership is qualified, and never carry an old
cooling flag across the boundary. Reassignment does not transfer capability
merely because II and type are unchanged. Conflicting current candidates remain
visible and withheld unless an existing qualified selection policy resolves
them; no arrival-order winner or averaging is introduced.

Produce exactly one disposition for each requested `(kind,item_id)` in the
existing deterministic envelope. The withheld/unavailable/loss language here
describes outcomes, not new response enums or a schema. Collect per-source
outcomes first, then reduce at the requested item granularity. If a qualified
source already projects a shared definition/service, an absent fact from another
source must not overwrite that projected disposition. Keep the absent source's
loss in its own provenance. A conflict affecting the selected binding is different
from unrelated source absence. Unsupported type/cooling fields stay explicitly
withheld and must not overwrite service dispositions or unrelated facts.

MCP and GraphQL must share the same admitted identities, valid false values,
source/loss decisions and ordering, using existing surface null/omission rules.
Retain eBUS MCP compatibility while exposing cutover loss; do not silently
replace legacy data with fabricated Thermal facts. Actual downstream parity is
not proven here. G5 D1–D5/O8 remain unchanged; eeBUS output binding stays
driver-owned. This is separate from Matter source inventory and temperature
cutovers.

## Synthetic source-specific acceptance cases

The following are proposed manual acceptance cases, not captured observations,
executed tests or evidence that runtime admission is implemented. `A` and `B`
are opaque synthetic sources; `C` and `D` are independently qualified service
identities. Each row inherits all binding prerequisites above.

| Case | Inputs / transition | Required equivalence or explicit loss |
| --- | --- | --- |
| Heating with cooling | A/C, ordinary qualified presence and role; type `01 00`, flag `01` | Legacy heating and true are independent native observations. Circuit read-service candidate can survive qualification; both field facts remain withheld. Type does not imply cooling or emitter identity. |
| Known type, missing flag | A/C type `01 00`; flag read missing, with and without a prior valid flag | Preserve prior native flag only as last-known-good with original freshness; first-read missing remains missing. Never infer false or cooling support; independently qualified service can survive. |
| Valid zero / false | A/C flag `00`; separately a qualified ordinary type `00 00` | Flag false is valid evidence, still unrepresentable as a Thermal field. Type zero means inactive in that context and withdraws active binding; neither is an invalid read. |
| Unknown or invalid | A/C type `07 00`; separately empty/truncated type, or flag outside 0/1 | Preserve unknown raw type separately from invalid decoding. Legacy may list `unknown_7` or convert a decoded nonzero flag to true; proposed path cannot use either as capability/presence proof. An independently qualified service need not lose unrelated facts. |
| Stale / unqualified | A/C valid bytes with expired freshness; separately fresh but unqualified bytes | Distinct loss reasons; neither admits new service presence or renews old evidence. Evidence label alone does not change qualification. |
| Sparse disappearance / return | C and D exist; C stops replying while D remains, then C returns | No count-based removal, renumbering or new device. Preserve D and historical C; qualify C's return. Contrast a qualified inactive C result, which withdraws C's binding. |
| Virtual pseudo-circuit | II09 inactive type with legacy heuristic evidence; separately independent qualified native-water presence and DHW role | Heuristic-only entry is withheld, never physical. Independently qualified virtual role may bind DHW read service without creating a heating device; current sources do not provide that missing predicate. |
| Module reassignment | A/C keeps II and type; module role/assignment context changes | Fence old owner and flag; require new qualified ownership. Legacy global topology rule alone does not prove a new per-circuit assignment. |
| Source replacement | A/C replaced by B at same native address/II, new epoch or generation | Historical A remains separate; B starts unqualified until its own evidence qualifies. No cached true/false or type transfers by address equality. |
| Conflict and shared definition | A and B disagree about the same selected role/flag; separately B has no fact while qualified A already projects a requested shared service | Unresolved relevant conflict is withheld with both candidates retained. Mere B absence cannot replace A's projected `(kind,item_id)` disposition. Different services C/D retain independent outcomes. |

Source-specific equivalence is limited to preserving an independently qualified
read service's identity, role and availability. It does not establish equivalence
of the lost type/cooling/ownership fields. Closing those losses requires an
accepted corresponding definition and qualified native mapping in future work,
not reinterpretation of a temperature, mode, action or writable operation.

## Acceptance boundary

Manual review must compare every selector, implementation claim, transition,
loss, example and public link with the sources above. The bounded contract is
complete when those distinctions and deliberate losses are reviewable; downstream
implementation, runtime conformance, full MCP/GraphQL integration and hardware
acceptance remain parent work. Readability checks prove only that this document
exists and is nonempty. No prose-token test, new fixture, validator or universal
definition is required or supplied.
