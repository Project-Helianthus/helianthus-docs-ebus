# Fronius M4-04 Live Qualification On 0.6.51

This directory publishes the public-redacted `FMV3-M4-04` result under
`FMV3-M4-05`. The terminal result is **`GO`** for qualification evidence on the
exact tested runtime, hardware, and profile tuple. It closes the read-only M4
qualification gate only. It does not create a product-support claim, canonical
PV semantics, consumer support, or authorization for Modbus writes, including
for the tested device.

The machine-readable record is [`evidence.json`](./evidence.json). It contains
no network endpoint, private address, MAC address, serial number, credential,
raw register payload, process or container identifier, backup identifier, or
private filesystem path.

## Exact Runtime

The authorized read-only run used:

- Home Assistant add-on `0.6.51`, merge
  `8be32bc7f49f3000eba6074f12ca782e10425093`;
- gateway merge `6f4aaa7a08eeffb655e5da0f6f6c2053e399a45b`;
- `helianthus-modbusreg v0.2.1`, merge
  `16a7dfbf8016750613d086fb98d10364953ea915`;
- multi-architecture image digest
  `sha256:876098e26a6b5f698d0f992f61a0784af8f677f4e3b96a424869fda9609eec6e`;
- target reference `sha256:cc2d63775c6f0074`.

The endpoint remained hidden. Acquisition used Modbus TCP unit `1`, FC03 only.
Writes were forbidden and none were performed.

## Qualification Result

The retained source observation reported:

- capability `sunspec.inverter.three_phase.monitoring@1.0.0` as `ADMITTED`;
- flavor `sunspec.flavor.fronius.gen24.float.observed@1.1.0` as `MATCHED`;
- manufacturer `Fronius`, model `Symo GEN24 10.0`, firmware `1.41.11-1`;
- ordered chain
  `1/65, 113/60, 120/26, 121/30, 122/44, 123/24, 160/88, 124/24, FFFF/0`.

All eight non-terminal model occurrences were admitted by exact
model-id/model-length/schema-revision dispatch. No structural unknown block was
present in this chain. Field-level sentinel and not-implemented values remain
retained in the immutable private source observation and are not promoted or
expanded into this public artifact.

Independent bounded raw MCP reads reproduced every model header and the
terminator exactly on the initial connection generation. The retained
qualification observation was byte-identical before and after the recovery
exercise.

## Recovery Result

One temporary network rule affected only the tested target's Modbus TCP flow.
While the rule was active, one admitted raw MCP request exhausted its single
owner-authorized reconnect and retry and returned the endpoint-free terminal:

```text
UNAVAILABLE: modbus provider unavailable
```

After the rule was removed, the next admitted request returned the same SunSpec
signature on connection and transport generation `2`, advanced from generation
`1`. The gateway process, HTTP listener, adapter-proxy listener, retained
observation, and unrelated protocol runtimes remained alive; no whole-gateway
restart or fallback occurred.

## Acceptance

The exact deployed run passed:

- qualified opt-in detection and bounded polling;
- retained profile observation and raw MCP header parity;
- coherent endpoint-redacted wire, logical-view, poll, and generation
  provenance;
- disconnect/reconnect generation integrity;
- no-write enforcement;
- HTTP and adapter-proxy readiness throughout the recovery window;
- no whole-gateway regression.

The final M4-04 decision is `GO`. After this M4-05 evidence merges, the next DAG
node is the public canonical PV proposal `FMV3-M5-02`; semantic implementation
does not precede that documentation gate.
