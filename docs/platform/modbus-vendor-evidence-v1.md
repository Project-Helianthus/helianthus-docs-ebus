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
  separates SmartLogger, S-Dongle, and EMMA as three first-class but unadmitted
  candidate families.

## Publication Rules

Each source records identity, permission/license, transformation,
applicability, sanitization, disposition, and permitted code mapping. Vendor
documents are not copied into this repository. Public fixtures must be
minimal, independently authored, sanitized, reproducible, and licensed for the
public lane.

`PROFILE_CANDIDATE`, `DOCUMENTARY_CANDIDATE`, and `HYPOTHESIS` are not
`PROFILE_ADMITTED`. Only M7-03 or M7-04 may record admission or a terminal
non-admission after their own exact-head review. The intake packet retains
those candidate states; the manifest's `downstream_outcomes` section links the
later terminal decisions to their exact repository merge and disposition
artifact without rewriting the original evidence classification.

## Runtime Boundary

Every detector operation is a non-executable evidence reference mapped to the
phase-one read allowlist: FC03, FC04, or FC2B/MEI `0x0E`. This packet does not
authorize even those reads. The manifest contains no Modbus write function and
no arbitrary vendor function. A later qualification node may narrow and admit
its own bounded read set after its independent gates pass.

The profile registry owns address normalization, codecs, version gates,
qualification, and vendor flavor applicability. The Modbus runtime owns only
bounded transport operations. A candidate whose required operation is absent
from the runtime allowlist is ineligible; it cannot implement framing locally.

## Downstream Gates

M7-02 may implement additional standard SunSpec models. M7-03 decides Growatt
admission. Before M7-04, `helianthus-modbus` must gain vendor-neutral unit-zero
reads and bounded extended-MEI cursor/wrap support. M7-04 then decides
SmartLogger, S-Dongle, and EMMA independently. M7-05 proves deterministic
mixed-catalog selection across those three families plus direct inverters. No
later node may reinterpret this evidence as a support claim.

## Mixed-Catalog Selection Contract

FMV3-M7-05 requires exclusive selection whenever independent family detectors
feed one mixed primary catalog. Eligibility is evaluated before selection: a
candidate must be qualified, active, default-enabled, and enabled by its
detector declaration. Revoked, superseded, unqualified, default-off, disabled,
or non-admitted candidates cannot participate in a positive match.

With exclusive matching enabled, two or more positive candidates produce
`INSUFFICIENT_EVIDENCE` before score ranking, regardless of candidate score,
catalog order, or detector order. The durable registry decision is
`outcome=ambiguous`, `reason=multiple_matches`, with empty selected profile ID
and version. No first-match or highest-score priority is permitted. With no
positive candidate the result remains `no_match`; with exactly one eligible
positive candidate that profile may be selected. Score, priority,
registration order, detector order, and vendor name never arbitrate between
multiple eligible profiles.

Selection is stateless and does not mutate activation lifecycle. It only
returns an immutable decision; activation remains a downstream responsibility.
The downstream M7-03 and M7-04 disposition artifacts currently record
`NO_ADMISSIBLE_PROFILE` for Growatt, SmartLogger, S-Dongle, and EMMA, so those
families remain absent from the production catalog. The Fronius GEN24 decision
remains post-primary SunSpec flavor classification, not a competing
mixed-catalog primary.
