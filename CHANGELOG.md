# Changelog

## Unreleased

- The Modbus multi-endpoint runtime page keeps the asset as the publication
  scope and follows the common identity rule in docs-semantic for what it
  publishes: one resource per unit, anchored on an operator label until the
  common element inventory lists an identification scheme, with the native
  child key as the documented native token. The pack class token and the routed
  unit are a selector and an address, never identity; a hybrid inverter is one
  asset and one resource; a replaced unit is a new equipment resource; one
  device reached through two labels has one identity or is withheld as
  `ASSET_CONFLICT`. The per-class digest rule for asset identifiers is removed.
  The Huawei candidate evidence page cites the stable child key of the native
  gateway contract in docs-modbus as the one native identity evidence of a
  child and drops the serial-digest allowance. The sentence pins of
  `tests/test_modbus_v1_addon_runtime_contract.py` and
  `tests/test_modbus_vendor_evidence_v1.py` move in place. Follow-ups: the
  gateway allocator and its identity vectors in
  Project-Helianthus/helianthus-ebusgateway#1539, the mapping gate statements
  of the Huawei gateway families, and the `esn_digest` member of
  `docs/platform/manifests/modbus-vendor-evidence-v1.json`.
- Plane, projection and lens wording states its native meaning. The GraphQL,
  MCP and Portal API pages, the architectural decisions, the registry catalog
  capability page, the B524 mapping page (now titled "B524 MCP Semantic Plane
  Mapping") and the semantic startup page each say whether they mean a registry
  plane, a registry projection, a method bundle or a gateway data family, and
  that none of these is a plane, a lens or a target projection of the common
  semantic contract in docs-semantic. No type, field, tool, argument or route
  name changes. `scripts/check_semantic_term_qualifiers.py` rejects the
  unqualified plane, lens and canonical identity terms on every page outside
  its exact quotation list, and its test runs in the local gate.
- The shared registry boundary, canonical photovoltaic semantics and draft
  candidate fact graph pages no longer define the canonical identity of a
  semantic fact or name this repository or the eBUS registry as semantic
  owner; they point to the common semantic contract in docs-semantic. The
  shared registry boundary text changes, so the digest that docs-eebus pins
  for it in `scripts/platform_cross_seed_snapshot.yaml` moves in a follow-up
  docs-eebus cross-seed change.
- The required `Modbus Trusted Revision` status is produced by
  `.github/workflows/modbus-trusted-revision-pr.yml` on `pull_request` events,
  with the same job, permissions, checkouts and pinned immutable anchor run as
  the protected `pull_request_target` workflow, which stays byte-identical.
  Docs CI path filters include the new workflow, repository tests fail when it
  differs from the protected workflow in anything but its name and trigger or
  when another workflow file names a job of that name literally, and the Modbus
  multivendor boundaries page states the guarantee, its limit and the pull
  requests that need the owner's explicit approval before merge.
- Breaking documentation URL change: the frame-atomic visibility revision pages
  `frame-atomic-visibility-v2.md` to `frame-atomic-visibility-v9.md` under
  `architecture/adaptermux/` are removed without redirect pages.
  `frame-atomic-visibility.md` now states the design the gateway implements,
  with a History section that summarizes each revision and maps earlier
  section citations; the SYN padding page is marked historical. Links from
  other repositories to the removed pages need the same update.
- Breaking documentation URL change: 154 page file names under `architecture/`,
  `protocols/` and `types/` use lowercase kebab-case. Directories, headings,
  anchors and page text are unchanged apart from the renamed file names in
  links and path mentions, every inbound link in this repository follows the
  new names, and no redirect page remains.
  Links from other repositories to the earlier file names need the same update.
  Tree indexes for `api/`, `architecture/`, `deployment/`, `development/` and
  `protocols/` list every page, and `architecture/page-status.json` keeps the
  status each renamed page states for itself from a closed set; a rename never
  changes a status. Repository control files keep their conventional names.
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
