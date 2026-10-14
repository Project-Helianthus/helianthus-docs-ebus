# BASV0 B524 description-profile reuse

The BASV0 metadata fixture is a candidate input to application profile reuse.
It may be selected only after the local EID, software raw value, hardware raw
value, API version, and revision match the fixture identity. A selector match without
that profile match must not reuse a bound or codec.

`DescribeParameter` and `DescribeDeviceParameter` echo group and register and
have equal-width limit spans. That proves response structure, not the value
codec. The consumer may use a decoded range only when the fixture labels it
`selector_qualified` and `qualified`; otherwise it must preserve the raw bytes
and expose no range-based validation authority.

The observed BASV0 DHW bivalence maximum is 20. The BASV2 maximum of 50 is a
separate observation. Selection must not substitute either value across these
profiles, software versions, or installation configurations.

For the BASV0 ventilation RR0001 observation, the profile-qualified UIN decoder
uses a two-byte response while presence remains unknown. Treating that response
as one-byte UCH, or treating an unknown slot as installed ventilation, is unsupported.
Remote descriptions whose identity is unqualified remain display-only or raw
evidence. They do not admit a device function or write path.

The profile itself has no current values and no write evidence. A consumer must
keep access flags distinct from write acceptance and use an independently
qualified, current interaction before attempting a write.
