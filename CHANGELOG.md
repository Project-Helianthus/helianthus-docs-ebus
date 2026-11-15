# Changelog

## Unreleased

- Each of the twelve thermal cutover and disposition pages under
  `architecture/` has a "Native attachment" section. It names the native
  resource each value belongs to (the system group of the B524 semantic root,
  a zone or circuit instance, the native hot-water group, the solar circuit, a
  device slot, or the boiler's B509 register space), the relation candidates
  of `architecture/fixtures/structural-relation-candidates-v1.json` that reach
  it or their absence, and the element inventory disposition of the target.
  Where that disposition is `unknown`, or the value has no element inventory
  entry, the page says that the common subject is not decided and proposes
  none. No page places a pump on a circuit service, pressure or a system
  value on the controller's system service, or a role or resource in
  dimension text. `architecture/energy-merge.md` states the hand-off to the
  common model: heating, cooling and hot-water usage, the reporting source
  path and the lifetime window stay distinct; the `climate` merge, the
  register-over-broadcast precedence and the two-slot form are losses of the
  one `EnergyTotals` target.
- The B524 thermal map fixture
  `architecture/fixtures/vaillant-semreg-thermal-map-v1.json` and the
  hot-water fixture `architecture/fixtures/dhw-setpoint-semreg-cutover-v1.json`
  key each row by the native identity of its value
  (`PB SB OP GG II RR`), never by a gateway GraphQL field. Each row names the
  native resource it attaches to in native terms (the B524 semantic root's
  system group, or the controller's native hot-water group), its relation
  candidates by reference to
  `architecture/fixtures/structural-relation-candidates-v1.json` or their
  explicit absence with a reason, and a copy of the element inventory entry of
  its target definition. Both temperature facts and the hot-water setpoint
  fact are `unknown` with the reason `catalog.reason.subject_unresolved` and
  no plane, so no row forms a FactKey, carries a role or resource in dimension
  text, or places a thermal quantity on a common resource; native values keep
  their native unit. The hot-water fixture records its service-identity gap
  as an unresolved subject: both projection cases are `withheld` with that
  reason and no loss. The controller qualification sidecar binds to the rows
  by native key in its new `thermal_rows` member.
  `scripts/validate_vaillant_semreg_thermal_map.py` checks both fixtures and
  rejects a row attached by ordinal, a false join to a native resource that
  does not hold the row's key, and a dangling endpoint (a relation candidate
  naming a native resource the fixture does not list). The Go contract module
  `tests/semreg_thermal_map_contract` pins a newer SemReg module and checks
  every row's target and disposition against SemReg's element inventory.
  Follow-ups: the thermal cutover pages and the energy merge page, the
  Prometheus coverage page's thermal rows, and the gateway's thermal
  publication.
- The B524 structural decision catalog hands the controller's attachments to
  the common model as relation and identity candidates. The new fixture
  `architecture/fixtures/structural-relation-candidates-v1.json` lists each
  attachment of SD-05, SD-06, SD-07, SD-09, SD-10, SD-15 and the
  functional-module page with its native endpoint kinds, the native identity
  evidence of each end and its classification, the evidence grade, the
  validity scope and one disposition: `relation_candidate`,
  `configuration_only`, `absent` with its reason, or `unresolved`. The
  zone-to-circuit assignment stays `unresolved` and names both native
  statements (`GG=0x03 RR=0x0013` read with an offset under laboratory scope,
  and `GG=0x03 RR=0x001C` `zone_circuit_assignment`) until the specialist
  review records which register establishes it. A controller-mediated device
  slot and the same unit's direct bus entry share no anchor key source, so
  they stay two views with the disposition `two_views_unresolved`. SD-10 and
  SD-15 give parenting to the common model instead of consumers; each listed
  entry gains a `Common-model candidate` row, and the functional-module and
  structure-discovery pages cite the fixture. No quantity is placed and no
  common relation definition is proposed. New validator
  `scripts/validate_structural_relation_candidates.py` with
  `tests/test_structural_relation_candidates.py`. Follow-ups: the thermal map
  fixtures and the gateway's resource and relation publication.
- The SunSpec model-chain contract defers canonical field identity to the
  common element inventory in docs-semantic and keeps native model and point
  names only: the required facts of the three-phase monitoring profile are
  profile keys with their native point, not field identifiers. A new section
  defines a multi-device chain and states, for its inverter, meter, storage
  control and per-device repeat occurrences, the resource kind each would
  describe and whether it is attributed. Only the inverter of a single-device
  chain is attributed; the semantic values of a multi-device chain are withheld
  with the reason `MULTI_DEVICE_UNATTRIBUTED`, while the native provider and
  native surface proceed. The sentence pins of
  `tests/test_sunspec_model_chain_contract.py` move in place. Follow-up: the
  gateway's SunSpec publication and its golden envelopes.
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
