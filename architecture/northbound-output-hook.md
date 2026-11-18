# Northbound output hook

Status: contract tracked by
[docs issue #1222](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/1222).
This page is a partial slice of that issue.

## Authority

The [runtime driver lifecycle](runtime-driver-lifecycle.md) owns registration,
start and stop. Health is the snapshot in the
[G5 runtime lifecycle MCP contract](../api/mcp.md#g5-runtime-lifecycle-mcp-contract-d4).
**Proven** means a fact
already stated by those public contracts: an empty hook list is a valid
registration, the reserved names fail as unimplemented, start and stop belong
to the driver manager, and health is that manager's snapshot. **Hypothesis**
names nothing on this page. **Unknown** names device publication and the lens
rules, which stay with their owners. Qualification of a device family stays a
separate record.

The runtime driver lifecycle states that the first host requires an empty hook
set and that all hook declarations fail. This page narrows that rule for one
name only: for the hook spelling `output` on a northbound descriptor, this page
takes precedence over that rule. The runtime driver lifecycle names this page
as the one narrowing of that rule. For every other hook name and every other
descriptor direction, that rule stands unchanged.

## Hook admission

A northbound descriptor may register the hook spelling `output`. The only
accepted non-empty hook list on that descriptor is the single name `output`.
An empty hook list remains a valid registration.

The `output` declaration carries hook version `1`, the only supported
version. An `output` declaration with no version or with any other version
fails as an unsupported version.

The hook spelling `output` is accepted only on a northbound descriptor. The
southbound eeBUS driver registers with an empty hook list, and that
registration stays valid. Declaring `output` on a descriptor that is not
northbound is refused.

The host refuses every hook name other than `output`. The reserved names
`mcp`, `setup`, `portal`, `semantic` and `evidence` fail as unimplemented.
Any name that is neither `output` nor one of those reserved names fails as
unknown. A refused hook list admits nothing and leaves the previous registry
and its last-known-good state unchanged.

Registering that descriptor does not by itself publish a fact.

## Lifecycle and health

Start and stop are the existing driver-manager lifecycle. A disabled
descriptor does not start.

Health is read from the existing driver-manager snapshot. Its health
indicators are observed state, reason and the safety-quarantine flag. They are
members of the closed driver object in the
[MCP read data](../api/mcp.md#read-and-mutation-data), which keeps every
member that contract lists; this page defines no reduced object. That
snapshot remains the health read on the
existing MCP driver object. There is no lifecycle GraphQL API and no second
health API.

## Boundary

This page does not restate the lens rules and does not choose which devices
are published.
