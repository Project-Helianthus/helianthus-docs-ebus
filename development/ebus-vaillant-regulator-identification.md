# VRC Explorer regulator catalog identification

The [neutral regulator reference](../protocols/vaillant/ebus-vaillant-regulators.md)
records exact EID and decoded SPN pairs. Explorer preserves raw EID, raw
software version, and the raw SPN field separately from its computed catalog
assignment.

A matched presentation row sets `identity.model_assignment_qualification` to `project_catalog`.
That annotation is not independently verified native model identity and does not
admit a protocol operation or device write. Missing, malformed or unlisted pairs
remain unknown. Catalog labels must not overwrite raw identity evidence.
