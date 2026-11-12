# B524 energy-command roles and requested instances

## Native contract and evidence

The [native B524 contract](ebus-vaillant-b524.md#411-writes-with-iiff-dhw-cylinder-and-buffer-registers)
comes first: OP02 and OP06 are independent namespaces, and request context
retains the instance. This supplement narrows that contract to five candidate
energy-command targets. The [synthetic tuples](fixtures/aj02_b524_energy_roles.json)
are metadata examples, not captures, complete telegrams or sendable packets.
No source, destination, product, firmware or capture conditions are supplied.
No public native observation qualifies these candidate meanings in this slice.

**Hypothesis:** each row below is a distinct local-namespace command target.
Command role, opcode, group, requested instance, register, field and codec are
separate properties. The Vaillant controller family and local-energy variant
labels scope the synthetic examples; they establish no installed family support.
The direction label `command` denotes the candidate role, not observed traffic.

## Five candidate targets

All selector numbers below are hexadecimal. Width is in bytes and concerns
only the isolated declared field, never a complete message.

| Command role | Opcode | Group | Requested instance | Register | Field | Codec | Width bytes | Grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| energy-setpoint | 02 | 01 | FF | 0004 | setpoint | binary32 | 4 | Hypothesis |
| energy-hysteresis | 02 | 00 | FF | 0027 | hysteresis | binary32 | 4 | Hypothesis |
| energy-control | 02 | 01 | FF | 000D | control | Unknown | Unknown | Hypothesis |
| energy-offset | 02 | 00 | FF | 00A2 | offset | binary32 | 4 | Hypothesis |
| energy-activation | 02 | 00 | FF | 00B6 | activation | byte | 1 | Hypothesis |

The readback context uses instance `00`. It must not replace requested instance
`FF` in command identity or establish an equivalent command target. Changing
only FF to 00, OP02 to OP06, group, register, command role or field cannot
inherit a command declaration. The three four-byte scalars remain separate
from the one-byte activation and the unknown-width control. No activation
values or control enumeration are established here.

## Unknowns and retained knowledge

| Property | Status |
| --- | --- |
| Binary32 byte order | Unknown |
| Field offsets | Unknown |
| Control enumeration | Unknown |
| Native units | Unknown |
| Response forms | Unknown |
| Installed capability | Unknown |
| Applied state | Unknown |

**Proven:** metadata lookup cannot establish applied state or installed
capability. This is an evidence limitation, independent of each candidate's
Hypothesis grade and physical qualification, which remains Unknown.
A binary32 declaration supplies no byte order, unit, field offset or response
form. The control codec and width remain unprovided; they must not inherit
binary32 from nearby scalars. A one-byte activation supplies no boolean enum.

Preserve raw values alongside partial interpretations. Unknown fields or a
failed interpretation must not erase retained raw evidence or prior
last-known-good partial state; that state has uncertain freshness and does not
qualify new data. Missing or malformed evidence withholds a usable claim.
No command builder or writer is included, and these candidates establish no
physical result, writable capability or permission to act.
