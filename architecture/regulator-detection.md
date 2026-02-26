# Regulator Detection Contract

This page documents how the gateway determines whether a Vaillant regulator is present on the eBUS network.

## Motivation

Regulator presence determines the gateway's operational mode:

- **Regulator present:** full zone/DHW semantic polling via B524 selector-multiplexed reads through the regulator address.
- **Regulator absent:** semantic polling is not possible; the gateway operates in reduced mode (broadcast energy ingestion only, if available).

Prior to this contract, regulator detection relied on a **naming heuristic**: scanning the device registry for entries whose identification string started with `BASV` (the eBUS address-family prefix for Vaillant system controllers). This was fragile — it coupled detection to string prefixes that could change across firmware versions or device families.

## Detection Method

Regulator detection uses the **product IDs catalog** from `helianthus-ebusreg` as the single source of truth.

### Algorithm

```text
for each device in registry:
    serial := device.Identification
    partNumber := extractPartNumber(serial)
    if partNumber is valid:
        capability := catalog.ControllerCapability(partNumber)
        if capability == ControllerPresent:
            return ControllerPresent
        if capability == ControllerNone:
            track as non-regulator
    // ControllerUnknown or invalid partNumber: skip

if any device was ControllerNone:
    return ControllerNone
return ControllerUnknown
```

### Part Number Extraction

The eBUS identification string contains a fixed-format serial where positions 4–14 encode the Vaillant article number (part number). The extraction:

1. Strips whitespace from the identification string.
2. Checks minimum length (14 characters).
3. Extracts substring `[4:14]`.
4. Validates all characters are digits.
5. Returns the 10-digit part number, or empty string on failure.

### ControllerCapability Tri-State

The `productids.ControllerCapability` enum in `helianthus-ebusreg` classifies part numbers:

| Value | Meaning |
| --- | --- |
| `ControllerPresent` | Part number maps to a product with `role = "Regulator"` in the catalog |
| `ControllerNone` | Part number found in catalog but role is not Regulator |
| `ControllerUnknown` | Part number not found in catalog |

### Catalog Source

The catalog is the `helianthus-ebus-vaillant-productids` dataset, loaded via `helianthus-ebusreg/vaillant/productids`. As of the initial implementation, the catalog contains 31 regulators and 6 thermostats correctly classified.

## Lifecycle

- Regulator capability is recomputed on every `refreshDiscovery` cycle.
- The computation runs **before** the BASV address lookup, so capability is always current even when no BASV-prefixed device is found in the registry.
- Capability changes are logged: `semantic_regulator_capability capability=<value>`.
- The legacy `findDeviceAddressByPrefix("BASV")` call remains for obtaining the controller's eBUS address for B524 polling. It is **not** used for regulator presence decisions.

## Known Limitations

- **Multi-regulator systems:** If multiple devices report `ControllerPresent`, the first one found wins. Multi-regulator topologies are not supported in v1.
- **Unknown devices:** Devices with part numbers absent from the catalog produce `ControllerUnknown`. The system does not assume regulator absence from unknown devices — only catalog-confirmed non-regulators produce `ControllerNone`.
- **Catalog coverage:** Detection quality depends on catalog completeness. New Vaillant products require catalog updates in `helianthus-ebus-vaillant-productids`.

## Cross-Links

- Vaillant regulator architecture: [`architecture/vaillant.md`](./vaillant.md)
- Startup FSM (uses regulator detection for readiness): [`architecture/startup-semantic-fsm.md`](./startup-semantic-fsm.md)
- Product IDs catalog: [`helianthus-ebus-vaillant-productids`](https://github.com/d3vi1/helianthus-ebus-vaillant-productids)
- ControllerCapability contract: [`helianthus-ebusreg/vaillant/productids`](https://github.com/d3vi1/helianthus-ebusreg)
