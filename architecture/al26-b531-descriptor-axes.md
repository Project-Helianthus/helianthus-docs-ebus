# B531 local descriptor counts and physical extent

## Evidence boundary

The [public native B531 contract](../protocols/vaillant/ebus-vaillant-b531-hem-power-limit.md)
comes first: its candidate layouts are **Hypothesis**, unconfirmed on the wire;
OP00 request and response remain **Unknown**. This residual representation
contract supplies no new native layout. Examples are synthetic, for the
heat-pump energy-management family, and do not qualify physical support.

**Hypothesis:** a local descriptor uses source `F1`, a destination selected
from its slot, and command-inclusive `NN`. The symbolic `slotA` and `slotB`
destinations below are independent identity values, not physical addresses.
The local response count at `R[0]` belongs to another representation.

## Separate axes

The following table is normative for these finite examples. A supplied number
is **Proven** only as a synthetic input, never as a native wire observation.

| Property | Representation | Unsupplied grade | Relation |
|---|---|---|---|
| logical_descriptor_count | command-inclusive NN | Unknown | independent |
| local_response_count | local R[0] | Unknown | independent |
| available_buffer_length | available local buffer | Unknown | independent |
| physical_wire_length | physical wire extent | Unknown | independent |

| Operation | Descriptor status |
|---|---|
| 01 | independent Hypothesis |
| 02 | independent Hypothesis |
| 03 | independent Hypothesis |
| 00 | Unknown; no descriptor body |

| Consequence | Grade |
|---|---|
| physical ACK | Unknown |
| physical CRC | Unknown |
| echo/correlation | Unknown |
| remote effect | Unknown |

Identity is `(source, destination, operation)`. Altering the slot preserves the
new destination identity; altering the operation preserves that distinct
operation. OP01, OP02 and OP03 cannot be collapsed into one descriptor operation.
Source `F1` is fixed for these examples; no alternative source is qualified.

## Finite synthetic examples

The [fixture](fixtures/al26_b531_descriptor_axes.json) contains explicit
descriptor objects and separately graded counts. The baseline has source `F1`,
destination `slotA`, operation `01`, and four unknown extent properties.
`slot_only`, `operation02_only` and `operation03_only` vary one identity axis
at a time. `nn_only`, `local_count_only` and `available_only` independently
supply one count. `partial_available` changes only the available buffer length
relative to `distinct_counts`.

In `distinct_counts`, NN is 3, local R[0] count is 5, available buffer length is
5, and physical wire extent is **Unknown**. These remain four properties:
NN is not copied into R[0], a local count is not physical length, and equal
local count and buffer length imply no general equality. No packet is
constructed, no body length is derived, and no echo/correlation rule is supplied.
`op00_unknown` has no fabricated descriptor body.

Physical qualification, presence, freshness and execution remain separate
**Unknown** properties in every example. Synthetic input evidence does not
upgrade any of them. A descriptor implies neither ACK nor CRC nor remote effect.
On partial input, retain supplied counts and any available raw evidence as
independent fields; a missing extent must not erase useful input or manufacture
missing bytes. These examples contain no raw capture and no packet bytes.
Admission remains fail closed: unknown physical evidence cannot qualify an
operation or authorize a transmission. There is no new transmit route or write
admission here.

This page does not define numeric scaling, cache retention, target admission,
effective-limit calculation or publication policy. It changes no eBUS MCP or
GraphQL contract. Nothing here establishes a stable contract before Helianthus 1.0.
