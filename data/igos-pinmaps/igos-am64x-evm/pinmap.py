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
#   <port-number>    : the port's PHYSICAL location on that controller -- the
#                      trailing integer of the sysfs attribute(s) named by
#                      ETH_PORT_ID_SOURCE (below). For the AM64x CPSW that is
#                      phys_port_name ("p1"/"p2" -> #1/#2). The igos-eth-port-id
#                      helper is generic: it only reads the attribute the pin
#                      map names -- no MAC addresses, no board assumptions -- so
#                      a new SoC (J7200) or an external switch chip is handled
#                      entirely here on the build side.
#
# Example: /devices/platform/bus@f4000/8000000.ethernet#2
#   -> port 2 of the CPSW ethernet switch at SoC address 0x08000000
#
# Path can be discovered on a running board with the following:
#
# Run as one command:
"""
printf '%-6s  %-16s  %s\n' IFACE PHYS_LOC IGOS_ETH_PORT; \
printf '%-6s  %-16s  %s\n' ----- -------- -------------; \
srcs=$(cat /usr/lib/igos/eth-port-id.source 2>/dev/null); \
for sys in /sys/class/net/eth*; do \
  [ -d "$sys" ] || continue; \
  ifname=${sys##*/}; \
  parent=$(readlink "$sys" | sed -e 's|^\.\./\.\.||' -e 's|/net/[^/]*$||'); \
  loc=; port=0; \
  for a in $srcs; do \
    v=$(cat "$sys/$a" 2>/dev/null); \
    [ -n "$v" ] || continue; \
    loc="$a=$v"; port=$(printf '%s' "$v" | sed 's/.*[^0-9]//'); \
    [ -n "$port" ] && break; \
  done; \
  [ -n "$port" ] || port=0; \
  printf '%-6s  %-16s  %s#%s\n' "$ifname" "$loc" "$parent" "$port"; \
done
"""
#
# ETH_PORT_ID_SOURCE names the /sys/class/net/<iface> attribute(s) whose
# trailing integer is the "#<port-number>" above. It lives HERE, on the build
# side, so the generic igos-eth-port-id helper needs no changes as new SoCs
# (e.g. J7200) or external switch chips are added -- each pin map just declares
# how ITS ports are identified. Give a list to try several in order (e.g. a
# board mixing the on-SoC CPSW with an external switch). The AM64x CPSW numbers
# ports as phys_port_name "p1"/"p2". Written at build time to
# /usr/lib/igos/eth-port-id.source.
ETH_PORT_ID_SOURCE = "phys_port_name"

# eth0 is the FIRST CPSW socket (port@1 / phys_port_name p1) and eth1 the
# second (port@2 / p2), matching the AM64x EVM's physical port order.
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