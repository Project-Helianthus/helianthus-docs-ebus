# Issue #517 author evidence

## Scope

This change corrects only the public adversarial runtime v1 fixture provenance.
It copies the four reports produced from public gateway squash revision
`936edbe873f35a8bad3763223dba9566154574d6`, tree
`d59bdfe02b9ad1168fe8d7ba2aff275f87ef06fd`. That public revision is both the
immutable fixture subject and the authenticated producer source.

## Reproducible producer evidence

Two independent clean detached clones of the public gateway revision built the
same test executable with:

`GOWORK=off go test -c -trimpath -buildvcs=true -o <output> ./internal/adversarial`

Both executables were byte-identical, size `6059426`, with SHA-256
`fc8993b6b0532a219534e557dfd8c7ee0974fe1402e14c8e7787f9cdb488d4d1`.
The exact toolchain, target, module version, VCS revision/time/dirty bit, build
ID, command arguments, environment, source tree, reproduction result and report
hashes are captured in the closed machine-readable
`docs/platform/fixtures/adversarial-runtime/v1/producer-build-evidence.json`.
The repository tests reject drift between this record, the canonical validator
identity and the checked-in report bytes.

## Provenance bindings

- Fixture subject and producer commit: `936edbe873f35a8bad3763223dba9566154574d6`
- Fixture subject source tree: `d59bdfe02b9ad1168fe8d7ba2aff275f87ef06fd`
- Fixture manifest SHA-256: `d7fbe89d068b1b5c0d41fe51176d9e9263a441ee0ed752c9e8cae794f5a8346a`
- Producer executable SHA-256: `fc8993b6b0532a219534e557dfd8c7ee0974fe1402e14c8e7787f9cdb488d4d1`
- Positive report SHA-256 values: `evaluated-fail` `1e4981bcf5e5b0b645365e7dbb1c1aa9e724de90024af997122a16184583126f`; `execution-error` `76efea7d94d912c03a78cacc9518176590e0d696eaa01f23b52fb88a237ae34c`; `infrastructure-block` `d48f81a8844bf3b7ed76b54aff80aa155e56308eeecffa0b1cac3645ca376f6a`; `offline-all-pass` `a9e556de71473a716dbce8c6e462cdb314bf92b91d1cbf9a13fc1cf1511a547d`.

## Validation

- `python3 -m pytest -q tests/test_adversarial_runtime_report_v1.py`: 46 passed.
- Each of the four checked-in positive reports passes
  `scripts/validate_adversarial_runtime_report_v1.py`.
- `PLATFORM_M625_DOCS_EEBUS_ROOT=/tmp/docs-eebus-m625-cedf238 PLATFORM_M625_EXECUTION_PLANS_ROOT=/tmp/plans-m625-fb384ab ./scripts/ci_local.sh`: pass, 1969 passed, 395 expected deselected, exit 0; log SHA-256 `e73c018e105833d3ff1cc684b0c04b650cb138bc105a4cd9952168636bcb1929`.
- `git diff --check`: pass.

The checker binds field-level provenance for the checked-in gateway fixture
corpus. It does not allowlist whole report bytes and preserves v1 dynamic
timestamps, valid seam/continuity variants, result variants and error
precedence.

## Residual risk and stop

This is deterministic offline evidence. It does not prove live gateway, Home
Assistant, adapter, network or hardware behavior. No live trigger, transport,
credential, deployment or device action occurred. Gateway issue #198 remains
open for the final public artifact integration after this docs correction is
accepted.
