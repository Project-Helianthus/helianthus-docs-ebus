# Growatt Modbus Candidate Evidence V1

## Status

This packet records an FMV3-M7-01 research candidate. It does not admit a
Growatt profile and does not claim product support.

## Source And Licensing

The inspected primary source is `Growatt Inverter Modbus RTU Protocol V1.24`,
85 pages, SHA-256
`fac88d609d74ff6b3c9c31ed65370d166d1fb17461e91b4b4855018fe232a320`.
The document is vendor-copyrighted and inspection-only. It is not redistributed
here. This packet contains independently authored interface facts and excludes
vendor prose, register tables, serial numbers, captures, and customer data.

The document describes multiple incompatible product ranges, including MIN,
MAX/MID/MAC, MOD, MIX, SPA, and SPH families. A response from one address range
cannot establish applicability to another family.

## Candidate Identity Reads

The following zero-based documentary offsets are research PDUs, not executable
activation probes:

| PDU | Purpose | Disposition |
| --- | --- | --- |
| configured unit, FC03, offset `9`, quantity `6` | Firmware tuple | `HYPOTHESIS` |
| configured unit, FC03, offset `43`, quantity `1` | Device type code | `HYPOTHESIS` |
| configured unit, FC03, offset `82`, quantity `2` | Model/build letters | `HYPOTHESIS` |
| configured unit, FC03, offset `88`, quantity `1` | Modbus protocol version | `HYPOTHESIS` |

All four operations map to the existing FC03 holding-register allowlist and are
within the 125-register bound. M7-03 must independently verify address
normalization, family coverage, firmware behavior, and whether the tuple is
unique before any probe becomes executable.

Serial-number fields are intentionally excluded from detection and fixtures.
No register marked writable in the source is writable through this profile.

## Not SunSpec

The inspected map is a proprietary Growatt Modbus RTU register map. It does not
expose a proven SunSpec signature/model chain in this evidence packet and must
not be labeled or decoded as SunSpec. A future device that independently
exposes real SunSpec is handled by the SunSpec core, not by silently treating
this map as a standard model.

## M7-03 Decision Inputs

`PROFILE_ADMITTED` requires a clean-room fixture and deterministic tuple that
separates at least the applicable product family, firmware branch, register
range, address base, and byte/word order. Missing or conflicting evidence must
produce `NO_ADMISSIBLE_PROFILE`. Either result is a valid M7-03 completion.
