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
    "search": true,
    "stream": true,
    "timeline": true,
    "provenance": true,
    "snapshots": true
  },
  "endpoints": {
    "graphql": "/graphql",
    "snapshot": "/snapshot",
    "subscriptions": "/graphql/subscriptions",
    "mcp": "/mcp",
    "search": "/portal/api/v1/search",
    "stream": "/portal/api/v1/stream",
    "timeline": "/portal/api/v1/timeline/events",
    "provenance": "/portal/api/v1/provenance/events",
    "snapshots": "/portal/api/v1/snapshots",
    "capture": "/portal/api/v1/snapshots/capture",
    "retention": "/portal/api/v1/snapshots/retention"
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

### `GET /portal/api/v1/semantic/snapshot`

Returns a read-only semantic snapshot for portal list views.

Response fields:

- `zones`: semantic zone list
- `dhw`: optional DHW semantic object
- `energy_totals`: optional aggregated energy object
- `captured_utc`: RFC3339 UTC timestamp

Example response:

```json
{
  "zones": [
    {
      "id": "zone_1",
      "name": "Living",
      "operating_mode": "auto",
      "current_temp_c": 21.3,
      "target_temp_c": 22.0
    }
  ],
  "dhw": {
    "operating_mode": "auto",
    "target_temp_c": 49.0
  },
  "energy_totals": {
    "gas": {
      "dhw": { "today": 1.2 },
      "climate": { "today": 4.8 }
    },
    "electric": {
      "dhw": { "today": 0.1 },
      "climate": { "today": 0.7 }
    },
    "solar": {
      "dhw": { "today": 0.0 },
      "climate": { "today": 0.0 }
    }
  },
  "captured_utc": "2026-02-23T22:45:00Z"
}
```

### `GET /portal/api/v1/projection/devices`

Returns projection summary per discovered device.

Query parameters:

- `q` (optional): case-insensitive filter over manufacturer/device/display name/plane
- `limit` (optional): max returned items (`default=200`, `max=1000`)

Example response:

```json
{
  "count": 1,
  "items": [
    {
      "address": 16,
      "manufacturer": "Vaillant",
      "device_id": "VRC720",
      "display_name": "sensoCOMFORT",
      "projections": [
        {
          "plane": "Service",
          "node_count": 18,
          "edge_count": 20
        },
        {
          "plane": "Observability",
          "node_count": 18,
          "edge_count": 20
        }
      ]
    }
  ]
}
```

### `GET /portal/api/v1/projection/graph`

Returns one projection graph for a selected device and plane.

Query parameters:

- `address` (required): device address (decimal or hex, e.g. `16` or `0x10`)
- `plane` (required): projection plane name (e.g. `Service`)

Example response:

```json
{
  "address": 16,
  "plane": "Service",
  "nodes": [
    {
      "id": "Service:/ebus/addr@16/device@BASV2",
      "path": "Service:/ebus/addr@16/device@BASV2",
      "canonical_path": "Service:/ebus/addr@16/device@BASV2"
    }
  ],
  "edges": [
    {
      "id": "Service:Service:/ebus/addr@16/device@BASV2->Service:/ebus/addr@16/device@BASV2/method@get_status",
      "from": "Service:/ebus/addr@16/device@BASV2",
      "to": "Service:/ebus/addr@16/device@BASV2/method@get_status"
    }
  ]
}
```

### `GET /portal/api/v1/search`

Returns unified, read-only search matches across currently available portal layers
(registry, semantic snapshot, projection summary).

Query parameters:

- `q` (required): search string (case-insensitive)
- `limit` (optional): max returned items (`default=25`, `max=1000`)

Example response:

```json
{
  "query": "service",
  "count": 2,
  "items": [
    {
      "layer": "registry",
      "kind": "method",
      "id": "reg:10:system:get_status",
      "title": "get_status",
      "subtitle": "system plane addr=0x10",
      "address": 16
    },
    {
      "layer": "projection",
      "kind": "plane",
      "id": "proj:10:service",
      "title": "Service",
      "subtitle": "addr=0x10 nodes=18 edges=20",
      "address": 16
    }
  ]
}
```

### `GET /portal/api/v1/stream`

Server-Sent Events (SSE) stream for lightweight live updates with server-side throttling and coalescing.

Query parameters:

- `layers` (optional): comma-separated layer filter (`registry`, `semantic`, `projection`)
- `interval_ms` (optional): producer interval (`default=1000`, bounded `200..5000`)
- `max_events_per_second` (optional): flush limit (`default=3`, bounded `1..30`)
- `max_events` (optional): stop stream after N emitted events (useful for tests)

SSE event format:

```text
event: update
data: {"at":"2026-02-24T01:00:00.123456Z","type":"snapshot","layer":"registry","correlation_id":"reg-...","payload":{"device_count":2},"provenance":{"source":"poll:registry","dropped":0,"interval_ms":1000}}
```

Notes:

- The server coalesces pending updates and reports dropped intermediate updates in
  `provenance.dropped`.
- Keep-alive comments (`: keep-alive`) are emitted periodically to keep the connection open.
- If no readable data providers are available, the endpoint returns `503`.

### `GET /portal/api/v1/timeline/events`

Returns recent stream events from the in-memory timeline store (newest first).

Query parameters:

- `limit` (optional): max returned events (`default=100`, `max=1000`)
- `layer` (optional): filter by layer (`registry`, `semantic`, `projection`)
- `correlation_id` (optional): substring match on correlation id
- `since` (optional): RFC3339/RFC3339Nano lower-bound timestamp (UTC recommended)

Example response:

```json
{
  "count": 2,
  "items": [
    {
      "at": "2026-02-24T01:23:45.123456Z",
      "type": "snapshot",
      "layer": "registry",
      "correlation_id": "reg-1740356625123456000",
      "payload": {
        "device_count": 2
      },
      "provenance": {
        "source": "poll:registry",
        "dropped": 0,
        "interval_ms": 1000
      }
    }
  ]
}
```

### `GET /portal/api/v1/provenance/events`

Returns provenance projections derived from timeline events (newest first).

Query parameters:

- `limit` (optional): max returned records (`default=50`, `max=1000`)
- `layer` (optional): filter by layer (`registry`, `semantic`, `projection`)
- `correlation_id` (optional): substring match on correlation id

Example response:

```json
{
  "count": 1,
  "items": [
    {
      "correlation_id": "reg-1740356625123456000",
      "layer": "registry",
      "at": "2026-02-24T01:23:45.123456Z",
      "source": "poll:registry",
      "dropped": 0,
      "interval_ms": 1000,
      "decode_path": [
        "source:poll:registry",
        "layer:registry",
        "gateway.portal.stream",
        "gateway.portal.timeline"
      ],
      "payload_keys": ["device_count"],
      "confidence": 0.7
    }
  ]
}
```

### `GET /portal/api/v1/snapshots`

Lists retained snapshots from the in-memory snapshot store (newest first).

Query parameters:

- `limit` (optional): max returned snapshots (`default=20`, `max=1000`)

Example response:

```json
{
  "count": 2,
  "stored_count": 2,
  "max_snapshots": 50,
  "items": [
    {
      "id": "snap-3",
      "label": "after-system-change",
      "captured_at": "2026-02-24T02:12:00.123456Z",
      "payload": {
        "captured_at": "2026-02-24T02:12:00.123456Z",
        "registry": { "count": 2 },
        "timeline": { "count": 6 }
      }
    }
  ]
}
```

### `GET /portal/api/v1/snapshots/capture`

Captures a new snapshot from current portal read models and returns capture metadata.

Query parameters:

- `label` (optional): free text label stored with the snapshot

If no readable providers are available, returns `503`.

### `GET /portal/api/v1/snapshots/retention`

Reads or updates snapshot retention limits.

Query parameters:

- `max_snapshots` (optional): set retention bound (`1..500`)

Example response:

```json
{
  "max_snapshots": 50,
  "stored_count": 3
}
```

## Portal Quick Probes

Use these commands against a local gateway instance (`:8080`) to verify portal API behavior:

```bash
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/health'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/bootstrap'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/registry/devices?limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/semantic/snapshot'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/projection/devices?limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/projection/graph?address=0x10&plane=Service'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/search?q=service&limit=10'
curl -N -fsS 'http://127.0.0.1:8080/portal/api/v1/stream?layers=registry&max_events=3'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/timeline/events?layer=registry&limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/provenance/events?layer=registry&limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/snapshots/capture?label=manual'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/snapshots?limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/snapshots/retention?max_snapshots=25'
```

## Portal Asset Build and Drift Check

Portal static assets are generated from `portal/web/src` and embedded into the gateway binary under
`portal/static/assets`.

Use the gateway helper scripts:

```bash
./scripts/build_portal_assets.sh
./scripts/check_portal_assets.sh
```

Production runtime does not require Node.js. Node is only required when regenerating embedded assets.

## Security Defaults

- Portal API accepts `GET` only in M0.
- CORS remains same-origin by default.
- No mutating/invoke actions are exposed by portal routes in M0.
- Snapshot capture/retention mutate only internal portal memory, not bus/device state.

## Observability and Performance

- M0 target latency:
  - portal list/read endpoints p95 < 200ms
- Static assets should include caching headers where possible.
- Portal-specific request metrics and logs should be tagged by route.

Baseline portal observability in gateway runtime:
- Request log fields: `method`, `path`, `route`, `status`, `duration_ms`
- `expvar` counters/maps: `portal_requests_total`, `portal_route_duration_ms_total`
- Stream counters/maps: `portal_stream_events_total`, `portal_stream_dropped_total`
