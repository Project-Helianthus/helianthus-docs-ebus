# Platform Documentation Ownership And Doc Gates

## Purpose

This ADR defines where platform contracts and protocol facts live while
Helianthus expands from eBUS to eeBUS and later protocol families.

## Canonical Ownership

| Content | Canonical owner |
| --- | --- |
| Cross-protocol MCP lifecycle | `helianthus-docs-ebus/docs/platform/` |
| Raw evidence, snapshot, and hash contract | `helianthus-docs-ebus/docs/platform/` |
| Semantic promotion gate | `helianthus-docs-ebus/docs/platform/` |
| Multi-runtime coexistence policy | `helianthus-docs-ebus/docs/platform/` |
| GraphQL, Portal, and HA rollout order | `helianthus-docs-ebus/docs/platform/` |
| eBUS wire protocol and Vaillant eBUS facts | `helianthus-docs-ebus/protocols/` |
| eeBUS SHIP/SPINE, VR940f, and eeBUS evidence | `helianthus-docs-eebus/` |

`helianthus-docs-ebus/docs/platform/` is a transitional platform home. Protocol
repositories never become long-term owners of cross-protocol contracts.

## Summary-Only Pages

Non-owning pages may summarize canonical material only with this shape:

```text
Canonical source: <repo/path>. This page is summary-only and non-normative.

<one-paragraph purpose>

Links:
- <canonical page>

Local usage notes:
- <optional>
```

Summary-only pages must not contain requirements, mandatory language,
acceptance criteria, checklists, version tables, deprecation policy, or
approval steps.

## Doc-Gate Rules

Every PR that changes architecture, API, protocol behavior, runtime behavior,
state-machine behavior, reverse-engineered knowledge, or consumer-visible
semantics must update the canonical owner docs in the same PR or link already
merged documentation commits from the canonical owner.

A PR fails doc-gate when it:

- adds normative platform text outside `docs/platform/`;
- duplicates acceptance criteria from the canonical page;
- publishes protocol claims without a publishable evidence id;
- treats an operator note as a protocol fact;
- introduces candidate or conflicted values into consumer docs as stable.

## Future Platform Repository

Create `helianthus-docs-platform` after this eeBUS raw-first bootstrap when a
later non-eBUS protocol reaches a promoted-leaf gate, or when a cross-protocol
contract changes for reasons unrelated to eBUS or the eeBUS VR940f raw-first
track. The migration moves platform pages, leaves stubs here, and updates
canonical links. Protocol repositories remain protocol-fact homes only.
