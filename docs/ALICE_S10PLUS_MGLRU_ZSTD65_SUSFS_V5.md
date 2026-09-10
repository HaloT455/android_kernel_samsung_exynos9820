# ALice S10+ MGLRU / ZSTD / 65C / SUSFS V5 TEST

Target: Galaxy S10+ Exynos9820 (`beyond2lte`, SM-G975F).

V5 starts from the CI-passing V4 branch and adds only the requested memory,
thermal and SUSFS options. The voltage-untouched three-cluster OC remains
unchanged.

| Area | V5 setting |
| --- | --- |
| CPU0-3 | Request 2,106,000 kHz only when CAL exposes the exact rate. |
| CPU4-5 | Request 2,400,000 kHz only when CAL exposes the exact rate. |
| CPU6-7 | Request 2,912,000 kHz only when CAL exposes the exact rate. |
| Voltage | No voltage, ASV or foreign SoC table is changed or copied. |
| Reclaim | Multi-Gen LRU is built in and enabled by default. |
| Android memory killer | PSI/MEMCG remain enabled for userspace lmkd; legacy in-kernel Android LMK remains disabled. |
| ZRAM | zram0 is forced to 2560 MiB when userspace initializes it, selects ZSTD and limits compression/decompression concurrency to six. |
| ZRAM writeback | Disabled; no zram writeback path to UFS. |
| Thermal | First CPU frequency cooling action for BIG/MID/LITTLE begins at 65 C after ECT is loaded. Battery, charging, GPU, hotplug and emergency protections are unchanged. |
| Governor | EMS/EAS and schedutil remain dynamic; maximum frequency is not locked. |
| Filesystem | EROFS support remains built in. No partition is reformatted. |
| Root | KernelSU-Next with SUSFS v2.2.0; SUSFS TRY_UMOUNT is enabled. |
| Ramdisk | Final packaging replaces the legacy JDK wrapper /init with the supplied native /init.real. |
| DTBO | The supplied matching DTBO is preserved byte-for-byte. |

## Runtime verification

```sh
adb shell "su -c 'cat /sys/kernel/mm/lru_gen/enabled; cat /sys/block/zram0/comp_algorithm; cat /sys/block/zram0/disksize; cat /sys/block/zram0/max_comp_streams; cat /proc/swaps; pidof lmkd; ls -ld /sys/module/lowmemorykiller 2>&1'"
adb shell "su -c 'dmesg | grep -E \"ALice zram|CPU cooling onset|first CPU frequency cap|ALice OC|ALice OPP\"'"
adb shell "su -c 'for p in /sys/devices/system/cpu/cpufreq/policy*; do echo ===$p===; cat $p/scaling_available_frequencies $p/scaling_max_freq; done'"
```

Expected ZRAM values are `[zstd]`, `2684354560` and `6`. The build and
package can be verified before flashing, but boot, stability, thermal behavior
and accepted CAL frequencies must be confirmed on the physical phone.
