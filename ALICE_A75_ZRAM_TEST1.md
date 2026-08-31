# ALice S10+ A75 2.4GHz + ZRAM TEST1

Experimental boot-kernel profile for the verified Galaxy S10+ Exynos9820
(`beyond2lte`, SM-G975F). It is based on ALice R1 plus the booted DIAG1.

## Changes from DIAG1

- CPU4-5 (Cortex-A75): permit the exact firmware OPP at 2,400,000 kHz only
  when device tree permits it and CAL returns that exact rate with a non-zero
  ASV voltage. Otherwise retain the stock ceiling.
- CPU0-3 (A55) and CPU6-7 (M4): unchanged.
- ZRAM0: ZSTD, 2.5 GiB (2,560 MiB), with at most six simultaneous compression
  or decompression operations. ZRAM writeback remains disabled.
- Retain DIAG1 debugfs so the first device test can verify the active table.
- Retain UI1/EMS/schedutil, CPU cooling onset at 65 C, EROFS, KernelSU and the
  native init ramdisk. DTBO is not modified.

This source has not yet proved that the phone can run the newly exposed OPP.
The firmware table is necessary evidence, not a stability guarantee. Test boot
first, then verify the frequency table and ZRAM before any benchmark.
