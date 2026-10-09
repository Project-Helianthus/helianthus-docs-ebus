# SunSpec Model-Chain Wire Reference V1

This reference records SunSpec wire structure only. It is an independent summary
of the Apache-2.0 `sunspec/models` catalog pinned at
`7abdf8982d5364f8ae916deee18aac86c11be36d`; it does not reproduce model files
or specification tables.

## Model occurrences

A SunSpec model occurrence has a model ID, declared length, header offset and
payload offset. The following standard shapes are relevant to the observed
catalog: Common `1/L66` and compatibility shape `1/L65`; inverter integer
models `101`, `102`, `103` at `L50`; FLOAT models `111`, `112`, `113` at
`L60`; `120/L26`, `121/L30`, `122/L44`, `123/L24`, and `124/L24`.

Model `160` has declared length `8 + 20 * N`, where `N` is its reported group
count. A reader can retain an unknown model occurrence when its declared extent
is in bounds. A known model with a different length is a distinct wire shape;
it must not be decoded as an ID-only match.

## Chain framing

The SunSpec signature precedes the Common Model. Model occurrences are ordered,
not a set: duplicate and unknown IDs retain their ordinal and raw words. The
terminal marker is `FFFF/0`. A valid structural walk has nonzero lengths before
that marker, checked extent arithmetic, no overrun, and no trailing words after
the marker. Raw words are big-endian Modbus register words.

These rules preserve a received wire structure. They do not establish device
support, acquisition policy, typed decoding, capability admission, or write
behavior.
