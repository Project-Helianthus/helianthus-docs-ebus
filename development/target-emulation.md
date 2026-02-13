# Target Emulation (Identify-Only Profiles)

This document tracks implemented Helianthus target-emulation behavior merged in:

- `helianthus-ebusgo` PR [#61](https://github.com/d3vi1/helianthus-ebusgo/pull/61) and PR [#65](https://github.com/d3vi1/helianthus-ebusgo/pull/65)
- `helianthus-tinyebus` PR [#10](https://github.com/d3vi1/helianthus-tinyebus/pull/10) and PR [#14](https://github.com/d3vi1/helianthus-tinyebus/pull/14)

## Licensing Boundary

- Protocol-generic field/layout docs stay in **CC0** under `protocols/`.
- Helianthus API names, presets, smoke commands, and package mapping stay in this **AGPL** page.

CC0 references for wire-level model:
- `protocols/ebus-overview.md#identification-scan-0x07-0x04`
- `protocols/ebus-overview.md#identify-only-profile-fields-generic`

## Identify-Only Model (Helianthus API Surface)

Both implementations expose the same logical identify-only constructor profile:

- target identity: `address`, `manufacturer`, `device_id`, `software`, `hardware`
- response behavior: fixed response delay + timing envelope validation
- single recognition rule: match identification query `PB=0x07`, `SB=0x04`

Current implementation constraints:

- identify-only behavior responds only to `0x07 0x04`
- no thermostat/write/register emulation in this profile
- `device_id` is normalized to a 5-byte ASCII slot (trim + truncate/pad)

## Supported Presets (Current Coverage)

| Preset | Address | Manufacturer | Device ID | Software | Hardware | Scope |
|---|---:|---:|---|---:|---:|---|
| VR90 | `0x15` | `0xB5` | `B7V00` | `0x0422` | `0x5503` | identify-only recognition |
| VR_71 | `0x26` | `0xB5` | `VR_71` | `0x0100` | `0x5904` | identify-only recognition |

Known limits:

- Presets are fixed defaults for recognition tests, not full device models.
- Additional profiles can be created through the generic constructor, but only identify behavior is implemented.
- Timing accuracy expectations remain firmware-first for strict response windows.

## Implementation Mapping

### `helianthus-ebusgo`

- Package: `emulation`
- Generic API:
  - `NewIdentifyOnlyTarget(profile IdentifyOnlyProfile)`
  - `PresetVR90IdentifyOnlyProfile()`
  - `PresetVR71IdentifyOnlyProfile()`
- Compatibility API:
  - `NewVR90Target(profile VR90Profile)` (kept for backward compatibility)

Smoke commands:

```bash
cd /path/to/helianthus-ebusgo
./scripts/smoke-identify-only.sh
./scripts/smoke-vr90-minimal.sh
```

Repository links:

- https://github.com/d3vi1/helianthus-ebusgo/blob/main/scripts/smoke-identify-only.sh
- https://github.com/d3vi1/helianthus-ebusgo/blob/main/scripts/smoke-vr90-minimal.sh

### `helianthus-tinyebus`

- Package: `firmware/emulation`
- Generic API:
  - `NewIdentifyOnlyTarget(profile IdentifyOnlyProfile)`
  - `PresetVR90IdentifyOnlyProfile()`
  - `PresetVR71IdentifyOnlyProfile()`
- Compatibility API:
  - `NewVR90Target(profile VR90Profile)` (kept for backward compatibility)

Smoke commands:

```bash
cd /path/to/helianthus-tinyebus
./scripts/smoke-vr90-minimal.sh vr90
./scripts/smoke-vr90-minimal.sh vr71
./scripts/smoke-vr90-minimal.sh all
```

Repository link:

- https://github.com/d3vi1/helianthus-tinyebus/blob/main/scripts/smoke-vr90-minimal.sh

## Timing Rationale

For strict target emulation, timing should run firmware-side (adapter MCU / TinyGo runtime) where response delay control is predictable.

Host-side relay paths (for example `ebusd-tcp`) are still useful for functional checks but can add scheduler/network jitter, so they should not be treated as cycle-accurate emulation backends.

See also: `protocols/ebusd-tcp.md#timing-caveat-for-target-emulation`.

## Out of Scope (Current Phase)

The following remain out of scope for the identify-only profile abstraction:

- full VR90 thermostat command coverage beyond identify
- full VR_71 command/register behavior beyond identify
- VR92, VR70, recoVAIR, VR50 full emulation
