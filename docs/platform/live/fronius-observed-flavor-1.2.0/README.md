# Fronius Observed Flavor 1.2.0 Walk Observation

This directory publishes the public-redacted observation behind the exact
Common identity tuple and ordered chain of the
[Fronius observed SunSpec flavor V1.2](../../../../architecture/protocol-routing-vendor-fronius-observed-flavor-v1-2.md).
It is the falsifiable artifact for that contract's `Proven` labels. It is
documentary evidence from one read-only model-chain walk: it is not a live
qualification result, not a Fronius support claim, and not permission to select
the flavor in a qualification run.

The machine-readable record is [`evidence.json`](./evidence.json). It uses the
closed public shape of the Fronius live packets
(see [`../fronius-m4-04-0.6.51/`](../fronius-m4-04-0.6.51/)), restricted to the
fields a read-only walk supports: the target identity tuple, the acquisition
parameters, the ordered chain headers, and the registry outcomes. It contains
no network endpoint, private address, MAC address, serial number, credential,
raw register payload, site name, capture date, time of day, or process
identifier.

## Observation

One read-only walk of a Fronius inverter, from the SunSpec signature through the
consuming `FFFF/0` terminal, recorded:

- manufacturer `Fronius`, model `Symo GEN24 10.0`, and version `1.42.9-1`, the
  decoded Common `Mn`, `Md`, and `Vr` strings; the NUL padding of the
  fixed-width strings is not part of the identity;
- the ordered chain
  `1/65, 113/60, 120/26, 121/30, 122/44, 123/24, 160/88, 124/24, FFFF/0`;
- a contiguous extent of `381` words. The chain geometry fixes this number: the
  two signature words, the two header words plus the length of each of the eight
  models, and the two terminal header words. A reader can recompute it from the
  published chain;
- acquisition over Modbus TCP, unit ID `1`, FC03 only, with the SunSpec
  signature at normalized PDU offset `40000`. Writes were forbidden and none
  were performed.

The chain equals the V1.1 chain entry for entry and in order. The Common version
string is the only element of the V1.1 identity tuple that differs: those
packets record `1.41.11-1`.

## Registry Evaluation

The registry evaluation of this walk reported capability
`sunspec.inverter.three_phase.monitoring@1.0.0` as `ADMITTED`, with exactly one
`113/L60` source in the chain, and reported each of the flavors
`sunspec.flavor.fronius.gen24.float.observed@1.0.0` and
`sunspec.flavor.fronius.gen24.float.observed@1.1.0` as `FIRMWARE_MISMATCH`:
manufacturer and model matched and the version string did not.

No registry has evaluated flavor `1.2.0` against this walk yet, so the record
holds no `MATCHED` result. The flavor contract is the exact admission tuple
that the downstream registry step consumes.

## Redaction

Withheld from this record:

- every holding-register word of the walk. The Fronius live packets publish
  model headers only, and this record carries the same subset;
- the Common serial-number field, which was zeroed before anything was derived,
  and the Common option and device-address fields;
- the endpoint, address, site, capture date, and time of day.

Field-level values stay `PRESERVED_PRIVATE_NOT_PROMOTED`.

## Limits

One walk is the whole basis. The record says nothing about repeatability across
operating states, decoded values, scale factors, or sentinel use, and nothing
about any other model, version string, or market variant. Those stay `Unknown`
in the flavor contract.
