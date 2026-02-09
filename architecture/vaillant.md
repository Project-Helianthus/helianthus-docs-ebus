# Vaillant Regulator Architecture Notes (eBUS Context)

Modern Vaillant systems often use an architectural approach that differs from the “classic” eBUS expectation of **one physical device ↔ one slave address**.

This document captures the implications for discovery, debugging, and third‑party integrations. It is intentionally **high-level**; for wire formats, see `protocols/vaillant.md`.

## The Architectural Difference (Classic eBUS vs Vaillant)

### Classic eBUS mental model (illustrative)

- Each physical device appears as its own slave address on the bus.
- Distinct subsystems (heating circuit, DHW, mixer modules, zone controllers) are typically represented as separate nodes.
- Bus scans show the “shape” of the system without vendor-specific application protocols.

Example (illustrative):

```text
Address  Device
-------  ----------------------
0x10     Room controller (master)
0x25     DHW circuit module
0x26     Heating circuit 1 module
0x27     Heating circuit 2 module
0x30     Zone thermostat 1
0x31     Zone thermostat 2
```

### Vaillant regulator model (as seen with B524)

In Vaillant’s regulator-centric approach, a single logical endpoint (the regulator) can expose many internal “subsystems” via a proprietary selector space. With `0xB5 0x24` (B524) this commonly looks like:

- One eBUS device address (the regulator) is the entry point.
- “Groups” (`GG`) and “instances” (`II`) multiplex internal circuits/zones/DHW/sensors behind that address.
- The bus topology does not directly reveal how many circuits/zones exist; that information is recovered by understanding and probing the vendor selector space.

## Why This Is Operationally Problematic

### Reduced bus transparency

- In classic eBUS setups, a scan of slave addresses approximates the physical topology.
- In Vaillant’s regulator model, a bus scan can look like a small system even when the internal topology is large, because many subsystems are “hidden” behind selectors.

### More difficult debugging

- Traffic for distinct subsystems can share the same eBUS address and primary/secondary bytes.
- Logs require additional context (selectors like `GG/II/RR` for B524) to understand which internal subsystem a transaction targets.

### Breaks the “one device, one address” intuition

Illustrative comparison:

```text
Classic eBUS style:
  master -> 0x26 (HK1)
  master -> 0x27 (HK2)
  master -> 0x25 (DHW)

Vaillant regulator style (selector-multiplexed):
  master -> <regulator address> group=0 (HK1)
  master -> <regulator address> group=1 (HK2)
  master -> <regulator address> group=3 (DHW)
```

## Possible Motivations (Speculative)

These are hypotheses; the intent cannot be proven from bus traffic alone.

- **Address economy:** eBUS address space is finite; multiplexing allows large logical systems while consuming fewer bus addresses.
- **Backward compatibility:** preserving an existing internal architecture avoids redesigning an installed ecosystem.
- **Centralized control:** the regulator remains the “brain” coordinating zones/circuits, rather than distributing autonomy to multiple independent nodes.
- **Ecosystem control / lock-in effects:** proprietary selector spaces increase the cost of third‑party integrations and replacements.

## Consequences for Users and Integrators

In practice, Vaillant’s approach often implies:

- You cannot infer internal topology (e.g., number of zones/circuits) from address scans alone.
- Tooling must implement vendor-specific probing to discover groups/instances/register maps.
- “Generic eBUS” tooling may require significant configuration (or reverse engineering) to expose meaningful per-zone/per-circuit data.

## What This Means for Helianthus Tooling

Helianthus should model Vaillant regulator subsystems as **logical components** rather than pretending they are separate eBUS addresses:

- Treat `(address, GG, II, RR)` (and opcode family) as the effective “address” for many values.
- Ensure traces/logs are annotated with the operation name and selector context (e.g., “Reading GG=0x03 II=0x01 RR=0x0016”).
- Prefer surfacing group/instance semantics in UI and artifacts (e.g., group names + instance counts), because the bus topology alone is insufficient.

