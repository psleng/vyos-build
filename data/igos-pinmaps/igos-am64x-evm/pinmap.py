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
    #   <MODEM>_SIM_SELECT_1N_OR_2  (0 = slot 1, 1 = slot 2; embedded
    #                                ``1N`` = slot 1 is the line-low value)
    #   <MODEM>_SIM_DETECT_*  (input family, one per slot)
    "MODEM0_SIM_DETECT_1":        _P(bank=0, line=49, dir="in",  bias="pull-up",   group="cell"),
    "MODEM0_SIM_DETECT_0":        _P(bank=0, line=52, dir="in",  bias="pull-up",   group="cell"),
    "MODEM0_SIM_SELECT_1N_OR_2":  _P(bank=0, line=60, dir="out", bias="pull-down", default=0, group="cell"),
    "MODEM0_SHUTDOWN_N":          _P(bank=0, line=56, dir="out", bias="pull-up",   default=1, group="cell"),
    "MODEM0_UNCOND_RESET":        _P(bank=0, line=59, dir="out", bias="pull-down", default=0, group="cell"),
    "MODEM0_FLIGHT_MODE":         _P(bank=0, line=85, dir="out", bias="pull-down", default=0, group="cell"),
    "MODEM0_GNSS_DISABLE":        _P(bank=0, line=86, dir="out", bias="pull-down", default=0, group="cell"),
    "MODEM0_PASS_THROUGH_SELECT": _P(bank=0, line=37, dir="out", bias="pull-down", default=0, group="cell"),

    # ---------------- WIFI0 ----------------
    # Per-instance naming (WIFI<N>_…) mirrors the modem convention so
    # additional radios drop in cleanly as WIFI1_*, WIFI2_*, …. ``PD``
    # is power-down; the ``_N`` suffix is the standard hardware
    # shorthand for ACTIVE-LOW: physical line high = radio powered,
    # low = held in power-down. vyos.hardware passes physical levels
    # through (no software inversion), matching what a scope would show.
    "WIFI0_PD_N":        _P(bank=0, line=14, dir="out", bias="pull-up",   default=1, group="wifi0"),

    # ---------------- CONTROL ----------------
    "VPP_LDO_EN":        _P(bank=0, line=33, dir="out", bias="pull-down", default=0, group="control"),
    "VSEL_SD_SWITCH":    _P(bank=0, line=45, dir="out", bias="pull-up",   default=1, group="control"),
    "PMIC_STBY":         _P(bank=0, line=51, dir="out", bias="pull-up",   default=1, group="control"),

    # ---------------- BUTTON / INPUT ----------------
    # ``_N`` = active-low at the silicon. *_VALID_N inputs read 0 when
    # the corresponding rail is present (line pulled low by the
    # monitor), 1 when absent.
    "PUSH_KEY":          _P(bank=1, line=36, dir="in",  bias="pull-up",   group="input"),
    "DC_VALID_N":        _P(bank=1, line=73, dir="in",  bias="pull-down", group="input"),
    "POE_VALID_N":       _P(bank=1, line=74, dir="in",  bias="pull-up",   group="input"),

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

# Pinned ethernet interfaces
# Link files to pin interfaces to physical ports are generated from teh following definitions
# matching properties are defined by the 'match' key, matching properties are required
# link options in the the generated .link files are statically infered so we dont accedentally link incorrectly
# IGOS_ETH_PORT can be constructed by doing the following: 
#
# Run as one command:
"""
printf '%-6s  %-17s  %s\n' IFACE MAC IGOS_ETH_PORT; \
printf '%-6s  %-17s  %s\n' ----- --- -------------; \
for sys in /sys/class/net/eth*; do \
  [ -d "$sys" ] || continue; \
  ifname=${sys##*/}; \
  parent=$(readlink "$sys" | sed -e 's|^\.\./\.\.||' -e 's|/net/[^/]*$||'); \
  mac=$(cat "$sys/address"); \
  port=; pd="$sys/device/of_node/ethernet-ports"; \
  if [ -d "$pd" ]; then \
    for p in "$pd"/port@*; do \
      [ -d "$p" ] || continue; \
      bytes=$(od -An -tx1 -N6 "$p/local-mac-address" 2>/dev/null | tr -d ' '); \
      pmac=$(printf '%s' "$bytes" | sed 's/../&:/g;s/:$//'); \
      [ "$pmac" = "$mac" ] && { port=$((0x${p##*port@})); break; }; \
    done; \
  fi; \
  [ -n "$port" ] || port=$(cat "$sys/dev_port" 2>/dev/null || echo 0); \
  printf '%-6s  %-17s  %s#%s\n' "$ifname" "$mac" "$parent" "$port"; \
done
"""
#
# If dev port (the number following #) is 0 verify with the following 
#
"""
cat /sys/class/net/eth0/dev_port
"""
#
# If the previous command resulted in a number other than 0 use that as dev port (the number following the #)

ETH_INTERFACES = {
    "eth0": {
        "match": {
            "Property": "IGOS_ETH_PORT=/devices/platform/bus@f4000/8000000.ethernet#1",
            "Type": "ether",
        }
    },
    "eth1": {
        "match": {
            "Property": "IGOS_ETH_PORT=/devices/platform/bus@f4000/8000000.ethernet#2",
            "Type": "ether",
        }
    }
}

WWAN_INTERFACES = {
    "wwan0": {
        "match": {
            "Property": "ID_MM_PHYSDEV_UID=modem0",
            "Driver": "qmi_wwan",
            "Type": "wwan",
        }
    }
}
