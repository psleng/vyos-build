#!/bin/sh
# Repack the freshly built, signature-enforcing arm64 grub module package under
# a distinct name so a build can SELECT it (secure_grub) in place of stock grub.
#
# The 0001-enforce-signatures patch makes pgp.mod (shipped in grub-efi-arm64-bin)
# always enforce. Publishing that under the stock name would silently replace
# grub for EVERY image. Instead we rename the built .deb to
# grub-efi-arm64-bin-secure and advertise the stock name via a versioned
# Provides so grub-efi-arm64's strict `grub-efi-arm64-bin (= ${binary:Version})`
# dependency still resolves; Conflicts/Replaces evict the stock module package
# when the secure one is explicitly installed. Installed file paths are
# identical, so grub-install and u-boot are unaffected -- only the compiled-in
# pgp enforcement differs.
#
# Run from the source tree (cwd) after dpkg-buildpackage; artifacts are one
# level up (dpkg-buildpackage writes to the parent of the source tree).
set -eu

SRC_NAME="grub-efi-arm64-bin"
NEW_NAME="grub-efi-arm64-bin-secure"
OUTDIR=".."

deb=$(ls "${OUTDIR}"/${SRC_NAME}_*_*.deb 2>/dev/null | head -n1 || true)
if [ -z "${deb:-}" ]; then
    echo "E: secure-repack: no ${SRC_NAME}_*.deb found in ${OUTDIR}" >&2
    exit 1
fi
echo "I: secure-repack: repacking ${deb} -> ${NEW_NAME}"

workdir=$(mktemp -d)
trap 'rm -rf "${workdir}"' EXIT

dpkg-deb -R "${deb}" "${workdir}"

ctrl="${workdir}/DEBIAN/control"
ver=$(awk -F': ' '/^Version:/{print $2; exit}' "${ctrl}")
if [ -z "${ver:-}" ]; then
    echo "E: secure-repack: could not read Version from ${ctrl}" >&2
    exit 1
fi

# Rename the package and inject the compatibility relationships right after the
# Package field so the stanza stays well formed (Description remains last).
awk -v new="${NEW_NAME}" -v src="${SRC_NAME}" -v ver="${ver}" '
    /^Package: / && !done {
        print "Package: " new
        print "Provides: " src " (= " ver ")"
        print "Conflicts: " src
        print "Replaces: " src
        done = 1
        next
    }
    { print }
' "${ctrl}" > "${ctrl}.new"
mv "${ctrl}.new" "${ctrl}"

# Passing a directory as the target lets dpkg-deb derive the canonical
# <package>_<version>_<arch>.deb filename (handles any epoch correctly).
dpkg-deb -b "${workdir}" "${OUTDIR}"
echo "I: secure-repack: wrote ${OUTDIR}/${NEW_NAME}_${ver}_*.deb"

# Never leave the enforcing build under the stock name: it must not be published
# where a non-secure image could pull it.
rm -f "${deb}"
echo "I: secure-repack: removed stock-named enforcing ${deb}"
