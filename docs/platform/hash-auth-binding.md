Canonical source: this page.

# Deterministic Hash And Auth Binding

## Canonical Material

Cross-runtime JSON hash material uses RFC 8785 JSON Canonicalization Scheme
bytes and SHA-256. Hash input excludes transport framing and formatting but
includes the complete versioned binding object and payload. Non-JSON payloads
must first map to the language-neutral envelope without lossy conversion.

The binding object contains:

- envelope and payload schema version;
- runtime id and runtime kind;
- tool or operation id and version;
- snapshot or request scope;
- mask tier;
- effective auth scope;
- capture instant or window;
- payload.

Two hashes are comparable only when every binding field matches exactly. A
hash is evidence of byte equality under that binding, not proof of semantic
equivalence, authorization, freshness, or device identity.

## Authorization

The producer calculates effective auth scope after authentication and policy
evaluation. A caller-provided scope is never authoritative. Snapshot creation
binds the effective scope and mask tier before hashing; dereference requires an
exact match and does not re-mask captured data under a broader scope.

Authentication material, tokens, keys, certificate data, raw peer identifiers,
network endpoints, and local paths are never included in public artifacts.
Authorization failure is `rejected`, while unavailable policy or identity
state is `unavailable`; neither is represented as an empty successful result.

## Verification

Verification reconstructs the complete binding object, applies RFC 8785, and
compares the SHA-256 digest in constant-time where the runtime exposes secret
or authorization-sensitive references. Missing binding fields make the hash
non-comparable and terminal for promotion.
