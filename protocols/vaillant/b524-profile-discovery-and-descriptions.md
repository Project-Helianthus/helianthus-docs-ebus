# B524 profile discovery and description baselines

This is the public contract for VRC Explorer's bounded scan policy. It preserves
the native `(OP, GG, II, RR)` identity and distinguishes observed response bytes,
profile-qualified interpretations, and scanner policy. It adds no device writes.

## Local circuit coverage

For OP02/GG02, the current profile is II01..II09: II01..II08 are ordinary
heating-circuit candidates and II09 is the virtual native-water circuit. The
legacy public name `circuit_count` for OP00/ID00 is a supported-capacity value
under the bounded contract below; it does not select or allocate II identities.
It does not add II00 or II0A, and II09 remains a separately selected candidate.
This applies to CLI, interactive planning, replanning, and custom plans;
estimates and safety limits include II09.

`virtual_native_water` is a presentation label, not a physical-circuit claim.
The selector is shown only after positive presence evidence. A historical trace
contains responsive II0A reads; retain that raw evidence in its artifact, but
do not turn it into the current profile's circuit range or Browser tree.

The Browser tree is a present-instance view: it contains only selectors with
group-qualified positive evidence. For current artifacts this is
`present=true`; a legacy artifact without that field may retain a successful
observed raw reply. `not_connected`, empty, timeout, decode failure, and
unprobed/unknown selectors remain in the scan artifact diagnostics; none becomes
a placeholder node. Tree projection does not alter the artifact or create a
synthetic slot. The final scan plan controls Browser group visibility independently
for each operation: deselected groups are omitted, while an explicitly selected
empty group may remain a navigation node without instance children. Discovery
results outside that plan remain in the artifact. Artifacts predating scan-plan
metadata retain their legacy group visibility.

Custom scan plans enforce the same selector intervals before transport I/O:
OP06 permits II01..II08 and OP02/GG02 permits II01..II09. Custom RR selectors
remain exact and are validated by the scalar request contract; they do not widen
an II interval. A group without an observed RR scheduling ceiling is selectable
only with an explicit custom RR ceiling, list, or range. Historical records outside these
intervals remain raw artifact diagnostics and never become Browser nodes.

## Explicit instance intervals

The following are current scanner profile bounds, not a claim that every
candidate exists. Artifacts record `ii_min` and `ii_max` separately from
positive presence observations; planner and discovery output expose the same
interval. A count from OP00 never changes the numbering origin.

| OP | GG | II_min | II_max | Scope |
| --- | --- | --- | --- | --- |
| 02 | 00, 01 | 00 | 00 | Singleton selectors |
| 02 | 02 | 01 | 09 | Heating candidates 01..08, virtual native water 09 |
| 02 | 03 | 00 | 0A | Current zone profile bound |
| 02 | 04, 05 | 00 | 01 | Current solar/cylinder profile bound |
| 02 | 08, 09, 0A | 00 | 0A | Current configured bounds; GG0A remains semantically unknown |
| 06 | Every admitted GG | 01 | 08 | Independent remote-device candidate interval |

The planner inventories every known local group (including OP02/GG0A, whose
semantic role remains Unknown) and every named OP06 family. All known rows
remain visible and manually selectable even with zero confirmed instances. It
shows an unprobed group separately from a group with zero confirmed-present
instances. Neither state suppresses selection in a custom plan. OP02/GG06 and
GG07 retain their presentation names, but their instance and RR layout remain
Unknown and require an explicit custom RR scope. OP06/GG04 and OP06/GG0D likewise require
a manual RR scope because their RR maxima are Unknown. `recommended`, `full`,
`research`, and `custom` retain their own selector policies. Same-numbered OP06
groups never supply their local selector contract.

The current circuit availability heuristic uses OP02/GG02/RR0002. A
correlated active, visible numeric zero is not rejected solely because it is
zero: the visible attribute supplies additional positive profile evidence.
This is an implementation qualification rule, not a universal physical
presence predicate. Existing nonzero candidates and the separate II09 probe
are retained; errors and invalid sentinel values remain non-positive.

### Recommended OP00 count guidance

The following are **profile-qualified planner mappings**, not wire-level group
identity. They apply only to `recommended`. A concrete presence predicate still
confirms every instance. `full`, `research`, and `custom` retain their own
selector policy.

For OP00/ID00 `circuit_count` and ID01 `zone_count`, the legacy public names
are retained, but their supported meaning is capacity, not configured or
present-instance cardinality. The following six combinations are the complete
supported contract:

| VR70 count | VR71 count | Circuit capacity | Zone capacity |
| --- | --- | --- | --- |
| 0 | 0 | 1 | 1 |
| 1 | 0 | 2 | 2 |
| 0 | 1 | 3 | 3 |
| 1 | 1 | 5 | 5 |
| 2 | 1 | 7 | 7 |
| 3 | 1 | 8 | 8 |

Do not extrapolate this table to another hardware mix or treat it as a global
capacity model. In particular, two configured or confirmed circuits with
circuit capacity `3`, and two configured or confirmed zones with zone capacity
`3`, are normal and are not mismatches. Capacity never creates, removes,
orders, or makes II slots contiguous; each candidate must pass its concrete
group predicate. II09 remains independent of `circuit_count`.

The two capacity values are recommendations for bounded candidate planning
only. They never construct instances. A missing, malformed, conflicting, or
otherwise unknown capacity remains separately recorded and uses the group's
qualified predicate. It does not by itself make concrete presence qualification
incomplete.

Every other mapped OP00 count retains count-guided cardinality semantics: a
valid count guides candidate generation, and a valid zero suppresses only
derived default candidates. It never erases an explicit positive observation.
A missing, malformed, conflicting, or otherwise unknown count falls back to
the group's qualified predicate and leaves count-guided coverage incomplete.

| OP/GG | OP00 ID | Count name | Scope of the hint |
| --- | --- | --- | --- |
| OP02/GG02 | 00 | `circuit_count` | Supported circuit capacity; candidate guidance only. II01..II08 retain their concrete predicate, and II09 is independent. |
| OP02/GG03 | 01 | `zone_count` | Supported zone capacity; candidate guidance only. II00..II0A retain their concrete predicate. |
| OP02/GG04 | 02 | `solar_circuit_count` | Local solar-circuit candidates. |
| OP02/GG05 | 03 | `solar_loaded_tank_count` | Local cylinder candidates. |
| OP02/GG08 | 0B | `delta_t_count` | Local DeltaT candidates. |
| OP02/GG09 | 10 | `recovair_count` | II00 only in `recommended`; zero avoids derived default slots. |
| OP06/all confirmed slots | 04 | `device_count` | Aggregate comparison; never GG06, membership, or a cutoff. |
| OP06/GG01 | 0C | `boiler_count` | Cardinality only. |
| OP06/GG02 | 0D | `heat_pump_count` | Cardinality only. |
| OP06/GG06 | 0F | `vpm_s_count` | Cardinality only. |
| OP06/GG07 | 0E | `vpm_w_count` | Cardinality only. |
| OP06/GG09 | 0A | `remote_control_count` | Cardinality only. |
| OP06/GG0B | 08 | `vr70_count` | Cardinality only. |
| OP06/GG0C | 09 | `vr71_count` | Cardinality only. |

There is no count mapping for OP06/GG03, GG05, GG08, GG0A, GG0D, GG0E, or
GG0F: use their qualified presence predicate. There is also no OP00 ID05
generator mapping and no ID17 cooling-group mapping. Remote hints are neither
device identities nor a reason to stop on an unconfirmed count. Solar discovery
requires a visible, finite EXP value at RR0004. A hidden default temperature is
an unknown slot observation, not positive presence. Empty responses and failed
local probes are likewise unknown, never present.

## Native DHW discovery

The complete OP02/GG00 System scope (II00, RR0000..00FF) is mandatory in
`recommended`. Native DHW admission always probes its gate and includes the
complete GG01 RR0000..0013 scope after a positive result.

OP02/GG01 uses only II00. For this profile, `RR0001` qualifies native DHW
presence only when a correlated read decodes as an exact two-byte UIN value
that is nonzero. Zero is `not_present`; an empty, wrong-width, NACK, decode
failure, or unmatched result is `unknown`. This predicate is independent of
the OP01 descriptions scheduled for RR0000..RR0013 and does not make a
description response a presence result.

## OP06 connected-device discovery

OP00 information identifiers do not enumerate OP06 groups. Counts and same-numbered
identifiers never suppress an independently configured device class. The following
table describes the characterized controller profile; names are operation-scoped.
The wider [OP06 presentation-name catalog](ebus-vaillant-B524.md#34-op06-family-presentation-name-catalog)
is a hypothesis catalog, not an expansion of this discovery policy.

| OP06 GG | Public class | Discovery II bounds | RR0001 interpretation |
| --- | --- | --- | --- |
| 01 | `primary_heating_source` | 01..08 | Profile-qualified native slot availability |
| 02 | `secondary_heating_source` | 01..08 | Profile-qualified fallback-slot availability |
| 03 | `air_recovery_slot` | 01..08 | Candidate only; concrete Boolean required per slot |
| 04 | `unused` | 01..08 | Unknown; no predicate is established |
| 05 | `appliance_interface_slot` | 01..08 | Candidate only; concrete Boolean required per slot |
| 06 | `solar_pump_module_slot` | 01..08 | Candidate only; concrete Boolean required per slot |
| 07 | `water_pump_module_slot` | 01..08 | Candidate only; concrete Boolean required per slot |
| 08 | `solar_module_slot` | 01..08 | Profile-qualified device-connected Boolean |
| 09 | `regulator_slot` | 01..08 | Profile-qualified connected/paired Boolean |
| 0A | `thermostat_slot` | 01..08 | Profile-qualified connected/paired Boolean |
| 0B | `functional_modules_vr70` | 01..08 | Candidate only; concrete Boolean required per slot |
| 0C | `functional_modules_vr71` | 01..08 | Connection state, distinct from retained inventory |
| 0D | `relay_module_slot` | 01..08 | `device_present`: exact one-byte BOOL at RR0001 |
| 0E | `clock_slot` | 01..08 | Observed Boolean connection candidate |
| 0F | `base_station_slot` | 01..08 | Observed Boolean connection candidate |

For this profile, every OP06 GG admitted by a scan plan uses the common candidate
slot interval II01..II08. II00, II09, and II0A are outside that interval. A
generic IIFFh DescribeDeviceParameter response for RR0001 supports the Boolean
format for the named candidate classes, but does not identify a concrete slot.
Only a complete, correlated concrete-II Boolean result can mark that slot
present or not connected. In particular, `false` does not create eight device
instances and does not erase retained identity evidence. Catalog visibility
does not create a group route, a device-presence claim, or a change to
conservative recommended admission.

**Hypothesis:** independent protocol evidence is required for this interpretation.

`unused` for GG04 does not justify suppressing a probe that an independently
qualified profile requires. GG04 retains Unknown RR layout and presence
semantics. GG0D retains Unknown RR maximum, but its qualified RR0001 predicate
must be probed.

Historical BASV2 observations for GG09/0A/0C/0E/0F include RR0001 raw `00` at
II00, `01` at II01, and `00` at later historical selectors. They explain why
the current profile begins at II01; they do not expand its upper bound beyond
II08. The captured RR1 result is independent from an older artifact's generic
`present=true`, which also appeared on disconnected slots.

For `recommended`, begin at II01 and probe sequentially to the first complete,
correlated Boolean false: `first_confirmed_absence` means **not connected at that
slot**, not absence of physical hardware or retained identity. Record the stopping
frontier. This is a bounded coverage policy, not proof of packed physical topology.
`full` and `research` retain the complete configured audit interval. A missing
terminal negative at the bound leaves discovery incomplete.

Keep `connected`, `not_connected`, `unknown`, and unprobed slots distinct.
Timeout, NACK, empty/status-only response, decode/echo failure, unsupported format,
or exhausted budget never supplies a false Boolean. Unknown results do not stop
the next probe and leave discovery incomplete. Readable RR0002..0004 can establish
inventory evidence, but do not override RR0001 false to mean connected. Historical
GG0C observations include both connection states while retaining module identity.
For GG08, a correlated RR0001 BOOL false means not connected. Readable identity or header registers do not override that result. A non-Boolean payload or failed decode remains unknown and cannot establish a present device.

### GG0D relay-module predicate

For OP06/GG0D (VR41 presentation family), probe II01..II08 at RR0001 even
though its RR maximum is Unknown. Its group-specific name is `device_present`,
which overrides the generic `device_connected` header name: there is no header
fallback. An exact one-byte BOOL `00` is `not_present` and `01` is `present`.
Values `02..FF`, wrong-width bodies, empty replies, NACK, decode failure, and
unmatched replies are `unknown`. Keep `present`, `not_present`, and `unknown`
separate from `connected`; this predicate does not establish a connection
state, identity, or an RR limit.

## Descriptions for every eligible parameter

Use `DescribeParameter` (OP01) for `GetParameter` (OP02) and
`DescribeDeviceParameter` (OP07) for `GetDeviceParameter` (OP06). Read the parameter
first and keep its complete selector and profile context. A qualified writable
attribute selects a description candidate; it does not authorize a device write.
Descriptions cover numeric, Boolean, enum, date, time, and other eligible formats,
including unknown codecs whose responses remain raw and unqualified.

The scan plans every eligible writable parameter in its selected scope. Callers
may apply an explicit request limit, but a limit, retry, omission, or unknown
result must be reported separately and never establishes exhaustive coverage.
Report eligible, planned, attempted, received, interpreted, unavailable,
unqualified, and omitted descriptions separately.

The normalized response is `GG RRlo RRhi MIN MAX STEP`, with three equal-width
spans. Decode it using the correlated parameter codec, never a response-length
datatype guess. For HDA:3 and numeric-byte HTI, decoded limits can qualify format
and range, while STEP encoding remains **Unknown**. Preserve `step_raw_hex` and
`step=null`; do not manufacture a day count or time duration. Offline changes can
be rejected for invalid format or known range, but are not fully validated when
STEP is unknown. This corrects the historical synthetic HDA day-step assumption.

## Bundled metadata and rechecking

The distributed schema contains sanitized observed baseline descriptions. Each
row keeps read/description operations, GG, II, RR16, model/firmware and API profile,
codec/width, known minimum/maximum/step, decoder revision and qualification scope.
Missing data remains unknown. Serial numbers, addresses, endpoints and original
captures are excluded. An interrupted scan may supply valid individual rows while
its exported coverage remains explicitly incomplete.

HTML and offline browse show `Bundled` separately from current-target descriptions:

| State | Meaning |
| --- | --- |
| `not_verified` | Matching baseline profile; no current-target recheck |
| `matches` | Current correlated description agrees with bundled fields |
| `differs` | Current description differs; keep both and use current evidence |
| `unavailable` | Recheck failed or remained unqualified; retain baseline as prior evidence |
| `profile_mismatch` | Relevant profile changed/unknown; baseline is not applicable verification |

The profile also retains the observed controller-slot class and firmware when
available. OP06 rows require the selected slot's own class and firmware bytes;
missing or changed device identity cannot qualify that slot's prior baseline.
Recompute annotations on model, firmware or relevant API-profile changes. Never
reuse a row across operations or instances or promote another profile's limits
to confirmed validation for device writes. Bundled observations remain prior
evidence even when their profile matches. Current read-only scans provide the
optional recheck; offline viewing sends no eBUS requests.

## Generic IIFFh description catalog

`DescribeParameter` and `DescribeDeviceParameter` replies echo GG and RR16 but
do not echo II. A response requested with II=FFh is therefore a generic class
observation, not a concrete-instance verification. Keep this catalog separate
from the concrete bundled baseline and never use it for device identity,
presence, or edit validation.

The Explorer stores qualified generic rows with
`qualification=generic_class_observation`,
`scope=generic_instance_class`, and
`device_identity_verified=false`. The catalog keeps controller-profile context
only; it does not carry a selected device identity. It is deliberately excluded
from the concrete baseline attachment and from edit validation. Raw responses
whose codec cannot be qualified are excluded from this public catalog.

The sanitized remote common-header samples use selectors
`(OP06, GG, IIFF, RR0001..0003)` and return the following OP07 bodies after the
echoed `GG RRlo RRhi`: `00 01 01` for `device_connected` (BOOL), `00 FF 01`
for `device_class_address` (UCH), and `00 01 01` for `device_error_code`
(UCH). They establish decoded class-level format/range evidence only. A
description for a named parameter beyond the common header has the same
limitation unless a concrete-II request independently verifies it.

The generic catalog contains 223 decoded IIFFh class descriptions. It neither
establishes a terminal RR maximum nor includes the 198 correlated raw responses
whose codec remains unqualified.

## Observed OP06 scan windows

The planner's scheduling windows combine correlated read and Describe evidence;
they are not properties of the generic IIFFh catalog alone. The sanitized
[OP06 observed-window fixture](fixtures/b524-op06-observed-windows-v1.json)
preserves representative payload-only requests and replies without endpoint,
serial, or capture metadata.

| OP06 groups | Observed scheduling window | Evidence boundary |
| --- | --- | --- |
| 01, 02, 03, 05, 06, 07, 08, 0B, 0C | RR0000..002F | bounded correlated read/Describe observations |
| 09, 0A | RR0000..0035 | bounded correlated read/Describe observations |
| 0E, 0F | RR0000..0033 | bounded correlated reads; RR0033 is a read-only observation, while the matching generic Describe body remains unqualified |
| 04, 0D | Unknown | explicit custom RR scope only |

These windows are observed scheduling ceilings, never terminal maxima. In
particular, a read-only state register can exist above the highest qualified
Describe response.

## Explorer description progress and browser presentation

Describe acquisition selects only active writable scalar parameters, in both
OP02 and OP06. Read-only parameters do not generate OP01/OP07 requests. The
Describe progress bar starts with the scheduled request count and increases its
total for actual retries; interrupted or exhausted acquisition does not report
successful completion.

Config and State tabs apply only to OP02/OP06 scalar register selections.
OP00 shows system information directly, without those tabs. Writable OP06
parameters belong in Config, as do the retained description/limit records. Native addresses remain
in artifacts and row models; the table displays `semantic_name (0xNNNN)` or
`0xNNNN` when no semantic name exists, without a separate Address column.
