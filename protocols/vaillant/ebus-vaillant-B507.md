# Vaillant B507 Heat Pump Load/Poll Protocol

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. Helianthus documentation uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

`PB=0xB5`, `SB=0x07`.

## Status

**Enrichment research** -- not yet live-validated on a Helianthus bus.
B507 is heat-pump specific (CTLV2 + HMU topology). It is absent from
john30/ebusd-configuration <!-- legacy-role-mapping:begin -->master<!-- legacy-role-mapping:end --> and was absent from helianthus-docs-ebus
prior to this document.

Helianthus live bus runs BAI00 + BASV2 (gas boiler topology). B507 frames
do NOT appear on this bus type. All information below is derived from
community ebusd-configuration forks.

Evidence labels:

- `FORK_JONESPD`: jonesPD/ebusd-configuration `ebusd-2.1.x/en/vaillant/08.hmu.csv`
- `FORK_XERION`: xerion3800/ebusd-configuration `ebusd-2.1.x/en/vaillant/08.hmu.csv`
- `FORK_MORPHZ`: morphZ/ebusd-configuration `ebusd-2.1.x/de/vaillant/08.hmu00.HW5103.csv`, `custom/myconfig.csv`
- `FORK_KOLIBRIE`: kolibrie-eric/ebusd-configuration `ebusd-2.1.x/de/vaillant/08.hmu.csv`, `ebusd-2.1.x/en/vaillant/08.hmu.csv`

**Confidence:** MEDIUM-HIGH for protocol existence and 0900 poll; MEDIUM for
HeatpumpLoadSensor decode; LOW for write semantics.

## Wire Format

```
Initiator -> Target request:
  [0xB5] [0x07] [0x09] [sub] [...]

Target response (ID 0900):  :HEX:* (variable length, undecoded)
Target response (ID 0931):  D1C (1 byte, signed 0.5-step %, range -64.0 to +63.5)

QQ (initiator):    0x15 (CTLV2 initiator address)
ZZ (target):       0x08 (HMU -- Heat Management Unit)
```

## Device Scope

**Target:** HMU (Heat Management Unit) at target address `0x08`.

In heat pump systems, `0x08` is the compressor/heat exchanger management
unit. In gas boiler systems, `0x08` is BAI00 -- a different device class at
the same address.

B507 is heat-pump specific. It does not appear on BASV2/BAI00 gas boiler
systems.

## Message Table

| ID (hex) | Name | ebusd type | Data fields | Direction | Poll interval | Confidence |
|----------|------|-----------|-------------|-----------|--------------|------------|
| `09 00` | unknown_m_poll_60s_b507h (`unknownMPoll60sB507h`) | `r` | `:HEX:*` (variable, undecoded) | CTLV2 (`0x15`) -> HMU (`0x08`) | 60 s | MEDIUM-HIGH |
| `09 31` | heatpump_load_sensor (`HeatpumpLoadSensor`) | `r` / `r5` | `percent1:D1C` (1 byte, %) | CTLV2 -> HMU | 5 s (morphZ custom) | MEDIUM |
| `09` (write) | -- (unnamed) | `*w` | -- (undecoded capture) | unknown initiator -> HMU | observed | LOW |

### D1C Encoding

ebusd Data type 1C -- signed 1-byte, 0.5 unit/LSB. Operational range
0-100%. Values above `0x63` (99.5%) or negative likely indicate a sentinel
or error state.

### ID 0900 Response

Not decoded in any fork. The `:HEX:*` wildcard in ebusd config means
response length and field structure are unknown.

### Write Direction (ID 09, *w entries)

Passive bus capture of write traffic (kolibrie-eric 2019 only). Content
unknown. May be a configuration push from CTLV2 to HMU.

## Evidence

### Fork Sources (4 named, 2-3 effectively independent)

| Fork | File | Line | URL |
|------|------|------|-----|
| jonesPD | `ebusd-2.1.x/en/vaillant/08.hmu.csv` | L4 | https://github.com/jonesPD/ebusd-configuration/blob/b1d506ae9b8d63bf5855532860e719d72d174cb4/ebusd-2.1.x/en/vaillant/08.hmu.csv#L4 |
| xerion3800 | `ebusd-2.1.x/en/vaillant/08.hmu.csv` | L4 | https://github.com/xerion3800/ebusd-configuration/blob/e30e2573c2ab47f2dd82da9158381b9cace96477/ebusd-2.1.x/en/vaillant/08.hmu.csv#L4 |
| morphZ | `ebusd-2.1.x/de/vaillant/08.hmu00.HW5103.csv` | L5 | https://github.com/morphZ/ebusd-configuration/blob/9c895ecd6bed3cea7676c89638aa9833ce31d2f5/ebusd-2.1.x/de/vaillant/08.hmu00.HW5103.csv#L5 |
| morphZ | `custom/myconfig.csv` | L209 | https://github.com/morphZ/ebusd-configuration/blob/9c895ecd6bed3cea7676c89638aa9833ce31d2f5/custom/myconfig.csv#L209 |
| kolibrie-eric | `ebusd-2.1.x/de/vaillant/08.hmu.csv` | L2, L4 | https://github.com/kolibrie-eric/ebusd-configuration/blob/2cd7c92e0a494808cdc38a6cdf36bf699054f286/ebusd-2.1.x/de/vaillant/08.hmu.csv#L2 |
| kolibrie-eric | `ebusd-2.1.x/en/vaillant/08.hmu.csv` | L5, L21 | https://github.com/kolibrie-eric/ebusd-configuration/blob/2cd7c92e0a494808cdc38a6cdf36bf699054f286/ebusd-2.1.x/en/vaillant/08.hmu.csv#L5 |

### Independence Assessment

jonesPD and xerion3800 have near-identical 2025-era content and their
`08.hmu.csv` files appear to share a common ancestor -- they confirm each
other's content but may not constitute fully independent observations.
kolibrie-eric (2019) confirms coarse B507 traffic from a physical capture
but does not decode registers. morphZ is the primary source for the
`HeatpumpLoadSensor` decode. Effective independent sources: 2-3, not 4.

### Fork Chronology

kolibrie-eric (2019) is the oldest observation -- B507 traffic was captured
on physical hardware before 2020. morphZ (2024) first decoded the
`HeatpumpLoadSensor` name. jonesPD and xerion3800 (2025) independently
replicate the 60-second poll entry.

## Falsifiable Claims

1. On a heat pump system with CTLV2 + HMU, ebusd passively captures frames
   with PBSB=`B507` and QQ=`0x15` / ZZ=`0x08` at approximately 60-second
   intervals.
2. The `HeatpumpLoadSensor` (ID `0931`) returns a D1C byte that tracks
   compressor load percentage in real time when the heat pump is active.
3. B507 frames do NOT appear on a gas boiler bus (BASV2 + BAI00).

## Open Questions

1. Full response layout for ID `0900` -- `:HEX:*` means no fork has decoded it.
2. Write semantics for B507 ID `09` (`*w` entries in kolibrie-eric) --
   content and trigger condition unknown.
3. Sub-selector space -- only `0x00` and `0x31` known after the `0x09` prefix.
4. Hardware scope -- whether B507 is specific to HMU hardware variant HW5103
   or applies to all HMU units.
5. Relationship to B51A (heat pump statistics) -- B507 appears to be a
   simpler, parallel poll rather than a replacement.
