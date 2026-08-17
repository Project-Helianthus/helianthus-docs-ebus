# Adapter-Direct Migration Guide

Migration and rollback procedures for transitioning from proxy-based (ebusd-tcp)
topology to adapter-direct transport.

## Forward Migration (Proxy-Based to Adapter-Direct)

### HA Addon Users

1. Update the addon to a version with adapter-direct support.
2. In the addon configuration, set:
   - `adapter_direct_enabled: true`
   - `adapter_direct_protocol: "enh"` or `"ens"` (default: `"enh"`)
   - `adapter_direct_address: "adapter.example.invalid:9999"` (your adapter's
     host and port)
   - `proxy_profile: "disabled"`
   - Optionally, `proxy_listen_addr: "0.0.0.0:19001"` to expose the
     gateway-integrated proxy listener for ebusd coexistence
3. Restart the addon.
4. Verify via MCP: `zones.get`, `dhw.get`, `boiler_status.get` should all return
   valid data within one polling cycle.

The add-on maps the typed protocol selector to the gateway URI without probing
the adapter over HTTP and without heuristic fallback:

| `adapter_direct_protocol` | Gateway address |
|---|---|
| `enh` | `adapter-direct://HOST:PORT` |
| `ens` | `adapter-direct-ens://HOST:PORT` |

`proxy_profile` configures only the separate case where the gateway consumes an
external proxy endpoint. It does not select the protocol used for the physical
adapter-direct connection. A legacy scheme prefix in `adapter_direct_address`
may be accepted as input syntax, but it does not override
`adapter_direct_protocol`.

For upgrade compatibility, the add-on recognizes one explicit legacy state:
adapter-direct is enabled, persisted options do not yet contain
`adapter_direct_protocol`, `proxy_profile` is `enh` or `ens`, and
`proxy_endpoint` is empty. The wrapper migrates that old profile value to the
matching typed adapter protocol for the current startup and normalizes the
effective proxy profile to `disabled`. Once `adapter_direct_protocol` exists in
persisted options, it is authoritative even if a stale empty-endpoint profile
remains. Save the typed selector and `proxy_profile: disabled` after upgrading.
This compatibility rule does not probe the adapter and is not a protocol
autodetection or fallback mechanism.

Adapter-direct and an external proxy endpoint are mutually exclusive add-on
configurations. To use an external proxy instead, disable adapter-direct and
configure the proxy explicitly:

```yaml
adapter_direct_enabled: false
proxy_profile: enh # or ens
proxy_endpoint: proxy.example.invalid:9999
```

#### eBUS Adapter 3 (ENS)

An eBUS Adapter 3 running build `20221215` was verified with its eBUS endpoint
configured as ENS on TCP port `9999`. Use the explicit selector and keep the
external-proxy profile disabled:

```yaml
adapter_direct_enabled: true
adapter_direct_protocol: ens
adapter_direct_address: adapter.example.invalid:9999
proxy_profile: disabled
proxy_endpoint: ""
proxy_listen_addr: 0.0.0.0:19001
```

The `proxy_listen_addr` option preserves the proxy functionality embedded in
the Helianthus gateway binary. Removing the former standalone proxy process or
using a single `exec`-based add-on wrapper does not remove this listener.

### Standalone Gateway Users

1. Stop the gateway process.
2. Select the supported adapter-direct transport and exact address URI:

   ```sh
   # ENH
   helianthus-gateway \
     -transport adapter-direct \
     -network tcp \
     -address adapter-direct://adapter.example.invalid:9999

   # ENS
   helianthus-gateway \
     -transport adapter-direct \
     -network tcp \
     -address adapter-direct-ens://adapter.example.invalid:9999
   ```

   Optionally add `-proxy-listen :19001` to expose the integrated proxy for
   non-gateway clients.
3. Start the gateway.
4. Verify via MCP or GraphQL that semantic planes populate normally.

## Rollback (Adapter-Direct to Proxy-Based)

1. For the add-on, set `adapter_direct_enabled: false` and restore the previous
   `transport`, `network`, and `address` values. If the previous topology used
   an external adapter proxy, also restore `proxy_profile` and
   `proxy_endpoint`.
2. For a standalone gateway, replace `-transport adapter-direct` and its
   adapter-direct address with the previous proxy transport and endpoint.
3. Restart the gateway or addon.

## Notes

- Zero-downtime migration is not required. A restart is acceptable and expected.
- The eBUS continues to operate independently during the gateway restart window;
  no bus state is lost.
- When `-proxy-listen` is configured, the standalone proxy remains available for
  non-gateway consumers (e.g. ebusd clients) even in adapter-direct mode.
- The adapter-direct transport and proxy-based transport are mutually exclusive
  at the gateway level. Only one may be active at a time.
