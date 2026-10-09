# Growatt Modbus RTU Documentary Facts

The inspected vendor source, *Growatt Inverter Modbus RTU Protocol V1.24*,
describes incompatible MIN, MAX/MID/MAC, MOD, MIX, SPA, and SPH product ranges.
It is inspection-only and is not redistributed here.

The source documents FC03 holding-register candidates at zero-based offsets
`9` (quantity `6`), `43` (quantity `1`), `82` (quantity `2`), and `88`
(quantity `1`) for firmware, device type, model/build letters, and protocol
version respectively. These facts do not prove an address base, family match,
device response, or writable behavior.

This is a proprietary Modbus RTU map and does not establish a SunSpec signature
or model chain.
