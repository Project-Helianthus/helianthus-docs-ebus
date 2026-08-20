# Modbus Vendor Evidence Intake V1

## Status

This is the FMV3-M7-01 platform disposition for the SunSpec, Growatt, and
Huawei evidence packets. It records research inputs and candidate boundaries;
it does not publish support or activate a registry profile.

The closed machine-readable companion is
[`manifests/modbus-vendor-evidence-v1.json`](./manifests/modbus-vendor-evidence-v1.json).

## Packets

- [SunSpec additional models](../../protocols/sunspec/additional-model-evidence-v1.md)
  uses the Apache-2.0 upstream model repository pinned to an immutable commit.
- [Growatt candidate](../../protocols/modbus/growatt-candidate-evidence-v1.md)
  records an inspection-only proprietary map and explicitly rejects a SunSpec
  label.
- [Huawei gateway candidates](../../protocols/modbus/huawei-gateway-candidate-evidence-v1.md)
  separates SmartLogger and S-Dongle applicability and leaves EMMA `UNKNOWN`.

## Publication Rules

Each source records identity, permission/license, transformation,
applicability, sanitization, disposition, and permitted code mapping. Vendor
documents are not copied into this repository. Public fixtures must be
minimal, independently authored, sanitized, reproducible, and licensed for the
public lane.

`PROFILE_CANDIDATE`, `DOCUMENTARY_CANDIDATE`, and `HYPOTHESIS` are not
`PROFILE_ADMITTED`. Only M7-03 or M7-04 may record admission or a terminal
non-admission after their own exact-head review.

## Runtime Boundary

Every detector operation is mapped to the phase-one read allowlist: FC03,
FC04, or FC2B/MEI `0x0E`. The manifest contains no Modbus write function and no
arbitrary vendor function. A packet may narrow this set further.

The profile registry owns address normalization, codecs, version gates,
qualification, and vendor flavor applicability. The Modbus runtime owns only
bounded transport operations. A candidate whose required operation is absent
from the runtime allowlist is ineligible; it cannot implement framing locally.

## Downstream Gates

M7-02 may implement additional standard SunSpec models. M7-03 decides Growatt
admission. M7-04 decides SmartLogger and S-Dongle separately while EMMA remains
ineligible. M7-05 proves deterministic mixed-catalog selection and ambiguity
handling. No later node may reinterpret this evidence as a support claim.
