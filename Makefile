# helianthus-docs-ebus — local validation targets
#
# Usage:
#   make validate-schemas      # runtime-state JSON Schema gate (M0_DOC_GATE)
#   make ci-local              # full local CI suite (ci_local.sh)
#
# Plans referenced:
#   - runtime-state-w19-26.locked (validate-schemas: AD05/AD22 acceptance)

.PHONY: validate-schemas ci-local help

help:
	@echo "Available targets:"
	@echo "  validate-schemas    Validate runtime-state JSON Schema vs example + negative fixtures (M0_DOC_GATE)"
	@echo "  ci-local            Run full local CI suite (scripts/ci_local.sh)"

validate-schemas:
	@bash scripts/check_runtime_state_schema.sh

ci-local:
	@bash scripts/ci_local.sh
