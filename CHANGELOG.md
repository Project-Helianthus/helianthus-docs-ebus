# Changelog

## Unreleased

- `architecture/enh-ens-conformance-tests.md` reserves unused
  session-extension nibbles beside the assigned host commands 0x0 to 0x3 and
  the assigned adapter replies 0x0 to 0x3 and 0xA to 0xC. Session to mux: 0x4 TARGET, 0x5 UNTARGET, 0x6 BEGIN,
  0x7 STAGE, 0x8 COMMIT. Mux to session: 0x4 TARGETED, 0x5 UNTARGETED, 0x6
  SLOT, 0x7 SLOT_END, 0xD TARGET_ERROR. Each reserved frame uses the encoded
  two-byte form; the short form is not used. A session that never sends
  TARGET sees an unchanged ENH stream. An unreserved nibble is still an
  explicit protocol error. A TARGET sent to an adapter with no extension
  receives that existing unknown-command error. Response timing is Unknown.
  The CC0 page `protocols/enh.md` lists only the reserved nibble values,
  without extension names, and keeps them under its unknown-command error for
  an adapter without the extension. The pages do not implement the mux.

- `architecture/northbound-output-hook.md` states the northbound hook spelling
  `output` at hook version `1`; a missing or other version fails as
  unsupported. `architecture/runtime-driver-lifecycle.md` names that page as
  the one narrowing of its hook rule. An empty hook list stays a valid
  registration, including the southbound eeBUS driver. Every other hook name
  is refused: the reserved names `mcp`, `setup`, `portal`, `semantic` and
  `evidence` fail as unimplemented, and any other name fails as unknown.
  Registering the descriptor does not publish a fact. Start and stop stay the
  driver-manager lifecycle, and a disabled descriptor does not start. Health
  reads that manager's snapshot through observed state, reason and the
  safety-quarantine flag, members of the full closed MCP driver object. The
  page does not restate the lens rules and does not choose which devices are
  published. `scripts/check_northbound_output_hook.py` pins those sentences.

- Mapped temperature rows of the eBUS thermal hand-off keep the native unit
  and state the SI unit kelvin, degrees Celsius plus 273.15. Humidity rows
  keep the native unit percent and state `unit.percent` as the semantic
  target, then the SI unit as a ratio, percent divided by 100. The
  statements are on the boiler, circuit, cylinder,
  domestic-hot-water measured and setpoint, humidity, solar-loop, zone room,
  zone setpoint and outdoor-temperature pages, on the mapped rows of
  `architecture/b524-semantic-mapping.md`, on the thermal air-temperature row
  of `api/semantic-snapshot-read.md`, and on the mapped rows of
  `architecture/fixtures/vaillant-semreg-thermal-map-v1.json` and
  `architecture/fixtures/dhw-setpoint-semreg-cutover-v1.json`. A row with no
  mapped quantity keeps the native unit only. The thermal map contract
  rejects a mapped row that lacks the SI unit or the conversion on that row.

- `architecture/naming.md` gives a function the maker names with a name of its
  own the vocabulary role `feature`: a closed list in the maker's spelling,
  with a definition or "meaning not established", in the subject or object
  slot of a native register name, with the predicate that the value class
  gives. The ban on product names in a name covers device products and
  models; a feature name is not a product name. The vocabulary lists
  `green_iq`, `fair` and `tri_vai` with that role, and both name checks accept
  such a term in the subject or object slot only and refuse a product or model
  name. B524 `OP=0x02, GG=0x00` RR=0x009A is `green_iq_enabled` (provisional:
  Boolean, polarity not established), RR=0x007E is `fair_mode` (provisional:
  the catalog decodes a float32, which fits neither `_enabled` nor `_mode`)
  and RR=0x003A is `tri_vai_unknown` (provisional: the rest of the name waits
  for the meaning of its kelvin value). The catalog, correspondence fixture,
  register map, name decomposition data and provisional-name evidence page use
  the names; that page lists 134 open rows with documented terms and 6 with
  indexed placeholders. No alias of the old names exists.

- B524 `OP=0x02, GG=0x00, RR=0x0007` is named `off_enabled` (`previous_name`
  `system_off`), final, with the observed Vaillant definition: 1 means that
  the system is switched off. The register map value cell reads
  `0=system on 1=system off`, and the catalog, correspondence, requester
  matrix, name annotation, semantic mapping and system-off cutover pages use
  the name. `OP=0x02, GG=0x02, RR=0x001E` (`circuit_state`) is final under the
  same rule; its only open point was hardware confirmation of the observed
  Vaillant definition. `architecture/naming.md` states that an observed
  Vaillant definition names a register without confirmation on the wire, that
  such a row is not provisional and that hardware qualification by device
  owners does not block the name; it lists the nine remaining `unknown`
  placeholders. `development/b524-provisional-name-evidence.md` lists 140 open
  rows. No alias of the old name exists. The gateway follows the fixture
  (Project-Helianthus/helianthus-ebusgateway#1483).

- `protocols/vaillant/fixtures/b509-register-name-correspondence.csv` has
  `codec` and `scale` columns after `unit`. They hold what the boiler and heat
  pump register maps state for each row: the codec of the `Codec / scale`
  column, or the `Type` column for the five-byte selectors, and the stated
  factor as a decimal multiplier (`SIN / 10` gives `0.1`; `0xE201` gives
  `100`). A row whose map states no codec, and the two operation rows, keep
  both cells empty. Every name, unit and open question is unchanged. The
  column table of `protocols/vaillant/ebus-vaillant-b509.md` defines both
  columns and states that an empty scale is not an unresolved factor.
  `protocols/vaillant/ebus-vaillant-b509-heatpump-register-map.md` has a
  "Refrigerant and compressor numeric rows" section that lists the final
  numeric refrigerant and compressor rows of the `heat_pump` and
  `heat_pump_interface_unit` classes and the evidence each needs: the pressure
  reference, absolute or gauge, for the refrigerant pressures and the unit for
  the compressor speed. `architecture/b509-heatpump-refrigerant-poll.md`
  defines the read-only poll of those rows: at most one read of each selector
  per cycle and at least 60 seconds between cycle starts, only on a target
  identified as a heat pump class, off by default and never started by a
  scrape or status read, with points that lack their evidence withheld.
  Enabling the poll on an installation is the owner's decision at live
  testing; the page authorizes no read on any installation.
  `tests/test_b509_register_name_correspondence.py` asserts that both columns
  equal the map pages, that the table matches the fixture and that the poll
  page states its bounds.

- `api/semantic-snapshot-read.md` has an "Assets with several sources"
  section. A source counts when it is admitted (live, not fenced, not retired)
  with a published, unfenced cursor of its current generation, and an asset
  with several sources is readable when at least one of its sources counts.
  Otherwise the entry is unavailable with `source_unavailable` when no source
  is admitted, `snapshot_unavailable` when no source has an accepted
  publication, and `publication_withheld` otherwise; a pending lifecycle
  control of any source keeps the whole asset closed. Each source's
  descriptor, cursors and fences stay visible, including a fenced or retired
  source, whose observations remain only as retained observations. Candidates
  of several sources coexist under one complete `FactKey` and a reader never
  adds or otherwise combines them into one value. The result for an asset with
  one source is unchanged, and seeing a source grants no control.
  `tests/test_semantic_snapshot_read_contract.py` asserts each of these rules
  and rejects a weakened wording of each. The request shape and the per-asset
  revision rule are unchanged. Follow-up: the gateway work under
  Project-Helianthus/helianthus-ebusgateway#1539.

- `deployment/prometheus-semantic-coverage.md` has a "Native point coverage"
  section with Target rows only for the optional native point export: one
  gauge family per physical quantity under `helianthus_native_`, each with one
  constant SI `unit` label (kelvin, pascals, cubic meters per second, joules,
  watts, seconds, hertz, amperes, volts, or a plain ratio or count), plus
  `helianthus_native_point_age` in seconds and
  `helianthus_native_render_overflow` without labels. The labels `protocol`,
  `device`, `index`, `point` and `unit` each have a closed documented domain
  and are native locators, never a semantic resource identity. The section
  states the rule for a clear interpretation, which the native registry
  evaluates; that values come only from retained observations, so a scrape
  sends no bus request; that a value is present only while fresh and the age
  while an observation is held; at most 1,024 value series in a fixed order
  with the rest counted; and that the export is off by default. The family
  names are provisional with an open question on the `native` qualifier. The
  sentences on native identity outside labels, label exclusions and
  unavailable facts now name the semantic series. `architecture/naming.md`,
  section Metrics, states the per-quantity native families, the `point` and
  `index` label keys and the SI constant unit.
  `scripts/validate_prometheus_semantic_coverage.py` checks both native
  tables (name pattern, one constant SI unit per family, closed label keys
  and domains, no family also emitted); the 107 emitted families are
  unchanged. `tests/test_prometheus_semantic_coverage.py` rejects a change of
  each field of every native row, a second unit on one family and a forbidden
  label key. Follow-ups: the gateway renderer and the native registry catalog.

- `docs/platform/promoted-semantic-consumers-v1.md` and its manifest
  `docs/platform/manifests/promoted-semantic-consumers-v1.json` map each
  target object (`zones[id=zone-1]`, `zones[id=zone-2]`, `dhw`, `system`) to
  one canonical resource in the new manifest member `resources`: the common
  resource kind (`resource.zone`, `resource.thermal_system`, or not decided for
  hot water, whose kind the element inventory holds as `unknown`), the
  candidate sources from both protocols with the public document that holds
  their native evidence, and the identity basis. An accepted basis is an
  operator declaration with a shared parent and slot or a shared native anchor
  key; an ordinal, a slot label, a name or an address is never one. Every
  mapping is `unresolved` and not merged, and each of the eighteen leaf rows
  carries that basis in `identity_basis`. `FILL_MISSING_ONLY` is the policy of
  the eBUS-typed GraphQL target over the candidates of one resource, not the
  internal merge. No leaf value or thermal quantity is placed on a common
  resource. `tests/test_promoted_semantic_consumers_v1.py` rejects a leaf or
  mapping without a recorded basis, a merge without an accepted basis, a
  mapping without candidates from both protocols or without provenance, and
  an undecided kind without its reason.
  `api/eebus-northbound-integrator-reference.md` states the same rule for
  integrators. Follow-ups: the gateway's replacement of its overlay and the
  Home Assistant consumer identity.

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
