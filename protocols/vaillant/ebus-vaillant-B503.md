# Vaillant B503 Diagnostic, Service, and Live-Monitor Selector Family

`PB=0xB5`, `SB=0x03`.

## Status

This is a reverse-engineered selector family, not a single fixed schema.

Evidence labels used below:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `LOCAL_MCP`: current Helianthus MCP runtime observations.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

Observed and configured reads/writes use a two-byte selector in the request
payload:

```text
Request payload:
  family_or_block : byte
  selector        : byte
```

The known examples use `selector=0x01` for error/service lists and
`selector=0x03` for HMU live-monitor status.

## Known Selectors

| Request payload | Direction | Name | Response shape | Evidence | Falsification test |
|---|---:|---|---|---|---|
| `00 01` | read | `Currenterror` | five `UIN` error slots (`errors`) | `LOCAL_TYPESPEC`, `LOCAL_CAPTURE` | Read `B503 00 01` from BAI00 and disprove that response bytes decode as five little-endian unsigned 16-bit slots. |
| `01 01` | read | `Errorhistory` | index plus `errorhistory` payload | `LOCAL_TYPESPEC` | Query multiple history indexes and show response does not change with the index byte or does not carry an error-history record. |
| `02 01` | install write | `Clearerrorhistory` | ACK/side effect | `LOCAL_TYPESPEC` | On isolated hardware, write the documented clear command and show error history remains unchanged after successful ACK. |
| `00 02` | read | `Currentservice` | five `UIN` service/error-style slots | `LOCAL_TYPESPEC` | Read `B503 00 02` from a target with a service message and show no five-slot response exists. |
| `01 02` | read | `Servicehistory` | index plus `errorhistory` payload | `LOCAL_TYPESPEC` | Query indexes and show no indexed service-history payload. |
| `02 02` | install write | `Clearservicehistory` | ACK/side effect | `LOCAL_TYPESPEC` | Clear on isolated hardware and verify history is unchanged after ACK. |
| `00 03` | service write/read pair | HMU live-monitor enable/status | response begins with `status`, `function` | `LOCAL_TYPESPEC`, `LOCAL_CAPTURE` | Enable live monitor, then read `B503 00 03`; falsify if first two data bytes do not track live-monitor status/function changes. |

## Current Error Decoding

`Currenterror` is modeled as `errors`, and `errors` is five unsigned 16-bit
values. Helianthus currently treats `0xFFFF` as an empty slot when decoding the
operator-provided capture.

Relevant local lab frame:

```text
REQ:  f1 08 b5 03 02 00 01
RESP: 0a 19 01 ff ff ff ff ff ff ff ff
```

The first response slot is `19 01`, i.e. little-endian `0x0119` decimal `281`.
During the same investigation, an unpublished operator UI observation reported
`F.281 Flame loss during the stabilisation period`.

This proves only a local correlation:

- `B503 00 01` carried decimal `281` in the first active-error slot.
- The unpublished operator UI observation reported `F.281`.

It does not prove that every Vaillant `F.xxx` code is always mirrored as the
same decimal value on every device generation.

## Live-Monitor Note

The vendored HMU TypeSpec says live-monitor reads require an enable message
first. A TypeSpec comment includes a frame shaped like:

```text
REQ:  31 08 b5 03 02 00 03
RESP: 0a f4 01 ff ff ff ff ff ff ff ff
```

The first response byte is modeled as `status`, the second as `function`.
Other bytes in the 10-byte response are not documented by this file.

## Local MCP State

At the time of this documentation pass, current Helianthus MCP exposed boiler
status and passive bus summaries but did not expose an active B503 error plane.
That is a gateway surface limitation, not evidence that B503 lacks the error.

## Unknowns

- Whether the first request byte is best named `block`, `base`, or
  `sub-family`.
- Whether `B503 00 01` always maps active `F.xxx` errors directly by decimal
  code across BAI, HMU, and other Vaillant device classes.
- Exact byte layout of HMU `LiveMonitorMain` beyond the first two modeled
  bytes.

## References

- Public TypeSpec: [errors_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/errors_inc.tsp)
- Public TypeSpec: [service_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/service_inc.tsp)
- Public TypeSpec: [08.hmu.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.hmu.tsp)
- Data type reference: [`../../types/ebusd-csv.md`](../../types/ebusd-csv.md)
