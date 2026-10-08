# B524 profile discovery and description baselines

This is the public contract for VRC Explorer's bounded scan policy. It preserves
the native `(OP, GG, II, RR)` identity and distinguishes observed response bytes,
profile-qualified interpretations, and scanner policy. It adds no device writes.

## Local circuit coverage

For OP02/GG02, the current profile is II01..II09: II01..II08 are ordinary
heating-circuit candidates and II09 is the virtual native-water circuit. The
OP00 `circuit_count` can guide which of II01..II08 are probed, but does not add
II00 or II0A. II09 remains a separately selected candidate. This applies to
CLI, interactive planning, replanning, and custom plans; estimates and safety
limits include II09.

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
synthetic slot. An instanced group remains a navigation node when it has no
present child instances; only its instance children are filtered.

Custom scan plans enforce the same selector intervals before transport I/O:
OP06 permits II01..II08 and OP02/GG02 permits II01..II09. Custom RR selectors
remain exact and are validated by the scalar request contract; they do not widen
an II interval. Historical records outside these intervals remain raw artifact
diagnostics and never become Browser nodes.

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

OP02/GG06 and GG07 presentation names do not establish additional
characterized local scan routes. Other research routes retain their separately
configured bounds rather than inheriting the same-numbered OP06 identity.

The current circuit availability heuristic uses OP02/GG02/RR0002. A
correlated active, visible numeric zero is not rejected solely because it is
zero: the visible attribute supplies additional positive profile evidence.
This is an implementation qualification rule, not a universal physical
presence predicate. Existing nonzero candidates and the separate II09 probe
are retained; errors and invalid sentinel values remain non-positive.

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
| 08 | `solar_module_slot` | 01..08 | Profile-qualified device-connected Boolean |
| 09 | `regulator_slot` | 01..08 | Profile-qualified connected/paired Boolean |
| 0A | `thermostat_slot` | 01..08 | Profile-qualified connected/paired Boolean |
| 0C | `functional_modules_vr71` | 01..08 | Connection state, distinct from retained inventory |
| 0E | `clock_slot` | 01..08 | Observed Boolean connection candidate |
| 0F | `base_station_slot` | 01..08 | Observed Boolean connection candidate |

For this profile, every OP06 GG admitted by a scan plan uses the common candidate
slot interval II01..II08. II00, II09, and II0A are outside that interval. This
does not create a group route, a device-presence claim, or an RR0001 predicate
for groups whose semantics remain unknown.

**Hypothesis:** independent protocol evidence is required for this interpretation.

### Unqualified VR70 presentation candidate

The operator-provided display designation `OP=0x06, GG=0x0B` = **Functional
Modules (VR70)** is outside this characterized discovery profile. It supplies no
slot schema, product identity, discovery limit, or liveness predicate. This display
mapping does not establish additional qualified scan targets or bounds; exploratory
probing remains separately qualified. Do not apply the `GG=0x0C` policy until a
profile-qualified contract supports it. The `functional_modules_vr71` class remains
specific to `GG=0x0C`.

The other names in the OP06 presentation-name catalog are subject to the same
boundary unless a row already appears in the table above with its own qualified
route. In particular, `unused` for GG04 does not justify suppressing a probe
that an independently qualified profile requires.

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

## Descriptions for every eligible parameter

Use `DescribeParameter` (OP01) for `GetParameter` (OP02) and
`DescribeDeviceParameter` (OP07) for `GetDeviceParameter` (OP06). Read the parameter
first and keep its complete selector and profile context. A qualified writable
attribute selects a description candidate; it does not authorize a device write.
Descriptions cover numeric, Boolean, enum, date, time, and other eligible formats,
including unknown codecs whose responses remain raw and unqualified.

Recommended/custom retain a default logical description budget 256. Extended
`full`/`research` plan every eligible parameter, with a finite 100000 logical cap
and a default 10000 actual B524-send cap including retries. Explicit smaller budgets
remain available. Fair family reservations protect OP07 first attempts from OP01
retries and vice versa. Report eligible, planned, attempted, received, interpreted,
unavailable, unqualified, and omitted descriptions separately. Omission or unknown
results do not establish exhaustive coverage.

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

## Explorer description progress and browser presentation

Describe acquisition selects only active writable scalar parameters, in both
OP02 and OP06. Read-only parameters do not generate OP01/OP07 requests. The
Describe progress bar starts with the scheduled request count and increases its
total for actual retries; interrupted or exhausted acquisition does not report
successful completion.

The CLI Browser exposes only Config and State. Writable OP06 parameters belong
in Config, as do the retained description/limit records. Native addresses remain
in artifacts and row models; the table displays `semantic_name (0xNNNN)` or
`0xNNNN` when no semantic name exists, without a separate Address column.
