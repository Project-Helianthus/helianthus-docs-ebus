# VRC Explorer: B524 description acquisition and offline validation

#### 4.2.2 Targeted acquisition

Read the parameter first. Description acquisition is planner configuration, not
a public command-line budget or probe option. The recommended known
BASV2/SW0507 local profile performs **zero implicit** OP01/OP07 requests.
`full` and `research` acquire eligible writable descriptions. An unknown
profile/type, an explicit per-class override, or a custom policy may also acquire
them. Read-only rows never request descriptions.

Candidates use the profile-scoped `FLAGS & 0x02` inference, including candidates
whose scalar codec is not yet known. An unknown codec is retained raw and remains
unqualified; it is not a reason to omit an otherwise eligible description request.
The inference selects candidates only: it neither proves live writability nor
authorizes a write. For each selected candidate, send its complete
profile-qualified description selector: OP=01h for the system family and OP=07h
for the device family. Keep the raw request and reply, decoder revision, source,
selected scope, actual request accounting, and qualification outcome in the
artifact. Unsupported or known-missing descriptions are explicit missing data;
no short-probe fallback is allowed. Generic IIFF descriptions remain class
metadata and cannot validate a concrete writable row.

#### 4.2.3 Offline value changes

A matching qualified description validates encoding/type/width, min/max and step
for every edit, including non-enum numeric values. A contradicted value is rejected.
When no qualified description is available, VRC Explorer warns that the edit is
unvalidated and permits its existing explicit confirmation. Offline editing does
not send a device write. Historical static ranges remain hints, not validation
authority. See the [historical constraint catalog](../protocols/vaillant/ebus-vaillant-B524-register-map.md#constraint-catalog).
