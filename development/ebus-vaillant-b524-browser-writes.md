# VRC Explorer B524 Browser write contract

This is an AGPL application contract for VRC Explorer. It describes offline
editing and explicitly confirmed native scalar writes. It does not establish a
native writable register, codec, range, or device effect.

## Visual configuration

The visual `scan` command accepts only adapter connection options
`--transport`, `--host`, `--port`, `--source-address`, and optional `--preset`,
besides help. There is no replacement adapter flag. Omit `--preset` to choose it
in the startup dropdown with its description. Destination, output, trace,
fixture replay, auxiliary reads and enrichment are configured in the startup
UI; coverage and description acquisition belong to the planner. A non-TTY scan
requires an explicit preset before transport creation.

`browse` accepts no configuration argv; its visual file picker opens JSON
offline. Connect and per-parameter editing are Browser actions. Technical
`discover`, `replay-trace`, and `b524` commands remain scriptable.

The retired scan-plan, operation-plan, preview-plan, description-budget,
request-budget and probe-constraint options are rejected. There are no hidden
global request or description budgets. Finite profile coverage, explicit visual
scope, bounded transport retries and actual request accounting remain in effect.

## Sessions and identity

Opening JSON starts an offline Browser session. Offline edits change only the
local artifact and preserve the observed value and provenance. They never mark a
device write confirmed.

The user must select **Connect** to provide transport, endpoint, and destination.
Connect reads and verifies the native controller identity before a live session
exists. A Browser opened after a scan receives that session context, but still
rechecks it before a write. Qualification identifies the controller by exact EID,
raw software and hardware bytes, and API version/revision from the profile
manifest; remote OP06 rows additionally require their own remote class and
firmware evidence. A matching controller profile does not substitute for
remote identity, and a failed recheck never erases prior evidence or becomes a
successful live result.

## Editable scalar values

The Browser can offer a scalar editor only for a concrete OP02 or OP06 selector
with a known codec, fresh writable/access and identity evidence, and an
unambiguous write address. An effective exact-profile description supplies limits
when present. Encoding, codec, width, minimum, maximum and STEP are validated
before confirmation; every known min/max/STEP violation is rejected. Missing
limits never permit bypassing a known constraint. An absence or incomplete limit
does not prevent the user-confirmed
exception. It displays the
native target `(destination, OP, GG, II, RR)`, baseline and proposed raw/value
forms, and numeric enum code. Enum editors are dropdowns that retain numeric/raw
identity. Unknown codes remain visible in the current display and are never
coerced to a first option; a dropdown requires an explicit enabled known
selection. A label does not establish a codec, writability, or native meaning.

Known false gates and excluded ranges are disabled with their reason. Unknown
gates are shown as unknown, never converted to false. A user may explicitly confirm the limited exception for an absent or incomplete limit, including
unknown STEP or a string with known encoding. That exception cannot bypass a
readonly row, unknown codec, identity mismatch, ambiguous write address, or a
contradictory qualified description.

## Confirmation and execution

Before a write, the Browser performs fresh identity, access, and baseline reads.
If the baseline changed, it presents the new baseline and requires another
confirmation. The confirmation names the exact target, old and new value, and
numeric enum codes where applicable. For absent or incomplete limits there are two
separate confirmations, in order:

1. A dedicated exception acknowledgement names the missing min/max/STEP fields,
   known codec, concrete target and proposed raw value.
2. A distinct final write confirmation shows the parameter, exact target and
   old → new value after the fresh context reads.

One combined acknowledgement cannot authorize this path. A changed baseline or
effective description invalidates both confirmations; the user must edit and
confirm again. A no-op sends zero writes.

All Browser transport operations share one serialized session queue. The final
pre-read, one native OT01 write, and readback are serialized as one operation.
There is one write attempt only: timeout, ambiguous feedback, reconnect, or
partial failure never auto-resubmits it. Bounded read retry or reconnect may
classify recovery as `desired`, `other`, or `unknown`; it cannot claim that a
write succeeded. **Recheck** is read-only. A later write starts a new operation
and requires fresh confirmation.

Only readback of the exact selector confirms the desired value. Native Event
writes remain disabled. Internal edit and operation artifact schemas may remain
available for runtime compatibility; retaining them does not revive public
command-driven write plans or event execution.

## Profile acquisition and reminders

The planner shows each description source and per-class override with finite
selected scope and actual request accounting. The known BASV2/SW0507 local
profile defaults to zero implicit descriptions. `full` and `research` acquire
eligible writable descriptions; unknown profile/type and explicit override also
acquire them. Readonly rows never Describe, generic IIFF metadata never qualifies
a concrete row, and a known missing description stays missing.

An unknown profile/type shows a one-time reminder to use `full` within configured
bounds and manually share JSON. It does not upload data or start additional
requests automatically.

## Evidence boundary

This contract governs application behavior only. Native B524 facts remain scoped
to `(OP, GG, II, RR)` in the protocol references. Historical labels or prose do
not override a correlated raw width from the effective exact profile.
