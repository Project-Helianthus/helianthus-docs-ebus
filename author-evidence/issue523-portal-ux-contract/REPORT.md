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
| Transition-safety correction commit | `9daf69ae1890499fe7101311ea7af4f544c39f95` |
| Transition-safety correction tree | `3da596c61881c39df85f548c9bc0aabf4e717df9` |
| B503-invariants correction commit | `33a30863066674c707451326cf87123881260df8` |
| B503-invariants correction tree | `a981911c0aecaf967d24b9233fac22714ad8ffe6` |
| Selector-normalization correction commit | `a237d04241c7f996cad2c8429b711f31ee76a073` |
| Selector-normalization correction tree | `7c198991457975b42dcecc05fbb597e6421be5a7` |
| B503-boundaries correction commit | `dedf448ed98aaec456f9503198184ecc8c9744a0` |
| B503-boundaries correction tree | `de950cd6df8a010e0c9cc957bc9f516c2b566913` |
| DOM-reference correction commit | `371ada15aace19293f7fa1896707d1b563a45b2d` |
| DOM-reference correction tree | `5782442ed96b09083f927b5ada103e056fed316a` |
| DOM-identifier correction commit | `86b7ccc9e4e120bf3a85b4632d8225de6af04bab` |
| DOM-identifier correction tree | `71552aeb3c829e306797fab0f939e0651ce87245` |
| Operation/DOM correction commit | `2243c1dbe868d87aaf0a078996dcc0b43cfd2857` |
| Operation/DOM correction tree | `527f08a54649b2f6424ca06bbbb48863e726b3d0` |
| Structured-DOM correction commit | `c655a54f82ed422f9c6ec6c97e067bcb478e5d24` |
| Structured-DOM correction tree | `96a395b5266aca820265637cb6388218551c09c0` |
| Parsed-component correction commit | `2ac1ecdea7f14b617b0e4beb3039d09357a82b8d` |
| Parsed-component correction tree | `56a0298bf2473e69a1fe0fb9f03aaa79d7aad262` |
| Compact-DOM correction commit | `b1899038f17803264a5b3c438f04aea834f4cf99` |
| Compact-DOM correction tree | `104dc4ca894775d63bef6faee327d62d02f91c28` |
| Inline/fallback correction commit | `97d57f5bef3f8563845ecb40d9081a4a2719a396` |
| Inline/fallback correction tree | `6c80b04f54fb5f4b37c0fbbcd93e6fc2d186da51` |
| Inline-selector correction commit | `89d8e1e6ea5e91f1e180a417d1fa7b8d97b55718` |
| Inline-selector correction tree | `fa96702d6b0a0125440f0ebbef13b22b938dbd17` |
| Direct-fallback correction commit | `e776a246107fc14c81595fd58f0de8db0c84cb7c` |
| Direct-fallback correction tree | `201f1c0ea241844b58d56745d37fde60b2a2d294` |
| Compact/fallback correction commit | `dd063de608bbd36835a37872fec741f8d38efc0c` |
| Compact/fallback correction tree | `c9bb9a04f338b21f66e7af01833050e58ec15a64` |
| Clear-control correction commit | `11b80226ce940e9c16a75c7272fc8e3fe2f7557c` |
| Clear-control correction tree | `0f4529e1fc46d6d657fca1ad36f3eb65407d02ed` |
| Mixed-inline-DOM correction commit | `004d16cd7181d6fe6dea7a42b3168d4f02bb5756` |
| Mixed-inline-DOM correction tree | `2c41ce0f16887d1b52e9d1f67079e5eef0f51175` |
| Milestone-scope correction commit | `4bd7c212d7f526ef63c5d1bb04056e7cc6d1cd28` |
| Milestone-scope correction tree | `929887fa2796436a0066387bc356fd4aa1e22bf1` |
| Refreshing-state correction commit | `bc33609e3b696d7e4707b82752fef57ac1602327` |
| Refreshing-state correction tree | `c95c106e9ccb71bcba742b498522ff40899c98fc` |
| Refreshing-release correction commit | `409f828a0a22294158aa4afea5ca6e766440ee1b` |
| Refreshing-release correction tree | `9a7ff14c9a4d7c4a7100adb20069fb5619d5875c` |
| Refreshing-cleanup correction commit | `11345ecc3ff0362a5a210ccc1352d852928f4745` |
| Refreshing-cleanup correction tree | `2b439ed0be045d204e38a7fdbff16441b08a3540` |
| Refresh-continuation correction commit | `daf010c90f50d245b2a2886c2be73dd8a0690c59` |
| Refresh-continuation correction tree | `4cc8850408fdcd6599416d46e569ec4f93a2a0da` |
| Refresh-disconnect correction commit | `1eff8709e522652914cd4913e3a7ed73570f33b9` |
| Refresh-disconnect correction tree | `1055b42939f1c9cba82764aa989e75177354c673` |
| Gateway contribution dependency | [#972](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/972), merge `0828afa6221197c01cca85abc2344d2b41899b92` |
| Gateway catalog/action dependency | [#974](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/974), merge `34c8a5d8a5444a7f5a8d6350c7b1258af665bb0a` |
| Gateway session-state dependency | [#975](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/975), open intermediate source contract `0e49b3019bfbfc438b1141a08f6c2872a2e21142`, evidence head `76ac4262bbda9fcaeb2846b56a46997d7dd07980` |

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
- The target-transition clauses are mechanically required inside that section:
  a switch atomically invalidates capability, current errors/service, history,
  live-monitor strip, and pending-completion presentation; a late completion
  cannot mutate the new target; and navigation away uses the same
  locally-token-bound cleanup rule.
- The availability table is parsed as one exact structured five-row set; it
  rejects any extra, duplicate, or custom `EXPIRED` row. The checker also binds
  projection-card admission to `AVAILABLE` only, and binds History to typed
  B503 GraphQL records for the selected target while prohibiting label or
  retained-aggregate inference.
- Every parsed DOM component is structurally inspected: tag name, attribute
  name, attribute value, and combined descendant text. Protected installation
  selectors are normalized across spaced, `0x`-prefixed, compact, and
  hyphenated hexadecimal forms. Command words are matched as exact component
  tokens after camelCase and PascalCase segmentation, leaving harmless prose,
  substrings, and raw Markdown assignments untouched.
- Compact controls are normalized only as full unambiguous B503 command forms,
  with an optional `b503` prefix and arbitrary identifier suffix.
  Protected selector sequences use decimal-digit boundaries, so identifier
  suffix letters are covered while longer numeric identifiers remain benign.
- A backticked fragment is classified as DOM when it contains a DOM-relevant
  attribute (`id`, `data-*`, `aria-*`, `role`, and related names); once
  classified, every parsed attribute, including standard event attributes, uses
  the same audit. Non-DOM Markdown assignments remain outside that extraction.
  A bounded
  main-GraphQL contradiction matcher rejects affirmative REST, MCP, native-I/O,
  or other-route fallback clauses.
- That matcher also rejects bounded direct `falls back to` and `use … instead`
  contradictions, while retaining explicit negative fallback wording.
- Compact control matching recognizes arbitrary suffixes only after unambiguous
  reset/delete/history-clear command prefixes, preserving benign `preset` and
  `clearance` names. The fallback matcher also rejects direct declarative
  `uses … as a fallback` clauses.
- Standalone compact clear controls now reject unambiguous arbitrary suffixes
  while retaining the lexical benign `clearance` and `clearly` prefixes.
- The selector tokenizer accepts an optional `0x` prefix on each byte, and
  inline-code extraction audits every DOM-relevant assignment in a
  multi-attribute fragment while ignoring unrelated assignments.
- The DOM audit also parses element names and visible text, so prohibited
  command tokens cannot move into a custom-element name, button label, or
  accessibility content.
- A standard-library structured DOM parser now combines each element's
  descendant text and attributes. The selector audit also recognizes protected
  four-digit values at camel/Pascal identifier boundaries without matching
  longer numeric identifiers.
- The target section mechanically requires named keyboard-accessible B503 tabs
  and session status, Gateway-owned reconnect/error presentation without
  browser action replay or route switching, and target-address plus frontend
  epoch fencing of asynchronous completions.
- Capability/reconnect transitions render the new Gateway availability state;
  pre-turnaround context cancellation renders `UPSTREAM_TIMEOUT`, while
  bus/arbitration timeout, NAK, and CRC render `UPSTREAM_RPC_FAILED`; both
  retain last-known availability.
- The canonical B503 milestone rows now preserve diagnostic read-only GraphQL
  and Portal behavior while admitting only the existing §6 live-monitor
  enable/disable session action and session strip. A dedicated gate rejects the
  earlier all-read-only contradiction and removal of the `02 01`/`02 02`
  install-write non-exposure invariant. The gate parses only the §14 companion
  milestone table and requires the exact M2b and M3 three-cell rows there, so
  copied fragments outside that table or in another milestone row cannot
  satisfy the contract.
- Portal and canonical B503 session wording now define exactly `Idle`,
  `Enabling`, `Active`, `Refreshing`, and `Disabled`. `Refreshing` holds the
  ownership gate and makes every live-monitor operation busy; success returns
  `Active`, failure releases the gate and returns `Idle`, and `Disabled` is
  never emitted with `owned:true`. This follows Gateway #975's current source
  contract `0e49b3019bfbfc438b1141a08f6c2872a2e21142` and evidence head
  `76ac4262bbda9fcaeb2846b56a46997d7dd07980`; #975 is open, intermediate,
  and is not claimed final or merged.
- Canonical validation scopes M2b/M3 rows to the parsed §14 table and the
  `02 01`/`02 02` non-exposure invariant to normative §9. Its mutations reject
  copied text outside those scopes and unsafe five-state contradictions; Portal
  DOM controls retain benign `clearfix` identifiers while rejecting unambiguous
  clear controls.
- The canonical diagram, transition table, and lock lifecycle now agree that a
  failed `Refreshing` session releases ownership and transitions directly to
  `Idle`; it never passes through an artificial `Disabled` state. `Disabled`
  remains the explicit operator/configuration disable state and is never owned.
  The table parser also requires a genuine Markdown delimiter row rather than
  any three-cell content row.
- Target change and navigation now queue a locally held `Refreshing`
  token/target disable until successful refresh reaches `Active`, then clear
  that queued pair without a disable if refresh releases to `Idle`. The
  Gateway-owned session strip stays observable as status-only during
  `Refreshing` plus temporarily `UNKNOWN` capability; it does not admit a card,
  tabs, or B503 operation. Public `Disabled` is explicit operator/configuration
  disable with `owned:false`; enable failure, idle timeout, disconnect, and
  restart clean up to public `Idle` with `owned:false`.
- Refresh success continues only a surviving authenticated current owner by
  revalidating its token, target, and epoch; it never reconstructs a session.
  Restart, lost ownership, or an absent/invalid issuer token require a new
  explicit client Enable. The structured DOM parser treats standard HTML void
  elements as leaves, so subsequent benign prose remains outside their
  descendant text audit while real DOM command references still reject.
- `Refreshing` is reachable only when an epoch advances while ownership remains
  held. A terminal transport disconnect releases to `Idle`; its later reconnect
  has no owner and requires explicit Enable. Standalone inline event-handler
  attributes are classified as DOM and audited like every other protected
  component.
- The main B503 GraphQL route also names graduated
  `vaillantErrorsHistory(targetAddress:limit:)` and
  `vaillantLiveMonitorSession(targetAddress:)` operations.
- Every required INT-10 fragment is checked only within that target section;
  globally forbidden stale implementation wording remains checked over the
  whole document. A regression moves a safety fragment after
  `TARGET_END` and requires rejection.
- It excludes REST and native-MCP fallbacks, dual publication, central vendor
  branching, arbitrary-English parsing, browser-derived evidence, and banner-
  derived action authority.
- `scripts/check_portal_ux_contract.py` and its 133 tests reject missing stable
  selectors, every prohibited B503 command/selector token, route absence or
  fallback, swapped/moved/mismatched availability rows, unsafe target-switch
  cleanup, missing source/authorization boundaries, premature #552
  implementation language, vendor branching, lost action-time confirmation,
  expanded availability tables, projection-card admission outside `AVAILABLE`,
  and untyped or inferred History semantics, including normalized protected
  selectors and exact command tokens in every parsed DOM component, and missing
  accessibility, reconnect/error, or frontend-epoch guarantees. The same
  regression matrix accepts command-word substrings, benign camelCase
  identifiers, compact preset/clearance controls, longer numeric identifiers,
  raw Markdown assignments, safe multi-attribute inline fragments, negative
  fallback language, and ordinary prose.

## Validation

| Command | Result |
|---|---|
| `python3 scripts/check_portal_ux_contract.py` | PASS |
| `python3 -m pytest -q tests/test_portal_ux_contract_checker.py` | PASS: 133 tests |
| `python3 scripts/check_vaillant_b503_milestones.py` | PASS |
| `python3 -m pytest -q tests/test_vaillant_b503_milestone_checker.py` | PASS: 20 tests |
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

The complete transition-safety correction CI log for commit `9daf69a` is
`/tmp/docs523-transition-9daf69a-ci.log`, SHA-256
`ea7fde928983049d15fad9372b649cdcb22abc0ee913c10fe1ead4bd6cdb1e05`.

The complete B503-invariants correction CI log for commit `33a3086` is
`/tmp/docs523-b503-invariants-33a3086-ci.log`, SHA-256
`4108f9f1ff4ad3c70ab5f11f13d12e609d1c7f251f9cd6dc6d0d6f8d81959c15`.

The complete selector-normalization correction CI log for commit `a237d04` is
`/tmp/docs523-selector-normalization-a237d04-ci.log`, SHA-256
`2f5c6158a02b2a179de3ad3ae9e952e519987762fe430ddb9aaa4deb02b8f354`.

The complete B503-boundaries correction CI log for commit `dedf448` is
`/tmp/docs523-b503-boundaries-dedf448-ci.log`, SHA-256
`6eb5390369cc66343886fc567a28184ea9e377b222d0362cb87acc252763fab0`.

The complete DOM-reference correction CI log for commit `371ada1` is
`/tmp/docs523-dom-references-371ada1-ci.log`, SHA-256
`27fab771dea88fe79d826a010912ad8bfa5f2275cef49e21de05a2a61c9ad2f7`.

The complete DOM-identifier correction CI log for commit `86b7ccc` is
`/tmp/docs523-dom-identifiers-86b7ccc-ci.log`, SHA-256
`895fde3ba3e4ffa349c00a781084be11767dabd6493ed917b73ac8c6984368a0`.

The complete operation/DOM correction CI log for commit `2243c1d` is
`/tmp/docs523-operation-dom-2243c1d-ci.log`, SHA-256
`30de17637d7827c602a875b34f383b251b15b692bf83b6ef81760173db6c4db2`.

The complete structured-DOM correction CI log for commit `c655a54` is
`/tmp/docs523-dom-structure-c655a54-ci.log`, SHA-256
`7416e15cc53c3eb1747d42e5142d86bd98a25efde12f20453790b105b7dc832b`.

The complete parsed-component correction CI log for commit `2ac1ecd` is
`/tmp/docs523-dom-components-2ac1ecd-ci.log`, SHA-256
`139c3ec7f2fd3ffdeccaaee3f66fd9c8a6859d7cf9861c8b4c867cfa321b1b18`.

The complete compact-DOM correction CI log for commit `b189903` is
`/tmp/docs523-compact-dom-b189903-ci.log`, SHA-256
`5f71dbe48dc44ea8fb511227e53cb5f72cc8c70f5c4a697dbf02557641b343ff`.

The complete inline/fallback correction CI log for commit `97d57f5` is
`/tmp/docs523-inline-fallback-97d57f5-ci.log`, SHA-256
`1e72ea3c7e62fd67b4cb8dfcaecf4abcb1008cc03c47ae8588e79fe4235a3f06`.

The complete inline-selector correction CI log for commit `89d8e1e` is
`/tmp/docs523-inline-selector-89d8e1e-ci.log`, SHA-256
`ce61ca7d741e70db89043af29d88a3da59ab05b1ac38e6f9104d3ba431e4d1ad`.

The complete direct-fallback correction CI log for commit `e776a24` is
`/tmp/docs523-direct-fallback-e776a24-ci.log`, SHA-256
`fd260e69121e0df92e978443944f042a2cc509abd082a5b75587061cf174ea92`.

The complete compact/fallback correction CI log for commit `dd063de` is
`/tmp/docs523-compact-fallback-dd063de-ci.log`, SHA-256
`47ae8e25f500f0124f8e6a3cb3e4212578fbd8ede396e6e64345fb466f2efbf4`.

The complete clear-control correction CI log for commit `11b8022` is
`/tmp/docs523-clear-controls-11b8022-ci.log`, SHA-256
`a030e3da06beede86ef5522e2f11368afa4d4557cb52378468fae6ea14c09027`.

The complete mixed-inline-DOM correction CI log for commit `004d16c` is
`/tmp/docs523-inline-dom-mixed-004d16c-ci.log`, SHA-256
`4e89e6116f29e9d77b32bc26228d5edc12652bb74004caef570d32e59e5b2f33`.

The complete milestone-scope correction CI log for commit `4bd7c21` is
`/tmp/docs523-milestone-scope-4bd7c21-ci.log`, SHA-256
`430eb0cbb495eb01d388623dcba72a85fd102c266ba2c13696fa991cbaae4cb8`.

The complete Refreshing-state correction CI log for commit `bc33609` is
`/tmp/docs523-refreshing-bc33609-ci.log`, SHA-256
`8a428048da100d509574fa22fbe839f33aed2bc263a9938d53eba3c84092e90f`.

The complete Refreshing-release correction CI log for commit `409f828` is
`/tmp/docs523-refreshing-release-409f828-ci.log`, SHA-256
`8555c67ce6378c009a49373253dc6984247dfe6fb97627b732aee5f31c059a98`.

The complete Refreshing-cleanup correction CI log for commit `11345ec` is
`/tmp/docs523-refreshing-cleanup-11345ec-ci.log`, SHA-256
`c924245e23e87d2246b1abf9b0058fd6e059aa6f674aa99bc0a99cdd5951c0fa`.

The complete Refresh-continuation correction CI log for commit `daf010c` is
`/tmp/docs523-refresh-continuation-daf010c-ci.log`, SHA-256
`fdca7a25d02f97afa1309d05ec4b56730838374f20353241f05a98357299fdb8`.

The complete Refresh-disconnect correction CI log for commit `1eff870` is
`/tmp/docs523-refresh-disconnect-1eff870-ci.log`, SHA-256
`3d97cf9ce5e4ab057e87a02aa144be3b558c328980858ea0586f7464309624d5`.

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
