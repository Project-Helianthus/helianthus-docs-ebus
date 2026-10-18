# DHW mode and special-function SemReg cutover

This is the bounded gateway-to-SemReg migration acceptance contract for
[docs-ebus #697](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/697),
advancing [gateway #952](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/952)
as a partial north-south MCP/GraphQL contract. It covers DHW operating mode,
special-function inputs, time-program membership, boost and operation state.
Measured temperature and setpoint, the broad Matter inventory, and downstream
implementation are outside acceptance. This document proposes behavior; it does
not enable a binding. Nothing is stable before Helianthus 1.0.

## Evidence and source authority

- [Native register map](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524-register-map.md): sections “GG=0x01 — Native Domestic Hot Water”, “opmode — Operation mode”, and “sfmode — Special function”. These are the public native contract first; candidate descriptions remain candidates.
- [Legacy semantic mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md): sections `ebus.v1.semantic.dhw.get`, `ebus.v1.semantic.boiler_status.get`, and “SemReg thermal v1 read-only Vaillant mapping”.
- [Gateway implementation](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/semantic_vaillant.go): `refreshDHWSlowConfig`, `refreshDHW`, `cachedDHWDerivationInputs`, `readDhwUint16`, `readB524Uint16`, `deriveDhwModeAndPreset`, `derivePresetFromSpecialFunctionAndOpMode`, `normalizeSpecialFunctionToken`, `publishDHW`, `expireDHWIfStaleLocked`, `mergeBoilerDHWFieldsFromSnapshot`, and `decodeDhwMode`.
- [Thermal definitions](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go): `fields`, `dimensions`, `services`, `capabilities`, `operations`, and `Metadata`.
- [Existing thermal mapping index](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/fixtures/vaillant-semreg-thermal-map-v1.json): `qualification`, `mappings`, `lifecycle`, and `nonclaims`. It covers temperatures, not these DHW inputs, and its unknown qualification does not authorize a DHW binding.

**Proven (source inspection):** the implementation behavior and pack inventory
below are directly present in these sources. That label does not prove a native
wire interpretation or qualify an installation. **Hypothesis:** candidate
special-function/load interpretations and proposed equivalences pending native
correlation. **Unknown:** unsupported layouts, applicability, or absent evidence.
Qualification, acquisition success, freshness and admission are separate axes;
a successful read or a Proven code path cannot substitute for qualification.
Public main links identify source files, not immutable runtime evidence.

## Native inputs and current legacy behavior

The exact local DHW read namespace is `PB=0xB5, SB=0x24, OP=0x02,
GG=0x01, II=0x00`, with the register below. The current poller fixes
`dhwInstance=0x00`; `OP=0x06, GG=0x01` means primary heat sources and is never
a DHW replacement. The native register map only establishes this local instance; a second
instance is an identity-isolation requirement, not a claim of native support.

| Input | Register, native type and evidence | Current behavior and loss risk |
| --- | --- | --- |
| Native configured mode | `RR=0x0003`, `u16`, native range 0..2; opmode DHW labels 0 off, 1 auto, 2 heat. The enum also lists 3 night, outside that row's range and not observed in practice in VRC720-family behaviour. | `refreshDHWSlowConfig` uses `readDhwUint16`, retains the decimal `ConfigurationDHWOperationMode` token, and derives mode/preset with cached special function. `deriveDhwModeAndPreset`: 0 → `off`, 1 → `auto`, 2 → `heat`; nil or other values default to `auto` inside the helper. Callers constrain when it runs; this is not proof that missing input is auto. |
| Special-function mode input | `RR=0x000D`, `u8`, observed one-byte reply width; normal code 0, DHW load code 6 in `sfmode`. The write/reaction descriptions for this register are candidate evidence only. | `dhw_special_function` points here, but `refreshDHW` calls `readDhwUint16`, which delegates through `readB524Uint16` to `decodeB524Uint16`. Keep the original one-byte/type evidence rather than asserting a two-byte native layout. The raw decimal token becomes `StateSpecialFunction`; helper normalization recognizes 2 as quickveto and 3/4 as away, but not 6 as load. Those generic helper labels do not establish DHW semantics. |
| Special-function state | `RR=0x000F`, `u16` state, not gated by circuit type. Code 9 as one-time tank loading is explicitly candidate evidence. | `refreshDHW` reads `0x000D`, not this selector. The legacy mapping table's `state` from `0x000D` is not evidence that `0x000F` was acquired. No qualified active/loading interpretation follows. |
| Time-program membership | No exact membership selector or Boolean derivation is established by these sources. | Preset `schedule` is selected from mode 1, or helper fallback for auto. It is not a read of current slot membership. No native membership fact may be reconstructed from that label. |
| Boost | Candidate load code 6 at `0x000D` and candidate state 9 at `0x000F` are different inputs. | Neither is an acquired, qualified Boolean boost observation here; the preset helper does not turn 6 into boost. A configured special function does not prove that loading is active. |
| Operation state | `RR=0x000F` remains raw special-function state. The separate DHW pump-active status registers at `RR=0x0002` (circulation pump) and `RR=0x0006` (DHW pump) in this same DHW namespace do not establish a qualified equivalence to operation state; such an equivalence stays a Hypothesis pending native correlation. | No qualified whole-system action or active/idle operation follows from configured mode, schedule or special function. This slice adds no alternate acquisition path. |

For gated rows the native discovery predicate is `RR=0x0001`, exact two-byte
UIN, nonzero for presence; zero is `not_present`, and empty/wrong-width/NACK/
decode failure/unmatched is `unknown`. That presence zero is distinct from
mode zero, which is valid off. Ungated `0x000F` does not establish a DHW service
by itself. Applicability remains family- and binding-specific.

`publishDHW` publishes `Config.OperatingMode`, `Config.Preset` and
`State.SpecialFunction`. The last is the token from `0x000D`, not decoded
operation state. `refreshDHW` can combine fresh special function with cached
mode; slow refresh can combine fresh mode with cached special function. A
successful unrelated field can update the shared DHW update time. Current
`expireDHWIfStaleLocked` expires the whole snapshot only on the cache path
when its configured TTL is reached; it does not establish component freshness.
The proposed contract below therefore requires separate component ages.

A further source-specific discrepancy must survive migration:
`mergeBoilerDHWFieldsFromSnapshot` copies the configured raw mode into the
boiler snapshot, and `decodeDhwMode` publishes 0 → `OFF`, 1 → `ON`, 2 → `AUTO`,
other → `UNKNOWN(raw)`. These differ from the DHW helper's 1 → `auto`,
2 → `heat`, other → `auto`. Neither decoder proves native semantics, and a
boiler mirror is not an independent boiler-source fact. Preserve source and
raw code; do not normalize the two surfaces into an asserted equivalence.

## Proposed cutover and explicit withholding

The current Thermal `fields` table has no dedicated DHW mode,
special-function, time-membership or boost definition. Its
`thermal.mode.system` symbols are auto/cool/heat/off and use
`thermal.dimension.system`; `thermal.mode.zone` uses `thermal.dimension.zone`.
`thermal.action.state` and `thermal.status.operation` also use the system
dimension. Symbol resemblance cannot turn a DHW observation into a system or
zone fact. No FactKey for these DHW inputs can be constructed under the
current pack; retain each native value outside the Thermal fact projection.
Do not invent a universal definition or attach a DHW dimension to a field
whose declared dimension is system or zone.

| Requested meaning | Proposed FactKey / service / qualification | Consumer loss disposition |
| --- | --- | --- |
| DHW configured mode, including valid off | FactKey withheld: no dedicated field. A separately qualified `thermal.service.dhw` may identify the service using `thermal.dimension.dhw`; this does not supply a mode field. | Retain exact raw mode and legacy source label; normalized DHW mode is unrepresentable in Thermal. |
| Native special-function mode or state | FactKey withheld: no matching field, with independent qualification for `0x000D` and `0x000F`. | Retain raw code, width and selector; lose normalized preset/load/state if consumer accepts only Thermal facts. |
| Membership or boost | FactKey withheld: no matching field and no qualified native derivation here. | Unknown membership/boost must remain unknown, never inferred false. |
| System mode, system action or system active/idle requested from these inputs | Withhold these candidates for `thermal.mode.system`, `thermal.action.state`, `thermal.status.operation`; no source-specific equivalence is established. | A native DHW off or load candidate cannot supply system off, action DHW, or operation active/idle. |
| DHW read service metadata | Candidate existing definitions: `thermal.service.dhw`, service FactKey dimension `thermal.dimension.dhw=<binding-owned DHW identity>`, and `thermal.capability.read.dhw`. `Metadata` declares the capability's service. No field FactKey or operation is added. | Expose only metadata backed by an independently qualified, admitted read binding; it advertises neither dedicated mode coverage nor the entire service's possible observations. Withhold runtime binding/capability admission when that evidence is absent. Definition inventory alone is not a bound service. |

The service identity must retain asset, service, source, source epoch, driver
generation, semantic revision, qualification evidence and its own native DHW
identity. Do not derive it from a display ID or assume `II=0x00` across sources
means the same asset. Record the actual request initiator and controller target,
request/value directions, PB/SB, opcode/group/instance/register, original reply
bytes and width, decoder identity, family/applicability context, evidence
reference, receipt fields and separate evaluation context. Unknown provenance
prevents qualified admission. No private address or device identity is needed
in public examples. The existing temperature fixture's receipt/evaluation
separation is a lifecycle precedent, not DHW qualification or reused evidence.

All preceding dispositions are **proposed migration acceptance**, not implemented
runtime behavior. These rows create no principal, credential or permission
gate; current trust/admission checks remain intact. Authentication/authorization
remain later platform work. G5 D1–D5/O8 remain unchanged; eeBUS output binding
remains driver-owned. No new major or experimental namespace is introduced.

## Transition and projection accounting rules (proposed)

1. Preserve missing, invalid, stale, unqualified and valid separately. Missing
   bytes, malformed width, unknown enum, or failed acquisition must not become
   mode off, auto, normal special function or Boolean false. Valid mode 0 and
   special-function 0 retain their value even though no Thermal fact represents
   them. A genuine qualified false from a separately defined Boolean source
   would be a value, but no membership/boost Boolean source is qualified here.
2. Retain partial last-known-good native components on a failed read; retain
   original receipt and component freshness. Fresh `0x000D` cannot rejuvenate
   old `0x0003`, or vice versa. Stale retained history is available as history,
   with current semantic admission withheld. Evaluation cannot refresh receipt.
3. On source replacement, fence by source epoch and driver generation. Retain
   old history under its old identity; do not combine its mode with replacement
   state or transfer qualification. Require the replacement binding's evidence.
4. Keep conflicting candidates, selectors and decoders visible. An admitted
   winner requires an existing qualified selection rule; this document invents
   none. Without one, withhold the affected candidate, not unrelated qualified
   components. Never resolve a conflict by last arrival or by numerical match.
5. Produce exactly one disposition per requested `(kind,item_id)`, after
   aggregating all sources for that definition. Native-field loss reasons are
   separate from definition-level disposition. If another qualified source
   projects `thermal.status.operation`, absent DHW operation evidence must not
   overwrite that item as withheld or append a duplicate disposition. If no
   source projects an existing requested definition, record one withheld result
   with reasons. Do not invent item IDs for undefined DHW fields; report their
   native consumer loss outside projection accounting.
6. Preserve deterministic envelopes and the same semantic result, provenance,
   losses and unavailable distinctions across eBUS MCP and GraphQL. Existing
   field names, aliases and absence/null conventions remain the compatibility
   boundary. Do not silently change legacy decoder behavior during cutover or
   fabricate replacement values to fill a schema. Consumers requiring the old
   mode/preset retain the native/legacy path until they explicitly accept loss;
   metadata-only exposure does not establish equivalent behavior.

## Synthetic acceptance cases

These are manual contract examples, not observations, executable fixtures, native
proof, or runtime tests. Codes are source values; identities A/B and epochs
old/new are synthetic. Every row assumes independent qualification evaluation;
none grants a binding merely by supplying valid bytes.

| Case | Inputs / transition | Required result and source-specific equivalence |
| --- | --- | --- |
| Missing and unknown mode | Mode absent, then raw 7, special function 0 | Missing and unknown code remain distinct. Helper default auto is legacy code behavior only; neither permits an auto fact. Retain 7 without inventing its native meaning. |
| Valid off / normal special function | Mode raw 0, special-function byte `00` | Retain valid off and normal-code evidence; neither missing nor false by default. DHW `off` and mirror `OFF` match only as legacy renderings of this same raw source; no system-off equivalence. |
| Decoder conflict | Mode raw 1, then raw 2 | Preserve DHW auto/heat versus mirror ON/AUTO and native raw code for each. Mode raw 3 remains the native enum/range discrepancy, not a qualified night mode. |
| Mode versus special function | Mode raw 0; `0x000D` byte `06`; independent `0x000F` raw state 9 candidate | Do not rewrite off into heat or action active. Keep all three selectors separate. Load/boost and state interpretation remain Hypothesis; the legacy helper does not recognize 6. One byte must not be silently documented as two. |
| Legacy preset ambiguity | Mode 1 with special-function codes 2, 3 or 4 | Code helper yields quickveto/away; DHW native meaning is not qualified by those generic labels. No boost or operation equivalence. |
| Two DHW identities | Qualified identity A at one source and identity B at a different source, each with local `II=0x00`; different mode values | Keep separate service identities, epochs and native evidence. Singleton legacy publication is not proof of multi-DHW aggregation. A synthetic `II=0x01` candidate remains unsupported until separately qualified; never collapse into A. |
| Stale component | Mode last-known-good, then fresh special-function 0 after mode freshness expires | Keep old mode history stale, special function fresh; withhold current mode admission. Shared snapshot update time does not refresh mode. No composite fresh auto/preset. |
| No qualified binding | Valid raw 0 with absent service qualification, or valid bytes after failed presence discovery | Retain raw evidence; no admitted runtime read capability/service and no mode fact. Definition metadata can exist independently. Valid zero cannot cure unqualified binding. |
| Invalid versus false | Wrong-width mode or failed special-function decode; separate hypothetical valid Boolean false | Invalid reads retain last-known-good without asserting false; a genuine false would retain value and evidence. No false membership/boost is synthesized here. |
| Source replacement | Same public label, old source epoch replaced by new driver generation | Do not join old mode to new state, transfer freshness, or reuse qualification; replacement must qualify separately. |
| Conflicting candidates | Two candidates for one service disagree, including one raw-equal value with different provenance | Preserve both; equality alone is not equivalence. No qualified arbitration means withholding the affected candidate. A boiler mirror and controller source are not independent votes. |
| Shared-definition accounting | Independent qualified source projects requested `thermal.status.operation`; DHW operation is absent | Exactly one projected disposition for the requested definition; native DHW loss remains separate. With no qualified projecting source, exactly one withheld disposition. |

## Acceptance boundary and remaining evidence

Manual review must cover each source claim, transition, loss row, synthetic case
and public source link against the cited sections/functions. File readability
checks only that the document exists and is nonempty; it does not validate
semantics or prove runtime behavior. No prose-token tests, new schema, fixture
or validator are required by this slice.

Missing evidence includes qualified per-family decoding and reply widths,
special-function mode/state correlation, membership/boost derivation, second
DHW identity support, component freshness policy and replacement/arbitration
runtime behavior. No command or writable capability follows from read metadata,
raw zero, register flag values or candidate write descriptions. This contract does not
qualify hardware, change polling or writes, implement a downstream projection,
or close the parent issue. Independent review and applicable committed-head
gates remain required for integration.
