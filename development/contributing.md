# Contributing

## Scope

This repository documents **implemented behavior** only. If a feature is not present in code, it should be described as not implemented rather than speculating.

## Dual License Model

This documentation is split across two licenses:

- **CC0-1.0** for `protocols/` and `types/` (public domain, implementation-agnostic).
- **AGPL-3.0** for everything else (Helianthus-specific architecture, APIs, and deployment).

When editing, keep protocol/type content implementation-neutral and avoid Helianthus-specific references.

## Style

- Prefer concise, testable statements.
- Include wire layouts, byte formats, and examples with language-tagged code blocks.
- Keep diagrams in Mermaid for architecture, data flow, and state machines.

## Documentation Gate (Doc-Gate)

Doc-gate is mandatory for changes that affect implemented architecture, APIs, or behavior. A PR that triggers doc-gate is not merge-ready until required docs are updated in the same PR (or in a linked docs PR that is already merged).

### Trigger Matrix

| Change trigger | Practical examples | Required documentation updates | Gate decision |
|---|---|---|---|
| Architecture change | Plane model updates, routing/lifecycle changes, projection model changes | Update relevant files in `architecture/` (typically `architecture/overview.md`, `architecture/decisions.md`, plus domain pages like `architecture/vaillant.md`) | **Block merge** until docs are updated |
| API surface change | GraphQL fields/types, MCP tool behavior, HTTP endpoint semantics | Update relevant files in `api/` (`api/graphql.md`, `api/mcp.md`, and endpoint behavior notes) | **Block merge** until docs are updated |
| Runtime behavior / protocol change | New wire layout, parser semantics, status handling, discovery flow, smoke/device-dump behavior | Update affected docs in `protocols/`, `types/`, and/or `development/` with concrete byte/field behavior | **Block merge** until docs are updated |
| Internal-only refactor with no external behavior change | Renames/moves with no architecture, API, or behavior effect | No mandatory doc update; add a short PR note explaining why doc-gate does not trigger | Merge allowed after reviewer confirmation |

### Mandatory Gate Flow

1. **Author classifies the PR** using the trigger matrix above.
2. **Author updates docs** for all triggered categories in the same PR, or links merged docs PR(s).
3. **Author completes checklist** in the PR description.
4. **Reviewer verifies doc-gate** coverage before approval.
5. **Merge remains blocked** until checklist items are satisfied and CI is green.

### PR Author Checklist

- [ ] I evaluated doc-gate triggers for architecture, API, and runtime behavior.
- [ ] I updated all required docs in this PR (or linked already-merged docs PRs).
- [ ] For architecture-impacting changes, I updated the relevant `architecture/` docs.
- [ ] For API-impacting changes, I updated the relevant `api/` docs.
- [ ] For behavior/protocol-impacting changes, I updated the relevant `protocols/`, `types/`, and/or `development/` docs.
- [ ] I added a concise “docs updated / not triggered” note in the PR description.

### PR Reviewer Checklist

- [ ] Trigger classification is correct for architecture/API/behavior impact.
- [ ] Required docs are updated and consistent with implemented behavior.
- [ ] Wire formats / API fields / behavior notes include concrete, testable details where needed.
- [ ] PR description includes clear evidence of doc updates (or valid non-trigger rationale).
- [ ] I will withhold approval if doc-gate requirements are incomplete.

## Transport Runtime Gate (Merge Blocking)

For eBUS transport/protocol changes, merge readiness requires an additional runtime gate:

- **Scope:** changes in transport/protocol code paths (gateway transport selection, proxy upstream/downstream transport behavior, ebusgo transport implementations, arbitration behavior tied to wire protocol).
- **Required artifact:** full matrix result (`T01..T88`) with no unexpected failures (`fail`) and no unexpected passes (`xpass`) against the active expected-failure inventory.
- **Required reference:** PR description must include the `results/index.json` path or attachment reference.
- **Expected-failure inventory:** any `xfail` must map to a documented transport limitation (case IDs + reason), and that inventory must be attached in the PR description.
- **Default policy:** if runtime gate is not satisfied, merge is blocked.
- **Owner override:** only explicit owner approval may bypass this gate, with a written reason.
