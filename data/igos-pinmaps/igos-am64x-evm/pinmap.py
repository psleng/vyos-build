# igOS AM64x base ("all") pin map.
#
# Source of truth lives in vyos-build so that pin numbers are version-
# controlled alongside the hardware flavor that consumes them. At image
# build time, build-vyos-image copies this file into the chroot at:
#
#   /usr/lib/python3/dist-packages/vyos/hardware/pinmap.py
#
# The board-agnostic vyos.hardware package (Pin dataclass, libgpiod
# backend, semantic helpers) is shipped by the main vyos-1x package and
# imports this overlay at runtime.
#
# To add a board variant: copy this file to
#   data/igos-pinmaps/igos-am64x-<variant>/pinmap.py
# adjust VARIANT and the pin numbers, and create a matching flavor TOML
# in data/build-flavors/igos-am64x-<variant>.toml pointing at it.

from vyos.hardware.base import Pin as _P

# TODO: replace pin numbers below with TI AM64x EVM (TMDS64EVM) values.
VARIANT = "am64x_evm"

PINS = {
    # ---------------- MODEM0 & SIM ----------------
    # Naming follows vyos.hardware modem-discovery convention. The ``_N``
    # suffix is the standard hardware shorthand for ACTIVE-LOW at the
    # silicon — values written/read via vyos.hardware.api are the
    # physical line level, matching what a scope would show:
    #   <MODEM>_UNCOND_RESET  (required)  -> defines modem name
    #   <MODEM>_SHUTDOWN_N    (power; 1 = line high = run, 0 = shutdown)
    #   <MODEM>_SIM_SELECT    (0 = slot 1, 1 = slot 2)
    #   <MODEM>_SIM_DETECT_*  (input family, one per slot)
    "MODEM0_SIM_DETECT_1":  _P(bank=0, line=49, dir="in",  bias="pull-up",   group="cell"),
    "MODEM0_SIM_DETECT_0":  _P(bank=0, line=52, dir="in",  bias="pull-up",   group="cell"),
    "MODEM0_SIM_SELECT":    _P(bank=0, line=60, dir="out", bias="pull-down", default=0, group="cell"),
    "MODEM0_SHUTDOWN_N":    _P(bank=0, line=56, dir="out", bias="pull-up",   default=1, group="cell"),
    "MODEM0_UNCOND_RESET":  _P(bank=0, line=59, dir="out", bias="pull-down", default=0, group="cell"),
    "MODEM0_FLIGHT_MODE":   _P(bank=0, line=85, dir="out", bias="pull-down", default=0, group="cell"),
    "MODEM0_GNSS_DISABLE":  _P(bank=0, line=86, dir="out", bias="pull-down", default=0, group="cell"),

    # ---------------- CONTROL ----------------
    "WIFI_PDN_GPIO":     _P(bank=0, line=14, dir="out", bias="pull-up",   default=1, group="control"),
    "VPP_LDO_EN":        _P(bank=0, line=33, dir="out", bias="pull-down", default=0, group="control"),
    "PATH_THROUGH_SEL":  _P(bank=0, line=37, dir="out", bias="pull-down", default=0, group="control"),
    "VSEL_SD_SWITCH":    _P(bank=0, line=45, dir="out", bias="pull-up",   default=1, group="control"),
    "PMIC_STBY":         _P(bank=0, line=51, dir="out", bias="pull-up",   default=1, group="control"),

    # ---------------- BUTTON / INPUT ----------------
    "PUSH_KEY":          _P(bank=1, line=36, dir="in",  bias="pull-up",   group="input"),
    "DC_VALIDN":         _P(bank=1, line=73, dir="in",  bias="pull-down", group="input"),
    "POE_VALIDN":        _P(bank=1, line=74, dir="in",  bias="pull-up",   group="input"),

    # ---------------- UARTC0 (THVD4431) ----------------
    "UARTC0_MODE0":      _P(bank=1, line=46, dir="out", bias="pull-up",   default=1, group="uartc0"),
    "UARTC0_MODE1":      _P(bank=1, line=42, dir="out", bias="pull-up",   default=0, group="uartc0"),
    "UARTC0_MODE2":      _P(bank=1, line=43, dir="out", bias="pull-up",   default=0, group="uartc0"),
    "UARTC0_TERM_TX":    _P(bank=1, line=44, dir="out", bias="pull-down", default=0, group="uartc0"),
    "UARTC0_TERM_RX":    _P(bank=1, line=45, dir="out", bias="pull-down", default=0, group="uartc0"),
    "UARTC0_SLR":        _P(bank=1, line=49, dir="out", bias="pull-up",   default=1, group="uartc0"),
    "UARTC0_SHUT_N":     _P(bank=1, line=50, dir="out", bias="pull-up",   default=0, group="uartc0"),

    # ---------------- UARTC2 (THVD4431) ----------------
    "UARTC2_MODE0":      _P(bank=0, line=40, dir="out", bias="pull-up",   default=1, group="uartc2"),
    "UARTC2_MODE1":      _P(bank=0, line=44, dir="out", bias="pull-up",   default=0, group="uartc2"),
    "UARTC2_MODE2":      _P(bank=0, line=32, dir="out", bias="pull-up",   default=0, group="uartc2"),
    "UARTC2_TERM_TX":    _P(bank=0, line=41, dir="out", bias="pull-down", default=0, group="uartc2"),
    "UARTC2_TERM_RX":    _P(bank=0, line=42, dir="out", bias="pull-down", default=0, group="uartc2"),
    "UARTC2_SLR":        _P(bank=0, line=35, dir="out", bias="pull-up",   default=1, group="uartc2"),
    "UARTC2_SHUT_N":     _P(bank=0, line=36, dir="out", bias="pull-up",   default=0, group="uartc2"),

    # ---------------- UARTC4 (THVD4431) ----------------
    "UARTC4_MODE0":      _P(bank=1, line=5,  dir="out", bias="pull-up",   default=1, group="uartc4"),
    "UARTC4_MODE1":      _P(bank=1, line=1,  dir="out", bias="pull-up",   default=0, group="uartc4"),
    "UARTC4_MODE2":      _P(bank=1, line=26, dir="out", bias="pull-up",   default=0, group="uartc4"),
    "UARTC4_TERM_TX":    _P(bank=1, line=41, dir="out", bias="pull-down", default=0, group="uartc4"),
    "UARTC4_TERM_RX":    _P(bank=1, line=40, dir="out", bias="pull-down", default=0, group="uartc4"),
    "UARTC4_SLR":        _P(bank=1, line=13, dir="out", bias="pull-up",   default=1, group="uartc4"),
    "UARTC4_SHUT_N":     _P(bank=1, line=33, dir="out", bias="pull-up",   default=0, group="uartc4"),

    # ---------------- UARTC5 (THVD4431) ----------------
    "UARTC5_MODE0":      _P(bank=1, line=15, dir="out", bias="pull-up",   default=1, group="uartc5"),
    "UARTC5_MODE1":      _P(bank=1, line=35, dir="out", bias="pull-up",   default=0, group="uartc5"),
    "UARTC5_MODE2":      _P(bank=1, line=37, dir="out", bias="pull-up",   default=0, group="uartc5"),
    "UARTC5_TERM_TX":    _P(bank=1, line=14, dir="out", bias="pull-down", default=0, group="uartc5"),
    "UARTC5_TERM_RX":    _P(bank=1, line=16, dir="out", bias="pull-down", default=0, group="uartc5"),
    "UARTC5_SLR":        _P(bank=1, line=30, dir="out", bias="pull-up",   default=1, group="uartc5"),
    "UARTC5_SHUT_N":     _P(bank=1, line=9,  dir="out", bias="pull-up",   default=0, group="uartc5"),
}

# Per-port application-facing identity. See igos-am64x-all/pinmap.py for the
# full explanation; the EVM uses the same AM64x silicon and the same SoC UART
# instance ↔ kernel ttyS<N> mapping, derived from k3-am64-main.dtsi:
#   MAIN_UART0 = 0x02800000  (console, ttyS0 — not exposed)
#   MAIN_UART1 = 0x02810000  (ttyS1, UARTC0)
#   MAIN_UART2 = 0x02820000  (ttyS2, UARTC2)
#   MAIN_UART4 = 0x02840000  (ttyS3, UARTC4)
#   MAIN_UART5 = 0x02850000  (ttyS4, UARTC5)
# ``dt_node`` is verified at startup by ``hw.verify_serial_bindings()``.
SERIAL_PORTS = {
    "UARTC0": {"tty": "/dev/ttyS1", "label": "Serial 1",
               "dt_node": "/bus@f4000/serial@2810000"},
    "UARTC2": {"tty": "/dev/ttyS2", "label": "Serial 2",
               "dt_node": "/bus@f4000/serial@2820000"},
    "UARTC4": {"tty": "/dev/ttyS3", "label": "Serial 3",
               "dt_node": "/bus@f4000/serial@2840000"},
    "UARTC5": {"tty": "/dev/ttyS4", "label": "Serial 4",
               "dt_node": "/bus@f4000/serial@2850000"},
}
