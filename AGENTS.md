# AGENTS

This repository is part of the **Helianthus Multi-Protocol HVAC Gateway Platform**.

## Dual-AI Operating Model

All development follows the dual-AI orchestrator protocol defined in the workspace-root [`AGENTS.md`](../AGENTS.md):

- **Orchestrator:** Claude Code — orchestration, hard dev (complexity 7–10), angry tester, deep consultant
- **Co-Pilot:** Codex — adversarial planning, easy dev (complexity 1–6), code review, second opinions
- Phases: Adversarial Planning → Smart Routing → Dual Code Review
- Hard rules: one issue/PR per repo, squash+merge only, doc-gate, transport-gate, MCP-first

See the root AGENTS.md for the full protocol, routing tables, system prompts, and invariants.

---

## Repo-Specific Rules

These instructions apply to the entire repository.

### Workflow

1. Keep changes scoped to the active issue.
2. Keep at most one open PR for this repository at any time.
3. Run `./scripts/ci_local.sh` before pushing.
4. React (emoji) to every review comment and reply with status when actioned.
5. Do not commit private environment details (IP addresses, credentials, device identifiers). Use placeholders.

