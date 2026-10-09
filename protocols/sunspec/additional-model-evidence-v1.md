# SunSpec Additional Model Documentary Facts

The Apache-2.0 `sunspec/models` catalog pinned at
`7abdf8982d5364f8ae916deee18aac86c11be36d` includes integer AC-meter models
`201` through `204`, FLOAT AC-meter models `211` through `214`, environmental
models `302` through `308`, and grid/control models `125` through `145`.

The standard signature is read from PDU offset `40000` with FC03 and quantity
`2`. Later model headers carry `(model_id, model_length)` and model blocks are
bounded by their declared lengths. These catalog facts do not establish device
availability, decoding, control behavior, or write authority.
