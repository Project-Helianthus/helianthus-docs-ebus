# B524 profile discovery and description baselines

This is the public contract for VRC Explorer's bounded scan policy. It preserves
the native `(OP, GG, II, RR)` identity and distinguishes observed response bytes,
profile-qualified interpretations, and scanner policy. It adds no device writes.

## Local circuit coverage

When OP02/GG02 is selected, include II0A independently of OP00 `circuit_count`.
For example, three discovered ordinary slots `00,01,02` produce the scan selection
`00,01,02,0A`. Deduplicate II0A if it is already selected. This applies to CLI,
interactive planning, replanning, and custom plans; estimates and safety limits
include the extra slot.

The user-facing designation is `virtual_dhw`. Its inferred protocol role remains
**Unknown**: selecting or reading this slot does not confirm an active physical
circuit. Preserve the native selector 0A; historical display `Heating Circuit 11`
was index-plus-one presentation. Do not alias this selector to the separately
documented II09 DHW pseudo-circuit rule.

Sanitized selector evidence on BASV2/SW0507: `0200020a0900` receives
`0202090000007042`, with RR0009 value bytes `00007042` (binary32 60.0);
`0200020a1300` receives `020213000100`, with RR0013 value bytes `0100` (u16 1).
These echoed read responses prove a sparse responsive selector, independently
of the semantic labels assigned by an older mapper.

## OP06 connected-device discovery

OP00 information identifiers do not enumerate OP06 groups. Counts and same-numbered
identifiers never suppress an independently configured device class. The following
table describes the characterized controller profile; names are operation-scoped.

| OP06 GG | Public class | Discovery II bounds | RR0001 interpretation |
| --- | --- | --- | --- |
| 01 | `primary_heating_source` | 01..08 | Profile-qualified native slot availability |
| 02 | `secondary_heating_source` | 01..08 | Profile-qualified fallback-slot availability |
| 09 | `regulator_slot` | 01..0A | Profile-qualified connected/paired Boolean |
| 0A | `thermostat_slot` | 01..0A | Profile-qualified connected/paired Boolean |
| 0C | `functional_modules_vr71` | 01..0A | Connection state, distinct from retained inventory |
| 0E | `clock_slot` | 01..0A | Observed Boolean connection candidate |
| 0F | `base_station_slot` | 01..0A | Observed Boolean connection candidate |

The heat-source bound follows the pinned KNX implementation already documented
in the [register map](ebus-vaillant-B524-register-map.md); it does not establish
eight populated slots or all models' maxima. The additional device classes retain
the bounded controller-profile qualification. Group names alone do not identify
physical radio, outdoor-sensor, or gateway hardware. Such correlations require
independent identity evidence; no radio stack is implemented by this policy.

### Unqualified VR70 presentation candidate

The operator-provided display designation `OP=0x06, GG=0x0B` = **Functional
Modules (VR70)** is outside this characterized discovery profile. It supplies no
slot schema, product identity, discovery limit, or liveness predicate. Do not add
it to a scan plan or apply the `GG=0x0C` policy until a profile-qualified contract
supports it. The `functional_modules_vr71` class remains specific to `GG=0x0C`.

Sanitized BASV2 observations for GG09/0A/0C/0E/0F have RR0001 raw `00` at II00,
`01` at II01, and `00` at II02 through II0A. Starting a first-empty scan at II00
would miss II01. The captured RR1 result is independent from an older artifact's
generic `present=true`, which also appeared on disconnected slots.

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
GG08's RR1 is an unknown status byte; it has no qualified connected-device predicate.

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
