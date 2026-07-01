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
