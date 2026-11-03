# B50F OP02 independent status spans

## Evidence and scope

This Vaillant-family supplement records the bounded candidate facts for issue
858. No native capture or vendor specification establishing these mappings is
available in this slice. Each allocation below is **Hypothesis**, not Proven.
The [synthetic tuples](fixtures/aj12_b50f_status_spans.json) illustrate the
candidate partitions; they are not observed telegrams or proof of wire behavior.

Candidate selectors are PB=0xB5, SB=0x0F, OP=0x02, variant B50F, family vaillant.
Direction, source, destination, absolute byte coordinates, product and firmware
context, and physical qualification are **Unknown**. Container numbers express
independent identities, not byte offsets or adjacency. Bit numbers are local to
each byte, with bit 0 least significant. Each span is eight bits; no unit is
assigned. No physical PDU is constructed.

## Relation to the existing B50F layout

The [B50F section](ebus-vaillant.md) lists a candidate layout for `B5 0F 02`:
values in both request and reply, six structures at offsets 3..8, burner state
at offset 9 and gas-pump state at offset 10. That layout is retained as a
separate **Hypothesis** and is not superseded or promoted here. This supplement
adds no evidence for or against its direction or offsets, so those coordinates
stay Unknown for the purposes of this page; the two statements are not
competing claims. If the earlier offsets hold, the six structures are the six
containers below in order and the two later bytes are the separate burner and
gas-pump raw bytes; the partitions here apply either way.

## Candidate field partitions

Masks retain all bits, including reserved bits. A category is not an individual
flag name. The entries in the last column are individual names in ascending bit
order; `Unknown` means no individual names were supplied.

| Field | Allocated mask | Reserved mask | Allocated category | Individual names | Grade | Coordinate grade | Qualification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| status_container_1 | 0x7F | 0x80 | Unknown | Unknown | Hypothesis | Unknown | Unknown |
| status_container_2 | 0x7F | 0x80 | Unknown | Unknown | Hypothesis | Unknown | Unknown |
| status_container_3 | 0x7F | 0x80 | temperature-limit | Unknown | Hypothesis | Unknown | Unknown |
| status_container_4 | 0xFF | 0x00 | plausibility/channel | Unknown | Hypothesis | Unknown | Unknown |
| status_container_5 | 0x0F | 0xF0 | Unknown | valve_1_open, valve_1_error, valve_2_open, valve_2_error | Hypothesis | Unknown | Unknown |
| status_container_6 | 0x07 | 0xF8 | Unknown | valve_open, error, air_check | Hypothesis | Unknown | Unknown |
| burner_status | Unknown | Unknown | Unknown | Unknown | Hypothesis | Unknown | Unknown |
| gas_pump_status | Unknown | Unknown | Unknown | Unknown | Hypothesis | Unknown | Unknown |

Containers 1 and 2 allocate bits 0..6 and reserve bit 7. Container 3 has seven
temperature-limit flags at bits 0..6 and reserves bit 7; their individual names
remain Unknown. Container 4 allocates all eight plausibility/channel bits;
individual channel names remain Unknown. Container 5 has two valve open/error
pairs at bits 0/1 and 2/3, reserving bits 4..7. Container 6 allocates valve-open,
error and air-check at bits 0..2, reserving bits 3..7. Reserved bits have no
assigned semantic name. Burner and gas-pump status are separate raw bytes with
Unknown internal partitions; neither is an alias of a container or of the other.

## Raw and partial evidence

Preserve each complete raw byte independently. Allocated and reserved portions
must together reconstruct the original byte. Reserved does not mean zero,
invalid or safe. Missing bytes remain absent, distinct from explicit zero; a
partial tuple retains its available bytes without inventing absent spans.
A last-known-good value remains separate from a missing current value, and
neither establishes current physical status.

OP03 demand-bit names and integrity-byte coordinates do not apply here.
Existing temperature, demand, integrity and feedback declarations are outside
this slice. These candidate names establish no writable behavior, actuator
behavior, safety check or physical status inference. Evidence grade, unknown
metadata and physical qualification remain independent. No entry is Proven.

## Synthetic tuple reading

The named bytes in the linked file are independent synthetic values, not ordered
wire positions. Cases include 0x80 and 0x7F for containers 1/2/3, 0xFF for
container 4, 0xF0 for container 5 and 0xF8 for container 6. Each bit in each
container is varied independently, with only one different nonzero burner or
gas-pump byte at a time. These examples preserve unnamed allocated flags and
reserved bits without asserting a native direction or absolute coordinate.
