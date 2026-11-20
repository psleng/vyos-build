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
outputs** (git-ignored), not committed. Packaging:

- runs `check-fips-provider.sh`: `openssl fipsinstall` self-tests the staged
  module, then loads it and **refuses to package it unless the provider
  self-reports the pinned version** (`3.1.2`, the upstream part of the package
  version). A wrong binary staged via the escape hatch below fails the build;
- ships `fips.so` **byte-for-byte as built** (`dh_strip`/`dh_dwz` disabled);
- writes an arch-specific identity manifest,
  `/usr/lib/<multiarch>/igos-openssl-fips-provider/fips.so.manifest`
  (`version=` + `sha256=` of the shipped `fips.so`).

## Which `fips.so` is active on the running system

OpenSSL resolves the `fips` provider to `/usr/lib/<multiarch>/ossl-modules/fips.so`
and `openssl fipsinstall` will self-test *any* FIPS provider there, so neither
proves the validated module is the one in use. Three layers make sure it is:

1. **Packaging:** `Conflicts`/`Replaces`/`Provides: openssl-provider-fips`.
   Debian's OpenSSL 3.5 source (our `openssl-3.5` package) also builds
   `openssl-provider-fips` — an **unvalidated 3.5** `fips.so` at the **same
   path**. This package takes that path over, so the two can never co-exist.
2. **Commit (`set system option fips`)** and **every boot**
   (`vyos-fips-regenerate.service`): vyos-1x refuses / fails closed unless the
   on-disk `fips.so` matches the manifest SHA-256 **and**, after `fipsinstall`,
   the provider OpenSSL actually loads reports the manifest version.
3. **Op-mode:** `show system fips` shows the loaded provider version against the
   validated version, and whether the module matches the manifest.

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

Packages from the APT mirror are only installed when **referenced**; the
package is listed in the igOS flavors (`data/build-flavors/igos-*.toml`):

```toml
packages = [
  # ...
  "igos-openssl-fips-provider",
]
```

Note that any `.deb` dropped into `vyos-build/packages/` is installed whether
or not a flavor lists it (live-build `packages.chroot`). Do not drop the
`openssl-provider-fips_*.deb` from an `openssl-3.5` build there — it conflicts
with this package and the image build will fail.

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

Validate the result (the package build already runs this):
```
./check-fips-provider.sh fips/<arch>/fips.so 3.1.2    # self-test + version; prints SHA-256
```

On target, with FIPS enabled:
```
show system fips          # Provider version: 3.1.2 (validated: 3.1.2), Validated module: yes
openssl list -providers   # fips ... version: 3.1.2, status: active
```
