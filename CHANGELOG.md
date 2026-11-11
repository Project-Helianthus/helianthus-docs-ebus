# Changelog

## Unreleased

- Breaking API naming change: owned GraphQL names and registered MCP names use
  the adopted snake_case spellings. Zone values use `zone_room_temperature` and
  `zone_room_humidity`; unresolved value names remain expressly provisional.
  The six circuit setter keys use their selector-qualified names. The misleading
  frost-protection float writer is withdrawn without an enum replacement.
  Three metric families use constant `unit` labels with numeric scales preserved;
  `_total` counters retain their names. Removed spellings are rejected.
- The candidate service `0700` body and `0702` request use
  `outdoor_temperature` for the previously documented `outside_temperature`.
  The prior spelling is documentary correspondence only. The candidate's
  support and physical behavior remain unknown.
- Other non-B524 names remain under investigation; their current spellings do
  not imply that they satisfy the naming contract. In particular, `duration`
  retains its spelling while its activity and zero semantics remain unresolved.
