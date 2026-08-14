# Fronius Observed SunSpec Flavor V1.1

## Status and evidence boundary

`sunspec.flavor.fronius.gen24.float.observed@1.1.0` is an experimental,
read-only successor to
`sunspec.flavor.fronius.gen24.float.observed@1.0.0`. It does not reinterpret
the V1 contract. Each identifier admits only its own exact ordered chain.

This contract is bounded to one sanitized observation of a Fronius
`Symo GEN24 10.0` reporting firmware `1.41.11-1`. It is not a product-family
support claim and does not infer another model, firmware, market variant, or
chain. The observation followed gateway merge
`81e18e67a1b7d1adff5273c8c43f08243a3e2a0a`; a preliminary registry run
correctly returned `CHAIN_MISMATCH` against V1 because the observed chain also
contained Model `123/L24`. This statement motivates the versioned contract; it
is not FMV3-M4-05 completion evidence.

No endpoint, serial, raw register payload, private capture, vendor register
row, or SunSpec table is reproduced here.

## Exact admission tuple

The capability must already be admitted as
`sunspec.inverter.three_phase.monitoring@1.0.0`. Flavor evaluation then requires
all of these independent exact gates:

- Common manufacturer: `Fronius`, exact string match;
- Common model: `Symo GEN24 10.0`, exact string match;
- Common version/firmware: `1.41.11-1`, exact string match;
- exact ordered chain match:
  `1/65, 113/60, 120/26, 121/30, 122/44, 123/24, 160/88, 124/24, FFFF/0`;
- exactly one admitted Model `113/L60` source for the required capability
  facts.

Model `123/L24`, Immediate Controls, is a standard model selected only through
the exact core decoder key `(123, 24, schema_revision)`. It is not a
vendor-specific extension. Its presence in this flavor changes neither its
ownership nor its access boundary: the decoder is read-only and the model's RW
metadata creates no write authority.

There is no case folding, prefix match, semantic-version range, model-ID-only
fallback, reordering, subset match, optional insertion, or int+SF substitution.
V1 remains exact for
`1/65, 113/60, 120/26, 121/30, 122/44, 160/88, 124/24, FFFF/0`; V1.1 remains
exact for the chain above. A different chain needs separate evidence and a new
versioned contract.

## Outcomes and ownership

Evaluation uses the same complete, terminal-verified snapshot as capability
admission and preserves V1's closed reasons and precedence:
`CAPABILITY_NOT_ADMITTED`, `COMMON_IDENTITY_MISMATCH`, `FIRMWARE_MISMATCH`,
`CHAIN_MISMATCH`, `AMBIGUOUS_SOURCE`, and `MATCHED`.

The flavor does not select a transport, construct a request, activate polling,
or decode by model ID alone. Standard SunSpec decoders remain authoritative;
the flavor has no semantic override, custom model, extension fact, or write
path. It creates no write authority, configuration mutation, canonical PV
publication, private binding, or automatic support declaration. A later
deployed exact `GO` is qualification evidence only and is not a product-family
support claim.
