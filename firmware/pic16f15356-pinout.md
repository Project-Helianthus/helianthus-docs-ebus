# PIC16F15356 Pin Configuration

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. Helianthus documentation uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

This document describes the complete pin assignment, peripheral mapping, and hardware configuration of the PIC16F15356 as used on the Helianthus eBUS adapter v3.x board (IC5, 28-pin SOIC).

See also:

- [`firmware/pic16f15356-overview.md`](pic16f15356-overview.md) for the firmware architecture and scope.
- [`firmware/pic16f15356-timing.md`](pic16f15356-timing.md) for clock, timer, and UART baud rate configuration.
- [`firmware/pic16f15356-registers.md`](pic16f15356-registers.md) for SFR values recovered from the original binary.

## Pin Map

Complete 28-pin SOIC assignment from the v3 schematic (IC5):

| Pin | Port | Function | Direction | Notes |
|---|---|---|---|---|
| 1 | VPP/MCLR/RE3 | Reset | Input | <!-- legacy-role-mapping:begin -->Master clear<!-- legacy-role-mapping:end --> (active low) |
| 2 | RA0 | GPIO | Input | J12 strap (variant decode) |
| 3 | RA1 | GPIO | Input | J12 strap (variant decode) |
| 4 | RA2 | C1IN0+ | Input | Comparator 1 input (analog) |
| 5 | RA3 | C1OUT | Output | Comparator 1 output |
| 6 | RA4 | GPIO | Input | J12 strap (protocol select) |
| 7 | RA5 | GPIO | Input | J12 strap (speed select) |
| 8 | VSS | Ground | -- | |
| 9 | RA7 | -- | -- | Not used (oscillator pin, HFINTOSC mode) |
| 10 | RA6 | -- | -- | Not used (oscillator pin, HFINTOSC mode) |
| 11 | RC0 | RX2 | Input | EUSART2 RX (host from ESP) |
| 12 | RC1 | TX2 | Output | EUSART2 TX (host to ESP) |
| 13 | RC2 | SCK2 | Output | SPI2 clock |
| 14 | RC3 | SDI2 | Input | SPI2 data in |
| 15 | RC4 | SDO2 | Output | SPI2 data out |
| 16 | RC5 | SEL2 | Output | SPI2 chip select |
| 17 | RC6 | GPIO | Output | LED2 in the current firmware model |
| 18 | RC7 | -- | I/O | Unmodeled / reserved in the current firmware tree |
| 19 | VSS | Ground | -- | |
| 20 | VDD | Power | -- | 3.3 V |
| 21 | RB0 | GPIO | Input | WiFi readiness gate in the current firmware tree |
| 22 | RB1 | INT | Input | Signal detect (eBUS transceiver presence, external interrupt) |
| 23 | RB2 | RX1 | Input | EUSART1 RX (bus from eBUS transceiver) |
| 24 | RB3 | TX1 | Output | EUSART1 TX (bus to eBUS transceiver) |
| 25 | RB4 | SCK1 | Output | SPI1 clock (W5500 Ethernet) |
| 26 | RB5 | SEL1 | Output | SPI1 chip select (W5500) |
| 27 | RB6 | SPCLK / PGC | I/O | SPI1 secondary clock, also sampled for J11 boot entry |
| 28 | RB7 | SPDAT / PGD | I/O | SPI1 data, also sampled for J11 boot entry |

Pin numbering follows the PIC16(L)F15356 28-pin PDIP/SOIC/SSOP package diagram from the Microchip datasheet (DS40001866B, page 5). Pins 9 (RA7) and 10 (RA6) are the external oscillator pins; they are unused because the firmware selects HFINTOSC as the clock source (OSCCON1 = 0x60, FEXTOSC = OFF).

## EUSART Configuration

Two independent EUSARTs provide the bus-side and host-side serial channels.

### EUSART1 (Bus Model)

| Parameter | Value |
|---|---|
| RX pin | RB2 (pin 23) |
| TX pin | RB3 (pin 24) |
| Connected to | eBUS transceiver IC |
| Bus-side baud | 2400 baud in the current host model |
| PPS routing | `RX1PPS` <- RB2, `RB3PPS` -> TX1 |

### EUSART2 (Host)

| Parameter | Value |
|---|---|
| RX pin | RC0 (pin 11) |
| TX pin | RC1 (pin 12) |
| Connected to | ESP8266 / USB-UART / RPi header |
| Host-side baud | 9600 or 115200 baud (switchable via J12 speed strap) |
| PPS routing | `RX2PPS` <- RC0, `RC1PPS` -> TX2 |

### Register Settings

Control bits match, but the current firmware model uses different divisors for bus and host roles:

| Register | Value | Meaning |
|---|---|---|
| BAUDxCON | `0x08` | BRG16 = 1 (16-bit baud rate generator) |
| RCxSTA | `0x90` | SPEN = 1, CREN = 1 (serial port enabled, continuous receive) |
| TXxSTA | `0x24` | TXEN = 1, BRGH = 1 (transmit enabled, high-speed baud) |

The current tree models `SP1BRG = 0x0D04` for the bus side and `SP2BRG = 0x0340/0x0044` for the host side. Earlier docs that claimed the two UARTs mirror each other were incorrect for the current codebase.

## SPI Buses

### SPI1 (Ethernet -- RB4-RB7)

| Signal | Pin | Port |
|---|---|---|
| SCK1 | 25 | RB4 |
| SEL1 (CS) | 26 | RB5 |
| SPCLK | 27 | RB6 |
| SPDAT | 28 | RB7 |

Connected to the W5500 Ethernet module (USR-ES1). This bus is **only active in the Ethernet variant** (J12 variant strap set to Ethernet). In RPi/USB variants these pins are unused.

### SPI2 (Secondary -- RC2-RC5)

| Signal | Pin | Port |
|---|---|---|
| SCK2 | 13 | RC2 |
| SDI2 | 14 | RC3 |
| SDO2 | 15 | RC4 |
| SEL2 (CS) | 16 | RC5 |

Secondary SPI bus. Active for expansion peripherals depending on board variant.

## Signal Detect

| Parameter | Value |
|---|---|
| Pin | RB1 (pin 22) |
| Interrupt | INT (external interrupt) |
| Pull-up | Weak pull-up enabled (`WPUB` bit 1) |
| Polarity | Active-high: high = signal present, low = no signal |

RB1/INT is connected to the signal-detect output of the eBUS transceiver. It indicates whether the transceiver has detected a valid eBUS signal on the wire.

**Original firmware behavior:** Sampled single-shot during startup. This was a P1-class bug -- no debounce, no periodic re-check. A transient glitch at power-on could latch an incorrect signal-detect state for the entire session.

**Current tree:** The HAL samples RB1 into `runtime->bus_busy`, but the periodic snapshot frame does not currently export a dedicated raw RB1 field. Any consumer that needs raw signal-detect semantics must treat this as not yet implemented.

## LEDs

The current firmware tree implements exactly one PIC-driven LED state machine:

| LED | Color | Function |
|---|---|---|
| LED2 | Blue | Firmware status / info (fade, blink patterns) |

LED2 is currently modeled on RC6. The repo does not implement separate PIC-side state machines for LED1/LED3/LED4.

## J12 AUX Strap Configuration

The J12 header is an 8-pin auxiliary connector that configures the firmware variant, protocol mode, and serial speed at boot. Strap values are read once during initialization and remain fixed for the session.

| J12 Pin | PIC Pin | Function | Open (pull-up) | Grounded |
|---|---|---|---|---|
| 1 | VDD | Power | -- | -- |
| 2 | RA4 | Protocol | Enhanced (ebusd) | Standard / raw mode requested |
| 3 | GND | Ground | -- | -- |
| 4 | RB0 | WIFI-Check | Wemos not ready | Wemos ready signal asserted |
| 5 | RA0/RA1 | Variant | RPi/USB | Ethernet (to GND) or WIFI (to Pin 4) |
| 6 | GND | Ground | -- | -- |
| 7 | RA5 | Speed | Normal-speed host UART | High-speed host UART |
| 8 | -- | Reset | -- | Pulse low to reset |

### Variant Decode Logic

The RA0/RA1 combination selects the hardware variant:

| RA1 | RA0 | Variant | Host Interface |
|---|---|---|---|
| 1 | 1 | RPi / USB | EUSART2 at 9600 or 115200 baud |
| 0 | 0 | Ethernet | SPI1 to W5500 (USR-ES1) |
| 0 | 1 | WIFI | ESP8266 via EUSART2 |

### Protocol Select (RA4)

| RA4 | Mode | Description |
|---|---|---|
| 1 (open) | Enhanced | ENH/ENS encoding between PIC and host (ebusd-compatible) |
| 0 (grounded) | Standard | Requested raw mode; currently decoded but not implemented in the runtime |

### Speed Select (RA5)

| RA5 | Host Baud Rate |
|---|---|
| 1 (open) | Normal speed (9600 baud) |
| 0 (grounded) | High speed (115200 baud) |

## ISR Dispatcher

The documentation recovered from the legacy binary describes a fixed-priority dispatcher. The current firmware tree exposes separate ISR entry points. Host TX now uses a staged HAL queue plus one-byte TX-ready service; the simulation profile appends transmitted bytes to an outbox, while the silicon profile currently remains a compile-only register-mirror scaffold rather than a proven XC8 TXREG binding.

| Priority | Flag | PIE/PIR | Handler | Description |
|---|---|---|---|---|
| 1 | TMR0IF | PIE0/PIR0 | isr_latch_tmr0 | 500 us period, drives all firmware timing |
| 2 | RC1IF | PIE3/PIR3 | isr_latch_bus_rx | Bus byte received from eBUS transceiver |
| 3 | Host RX | variant-dependent | isr_latch_host_rx | Host byte received; exact PIE/PIR pair depends on the active host peripheral (EUSART2 or SPI) and has not been fully recovered from the binary |

### Original Firmware Dispatch

The original firmware used **mutable function pointers** stored in RAM (`DAT_DATA_005b`, `DAT_DATA_0059`, `DAT_DATA_0057`, `DAT_DATA_0055`) for the four EUSART handlers. The ISR performed an indirect call through these pointers, allowing the handler targets to be changed at runtime. This pattern was a source of non-determinism -- a malformed state transition could redirect the ISR to an unintended handler.

### Reimplementation Dispatch

The reimplementation uses **direct static function calls** for all ISR handlers. No function pointers are used in the ISR path. This satisfies DETERMINISM.md rule R8 (no indirect calls in ISR context) and eliminates the class of bugs where stale or corrupted pointers cause ISR misdispatch.

## GPIO Register Defaults

Initial register values derived from the schematic pin assignment. In the current tree they are applied from `picfw_pic16f15356_hal_runtime_init()` after oscillator / timer setup and after early strap sampling for J11 and J12.

### TRISA/TRISB/TRISC (Data Direction)

`1` = input, `0` = output.

| Register | Value | Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0 |
|---|---|---|---|---|---|---|---|---|---|
| TRISA | `0x37` | 0 | 0 | 1 (RA5 in) | 1 (RA4 in) | 0 | 1 (RA2 in) | 1 (RA1 in) | 1 (RA0 in) |
| TRISB | `0x07` | 0 | 0 | 0 | 0 | 0 | 1 (RB2 in) | 1 (RB1 in) | 1 (RB0 in) |
| TRISC | `0x09` | 0 | 0 | 0 | 0 | 1 (RC3 in) | 0 | 0 | 1 (RC0 in) |

### ANSELA/ANSELB/ANSELC (Analog Select)

`1` = analog, `0` = digital.

| Register | Value | Notes |
|---|---|---|
| ANSELA | `0x04` | Only RA2 (C1IN0+) is analog; all other PORTA pins are digital |
| ANSELB | `0x00` | All PORTB pins are digital |
| ANSELC | `0x00` | All PORTC pins are digital |

### WPUB (Weak Pull-Up Enable)

| Register | Value | Notes |
|---|---|---|
| WPUB | `0x02` | Bit 1 set: weak pull-up on RB1 (signal detect INT pin) |

WPUA is not explicitly configured (J12 straps use external pull-ups on the header).

## Cross-References

- [Firmware Overview](pic16f15356-overview.md) -- architecture, scope, original firmware issues
- [Timing Model](pic16f15356-timing.md) -- clock switch, TMR0 period, UART baud rate derivation
- [Register Configuration](pic16f15356-registers.md) -- full SFR catalog from Ghidra decompilation
- [State Machines](pic16f15356-fsm.md) -- protocol FSM states, scan phases, ENH parser
