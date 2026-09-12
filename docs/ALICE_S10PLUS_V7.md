# ALice S10+ V7 TEST

V7 starts from V4 commit `e8ad33ee31404ccfdd30ee0c9a508c36d95f79db`, the build reported by the device owner as booting. It does not inherit the V5 branch history.

| Area | V7 declaration |
|---|---|
| Device | Galaxy S10+ Exynos 9820, `beyond2lte` |
| CPU clocks | V4 frequency-only targets: M4 2912 MHz, A75 2400 MHz, A55 2106 MHz when the exact CAL rate exists |
| Voltage | Unchanged; no voltage-table uplift |
| Scheduler | EMS/EAS + schedutil, UI-oriented V4 policy |
| CPU thermal | CPU cooling/capping begins at 65°C; higher emergency, battery, charging and GPU protection remain unchanged |
| MGLRU | Built in and enabled; statistics/debug overhead disabled |
| LMKD | Android userspace `lmkd` and PSI/MEMCG remain; legacy kernel lowmemorykiller stays disabled |
| ZRAM | `zram0` is forced to 4 GiB when initialized, ZSTD default, six concurrent compression/decompression streams |
| ZRAM writeback | Disabled, including LRU writeback to UFS |
| EROFS | Built in and retained from V4; no partition formatting |
| KernelSU | `longuirom/KernelSU` branch `fork`, pinned at `b7d830918d863eaa88581fc88114065cc2d3e6b4`, kernel ABI 32628 |
| KSU hook | Automatic syscall-table hook (`KSU_TAMPER_SYSCALL_TABLE`); kprobe, branch-link and manual-hook modes are off |
| SUSFS | V2.2.0 NON-GKI bridge enabled |
| Try Umount | SUSFS Try Umount enabled; longuirom native kernel-umount feature retained |
| DTBO | No source DTBO edits; final test package must use the exact matching DTBO supplied by the owner |

The build passing GitHub Actions proves compilation, linkage and packaging only. Physical boot, root enrollment, thermals and overclock stability still require a device test.

Matching manager: [KernelSU v3.3.0-28 / ABI 32629](https://github.com/backslashxx/KernelSU/releases/download/v3.3.0-28/KernelSU_v3.3.0-28_32629-release.apk). It is signed for the manager certificate accepted by this fork and is one ABI revision newer than the pinned kernel.
