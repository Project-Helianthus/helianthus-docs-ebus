# Issue 523 Portal UX Contract — Author Evidence

## Scope and state

This report records the public documentation gate for
[helianthus-docs-ebus#523](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/523).
It freezes the contribution-driven Portal and Vaillant B503 target contract for
Gateway [#552](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/552).
Gateway #552 remains open. This change does not claim Gateway implementation,
device validation, deployment, credential handling, installation control,
hardware work, or SemReg cutover.

| Item | Exact value |
|---|---|
| Repository | `Project-Helianthus/helianthus-docs-ebus` |
| Branch | `issue/523-portal-ux-contract` |
| Base commit | `6ce5c9f62690e1b9b18cb888f187ba7d89b845f0` |
| Base tree | `2f60febe5760a895b31f10c6f8129f97e7d0b008` |
| Validated contract commit | `9a60d74a665a38a945a9f997dbc98e77885630ab` |
| Validated contract tree | `6f867c796d095e7d090c2eb683b3f66cbcbc0a94` |
| Blocking review report | `docs524-0f2c935-independent/REPORT.md`, SHA-256 `70d3f392472bab8e48808d3ae9d13c772bd69556aba5ab02664548ab667b3a8f` |
| Corrected contract commit | `5443075355407e05d588c476b92679843a30c7ad` |
| Corrected contract tree | `41e62cd0a3bfaeede159355af881abd561e26343` |
| Availability/switch correction commit | `5f5868c38e7c2ca9af69ac9b76dcb7dd606c7c4d` |
| Availability/switch correction tree | `063cdb2118e68ddf4be5602cbd249b3c3cdcd8bd` |
| Target-section correction commit | `e3fa1b544b5a83f540da0f2e49289e27b11db170` |
| Target-section correction tree | `0af507bd9404d7ac91533798eacb9e1e2e0797b5` |
| Gateway contribution dependency | [#972](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/972), merge `0828afa6221197c01cca85abc2344d2b41899b92` |
| Gateway catalog/action dependency | [#974](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/974), merge `34c8a5d8a5444a7f5a8d6350c7b1258af665bb0a` |

## Delivered contract

- `api/portal.md` names Gateway as the owner of the immutable five-domain
  catalog, contribution identity, rendering boundary, and caller-scoped action
  admission.
- It binds only `PortalCatalogV1` and `PortalActionInvokeV1` to
  `POST /graphql/portal/v1`, while every target-bearing B503 read/session
  operation uses only the graduated/parity-protected main `POST /graphql`
  endpoint. This split is exclusive and does not expand #974.
- It freezes five `B503Availability` states, stable state/session/AD02
  selectors, projection-card admission, typed history, and nav-away cleanup.
- The AD02 banner is generic and has no B503 command or selector vocabulary.
  `SESSION_BUSY` is neutral bounded ownership-or-lifecycle contention; the
  Gateway `owned` bit identifies only a held gate, never a client. A missing
  browser token never identifies a foreign owner.
- Each availability row is mechanically bound inside the INT-10 target section
  to its exact reason, stable selector, and presentation text. Target switching
  starts token-bound cleanup for all locally owned `ENABLING` and `ACTIVE`
  prior-target sessions, while preserving late-completion cleanup and never
  disabling an opaque gate-held session without a local token.
- The main B503 GraphQL route also names graduated
  `vaillantErrorsHistory(targetAddress:limit:)` and
  `vaillantLiveMonitorSession(targetAddress:)` operations.
- Every required INT-10 fragment is checked only within that target section;
  globally forbidden stale implementation wording remains checked over the
  whole document. The 36th regression moves a safety fragment after
  `TARGET_END` and requires rejection.
- It excludes REST and native-MCP fallbacks, dual publication, central vendor
  branching, arbitrary-English parsing, browser-derived evidence, and banner-
  derived action authority.
- `scripts/check_portal_ux_contract.py` and its 36 tests reject missing stable
  selectors, every prohibited B503 command/selector token, route absence or
  fallback, swapped/moved/mismatched availability rows, unsafe target-switch
  cleanup, missing source/authorization boundaries, premature #552
  implementation language, vendor branching, and lost action-time
  confirmation.

## Validation

| Command | Result |
|---|---|
| `python3 scripts/check_portal_ux_contract.py` | PASS |
| `python3 -m pytest -q tests/test_portal_ux_contract_checker.py` | PASS: 36 tests |
| `git diff --check` | PASS |
| `PLATFORM_M625_DOCS_EEBUS_ROOT='/Users/razvan/Desktop/Helianthus Project/work/helianthus-stabilization-20260904/wave11/read/docs-eebus-m625-81cd' PLATFORM_M625_EXECUTION_PLANS_ROOT='/Users/razvan/Desktop/Helianthus Project/work/helianthus-stabilization-20260904/wave11/read/plans-m625-4e15' ./scripts/ci_local.sh` | PASS, exit 0 |

The complete correction-CI log for corrected contract commit `5443075` is
`/tmp/docs523-correction-5443075-ci.log`, SHA-256
`e40eba821812196c039c9effcb2a18384ad64ab22ff0b87a22136cf72c1bbcb5`.

The complete availability/switch correction CI log for commit `5f5868c` is
`/tmp/docs523-row-switch-5f5868c-ci.log`, SHA-256
`8b1b9e5d6e2d9f918024950937f35365fa41cb493c69e656ce72c1be3eba1eb5`.

The complete target-section correction CI log for commit `e3fa1b5` is
`/tmp/docs523-target-scope-e3fa1b5-ci.log`, SHA-256
`7dd787ac56083380913980b9d3a84242ca772bfe3e24fbb7f0d451c889f5d32b`.

The read-only M6.25 inputs were verified clean and detached before CI:

- docs-eeBUS `cedf238e34f879815ba773e9cd76b2b31c2822a3`, tree
  `7667c4f2675ee627812f048ee164bc30eec331b3`;
- execution plans `fb384ab57d79f0020c54d2c66416e8a7666f0ceb`, tree
  `1f48c5d0cf1aecd2cfa72e0b16f50e41df3ea5af`.

The complete configured CI includes the new Portal gate and passed the
repository's source-address, identity, SemReg, GraphQL provenance,
cross-runtime, synchronized-evidence, Modbus, opaque-acquisition,
runtime-state, deployment-wording, and NM terminal gates. No transport or
physical smoke gate applies to this documentation/checker-only change.

## Stop boundary

The correction is committed on the existing PR branch. No merge, issue, or
Project state change was made. The branch is pushed for a fresh exact-HEAD
review; normal remote checks and that review remain required before any merge
decision.
