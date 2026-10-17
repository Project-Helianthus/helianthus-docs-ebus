# System pressure ownership and SemReg disposition

> **License:** AGPL-3.0. Helianthus architecture contract; this page neither
> changes the native protocol nor enables a producer.

This is the pressure disposition slice of gateway #952 / Project #2 INT-08.
It separates the existing `state.system_water_pressure` observation from
boiler-pressure consumers and deliberately withholds universal projection.
The parent acceptance remains open. Nothing here declares a stable contract
before Helianthus 1.0 or adds an authorization gate.

## Public native evidence first

The [B524 register catalog](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md)
is the native starting point: its VRC720-family singleton system group uses
`OP=0x02, GG=0x00, II=0x00`. The `RR=0x0039` row names `water_pressure`,
lists wire type `f32`, unit `bar`, and read-only behavior. Its legend identifies
unannotated rows as corroborated by multiple sources. This page adds no native
capture or target-qualified evidence.

The [B524 wire contract](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524.md)
supplies service `PB=0xB5, SB=0x24`, read operation type `OT=0x00`, and
four-byte IEEE-754 float representation. Float byte order is profile-dependent:
the characterized VRC720 controller uses little-endian; destination alone
never selects a codec. The catalog's separate requester matrix describes
little-endian identity scaling and bar for this register as candidate,
unconfirmed-on-wire interpretation. Do not turn that candidate or the
temperature-only mapping's applicability into pressure qualification for
another family, firmware, or installation. Unknown profile-specific scaling
or byte order stays **Unknown**.

**Proven — documented correspondence:** the catalog and
[B524 semantic mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md)
associate this system register with `state.system_water_pressure` (`f32`).
This is a source-document correspondence, not newly proven native sensor
placement or an executed gateway result.
**Hypothesis — broader physical equivalence:** the system and boiler readings
may agree in an installation; numerical agreement alone cannot establish the
same sensor, hydraulic location, owner, or fallback entitlement.
**Unknown — universal pressure semantics and qualification:** the supplied
[typed Thermal mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/fixtures/vaillant-semreg-thermal-map-v1.json)
defines two temperature candidates and an aggregate withholding row. It
defines no pressure fact, pressure role dimension, or pressure mapping. This
absence is scoped to the supplied public contract, not a claim about every
possible registry. Evidence labels Proven/Hypothesis/Unknown remain separate
from acquisition success, freshness, admission, and binding qualification.

## Four distinct dispositions

| Layer | Current documented identity or evidence | Disposition of this contract |
| --- | --- | --- |
| Native system value | B524 `PB=0xB5, SB=0x24, OP=0x02, OT=0x00, GG=0x00, II=0x00, RR=0x0039`; request initiator to controller, reply controller to initiator; family/profile-qualified `f32` in bar. | Retain native bytes, selector, source identity and decode provenance. Preserve the existing system-field correspondence; no new native read or write is specified. |
| Boiler-pressure consumer | The separate [B509 boiler catalog](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B509-boiler-register-map.md) lists candidate `water_pressure`, selector bytes `02 00` (printed `0x0200`), `DATA2b`, legacy path `state.waterPressureBar`, under `PB=0xB5, SB=0x09`. Target qualification remains required. | Keep boiler ownership independent. Do not alias or fill it from B524 system pressure, even when both numbers or units agree. This slice does not qualify B509 or change its producer. |
| Universal pressure fact | No pressure fact, quantity unit contract, role dimension, validation bounds or qualified pressure mapping is defined by the supplied Thermal map. | Leave these undefined. Invent no pack ID, fact name, dimension key/value, numeric bound, or conversion route. An existing temperature fact cannot carry pressure. |
| Universal projection | No accepted pressure semantic definition plus qualified mapping is available in this slice. | Withhold the pressure fact and its universal consumer projection. Record the disposition independently of a retained native value; emit no fabricated zero, temperature fact, or boiler substitute. |

The [GraphQL contract](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/api/graphql.md)
also distinguishes `SystemState.systemWaterPressure` from
`BoilerState.waterPressureBar`. Their presence is API correspondence, not native
equivalence. Existing MCP envelopes and GraphQL fields remain unchanged. Future
bindings must give both surfaces the same owner, value eligibility and
withholding meaning, using their existing omission/null conventions; this page
adds neither a response member nor a new API error/reason enumeration.

## Owner and retained observation

The following are requirements for a future pressure binding, not a new
artifact schema or a claim about today's cache implementation.

| Identity or retained information | Required boundary |
| --- | --- |
| Owning asset and service | Explicitly bound system asset and controller system service. A boiler asset/service remains distinct. Never derive ownership from a display name, public ID, equal scalar, or shared bus address. |
| Native route | Actual initiator and target, request/reply direction, full `PB/SB/OP/OT/GG/II/RR`, controller family and qualified profile context. A routing address is not a durable asset identity. Do not copy the temperature map's destination as pressure proof. |
| Source continuity | Source identity, source epoch and driver generation remain separate from asset/service and selector. Replacement at the same address cannot inherit qualification or last-known-good state by address alone. |
| Evidence and decoding | Preserve original reply/value bytes, response outcome, evidence reference, codec, byte order, unit and interpretation status alongside the decoded scalar. Rejected attempts remain distinguishable from accepted observations. |
| Time and lifecycle | Preserve original receipt information, receipt monotonic epoch and age, qualification and applicable freshness/retention policy identity. Evaluation and cache load cannot become receipt. Unknown source/phenomenon time remains absent. |
| Semantic identity | Remains absent for universal pressure until a reviewed definition supplies the fact, quantity unit, role dimensions and mapping revision. Native ownership is not an invented FactKey dimension. |

Only a valid observation with matching identity may replace a field's native
last-known-good observation. An unrelated field's success cannot refresh
pressure. Preserve existing admission/trust boundaries; this contract supplies
no new qualification rule or pressure lifetime. Policy durations and accepted
cross-epoch freshness rules remain downstream acceptance, not guessed values.

## Value and transition rules

These are proposed retention/admission requirements. The current source
documents establish field correspondence; they do not prove that the pressure
producer already implements this transition table. Universal pressure stays
withheld in every row, including an otherwise qualified native observation.

| Input or transition | Native observation / last-known-good treatment | Eligibility distinction |
| --- | --- | --- |
| Valid finite zero, with independently established codec and no applicable invalid sentinel | Keep numeric zero and its raw bytes as a value; replace the eligible prior observation normally. | Zero is not missing, invalid, or evidence that pressure is physically safe. No unsupported physical range is imposed here. |
| Missing sample, timeout, or empty response | Record the distinct acquisition outcome; do not replace a prior observation with zero or erase its evidence. With no prior observation, value remains absent. | Missing is not a fresh measurement; empty is not automatically dormant. |
| Invalid response shape, selector mismatch, undecodable value or non-finite float | Retain rejected raw evidence separately; do not update the accepted scalar. Preserve only an independently eligible prior observation. | No successful measurement. The wire contract's NaN example does not establish every profile's sentinel policy. Non-finite input is never promoted as a pressure quantity by this proposal. |
| Partial refresh: pressure fails, another field succeeds | Keep pressure's own last-known-good value and original receipt/evidence under its existing policy. Independently valid fields may update. | A plane-level success cannot mark pressure fresh or qualified. |
| Prior pressure becomes stale or exceeds retention | Preserve native evidence for diagnosis; mark it stale, then withdraw from eligible current-value use when its policy requires. Do not reset age or invent a lifetime here. | Stale is distinct from missing and invalid; retained bytes do not imply admission. |
| Decodable but unqualified observation | Retain native candidate and provenance without granting qualified use. No prior qualified observation means no qualified last-known-good value. | Acquisition success and plausibility cannot manufacture qualification. |
| Owner/source epoch/driver generation changes or evidence conflicts | Do not carry a former owner's qualification forward. Preserve prior evidence under its original identity; withhold current use pending the existing qualification/admission process. | Fail closed rather than selecting a convenient source or averaging conflicts. |
| Cache restore or delayed evaluation | Preserve original receipt and identity. Value-only cache data cannot reconstruct missing proof; unknown age/epoch handling remains unknown and ineligible without an accepted policy. | Restoration is neither a new sample nor requalification. No universal projection follows from cache availability. |

The typed Thermal map already separates retained receipt from delayed
evaluation and forbids using receipt restamping as freshness. Applying that
principle here requires field-local evidence. This page does not redesign
recovery, receipts, idempotency, or principal boundaries.

## Synthetic review examples and falsifiers

The examples below are reasoned contract checks, not executed producer tests,
captures, device qualification or runtime success. Bytes are value payloads
only, not complete telegrams. Assume an independently established matching
little-endian binary32 profile for the arithmetic examples.

| Synthetic case | Expected disposition | Counterexample that this rule rejects |
| --- | --- | --- |
| System value bytes `00 00 C0 3F` | Decode to `1.5` in the established native bar unit; retain as system pressure; universal projection withheld. | Publishing the same number under a temperature fact or boiler owner. |
| System value bytes `00 00 00 00` | Decode to valid numeric zero when the profile permits it; universal projection still withheld. | Treating zero as an absent pointer or a boiler-pressure fallback signal. |
| Earlier accepted system value, followed by an empty pressure reply and a valid temperature reply | Keep original pressure evidence/age; record pressure acquisition failure separately. | Updating pressure receipt because the overall system snapshot changed. |
| Same scalar and address after a source-epoch change | Retain the old evidence under the old owner; qualification cannot transfer automatically. | Admitting a cache scalar solely because its address and value match. |

Review each field below independently while holding the others constant. Each
variation must break source equivalence or leave the new binding unqualified;
no executed mutation coverage is claimed.

| Independent variation | Falsifier / forbidden inference |
| --- | --- |
| `PB`; `SB` | Either service byte changes: this is not the B524 system source; B509 is not interchangeable. |
| `OP`; `OT` | Changing opcode (including `0x06`) or read operation type breaks the read binding; matching group/register cannot restore it. |
| `GG`; `II`; `RR` | Vary any one selector component: another group, instance or register is not RR0039 system pressure. |
| Initiator; target; request direction; value direction | Change one route participant or direction: retain that distinct provenance; no automatic reply attribution or byte-order selection. |
| Family; profile context | Change either: previous decoding/applicability is insufficient for qualified pressure use. |
| Asset; service owner | Change either: a system observation cannot become a boiler observation. |
| Source identity; source epoch; driver generation | Change any one: qualification/retention cannot silently carry across continuity boundaries. |
| Codec; byte order; unit | Change any one: equal bytes or a plausible number cannot establish the same quantity. A temperature codec or Celsius unit is a dimension mismatch. |
| Evidence reference; receipt; freshness policy | Change any one without supporting evidence: no invented proof, freshening or extension of eligibility. |
| Proposed universal fact; role dimension | Any guessed pressure role or temperature dimension is unsupported. Withhold until both semantic definition and qualified mapping exist. |

## Remaining acceptance and scope

Native equivalence means the existing system field retains its documented
source, unit and established profile-specific decode; it does not promise
equivalence with boiler pressure. Deliberate universal withholding is the
required result today, including for a normal native value.

Downstream acceptance must supply a reviewed pressure semantic definition
(quantity, unit, roles, validity and loss rules), source/owner-qualified
mapping, accepted freshness/retention policy, and producer/projection evidence
with MCP/GraphQL parity. A scalar projection must account for identity,
provenance and time it loses. This page supplies none of those missing runtime
artifacts and changes no fixture or producer. It does not expand M15, close
gateway #952 / INT-08, or alter the J01-J17-owned G5 D1-D5/O8 boundaries.
There is no hardware, transport, live-smoke, deployment or release acceptance.
