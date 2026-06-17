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

VARIANT = "am64x_all"

PINS = {
    # ---------------- MODEM0 & SIM ----------------
    # Naming follows vyos.hardware modem-discovery convention:
    #   <MODEM>_UNCOND_RESET  (required)  -> defines modem name
    #   <MODEM>_SHUTDOWN_N    (power, active-low: 1 = run)
    #   <MODEM>_SIM_SELECT_1N_OR_2  (0 = slot 1, 1 = slot 2; embedded
    #                                ``1N`` = slot 1 is the line-low value)
    #   <MODEM>_SIM_DETECT_*  (input family, one per slot)
    #"MODEM0_SIM_DETECT_1":  _P(bank=0, line=49, dir="in",  bias="pull-up",   group="cell"),
    #"MODEM0_SIM_DETECT_0":  _P(bank=0, line=52, dir="in",  bias="pull-up",   group="cell"),
    #"MODEM0_SIM_SELECT_1N_OR_2":  _P(bank=0, line=60, dir="out", bias="pull-down", default=0, group="cell"),
    "MODEM0_SHUTDOWN_N":    _P(bank=0, line=56, dir="out", active_low=True, bias="pull-up",   default=1, group="cell"),
    "MODEM0_UNCOND_RESET":  _P(bank=0, line=59, dir="out", bias="pull-down", default=0, group="cell"),
    "MODEM0_FLIGHT_MODE":   _P(bank=0, line=85, dir="out", bias="pull-down", default=0, group="cell"),
    "MODEM0_GNSS_DISABLE":  _P(bank=0, line=86, dir="out", bias="pull-down", default=0, group="cell"),
    "MODEM0_STAT_RED":       _P(bank=0, line=63, dir="out", active_low=False, bias="pull-up", default=0, group="cell"),
    "MODEM0_STAT_GREEN":     _P(bank=0, line=61, dir="out", active_low=False, bias="pull-down", default=1, group="cell"),
    "MODEM0_STAT_BLUE":       _P(bank=0, line=48, dir="out", active_low=False, bias="pull-down", default=0, group="cell"),
    "MODEM0_PASS_THROUGH_SELECT": _P(bank=0, line=37, dir="out", bias="pull-down", default=0, group="cell"),

    # ---------------- WIFI0 ----------------
    # Per-instance naming (WIFI<N>_…) mirrors the modem convention so
    # additional radios drop in cleanly as WIFI1_*, WIFI2_*, …. ``PD``
    # is power-down; the ``_N`` suffix is the standard hardware
    # shorthand for ACTIVE-LOW: physical line high = radio powered,
    # low = held in power-down. vyos.hardware passes physical levels
    # through (no software inversion), matching what a scope would show.
    "WIFI0_PD_N":        _P(bank=0, line=14, dir="out", bias="pull-up",   default=1, group="wifi0"),
    "WIFI0_STAT_RED":     _P(bank=0, line=64, dir="out", active_low=False, bias="pull-up", default=0, group="wifi0"),
    "WIFI0_STAT_GREEN":   _P(bank=0, line=58, dir="out", active_low=False, bias="pull-down", default=1, group="wifi0"),
    "WIFI0_STAT_BLUE":    _P(bank=0, line=47, dir="out", active_low=False, bias="pull-down", default=0, group="wifi0"),
    # ---------------- CONTROL ----------------
    "VPP_LDO_EN":        _P(bank=0, line=33, dir="out", bias="pull-down", default=0, group="control"),
    "VSEL_SD_SWITCH":    _P(bank=0, line=45, dir="out", bias="pull-up",   default=1, group="control"),
    "PMIC_STBY":         _P(bank=0, line=51, dir="out", bias="pull-up",   default=1, group="control"),
    "SYS_STAT_RED":      _P(bank=0, line=62, dir="out", active_low=False, bias="pull-up", default=0, group="control"),
    "SYS_STAT_GREEN":    _P(bank=0, line=57, dir="out", active_low=False, bias="pull-down", default=1, group="control"),
    "SYS_STAT_BLUE":     _P(bank=0, line=46, dir="out", active_low=False, bias="pull-down", default=0, group="control"),
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
    "UARTC0_SHUT_N":     _P(bank=1, line=50, dir="out", active_low=True, bias="pull-down", default=1, group="uartc0"),

    # ---------------- UARTC2 (THVD4431) ----------------
    "UARTC2_MODE0":      _P(bank=0, line=40, dir="out", bias="pull-up",   default=1, group="uartc2"),
    "UARTC2_MODE1":      _P(bank=0, line=44, dir="out", bias="pull-up",   default=0, group="uartc2"),
    "UARTC2_MODE2":      _P(bank=0, line=32, dir="out", bias="pull-up",   default=0, group="uartc2"),
    "UARTC2_TERM_TX":    _P(bank=0, line=41, dir="out", bias="pull-down", default=0, group="uartc2"),
    "UARTC2_TERM_RX":    _P(bank=0, line=42, dir="out", bias="pull-down", default=0, group="uartc2"),
    "UARTC2_SLR":        _P(bank=0, line=35, dir="out", bias="pull-up",   default=1, group="uartc2"),
    "UARTC2_SHUT_N":     _P(bank=0, line=36, dir="out", active_low=True, bias="pull-down", default=1, group="uartc2"),

    # ---------------- UARTC4 (THVD4431) ----------------
    "UARTC4_MODE0":      _P(bank=1, line=5,  dir="out", bias="pull-up",   default=1, group="uartc4"),
    "UARTC4_MODE1":      _P(bank=1, line=1,  dir="out", bias="pull-up",   default=0, group="uartc4"),
    "UARTC4_MODE2":      _P(bank=1, line=26, dir="out", bias="pull-up",   default=0, group="uartc4"),
    "UARTC4_TERM_TX":    _P(bank=1, line=41, dir="out", bias="pull-down", default=0, group="uartc4"),
    "UARTC4_TERM_RX":    _P(bank=1, line=40, dir="out", bias="pull-down", default=0, group="uartc4"),
    "UARTC4_SLR":        _P(bank=1, line=13, dir="out", bias="pull-up",   default=1, group="uartc4"),
    "UARTC4_SHUT_N":     _P(bank=1, line=33, dir="out", active_low=True, bias="pull-down", default=1, group="uartc4"),

    # ---------------- UARTC5 (THVD4431) ----------------
    "UARTC5_MODE0":      _P(bank=1, line=15, dir="out", bias="pull-up",   default=1, group="uartc5"),
    "UARTC5_MODE1":      _P(bank=1, line=35, dir="out", bias="pull-up",   default=0, group="uartc5"),
    "UARTC5_MODE2":      _P(bank=1, line=37, dir="out", bias="pull-up",   default=0, group="uartc5"),
    "UARTC5_TERM_TX":    _P(bank=1, line=14, dir="out", bias="pull-down", default=0, group="uartc5"),
    "UARTC5_TERM_RX":    _P(bank=1, line=16, dir="out", bias="pull-down", default=0, group="uartc5"),
    "UARTC5_SLR":        _P(bank=1, line=30, dir="out", bias="pull-up",   default=1, group="uartc5"),
    "UARTC5_SHUT_N":     _P(bank=1, line=9,  dir="out", active_low=True, bias="pull-down", default=1, group="uartc5"),
}

# Per-port application-facing identity. Pin names above stay aligned with the
# silicon (UARTC0/2/4/5 = SoC UART instances); this table tells the runtime
# which kernel tty each transceiver block is wired to, plus a human label for
# CLI output. ``tty`` is the canonical device app code should open;
# ``label`` is purely cosmetic for ``test hardware show serial``.
#
# ``dt_node`` is the device-tree node tail of the SoC UART peripheral. The
# runtime verifies, at FSM startup via ``hw.verify_serial_bindings()``, that
# ``/sys/class/tty/<basename(tty)>/device/of_node`` realpath ends with this
# string — catching any DTS / pinmap drift before the FSM silently flips the
# wrong transceiver. AM64x MAIN_UART base addresses come from k3-am64-main.dtsi:
#   MAIN_UART0 = 0x02800000  (console, ttyS0)
#   MAIN_UART1 = 0x02810000  (ttyS1, UARTC0)
#   MAIN_UART2 = 0x02820000  (ttyS2, UARTC2)
#   MAIN_UART4 = 0x02840000  (ttyS3, UARTC4)
#   MAIN_UART5 = 0x02850000  (ttyS4, UARTC5)
# Confirm on a running board with:
#   readlink -f /sys/class/tty/ttyS2/device/of_node
#
# ttyS0 is the system console and is intentionally NOT exposed here.
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
# At build time, the "path" value from each entry is written to
# /usr/lib/igos/interfaces.conf as a key=name mapping that the udev helper
# igos-eth-port-id reads at boot to assign stable interface names.
#
# Path format:  <parent-devpath>#<port-number>
#   <parent-devpath> : sysfs device path of the ethernet controller (board-stable,
#                      derived from device-tree platform addresses).
#   <port-number>    : which physical port on that controller (from DT port@N
#                      node matching, or kernel dev_port for PCI NICs).
#
# Example: /devices/platform/bus@f4000/8000000.ethernet#2
#   -> port 2 of the CPSW ethernet switch at SoC address 0x08000000
#
# Path can be discovered on a running board with the following:
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
# For the pupose of engineering on the target board the logical ethernet ports have been swapped
ETH_INTERFACES = {
    "eth0": {
        "path": "/devices/platform/bus@f4000/8000000.ethernet#2",
    },
    "eth1": {
        "path": "/devices/platform/bus@f4000/8000000.ethernet#1",
    },
}

# Pinned WWAN interfaces
# At build time, the "path" value from each entry is written to
# /usr/lib/igos/interfaces.conf. The udev helper igos-wwan-port-id reads
# this at boot to assign stable wwan interface names.
#
# Path format:  <usb-controller-devpath>#<bus>-<port[.port...]>
#   <usb-controller-devpath> : sysfs path of the USB controller platform device
#                              (board-stable, from device-tree addresses).
#   <bus>-<port>             : USB topology — bus number and physical port on
#                              the root hub (e.g. 1-1 = bus 1, port 1).  For
#                              hub-attached devices this extends with dot
#                              notation (e.g. 1-1.2 = port 2 on a hub at port 1).
#
# Example: /devices/platform/bus@f4000/f900000.cdns-usb/f400000.usb#1-1
#   -> device on USB bus 1 port 1 of the Cadence USB3 controller at 0x0f400000
#
# Path can be discovered on a running board with the following:
"""
printf '%-6s  %-17s  %s\n' IFACE DRIVER IGOS_WWAN_PORT; \
printf '%-6s  %-17s  %s\n' ----- ------ --------------; \
for sys in /sys/class/net/wwan*; do \
  [ -d "$sys" ] || continue; \
  ifname=${sys##*/}; \
  devpath=$(readlink "$sys" | sed 's|^\.\./\.\.||'); \
  driver=$(basename "$(readlink "$sys/device/driver" 2>/dev/null)"); \
  usb_parent=$(printf '%s' "$devpath" | sed -n 's|\(.*\.usb\)/.*|\1|p'); \
  usb_port=$(printf '%s' "$devpath" | sed -n 's|.*usb[0-9]*/\([0-9][0-9.-]*\)/.*|\1|p'); \
  [ -n "$usb_parent" ] && [ -n "$usb_port" ] || continue; \
  printf '%-6s  %-17s  %s#%s\n' "$ifname" "$driver" "$usb_parent" "$usb_port"; \
done
"""
WWAN_INTERFACES = {
    "wwan0": {
        "path": "/devices/platform/bus@f4000/f900000.cdns-usb/f400000.usb#1-1",
        "usb_controller": "f400000.usb",
        "usb_port": "1-1",
        "ID_MM_PHYSDEV_UID": "modem0",
    }
}
