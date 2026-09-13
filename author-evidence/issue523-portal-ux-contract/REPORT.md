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
| Gateway contribution dependency | [#972](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/972), merge `0828afa6221197c01cca85abc2344d2b41899b92` |
| Gateway catalog/action dependency | [#974](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/974), merge `34c8a5d8a5444a7f5a8d6350c7b1258af665bb0a` |

## Delivered contract

- `api/portal.md` names Gateway as the owner of the immutable five-domain
  catalog, contribution identity, rendering boundary, and caller-scoped action
  admission.
- It locks B503 to `POST /graphql/portal/v1`, exact target-bearing GraphQL
  operations, five `B503Availability` states, stable state/session/AD02
  selectors, projection-card admission, typed history, and nav-away cleanup.
- It excludes REST and native-MCP fallbacks, dual publication, central vendor
  branching, arbitrary-English parsing, browser-derived evidence, and banner-
  derived action authority.
- `scripts/check_portal_ux_contract.py` and its 10 tests reject missing stable
  selectors, fallback regression, missing source/authorization boundary,
  premature #552 implementation language, vendor branching, and lost
  action-time confirmation.

## Validation

| Command | Result |
|---|---|
| `python3 scripts/check_portal_ux_contract.py` | PASS |
| `python3 -m pytest -q tests/test_portal_ux_contract_checker.py` | PASS: 10 tests |
| `git diff --check` | PASS |
| `PLATFORM_M625_DOCS_EEBUS_ROOT='/Users/razvan/Desktop/Helianthus Project/work/helianthus-stabilization-20260904/wave11/read/docs-eebus-m625-81cd' PLATFORM_M625_EXECUTION_PLANS_ROOT='/Users/razvan/Desktop/Helianthus Project/work/helianthus-stabilization-20260904/wave11/read/plans-m625-4e15' ./scripts/ci_local.sh` | PASS, exit 0 |

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

Changes are committed locally only. Nothing was pushed, no PR was opened or
merged, and no issue or Project state was changed. A fresh exact-HEAD review
and the normal remote checks remain the next delivery-lead actions before any
merge decision.
