# Target Emulation (VR90 Minimal)

This document tracks implemented Helianthus target-emulation behavior merged in:

- `helianthus-ebusgo` PR [#61](https://github.com/d3vi1/helianthus-ebusgo/pull/61)
- `helianthus-tinyebus` PR [#10](https://github.com/d3vi1/helianthus-tinyebus/pull/10)

## Licensing Boundary

- Protocol-generic wire behavior and query layouts stay in **CC0** docs under `protocols/`.
- This page is **AGPL** and documents Helianthus implementation details (package structure, harness behavior, and project smoke commands).

## Framework Shape (Generic Concepts)

Both implementations use the same logical model:

- request matcher (`PB/SB` and optional payload prefix matching),
- response builder (returns delay + response payload),
- timing constraints (min/max response delay validation),
- deterministic harness (virtual time sequence runner for tests).

## Minimal VR90 Behavior (Current Scope)

Current behavior is intentionally minimal and limited to recognition:

- responds to identification query `0x07 0x04`,
- configurable target address,
- configurable identity fields: manufacturer, device id, software version, hardware version,
- no extended thermostat command coverage in this phase.

For the protocol-level query layout, see:
- `protocols/ebus-overview.md#identification-scan-0x07-0x04`
- `protocols/ebus-overview.md#minimal-vr90-recognition-query-set-observed`

## Implementation Mapping

### `helianthus-ebusgo`

- Package: `emulation`
- Entry point: `NewVR90Target(profile VR90Profile)`
- Deterministic harness: `Harness` with virtual `time.Duration`

Minimal smoke command:

```bash
cd /path/to/helianthus-ebusgo
./scripts/smoke-vr90-minimal.sh
```

### `helianthus-tinyebus`

- Package: `firmware/emulation`
- Entry point: `NewVR90Target(profile VR90Profile)`
- Deterministic harness: `Harness` with millisecond virtual time (`uint32`)

Minimal smoke command:

```bash
cd /path/to/helianthus-tinyebus
./scripts/smoke-vr90-minimal.sh
```

## Timing Rationale

For strict target emulation, timing should run firmware-side (adapter MCU / TinyGo runtime) where response delay control is predictable.

Host-side relay paths (for example `ebusd-tcp`) are still useful for functional checks but can add scheduler/network jitter, so they should not be treated as cycle-accurate emulation backends.

See also: `protocols/ebusd-tcp.md#timing-caveat-for-target-emulation`.

## Out of Scope (Current Phase)

The following devices/behaviors are not included in this minimal phase:

- VR92
- VR70 / VR71
- recoVAIR
- VR50
