# ALice S10+ V9 MGLRU diagnostic

V9 starts directly from the phone-tested V4 commit
`e8ad33ee31404ccfdd30ee0c9a508c36d95f79db`. It does not inherit the V7
KernelSU, ZRAM, thermal or packaging commits.

## What changed from V4

- The MGLRU implementation is backported into the Exynos 9820 Linux 4.14 tree.
- `CONFIG_LRU_GEN=y`, but `CONFIG_LRU_GEN_ENABLED` is intentionally off for
  the first boot. Android therefore boots on the exact V4 legacy-LRU reclaim
  path.
- MGLRU can be enabled after Android is stable with:

  ```sh
  echo 1 > /sys/kernel/mm/lru_gen/enabled
  ```

- Android userspace `lmkd`, PSI and MEMCG remain enabled. The legacy in-kernel
  lowmemorykiller remains disabled.
- The V7 ZSTD/forced-ZRAM profile is absent. ZRAM uses the V4/ROM LZ4 path.
- V4 KernelSU-Next manual hook and SUSFS configuration are retained. The
  longuirom automatic hook and Try Umount are not part of this diagnostic.
- V4 frequency-only CPU targets and EROFS remain unchanged.
- V4 stock thermal policy is retained. The V7 patch that moved CPU cooling to
  65 C is absent.

## Why this build exists

V7 introduced MGLRU, forced ZRAM/ZSTD and a replacement KernelSU hook in the
same boot. It reached Android and then froze, so compile success cannot identify
which runtime subsystem failed. V9 isolates MGLRU while keeping its core off
during boot. If V9 boots, the user can enable MGLRU at runtime and capture the
failure without changing ZRAM or KernelSU.

This is a diagnostic kernel. A successful CI build proves compilation and
linkage only; device boot and runtime MGLRU still require phone testing.
