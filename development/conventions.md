# Development Conventions

## Go Version

- Minimum Go version: **1.22**
- Library targets are expected to remain TinyGo compatible.

## Build Tags

- `//go:build !tinygo` for full-Go only implementations.
- `//go:build tinygo` for TinyGo-specific stubs or alternatives.

## Error Handling

- Sentinel errors live in the errors package and are matched via `errors.Is`.
- Callers wrap errors with context but do not replace the sentinel.

## Concurrency Rules (Implemented in Bus)

- Bus serialization is centralized via a priority queue.
- Retry logic lives in Bus and is applied per frame type.

## Testing

- Transport, protocol, and type logic are covered by unit tests in `helianthus-ebusgo`.
- Registry and schema logic are covered by unit tests in `helianthus-ebusreg`.
