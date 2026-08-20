# Huawei Gateway Candidate Evidence V1

## Status

This FMV3-M7-01 packet separates SmartLogger, S-Dongle, and EMMA evidence. It
does not admit a Huawei profile, does not copy vendor register tables, and does
not authorize Modbus writes.

## Evidence Inputs

The documentary corpus was converted to searchable Markdown during the
operator-owned Tancabesti analysis. The relevant immutable document digests
are:

| Source | SHA-256 | Use |
| --- | --- | --- |
| SmartLogger V300R024C10 interface revision 54 | `f00b197c84a581bfcaec95a1b6a959ab8f08c670a31ea3d27414f1f2b33bc794` | Function codes, device identifiers, public/remapped registers |
| SmartLogger register gate table | `3b730d98c423be5965fd65788fb5e086337361e866e9266f38daea1c7be48e1c` | Cross-revision firmware/model applicability |
| S-Dongle V200R025C00SPC120 interface revision 01 | `2806fac6a6176c3f815e8d8135f306b0bb585bcfed8770bfa822536fcf39ab1b` | Unit 100 identity and read-only telemetry |
| S-Dongle Modbus TCP guide revision 05 | `cc5b5c45e90d4607a6d79a4b5069632576731cb1165957bd120970a97ff45d47` | Product and minimum-version applicability |

These are vendor-copyrighted inspection inputs and are not redistributed. The
AGPL-3.0 fork `d3vi1/huawei-solar-lib` at
`9029a9e2320c3fb3295e2e4ce64adede55acac24` is a research lead for probe order,
not independent documentary proof and not copied into this contract.

## SmartLogger Candidate

The documentary family exposes a device-list change counter at unit `0`, FC03,
offset `65521`, quantity `1`. FC2B/MEI `0x0E` basic identification exposes
manufacturer, product code, and revision. The register at `65524` is a writable
operator device name and is forbidden as an identity discriminator.

Version-family prefixes and register availability vary across SmartLogger1000,
SmartLogger2000, and SmartLogger3000. The gate table distinguishes baseline,
V100, V200, V300, V300R024C10, and V300R024C10SPC210-era additions. A firmware
prefix alone is not a product identity.

Disposition: `HYPOTHESIS`. The `65521@unit0` response plus FC2B identity still
requires a negative-overlap fixture against EMMA and direct inverter/proxy
behavior before automatic eligibility.

## S-Dongle Candidate

The S-Dongle interface documents logical unit `100`. FC2B/MEI `0x0E` basic
identification provides manufacturer `HUAWEI`, an S-Dongle product code, and
the software revision. Bounded FC03 enrichment may read:

- offset `30068`, quantity `2`, protocol version;
- offset `37410`, quantity `3`, dongle type, device-search state, and device
  change sequence.

The revision-01 interface applies to SDongleA-05, SDongleB-03, and SDongleB-06
at V200R022C10 or later. The separate TCP guide records an older SDongleA-05
minimum of V100R001C00SPC124 plus inverter-side minimum versions. M7-04 must
keep those document branches distinct rather than collapsing them into one
synthetic minimum.

Disposition: `DOCUMENTARY_CANDIDATE`. Admission still requires a sanitized
fixture proving the exact product-code and revision tuple.

## EMMA Boundary

The research fork proposes unit `0`, FC03, offset `30222`, quantity `20`, with
a `SmartHEMS` model string. No authoritative EMMA document in the admitted
public corpus currently proves that this read is unique, version-gated, and
non-overlapping with SmartLogger behavior.

Disposition: `UNKNOWN`. EMMA has no executable detector PDU, no semantics, no
catalog eligibility, and no fallback to SmartLogger or S-Dongle. M7-04 must
leave it ineligible until a separately licensed authoritative source and a
negative-overlap fixture prove a discriminator.

## Safety

Only FC03 and FC2B/MEI `0x0E` appear in the candidate detector set. FC06,
FC10, power-control, start/stop, reset, registration-key, serial-number, and
credential registers are excluded. Timeout, exception, ambiguous identity, or
unsupported firmware yields no admission.
