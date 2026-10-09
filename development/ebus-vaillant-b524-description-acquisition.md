# VRC Explorer: B524 description acquisition and offline validation

#### 4.2.2 Targeted acquisition

Read the parameter first. Acquisition includes all deduplicated, observed
writable candidates in the selected scope by default. An explicit caller budget
may limit acquisition; no default budget exists. Candidates use the profile-scoped static
`FLAGS & 0x02` inference is present, including candidates whose scalar codec is
not yet known. An unknown codec is retained raw and remains unqualified; it is
not a reason to omit an otherwise eligible description request. That inference
selects candidates only: it neither proves live writability nor authorizes a
write. For each selected candidate, send its complete
profile-qualified description selector: OP=01h for the system family and OP=07h
for the device family. Keep the raw request and reply, decoder revision and
qualification outcome in the artifact. Unsupported descriptions are explicit
missing data; no short-probe fallback is allowed. The implementation records
`eligible`, `attempted`, `matched`, `unavailable`, `unqualified`, and
`budget_skipped` counters per description family.

#### 4.2.3 Offline value changes

A matching qualified description validates encoding/type/width, min/max and step
for every edit, including non-enum numeric values. A contradicted value is rejected.
When no qualified description is available, VRC Explorer warns that the edit is
unvalidated and permits its existing explicit confirmation. Offline editing does
not send a device write. Historical static ranges remain hints, not validation
authority. See the [historical constraint catalog](../protocols/vaillant/ebus-vaillant-B524-register-map.md#constraint-catalog-ebusreg).
