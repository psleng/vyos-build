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
    },
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
