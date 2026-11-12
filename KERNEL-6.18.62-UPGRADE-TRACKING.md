# Kernel 6.18.62 Bump & Package Upgrade Tracking

Fork: `psleng/vyos-build` (iGOS / perle).  Upstream reference: `vyos/vyos-build`
(`~/vyos-build-upstream`).  Target kernel: **6.18.38 → 6.18.62**.

Plan: **(1) build the kernel first, then (2) update packages one-by-one.**

Status legend: ☐ TODO  ◐ IN PROGRESS  ☑ DONE  ⊘ SKIP (not needed)

---

## Phase 1 — Kernel bump  ☑ DONE (pending full container build)

### Change set (uncommitted in working tree)
- ☑ `data/defaults.toml` — `kernel_version` `6.18.38` → `6.18.62`
  - Note: upstream `kernel_revision` key intentionally **not** added — your
    `build.py` takes only `kernel_version` and `build-kernel.sh` hardcodes `-1`.
- ☑ `scripts/package-build/linux-kernel/patches/kernel/0001-linkstate-ip-device-attribute.patch`
  — refreshed context for 6.18.62 (from upstream; body unchanged)
- ☑ `scripts/package-build/linux-kernel/patches/accel-ppp-ng/0002-cmake-run-depmod-for-the-target-kernel-version.patch`
  — NEW (auto-applied by build loop)
- ☑ `scripts/package-build/linux-kernel/patches/ipt-netflow/0005-Fix-build-with-sockaddr_unsized-bind-callbacks.patch`
  — NEW, **required** for 6.18.y (sockaddr_unsized bind() backport)
- ☑ `scripts/package-build/linux-kernel/patches/mlnx-ofed-kernel/` — NEW (4 patches)
- ☑ `scripts/package-build/linux-kernel/build-mellanox-ofed.sh` — ported upstream
  rewrite (OFED 24.07 → DOCA 26.07, `--kernel-only --build-only`, patch loop,
  mlnx-tools build)
- ☑ `scripts/package-build/linux-kernel/common.sh` — NEW helper (`require_amd64`,
  `debian_version`) required by the new mellanox script
- ☑ `scripts/package-build/linux-kernel/platform/perle-igos/bookworm-am64xx-igos/patches/kernel/0005-ttyS-iolan.patch`
  — **refreshed** against 6.18.62 (zero fuzz; produces byte-for-byte identical
  tree; only context/`@@`/`index` lines changed)

### Patch validation vs 6.18.62 (dry-run + cumulative apply, verified)
| Patch set | Result |
|---|---|
| Shared `patches/kernel/*` (5) | ☑ clean |
| perle-igos am64x-igos (9) | ☑ clean (serial patch refreshed from fuzz→clean) |
| ti-evm am64x-evm (2) | ☑ clean |
| ti-evm j7200-evm (1) | ☑ clean |

### Remaining
- ☐ Full container build of the kernel + OFED (needs Docker build env; OFED needs amd64)
- ☐ Smoketests (`make test ...`, run as root for QEMU)
- ☐ Commit with `component: T####: description` message style

### Build reminder
Mellanox OFED is amd64-only (`require_amd64` soft-skips on arm64). The ISO build
applies platform patches with `patch -f -p1 || echo "E: patch FAILED"` and does
**not** stop on failure — watch build logs for `E: patch ... FAILED` / `fuzz`.

---

## Phase 2 — Package updates (one-by-one)

### How packages are built & shipped (important)
- The **ISO build does NOT use `package-build/` recipes.** It pulls prebuilt
  `.deb`s from your mirror (`psleng.github.io`) + Debian at ISO assembly time.
- `package-build/<pkg>` recipes are built by the **separate package pipeline**
  (`.github/workflows/trigger_rebuild_packages.yml` → `vyos-build-packages`),
  which publishes `.deb`s to your mirror.
- So "bringing a package in" = **3 steps**:
  1. Add the `package-build/<pkg>/` recipe (`package.toml` + `build.py` symlink).
  2. Build it in the container: `cd scripts/package-build/<pkg> && ./build.py`.
  3. Publish the resulting `.deb` to `psleng.github.io` (pipeline) so the ISO
     pulls it instead of the Debian/stock version.
- Working in-fork example of this pattern: `scripts/package-build/ethtool/`.

### 2A — Missing upstream packages (decide whether to add)

Versions below are from the real ISO manifest at
`~/nexus-build-perle/vyos-build/build/live-image-arm64.packages`
(arm64 igos-am64x-all, kernel 6.18.38).

| Pkg | Your ISO ships | Upstream recipe | Priority | Decision / Status |
|---|---|---|---|---|
| **iproute2** | `6.15.0-1~bpo12+1` (Debian backport) | `debian/6.18.0-1` (matches kernel) | Medium (kernel-coupled) | ☑ recipe added (build+publish pending) |
| **pdns-recursor** | `4.8.8-1+deb12u1` (stock, no fix) | same ver **+ /etc/hosts dual A/AAAA fix** | Only if DNS forwarding used | ☐ |
| **haproxy** | `2.6.12-1+deb12u4` (stock) | `3.0.29` | Only if reverse-proxy used | ☐ |
| **squid** | `5.7-2+deb12u6` (stock) | `7.6-2` | Only if webproxy used | ☐ |
| **shim-signed** | not in arm64 ISO (uses grub-efi-arm64-bin-secure + mokutil + igos-sign-boot) | amd64 UEFI shim | ⊘ N/A for arm64 flavor | ⊘ |

Covered under other names (not truly missing):
- **vyatta-bash** → `package-build-iGOS/vyatta-bash` ☑
- **openssl** → iGOS `openssl-3.5`, `openssl-fips-provider`, `tpm2-openssl` ☑
- **openvpn** → only `openvpn-plugin-duo` + `openvpn-otp`; no core recipe ☐ (if needed)

Ready-to-use iproute2 recipe (`scripts/package-build/iproute2/package.toml`):
```toml
[[packages]]
name = "iproute2"
commit_id = "debian/6.18.0-1"
scm_url = "https://salsa.debian.org/kernel-team/iproute2.git"
pre_build_hook = "sudo apt-get install -y -t bookworm-backports debhelper"
```
(+ `build.py` symlink to `../build.py`, and a `.gitignore`.)

**Status:** ☑ **recipe dir created** (`scripts/package-build/iproute2/`: `package.toml`
+ `build.py` symlink + `.gitignore`, identical to upstream, TOML validated).
Remaining pipeline steps: ☐ build in container (`cd scripts/package-build/iproute2 && ./build.py`)
→ ☐ publish `.deb` to `psleng.github.io` mirror.

### 2B — Shared packages you build at a DIFFERENT version

Branch-naming only — same repos, your `current` ≈ upstream `rolling` (no action):
| Pkg | You | Upstream |
|---|---|---|
| libnss-mapuser | `current` | `rolling` |
| libpam-radius-auth | `current` | `rolling` |
| tacacs | `master` | `rolling` |
| vpp | `current` | `rolling` (your scm_url = psleng fork) |
| vyos-1x | `current` | `rolling` |

Real version differences:
| Pkg | You | Upstream | Direction | Decision / Status |
|---|---|---|---|---|
| **ethtool** | `1%6.14.2-1` | `1%6.10-1` | 🟢 you are AHEAD (intentional PSL pin) | ⊘ keep |
| **strongswan** | `5.9.11-2` | `6.0.7-1` | 🔴 BEHIND (major 5.9→6.0) | ☐ |
| **podman** | `v4.9.5` | `debian/1.14.0-2` | upstream moved to Debian pkg | ☐ (also in iGOS tree — confirm which builds) |
| **ddclient** | `debian/3.11.2-1` | `ae21b1deee` | upstream moved to git snapshot | ☐ |

---

## Notes / open questions
- Your fork spreads recipes across TWO trees: `package-build/` (upstream-derived)
  and `package-build-iGOS/` (fork-specific + some overrides like `podman`,
  `net-snmp`, `salt-minion`). Check the iGOS tree before assuming a gap.
- Broader `linux-kernel/` build-tooling drift exists but is independent of the
  kernel bump: intentional PSL customizations (tarball skip, FIPS, NXP signing)
  + upstream refactors not yet adopted (`build-jool`/`build-realtek*` `.py`→`.sh`,
  `config/arm64`, `config/x86`, `kernel_revision` plumbing). Out of scope for now.
- shim-signed (T861) is upstream's standard UEFI Secure Boot chain; you already
  have a custom secure-boot/FIPS signing scheme — compare before adopting.
