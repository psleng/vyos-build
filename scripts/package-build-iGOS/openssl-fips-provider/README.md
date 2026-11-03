# igos-openssl-fips-provider

Builds the **OpenSSL 3.1.2 FIPS provider** (`fips.so`, NIST CMVP **certificate
#4985** lineage) from **pinned validated source** and packages it as a standalone
Debian binary package that installs it into the OpenSSL provider module
directory:

    /usr/lib/<arch>/ossl-modules/fips.so

The system's **OpenSSL 3.5** `libcrypto` loads this provider when FIPS mode is
enabled via `set system option fips`. The provider is version-decoupled from the
base library, so a 3.1.2 provider against a 3.5 base is the OpenSSL-sanctioned
configuration. See `vyos-1x/docs/igos-fips-140-3-design.md` (§0.3, §0.4, §7.5,
§8.1).

## How it builds

`produce-fips-provider.sh` (run from `build_cmd`):
1. git-clones the **pinned** OpenSSL tag `openssl-3.1.2`
   (commit `17a2c5111864d8e016c5f2d29c40a3746b559e9d`) and verifies the commit,
2. `./Configure enable-fips && make` (native for the build arch — igOS builds
   each arch in its matching container, like the other packages),
3. stages `providers/fips.so` into `fips/<arch>/fips.so` and records
   `fips/SHA256SUMS`.

Then `dpkg-buildpackage` packages that `fips.so` into
`igos-openssl-fips-provider`. The built `fips.so`/`SHA256SUMS` are **build
outputs** (git-ignored), not committed.

### Pre-stage escape hatch (vendor / lab validated binary)
If you drop a validated `fips.so` into `fips/<arch>/fips.so` by hand, the source
build is **skipped** and that binary is used as-is. This is the path for a
vendor-supplied or lab-produced **validated** module.

## Compliance note (read before claiming "validated")

`enable-fips` produces a **functional** FIPS provider — good for engineering
bring-up. For a defensible FIPS 140-3 **claim**:

- the `./Configure` options must match the **Security Policy** for cert #4985
  (authoritative build instructions, linked from the certificate page:
  <https://csrc.nist.gov/projects/cryptographic-module-validation-program/certificate/4985>),
  and
- the build host must be a **covered Operational Environment** (OE) — especially
  **am64x / aarch64** (vendor affirmation or lab OE addition). See design doc
  §8.1 / §8.6.

Practical guide: <https://github.com/openssl/openssl/blob/openssl-3.1.2/README-FIPS.md>

## Why a separate package (not folded into openssl-3.5)

- The base `openssl-3.5` floats (rebuilt for CVEs); the provider is produced from
  fixed, pinned inputs — the two lifecycles stay decoupled.
- No divergence patched into Debian's openssl packaging.
- Auditable: pinned source commit + recorded `fips.so` SHA per build.

At runtime there is **no difference** from folding it in — the same `fips.so`
sits in `ossl-modules/` and is loaded by the same 3.5 `libcrypto`.

## Enabling it in an image

Local `.deb`s are only installed when **referenced**. The package is already
listed in `data/build-flavors/igos-am64x-all.toml`:

```toml
packages = [
  # ...
  "igos-openssl-fips-provider",
]
```

Add the same line to any other FIPS-capable flavor. The provider is present but
**inert** until `set system option fips` activates it (vyos-1x T8529:
`openssl fipsinstall` self-test -> /run/ssl/fipsmodule.cnf -> openssl.cnf).

## Build

Via the harness (local, in-place -- no git clone of this package's debian tree):
```
cd scripts/package-build-iGOS/openssl-fips-provider
./build.py            # package.toml sets build_mode = "local_app"
```
or directly: `./produce-fips-provider.sh && dpkg-buildpackage -us -uc -tc -b`.

Validate the result:
```
openssl fipsinstall -module fips/<arch>/fips.so -out /tmp/fipsmodule.cnf   # -> INSTALL PASSED
```
