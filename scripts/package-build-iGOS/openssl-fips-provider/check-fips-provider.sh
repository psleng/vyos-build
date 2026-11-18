#!/bin/bash
# Prove a staged fips.so is the provider we intend to ship, before packaging it.
#
# Usage: check-fips-provider.sh <path/to/fips.so> <expected-version>
#
# 1. Runs `openssl fipsinstall` against the module: this executes the module's
#    power-on self-tests (KATs) and integrity MAC, so a corrupt/broken module
#    fails the package build.
# 2. Loads the module through a throwaway openssl.cnf -- the same `.include
#    fipsmodule.cnf` + `fips = fips_sect` activation vyos-1x renders on target
#    -- and requires the provider to self-report <expected-version>. This
#    catches a wrong binary staged through the pre-stage escape hatch (e.g. an
#    unvalidated 3.5 fips.so dropped in as fips/<arch>/fips.so).
#
# Prints the provider's SHA-256 on success (consumed by debian/rules to write
# the on-target identity manifest).
set -euo pipefail

SO="$(readlink -f "$1")"
EXPECTED="$2"

tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

if ! OPENSSL_CONF=/dev/null openssl fipsinstall -module "${SO}" \
        -out "${tmp}/fipsmodule.cnf" >"${tmp}/fipsinstall.log" 2>&1; then
    cat "${tmp}/fipsinstall.log" >&2
    echo "E: ${SO}: fipsinstall self-test FAILED" >&2
    exit 1
fi

cat > "${tmp}/openssl.cnf" <<EOF
openssl_conf = openssl_init
.include ${tmp}/fipsmodule.cnf

[openssl_init]
providers = provider_sect

[provider_sect]
fips = fips_sect
EOF

# OPENSSL_MODULES makes libcrypto resolve the "fips" provider to THIS file,
# exactly as it resolves ossl-modules/fips.so on target.
got="$(OPENSSL_CONF="${tmp}/openssl.cnf" OPENSSL_MODULES="$(dirname "${SO}")" \
        openssl list -providers 2>&1 \
    | awk '/^  fips$/ {f = 1; next} f && /^  [^ ]/ {f = 0} f && $1 == "version:" {print $2; exit}')"

if [ "${got}" != "${EXPECTED}" ]; then
    echo "E: ${SO}: FIPS provider reports version '${got:-<not loaded>}', expected '${EXPECTED}'" >&2
    echo "E: refusing to package a provider that is not the pinned validated build" >&2
    exit 1
fi

echo "I: ${SO}: fipsinstall self-test passed; provider version ${got}" >&2
sha256sum "${SO}" | cut -d' ' -f1
