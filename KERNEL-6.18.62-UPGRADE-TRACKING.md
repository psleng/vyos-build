# Kernel 6.18.62 Bump & Package Upgrade Tracking

Fork: `psleng/vyos-build` (iGOS / perle).  Upstream reference: `vyos/vyos-build`
(`~/vyos-build-upstream`).  Target kernel: **6.18.38 → 6.18.62**.

Plan: **(0) merge `vyos-1x` with upstream first (prerequisite — see Phase 0),
then (1) build the kernel, then (2) update packages one-by-one.**

Status legend: ☐ TODO  ◐ IN PROGRESS  ☑ DONE  ⊘ SKIP (not needed)

---

## Phase 0 — Merge `vyos-1x` with upstream (PREREQUISITE)  ☐ TODO

Several package bumps (notably **strongswan 6**, §2B) need upstream `vyos-1x`
changes the fork does not have, so the fork must be merged with upstream first.

### Where things stand (measured 2026-11-13)
- Fork: `psleng/vyos-1x` branch `vyos-1x-jf` (`~/vyos-1x`). Upstream renamed its
  main branch **`current` → `rolling`** (`git fetch upstream rolling`).
- Merge-base with `upstream/rolling`: `2430dd1db` (**2026-05-19**).
  Since then: **924** fork commits vs **732** upstream commits (non-merge).
  Fork diff is mostly additions (+76k / −1.4k lines); **115** files changed on
  both sides.
- Trial merge (throwaway worktree): **59 conflicted files**, ~150 hunks,
  ~5,300 conflict lines (53 content, 4 modify/delete, 2 add/add,
  1 rename/delete).

### Conflict areas (hardest first)
| Area | Main files | Approach |
|---|---|---|
| **Interface naming — upstream T3871** (slot-anchored mapping store, `hw-id` node removed, udev `vyos_net_name`/`65-vyos-net.rules` deleted) | `ifconfig/interface.py`, `utils/network.py`, `vyos-interface-rescan.py`, `vyos-netlinkd`, `ifconfig/ethernet.py`, udev rules | **Decided: take upstream, make it inert for Perle hardware.** Upstream's scheme targets PC/VM hardware (PCI slots, ESXi/Hyper-V/Azure). On AM64x both CPSW ports share `ID_PATH=platform-8000000.ethernet`, so upstream would fall back to MAC keys. Keep Perle pin-map naming (`63-igos-eth-pin.rules` / `igos-eth-port-id`, `IGOS_IFNAME`) and make `vyos-net-name-resolve`/`resolve()` skip devices with `IGOS_IFNAME` set (and not store them). Same for the pinned `wwan0` (upstream `9d44e9363` also names modems). |
| **Migration `interfaces/34-to-35`** (add/add) | — | ☑ **Pre-fixed in fork** (see below) — take upstream's `34-to-35` (hw-id removal) on merge. |
| **Security / PKI / API** | `conf_mode/pki.py`, `vyos/pki.py`, `service_https.py`, API `routers.py`, `system_login.py`, `utils/auth.py`, `openssl.cnf.j2` (add/add), `vyos-config-encrypt.py` | Resolve hunk-by-hunk against the FIPS / TPM / overlay-encryption design docs. |
| **WWAN / TPM** (fork-owned) | `show_wwan.py`, `interfaces_wwan.py`, `ifconfig/wwan.py`, `show_tpm.py` | Mostly keep fork; decide per upstream fix (e.g. T9388, Nov 7–8) whether to port. |
| Everything else (~30 files) | container, snmp, syslog, bgp, ospf, image_installer, version, grub, smoketests | Low/medium — a few hunks each. |

Plus semantic breakage that merges cleanly but fails at runtime (renamed/changed
upstream helpers): build the package, run `src/tests`, smoketests on hardware —
especially interface naming per Perle model, and config migration.

### Config-migration fix (done ahead of the merge)  ☑ (uncommitted in `~/vyos-1x`)
- Bug found: the fork declared `interfaces` **version 34** but shipped
  `interfaces/34-to-35` (ip-passthrough key rename, `c36927437`). The migrator
  runs every script `>=` the file version whenever **any** component differs,
  so `34-to-35` pushed `interfaces` to 35 ≠ 34 → **"incomplete migration"**.
  Reproduced on `10.10.50.165` against a config copy (older `system` component).
  At boot `vyos-router` then loads the un-migrated config on every boot.
  Latent today only because unit configs already match the image versions.
- Fix: new component **`igos`** —
  `interface-definitions/include/version/igos-version.xml.i` (version 1) and
  `src/migration-scripts/interfaces/34-to-35` → `src/migration-scripts/igos/0-to-1`.
  `interfaces` stays at 34 (= upstream pre-T3871). Rule added to `AGENTS.md`:
  igOS-only migrations go under `igos/`, never into upstream components.
- Verified on the unit with the real migrator: current config, upgrade case
  (`system@31`), and re-run all succeed → `interfaces@34 igos@1 system@32`.
- It is the fork's **only** fork-specific migration script.
- ☐ Commit: `igos: move ip-passthrough migration out of interfaces into igos component`.

### Merge plan
- ☐ Merge (not rebase 924 commits) `upstream/rolling` into a new branch.
- ☐ Resolve WWAN/TPM + low-risk areas; keep a per-file decision log.
- ☐ Interface naming: implement the "skip `IGOS_IFNAME` devices" change in the
  resolver; verify names on each Perle model.
- ☐ Security/PKI/API hunks reviewed against the igOS design docs.
- ☐ Build, `src/tests`, smoketests; then merge upstream regularly (every few
  weeks) to keep future merges small.
- Alternative if strongswan 6 is needed before the full merge: cherry-pick only
  the commits listed under strongswan in §2B.

---

## Phase 1 — Kernel bump  ☑ DONE (built and running on `10.10.50.165`)

### Change set (committed in `82a512b5` "bump kernel to 6.18.62 add iproute2")
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
- ☑ Kernel built (perle-igos, arm64) and running on the reference unit
  `igos@10.10.50.165` (IOLAN SDW4-PT, `6.18.62-vyos`)
- ☐ Full container build of OFED (amd64 only)
- ☐ Smoketests (`make test ...`, run as root for QEMU)
- ☐ Apply the ASPM change to the ti-evm defconfig (see below)

### Build reminder
Mellanox OFED is amd64-only (`require_amd64` soft-skips on arm64). The ISO build
applies platform patches with `patch -f -p1 || echo "E: patch FAILED"` and does
**not** stop on failure — watch build logs for `E: patch ... FAILED` / `fuzz`.

### Hardware findings & fixes on 6.18.62 (reference unit `10.10.50.165`)

**1. NXP 88W9098 Wi-Fi panic at boot — PCIe ASPM** ☑ (`a28a3641` "turn off pcie powersave")
- Symptom: intermittent `Internal error: synchronous external abort` →
  `Kernel panic` in `woal_pcie_read_reg` (`insmod moal`, first BAR2 read of
  `PCIE9098_SCRATCH_3_REG` 0x1C6C during FW download); a later boot worked.
- Cause: since 6.18, devicetree platforms get ASPM L0s/L1 enabled by default
  (`pcie_aspm_override_default_link_state()`; dmesg
  `pci 0000:01:00.0: ASPM: default states L1`). With
  `CONFIG_PCIEASPM_POWERSAVE` the link to the 9098 ran in L1 (endpoint reports
  L1 exit latency "unlimited"); an MMIO read during L1 exit aborted.
- Fix (perle-igos defconfig): `CONFIG_PCIEASPM_PERFORMANCE=y` (ASPM + Clock PM
  off on every link). Verified on the unit: policy `[performance]`,
  `LnkCtl: ASPM Disabled` on both ends; FW loads cleanly. The
  `ASPM: default states L1` dmesg line still prints (informational only).
- Root-port runtime D3 was ruled out (pcieport binds with PME/AER IRQ 554;
  Wi-Fi functions are `power/control=on`, so the port never suspends).
- ☐ **ti-evm** defconfig (`am64x-evm` + `j7200-evm`) still has
  `CONFIG_PCIEASPM_DEFAULT=y`, which on DT platforms also enables L0s/L1 since
  6.18 → apply the same `CONFIG_PCIEASPM_PERFORMANCE=y` swap. x86_64 can stay on
  DEFAULT (keeps BIOS settings).

**2. Wi-Fi AP fails to start / FW reset at boot — NXP driver command timeout** ☑ (`5ac4e7b2`)
- Symptom: `Timeout cmd id ... APCMD_BSS_START [0xb1]` → driver in-band FW
  reset → AP (`hostapd@wlan0`) stays down.
- Cause: the 9098 FW holds BSS_START until a scan on the other MAC (`wlan3`,
  wpa_supplicant) completes; a scan of 110–140 APs takes 6–7 s but the driver
  gives BSS_START only 5 s. Reproduced on the unit (AP started 1 ms after
  `SCAN COMPLETED`). Not PCIe related (response arrived just after the timeout).
- Fix: NXP driver + firmware bumped to **`lf-6.18.37_2.1.0`** (FW
  `17.92.1.p149.115` → `p149.159`; `build_iGOS_drivers` `BRANCH` + `VERS=1.0.6`)
  with new `mwifiex.lf-6.18.37_2.1.0.patch`: `APCMD_BSS_START`/`BSS_STOP`
  timeout 5 s → 20 s (same as SCAN; NXP itself moved `APCMD_SYS_CONFIGURE` to
  20 s in this branch), plus the existing `signal_avg` change. New
  `imx-firmware.lf-6.18.37_2.1.0.patch` carries the PSL `wifi_mod_para.conf`
  (`uap_max_sta = 48`, `antcfg = 0x101`). Driver compiled clean against the
  6.18.62 tree with the perle defconfig.
- ⚠ Before rebuilding: delete stale clones
  `~/nexus-build-perle/vyos-build/scripts/package-build/linux-kernel/build_iGOS_drivers/{mwifiex,imx-firmware}`
  — the script only `git pull`s an existing clone (no branch switch, no patch).
- Known limitation (accepted): after any FW in-band reset the driver recovers
  in ~1.5 s, but `hostapd@wlanN` is stopped via `BindsTo=` and
  `wpa_supplicant@wlanN` loses its interface; neither restarts until reboot /
  commit (`systemctl restart hostapd@wlan0 wpa_supplicant@wlan3` by hand).
- Expected: after a reset the driver reloads `pcie9098_wlan_v1.bin` (WLAN-only),
  not the combo FW — by design (`woal_update_firmware_name()`), BT keeps running.

**3. CVE-2026-98432** (ipv4 `inet_opt`/`ireq_opt` use-after-free) ☑ fixed in
6.18.56+; verified present in the 6.18.62 tree (`net/ipv4/af_inet.c:159`,
`net/ipv4/tcp_ipv4.c:1238` use `kfree_rcu`). 6.18.38 was vulnerable.

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

`vyos-1x` is **not** just a rename: the fork (`vyos-1x-jf`) is 732 upstream
commits behind `rolling` — see **Phase 0**.

Real version differences:
| Pkg | You | Upstream | Direction | Decision / Status |
|---|---|---|---|---|
| **ethtool** | `1%6.14.2-1` | `1%6.10-1` | 🟢 you are AHEAD (intentional PSL pin) | ⊘ keep |
| **strongswan** | `5.9.11-2` | `6.0.7-1` | 🔴 BEHIND (major 5.9→6.0) | ☐ blocked on Phase 0 — details below |
| **podman** | `v4.9.5` | `debian/1.14.0-2` | upstream moved to Debian pkg | ☐ (also in iGOS tree — confirm which builds) |
| **ddclient** | `debian/3.11.2-1` | `ae21b1deee` | upstream moved to git snapshot | ☐ |

#### strongswan 5.9.11 → 6.0.7 — what the bump needs

Upstream history: T8099 6.0.6 (2026-06, `8c11ba45`, `71dcf959`), T9209 6.0.7-1
(`74d2cc6e`), T9294 security patches (`4424d677`).

**vyos-build side (this repo):**
- ☐ `scripts/package-build/strongswan/package.toml`: `commit_id =
  "debian/6.0.7-1"`, `dch -v "6.0.7-1+vyos0"`, `set -e` in `build_cmd`; keep the
  PSL `mk_build_deps_cmd = "true"` (upstream instead uses a `pre_build_hook`
  removing `systemd-dev` from `debian/control`).
- ☐ Patches: fork `0001`–`0004` are byte-identical to upstream's pre-6.0 set →
  take upstream's rebased `0001`–`0004` + new `0005` (ML-KEM) and
  `0006`–`0016` (T9294 security fixes) as-is. Only local diff in the dir:
  `exec 2>&1` in `build-vici.sh`.
- ☐ **Required:** `data/live-build-config/hooks/live/30-strongswan-configs.chroot`
  — take upstream's version. The fork's hook edits
  `/etc/strongswan.d/charon.conf`, which in 6.0 belongs to `strongswan-charon`
  (not installed) → the image build would fail.

**vyos-1x side (fork has none of these):**
- ☐ **Required — T9542** `ad3b09bc0` (+ `2c510ff27`, `b1a421fa8`): strongswan 6
  no longer ships the `ipsec` script. Fork call sites (same as upstream fixed):
  `src/conf_mode/system_acceleration.py` (`ipsec start` / `ipsec {action}`),
  `src/op_mode/vpn_ipsec.py:42,69` (`ipsec statusall`),
  `op-mode-definitions/vpn-ipsec.xml.in:288` (`/usr/sbin/ipsec status`).
  Without it `show vpn debug`, `show vpn debug peer`, `show vpn ipsec status`
  fail and QAT acceleration cannot restart the daemon.
- ☐ **Required — T8099** `24dd25712`: `debian/control` strongswan deps
  `>= 6.0.6` (fork currently `>= 5.9`).
- ☐ **Strongly recommended — ESN interop: T8097** `e8611801c` (+ tests) **and
  T9254** `712c1520f`, `0db7521a9`: strongswan 6.0.6 will not match `-noesn`
  against a proposal without ESN; fork proposals carry no ESN suffix. Take
  T9254 with T8097 (otherwise ESN ends up in IKE proposals — breaks e.g. Cisco
  FTD).
- Optional: T8099 `7693c06dc` (post-quantum ML-KEM CLI; needs patch 0005),
  T9216 `c2d2f51c3` (drop python3-vici build-dep), T8912 `3b22850f4` (log level).

**Not affected:** igOS TPM design binds IPsec keys via the charon `pkcs11`
plugin (tpm2-pkcs11); upstream 6.0 patch `0004` still builds `pkcs11` and `tpm`
(disables only ldap, led, nm, mediation, mysql, sqlite). No other fork code uses
the `ipsec` script or stroke/`ipsec.conf`.

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

### Related findings on the reference unit (not kernel-specific)
- **CPU load** (4 h uptime, 2 cores): bursty Python start-ups, not overload.
  - `dial-on-demand@wwan0` exits after every cycle and relies on
    `Restart=always` → **194 restarts in 4 h**, ~7 s CPU per start (1,117 s
    total). Redesign as a long-running daemon using the existing bearer-lease
    API (`owner=dod-traffic`): design draft
    `~/vyos-1x/docs/igos-wwan-dial-on-demand-design.md` (separate service kept;
    no CLI / conf-mode changes).
  - The modem reconnects every ~78 s because all DNS goes to the carrier
    resolvers via `wwan0` (`eth1` unplugged) and the failover check targets
    `wwan0` — configuration guidance in the design doc §11.
  - `eth1 address dhcp` with no cable: `dhclient` fails every ~2 min and runs
    `dhclient-script-vyos` each time (~950 s CPU) — disable unused DHCP ports.
  - Steady consumers: `vyos-http-api` 1,324 s, `flask` GUI 1,245 s,
    `igos-wwan-manager` 960 s, `vyos-failover` 614 s.
- **GPIO read-back:** pads declared `PIN_OUTPUT*` (input buffer off) always read
  0 via debugfs/`gpiod_get_*` — DTR (GPIO1_17/18/60/66), UART LEDs
  (GPIO0_4–9/12/13), PCIe PERST (GPIO0_38), `VSEL_SD_SWITCH` hog (GPIO0_45).
  Drive is unaffected; use `PIN_INPUT*` (same pull) if read-back is wanted.
  Pin-map-managed outputs already use `PIN_INPUT*`.
