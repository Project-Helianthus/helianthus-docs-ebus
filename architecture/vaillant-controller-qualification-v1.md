# Vaillant controller qualification v1

This is the native, read-only applicability rule for the accepted B524 thermal
mapping. It is deliberately one observed tuple, rather than a family claim.

## Direct `0x07/0x04` observation

The target is the directly observed eBUS address `0x15`. The Identification
response is the standard `0x07/0x04` response: manufacturer byte, five-byte
ASCII device identifier, then two opaque software bytes and two opaque hardware
bytes. The exact rule is:

| Field | Required normalized value | Wire evidence |
| --- | --- | --- |
| Manufacturer | `VAILLANT` | `0xB5` |
| Device ID | `BASV2` | ASCII after trimming padding |
| Software version | `0507` | two identification bytes, rendered as uppercase hex |
| Hardware version | `1704` | two identification bytes, rendered as uppercase hex |
| Address | `0x15` | response source and queried target agree |

The source document records the BASV2 (VRC720f/2) observation at address
`0x15`, HW `1704`, and SW `0507`. Its byte digest and immutable source link are
in the checked fixture. `0xB5` is the observed Vaillant manufacturer byte in
the public `0x07/0x04` service contract. The registry still requires its
separate current complete manufacturer/device/serial witness; Identification
does not itself carry a serial number.

The accepted B524 thermal map references this rule and cannot be applied until
the registry supplies a current qualified result for this exact tuple. No rule
is inferred for another BASV variant, CTLV device, controller family member,
firmware, hardware revision, address, or a value derived from B524 data.

## Current-use and retirement boundary

The registry result binds the direct address, complete current identity witness,
observation and proof generations, observation time, this rule revision, and
the immutable native evidence reference/digest. Missing, sentinel, malformed,
unsupported, or conflicting members reject without changing a current result.
A matching sparse refresh may retain an already direct proof; it cannot combine
last-known-good fields into a new proof.

The result retires when identity is replaced, the address splits, an observation
conflicts, the underlying proof retires, or an applicable product/software/
hardware member changes. It grants no write, operation, SemReg, gateway, live,
or physical qualification authority.
