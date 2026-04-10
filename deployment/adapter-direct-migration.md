# Adapter-Direct Migration Guide

Migration and rollback procedures for transitioning from proxy-based (ebusd-tcp)
topology to adapter-direct transport.

## Forward Migration (Proxy-Based to Adapter-Direct)

### HA Addon Users

1. Update the addon to a version with adapter-direct support.
2. In the addon configuration, set:
   - `adapter_direct_enabled: true`
   - `adapter_direct_address: "boiler.local:9999"` (your adapter's address)
   - Optionally: `adapter_proxy_listen: "127.0.0.1:19001"` for ebusd coexistence
3. Restart the addon.
4. Verify via MCP: `zones.get`, `dhw.get`, `boiler_status.get` should all return
   valid data within one polling cycle.

### Standalone Gateway Users

1. Stop the gateway process.
2. Change startup flags:
   - Add: `--adapter-direct enh://boiler.local:9999`
   - Optionally add: `--proxy-listen :19001` (enables proxy for non-gateway clients)
3. Start the gateway.
4. Verify via MCP or GraphQL that semantic planes populate normally.

## Rollback (Adapter-Direct to Proxy-Based)

1. Set `adapter_direct_enabled: false` (addon) or remove the `--adapter-direct`
   flag (standalone).
2. Restart the gateway or addon.
3. The previous proxy-based topology is restored automatically; no additional
   configuration changes are required.

## Notes

- Zero-downtime migration is not required. A restart is acceptable and expected.
- The eBUS continues to operate independently during the gateway restart window;
  no bus state is lost.
- When `--proxy-listen` is configured, the standalone proxy remains available for
  non-gateway consumers (e.g. ebusd clients) even in adapter-direct mode.
- The adapter-direct transport and proxy-based transport are mutually exclusive
  at the gateway level. Only one may be active at a time.
