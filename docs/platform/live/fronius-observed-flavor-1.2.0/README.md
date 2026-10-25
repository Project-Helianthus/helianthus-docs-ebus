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
register word, site name, capture date, time of day, or process identifier.

The directory holds one further file, the sidecar
[`common-block.json`](./common-block.json). It lists the sanitized register
words of the SunSpec Common block (Model 1) and of nothing else, so the
firmware decoding can be checked against an observed register dump; see
[Common Block Sidecar](#common-block-sidecar).

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

## Common Block Sidecar

[`common-block.json`](./common-block.json) records the holding-register words
of the walk from the SunSpec signature at normalized PDU offset `40000` through
the Common device-address register at offset `40068`: 69 words, being the two
signature words, the Model 1 header, and the 65 Model 1 data registers. It
records function code `3`, unit ID `1`, and base offset `40000`. Its `label`
field is the provenance reference: the label of this packet,
`fronius-observed-flavor-1.2.0`. The label names no device, site, endpoint,
date, or digest.

The 16 Common serial-number registers, offsets `40052` through `40067`, are
zeroed, and the file carries no word of any other model: the word at offset
`40069`, which opens the next chain entry, is not published. The file has no
endpoint, date, time of day, or digest.

Reading the words as big-endian pairs of ASCII characters, with NUL padding
that is not part of the identity, reproduces the tuple above and the first
chain entry:

- offsets `40000` and `40001` decode to the SunSpec signature `SunS`;
- offsets `40002` and `40003` hold model ID `1` and length `65`, the first
  chain entry `1/65`;
- offsets `40004` through `40019` (`Mn`) decode to `Fronius`;
- offsets `40020` through `40035` (`Md`) decode to `Symo GEN24 10.0`;
- offsets `40044` through `40051` (`Vr`) decode to `1.42.9-1`;
- the option registers, offsets `40036` through `40043`, hold zero words, and
  the device-address register, offset `40068`, holds `1`.

The sidecar covers Model 1 only. The other chain entries and the extent are
recorded in [`evidence.json`](./evidence.json) as headers, and the capability
outcome as a registry result, each without register words.

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

- every holding-register word of the walk after the Common block, that is, the
  words of every other model and of the terminal. The Fronius live packets
  publish model headers only, and `evidence.json` carries the same subset;
- the contents of the Common serial-number field, which was zeroed before
  anything was derived;
- the endpoint, address, site, capture date, and time of day.

Apart from the Common block words in the sidecar, field-level values stay
`PRESERVED_PRIVATE_NOT_PROMOTED`.

## Limits

One walk is the whole basis. The record says nothing about repeatability across
operating states, decoded values, scale factors, or sentinel use, and nothing
about any other model, version string, or market variant. Those stay `Unknown`
in the flavor contract.
