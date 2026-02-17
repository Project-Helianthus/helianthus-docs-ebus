# Home Assistant Integration

## Scope

This guide documents how `helianthus-ha-integration` discovers a Helianthus gateway and what GraphQL capabilities are required versus optional.

## Setup

### 1. Automatic discovery (mDNS)

- The integration listens for `_helianthus-graphql._tcp.local.`.
- TXT keys used by the integration:
  - `path` (default: `/graphql`)
  - `transport` (`http` or `https`, default: `http`)
  - `version` (optional, informational)
- TXT key matching is case-insensitive.

### 2. Manual configuration

The config flow supports manual fields:

- `host`
- `port`
- `path` (GraphQL endpoint path)
- `transport` (`http` or `https`)
- `version` (optional metadata)

Before creating the config entry, the integration validates connectivity by running a schema probe query:

```graphql
query HelianthusSchema {
  __schema {
    queryType { name }
  }
}
```

Duplicate endpoint detection (`host:port`) is checked before network validation.

## GraphQL Capability Matrix

| Capability | Query/Field | Required | Behavior if Missing |
|---|---|---|---|
| Config-flow probe | `__schema.queryType.name` | Yes | Setup blocked (`invalid_response` / `cannot_connect`) |
| Device inventory (base) | `devices { address manufacturer deviceId softwareVersion hardwareVersion }` | Yes | Setup cannot build device tree |
| Device identity enrichment | `devices { serialNumber macAddress }` | Optional | Integration falls back to base query and fallback ID scheme |
| Service status | `daemonStatus`, `adapterStatus` | Yes (current implementation) | Setup refresh fails |
| Semantic climate/DHW | `zones`, `dhw` | Optional | Coordinator returns empty/default semantic payload |
| Energy totals | `energyTotals` | Optional | Coordinator returns `energyTotals: null` |
| Realtime subscriptions | GraphQL WS (`graphql-transport-ws`) | Optional | Polling remains available via coordinator intervals |

## Device Tree

The integration materializes this hierarchy in HA device registry:

1. `Helianthus Daemon` (root)
2. `eBUS Adapter` (via daemon)
3. Physical eBUS devices (via adapter)
4. Virtual semantic devices (derived) attached to their semantic parent (for example zones/DHW via the regulator)

Device IDs are generated with deterministic fallback:

1. Prefer stable, addressable identity: `deviceId + address + hw + sw`
2. If present, include `serialNumber` and/or `macAddress` as *additional* identifiers (enrichment), but do not create a new device when those fields are temporarily missing.

## Troubleshooting

### `cannot_connect`

- Host/port/path/transport mismatch.
- Endpoint unreachable from HA.
- TLS mismatch (for example `http` configured for an `https` endpoint).

### `invalid_response`

- Endpoint is reachable but does not return GraphQL schema data.
- Reverse proxy or non-GraphQL endpoint is mapped to the configured path.

### `already_configured`

- Another config entry already uses the same `host:port`.

### Missing optional data

- If `zones`/`dhw` are absent, climate and DHW semantic entities remain empty.
- If `energyTotals` is absent, energy entities remain unavailable.
