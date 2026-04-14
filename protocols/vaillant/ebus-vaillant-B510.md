# Vaillant B510 SetMode / Controller-to-Boiler Operational Data

`PB=0xB5`, `SB=0x10`.

## Status

`B510` is modeled by john30 TypeSpec as a passive/write `SetMode` command in
the heating-circuit mode family. Historical Vaillant notes describe it as
operational data from room/controller to burner/boiler.

This document supersedes the weaker older label "Status/Diagnostic" for
`B510` in the top-level Vaillant identifier overview.

Evidence labels:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `LOCAL_MCP`: current Helianthus MCP runtime observations.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `PUBLIC_CAPTURE`: public Pittnerovi eBUS trace examples.

## Wire Shape

Known `SetMode` shape:

```text
Request payload:
  00
  hcmode
  flowtempdesired
  hwctempdesired
  hwcflowtempdesired
  ign
  disable bits
  ign
  release/control bits
```

The exact byte widths and scaling come from ebusd data types (`hcmode`,
`temp1`, `temp0`, `IGN`, and bit fields). Do not decode bytes without the
request context and target profile.

## Local and Public Captures

Operator-provided traffic included:

```text
REQ:  10 08 b5 10 09 00 00 00 ff ff ff 01 00 00
RESP: 01 01

REQ:  10 08 b5 10 09 00 03 ff ff a0 ff 01 c8 00
RESP: 01 01
```

Current Helianthus MCP passive specimens also showed `B510` from source `0x10`
to target `0x08` with request payload `0003ffffa0ff01c800`, and broadcast
`B510` from `0x10` to `0xfe` with payload `0600`.

The Pittnerovi public page includes periodic `B5 10` frames between controller
and boiler. Treat that page as public capture corroboration, not as a complete
modern schema.

## Falsification Tests

- Change controller mode/setpoints and passively capture `B510`; falsify the
  `SetMode` mapping if the fields do not track the changed values.
- Compare captured `B510` bytes against controller B509 monitor registers whose
  names mirror `B510` payload bytes; falsify if the monitor registers do not
  match.
- Capture a topology where `B510` is not controller-to-boiler and document the
  alternate source/target role.

## Unknowns

- Full semantics of all disable/release bits across controller generations.
- Whether the broadcast `B510 06 00` form is part of the same `SetMode` family
  or a separate broadcast selector.
- Whether non-BAI targets reuse the same payload layout.

## References

- Public TypeSpec: [hcmode_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/hcmode_inc.tsp)
- Public config corpus: [john30/ebusd-configuration](https://github.com/john30/ebusd-configuration/tree/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant)
- Public capture/reference: [Pittnerovi eBUS page](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/)
- Historical PDF: [Vaillant_ebus.pdf](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/Vaillant_ebus.pdf)
