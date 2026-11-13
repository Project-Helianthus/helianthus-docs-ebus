# Changelog

## Unreleased

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
