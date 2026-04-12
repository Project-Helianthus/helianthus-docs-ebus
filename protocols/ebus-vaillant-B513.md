# Vaillant B513 Value-Range Query

`PB=0xB5`, `SB=0x13`.

## Status

`B513` appears in the john30 TypeSpec `General` namespace as a read-only
value-range query. It is not yet proven by current Helianthus MCP captures.

Evidence labels:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `LOCAL_MCP`: current Helianthus MCP runtime observations.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

The TypeSpec uses `@base(MF, 0x13)` and `@ext(0x4)` for `Valuerange`.

```text
Request payload:
  04 <id: UIN?>

Response payload:
  id  : UIN
  ign : up to 2 ignored bytes
  cur : UIN
  min : UIN
  max : UIN
  def : UIN
```

The request-side `id` is marked `@out` in TypeSpec. Treat the exact request
encoding as unconfirmed until captured against real hardware.

## Known Selectors

| Request selector | TypeSpec name | Direction | Shape | Evidence | Falsification test |
|---|---|---|---|---|---|
| `04` | `Valuerange` | read | register id plus current/min/max/default unsigned 16-bit values | `LOCAL_TYPESPEC` | Query `B513 04` for a known configurable value and show the response cannot decode as id/current/min/max/default. |

## Unknowns

- Which device classes implement `B513`.
- Whether the `id` field is always present in the request or only in the
  decoded response model.
- Whether the ignored bytes carry status, units, or access flags.

## References

- Public TypeSpec: [general.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/general.tsp)
