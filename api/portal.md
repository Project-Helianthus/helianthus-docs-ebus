# Portal API

## Status

Portal API is exposed by `helianthus-ebusgateway` as an additive HTTP surface.

- UI shell: `/portal`
- Versioned API base: `/portal/api/v1`
- Current UX is capability-driven (status cards + enabled sections) and does not expose milestone placeholder labels.

## Observe-First Contract Ownership

This page owns the frozen Portal-specific observe-first contract after merged
`ISSUE-GW-14`.

- GraphQL owns domain aggregate contracts (`zones`, `dhw`, `energyTotals`,
  `watchSummary`, `busObservability`) and cross-surface schema semantics.
- Portal API/SSE own Portal-specific transport/bootstrap/presentation behavior:
  endpoint names under `/portal/api/v1/*`, capability flags, stream/timeline/
  provenance/snapshots/session flows, and bus-panel state mapping.
- [`watch-summary.md`](./watch-summary.md) remains the shared watch-summary
  schema/semantics authority. This page freezes only the Portal-facing behavior.

## Design Constraints

- Gateway-first: semantic logic stays in gateway runtime.
- Read-only by default for portal API.
- Versioned endpoint paths (`/api/v1`) for forward evolution.
- Runtime is Go-only; frontend assets are embedded in the gateway binary.

## Core Endpoints

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
    "bus_observability": true,
    "projection": true,
    "search": true,
    "stream": true,
    "timeline": true,
    "provenance": true,
    "snapshots": true,
    "snapshot_diff": true,
    "sessions": true,
    "issue_builder": true
  },
  "endpoints": {
    "graphql": "/graphql",
    "snapshot": "/snapshot",
    "subscriptions": "/graphql/subscriptions",
    "mcp": "/mcp",
    "bus_observability": "/portal/api/v1/bus/observability",
    "search": "/portal/api/v1/search",
    "stream": "/portal/api/v1/stream",
    "timeline": "/portal/api/v1/timeline/events",
    "provenance": "/portal/api/v1/provenance/events",
    "snapshots": "/portal/api/v1/snapshots",
    "capture": "/portal/api/v1/snapshots/capture",
    "retention": "/portal/api/v1/snapshots/retention",
    "snapshot_diff": "/portal/api/v1/snapshots/diff",
    "sessions": "/portal/api/v1/sessions",
    "session_save": "/portal/api/v1/sessions/save",
    "session_load": "/portal/api/v1/sessions/load",
    "issue_draft": "/portal/api/v1/issues/draft",
    "issue_export": "/portal/api/v1/issues/export",
    "vrc_migration": "/portal/api/v1/deprecation/vrc-explorer"
  },
  "limits": {
    "max_events_per_second": 200,
    "snapshot_retention": "disabled_in_m0"
  },
  "ui_version": "m0"
}
```

## Data Endpoints

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
Portal overview renders all zones from this payload (not only the first zone), plus DHW and energy summary.

Response fields:

- `zones`: semantic zone list
- `dhw`: optional DHW semantic object
- `energy_totals`: optional aggregated energy object (numeric values + freshness/provenance metadata)
- `boiler_status`: optional boiler semantic object (`state`, `config`, `diagnostics`)
- `system`: optional system status (state, config, properties)
- `circuits`: optional circuit list (`index`, `circuit_type`, `has_mixer`, `state`, `config`, `managing_device`)
- `radio_devices`: optional radio-device list (per-slot semantic RF data)
- `fm5_semantic_mode`: optional FM5 semantic mode string
- `solar`: optional solar semantic object
- `cylinders`: optional cylinder list
- `captured_utc`: RFC3339 UTC timestamp

Energy freshness/provenance metadata (`GW-13` freeze):

- Each series (`gas/electric/solar` × `dhw/climate`) includes `today_meta` and
  may include `yearly_meta[]` / `monthly_meta[]`.
- Metadata fields are: `freshness_state`, `provenance`, `last_observed_utc`,
  `age_seconds`, `stale`.
- `freshness_state` values are `never_seen`, `fresh`, `warming_up`, `stale`,
  `unavailable`.
- `provenance` values are `none`, `register`, `broadcast`.
- Values are non-destructive: stale/unavailable points may keep last numeric
  value; consumers must use metadata for freshness/availability truth.

Example response:

```json
{
  "zones": [
    {
      "id": "zone_1",
      "name": "Living",
      "state": {
        "current_temp_c": 21.3,
        "hvac_action": "HEATING"
      },
      "config": {
        "operating_mode": "auto",
        "target_temp_c": 22.0,
        "allowed_modes": ["auto", "day", "night"]
      }
    }
  ],
  "dhw": {
    "state": {
      "current_temp_c": 47.2
    },
    "config": {
      "operating_mode": "auto",
      "target_temp_c": 49.0
    }
  },
  "energy_totals": {
    "gas": {
      "dhw": { "today": 1.2, "yearly": [1.0, 1.1, 1.2], "today_meta": { "freshness_state": "fresh", "provenance": "register", "last_observed_utc": "2026-02-23T22:44:55Z", "age_seconds": 5, "stale": false } },
      "climate": { "today": 4.8, "yearly": [4.2, 4.5, 4.8], "today_meta": { "freshness_state": "fresh", "provenance": "register", "last_observed_utc": "2026-02-23T22:44:55Z", "age_seconds": 5, "stale": false } }
    },
    "electric": {
      "dhw": { "today": 0.1, "yearly": [0.0, 0.1, 0.1], "today_meta": { "freshness_state": "fresh", "provenance": "register", "last_observed_utc": "2026-02-23T22:44:55Z", "age_seconds": 5, "stale": false } },
      "climate": { "today": 0.7, "yearly": [0.5, 0.6, 0.7], "today_meta": { "freshness_state": "fresh", "provenance": "register", "last_observed_utc": "2026-02-23T22:44:55Z", "age_seconds": 5, "stale": false } }
    },
    "solar": {
      "dhw": { "today": 0.0, "yearly": [0.0, 0.0, 0.0], "today_meta": { "freshness_state": "never_seen", "provenance": "none", "stale": false } },
      "climate": { "today": 0.0, "yearly": [0.0, 0.0, 0.0], "today_meta": { "freshness_state": "never_seen", "provenance": "none", "stale": false } }
    }
  },
  "boiler_status": {
    "state": {
      "flow_temperature_c": 54.2,
      "water_pressure_bar": 1.5,
      "flame_active": true
    },
    "config": {
      "dhw_operating_mode": "auto",
      "flowset_hc_max_c": 75.0
    },
    "diagnostics": {
      "heating_status_raw": 3,
      "central_heating_hours": 1042.0
    }
  },
  "system": {
    "state": {
      "system_off": false,
      "system_water_pressure": 1.5,
      "system_flow_temperature": 31.4,
      "outdoor_temperature": 5.0,
      "outdoor_temperature_avg24h": 4.8,
      "maintenance_due": false,
      "hwc_cylinder_temperature_top": 58.0,
      "hwc_cylinder_temperature_bottom": 42.5
    },
    "config": {
      "adaptive_heating_curve": true,
      "heating_circuit_bivalence_point": -3.0,
      "dhw_bivalence_point": -7.0,
      "hc_emergency_temperature": 30.0,
      "hwc_max_flow_temp_desired": 60.0,
      "max_room_humidity": 70
    },
    "properties": {
      "system_scheme": 1,
      "module_configuration_vr71": 2
    }
  },
  "circuits": [
    {
      "index": 0,
      "circuit_type": "HC",
      "has_mixer": false,
      "state": {
        "flow_setpoint_c": 35.0,
        "flow_temperature_c": 31.2,
        "circuit_state": "active",
        "pump_active": true,
        "calc_flow_temp_c": 35.0
      },
      "config": {
        "heating_curve": 0.8,
        "flow_temp_max_c": 75.0,
        "flow_temp_min_c": 20.0,
        "room_temp_control": "modulating",
        "cooling_enabled": false
      },
      "managing_device": {
        "role": "FUNCTION_MODULE",
        "device_id": "VR_71",
        "address": 38
      }
    }
  ],
  "radio_devices": [
    {
      "group": 0,
      "instance": 1,
      "slot_mode": "THERMOSTAT",
      "device_connected": true,
      "device_model": "VR92",
      "firmware_version": "09.03",
      "zone_assignment": 2,
      "room_temperature_c": 22.5,
      "room_humidity_pct": 44.0
    }
  ],
  "fm5_semantic_mode": "INTERPRETED",
  "solar": {
    "collector_temperature_c": 62.5,
    "return_temperature_c": 45.1,
    "pump_active": true,
    "current_yield": 3.4,
    "pump_hours": 104.0,
    "solar_enabled": true,
    "function_mode": false
  },
  "cylinders": [
    {
      "index": 1,
      "temperature_c": 49.5,
      "max_setpoint_c": 59.0,
      "charge_hysteresis_c": 5.0,
      "charge_offset_c": 2.0
    }
  ],
  "captured_utc": "2026-02-23T22:45:00Z"
}
```

### `GET /portal/api/v1/bus/observability`

Returns Portal bus-observability summary (bus panel + bootstrap capability
surface).

Behavior:

- Returns `200` with JSON when bus observability provider is wired.
- Returns `503` with `bus observability unavailable` when provider is absent or
  nil.

Response fields:

- `status.transport_class`: runtime transport class (`enh`, `ens`, `udp-plain`,
  `tcp-plain`, `ebusd-tcp`).
- `status.capability`: capability booleans plus passive state:
  `passive_state` uses `unavailable | warming_up | available`.
- `status.capability.passive_reason`: when unavailable, one of
  `startup_timeout`, `reconnect_timeout`, `socket_loss`, `flap_dampened`,
  `unsupported_or_misconfigured`, `capability_withdrawn`.
- `status.capability.endpoint_state`: passive endpoint state
  (`unknown`, `connected`, `temporarily_disconnected`,
  `unsupported_or_misconfigured`, `closed`).
- `status.warmup`: warmup counters and blocker/completion fields.
- `status.degraded`: `active` + `reasons`; reasons may include passive
  unavailability reason and/or `dedup_degraded`.
- `status.feature_flags`: observe-first feature-flag state and normalizations.
- `messages`, `periodicity`, `counters`: bounded summary counters used by Portal
  observability views.

Portal-facing bus state mapping (frozen):

1. `warming_up` when `status.warmup.state` is `warming_up` (fallback:
   `status.capability.passive_state`).
2. `degraded` when not warming-up and `status.degraded.active == true`.
3. `unavailable` when neither above matches and (`passive_state == unavailable`
   or `passive_supported == false`).
4. `available` otherwise.

For `transport_class == ebusd-tcp`, when Portal view-state is `degraded` or
`unavailable`, the banner appends:
`ebusd-tcp transport limits passive observe-first coverage.`

Example response:

```json
{
  "status": {
    "transport_class": "ebusd-tcp",
    "capability": {
      "active_supported": true,
      "passive_supported": false,
      "broadcast_supported": false,
      "passive_available": false,
      "passive_state": "unavailable",
      "passive_reason": "unsupported_or_misconfigured",
      "endpoint_state": "unsupported_or_misconfigured",
      "tap_connected": false
    },
    "warmup": {
      "state": "unavailable",
      "completed_transactions": 0,
      "required_transactions": 20
    },
    "timing_quality": {
      "active": "unavailable",
      "passive": "unavailable",
      "busy": "unavailable",
      "periodicity": "unavailable"
    },
    "degraded": {
      "active": true,
      "reasons": ["unsupported_or_misconfigured"]
    },
    "feature_flags": {
      "observe_first_enabled": false,
      "passive_state_direct_apply": false,
      "passive_config_direct_apply": false,
      "external_write_policy": "record_only",
      "normalizations": []
    }
  },
  "messages": {
    "count": 0,
    "capacity": 384
  },
  "periodicity": {
    "count": 0,
    "capacity": 256
  },
  "counters": {
    "series_budget_overflow_total": 0,
    "periodicity_budget_overflow_total": 0
  }
}
```

### `GET /portal/api/v1/projection/devices`

Returns projection summary per discovered device.
Portal overview uses this endpoint to populate projection device/plane selectors.

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
Portal overview uses this endpoint for the live projection graph canvas.

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

### `GET /portal/api/v1/snapshots/diff`

Computes a structural diff between two snapshots.

Query parameters:

- `from_id` (optional): source snapshot id
- `to_id` (optional): target snapshot id
- `limit` (optional): max returned diff entries (`default=200`, `max=1000`)

Behavior:

- If both ids are omitted, the endpoint compares the latest two snapshots.
- If only one id is provided, the endpoint returns `400`.
- If referenced snapshots are missing, the endpoint returns `404`.

Example response:

```json
{
  "from_snapshot": {
    "id": "snap-4",
    "label": "before-change",
    "captured_at": "2026-02-24T02:15:00.123456Z"
  },
  "to_snapshot": {
    "id": "snap-5",
    "label": "after-change",
    "captured_at": "2026-02-24T02:16:00.123456Z"
  },
  "change_count": 2,
  "count": 2,
  "items": [
    {
      "path": "$.registry.items[0].device_id",
      "change": "changed",
      "from": "\"VRC720\"",
      "to": "\"VRC720B\""
    }
  ]
}
```

### `GET /portal/api/v1/sessions`

Lists saved investigation sessions (newest first).

Query parameters:

- `limit` (optional): max returned sessions (`default=30`, `max=1000`)

### `GET /portal/api/v1/sessions/save`

Saves an investigation session/bookmark in the in-memory session store.

Query parameters (all optional):

- `name`
- `search_query`
- `timeline_correlation`
- `provenance_correlation`
- `snapshot_from_id`
- `snapshot_to_id`
- `selected_layer`

### `GET /portal/api/v1/sessions/load`

Loads one saved session by id.

Query parameters:

- `id` (required): session id (e.g. `sess-3`)

Returns `400` when id is missing and `404` when not found.

### `GET /portal/api/v1/issues/draft`

Generates a Markdown issue draft using live portal evidence.

Query parameters (optional):

- `title`
- `observation`
- `reproduction_steps`
- `hypothesis`
- `impact`
- `proposal`
- `acceptance_criteria`
- `controller`
- `device`

Response includes:

- `title`
- `markdown` (full issue body)
- `evidence` (snapshot/timeline/provenance context)

### `GET /portal/api/v1/issues/export`

Builds an export bundle for issue filing workflows.

Response includes:

- `format_version` (`helianthus-issue-bundle/v1`)
- `generated_at`
- `title`
- `markdown`
- `evidence`
- `filename_hint`

### `GET /portal/api/v1/deprecation/vrc-explorer`

Returns deprecation and migration metadata for VRC-Explorer transition.

Response includes:
- `status` (`deprecated`)
- replacement metadata (`Helianthus Portal`)
- migration doc URL
- feature mapping summary
- deprecation gates list

## Portal Quick Probes

Use these commands against a local gateway instance (`:8080`) to verify portal API behavior:

```bash
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/health'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/bootstrap'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/registry/devices?limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/semantic/snapshot'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/bus/observability'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/projection/devices?limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/projection/graph?address=0x10&plane=Service'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/search?q=service&limit=10'
curl -N -fsS 'http://127.0.0.1:8080/portal/api/v1/stream?layers=registry&max_events=3'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/timeline/events?layer=registry&limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/provenance/events?layer=registry&limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/snapshots/capture?label=manual'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/snapshots?limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/snapshots/retention?max_snapshots=25'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/snapshots/diff'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/sessions?limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/sessions/save?name=investigation-a&search_query=service'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/sessions/load?id=sess-1'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/issues/draft?title=Mapping+Candidate'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/issues/export?title=Mapping+Candidate'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/deprecation/vrc-explorer'
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

- Portal API accepts `GET` only.
- CORS remains same-origin by default.
- No mutating/invoke actions are exposed by portal routes.
- Snapshot capture/retention mutate only internal portal memory, not bus/device state.
- Session save/load mutate only internal portal memory, not bus/device state.
- Issue draft/export endpoints are read-only generators over in-memory evidence.

## Observability and Performance

- Target latency:
  - portal list/read endpoints p95 < 200ms
- Static assets should include caching headers where possible.
- Portal-specific request metrics and logs should be tagged by route.

Baseline portal observability in gateway runtime:
- Request log fields: `method`, `path`, `route`, `status`, `duration_ms`
- `expvar` counters/maps: `portal_requests_total`, `portal_route_duration_ms_total`
- Stream counters/maps: `portal_stream_events_total`, `portal_stream_dropped_total`
