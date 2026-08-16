# Fronius M4-04 Live Qualification On 0.6.47

This directory publishes the public-redacted `FMV3-M4-04` rerun under
`FMV3-M4-05`. The terminal result is **`STOP_ENVIRONMENTAL`**. The target
qualified internally, but the end-to-end acceptance boundary did not become
observable. This is valid negative evidence, not a Fronius support claim and
not permission to start M5.

The machine-readable record is [`evidence.json`](./evidence.json). It contains
no network endpoint, private address, MAC address, serial number, credential,
raw register payload, process/container identifier, backup identifier, or
private filesystem path.

## Exact Runtime

The authorized read-only run used:

- Home Assistant add-on `0.6.47`, merge
  `176b00ccdd356514532a893e0eef83f173a68c3a`;
- gateway merge `225f3d96fee3422bc565870f946af19fac42d471`;
- `helianthus-modbusreg v0.2.1`, merge
  `16a7dfbf8016750613d086fb98d10364953ea915`;
- image digest
  `sha256:9d79fed17e4ea682adae25ae00f667dc7277bf88f4e6635dd8561c74ac8828b6`;
- target reference `sha256:cc2d63775c6f0074`.

The endpoint remained hidden. Acquisition was Modbus TCP unit `1`, FC03 only.
Writes were forbidden and none were performed.

## Registry Qualification

Each observed current-runtime qualification completed on its first worker
attempt as `GO`, category `registry_match`, without Modbus reconnect. The
registry admitted `sunspec.inverter.three_phase.monitoring@1.0.0` and selected
`sunspec.flavor.fronius.gen24.float.observed@1.1.0` for the closed reference
tuple:

- manufacturer `Fronius`;
- model `Symo GEN24 10.0`;
- firmware `1.41.11-1`;
- ordered chain
  `1/65, 113/60, 120/26, 121/30, 122/44, 123/24, 160/88, 124/24, FFFF/0`.

The tuple is the registry-selected flavor contract. The run did not retrieve a
retained observation through MCP and did not independently compare raw MCP
words. Unknown occurrences, field-level unknown retention, and raw parity are
therefore `WITHHELD_UNPROVEN`; the tuple must not be read as an independently
captured raw dump.

The internal `GO` is only the registry-owned qualification result. It is not
the final M4-04 decision.

## Why The Final Result Is STOP

The target was reachable during the bounded window, but a separate
adapter-direct startup dependency was unreachable from the runtime network
namespace. This evidence does not establish that the physical adapter was
down or defective.

Gateway HTTP and the adapter proxy never listened. Consequently the run could
not retrieve the retained qualification observation, compare raw MCP output,
exercise reconnect-generation integrity, or prove no gateway regression.
Those missing acceptance checks make the only valid terminal result
`STOP_ENVIRONMENTAL` despite the internal registry `GO`.

The operator ended the bounded window and restored
`modbus_tcp_enabled=false`, removed the endpoint value, and returned Modbus
health to `DISABLED / EXPLICIT_DISABLE`.

## Remediation Evidence

The two defects reported by the 0.6.46 run did not recur:

1. The readiness guard did not publish `RUNNING` when HTTP and proxy listeners
   were absent. Current-runtime retries remained bounded and fallback did not
   publish an active state.
2. The failed adapter dependency was redacted as an adapter-direct endpoint,
   not as a Modbus endpoint.

These are focused live regression results. They do not replace the missing
MCP parity or convert the stopped run into a final `GO`.

## Next Gate

M5 remains `BLOCKED_UNTIL_DEPLOYED_EXACT_GO`. A new read-only M4-04 run requires
the adapter-direct path to be reachable from the runtime namespace, gateway
HTTP and adapter-proxy listeners to become ready, and fresh retained-observation
plus raw-MCP parity to be captured. Replay, the registry-internal `GO`, or this
stopped run cannot satisfy that gate.
