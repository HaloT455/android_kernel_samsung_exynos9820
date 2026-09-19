# ALice S10+ V9: KSU 32567 + SUSFS + dormant MGLRU

V9 starts directly from the phone-tested V4 commit
`e8ad33ee31404ccfdd30ee0c9a508c36d95f79db`. The V4 branch is unchanged.

## V9 profile

- CPU frequency-only OC remains the V4 profile: A55 2.106 GHz, A75 2.400 GHz,
  M4 2.912 GHz. Voltage tables remain unchanged.
- EROFS support remains enabled.
- MGLRU is backported and compiled with `CONFIG_LRU_GEN=y`, but starts
  disabled. Android therefore boots with the V4 legacy reclaim path. After a
  stable boot it can be enabled with:
  `echo 1 > /sys/kernel/mm/lru_gen/enabled`.
- Android userspace `lmkd`, PSI and MEMCG remain enabled. Legacy in-kernel
  lowmemorykiller remains disabled.
- No forced ZSTD or forced ZRAM size is present. ZRAM stays on the V4/ROM LZ4
  path.
- KernelSU is pinned to `longuirom/KernelSU` branch `32567b`, commit
  `7bd071c11f5a4d22729d73179d149493a6362a26`, ABI 32567.
- The automatic syscall-table hook is used for Linux 4.14. V4 manual KSU hook
  call sites remain inactive.
- SUSFS v2.2 NON-GKI and Try Umount are enabled. The integration follows the
  Linux 4.14 SUSFS patching model in `cyberc3dr/nGKI_Kernel_Build`; the V4
  tree already contains the corresponding kernel-side SUSFS 2.2 hooks, so V9
  merges the controller bridge into the pinned KernelSU source instead of
  reapplying the whole generic patch.
- V4 stock thermal policy remains. The V7 65 C thermal modification is absent.

## Test order

1. Flash the V9 boot image only. Keep the matching DTBO unchanged.
2. Confirm Android reaches the launcher and remains stable for several minutes.
3. Confirm KernelSU Manager reports kernel ABI 32567 and SUSFS.
4. Confirm MGLRU is initially off:
   `cat /sys/kernel/mm/lru_gen/enabled`.
5. Only then enable MGLRU:
   `echo 1 > /sys/kernel/mm/lru_gen/enabled`.

A successful CI build proves compilation and linkage only. Device boot, the
automatic hook and runtime MGLRU still require phone testing.
