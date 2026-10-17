# Boiler temperature SemReg cutover slice

> **License:** AGPL-3.0. This is a Helianthus read-only mapping proposal, not a
> native protocol specification or an enabled producer.

This slice covers exactly the existing boiler flow and return temperature
fields. It is partial acceptance for gateway #952 / Project #2 INT-08; the
parent stays open. It adds no controller profile or boiler qualification rule.
The downstream producer work owns implementation and cutover evidence.

## Native contract and evidence boundary

Start with the public [B509 wire contract](../protocols/vaillant/ebus-vaillant-B509.md#wire-shape),
its [Device-Type Gate](../protocols/vaillant/ebus-vaillant-B509.md#device-type-gate-register-address-collision),
the [boiler register candidates](../protocols/vaillant/ebus-vaillant-B509-boiler-register-map.md#direct-read-candidates),
and the [name correspondence fixture](../protocols/vaillant/fixtures/b509-register-name-correspondence.csv).
The flow row identifies operation `0D`, selector bytes `18 00`, canonical name
`flow_temperature`, and codec `DATA2c`. There is no boiler-return row. Selector
bytes are written in wire order: interpreting those bytes as a numeric
little-endian symbolic address remains **Hypothesis** under the native page.
Do not confuse selector byte order with the documented
[DATA2c value codec](../types/primitives.md#data2c-d2c).

**Hypothesis — native flow meaning:** the public boiler-family correspondence
supports a candidate flow temperature, not target-qualified wire proof.
**Unknown — native boiler return source:** no accepted selector or codec is
established for this field. Unproven meaning or polarity elsewhere remains
Hypothesis or Unknown; an application label never resolves it.

**Proven — software read path:** the functions below establish what the gateway
does. This is corroborating implementation evidence only. Evidence labels
Proven/Hypothesis/Unknown are independent of SemReg qualification values
`candidate`, `qualified`, `unsupported`, `unknown`, and `rejected`, and of
assertion, promotion, validity, availability, and freshness.

## Existing read and publication path

In the gateway repository, trace `cmd/gateway/semantic_vaillant.go` by function:

1. `findBoilerAddress` selects a routing target from registry snapshots accepted
   by `isBoilerDeviceSnapshotCandidate`: normalized device-ID prefixes `BAI`
   or `BMU`. This family heuristic is not product-ID qualification.
2. `refreshBoilerStatusTier` runs the controller path first, then the boiler
   path. In the fast tier, `refreshBoilerStatusB524` calls
   `mergeBoilerMirrorFieldsFromSnapshots`. An age-bounded system-flow
   observation from the same controller can fill `FlowTemperatureC`;
   `boilerMirrorMaxAge` bounds admission of that mirror only.
3. `refreshBoilerStatusB509` reads `boiler_b509_flow_temperature` through
   `readB509DATA2c` during the fast tier. A successful B509 result overwrites
   that tick's mirror. `refreshBoilerStatusStartup` in
   `cmd/gateway/semantic_vaillant_startup.go` also performs the B509 flow read.
   `readB509ValueWithMaxAge` and `parseB509ReadPayload` handle the read/selector
   response path; scheduler reuse is not a new native observation.
4. `decodeDATA2c` in `cmd/gateway/b509_decode.go` requires at least two bytes
   and computes signed little-endian integer divided by 16 from the first two
   value bytes; trailing value bytes do not fail that decoder. It currently
   checks neither the replacement value nor the Thermal bounds. Thus `00 80`
   can become `-2048 °C` in the legacy flow field.
5. `mergeBoilerSnapshotNonDestructive` retains an omitted flow value without a
   field expiry and forces `ReturnTemperatureC` to nil on every merge. Return
   has no live producer. `publishBoilerStatus` copies both pointers to the
   GraphQL provider. Plane-level live/cache provenance does not prove that
   each retained field was freshly observed.
6. `cacheBoilerToGraphQL` and `graphQLBoilerToCache` in
   `cmd/gateway/semantic_cache.go` restore/persist flow and return values.
   A historical return value can therefore reappear from cache without native
   provenance before a merge clears it. Cache restoration is not return-source
   evidence.

The legacy identities are boiler `BoilerState.FlowTemperatureC` and
`BoilerState.ReturnTemperatureC`: MCP `ebus.v1.semantic.boiler_status.get`
state members `flow_temperature_c` / `return_temperature_c`, and GraphQL
`BoilerState.flowTemperatureC` / `returnTemperatureC` (including existing
snake-case aliases). In gateway `mcp/server.go` nil pointers are omitted;
`graphql/schema_types.go` resolves them as null. The boiler projection in
`cmd/gateway/gateway_portal_projection.go` copies the same pointers. HA
`custom_components/helianthus/sensor_descriptors.py` lists these two names in
`REDUCED_BOILER_TEMPERATURE_FIELDS`. Circuit `flowTemperatureC` and solar
`returnTemperatureC` are separate fields.

## Two-field mapping and qualification

The Thermal pack source is SemReg `semreg/v1/packs/thermal/definitions.go`
and `validator.go`: `thermal.measurement.water_temperature` is a quantity in
`unit.celsius`, with exactly one typed-text FactKey dimension
`thermal.dimension.temperature` and inclusive bounds `-100..200 °C`.
Out-of-bounds input is `bounds_exceeded`; bounds are semantic validation, not
a claim about a boiler's physical operating range. Asset, service, source,
source epoch, driver generation, native binding and evidence identity remain
separate from that role dimension, following the
[existing Thermal mapping](b524-semantic-mapping.md#semreg-thermal-v1-read-only-vaillant-mapping).

| Existing boiler field | Native source and evidence | Required qualification | Proposed Thermal mapping / current disposition |
| --- | --- | --- | --- |
| Flow: `FlowTemperatureC` | B509 `PB=0xB5, SB=0x09, OP=0x0D`, complete selector `18 00`; initiator-to-qualified-boiler-target request, target-to-initiator reply; `DATA2c`, °C. Native meaning **Hypothesis**; software source **Proven**. | Exact current boiler-class target identity through the native product-ID gate, bound to the actual routing target, service, operation, complete selector, response shape and codec. Family-prefix or bus-address matching alone is insufficient. No qualifying boiler-target artifact/rule exists today: runtime qualification `unknown`, field withheld. | Candidate `thermal.measurement.water_temperature`, quantity `unit.celsius`, dimension `thermal.dimension.temperature` with proposed text role `temperature:boiler_flow`. Exact numeric mapping only after qualification and validity/freshness admission; no fact emitted today. Missing qualification has proposed reason `reason.boiler_temperature.qualification_unknown`. |
| Return: `ReturnTemperatureC` | No accepted native source, selector, codec or source unit; evidence **Unknown**. Legacy C suffix is not source evidence. | A future exact boiler-target product identity, native return selector, response shape, codec and unit must be evidenced and qualified independently. None exists: runtime qualification `unknown`, field withheld. | Legacy field absent; no fact emitted and no separate projection disposition. `temperature:boiler_return` is reserved and unpublished, not an admitted FactKey. Proposed missing-source reason `reason.boiler_temperature.return_source_unknown` describes this legacy-field absence outside projection accounting; it must not be replaced by a guessed temperature. |

Reason codes here are proposed mapping diagnostics for downstream adoption,
not a claim that the producer or a reason registry already implements them.
The [controller qualification evidence gap](vaillant-controller-qualification-v1.md)
also has `qualified_use_permitted=false`; it cannot qualify a boiler target.
This page does not create the missing qualification rule, transfer controller
qualification to a boiler, or invent an identity witness.

## Value, retention, freshness and loss rules

These are cutover requirements; they do not describe implemented new behavior.
Retain the native observation and selector/reply evidence separately from its
semantic interpretation. A short, over-length or mismatched reply, read failure,
`DATA2c` replacement bytes `00 80`, or out-of-bounds quantity supplies **no update**.
Never synthesize zero or another default, or emit the replacement decoded as a
measurement. The proposed exact shape requires exactly two DATA2c value bytes
after validating and removing the qualified reply envelope. The public native
contract describes both `0D 18 00 data...` and `18 00 data...` response forms;
neither authorizes accepting extra value bytes as a boiler temperature. The
actual form must be qualified for the exact target and binding, with a complete
matching selector (and matching operation when echoed). This is a proposed
admission restriction, distinct from the legacy decoder's minimum width; it
does not assert that either reply form has been qualified on a boiler target.
Valid `00 00` is `0 °C` and remains a value. DATA2c increments of `1/16 °C`
can be represented exactly as canonical decimal quantities, without rounding.

A partial failure preserves an already qualified field-local last-known-good
observation and its original evidence and deadlines while independently valid
fields may update. It does not requalify a value or restart its age. Once the
retention deadline expires, withdraw the field; loss of qualification or a
conflicting identity withholds it immediately. Retention cannot keep an
unqualified or provenance-free legacy value admitted. Return has no accepted
last-known-good observation to retain.

Preserve `Times.received_at` and `receipt_monotonic` from the original retained
observation; caller `evaluated_at` and `evaluate_monotonic` are separate.
Unknown source/phenomenon time stays absent. Evaluation or publication must not
restamp receipt. Same-epoch freshness uses elapsed monotonic time; restart or
cache load never promotes a retained value to fresh or qualified. Across epochs,
use the kernel's conservative wall-time/uncertainty rules, otherwise freshness
is `unknown`. A legacy value-only cache cannot reconstruct missing native proof.

SemReg `semreg/v1/types.go` defines the independent Quality axes, Times and
FreshnessPolicy; `semreg/v1/thermal_unknown_zero_test.go` pins valid zero versus
unknown and rejection without loss of prior state. The public docs-semantic
contracts are `api/v1/kernel.md` and `api/v1/packs/thermal-hvac-v1.md`. No accepted
numeric Thermal FreshnessPolicy for this boiler slice is supplied. Lifetimes
and policy identity remain **Unknown**, owned by downstream M15; admission must
stay withheld until that policy exists. Do not reuse the old mirror age as a
boiler-temperature lifetime.

SemReg `semreg/v1/projection/types.go` defines loss kinds separately from
outcomes. Qualified valid flow can be numerically exact, but projecting only a
scalar to a legacy surface drops native identity, provenance, time and policy
unless conveyed separately: account for `identity`, `provenance`, `time` and
`policy` loss explicitly in separate legacy-scalar accounting. These losses do
not belong to the `target:semantic-snapshot-read` report, which copies source
records intact without transformation. Do not call the legacy scalar projection
exact merely because Celsius matches. Reject invalid/out-of-bounds samples with
their reasons in raw/quality evidence, never clamp them (which would hide range
loss). If an eligible retained fact is emitted, its projection determines the
disposition;
use `withheld` only when the requested item is not projected. The
[snapshot projection accounting contract](../api/semantic-snapshot-read.md#projection-accounting-and-deterministic-order)
requires one disposition per `(kind,item_id)`, collecting all matching complete
FactKeys in `source_keys`. Flow and the reserved return role share
`thermal.measurement.water_temperature`; an absent return cannot add a separate
disposition or make the shared item withheld when flow is projected. Return's
qualification remains `unknown`; its missing-source reason describes only the
legacy-field absence outside this report. No return fact is emitted, including
a zero-valued fact, and return must not reuse the flow role. These
loss requirements do not introduce a new projection schema or erase retained
native bytes.

## Examined, not admitted

- [B524 circuit flow](../protocols/vaillant/ebus-vaillant-B524-register-map.md):
  `(OP=0x02, GG=0x02, II=circuit instance, RR=0x0008)` is circuit flow, explicitly
  **not boiler return**.
- B524 system flow `(OP=0x02, GG=0x00, II=0x00, RR=0x004B)` is a distinct
  controller observation with role `temperature:system_flow`. Its use as the
  old boiler-flow mirror does not admit it here. The
  [existing typed map](fixtures/vaillant-semreg-thermal-map-v1.json) explicitly
  forbids substituting B509 for B524 rows; neither direction supplies identity
  equivalence. Excluding this mirror from the proposed boiler-flow mapping is
  an **intentional difference**, not an unresolved source-equivalence claim.
  Without an eligible qualified B509 observation, new boiler flow is withheld.
  Whether the legacy mirror remains on its existing surface or is removed is
  an open M15 / gateway #952 decision; this page does not resolve it.
- [OP06 controller-mediated selectors](../protocols/vaillant/ebus-vaillant-B524-register-map.md#op0x06--controller-mediated-device-parameters)
  remain a different namespace. Their unproven layouts/meanings do not supply
  either boiler temperature.
- B509 selector `39 00` (`0x3900`) is a setpoint candidate, with flow-versus-return
  regulation meaning unresolved in the boiler register map. It is not a
  measured return value or a replacement for `18 00`.
- Return-bearing fields in [B511](../protocols/vaillant/ebus-vaillant-B511.md),
  [B512](../protocols/vaillant/ebus-vaillant-B512.md),
  [B514](../protocols/vaillant/ebus-vaillant-B514.md),
  [service 05h](../protocols/ebus-services/ebus-service-05h.md), and
  [service 08h](../protocols/ebus-services/ebus-service-08h.md) belong to other
  service/selector or device-family contexts. They are unqualified for this
  slice. Similar names do not establish an accepted boiler-return source.

## Old/new equivalence acceptance

Only these two boiler fields participate. The downstream producer must compare
the old and new paths on the same synthetic/public observations, with explicit
qualification and evaluation context. No result below is a claimed executed
producer test.

| Case | Existing behavior | Required new behavior / equivalence boundary |
| --- | --- | --- |
| Normal B509 flow read, including valid zero | Decoded flow reaches the legacy pointer. | With exact qualification, accepted policy and valid fresh bytes, identical Celsius and flow identity. Today qualification is missing, so publication is withheld. |
| Partial update | Missing flow preserves the old pointer; return becomes nil on merge. | Retain only independently qualified flow with original receipt/evidence until expiry; return stays withheld. Other successes cannot refresh flow age. |
| B509 failure, no usable mirror | Flow can remain last-known indefinitely. | No flow update; retain only eligible prior observation, then withdraw on expiry. No default or new source. |
| Replacement `00 80` | Decoder can publish `-2048 °C`. | No update; withhold invalid sample, retain only eligible prior evidence until expiry. Intentional difference. |
| No exact qualification | Prefix-selected target can supply legacy flow. | Qualification `unknown`; no flow or return fact. Intentional difference. |
| B524 system-flow mirror | Age-bounded mirror can supply flow when B509 supplies no value; B509 wins within the tick. | Intentional difference: no mirror admitted as boiler flow. Only an eligible qualified B509 last-known-good observation may be retained; otherwise flow is withheld. Retain/remove disposition of the old mirror on the legacy surface remains open for M15 / #952. |
| Cache restoration / restart | Flow and historical return can be restored without source proof; plane reports cache. | Value-only legacy cache cannot admit either field; never reset age or promote qualification/freshness. Proven retained observations require identity and clock/policy reevaluation. |
| Return on live merge | Forced nil; no producer. | No accepted source, no fact, reserved role unpublished, explicit missing-source reason. Equivalent absence, with the cache difference above. |

### Synthetic boundary and transition outcomes

The following are reasoned contract vectors, not device captures or executed
producer tests. `F` means the B509 flow binding above: exact boiler product
identity and routing target, service B5/09, operation 0D, complete selector
`18 00`, qualified response form and DATA2c codec. Bytes below are value bytes
after envelope validation, not complete replies. For the conditional admission
rows only, assume `F` is qualified, a downstream accepted FreshnessPolicy
exists, and the new observation meets its freshness requirements. Those
prerequisites do not exist today; without them, admission remains withheld.

For rejection rows, assume a prior qualified `F` observation with value
`50 °C` (`20 03`), still fresh and within its original retention deadline.
`Retain F` means keep that value, raw evidence, original receipt and deadlines;
the rejected sample produces no fact or refresh. Freshness remains evaluated
from that original receipt, never from this failed acquisition. If no eligible
prior observation exists, the result is withheld; if its deadline has expired,
the explicit expiry row applies. The [snapshot projection accounting
contract](../api/semantic-snapshot-read.md#projection-accounting-and-deterministic-order)
requires exactly one disposition per requested `(kind,item_id)`, with all
matching complete FactKeys in `source_keys`. An emitted retained fact is copied
intact on `target:semantic-snapshot-read`, with outcome `exact` and `loss: []`;
legacy-scalar losses are accounted for separately. A rejected sample has no
separate projection disposition and remains only in raw/quality evidence.

| Case / source and value bytes | Legacy value handling | New value / retention | Freshness | Projection outcome |
| --- | --- | --- | --- | --- |
| F, normal `20 03` | `50 °C` | Accept `50 °C`; replace prior F | Fresh from new receipt under assumed policy | Emit flow `50 °C` |
| F, zero `00 00` | `0 °C` | Accept `0 °C`; replace prior F | Fresh from new receipt under assumed policy | Emit flow `0 °C`, never absence |
| F, lower bound `C0 F9` | `-100 °C` | Accept inclusive `-100 °C`; replace prior F | Fresh from new receipt under assumed policy | Emit flow `-100 °C` |
| F, below lower bound `BF F9` | `-100.0625 °C` can publish | Reject `bounds_exceeded`; retain F | Original F freshness; no refresh | Emit retained flow `50 °C` |
| F, upper bound `80 0C` | `200 °C` | Accept inclusive `200 °C`; replace prior F | Fresh from new receipt under assumed policy | Emit flow `200 °C` |
| F, above upper bound `81 0C` | `200.0625 °C` can publish | Reject `bounds_exceeded`; retain F | Original F freshness; no refresh | Emit retained flow `50 °C` |
| F, replacement `00 80` | `-2048 °C` can publish | Reject replacement; retain F | Original F freshness; no refresh | Emit retained flow `50 °C` |
| F, empty value payload | Minimum width fails; no decoded update | Reject short shape; retain F | Original F freshness; no refresh | Emit retained flow `50 °C` |
| F, one value byte `20` | Minimum width fails; no decoded update | Reject short shape; retain F | Original F freshness; no refresh | Emit retained flow `50 °C` |
| F, three value bytes `20 03 00` | Minimum-width decoder yields `50 °C` from first two bytes if passed through the parser | Reject over-length shape; retain F | Original F freshness; no refresh | Emit retained flow `50 °C`; intentional difference |
| F, complete reply with mismatching selector or echoed operation, otherwise `20 03` | Selector/read parsing precedes decoding; no valid F update is established | Reject binding mismatch; retain F | Original F freshness; no refresh | Emit retained flow `50 °C` |
| F read failure or omitted field in partial update | Old pointer can persist indefinitely | No new value; retain F independently of other fields | Original F freshness; no refresh | Retained flow `50 °C` |
| F retention deadline expires after a failed read | Old pointer has no field expiry | Withdraw F; keep native evidence separately | Expired under original policy | Flow withheld; no scalar |
| F loses qualification or conflicts with current target identity | Legacy family heuristic does not establish exact qualification | Withhold immediately; prior F cannot remain admitted | No fresh promotion; original receipt unchanged | Flow withheld despite an unexpired prior value |
| F `20 03`, no exact qualification or accepted policy (current situation) | Can decode `50 °C` | No admitted value; legacy value cannot seed retention | No admitted fresh observation; policy remains Unknown | Flow withheld; qualification `unknown` when exact qualification is missing |
| B524 `(OP=0x02, GG=0x00, II=0x00, RR=0x004B)`, synthetic f32 `00 00 48 42` (`50 °C`), no eligible F | Age-bounded controller mirror can supply boiler flow | No F update or F retention seed; preserve distinct system-flow evidence | Mirror age does not refresh F | Boiler flow withheld; intentional mirror exclusion |
| Value-only cache restore, flow `50 °C` and historical return `40 °C` | Can restore both pointers before merge clears return | Admit neither; no native proof or eligible retention seed | Unknown; restore cannot restamp receipt | Both fields withheld |
| Return, no accepted source or bytes | Nil on live merge | No value and no last-known-good observation | Unknown; no native receipt | No separate disposition or emitted return fact; qualification `unknown`; legacy-field absence reason `reason.boiler_temperature.return_source_unknown` outside projection accounting |

Rejection and retention are independent: when a retained F becomes stale but
is still within retention, retain its evidence and original age; publish a
scalar only if the accepted downstream policy permits that freshness state.
Otherwise withhold it. No numeric stale or retention interval is established
here. A valid new F observation replaces prior F only after all qualification,
shape, validity and freshness prerequisites pass. All conditional emitted
values above remain subject to the scalar projection losses already listed.

The existing gateway tests `TestRefreshBoilerStatusFast*`,
`TestBoilerStatusRegisterDefinitionsForTier_NoReturnTemperatureMapping`, and
`TestMergeBoilerSnapshotNonDestructive_PartialUpdatePreservesLastKnown` in
`cmd/gateway/semantic_vaillant_test.go` pin the old mirror/retention/return
boundaries. They are implementation evidence, not hardware qualification.
Cutover requires matching admitted values and explicit accounting for every
withheld or withdrawn case above across existing MCP and GraphQL boiler fields;
Portal and HA must preserve the same value/absence meaning. Keep existing MCP
names and GraphQL aliases: all MCP namespaces remain pre-stable until Helianthus
1.0, and this slice grants no stability promise.

## Remaining groups pending

The following remain outside this two-field cutover acceptance:

- System temperatures and other system facts (the separate B524 map retains
  its own scope and qualification gap).
- Circuits, zones, DHW, solar and cylinders.
- Other boiler fields: pump, pressure, modulation, flame and setpoints.
- Operations, writes, capability admission and live authority.

Circuit-zero pump/status observations are not reinterpreted or promoted to
boiler identity. Native qualification and trust safeguards remain in force.
This slice makes no hardware, transport, deployment, release or parent-closure
claim.
