# Vaillant B509 Register Access

`PB=0xB5`, `SB=0x09`.

## Status

`B509` is a flat-register access primitive with an operation byte and a 16-bit
address in the common BAI/BASV-style form. Register semantics and codecs are
target-specific.

The BAI00 boiler register map used by Helianthus is documented separately in
[`ebus-vaillant-B509-boiler-register-map.md`](ebus-vaillant-B509-boiler-register-map.md).

Evidence labels:

- `LOCAL_CODE`: Helianthus gateway and registry code.
- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `LOCAL_MCP`: current Helianthus MCP runtime observations.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.

## Wire Shape

```text
Read request:
  0d addr_hi addr_lo

Write request:
  0e addr_hi addr_lo data...
```

Helianthus accepts either of these response forms for reads:

```text
0d addr_hi addr_lo data...
addr_hi addr_lo data...
```

The first form echoes the read opcode; the second echoes only the address.

## Local MCP Evidence

Current MCP bus summary showed active `B509` initiator-target traffic from the
gateway initiator to multiple Vaillant targets, including BAI00. This proves
the local gateway is using `B509` actively, but it does not by itself prove
individual register semantics.

## Known Boiler Registers

Helianthus currently treats direct BAI00 `B509` as authoritative for most
`boilerStatus` state/config/diagnostics. Examples from the implemented BAI00
map:

| Register | Semantic use | Codec |
|---:|---|---|
| `0x1800` | boiler flow temperature | `DATA2c` |
| `0x4400` | central heating pump active | on/off |
| `0x0200` | water pressure | `DATA2b` |
| `0x0500` | flame active | on/off |
| `0xBB00` | gas valve active | on/off |
| `0x8300` | fan speed | `UIN` |
| `0x2E00` | modulation percent | `SIN / 10` |

The full list is in
[`ebus-vaillant-B509-boiler-register-map.md`](ebus-vaillant-B509-boiler-register-map.md).

## Falsification Tests

- Disprove flat addressing by capturing a valid `B509` exchange where bytes
  after `0x0D` or `0x0E` are not a 16-bit address.
- Disprove write semantics by producing a write ACK that is accepted as
  success without a matching read-back. Helianthus requires ACK plus read-back
  for semantic writes.
- Disprove a register mapping by changing the physical state and showing the
  documented register value does not change while an alternate register does.

## Unknowns

- Complete register map per product ID and firmware generation.
- Meaning of invalid/unavailable response markers across device classes.
- Whether every target accepts both echoed-op and address-only response forms.

## References

- Public TypeSpec: [_templates.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/_templates.tsp)
- Public config corpus: [john30/ebusd-configuration](https://github.com/john30/ebusd-configuration/tree/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant)
- Boiler register map: [`ebus-vaillant-B509-boiler-register-map.md`](ebus-vaillant-B509-boiler-register-map.md)
- Consolidated local reference: [`ebus-vaillant.md`](ebus-vaillant.md)
- Historical Vaillant reference: [Pittnerovi eBUS page](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/)
