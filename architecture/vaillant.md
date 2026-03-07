# Vaillant Regulator Architecture Notes (eBUS Context)

Modern Vaillant systems often use an architectural approach that differs from the “classic” eBUS expectation of **one physical device ↔ one target address**.

This document captures the implications for discovery, debugging, and third‑party integrations. It is intentionally **high-level**; for wire formats, see `protocols/ebus-vaillant.md`.

## The Architectural Difference (Classic eBUS vs Vaillant)

### Classic eBUS mental model (illustrative)

- Each physical device appears as its own target address on the bus.
- Distinct subsystems (heating circuit, DHW, mixer modules, zone controllers) are typically represented as separate nodes.
- Bus scans show the “shape” of the system without vendor-specific application protocols.

Example (illustrative):

```text
Address  Device
-------  ----------------------
0x10     Room controller (initiator)
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

### Native eBUS addressing vs Vaillant selectors (GG/II)

It helps to be explicit about the “two addressing layers” involved:

- **Native eBUS addressing** is the 1‑byte bus address used for arbitration/ACKs and for basic discovery (bus scans).
- Vaillant’s `GG/II` (and related selectors like `RR`) live **inside the application payload** (e.g., B524) and are not visible to the bus.

Practical implication:

- Multiple internal subsystems can share the same bus destination address and cannot be distinguished via a bus scan alone.
- For decoding/UI, you often need to treat `(DST address, PB/SB, GG, II, RR, opcode family)` as a *logical* address.

## Why This Is Operationally Problematic

### Reduced bus transparency

- In classic eBUS setups, a scan of target addresses approximates the physical topology.
- In classic eBUS setups, a scan of target addresses approximates the physical topology.
- In Vaillant’s regulator model, a bus scan can look like a small system even when the internal topology is large, because many subsystems are “hidden” behind selectors.

### More difficult debugging

- Traffic for distinct subsystems can share the same eBUS address and primary/secondary bytes.
- Logs require additional context (selectors like `GG/II/RR` for B524) to understand which internal subsystem a transaction targets.

### Breaks the “one device, one address” intuition

Illustrative comparison:

```text
Classic eBUS style:
  initiator -> 0x26 (HK1)
  initiator -> 0x27 (HK2)
  initiator -> 0x25 (DHW)

Vaillant regulator style (selector-multiplexed):
  initiator -> <regulator address> group=0 (HK1)
  initiator -> <regulator address> group=1 (HK2)
  initiator -> <regulator address> group=3 (DHW)
```

## Why This Diverges From the “Spirit” of eBUS (Notes)

This is a value judgement, but it is useful for setting expectations: **many integrators approach eBUS as a “transparent bus”** where the device graph is discoverable at the address level.

With selector-multiplexing:

- The regulator becomes a *black box* that hides internal topology behind vendor selectors.
- Discovery, debugging, and interoperability require proprietary application knowledge (e.g., B524 group/instance semantics).
- You cannot reliably isolate subsystems by bus address alone, because many logical components share the same bus node.

## Possible Motivations (Speculative)

These are hypotheses; the intent cannot be proven from bus traffic alone.

- **Address economy:** eBUS address space is finite; multiplexing allows large logical systems while consuming fewer bus addresses.
- **Backward compatibility:** preserving an existing internal architecture avoids redesigning an installed ecosystem.
- **Centralized control:** the regulator remains the “brain” coordinating zones/circuits, rather than distributing autonomy to multiple independent nodes.
- **Ecosystem control / lock-in effects:** proprietary selector spaces increase the cost of third‑party integrations and replacements.

## What It Could Have Looked Like (Illustrative)

If internal subsystems were exposed as separate native bus nodes (still illustrative):

```text
Address  Device
-------  ----------------------
0x10     Room controller (initiator)
0x25     DHW circuit (native target)
0x26     Heating circuit 1 (native target)
0x27     Heating circuit 2 (native target)
0x28     Heating circuit 3 (native target)
0x30     Zone controller 1 (native target)
0x31     Zone controller 2 (native target)
...
```

This style would make bus scans reflect topology and would reduce the amount of vendor-specific selector probing needed for basic discovery.

## Comparison Notes (Non-Normative)

Different vendors implement eBUS-like systems differently:

- Some ecosystems expose more “physical topology” at the bus-address layer (circuits as distinct nodes).
- Others, like Vaillant regulators using selector spaces, centralize control and expose topology only via vendor payload selectors.

## Consequences for Users and Integrators

In practice, Vaillant’s approach often implies:

- You cannot infer internal topology (e.g., number of zones/circuits) from address scans alone.
- Tooling must implement vendor-specific probing to discover groups/instances/register maps.
- “Generic eBUS” tooling may require significant configuration (or reverse engineering) to expose meaningful per-zone/per-circuit data.

## What This Means for Helianthus Tooling

Helianthus should model Vaillant regulator subsystems as **logical components** rather than pretending they are separate eBUS addresses.

For how the gateway discovers the B524 semantic root and then enriches its identity, see:

- [`architecture/b524-semantic-root-discovery.md`](./b524-semantic-root-discovery.md)
- [`architecture/regulator-identity-enrichment.md`](./regulator-identity-enrichment.md)

Tooling guidelines:

- Treat `(address, GG, II, RR)` (and opcode family) as the effective “address” for many values.
- Ensure traces/logs are annotated with the operation name and selector context (e.g., “Reading GG=0x03 II=0x01 RR=0x0016”).
- Prefer surfacing group/instance semantics in UI and artifacts (e.g., group names + instance counts), because the bus topology alone is insufficient.
