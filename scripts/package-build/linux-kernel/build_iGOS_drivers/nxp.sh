#!/bin/sh
#
# Start/stop NXP 88W9098 wifi/BT module
# This should be invoked by /lib/systemd/system/nxp.service
#

# Debug flags (see dmesg)
d=0x7
#d=0x20037

LOG=/var/log/wifibt.log
if [ "$1" = "start" ]; then
    # Rotate logs
    mv -f $LOG $LOG.1
fi

exec >> $LOG 2>&1

echo ==== $(date) $0 "$@"
set -x

case "$1" in

stop) # Stop all wifi stuff
    # Stop all and any hostapd
    for i in 0 1 2 3
    do
        systemctl stop hostapd@wlan$i.service
    done

    # Stop all and any wpa_supplicant
    for i in 0 1 2 3
    do
        systemctl stop wpa_supplicant-macsec@wlan$i.service
        systemctl stop wpa_supplicant-nl80211@wlan$i.service
        systemctl stop wpa_supplicant-wired@wlan$i.service
        systemctl stop wpa_supplicant@wlan$i.service
    done

    # Bring down all possible associated interfaces
    for i in wlan0 wlan1 wlan2 wlan3 phy1 phy0 mlan0 uap0 mmlan0 muap0 uap1 muap1 wfd0 wfd1 mwfd0 mwfd1 nan0 mnan0
    do
        ifconfig $i down > /dev/null 2>&1
    done

    # Remove modules
    for i in 1 2 3; do rmmod moal && break; done
    for i in 1 2 3; do rmmod mlan && break; done
    ;;

*) # Start all wifi stuff
    sudo modprobe cfg80211
    sudo insmod /usr/lib/modules/nxp/mlan.ko drvdbg=$d
    sudo insmod /usr/lib/modules/nxp/moal.ko mod_para=/nxp/wifi_mod_para.conf drvdbg=$d
    sudo sudo iw phy mwiphy1 set name phy1
    sudo sudo iw phy mwiphy0 set name phy0
    ;;

esac
