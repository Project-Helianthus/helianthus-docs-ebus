from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "api" / "eebus-operator-admin.md"
PORTAL = ROOT / "api" / "portal.md"
DECISIONS = ROOT / "architecture" / "decisions.md"
B524 = ROOT / "architecture" / "b524-structural-decisions.md"
B524_MAPPING = ROOT / "architecture" / "b524-semantic-mapping.md"
FSM_MAP = ROOT / "architecture" / "semantic-structure-fsm-map.md"
CONFIG_GATES = ROOT / "architecture" / "semantic-configuration-gates.md"
GRAPHQL = ROOT / "api" / "graphql.md"
MCP = ROOT / "api" / "mcp.md"
HA = ROOT / "development" / "ha-integration.md"


def _normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_shared_operator_boundary_is_closed_and_consumer_safe() -> None:
    text = _normalized(CONTRACT)
    for required in (
        "canonical protocol-specific contract remains exclusively in",
        "post-m9-operator-pairing-browsers-v1.md",
        "post-m9-operator-admin-v1.md",
        "Those documents alone own protocol routes",
        "`eebus.v1.*` remains the only eeBUS MCP namespace",
        "all operator reads and mutations fail closed",
        "authentication and authorization run before object resolution",
        "CSRF-safe mutation admission",
        "Home Assistant receives no mutation grant",
        "Portal and Home Assistant never read the trust store",
        "owner-only operator socket",
        "private keys, tokens, private PEM, trust-store bytes",
        "must not enter `ebus.v1`, GraphQL semantic fields, or the semantic registry",
    ):
        assert required in text


def test_protocol_contract_is_linked_not_duplicated() -> None:
    text = _normalized(CONTRACT)
    for forbidden in (
        "/admin/eebus/v1/",
        "admin_boundary_unavailable",
        "`trusted`, `connected`, `discovered`, and `candidate`",
        "40-character lowercase certificate short identifier",
        "device/entity/feature/use-case tree",
        "snapshot hash",
        "one device, eleven entities, twenty features",
    ):
        assert forbidden not in text
    for required in (
        "authorized inspection of lossless protocol-native data",
        "canonical protocol documents own all tree shape",
        "Home Assistant and public formatters receive no raw",
    ):
        assert required in text


def test_fm5_mode_cannot_hide_failed_interpretation() -> None:
    text = _normalized(CONTRACT)
    for required in (
        "`INTERPRETED`, `GPIO_ONLY`, and `ABSENT`",
        "`fm5_semantic_degraded_reason`",
        "`CONTROLLER_UNREACHABLE`",
        "`CONFIGURATION_UNAVAILABLE`",
        "`CONFIGURATION_NOT_INTERPRETABLE`",
        "`SOLAR_ACQUISITION_FAILED`",
        "`CYLINDER_ACQUISITION_FAILED`",
        "current or retained admissible FM5 identity evidence exists",
        "`CONTROLLER_UNREACHABLE` when only retained evidence remains",
        "must not collapse an acquisition or configuration failure into an unexplained `GPIO_ONLY`",
        "reason is `null` only for `INTERPRETED` and `ABSENT`",
    ):
        assert required in text


def test_version_has_one_runtime_build_source_and_portal_links_contract() -> None:
    contract = _normalized(CONTRACT)
    portal = _normalized(PORTAL)
    decisions = _normalized(DECISIONS)
    for required in (
        "single injected build-time release version",
        "runtime health, Portal health, and add-on package metadata",
        "hard-coded fallback release number is forbidden",
        "startup fails closed for a release artifact whose injected version is empty or mismatched",
    ):
        assert required in contract
    assert "[`eebus-operator-admin.md`](./eebus-operator-admin.md)" in portal
    assert '"fm5_semantic_degraded_reason": null' in portal
    assert '"fm5_semantic_evidence_revision": "opaque-acquisition-revision"' in portal
    assert "ADR-028: Post-M9 operator boundary, FM5 degradation, and version authority" in decisions


def test_existing_fm5_authority_uses_the_provider_verdict() -> None:
    text = _normalized(B524)
    for required in (
        "one mode/reason/revision verdict",
        "`GPIO_ONLY` plus exactly one closed reason",
        "may not become an unexplained `GPIO_ONLY`",
        "`fm5SemanticDegradedReason`",
        "`fm5SemanticEvidenceRevision`",
        "retains the last coherent solar snapshot without updating it",
        "retains the last coherent instance set without updating it",
        "`ABSENT` or `GPIO_ONLY / CONFIGURATION_NOT_INTERPRETABLE` withdraws the family",
        "requires a decodable `temperatureC` to create or update an instance",
        "an already coherent instance may be retained unchanged",
        "does not refresh its values",
    ):
        assert required in text
    mapping = _normalized(B524_MAPPING)
    for required in (
        "A transient acquisition degradation retains only the last coherent snapshot",
        "it is not a new live sample",
        "does not update or zero it",
        "mode/reason/revision result",
    ):
        assert required in mapping
    fsm_map = _normalized(FSM_MAP)
    gates = _normalized(CONFIG_GATES)
    for text in (fsm_map, gates):
        for required in (
            "transient `GPIO_ONLY` acquisition reason retains the last coherent",
            "`ABSENT` or `GPIO_ONLY / CONFIGURATION_NOT_INTERPRETABLE` withdraws",
            "without updating or zeroing it",
        ):
            assert required in text
    assert "only instances with live temperature evidence are published" not in gates


def test_mcp_graphql_and_ha_expose_one_fm5_verdict() -> None:
    mcp = _normalized(MCP)
    graphql = _normalized(GRAPHQL)
    ha = _normalized(HA)
    for required in (
        "`ebus.v1.semantic.fm5_interpretation.get`",
        "`mode`, `degraded_reason`, and `evidence_revision`",
        "no v2 tool or legacy alias is introduced",
    ):
        assert required in mcp
    for required in (
        "fm5Interpretation: Fm5Interpretation!",
        "degradedReason: Fm5SemanticDegradedReason",
        "evidenceRevision: String!",
        "Existing `fm5SemanticMode` remains stable",
    ):
        assert required in graphql
    for required in (
        "candidate-free gateway projection",
        "fm5Interpretation { mode degradedReason evidenceRevision }",
        "does not derive a reason",
        "`GPIO_ONLY` without a closed reason is an invalid response",
    ):
        assert required in ha
