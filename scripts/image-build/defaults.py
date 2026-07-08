# Copyright (C) 2024 VyOS maintainers and contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# File: defaults.py
# Purpose: Various default values for use in build scripts.


import os
import getpass
import platform

def get_default_build_by():
    return "{user}@{host}".format(user= getpass.getuser(), host=platform.node())

# Default boot settings
boot_settings: dict[str, str] = {
    'timeout': '5',
    'console_type': 'tty',
    'console_num': '0',
    'console_speed': '115200',
    'bootmode': 'normal'
}

# Hardcoded default values
HARDCODED_BUILD = {
    'custom_apt_entry': [],
    'custom_apt_keys': [],
    'custom_package': [],
    'reuse_iso': None,
    'disk_size': 10,
    'build_by': get_default_build_by(),
    'build_comment': '',
}

# Relative to the repository directory

BUILD_DIR = 'build'
BUILD_CONFIG = os.path.join(BUILD_DIR, 'build-config.toml')

DEFAULTS_FILE = 'data/defaults.toml'

BUILD_TYPES_DIR = 'data/build-types'
BUILD_ARCHES_DIR = 'data/architectures'
BUILD_FLAVORS_DIR = 'data/build-flavors'

# Fork-only: igOS processor-family fragments and per-flavor pin maps. A
# build flavor may declare `platform = "<name>"` to merge in
# data/igos-platforms/<name>.toml (kernel package, family packages, etc.)
# and/or `pinmap_file = "<name>/pinmap.py"` to overlay a board pinmap from
# data/igos-pinmaps/ into the image at /usr/lib/python3/dist-packages/vyos/
# hardware/pinmap.py via includes.chroot.
#
# A flavor may also declare `models_dir = "<platform>"` to ship the per-model
# definition tree data/models/<platform>/ into the image at
# /usr/share/igos/models/<platform>/, where vyos.system.model resolves this
# unit's model at boot (one family image serves many board variants).
IGOS_PLATFORMS_DIR = 'data/igos-platforms'
IGOS_PINMAPS_DIR = 'data/igos-pinmaps'
IGOS_MODELS_DIR = 'data/models'
IGOS_MODELS_INSTALL_DIR = 'usr/share/igos/models'
# Relative to the build directory

PBUILDER_CONFIG = 'pbuilderrc'
PBUILDER_DIR = 'pbuilder'

LB_CONFIG_DIR = 'config'

CHROOT_INCLUDES_DIR = 'config/includes.chroot'
BINARY_INCLUDES_DIR = 'config/includes.binary'
ARCHIVES_DIR = 'config/archives/'

VYOS_REPO_FILE = 'config/archives/vyos.list.chroot'
VYOS_PIN_FILE = 'config/archives/release.pref.chroot'
CUSTOM_REPO_FILE = 'config/archives/custom.list.chroot'
PACKAGE_LIST_FILE = 'config/package-lists/custom.list.chroot'

LOCAL_PACKAGES_PATH = 'config/packages.chroot/'
