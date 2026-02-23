# Portal API

## Status

Portal API is exposed by `helianthus-ebusgateway` as an additive HTTP surface.

- UI shell: `/portal`
- Versioned API base: `/portal/api/v1`

M0 provides the read-only skeleton only. Data exploration APIs are added in later milestones.

## Design Constraints

- Gateway-first: semantic logic stays in gateway runtime.
- Read-only by default for portal API.
- Versioned endpoint paths (`/api/v1`) for forward evolution.
- Runtime is Go-only; frontend assets are embedded in the gateway binary.

## M0 Endpoints

### `GET /portal/api/v1/health`

Returns lightweight health metadata used by the portal shell.

Example response:

```json
{
  "status": "ok",
  "gateway_version": "dev",
  "build_id": "unknown",
  "time_utc": "2026-02-24T00:00:00Z"
}
```

### `GET /portal/api/v1/bootstrap`

Returns portal boot configuration and capability flags.

Example response:

```json
{
  "capabilities": {
    "registry": true,
    "semantic": true,
    "projection": true,
    "stream": false
  },
  "endpoints": {
    "graphql": "/graphql",
    "snapshot": "/snapshot",
    "subscriptions": "/graphql/subscriptions",
    "mcp": "/mcp"
  },
  "limits": {
    "max_events_per_second": 200,
    "snapshot_retention": "disabled_in_m0"
  },
  "ui_version": "m0"
}
```

## M1 Endpoints

### `GET /portal/api/v1/registry/devices`

Returns a read-only snapshot list of discovered registry devices.

Query parameters:

- `q` (optional): case-insensitive filter across manufacturer, device id, serial, plane names, method names
- `limit` (optional): max returned items (`default=200`, `max=1000`)

Example response:

```json
{
  "count": 2,
  "items": [
    {
      "address": 8,
      "addresses": [8],
      "manufacturer": "Vaillant",
      "device_id": "BAI",
      "software_version": "08.06",
      "hardware_version": "01.00",
      "planes": [
        {
          "name": "heating",
          "methods": ["get_operational_data"]
        }
      ]
    },
    {
      "address": 16,
      "addresses": [16],
      "manufacturer": "Vaillant",
      "device_id": "VRC720",
      "software_version": "08.05",
      "hardware_version": "01.00",
      "planes": [
        {
          "name": "system",
          "methods": ["get_status"]
        }
      ]
    }
  ]
}
```

## Security Defaults

- Portal API accepts `GET` only in M0.
- CORS remains same-origin by default.
- No mutating/invoke actions are exposed by portal routes in M0.

## Observability and Performance

- M0 target latency:
  - portal list/read endpoints p95 < 200ms
- Static assets should include caching headers where possible.
- Portal-specific request metrics and logs should be tagged by route.
