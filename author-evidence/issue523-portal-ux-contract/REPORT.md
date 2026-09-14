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
| Initial validated contract commit | `9a60d74a665a38a945a9f997dbc98e77885630ab` |
| Initial validated contract tree | `6f867c796d095e7d090c2eb683b3f66cbcbc0a94` |
| Final validated contract commit | `dd93e12f53dc4740ea7b493717eae89daa4bf999` |
| Final validated contract tree | `a27753545728cd12509e6ddd99e0f9141976ce8f` |
| Final contract validation | Complete configured CI PASS; 250 Portal checker tests and 101 canonical B503 milestone tests; log SHA-256 `8a602b0acc178c5c66c22ab36db600479424942439a32506a2aa850273baedf8` |
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
| Final pin/DOM-prefix correction commit | `80efd4b74d7650481f1ebbcc0da62e4f17dcd505` |
| Final pin/DOM-prefix correction tree | `e0a73e0039dfb6226f42c51c0231902d58267acb` |
| Intermediate full-CI Gateway-pin correction commit | `9290dd797287a4e0ec68ecda656def4f22fce074` |
| Intermediate full-CI Gateway-pin correction tree | `78da165c7ebc41af9b8d5b3e5f0012dc2986623b` |
| Intermediate Gateway source-reconciliation correction commit | `002fae3a240709754779a2eb9f48341492ce5db0` |
| Intermediate Gateway source-reconciliation correction tree | `ad4bb5298e3f768c4b61dc7d0a37b56288659c69` |
| Intermediate bounded-status Gateway-pin correction commit | `6b4c531185e8c0166a07f4963fd986dbe3e8660a` |
| Intermediate bounded-status Gateway-pin correction tree | `4d331dd546b6f89f02812745bb50f04e7d18a64f` |
| Session-authority/epoch-transition correction commit | `e1f894afc432d97523dd2a3ccee9d121eab2845c` |
| Session-authority/epoch-transition correction tree | `294b3b5f23743b88ab1e79b59e4b837415b0e256` |
| Refresh-availability/install-write exposure correction commit | `460f60fa6d37bbf125b95175b76c253bb2a80117` |
| Refresh-availability/install-write exposure correction tree | `a44e4aa4943b05b436be9e916421bc7f8514cbaf` |
| Refresh-status/individual-selector exposure correction commit | `7fc07a78b4d814b07ce0dc5a39a2cbe759aea4ee` |
| Refresh-status/individual-selector exposure correction tree | `243f1b93fc869b06ed9c6d5c30604c30ab1173df` |
| Affirmative normative-form correction commit | `5e6ed3dd285f148280d0c118caaffc1489775301` |
| Affirmative normative-form correction tree | `32d7bf0cef885136443bf4dd5a6478f2583cf760` |
| Installation-selector normalization correction commit | `8a0744211be6e69bebb56474836a38bee998b389` |
| Installation-selector normalization correction tree | `bb8cf8c8a84937d942897594d9dc5e333f971071` |
| Markdown-control/fallback correction commit | `8ff31c555ef11d2a51b97d933f12b80f15e1ffd8` |
| Markdown-control/fallback correction tree | `abdfce3249241e15a66e0947a9b553e01ea45389` |
| Reference-control/passive-exposure correction commit | `51efc0eaf3e6a4a496e712b389660db2fb29806c` |
| Reference-control/passive-exposure correction tree | `379307cec7b5da493c3db6ccd3b2d992840235d6` |
| Markdown-entity decoding correction commit | `67755252a53ceabe4a91025d1642e48d964c2d3c` |
| Markdown-entity decoding correction tree | `173ee01f90b7b13a5d27c86ef0f2c78bc7a01534` |
| Document-scoped reference correction commit | `a797a7de248cb081230827062f364c8621e6b584` |
| Document-scoped reference correction tree | `0b883557779b1c5fb31d16dde23fc82b45216201` |
| Reference-title correction commit | `0e0303b91f7f0b0b815ac33542f23e0888d09cae` |
| Reference-title correction tree | `8c4ee31be60cf32eda031bdd06642b31a30030c5` |
| Failed-enable cleanup correction commit | `177b87de203b55d7da3ca4c2af11631a28c60543` |
| Failed-enable cleanup correction tree | `04182ccbbc83723bbcefb941828afac077078d7a` |
| Complete enable-failure/URL-attribute correction commit | `1f393d6df96a50fb7350dbccff2f1ac00ec39b86` |
| Complete enable-failure/URL-attribute correction tree | `44ffc6e070b38591a6e52a730525720cdd6bfd79` |
| Pending-enable FSM/plain-control correction commit | `cc86adf5371fa5b85f51350a517ee0d5157efa78` |
| Pending-enable FSM/plain-control correction tree | `b9b25d28b78c36f30846df6a3692bd504644b534` |
| Plain-control shorthand correction commit | `b92028347b791a8c5385a94b582e995e4f312f11` |
| Plain-control shorthand correction tree | `1c481f3046486a11b13eb3be8b0798f5e2c97e79` |
| Existential-control correction commit | `957028d4dbfd426db4132fa93d2742c3fc22d126` |
| Existential-control correction tree | `f82e9a5b86f6403a4aeb61ae1e28cad6fc2c68f1` |
| Inline-command prose correction commit | `8df962d228fab7c30067204f185a3ea98d13bb8e` |
| Inline-command prose correction tree | `d20fdc25c218687aa212d9f9dc1b7c3ffa21329b` |
| Route/epoch-split correction commit | `9e1d6e599f3eee51c74d5133e7e6e43b03680866` |
| Route/epoch-split correction tree | `3a3741de0d5c69637f9563e7dd5fc1c3b9330591` |
| Concrete-route audit correction commit | `9879a8d6f7c87c5f02e515243918d2ab000e6604` |
| Concrete-route audit correction tree | `af4790b58d985cf6d8bd6aa616566d8ae6d5156a` |
| Disconnect-cleanup/double-negative correction commit | `dc3aaf582ac62bb7e1beea3879514aa1ec4a483f` |
| Disconnect-cleanup/double-negative correction tree | `891d197b98679da0dcbedc6a5ec8406a4daaee3f` |
| Literal-HTML route-destination correction commit | `c26685f168ba27a7c82f581812090e3948688167` |
| Literal-HTML route-destination correction tree | `88fcab524e05b7eba6773443a9976798e9fc5193` |
| Confirmed-cleanup/fail-closed correction commit | `12658921c5e2763dd689a1c8781399c2c598ae78` |
| Confirmed-cleanup/fail-closed correction tree | `99a02087d83211f49f6cd11d1930af371f226925` |
| Gateway-cleanup-identity/HTML-ping correction commit | `dd93e12f53dc4740ea7b493717eae89daa4bf999` |
| Gateway-cleanup-identity/HTML-ping correction tree | `a27753545728cd12509e6ddd99e0f9141976ce8f` |
| Gateway contribution dependency | [#972](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/972), merge `0828afa6221197c01cca85abc2344d2b41899b92` |
| Gateway catalog/action dependency | [#974](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/974), merge `34c8a5d8a5444a7f5a8d6350c7b1258af665bb0a` |
| Gateway session-state dependency | [#975](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/975), open/intermediate/unmerged functional source and evidence head `a39d43fbeaf8d745222b85649ebb8494203163f0`, evidence tree `598884b896ce75e30f24fcab1a0fa6db0b82f022` |

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
- Compact controls are normalized only as full unambiguous B503 or Vaillant
  command forms, with the component prefix and arbitrary identifier suffix.
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
  contract and evidence head `a39d43fbeaf8d745222b85649ebb8494203163f0`
  (tree `598884b896ce75e30f24fcab1a0fa6db0b82f022`); #975 is open, intermediate,
  unmerged,
  and is not claimed final or merged.
- §1 now identifies the archived amendment-1 plan SHA as traceability for its
  original §12 scope, while this current docs-ebus#523 revision is authoritative
  for the five-state public session contract. It does not claim plan-state
  mutation or retain a compatibility state, route, or fallback.
- An epoch advance while `ENABLING` deterministically transitions to `IDLE`,
  releases the gate, and discards stale enable ACK/NAK/timeout; only `ACTIVE`
  enters `Refreshing`. The canonical gate requires the matching diagram,
  operation row, transition row, and lock-lifecycle clause.
- §12.5 row 7 now separates temporary `UNKNOWN` capability from the
  `Refreshing` session status. Its strip is status-only: only capability and
  session-status queries remain admitted; no card, tabs, bus-facing reads, or
  actions are admitted until capability returns `AVAILABLE`. A structured row
  mutation rejects stale `AVAILABLE`, removal of status polling, or premature
  bus-facing admission.
- §9 keeps its exact non-exposure invariant and rejects bounded affirmative
  GraphQL/MCP/Portal/Home Assistant/HA/public-API installation-write clauses,
  while accepting explicit negative safety wording.
- The `Refreshing` strip may make only status-only
  `vaillantCapabilities(targetAddress:)` and
  `vaillantLiveMonitorSession(targetAddress:)` queries to observe completion
  and capability recovery. Bus-facing reads/actions remain busy, and no other
  operation gains permission.
- The §9 checker now rejects affirmative public exposure of either `02 01` or
  `02 02` independently, while preserving explicit negative safety clauses.
- Refresh success atomically rebinds the surviving owner's transport key from
  epoch N to the returned epoch N+1 while preserving the issuer token and
  target. Epoch-N completions cannot satisfy, disable, extend, or mutate the
  rebound session; failed refresh installs no new key and releases the owner.
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
  held. A terminal transport disconnect releases the owner. When an enable may
  have reached the wire without confirmed disable completion, Gateway retains a
  process-local, operation-ineligible cleanup obligation and blocks B503 use on
  reconnect until one bounded target-specific defensive disable reaches a
  valid disable ACK. Standalone inline event-handler attributes are
  classified as DOM and audited like every other protected component.
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
- `scripts/check_portal_ux_contract.py` and its 250 tests reject missing stable
  selectors, every prohibited B503 command/selector token, route absence or
  fallback, swapped/moved/mismatched availability rows, unsafe target-switch
  cleanup, missing source/authorization boundaries, premature #552
  implementation language, vendor branching, lost action-time confirmation,
  expanded availability tables, projection-card admission outside `AVAILABLE`,
  and untyped or inferred History semantics, including normalized protected
  selectors and exact command tokens in every parsed DOM component, and missing
  accessibility, reconnect/error, frontend-epoch guarantees, compact
  Vaillant-prefixed clear/reset controls, rendered CommonMark controls, or any
  extra route-surface paragraph. The same regression matrix accepts benign
  command-word substrings, preset/clearance controls, longer numeric
  identifiers, safe Markdown links/images, non-DOM assignments, and safe
  multi-attribute inline fragments.

## Validation

| Command | Result |
|---|---|
| `python3 scripts/check_portal_ux_contract.py` | PASS |
| `python3 -m pytest -q tests/test_portal_ux_contract_checker.py` | PASS: 250 tests |
| `python3 scripts/check_vaillant_b503_milestones.py` | PASS |
| `python3 -m pytest -q tests/test_vaillant_b503_milestone_checker.py` | PASS: 101 tests |
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

The complete final pin/DOM-prefix correction CI log for commit `80efd4b` is
`/tmp/docs523-final-pin-80efd4b-ci.log`, SHA-256
`e960b2bac36fffee0aeb163d5f791e28055dbeeebac540e9207c603bb2c19c64`.
It passed with 137 Portal checker tests and 20 canonical B503 milestone tests.

The complete intermediate full-CI Gateway-pin correction log for commit
`9290dd7` is `/tmp/docs523-final-gateway-pin-9290dd7-ci.log`, SHA-256
`8409583e5529b0d9851061f41a6c48fdbd2d8aef6d6411a3b40e1d535d139411`.
It passed with 137 Portal checker tests and 20 canonical B503 milestone tests.

Gateway #975 history reconciles `a39d43fbeaf8d745222b85649ebb8494203163f0`
as the current functional commit (`fix(portal): preserve B503 pane across discovery`) and current open PR head, directly following the earlier functional
commit `34a2c06c2f0dce85c95b3995c6be7776ecc5f35c`. Therefore this intermediate
pin deliberately uses `a39d43f` as both functional source and evidence head;
it does not claim a merge or final acceptance.

The complete intermediate source-reconciliation CI log for commit `002fae3` is
`/tmp/docs523-intermediate-a08-pin-002fae3-ci.log`, SHA-256
`61d847ed400b3a8b16219babb2a42444a3b5a9d8f0b16166b64e625c89e0149c`.
It passed with 137 Portal checker tests and 20 canonical B503 milestone tests.

The complete intermediate bounded-status Gateway-pin CI log for commit
`6b4c531` is `/tmp/docs523-bounded-status-pin-6b4c531-ci.log`, SHA-256
`e22ea9b1c655d32a2c2de4ad3ac78bc4769fe3f994f5c45caccbd152864e1d9b`.
It passed with 137 Portal checker tests and 20 canonical B503 milestone tests.

The complete session-authority/epoch-transition correction CI log for commit
`e1f894a` is `/tmp/docs523-session-authority-e1f894a-ci.log`, SHA-256
`b896b2d880e0882eb003f17b568e79076dea4545851b95d5fb1085bbae74ca52`.
It passed with 137 Portal checker tests and 25 canonical B503 milestone tests.

The complete refresh-availability/install-write exposure correction CI log for
commit `460f60f` is `/tmp/docs523-refresh-availability-460f60f-ci.log`, SHA-256
`5f1d03f318074629efa2a99e97de246309f50b1136f35944b18e11b0c64951f4`.
It passed with 137 Portal checker tests and 30 canonical B503 milestone tests.

The complete refresh-status/individual-selector exposure correction CI log for
commit `7fc07a7` is `/tmp/docs523-refresh-status-7fc07a7-ci.log`, SHA-256
`ec560a5115f991968314b7081030d014c4948f0d0b6a300e4f1d59e3c83f2015`.
It passed with 138 Portal checker tests and 32 canonical B503 milestone tests.

The complete final Gateway `a39d43f` source/evidence repin CI log is
`/tmp/docs523-final-a39d43f-pin-ci.log`, SHA-256
`79139a1aeb54bfee496c98ddee564a77e423a665f41970712decea9a6c02ecbd`.
It passed with 138 Portal checker tests and 32 canonical B503 milestone tests.

The complete canonical status-query, public-surface, and owner-key rebinding
correction CI log is `/tmp/docs523-canonical-refresh-rebind-ci.log`, SHA-256
`54ccbf30f8684ea5b4bc9dc79599b09f153b546e0a38181c56e00c53715ba425`.
It passed with 138 Portal checker tests and 38 canonical B503 milestone tests.

The complete qualified-public-surface correction CI log is
`/tmp/docs523-qualified-surface-ci.log.log`, SHA-256
`e4e8134127b0f9e2cfd2e15d47b1eb0dd90dd9fa866f4733541efe4dc530c6e4`.
It passed with 138 Portal checker tests and 41 canonical B503 milestone tests.
That complete run validated the qualified-public-surface correction commit
`5804a06e4c7e8ee0208fd0a22107aed5199f2ad3`, tree
`310e6ff7dbb1ba04ef41cbbb2e90b26cfd78923e`.

The complete affirmative normative-form correction CI log is
`wave12/ci/docs524-5e6ed3d-ci-local.log`, SHA-256
`24ae3e86d48320a2d218f2967f78eb270387885c7a251a404dcaedff3a69385e`.
It validated final contract commit
`5e6ed3dd285f148280d0c118caaffc1489775301`, tree
`32d7bf0cef885136443bf4dd5a6478f2583cf760`, with 138 Portal checker tests and
44 canonical B503 milestone tests. The subsequent correction changes only this
evidence report so the final contract revision and results are explicit; it
does not change the documented contract, checkers, or tests.

The complete installation-selector normalization correction CI log is
`wave12/ci/docs524-8a07442-ci-local.log`, SHA-256
`6a4df8b0c2c27495637ebf7be93f3d4966f88237e391e32647c86f200cb23c52`.
It validated final contract commit
`8a0744211be6e69bebb56474836a38bee998b389`, tree
`bb8cf8c8a84937d942897594d9dc5e333f971071`, with 138 Portal checker tests and
48 canonical B503 milestone tests. The following evidence-only commit records
that immutable contract revision and does not change the documented contract,
checkers, or tests.

The complete Markdown reference-title correction CI log is
`wave12/ci/docs524-0e0303b-ci-local.log`, SHA-256
`ad49b24fae47d916813091389ffcbf9f16716dfb2a9feb37f1455e32a3788bcd`.
It validated final contract commit
`0e0303b91f7f0b0b815ac33542f23e0888d09cae`, tree
`8c4ee31be60cf32eda031bdd06642b31a30030c5`, with 164 Portal checker tests and
51 canonical B503 milestone tests. The following evidence-only commit records
that immutable contract revision and does not change the documented contract,
checkers, or tests.

The complete document-scoped Markdown-reference correction CI log is
`wave12/ci/docs524-a797a7d-ci-local.log`, SHA-256
`6ba4ea933f81a0ee72d1fba96d6d41b763267c551789aff8bfeda6fb36cc9687`.
It validated final contract commit
`a797a7de248cb081230827062f364c8621e6b584`, tree
`0b883557779b1c5fb31d16dde23fc82b45216201`, with 160 Portal checker tests and
51 canonical B503 milestone tests. The following evidence-only commit records
that immutable contract revision and does not change the documented contract,
checkers, or tests.

The complete Markdown-entity decoding correction CI log is
`wave12/ci/docs524-6775525-ci-local.log`, SHA-256
`6b15ce405bcaf1d6696492b456250c8e3d79cf8f636ecc2ad694c391f6b4f8d1`.
It validated final contract commit
`67755252a53ceabe4a91025d1642e48d964c2d3c`, tree
`173ee01f90b7b13a5d27c86ef0f2c78bc7a01534`, with 156 Portal checker tests and
51 canonical B503 milestone tests. The following evidence-only commit records
that immutable contract revision and does not change the documented contract,
checkers, or tests.

The complete reference-control and passive-exposure correction CI log is
`wave12/ci/docs524-51efc0e-ci-local.log`, SHA-256
`be781ee5400a3c0246741b96c7cc51fb829ab256bed3b833aaaa93fafc64db7f`.
It validated final contract commit
`51efc0eaf3e6a4a496e712b389660db2fb29806c`, tree
`379307cec7b5da493c3db6ccd3b2d992840235d6`, with 152 Portal checker tests and
51 canonical B503 milestone tests. The following evidence-only commit records
that immutable contract revision and does not change the documented contract,
checkers, or tests.

The complete Markdown-control and retry/switch/reroute fallback correction CI
log is `wave12/ci/docs524-8ff31c5-ci-local.log`, SHA-256
`19c44d1b653cacc073f0cef95f5fa7a7a0bb2e62bd74b878d6401c6c87b8ea4c`.
It validated final contract commit
`8ff31c555ef11d2a51b97d933f12b80f15e1ffd8`, tree
`abdfce3249241e15a66e0947a9b553e01ea45389`, with 148 Portal checker tests and
48 canonical B503 milestone tests. The following evidence-only commit records
that immutable contract revision and does not change the documented contract,
checkers, or tests.

The complete CommonMark, §9 exact-scope, and route-surface correction CI log is
`wave12/ci/docs524-61eb492-ci-full.log`, SHA-256
`2c68901f294cc13d344ea06d9db73c567c1a8b71781cf291ddc2578b8976da7a`.
It validated final contract commit
`61eb49232a77611194e78a60733133b2ebfbf7e4`, tree
`201c7b19407570193da8ffb91fda043f6a919970`, with 183 Portal checker tests and
58 canonical B503 milestone tests. The correction parses rendered controls with
the repository's pinned CommonMark implementation, freezes the complete §9
installation-write boundary, and confines route-surface wording to four exact
contract paragraphs. The preceding unconfigured full-CI attempt stopped
fail-closed only because the required M6.25 roots were absent (log SHA-256
`65eb3081369cea93f6c3bdddde13a680f91fe3d417d8d81468f8fcca503eff30`);
no failure was reclassified or omitted. The following evidence-only commit
records this immutable contract revision.

The complete Refreshing-disconnect release correction CI log is
`wave12/ci/docs524-4441cc2-ci-full.log`, SHA-256
`75e97b473a8b377fb9efb30ac849e21f3d5a46422f7cabb856ebccae5fb5d49a`.
It validated final contract commit
`4441cc2b9e7b4d6e9c3b14bf13226330b60f335e`, tree
`6cefda746e00c0af9f0dfaf6735248dc5c3dd6c7`, with 183 Portal checker tests and
59 canonical B503 milestone tests. The lock-lifecycle list now names
`REFRESHING` among the held-owner states that release exactly once on entry to
`DISABLED`, and a mutation test rejects its omission. The following
evidence-only commit records this immutable contract revision.

The complete triggering-refresh-request correction CI log is
`wave12/ci/docs524-4b9dd2f-ci-full.log`, SHA-256
`643ef6c65969f355203ae7ee33ee587061e7c955855eeec1038a6a848cf3e105`.
It validated final contract commit
`4b9dd2fda47ed059d5f36d8af4079b95f0ad0df3`, tree
`ef85b922143269451017a7823ca958fd03e37776`, with 183 Portal checker tests and
62 canonical B503 milestone tests. The already-admitted request that detects
the epoch advance remains pending through the single refresh, dispatches
exactly once only after successful atomic rebind, and receives the exact result;
subsequent bus-facing operations receive `SESSION_BUSY`. Refresh failure returns
the exact Gateway failure without native dispatch. Three mutations bind these
outcomes. The following evidence-only commit records this immutable contract
revision.

The complete percent-decoding and operation-specific refresh correction CI log
is `wave12/ci/docs524-6c6b2df-ci-full.log`, SHA-256
`14cb64af27aa99ea6d2a9c3fb7cc235de02fc322d33270eb2ffad091c16c7be3`.
It validated final contract commit
`6c6b2df97fb0c060445f31440f6b2bc195cb230b`, tree
`9d5758271de53f99b169c29706d5708c66ac80b9`, with 186 Portal checker tests and
66 canonical B503 milestone tests. Markdown link/image destinations are URL
percent-decoded before command/selector audit. After successful refresh, a
triggering READ dispatches once and retains `Active`, while a triggering
current-owner DISABLE dispatches once after quiesce and completes
`Disabled`-to-`Idle` cleanup; four diagram/transition mutations enforce the
operation-dependent terminal state. The following evidence-only commit records
this immutable contract revision.

The complete queued-cleanup and HTML URL-attribute correction CI log is
`wave12/ci/docs524-9e0bd88-ci-full.log`, SHA-256
`4eea58bf94fd816ba1cef91462e662e21fa05294591a0d51cd36ea9c55c5eb5b`.
It validated final contract commit
`9e0bd883bef57e37e078b2391e8866eb3e8afcf5`, tree
`2fb14698e74fec4254114e2e0081f96731d2f4de`, with 192 Portal checker tests and
67 canonical B503 milestone tests. A successful triggering current-owner
DISABLE clears any matching queued cleanup without a second write. URL-bearing
literal-HTML and documented inline `href`/`src` attributes are percent-decoded
before audit, while non-DOM assignments retain their safe control behavior. The
following evidence-only commit records this immutable contract revision.

The complete failed-pending-enable cleanup correction CI log is
`wave12/ci/docs524-pending-enabling-cleanup-ci.log`, SHA-256
`2475ba63d2e6d00de8da7be30a73e1341858d23e2ab0ef883073d0a08b8409de`.
It validated contract commit
`177b87de203b55d7da3ca4c2af11631a28c60543`, tree
`04182ccbbc83723bbcefb941828afac077078d7a`, with 193 Portal checker tests and
68 canonical B503 milestone tests. A prior-target cleanup registered while an
enable is pending now has two complete terminal outcomes: successful enable
supplies the issuer token and causes exactly one disable, while ACK timeout,
NAK, epoch discard, transport disconnect, or gateway restart clears the
registration without a disable before any later enable. Mutation tests reject
retaining the registration for a later session. The following evidence-only
commit records this immutable contract revision.

The complete enable-failure and URL-attribute correction CI log is
`wave12/ci/docs524-all-enable-failures-urlattrs-ci.log`, SHA-256
`d3adbe59366ebb811e674ab5248dd206c33205835b03bfa8485abff795841e21`.
It validated contract commit
`1f393d6df96a50fb7350dbccff2f1ac00ec39b86`, tree
`44ffc6e070b38591a6e52a730525720cdd6bfd79`, with 207 Portal checker tests and
77 canonical B503 milestone tests. Cleanup registration now clears on every
non-successful enable terminal, including cancellation before bus turnaround,
ACK timeout, NAK, CRC mismatch, bus-arbitration timeout, epoch discard,
disconnect, restart, and any other terminal failure. Inline DOM shorthand now
recognizes every URL-bearing attribute already handled by literal HTML, including
`action`, `formaction`, `poster`, `cite`, and `data`; encoded and direct unsafe
destinations reject while safe destinations remain accepted. The following
evidence-only commit records this immutable contract revision.

The complete pending-enable FSM and plain-control correction CI log is
`wave12/ci/docs524-enabling-fsm-plain-controls-ci.log`, SHA-256
`7a25669f4730d094526a8dfd6db3f02a7db48c39d2267fc7e46360e6028b7a98`.
It validated contract commit
`cc86adf5371fa5b85f51350a517ee0d5157efa78`, tree
`b9b25d28b78c36f30846df6a3692bd504644b534`, with 222 Portal checker tests and
83 canonical B503 milestone tests. Pending-enable cleanup is keyed by a fresh,
never-reused local attempt ID plus target and presentation epoch. The FSM now
separates cancellation before frame emission, proven NAK, ambiguous failures
after emission, epoch discard, and disconnect/restart, with exact release and
single defensive-disable behavior. Rendered plain Markdown is checked for
affirmative declarations of prohibited command controls, including formatted
and entity-decoded spellings, while explicit negative safety wording and benign
presentation prose remain accepted. The following evidence-only commit records
this immutable contract revision.

The complete plain-control shorthand correction CI log is
`wave12/ci/docs524-plain-control-complete-ci.log`, SHA-256
`1740934378b94ade3b87194fb28985013ec939c9b3ff0eb964b80638afbdb9bd`.
It validated contract commit
`b92028347b791a8c5385a94b582e995e4f312f11`, tree
`1c481f3046486a11b13eb3be8b0798f5e2c97e79`, with 223 Portal checker tests and
83 canonical B503 milestone tests. An affirmative exposure verb plus a forbidden
command name now rejects even without a `button` or `control` noun; explicit
negation remains accepted. The following evidence-only commit records this
immutable contract revision.

The complete existential-control correction CI log is
`wave12/ci/docs524-existential-controls-ci.log`, SHA-256
`0b877264dbecdeaa6a6109664043d9974ff9c44115d63ab5213c55e5c0c9dffc`.
It validated contract commit
`957028d4dbfd426db4132fa93d2742c3fc22d126`, tree
`f82e9a5b86f6403a4aeb61ae1e28cad6fc2c68f1`, with 228 Portal checker tests and
83 canonical B503 milestone tests. Normative existential and copular forms such
as `There MUST be a Reset button` now reject, while `MUST NOT be`, `is absent`,
`is prohibited`, and benign non-command copular prose remain accepted. The
following evidence-only commit records this immutable contract revision.

The complete inline-command prose correction CI log is
`wave12/ci/docs524-inline-command-prose-ci.log`, SHA-256
`95987c6c91e256ca77f8cbbf340dc757cb7f1d69de39ba7f0d74702190169e07`.
It validated contract commit
`8df962d228fab7c30067204f185a3ea98d13bb8e`, tree
`d20fdc25c218687aa212d9f9dc1b7c3ffa21329b`, with 232 Portal checker tests and
83 canonical B503 milestone tests. The affirmative prose audit includes inline
code command names and capability/operation/service/feature nouns, while
contracted or explicit negative forms remain accepted. The following
evidence-only commit records this immutable contract revision.

The complete route-surface and epoch-split correction CI log is
`wave12/ci/docs524-route-epoch-split-ci.log`, SHA-256
`880ac961a82f76f3a08a0d150b5820418aab59843881c39459ae3d4171ea06b2`.
It validated contract commit
`9e1d6e599f3eee51c74d5133e7e6e43b03680866`, tree
`3a3741de0d5c69637f9563e7dd5fc1c3b9330591`, with 234 Portal checker tests and
86 canonical B503 milestone tests. Concrete `/portal/api/v1/*` paths are route
surfaces, while the existing exact negative historical-endpoint paragraph
remains allowed. Epoch advance during `Enabling` is split at frame emission:
pre-emission cancels without a write; post-emission fences stale completions and
issues exactly one defensive disable on the current transport epoch before
cleanup, recording the exact cleanup outcome without automatic retry. The
following evidence-only commit records this immutable contract revision.

The complete concrete-route audit CI log is
`wave12/ci/docs524-route-surfaces-complete-ci.log`, SHA-256
`b540f5359e96c4e480ea76a2f01754bf6d12e16fe67a025e326bb37735b844ac`.
It validated contract commit
`9879a8d6f7c87c5f02e515243918d2ab000e6604`, tree
`af4790b58d985cf6d8bd6aa616566d8ae6d5156a`, with 237 Portal checker tests and
86 canonical B503 milestone tests. The complete `/portal/api/v1` family is a
route surface with or without a trailing slash, after percent decoding, and
when carried in a resolved Markdown link or image destination. The one frozen
negative historical-endpoint paragraph remains the only allowed occurrence.
The following evidence-only commit records this immutable contract revision.

The complete disconnect-cleanup and double-negative correction CI log is
`wave12/ci/docs524-disconnect-double-negative-ci.log`, SHA-256
`0f272df69d83eb30bb7553bd90a46aaf9430c164d264e1c5b88cff7eeacdc4b5`.
It validated contract commit
`dc3aaf582ac62bb7e1beea3879514aa1ec4a483f`, tree
`891d197b98679da0dcbedc6a5ec8406a4daaee3f`, with 242 Portal checker tests and
89 canonical B503 milestone tests. A disconnect after possible enable-frame
emission retains only a process-local defensive-cleanup obligation. Reconnect
does not publish the transport epoch as B503-usable or admit another Enable
until one bounded target-specific disable reaches a confirmed terminal outcome;
an ambiguous outcome retains the obligation and fails closed. The plain
Markdown checker also rejects affirmative double-negative exposure such as a
Reset button that “MUST NOT be hidden”, while accepting direct requirements
that the control remain hidden or disabled. The following evidence-only commit
records this immutable contract revision.

The complete literal-HTML route-destination correction CI log is
`wave12/ci/docs524-literal-html-route-ci.log`, SHA-256
`4810098e5cae57299d62d3a3fceb6de7e2448027f7c0eeed38a5e9ae085ff7ff`.
It validated contract commit
`c26685f168ba27a7c82f581812090e3948688167`, tree
`88fcab524e05b7eba6773443a9976798e9fc5193`, with 245 Portal checker tests and
89 canonical B503 milestone tests. URL-bearing literal-HTML attributes are now
percent-decoded and included in the fixed-route audit, so a link or form action
cannot authorize `/portal/api/v1/*` as a fallback while ordinary non-route HTML
destinations remain accepted. The following evidence-only commit records this
immutable contract revision.

The complete confirmed-cleanup and fail-closed correction CI log is
`wave12/ci/docs524-cleanup-ack-ci.log`, SHA-256
`85e6f52e6d20c680d8ea9e67117d7d9c01923b700476c669886465be9bcb0ad4`.
It validated contract commit
`12658921c5e2763dd689a1c8781399c2c598ae78`, tree
`99a02087d83211f49f6cd11d1930af371f226925`, with 249 Portal checker tests and
100 canonical B503 milestone tests. Only a valid native disable ACK proves
cleanup success. Every other defensive-disable outcome keeps the internal FSM
fail-closed in `DISABLED`, retains a process-local operation-ineligible cleanup
obligation, publishes capability `UNKNOWN`, admits no Enable, and permits no
same-epoch retry. A refreshed current-owner DISABLE has the same split outcome.
Both validators also reject supported declarative contradictions that allow
live-monitor operations during `Refreshing` or pair `Disabled` with
`owned:true`. The following evidence-only commit records this immutable
contract revision.

The complete Gateway-cleanup-identity and HTML-ping correction CI log is
`wave12/ci/docs524-gateway-cleanup-id-ping-ci.log`, SHA-256
`8a602b0acc178c5c66c22ab36db600479424942439a32506a2aa850273baedf8`.
It validated contract commit
`dd93e12f53dc4740ea7b493717eae89daa4bf999`, tree
`a27753545728cd12509e6ddd99e0f9141976ce8f`, with 250 Portal checker tests and
101 canonical B503 milestone tests. Gateway allocates and owns the fresh opaque
cleanup-attempt identity; it is distinct from the browser-local enable-attempt
identity, is never caller-supplied, and carries no operation authority. The
URL-bearing attribute audit also includes `ping`, so an activated anchor cannot
request an alternate Portal API route while retaining a safe `href`. The
following evidence-only commit records this immutable contract revision.

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
