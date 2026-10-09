# Huawei Proprietary Modbus Evidence

This reference records documentary wire facts only. SmartLogger, S-Dongle, and
EMMA are distinct proprietary device families; none of their address ranges or
identity strings establishes SunSpec behavior.

Huawei documents holding-register addresses as zero-based. For FC03, the PDU
offset equals the documented register address; no `+1` conversion applies.
Numeric fields are big-endian and most-significant word first. A string field
contains `quantity * 2` ASCII bytes, with only terminal NUL or space padding
removed after retaining the raw bytes.

The documented read-only family-specific candidates include SmartLogger unit
`0` FC03 offset `65521` quantity `1`; S-Dongle logical unit `100` FC03 offsets
`30068` quantity `2` and `37410` quantity `3`; and EMMA unit `0` FC03 offsets
`30000` quantity `15`, `30222` quantity `20`, and `30035` quantity `15`.
The Device Identification request form is FC2B/MEI `0x0E`; a documented child
object request has PDU `2B 0E 03 87`. These are documentary facts, not probing
instructions or proof of support on a particular endpoint.
