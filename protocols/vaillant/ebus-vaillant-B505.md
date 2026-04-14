# Vaillant B505 SetOperationalData

`PB=0xB5`, `SB=0x05`.

## Status

`B505` is the write-side companion to `B504`. It is op-coded and
device/state-dependent. Treat every write as side-effectful until a safe test
fixture proves otherwise.

Evidence labels:

- `LOCAL_CODE`: Helianthus registry/gateway code.
- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

The Helianthus generic method builds:

```text
Request payload:
  op      : byte
  payload : bytes, optional and op-dependent
```

The response is usually interpreted as ACK/status plus any target-specific
bytes. A successful eBUS response alone does not prove that the target accepted
or persisted the requested state.

## Known Selectors and Shapes

| Selector bytes | Name/context | Request data | Evidence | Falsification test |
|---|---|---|---|---|
| `09 01..09 07` | Timer periods Monday..Sunday | `timer` composite | `LOCAL_TYPESPEC` | Write on isolated hardware, then read back with the matching `B504 02..08` selector and show no matching change. |
| `2E 01..2E 07` | Daily temperature setpoints | three `temp1` values | `LOCAL_TYPESPEC` | Write setpoints, read back with matching `B504 19 <day>` selector, and show no match. |
| `2D` | Room temperature offset | `temp` | `LOCAL_TYPESPEC` | Write a harmless test offset on non-production hardware and show no matching room-offset change. |
| `05`, `06`, `07` | archived quick commands | command-specific | archived john30 config | Prove that the selector is read-only or that the target never ACKs it on devices that claim support. |

## Local Validation Rule

For Helianthus writes, protocol-level ACK is not sufficient. A safe write must
be followed by a read-back through the authoritative read path for that field.
This is the same rule used by the existing B509 boiler config write path.

## Unknowns

- Complete write selector namespace.
- Which selectors require user, installer, or service authentication state.
- Whether some controllers silently clamp values while still ACKing the frame.

## References

- Public TypeSpec: [timer_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/timer_inc.tsp)
- Public TypeSpec: [tempsetpoints_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/tempsetpoints_inc.tsp)
- Public TypeSpec: [roomtempoffset_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/roomtempoffset_inc.tsp)
- Consolidated local reference: [`ebus-vaillant.md`](ebus-vaillant.md)
