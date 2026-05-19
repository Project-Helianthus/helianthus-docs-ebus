# Prometheus Alert Rules — Helianthus Gateway

This document is the operations-side reference for Prometheus alert rules
that the operator deployment manifest MUST include alongside the
helianthus-ebusgateway image. The gateway itself only exposes counters;
the *alerting decisions* — including any cross-counter or
mode-conditioned predicates — live in the Prometheus rules file shipped
with the deployment.

## Index

| Alert name | Source counter | Reference |
|---|---|---|
| `HelianthusRound9FiredUnderProxy` | `helianthus_round9_absorb_entered_total` | [frame-atomic-visibility-v8 §1.12 / I8](../architecture/adaptermux/frame-atomic-visibility-v8.md) |

## HelianthusRound9FiredUnderProxy

**Owner:** operations team. The rule MUST be present in the Prometheus
config (`prometheus-rules.yaml`) before the adaptermux classifier is
enabled in `enforce` mode. Step C live-bus validation (v8 §14) verifies
rule presence via the Prometheus API before proxy rollout.

**Counter source:** `helianthus_round9_absorb_entered_total`
— exported by `helianthus-ebusgo`'s `protocol.Bus.Round9AbsorbEntered()`
accessor. The counter is named neutrally on the Go side — it counts
every round-9 AUTO-SYN absorb predicate fire inside `sendRawWithEcho`
(`protocol/bus.go`), gated on the runtime phase predicate
`inSendRawWithEchoActiveEchoWait()` (see [frame-atomic-visibility-v8 §1.8](../architecture/adaptermux/frame-atomic-visibility-v8.md)).
The "fired under proxy" interpretation lives ENTIRELY in this alert
rule's PromQL (which AND-s the counter with `classifier_mode == "enforce"`),
not in the counter's code-side name. This keeps the Go protocol layer
free of cross-repo coupling.

**Why this alert exists:** under v8 I8, round-9 absorb code is RETAINED
as a legacy fallback for direct-adapter mode (no proxy mediating wire
AUTO-SYNs). When the adaptermux classifier is in `enforce` mode, the
proxy is contractually obligated to filter wire AUTO-SYNs before they
reach the gateway's echo position; any round-9 fire under that mode is
a v8 invariant violation — the proxy is not filtering correctly.

**Suggested rule:**

```yaml
groups:
  - name: helianthus.round9
    rules:
      - alert: HelianthusRound9FiredUnderProxy
        expr: |
          rate(helianthus_round9_absorb_entered_total[5m]) > 0
          and on(instance) helianthus_adaptermux_classifier_mode{mode="enforce"} == 1
        for: 1m
        labels:
          severity: warning
          component: helianthus-gateway
          invariant: frame-atomic-v8-I8
        annotations:
          summary: "Round-9 AUTO-SYN absorb fired while adaptermux classifier is in enforce mode"
          description: |
            The gateway's round-9 AUTO-SYN absorb predicate fired on instance
            {{ $labels.instance }} while the adaptermux classifier is in
            `enforce` mode. Per frame-atomic-visibility v8 §1.8 / I8, the
            proxy MUST filter wire AUTO-SYNs before they reach the gateway's
            echo position when classifier mode is `enforce` — round-9 firing
            indicates the proxy is not correctly filtering. Investigate the
            adaptermux classifier path and per-session pacer; this is the
            v8 invariant violation that the round-9 fallback was kept to
            measure, not to mask.
          runbook_url: |
            https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/adaptermux/frame-atomic-visibility-v8.md#18
```

**Gating model:**

- The counter increments unconditionally on every round-9 fire, regardless
  of classifier mode. The Go code does NOT consult the classifier mode
  (no cross-repo coupling).
- The alert rule does the gating via the `helianthus_adaptermux_classifier_mode`
  gauge (exported by `helianthus-ebusgateway/internal/adaptermux` —
  scheduled for Phase 3 of the frame-atomic-visibility rollout). Until
  Phase 3 lands, deploy with the second clause commented out; the alert
  will trip on ANY round-9 fire, which is conservative and
  acceptable for the bootstrap phase.

**Pre-deploy gate (Step C live-validation, v8 §14):**

```bash
# Check the rule is loaded.
curl -s "${PROMETHEUS_URL}/api/v1/rules" \
  | jq '.data.groups[].rules[] | select(.name == "HelianthusRound9FiredUnderProxy")'

# Check the rule was loaded WITHOUT errors.
curl -s "${PROMETHEUS_URL}/api/v1/rules" \
  | jq '.data.groups[].rules[] | select(.name == "HelianthusRound9FiredUnderProxy") | .lastError // empty'
# Empty output = OK; any output here is a load error.
```

If the rule is absent or fails to load, the proxy MUST NOT be promoted
to `enforce` mode — the v8 invariant is unobservable without it.
