# igOS AM64x EVM pin map placeholder.
#
# This flavor intentionally declares no GPIO pins yet. Keeping this file
# allows the build flavor to remain valid while preventing accidental use of
# copied/incorrect pin numbers.
#
# Once hardware mapping is finalized, populate PINS (and optionally
# SERIAL_PORTS) with verified AM64x EVM values.

VARIANT = "am64x_evm"

# No board GPIOs are defined for this flavor yet.
PINS = {}

# No serial port identity mapping until pins/ttys are verified on hardware.
SERIAL_PORTS = {}

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
ETH_INTERFACES = {
    "eth0": {
        "path": "/devices/platform/bus@f4000/8000000.ethernet#1",
    },
    "eth1": {
        "path": "/devices/platform/bus@f4000/8000000.ethernet#2",
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