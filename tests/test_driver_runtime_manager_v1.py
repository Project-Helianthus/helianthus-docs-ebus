from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE = ROOT / "docs" / "platform" / "driver-runtime-manager-v1.md"
API = ROOT / "api" / "driver-runtime-v1.md"
PORTAL = ROOT / "api" / "portal.md"
MODBUS_ADDON = ROOT / "api" / "modbus-v1-addon-runtime.md"
PLATFORM_INDEX = ROOT / "docs" / "platform" / "README.md"


def _normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_closed_driver_snapshot_v1_vocabulary() -> None:
    text = _normalized(API)
    for required in (
        "DriverSnapshotV1",
        "`ebus.primary`",
        "`modbus.tcp.default`",
        "`eebus.primary`",
        "`RUNNING`, `STOPPED`",
        "`DISABLED`, `STOPPED`, `STARTING`, `RUNNING`, `DEGRADED`, `BACKOFF`, `STOPPING`, `FAILED`",
        "`reason`",
        "`retry`",
        "`generation`",
        "`revision`",
        "`attempt`",
        "`capabilities`",
        "`effective_capabilities`",
        "`safety_quarantined`",
    ):
        assert required in text


def test_snapshot_invariants_are_explicit() -> None:
    text = _normalized(API)
    for required in (
        "desired state is operator intent",
        "observed state is runtime fact",
        "monotonically increases",
        "generation changes only when a new driver instance is admitted",
        "revision changes on every externally visible snapshot mutation",
        "attempt is scoped to one generation",
        "reason is a closed categorical value",
        "endpoint, credential, raw transport error, or protocol payload",
        "capabilities are immutable for one generation",
    ):
        assert required in text


def test_effective_capability_withdrawal_is_atomic_with_stop() -> None:
    api = _normalized(API)
    architecture = _normalized(ARCHITECTURE)
    for required in (
        "effective capabilities are the currently admitted subset",
        "subset of `capabilities`",
        "empty in `DISABLED`, `STOPPED`, `STARTING`, `BACKOFF`, `STOPPING`, and `FAILED`",
        "same per-driver admission lock",
        "withdraws all effective capabilities before publishing `STOPPING`",
        "no provider invocation can be admitted after withdrawal",
    ):
        assert required in api
    for required in (
        "atomic effective-capability withdrawal",
        "blocked before provider invocation",
        "stop/restart withdrawal race",
    ):
        assert required in architecture


def test_unproven_close_enters_process_epoch_safety_quarantine() -> None:
    api = _normalized(API)
    architecture = _normalized(ARCHITECTURE)
    for required in (
        '"safety_quarantined": true',
        "`CLOSE_UNCONFIRMED`",
        "`SAFETY_QUARANTINED`",
        "observed state is `FAILED`",
        "effective capabilities are empty",
        "manual start and restart",
        "automatic retry",
        "provider construction",
        "until process restart",
    ):
        assert required in api
    for required in (
        "ordinary recoverable `FAILED`",
        "does not set `safety_quarantined`",
        "unproven-close safety quarantine",
        "cannot be cleared by an API operation",
    ):
        assert required in architecture


def test_active_callback_timeout_never_closes_beneath_raw_transport() -> None:
    api = _normalized(API)
    architecture = _normalized(ARCHITECTURE)
    for required in (
        "actively executing admitted lease callback",
        "must not send `CloseRequest`",
        "must not close beneath `RawTransport`",
        "boundedly returns `CLOSE_UNCONFIRMED` safety quarantine",
        "blocks replacement",
        "fresh `CloseRequest` and close proof may run only when no callback actively uses the transport",
        "abandoned non-invoking lease",
        "a proven `STOP_TIMEOUT` outcome",
        "outcome is restartable",
    ):
        assert required in api
        assert required in architecture


def test_operation_concurrency_idempotency_and_audit() -> None:
    text = _normalized(API)
    for required in (
        "`drivers.v1.list`",
        "`drivers.v1.start`",
        "`drivers.v1.stop`",
        "`drivers.v1.restart`",
        "one operation is active per driver",
        "same idempotency key",
        "same operation result",
        "different intent",
        "`CONFLICT`",
        "stable `UNAVAILABLE`",
        "one audit record",
        "request ID",
        "operation ID",
        "before and after revision",
        "never contains an endpoint, credential, raw error, or protocol payload",
    ):
        assert required in text


def test_nonfatal_process_and_driver_readiness_boundary() -> None:
    text = _normalized(ARCHITECTURE)
    for required in (
        "Process readiness is not driver readiness",
        "protocol-local startup failure never terminates the shared gateway",
        "HTTP, MCP, GraphQL, and the operator surface remain available",
        "stable unavailable provider",
        "`FAILED` or `BACKOFF`",
        "At least one failed driver does not make process readiness fail",
        "global-fatal boundary",
    ):
        assert required in text


def test_retry_stop_restart_and_runtime_override_semantics() -> None:
    text = _normalized(ARCHITECTURE)
    for required in (
        "bounded exponential backoff",
        "retry budget",
        "`STARTING -> RUNNING`",
        "`STARTING -> BACKOFF`",
        "`BACKOFF -> STARTING`",
        "`STOPPING -> STOPPED`",
        "drain deadline",
        "adapter-owned close worker",
        "restart is one serialized stop-then-start operation",
        "process-epoch-local",
        "does not rewrite add-on options",
        "does not survive a gateway process restart",
    ):
        assert required in text


def test_transport_close_channels_have_explicit_owner_and_fresh_proof_budget() -> None:
    api = _normalized(API)
    architecture = _normalized(ARCHITECTURE)
    for required in (
        "`DriverRuntime` is the sole sender to `CloseRequest`",
        "adapter owns the `CloseRequest` receiver and close worker",
        "adapter closes `Closed` only after its resources and adapter-owned closer retire",
        "never invokes an arbitrary manager callback or starts a manager cleanup goroutine",
        "closed or invalid `CloseRequest` is a lifecycle ownership violation",
        "adapter-owned close worker",
    ):
        assert required in api
    for required in (
        "two separately bounded phases",
        "fresh close-request/proof budget",
        "drain budget plus a fresh close/proof budget",
        "`STOP_TIMEOUT` only after adapter-proven closure",
        "absent adapter closure proof enters safety quarantine",
    ):
        assert required in architecture
    forbidden = "forced" + " local " + "tear" + "down"
    for path in (API, ARCHITECTURE):
        assert forbidden not in path.read_text(encoding="utf-8").lower()


def test_addon_validation_and_fatal_boundary_are_closed() -> None:
    architecture = _normalized(ARCHITECTURE)
    addon = _normalized(MODBUS_ADDON)
    for required in (
        "validates each enabled driver's own configuration independently",
        "invalid driver-local configuration disables only that driver",
        "global process inputs",
        "packaged binary integrity",
        "unreadable global configuration document",
        "global-fatal",
    ):
        assert required in architecture
    for required in (
        "DriverManager V1 successor",
        "driver-local Modbus validation failure",
        "must not prevent the gateway process from starting",
    ):
        assert required in addon


def test_rollout_is_mcp_first_and_one_release_acceptance_is_explicit() -> None:
    text = _normalized(ARCHITECTURE)
    for required in (
        "MCP prototype",
        "GraphQL parity",
        "Portal rollout",
        "Home Assistant rollout",
        "one consolidated add-on release",
        "one multi-architecture build",
        "one CI/CD publication",
        "all three driver IDs",
        "startup failure injection",
        "process remains ready",
    ):
        assert required in text


def test_portal_and_platform_indexes_link_the_contract() -> None:
    portal = _normalized(PORTAL)
    platform = _normalized(PLATFORM_INDEX)
    for required in (
        "[`driver-runtime-v1.md`](./driver-runtime-v1.md)",
        "Portal is a consumer, not lifecycle authority",
    ):
        assert required in portal
    for required in (
        "[`driver-runtime-manager-v1.md`](./driver-runtime-manager-v1.md)",
        "[`../../api/driver-runtime-v1.md`](../../api/driver-runtime-v1.md)",
    ):
        assert required in platform
