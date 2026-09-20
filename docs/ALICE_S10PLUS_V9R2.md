# ALice S10+ V9R2: sucompat authorization fix and MGLRU at boot

Base: phone-tested V9, commit 2fa109a780ee2d046710209d5b84da176992237b.
The working V4 branch is not modified.

## Changes

- Fix the longuirom 32567b sucompat gate: every non-root UID must pass the
  existing KernelSU allowlist before access/stat/exec redirects apply. Absence
  of a seccomp filter is not treated as permission to use su. Root callers
  still need the KernelSU SELinux domain; Manager and granted apps retain the
  existing allowlist behavior.
- This targets the native-service interaction observed on the phone: epicd
  exited with status 255 105 times, each immediately following a KernelSU
  faccessat redirection. The code defect is confirmed. Resolution of epicd's
  restart loop still requires a phone test; no epicd logcat was supplied.
- Enable CONFIG_LRU_GEN_ENABLED after the user confirmed runtime MGLRU works.
  Preserve V9 ARM64 access-flag capabilities, so the supported runtime mask
  remains 0x0001. No additional page-table walker capability is enabled.
- Compile and execute the actual authorization function with 42 credential,
  grant, seccomp and pointer cases in CI. The original code fails the denied
  native-service/application cases; the patch passes them.

## Retained profile

- KernelSU ABI 32567; automatic syscall-table hook; no legacy manual hooks.
- SUSFS 2.2 NON-GKI with Try Umount and EROFS support.
- Android lmkd, PSI and MEMCG; legacy in-kernel LMK disabled.
- ROM-controlled ZRAM size (8 GiB observed on the phone); LZ4 default.
- V4 frequency-only OC: M4 2.912 / A75 2.400 / A55 2.106 GHz. Same voltages.
- Same V9 thermal and scheduler settings. The user reports TikTok heat is
  resolved on V9; V9R2 does not add a separate thermal modification.
- Final boot packaging preserves the previously working ramdisk, boot header
  fields and matching DTBO. CI's repository-ramdisk boot is not the delivered
  phone boot. SHA1 boot ID and SHA256 file checksums are recomputed.

## Phone acceptance

Reboot without running an MGLRU enable command. Check lru_gen/enabled is
0x0001, lmkd is running and ZRAM retains its ROM setting. Check KernelSU root
access for an allowed app and ADB shell. Observe epicd for at least one minute:
it must stay running without repeated status-255 exits. If it still exits,
collect logcat and dmesg to distinguish remaining userspace causes.

Compilation and host regression tests do not prove phone boot or stability.
