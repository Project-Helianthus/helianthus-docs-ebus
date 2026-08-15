# Fronius M4-04 Live Qualification On 0.6.46

This directory publishes the public-redacted `FMV3-M4-04` result under
`FMV3-M4-05`. The terminal result is **`STOP_ENVIRONMENTAL`**. It is valid
negative evidence, not a Fronius support claim and not permission to start M5.

The machine-readable record is [`evidence.json`](./evidence.json). It contains
no network endpoint, private address, MAC address, serial number, credential,
raw register payload, process/container identifier, or backup identifier.

## Exact Runtime

The bounded run used:

- Home Assistant add-on `0.6.46`, merge
  `eff3f910c5a96c1fc2a9d10a7eb9f618162340c7`;
- gateway merge `53fe86d1beb656c8453a6213127ddddef83c887b`;
- `helianthus-modbusreg v0.2.1`, merge
  `16a7dfbf8016750613d086fb98d10364953ea915`;
- image digest
  `sha256:9169f41b1d15ccf989d182ad125239df682602d87f74c1665b42802b96cabfca`;
- target reference `sha256:cc2d63775c6f0074`.

The endpoint remained hidden. Acquisition was Modbus TCP unit `1`, FC03 only.
Writes were forbidden and none were performed.
The `endpoint_ref` is the stable pseudonymous correlator required by the
current runtime contract. It is not an unlinkability or enumeration-resistance
claim; changing that identifier scheme requires a separate contract revision.

## Registry Qualification

On each of three wrapper-managed gateway starts, the one allowed qualification
attempt completed internally as `GO`, category `registry_match`, without a
Modbus reconnect. The registry admitted
`sunspec.inverter.three_phase.monitoring@1.0.0` and matched exactly
`sunspec.flavor.fronius.gen24.float.observed@1.1.0` for:

- manufacturer `Fronius`;
- model `Symo GEN24 10.0`;
- firmware `1.41.11-1`;
- ordered chain
  `1/65, 113/60, 120/26, 121/30, 122/44, 123/24, 160/88, 124/24, FFFF/0`.

The ordered chain is the exact reference tuple selected by the registry. The
public run could not inspect unknown occurrences or field-level unknown
retention because the MCP observation endpoint never became available. Both
are therefore `WITHHELD_UNPROVEN`; this packet does not infer their absence
from the reference tuple or claim complete raw parity.

The internal `GO` is only the registry-owned qualification result. It is not
the final M4-04 decision.

## Why The Final Result Is STOP

The target remained reachable throughout the bounded window, but a separate
adapter-direct startup dependency timed out. A route existed, while neighbor
resolution was unsuccessful. This evidence does not establish that the
physical adapter was down.

The eeBUS listener became reachable, but gateway HTTP and the adapter proxy did
not listen. Consequently the run could not retrieve the retained qualification
observation, compare raw MCP output, exercise reconnect-generation integrity,
or prove no gateway regression. Those missing acceptance checks make the only
valid final result `STOP_ENVIRONMENTAL` despite the internal registry `GO`.

No additional restart was attempted after the bounded window. The operator
rollback restored `modbus_tcp_enabled=false`, removed the endpoint value, and
returned Modbus health to `DISABLED / EXPLICIT_DISABLE`.

## Separate Findings

Two defects were observed outside SunSpec qualification:

1. Modbus health reported `RUNNING / STARTUP_WINDOW_PASSED` while gateway HTTP
   and adapter-proxy listeners were absent. Process liveness did not establish
   runtime readiness.
2. The log redactor labeled a non-Modbus adapter-direct endpoint as
   `[REDACTED_MODBUS_ENDPOINT]`. That classification obscured the failing
   dependency.

Neither finding changes the retained SunSpec result. They require independent
runtime/redaction triage.

## Next Gate

M5 remains `BLOCKED_UNTIL_DEPLOYED_EXACT_GO`. A new read-only M4-04 run requires
the adapter-direct dependency to recover, gateway HTTP and adapter-proxy
listeners to become ready, and fresh retained-observation plus raw-MCP parity
to be captured. Replay, the internal `GO`, or this stopped run cannot satisfy
that gate.
