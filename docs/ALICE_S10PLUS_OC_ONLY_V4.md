# ALice S10+ OC + SUSFS V4 TEST

Target: Galaxy S10+ Exynos9820 (`beyond2lte`, SM-G975F).

This diagnostic branch starts from ArtisanKRNL v3.1.0.1 commit
`585634bd018ba961774b32d9f2bea340d4b60521`, matching the source generation of
the user's currently booting kernel.  It intentionally does not inherit the R2
MGLRU, ZRAM, scheduler or thermal patches.

## Functional changes

- CPU0-3 (A55): expose 2,106,000 kHz when that exact rate exists in CAL.
- CPU4-5 (A75): expose 2,400,000 kHz when that exact rate exists in CAL.
- CPU6-7 (M4): expose 2,912,000 kHz when that exact rate exists in CAL.
- No voltage/ASV value is added, changed, offset or copied from another SoC.
- If an exact rate is absent, that cluster retains its stock ceiling.
- Boot and resume frequencies remain stock; schedutil still selects frequency
  dynamically inside the resulting table.

- SUSFS v2.2.0 is enabled through the KernelSU-Next bridge patch stored in
  `patches/alice-ksunext-susfs-v2.2.patch`.  `KSU_SUSFS_TRY_UMOUNT` remains off
  for this first boot test; the other SUSFS interfaces from the source profile
  are enabled.

## Baseline features retained, not newly ported

- Built-in EROFS support from ArtisanKRNL v3.1.0.1.
- PSI with Android userspace lmkd; legacy kernel lowmemorykiller disabled.
- KernelSU-Next is pinned to `fd093e8b879063aeb0192a3959b0652101ded623` and the
  SUSFS bridge is applied during the build.

The source build can be verified before flashing, but boot, stability and the
three requested rates must still be confirmed on the physical phone.
