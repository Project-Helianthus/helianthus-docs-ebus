# First Official Live Promotion Lock

This directory publishes the public-redacted result of the first official
M8/M8.5 campaign against a live VR940 runtime. The private capture, operator
identity, protocol addresses, trust material, and raw values remain outside the
public repository.

## Deployment Binding

- Gateway source commit:
  `39340f4f5aa79499957a42cfd977b2fe1218f823`
- Add-on source commit:
  `be9d74f3b5d9cc8ac8c5fb552939e5abbb450533`
- Gateway binary SHA-256:
  `bd1a1397b8fc94bb308739401efeb2aab7b2aee767b8110c59a0bfdfb9deb877`
- Add-on version: `0.6.37`
- Image digest:
  `sha256:27d0c4593f0c11b3fbf178f0551727c84f8ca7a52294a5ce125b5a1727e0c7bb`
- Image ID:
  `sha256:21b5a46a374e00c8a70860fc43db449a5235b316b64032f976f39e4084212f80`

## M8 Result

[`m8-evidence.json`](./m8-evidence.json) is the byte-exact public-redacted
coexistence evidence. Its SHA-256 is
`529c18ea157fb7ea366e864f27927c680725f77d90295c4b2d1841fbc47d05cf`.

[`m8-report.json`](./m8-report.json) is the byte-exact deterministic report.
Its SHA-256 is
`b2663e24d6c290a5ab3f508dbb5858e56c9f22337e0e023bfd7bffbf632f5306`.
The report verdict is `PASS`, including the restart-persisted state and exact
rollback checks.

## M8.5 Result

[`public-result.json`](./public-result.json) is the byte-exact
`PUBLIC_REDACTED` projection. Its SHA-256 is
`ae5998f450ec08b936104134f2c5c04546ed26fe5df8aaa13d6a0546c9382784`
and its result hash is
`sha256:30f9e6b02c1f3a4cf0a8e8ef4d60035de9ecdb9862423843511c9a47bdf58fd5`.

The restart-separated campaign evaluated all 18 candidates. Exactly three
candidate IDs, `m7-candidate-0012`, `m7-candidate-0014`, and
`m7-candidate-0016`, matched in both windows and have deterministic dossier
hashes. All three remain `LOCKED_NOT_EXPOSED`; the other 15 candidates remain
`RAW_DEBUG_ONLY` with explicit terminal outcomes.

The `READY_FOR_M9_PLANNING` value permits planning only. It does not expose a
leaf through GraphQL, Portal, Home Assistant, or any semantic registry, and it
does not authorize M9 implementation.

## Verification

The private campaign passed private verification, deterministic public
derivation, public verification against the private campaign, and a clean
rebuild against the exact gateway source and deployed binary. The repository
tests independently verify public schema, result hash, candidate decisions,
source byte bindings, and the absence of private identity and secret material
from this published projection.
