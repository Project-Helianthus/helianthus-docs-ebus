# MSP-085 0.6.40 Final 18-Leaf Promotion Lock

This directory publishes the `PUBLIC_REDACTED` result derived from the final
VR940/eBUS campaign `m8-18c-0640-20260813e`. The deployed Home Assistant
add-on was `0.6.40`; its gateway source commit was
`f45ccecc27166596e3521d2ccc9683d17d6f5070`, and the deployed gateway binary
SHA-256 was
`971f3d247fab02346549d83ecbdbc9bbaefc7296a373af803e716a513f097e9d`.

The owner-held campaign used one `PRE_RESTART` and one `POST_RESTART` window.
The process hashes changed across restart, the SHIP connection generation
changed from `109` to `110`, and the persistent VR940 trust and peer bindings
remained stable. Both windows produced `11` cross-protocol `MATCH` outcomes
and `7` eeBUS-native `NATIVE_VALID` outcomes. The production gateway assembler
therefore returned `18` promoted real leaves, `0` withheld real leaves, and
the same four immutable retired historical records.

The private campaign hash is
`sha256:4e71ee022e54fbaf36452d6ad774ac4f72ebd0ea28803f67b86d7a474d486262`.
Its exact private bytes SHA-256 is
`ae932de0a3a02242da9923627978279d4ae3f4aa159cec060c140e9fd4763b00`.
The published result bytes SHA-256 is
`376e683b0930d475f6032db401ae8bdca4bafcd7dd69c64aee164ee939a5baa6`,
and its result hash is
`sha256:0f07e2b0624dccefa4e5ef6497d5d221e4dc1febebb17988fbaba83dc46bfb64`.
An owner-local read-only verification against the exact private campaign,
both capture receipts, all M7/M8 source inputs, the deployment receipt, the
canonical gateway source checkout, and the deployed binary returned `PASS`.
Re-derivation produced the published result byte-for-byte; only this verdict
and the non-secret hashes above are public.

The source-bound M8 evidence id is
`mrcv1:sha256:fa1a7577c51fe96b93210c1ced85a1b4f9775e0d80f3fdbb6eaba7c190d199d4`
and its report id is
`mrcrv1:sha256:7fc747d08717f502be64d3f32e94fb4ec2710e1622a93976522d084cfdcf8be9`.
Its protected semantic-registry view uses the fixed 11-leaf M8.5
cross-protocol eBUS core; the immutable source captures retain the full
registry. The 18 semantic paths are the
exact paths in the canonical captured multi-leaf registry; the redacted result
intentionally publishes candidate ids and hashes rather than operational
selectors or paths.

Every promoted leaf remains `LOCKED_NOT_EXPOSED`. `READY_FOR_M9_PLANNING` is a
DAG disposition, not consumer exposure: this record does not add GraphQL,
Portal, Home Assistant, command-routing, write, or source-precedence behavior.
