# B509 heat pump refrigerant poll

Status: candidate. This page describes gateway behaviour that is not
implemented. It defines a read-only poll of the refrigerant circuit and
compressor rows of the heat pump family. The wire facts (selectors, codecs,
scales, units and the evidence each row needs) are in the
[heat pump register map](../protocols/vaillant/ebus-vaillant-b509-heatpump-register-map.md)
and the correspondence fixture beside it; this page adds no wire fact and
qualifies no row.

## Selectors

The poll covers exactly the rows of the table in the section "Refrigerant and
compressor numeric rows" of the register map. It sends no selector outside that
table. Each selector keeps the unresolved evidence stated in that table.

## Cycle

- One cycle issues at most one read of each listed selector. A cycle starts at
  least 60 seconds after the start of the previous cycle.
- A read that fails, times out or is refused is not repeated within the same
  cycle. The other reads of the cycle proceed.
- The poll uses only the read operation `0D` for the two-byte registers and the
  data-point read `54` for the five-byte selectors, each sent exactly as listed.
  That the configuration byte `00` of these selectors selects a read is a
  **Hypothesis** (Open Questions item 12 of the register map). The poll never
  sends the write operation `0E` and never writes to the target.

## Applicability

- The poll reads only from a heat source whose documented class is heat pump:
  the two-byte registers only from a target identified as `heat_pump`, and the
  five-byte selectors only from a target identified as
  `heat_pump_interface_unit`. A two-byte register is never sent to a heat pump
  interface unit.
- It sends no read to a boiler, to a target whose class is not established, or
  to a target whose identity has changed until its class is established again.

## Default and triggers

- The poll is off by default: it sends no read until it is enabled for the
  installation.
- A request for exported or displayed values, such as a metrics scrape or a
  status read, never starts, schedules or hastens a poll read. Exported values
  come only from retained observations.

## Retained state and export

Each read keeps its raw response bytes beside the decoded value. A point is
exported only when its row has a final name, a unit, a codec in the
correspondence fixture and a class that matches the identified target, and when
the evidence the register map names as unresolved is stated: the pressure
reference for the two refrigerant pressures, the unit for the compressor speed.
A point without that evidence stays withheld: no value is exported for it, and
no other selector fills it, even one with the same name. A failed read of one
selector leaves the other points of the cycle unchanged, and the point keeps its
last-known-good observation with its age.

## Owner approval

Enabling the poll on an installation is the owner's decision at live testing.
Nothing in this page authorizes a read on any installation or field bus. The
poll is new bus traffic: the selectors, the cycle and the applicability above
bound it, and they do not permit it.
