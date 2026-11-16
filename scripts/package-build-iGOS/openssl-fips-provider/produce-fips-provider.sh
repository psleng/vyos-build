#!/bin/bash
# Produce the OpenSSL 3.1.2 FIPS provider (fips.so) for the BUILD host arch and
# stage it at fips/<arch>/fips.so (+ record fips/SHA256SUMS), so the Debian
# package in this directory can ship it into ossl-modules/.
#
# Per-arch by construction: igOS builds each arch in its matching-arch container
# (native), exactly like the other package-build-iGOS packages, so OpenSSL's
# ./Configure auto-targets the right CPU — no cross-compile here.
#
# IMPORTANT (compliance): this builds the provider from PINNED validated 3.1.2
# source. For a defensible FIPS 140-3 claim the Configure options MUST match the
# module's Security Policy (cert #4985), and the build host must be a covered
# Operational Environment. See ../../.. docs/igos-fips-140-3-design.md §8.1/§8.6
# and https://github.com/openssl/openssl/blob/openssl-3.1.2/README-FIPS.md
#
# Pre-staging escape hatch: if fips/<arch>/fips.so already exists (e.g. a
# vendor-supplied validated binary dropped in by hand), the source build is
# skipped and that binary is used as-is.
set -euo pipefail

OPENSSL_TAG="openssl-3.1.2"
# Commit the annotated tag openssl-3.1.2 dereferences to (git rev-parse HEAD
# after checkout). NOT the tag-object SHA (11ee83c3...).
OPENSSL_COMMIT="17a2c5111864d8e016c5f2d29c40a3746b559e9d"
OPENSSL_GIT="https://github.com/openssl/openssl.git"

HERE="$(cd "$(dirname "$0")" && pwd)"
ARCH="$(dpkg-architecture -qDEB_HOST_ARCH)"
DEST="${HERE}/fips/${ARCH}"
SO="${DEST}/fips.so"

mkdir -p "${DEST}"

if [ -f "${SO}" ] && head -c4 "${SO}" | od -An -tx1 | tr -d ' \n' | grep -q '^7f454c46'; then
    echo "I: fips.so already staged for ${ARCH} (pre-staged binary) — skipping source build"
else
    echo "I: building OpenSSL ${OPENSSL_TAG} FIPS provider for ${ARCH}"
    SRC="${HERE}/.openssl-src"
    rm -rf "${SRC}"
    git clone --depth 1 --branch "${OPENSSL_TAG}" "${OPENSSL_GIT}" "${SRC}"
    got="$(git -C "${SRC}" rev-parse HEAD)"
    if [ "${got}" != "${OPENSSL_COMMIT}" ]; then
        echo "E: openssl source commit mismatch: got ${got}, expected ${OPENSSL_COMMIT}" >&2
        exit 1
    fi
    (
        cd "${SRC}"
        # NOTE: align these options with the cert #4985 Security Policy for a
        # validated build. 'enable-fips' is the minimum to produce fips.so.
        ./Configure enable-fips
        make -j"$(nproc)"
    )
    install -m 0644 "${SRC}/providers/fips.so" "${SO}"
    rm -rf "${SRC}"
    echo "I: staged ${SO}"
fi

# Record / refresh the pin hash for THIS arch (merge-friendly across arches).
(
    cd "${HERE}/fips"
    tmp="$(mktemp)"
    [ -f SHA256SUMS ] && grep -v "  ${ARCH}/fips.so$" SHA256SUMS > "${tmp}" || true
    sha256sum "${ARCH}/fips.so" >> "${tmp}"
    sort -o "${tmp}" "${tmp}"
    mv "${tmp}" SHA256SUMS
)
echo "I: fips/SHA256SUMS:"; cat "${HERE}/fips/SHA256SUMS"

# Remove the placeholder once a real provider is staged.
rm -f "${DEST}/PLACEHOLDER.txt"
