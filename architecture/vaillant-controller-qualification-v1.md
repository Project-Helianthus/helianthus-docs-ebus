# Vaillant controller qualification v1

A system controller at an exact address is qualified for a thermal-map row when
its Identification descriptor at that address has manufacturer `0xB5`, its exact
device ID and product number are a row of
`tests/fixtures/vaillant_regulator_identity_crosswalk_v1.json`, and
`protocols/vaillant/fixtures/b524-op02-requester-register-matrix.csv` lists that
row for the pair. The software version is recorded beside the result and does
not restrict the pair. An unlisted pair, a malformed descriptor, or a product
number that is an `0xFF` replacement is unknown.

The published key of a controller is the device ID and product number the bus
transmits. A product-line name is not a key. The level of each pair is
`declared`. `tested_on_hardware` is recorded only with the path of a public
test record in a project repository. No such record is named here. The level
does not change `qualified_use_permitted`.

## Identification

The descriptor is the eBUS Identification service `0x07` `0x04`, ten bytes, as
[the identification layout](ebus_standard/03-identification.md) records it.
Byte 0 is the manufacturer. Bytes 1–5 are the device ID. Bytes 6–7 are the
software version. Bytes 8–9 are the product number, BCD, least-significant byte
first, as [the regulator page](../protocols/vaillant/ebus-vaillant-regulators.md)
states. The layout grade is Proven. The product-number reading and each
crosswalk pair are Hypothesis. Those grades are recorded beside the level. A
grade does not condition the declaration.

## Declared rows and the boiler target

The record lists each group and register that a cutover page maps and that the
register matrix lists for the pair. The list is keyed by the device IDs the bus
transmits. A row the matrix does not list is not declared. Each row keeps its
evidence grade beside it.

A bus participant is a declared boiler target when its Identification descriptor
has manufacturer `0xB5` and a device ID of the boiler class that the B509
device-type gate names, at the address it answers on. The flow row opcode
`0x0D`, selector `18 00`, `DATA2c`, is declared for that target. Its meaning
grade stays Hypothesis. A heat-pump class identity is not a boiler target. A
valid routed boiler reply on that row publishes
`thermal.measurement.heat_generator_flow_temperature` with no qualified-binding
condition.

## Writes

Write operations of these rows follow the access flag the device reports for
each register. This record grants or withholds none.

## Transition

Malformed or incomplete input is refused with a reason and changes nothing. A
valid direct observation that conflicts retires the current result atomically.
A matching sparse refresh may keep it.

The revision token is `vaillant-controller-qualification-evidence-gap/v1`. The
scope is `native_controller_qualification`. The fixture records the SHA-256 of
the crosswalk file and of the register matrix, and the validator recomputes
both.
