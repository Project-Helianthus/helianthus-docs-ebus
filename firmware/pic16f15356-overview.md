# PIC16F15356 eBUS Adapter Firmware

This document describes the architecture and scope of the PIC16F15356 firmware used in Helianthus eBUS adapter v3.x hardware.

See also:

- [`protocols/enh.md`](../protocols/enh.md) for the Enhanced adapter protocol encoding.
- [`protocols/ens.md`](../protocols/ens.md) for the high-speed serial variant.
- [`architecture/overview.md`](../architecture/overview.md) for the gateway-level architecture.

## Scope

The current PIC16F15356 firmware tree is a **host-buildable adapter/runtime scaffold** between an ESP host and the eBUS adapter hardware model. It is **not** yet a silicon-complete production image, and all eBUS protocol responsibilities above the adapter framing layer remain delegated to host software.

The firmware handles:

- SYN byte (`0xAA`) detection and forwarding
- ENH encoding and decoding between PIC and host (the runtime uses ENH protocol only; there is no ENS parser path in the current firmware)
- Bus byte receive and forwarding to the host (the firmware does not implement bus TX -- it receives and relays only; the HAL has no EUSART1 write binding for bus-side transmission)
- Scan window management and descriptor processing
- Periodic status emission (snapshot and variant frames)
- Host parser timeout enforcement (64 ms)
- Bootloader framing engine for flash / EEPROM / config commands
- Runtime normalization from legacy loader config windows (`WRITE_CONFIG`, MUI)

## Architecture

```mermaid
graph TD
    subgraph PIC16F15356["PIC16F15356 Firmware"]
        APP["Application<br/><i>pic16f15356_app</i><br/>ISR + mainline wrapper"]
        RT["Runtime<br/>Protocol FSM + ENH codec (RX only)<br/>Scan engine + Descriptor merge<br/>Status emission + Diagnostics"]
        HAL["HAL<br/><i>pic16f15356_hal</i><br/>ISR latch FIFOs + TMR0 tick<br/>UART mode switching"]
        BOOT["Bootloader<br/><i>picboot</i><br/>STX frames + Flash/EEPROM<br/>11 commands + CRC16-CCITT"]
        APP --> RT
        RT --> HAL
        BOOT -.->|reset handoff| APP
    end

    subgraph ESP["ESP8266 D1 mini"]
        TINY["helianthus-tinyebus<br/>Go oracle + northbound bridge"]
    end

    subgraph BUS["eBUS Wire"]
        BOILER["Boiler BAI00 @ 0x08"]
        VRC["Controller VRC700 @ 0x15"]
    end

    ESP <-->|"ENH/ENS 9600 / 115200 baud"| PIC16F15356
    HAL <--|"UART RX byte forwarding (receive only)"| BUS
    BOILER --- VRC
```

### Layer Responsibilities

| Layer | Role | Implementation |
|---|---|---|
| **Application** | ISR dispatcher, mainline superloop, clock switch | `pic16f15356_app` |
| **Runtime** | Protocol FSM, ENH codec (receive path only), scan/status scaffolding, diagnostics | `runtime.c` |
| **HAL** | ISR byte latch into FIFOs, TMR0 tick management, UART baud rate switching | `pic16f15356_hal` |
| **Bootloader** | STX-framed protocol, host validation model, target backend profile | `picboot` |

## Protocol Layers

| Layer | Scope | Owner |
|---|---|---|
| Physical | eBUS transceiver, 2400 baud, differential signaling | External hardware |
| Data link | CRC-8, frame escaping (`ESC=0xA9` / `SYN=0xAA`), arbitration decisions | Host gateway (Go) |
| Adapter | ENH encoding (receive path only), SYN forwarding, scan windows, status emission | This firmware (PIC) |
| Application | Scan/status interpretation, INFO queries, feature negotiation | Host gateway (Go) |

## Memory Map

| Region | Address Range | Size | Content |
|---|---|---|---|
| Boot | `0x0000`--`0x03FF` | 1 KB | Bootloader image, reset vector, clock-switch helper |
| App | `0x0400`--`0x3FFF` | 15 KB | Application image, ISR dispatcher, runtime, HAL |
| EEPROM | 256 bytes | 256 B | Persistent configuration |
| RAM | `0x0000`--`0x07FF` | 2 KB (2048 bytes) | Runtime state, stack, FIFOs |

## Provisioning Model

Provisioning is loader-canonical. The firmware consumes the legacy config space
written by `ebuspicloader` and derives runtime state from it at boot:

- settings window `0x0000..0x0007`
- MUI window `0x0106..0x010D`
- derived cache for IP, MAC, arbitration delay, and variant policy

The runtime cache is derivative only. It is not a second persistent format.

The current combined static footprint (`picfw_runtime_t` + `picfw_pic16f15356_hal_t`) is tracked by `make check-all`. At the time of this review the host-side `sizeof` reports 1056 bytes. The 75% budget threshold is applied against the PIC16F15356's full 2048-byte RAM (i.e. 1536 bytes usable budget), giving 1056/2048 = 51.6% utilization.

## Determinism

The codebase is structured for bounded execution, but the deterministic guarantees are only as strong as the current host-side model. `make check-all` enforces the enabled static checks; hardware-specific ISR/delay checks remain optional and real UART/NVM timing is not yet proven on silicon.

### Why Determinism

The eBUS adapter firmware must behave as a transparent, jitter-free UART bridge. eBUS master-master arbitration is bit-level at 2400 baud: if the adapter introduces more than ~10 us of jitter in byte forwarding, it loses arbitration and corrupts the bus. There is no retry mechanism -- a missed window means dropped frames and broken heating control.

This constraint drives every architectural decision:

- **No recursion, no dynamic allocation, no VLAs** (R1, R2, R7) -- stack depth and RAM usage must be statically provable. On PIC16F15356 with 2 KB RAM and a 16-level hardware call stack, any unpredictable growth is fatal.
- **All loops bounded by constants** (R3) -- unbounded iteration produces unbounded execution time. Every loop has a compile-time-visible upper bound or a provably-decreasing guard.
- **No floating point** (R6) -- PIC16F has no FPU. Software float emulation is non-deterministic in cycle count and consumes ~1 KB of ROM.
- **Cyclomatic complexity < 10** (R8) -- high-CC functions have deep nesting and many execution paths, making WCET analysis intractable. The threshold ensures every function is small enough to reason about exhaustively. Monolithic dispatchers were replaced with `const` lookup tables (O(1) dispatch, constant WCET).
- **ISR WCET < 60 cycles** (R4/WCET) -- the ISR fires every 500 us (TMR0 period). At 8 MHz instruction clock, 60 cycles = 7.5 us -- well under the 500 us period and the 10 us jitter budget. ISR functions only latch bytes into ring buffer FIFOs; all protocol processing happens in the mainline superloop. This separation guarantees the ISR never blocks.
- **Call depth < 13** (STACK) -- PIC16F15356 has a 16-level hardware call stack (not software, not growable). 3 levels are reserved for the deepest ISR chain (`app_isr_host_rx -> isr_latch_host_rx -> byte_fifo_push`), leaving 13 for mainline. The deepest mainline chain (scan FSM retry path) uses exactly 13 -- zero margin. This is a frozen path: new function extractions here are prohibited.
- **Power-of-2 ring buffers with bitmask indexing** (R10) -- the PIC16F has no hardware divider. Modulo (`%`) on a non-power-of-2 value compiles to a software division routine (~30 cycles). Bitmask (`& (CAP - 1)`) is a single AND instruction (~1 cycle). For ISR-context FIFO push/pop, this 30x speedup is the difference between meeting and missing the WCET budget.
- **RAM budget < 75%** (RAM) -- the combined static footprint of `picfw_runtime_t` + `picfw_pic16f15356_hal_t` is tracked by a compiled C program using `sizeof` against the PIC16F15356's 2048-byte RAM. Host compiler alignment differs from XC8, but relative growth is tracked: if a struct grows 32 bytes on the host, it grew similarly on PIC. The 25% headroom covers the hardware call stack, local variables, and compiler temporaries.
- **Const dispatch enforcement** (CONST) -- function pointer arrays must be `const` (placed in ROM by XC8). Mutable function pointer dispatch is prohibited because it introduces runtime-dependent branching that defeats WCET analysis. The `const` qualifier is both a correctness guarantee (table cannot be corrupted) and a ROM/RAM optimization.

### Self-Testing

Every determinism rule has an automated check script (pure Python 3, zero pip dependencies) that produces a `PASS`/`FAIL` verdict. The checks are validated in both directions:

- **Good code must pass** -- the enabled checks are run against `runtime/src` and `bootloader/src`.
- **Bad code must fail** -- synthetic violations in `tests/fixtures/bad_example.c` trigger each check (10 negative tests).
- **Total: 31 self-tests** via `bash tests/test_checks.sh`, ensuring the checks themselves do not silently regress.

The `NOLINT(determinism)` comment suppression mechanism allows intentional exceptions (e.g., a loop with a provably-constant bound that the checker cannot statically verify), documented inline at the suppression site.

### Rule Summary

| ID | Rule | Threshold | Enforcement |
|----|------|-----------|-------------|
| R1 | No recursion (direct or mutual) | -- | Call graph cycle detection |
| R2 | No malloc/calloc/realloc/free | -- | Pattern scan |
| R3 | All loops bounded by constant | -- | AST pattern analysis |
| R4 | ISR-context WCET | < 60 cycles | Naming pattern + source heuristic |
| R5 | No `__delay` in critical paths | -- | Skipped (HAL simulation model) |
| R6 | No float/double/math.h | -- | Pattern scan |
| R7 | No variable-length arrays | -- | Pattern scan (with R2) |
| R8 | Cyclomatic complexity | < 10 per function (peak: 9) | Decision point counting |
| R9 | Hardware timers for temporal decisions | -- | Manual code review |
| R10 | Ring buffers power-of-2 + bitmask | -- | Buffer size + indexing scan |
| STACK | Call depth limit | < 13 of 16 HW levels | Call graph DFS |
| GUARD | Header include guards | -- | Pattern scan |
| RAM | Static struct footprint | < 75% of 2 KB (1056 / 2048 = 51.6%) | Host sizeof budget check |
| WCET | ISR-context functions | < 60 cycles (peak: 51) | Source heuristic (`*_isr_*`) |
| CONST | Function pointer arrays | Must be `const` | Qualifier scan |

### Frozen Call Path

The deepest mainline call chain is exactly 13 levels, running through the scan FSM retry path:

```
app_mainline_service -> mainline_service -> runtime_step ->
  service_periodic_status -> try_emit_variant -> emit_periodic_variant ->
    continue_scan_window -> continue_scan_fsm -> continue_fsm_phase_retry ->
      protocol_state_dispatch -> dispatch_flags_retry ->
        set_protocol_state_ready -> set_protocol_state
```

Budget: 13 mainline + 3 ISR (`app_isr_host_rx -> isr_latch_host_rx -> byte_fifo_push`) = 16 hardware stack levels. Zero margin. New function extractions on this path are prohibited.

### Dispatch Table Architecture

The bootloader uses `const` dispatch tables instead of large `switch/case` cascades:

- `PICBOOT_COMMAND_HANDLERS[11]` -- `static const` function pointer array with O(1) command dispatch. Protected by `_Static_assert` on array size and a NULL guard at dispatch time.
- `PICBOOT_VALIDATION_RULES[11]` -- `static const` struct array with per-command validation rules (`min_data_len`, `max_data_len`, `needs_even`). Protected by `_Static_assert`.

This pattern is explicitly permitted by R8 (DETERMINISM.md). Mutable function pointer dispatch remains prohibited.

## Provenance

All register values and code paths were recovered from Ghidra decompilation of the original production `combined.hex` image (76 functions, 10K decompiled lines). The firmware was then re-implemented as a clean-room C codebase and cross-validated against a Go reference oracle (`helianthus-tinyebus`) for the currently modeled northbound behavior. That does not by itself prove silicon-complete feature parity.

## Original Firmware Issues

Ghidra decompilation of the production `combined.hex` revealed systemic issues in the original PIC firmware. These findings motivated the clean-room reimplementation and the determinism rules enforced by this project. Issues are classified by severity: P0 (critical, data loss or corruption), P1 (significant, degraded operation), P2 (latent, long-term instability).

### P0 -- Critical

**FAILED-to-START race bypasses minimum inter-scan delay.** When a new START command arrives before a FAILED response is fully consumed, one code path transitions directly to READY, bypassing the mandatory 0x3C (60 ms) minimum delay. The scan engine then samples the transceiver in a transient window, producing false "no signal" reports. Under START flooding, this cascades into lost SYNs and violent degradation. *Addressed by: bounded deadline enforcement in `normalize_scan_delay()` with `SCAN_MIN_DELAY` floor clamping.*

**ISR and mainline reentrancy on shared FSMs.** The low-priority ISR enters protocol and scan logic directly (`continue_scan_fsm`, flush path) instead of only latching bytes into FIFOs. Mainline simultaneously processes the same state and cursors. The ISR observes partially updated state and makes decisions on incoherent data -- classic torn-state reentrancy. *Addressed by: strict ISR/mainline separation. ISR only latches into ring buffer FIFOs (R4/WCET < 60 cycles). All protocol processing runs in the mainline superloop.*

**Fail-open on invalid protocol codes.** Protocol codes that should be rejected are routed to READY instead of a reject/fault path. A corrupted or malicious response can artificially validate the FSM. *Addressed by: explicit state validation inlined into `set_protocol_state()` (switch on valid enum values, default rejects). XOR-encoded diagnostic return codes on every rejection path.*

**Deadline comparison is wrap-unsafe.** Absolute tick values are compared byte-by-byte (lexicographic) rather than modularly. On counter wrap-around, a deadline can appear expired too early or not at all. *Addressed by: `picfw_deadline_reached_u32()` using modular subtraction (`(int32_t)(now - deadline) >= 0`), which is wrap-safe for intervals < 2^31.*

### P1 -- Significant

**Incomplete state reset in `set_protocol_state_pending()`.** Only a subset of protocol state is reset. Saved deadlines, merged windows, and latches remain stale, explaining paths that reuse old timing state after a rapid FAILED-to-START transition. *Addressed by: `picfw_runtime_seed_scan_state()` performs a full reset of all scan-related fields on INIT.*

**Backoff timing collapses under noise.** On some deadline expirations, the firmware halves timing windows instead of stabilizing, becoming more aggressive under stress. *Addressed by: `post_merge_validate()` enforces floor and ceiling on all scan window parameters. Window limit, delay, and merged values are clamped to validated ranges on every merge cycle.*

**"No signal" detection lacks debounce.** A single LOW sample on the signal-detect pin immediately triggers a "no signal" path, producing false negatives during frame transitions. *Addressed by: the reimplementation delegates signal detection entirely to the Go gateway, which has proper debounce and hysteresis.*

**Self-DoS via busy-wait loops.** `service_timed_loop()` and related paths use spin loops. Under command flooding, CPU time is consumed by polling instead of UART servicing, causing the firmware to lose determinism at peak stress. *Addressed by: R3 (all loops bounded by constants), no spin-wait patterns. The mainline superloop processes a fixed event budget per step (`STEP_EVENT_BUDGET = 8`).*

**Critical sections too narrow and inconsistent.** Interrupt masking covers small fragments, not full atomic updates of shared state. Shared state is mutated outside the protected window. *Addressed by: eliminating shared mutable state between ISR and mainline. ISR writes to FIFO tail (atomic push); mainline reads from FIFO head (atomic pop). No shared cursor or state variable.*

**Non-atomic multi-byte updates.** 16/32-bit values are written and read byte-by-byte on the 8-bit MCU without coherent protection, allowing readers to observe mixed old/new bytes. *Addressed by: all multi-byte deadline/timestamp writes happen in mainline only (never ISR). The ISR only increments single-byte counters and pushes single bytes to FIFOs.*

**Buffer cursors lack hard bounds.** Some cursors grow with only soft thresholds, risking wrap or RAM overwrite if producers outrun consumers. *Addressed by: R10 (power-of-2 ring buffers with bitmask indexing). All buffer capacities have `_Static_assert` enforcement. Overflow increments a diagnostic counter and transitions to DEGRADED -- no silent corruption.*

**Flush path is reentrant.** The message output path runs in both ISR and mainline with incomplete serialization, causing frame interleaving and dropped output. *Addressed by: the HAL now owns a bounded staged TX queue. Mainline fills `host_tx_stage`; TX-ready service may consume exactly one staged byte per event. On simulation builds, `hal_drain_host_tx()` exposes only bytes already transmitted into the simulation outbox, never merely staged bytes. The silicon profile keeps the same public HAL API but has no outbox observer.*

**Weak descriptor validation.** The firmware accepts "plausible" descriptor blocks and derives seeds, masks, and deadlines from them. A malicious peer can inject values that pass superficial validation but poison the scheduler. *Addressed by: `post_merge_validate()` clamps all derived values to validated ranges. `SCAN_WINDOW_LIMIT_FLOOR` (240 ms), `SCAN_DELAY_THRESHOLD` (120 ms), and `SCAN_MERGED_THRESHOLD` (210 ms) enforce hard bounds on descriptor-derived timing.*

### P2 -- Latent

**State leak (sticky latches).** There is no dynamic allocation (`malloc/free`), but sticky flags/latches are set and not cleared on all paths, causing cumulative degradation over long uptime. *Addressed by: `picfw_runtime_init()` performs a full zero-init of all runtime state. INIT command triggers a complete re-initialization cycle.*

**Multiple READY encodings.** Several `state + flags` combinations represent effectively the same READY condition, creating "weird machine" behavior where logically equivalent transitions have different side effects. *Addressed by: the reimplementation uses a single canonical `set_protocol_state(READY, FLAGS_IDLE)` path. State validation rejects any state value not in the defined enum.*

**Weak recovery after malicious input.** Parsers and FSMs do not perform hard resets after errors or partial sequences, allowing residual state to poison subsequent frames. *Addressed by: the ENH parser resets to IDLE after every complete frame and on every error (conservative reset policy). The scan FSM transitions to DEGRADED on any unrecoverable error, requiring a full INIT to resume.*

### Assessment

The original firmware was not designed for strict real-time determinism. The dominant failure modes are not memory leaks but state leaks, ISR/mainline races, wrap-unsafe comparisons, fail-open logic, busy-wait self-DoS, and cursor drift. Under normal traffic it may appear acceptable; under flood, jitter, line noise, or long uptime, it becomes fragile and amplifies its own failures. Every determinism rule in this project traces back to at least one of these findings.

## Related Firmware Documents

- [State Machines](pic16f15356-fsm.md) -- protocol FSM, scan phase FSM, ENH parser, startup states
- [Timing Model](pic16f15356-timing.md) -- clock, TMR0, UART baud rates, scan deadlines
- [Register Configuration](pic16f15356-registers.md) -- oscillator, timer, EUSART, interrupt, descriptor addresses
