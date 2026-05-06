# Address-Table Model

Status: Normative
Plan: address-table-registry-w19-26
Plan-SHA256: eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b
Decision references: AD01, AD02, AD11

<!-- legacy-role-mapping:begin -->
> Legacy role mapping for this ATR spec: `master` -> `initiator`, `slave` -> `target`.
> The legacy terms are retained where the locked plan and eBUS address-pair
> vocabulary require them.

This document defines the registry-side address-table representation. It MUST
be read alongside [`../ebus_standard/12-source-address-table.md`](../ebus_standard/12-source-address-table.md),
which remains the protocol source of truth for address facts and companion
rows. It does not replace [`../nm-discovery.md`](../nm-discovery.md) or
[`../nm-model.md`](../nm-model.md); it defines the storage model those
discovery paths populate.

## Storage Primitive

Per AD01, the registry MUST store address occupancy as a fixed indexed array:

```go
type AddressTable [256]*AddressSlot
```

The registry MUST index the array by the raw byte value. `slot[i] == nil` means
address `byte(i)` has no slot. `slot[i] != nil` means an `AddressSlot` exists
for that address. The registry MUST use the array form instead of a map because
AD01 pins the design to the canonical `ebusd` reference implementation
`m_seenAddresses[256]`, and because the address space is the complete one-byte
domain rather than a sparse unbounded key set.

## Structural Separation

Per AD02, slot state and device identity MUST remain separate:

```go
type AddressSlot struct {
    Addr              byte
    Role              SlotRole
    DiscoverySource   DiscoverySource
    VerificationState VerificationState
    Device            *DeviceEntry
    FirstObservedAt   time.Time
    LastObservedAt    time.Time
}

type DeviceEntry struct {
    Identity Identity
    Faces    []BusFace
}

type BusFace struct {
    Addr              byte
    Role              SlotRole
    DiscoverySource   DiscoverySource
    VerificationState VerificationState
    AccessProtocols   []string
}
```

`AddressSlot` MUST carry address-local state only. `DeviceEntry` MUST carry
identity only. `BusFace` MUST represent a device's participation on a specific
bus address without collapsing that address into the identity object.

## Slot Lifecycle

Per AD02, slot verification MUST advance monotonically through this lifecycle:

```text
nil -> candidate -> corroborated -> identity_confirmed
```

- `nil` means no slot exists.
- `candidate` means the slot exists but has only seed-level or other
  low-confidence evidence.
- `corroborated` means at least two independent observations or one
  observation plus one coherent identity reply have established the slot per
  AD05.
- `identity_confirmed` means the slot is tied to a coherent device identity.

An implementation MUST NOT downgrade a slot from a stronger state to a weaker
state because of later lower-confidence evidence.

## Array Semantics

The array slot is an address index, not an identity record. A slot MUST NOT be
treated as the canonical owner of a physical device. Multiple array indexes MAY
point to the same `*DeviceEntry`, and one `*DeviceEntry` MAY expose multiple
`BusFace` values.

The registry MUST preserve O(1) address lookup semantics across the full
`0x00..0xFF` range. It MUST NOT introduce map-based fallback logic that can
disagree with the array for the same address.

## Slot Aliasing

Per AD02, slot aliasing is the only normative mechanism for multi-address
device ownership. If multiple bus addresses belong to one physical device, the
implementation MUST model that by pointing those slots at the same
`*DeviceEntry` while keeping the slot-local fields distinct.

For the operator-confirmed NETX3 case, the device MUST be modeled as owning
`0xF1`, `0xF6`, and `0x04`. The slots MAY therefore share one device pointer:

```go
table[0xF1].Device == table[0xF6].Device
table[0xF6].Device == table[0x04].Device
```

That aliasing MUST NOT erase per-slot role or provenance. `0xF1` remains a
master face, while `0xF6` and `0x04` remain slave faces.

## Phase Boundary

Per AD11, Phase A MUST preserve predecessor behavior from PR #560 and PR #562.
The address table MAY emit additive events for downstream consumers, but it
MUST NOT deprecate or rewire predecessor logic in this milestone.
<!-- legacy-role-mapping:end -->
