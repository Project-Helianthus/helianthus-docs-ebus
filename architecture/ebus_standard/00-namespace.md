# ebus_standard Namespace

Status: Normative
Plan reference: ebus-standard-l7-services-w16-26.locked/00-canonical.md
Canonical SHA-256: 9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305

## Namespace Boundary

The locked plan states:

> `ebus_standard` sits strictly above `protocol.Frame`. Framing, CRC, escaping,
> and bus-transaction behaviour are unchanged. Device identification
> (`0x07 0x04`) is a catalog entry in this namespace, not a hand-coded path in
> scan/identity code.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

`ebus_standard` is therefore an L7 semantic provider only. It does not
alter frame construction, CRC validation, ACK/NACK handling, escaping,
transport arbitration, or bus retry behavior.

## Cross-Vendor Rationale

The standard eBUS application-layer services are not owned by a device
vendor. They describe bus-wide behavior such as identification,
capability discovery, burner service data, memory server access, general
broadcasts, and network management. Helianthus therefore models them as
a cross-vendor namespace whose methods can apply to any conformant eBUS
participant.

Provider selection MUST NOT use manufacturer identity as a precondition
for decoding `ebus_standard`. A frame with PB/SB in this namespace is
eligible for catalog lookup based on its catalog identity axes, even when
the sender is unknown, non-Vaillant, or has no confirmed `DeviceInfo`.

## Provider Separation

The locked plan states:

> `ebus_standard` is cross-vendor and must not contain any
> Vaillant-specific logic.
> Vaillant `0xB5` remains a parallel, unchanged namespace.
> Shared L7 primitives, registry lookup, MCP envelope helpers, and method
> identifiers are namespace-isolated with explicit tests.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

Normative implications:

1. A Vaillant-specific selector, quirk, alias, fallback, or manufacturer
   heuristic MUST NOT be encoded in the `ebus_standard` catalog.
2. Shared codecs MAY be reused only behind namespace-isolated catalog
   metadata and tests.
3. A standard service decode result MUST NOT depend on Vaillant provider
   state.
4. A Vaillant `0xB5` decode result MUST NOT depend on `ebus_standard`
   provider state.

## Catalog Source of Truth

The locked plan states:

> Every method in `ebus_standard` is generated from a catalog data file.
> No provider hard-codes per-device behaviour.
> Catalog is SHA-pinned and version-tagged.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

The catalog is the normative method source. Runtime providers consume
catalog entries; they do not invent hidden service variants.

## Catalog Identity Key

The locked plan states:

> The catalog identity key for each method is the full tuple:
>
> - `namespace` (`ebus_standard`)
> - `PB`
> - `SB`
> - `selector_path` (nullable)
> - `telegram_class` (for example initiator-target,
>   initiator-initiator, broadcast)
> - `direction` (request / response)
> - `request_or_response_role`
> - `broadcast_or_addressed`
> - `answer_policy` (answer-required / no-answer)
> - `length_prefix_mode`
> - `selector_decoder` identifier
> - `service_variant`
> - `transport_capability_requirements`
> - `version`

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

Generation MUST fail when two methods share the same full identity key.
Generation MUST also fail when a length-dependent selector can resolve
to more than one branch for the same payload.

## First-Lock Service Set

The first-lock `ebus_standard` namespace covers these primary services:

| PB | Service |
|---:|---|
| `0x03` | Service Data |
| `0x05` | Burner Control |
| `0x07` | System Data |
| `0x08` | Controller-to-Controller |
| `0x09` | Memory Server |
| `0x0F` | Test Commands |
| `0xFE` | General Broadcast |
| `0xFF` | Network Management |

The per-command catalog is frozen in
[`01-services-catalog.md`](./01-services-catalog.md).
