# Fronius Observed SunSpec Flavor V1.2

## Status and evidence boundary

`sunspec.flavor.fronius.gen24.float.observed@1.2.0` is an experimental,
read-only successor to `sunspec.flavor.fronius.gen24.float.observed@1.1.0` and
`sunspec.flavor.fronius.gen24.float.observed@1.0.0`. It does not reinterpret
either earlier contract. Each identifier admits only its own exact Common
identity tuple and ordered chain.

This contract is bounded to one sanitized observation: a single read-only
model-chain walk of a Fronius `Symo GEN24 10.0` reporting firmware `1.42.9-1`,
whose complete snapshot admitted the
`sunspec.inverter.three_phase.monitoring@1.0.0` capability. It is not a
product-family support claim and does not infer another model, firmware,
market variant, or chain. Registry evaluation of that device against V1 and
V1.1 correctly returned `FIRMWARE_MISMATCH`: manufacturer and model matched,
and the version string did not. That designed fail-closed result motivates
this versioned contract; it is not completion evidence for any live
qualification.

No endpoint, serial, private capture, capture time, vendor register row, or
SunSpec table is reproduced here, and this page carries no register word. The
sanitized observation record is published separately under
[`docs/platform/live/fronius-observed-flavor-1.2.0/`](../docs/platform/live/fronius-observed-flavor-1.2.0/):
the exact Common identity tuple, the ordered chain headers, the acquisition
parameters, and the registry outcomes, with no register words in
`evidence.json`. That record is the falsifiable artifact for the `Proven`
labels below, and a disagreement between it and this page is a defect in this
contract. One sidecar in the same directory,
[`common-block.json`](../docs/platform/live/fronius-observed-flavor-1.2.0/common-block.json),
lists the sanitized register words of the Common block (Model 1) alone, from
the SunSpec signature through the device-address register, with the
serial-number field zeroed and no word of any other model; it names the
packet's own label as its provenance reference. The sidecar covers Model 1
only: the other chain entries and the capability outcome are recorded as
headers and outcomes without register words. The native geometry
of this ordered chain is recorded in the
[Modbus-family Fronius flavor reference](https://github.com/Project-Helianthus/helianthus-docs-modbus/blob/main/protocols/fronius/sunspec-float-v1.md);
this AGPL contract owns only the Helianthus exact-admission tuple and outcomes
below.

## Evidence status

Labels follow the repository evidence rules and are scoped to this exact tuple.
They describe documentary evidence and are not a qualification result.

`Proven`, established by the one sanitized walk recorded in that artifact
within its stated acquisition context:

- Common `Mn`, `Md`, and `Vr` decoded to `Fronius`, `Symo GEN24 10.0`, and
  `1.42.9-1`. The fixed-width Common strings are NUL-padded on the wire; the
  tuple values are the decoded strings, and the padding is not part of the
  identity. The sanitized Common block register words in the sidecar decode to
  the same three strings and carry the Model 1 header `1/65`, so this decoding
  can be checked against an observed register dump.
- The walk followed the chain from the SunSpec signature through the
  consuming `FFFF/0` terminal and found, in order,
  `1/65, 113/60, 120/26, 121/30, 122/44, 123/24, 160/88, 124/24, FFFF/0`.
- That chain equals the V1.1 chain entry for entry and in order. The Common
  version string is the only element of the V1.1 identity tuple that differs.
- The complete terminal-verified snapshot admitted the capability from exactly
  one `113/L60` source.
- Acquisition used FC03 holding-register reads only, unit ID `1`, and
  normalized PDU offset `40000` for the SunSpec signature. No write of any kind
  was performed.

`Hypothesis`:

- Manufacturer, model, and firmware as a candidate detector gate for a chain or
  behavior family (`FSS-C-007`) remains a retained hypothesis. It stays
  forbidden from production use and is not implemented here: this contract
  admits one exact tuple, not a detector, a series, or a range.

`Unknown`:

- Any Common version string other than `1.42.9-1` for this model, however it
  relates to that string, and any other model, market variant, or device.
- Whether the chain is stable across repeated walks and operating states. One
  walk is the whole basis of this contract.
- Whether decoded values, scale factors, or sentinel use differ from firmware
  `1.41.11-1` outside the facts the capability admission required. This
  contract compares identity and structure only.
- Live qualification and present live state. None is recorded here.

## Exact admission tuple

The capability must already be admitted as
`sunspec.inverter.three_phase.monitoring@1.0.0`. Flavor evaluation then requires
all of these independent exact gates:

- Common manufacturer: `Fronius`, exact string match;
- Common model: `Symo GEN24 10.0`, exact string match;
- Common version/firmware: `1.42.9-1`, exact string match;
- exact ordered chain match:
  `1/65, 113/60, 120/26, 121/30, 122/44, 123/24, 160/88, 124/24, FFFF/0`;
- exactly one admitted Model `113/L60` source for the required capability
  facts.

The identity tuple contains exactly Common `Mn`, `Md`, and `Vr`. Common `SN`,
`Opt`, and `DA`, plus endpoint, unit ID, function, PDU offset, and other
acquisition provenance, are not matching inputs.

Model `123/L24`, Immediate Controls, is a standard model selected only through
the exact core decoder key `(123, 24, schema_revision)`, as for V1.1. It is not
a vendor-specific extension. The decoder is read-only and the model's RW
metadata creates no write authority.

There is no case folding, trimming, prefix match, semantic-version range,
"at least" or "newer than" comparison, model-ID-only fallback, reordering,
subset match, optional insertion, or int+SF substitution. Firmware strings are
compared, never ordered: `1.42.9-1` is not treated as an upgrade of, or as
compatible with, `1.41.11-1`, and neither string admits the other. A firmware
string that a flavor does not list fails closed with `FIRMWARE_MISMATCH` for
that flavor, however it relates to a listed string.

The three identifiers stay mutually exclusive:

- V1 remains exact for firmware `1.41.11-1` and
  `1/65, 113/60, 120/26, 121/30, 122/44, 160/88, 124/24, FFFF/0`;
- V1.1 remains exact for firmware `1.41.11-1` and
  `1/65, 113/60, 120/26, 121/30, 122/44, 123/24, 160/88, 124/24, FFFF/0`;
- V1.2 is exact for firmware `1.42.9-1` and the same ordered chain as V1.1.

V1.1 and V1.2 share one ordered chain and differ only in the exact Common
version string, so no snapshot can match both. A different tuple or chain needs
separate evidence and its own versioned contract.

## Outcomes and ownership

Evaluation uses the same complete, terminal-verified snapshot as capability
admission and preserves the closed reasons and precedence of V1 and V1.1:
`CAPABILITY_NOT_ADMITTED`, `COMMON_IDENTITY_MISMATCH`, `FIRMWARE_MISMATCH`,
`CHAIN_MISMATCH`, `AMBIGUOUS_SOURCE`, and `MATCHED`. A snapshot whose
manufacturer and model match but whose version is any other string yields
`FIRMWARE_MISMATCH` before the chain is compared, without partial flavor facts.
A mismatch never rewrites or drops raw model occurrences, canonical capability
facts, or acquisition provenance, which stay with their owning contracts.

The sanitized observation used FC03 reads, unit ID `1`, and normalized PDU
offset `40000`. These values are non-actionable provenance only. They are not
defaults and do not prove that another Fronius device uses the same acquisition
parameters.

The flavor does not select a transport, construct a request, activate polling,
or decode by model ID alone. Standard SunSpec decoders remain authoritative;
the flavor has no semantic override, custom model, extension fact, or write
path. It creates no write authority, configuration mutation, canonical PV
publication, private binding, or automatic support declaration. A later
deployed exact `GO` is qualification evidence only and is not a product-family
support claim.

This page adds the identifier to no live-qualification record. The
registry-selected V3 record keeps its closed list of the two earlier
identifiers and is not amended here. Registry dispatch, the sanitized chain
fixture, any live-smoke flavor allowlist, and any registry pin are downstream
steps that consume this contract.
