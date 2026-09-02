# ALice S10+ MGLRU / 3OC / EROFS R2 TEST

Target: Galaxy S10+ Exynos 9820 (`beyond2lte`, EUR OPEN). This is an
experimental, device-specific boot image and has not been validated on phone.

| Area | R2 setting |
| --- | --- |
| Reclaim | Multi-Gen LRU is built in and enabled by default. |
| Android memory killer | PSI and MEMCG remain enabled for userspace `lmkd`; the legacy in-kernel Android LMK is disabled. |
| ZRAM | `zram0` is forced to 2560 MiB and ZSTD when userspace initializes it, permits six concurrent compression/decompression operations, and has no writeback path. |
| Filesystem | EROFS is built in with compressed-file support, xattrs, POSIX ACLs and security labels. Existing EROFS/ext4 fstab fallback entries are preserved; no partition is reformatted. |
| CPU0-3 | Requests the exact firmware CAL OPP at 2,106,000 kHz. |
| CPU4-5 | Requests the exact firmware CAL OPP at 2,400,000 kHz. |
| CPU6-7 | Requests the exact firmware CAL OPP at 2,912,000 kHz. |
| OC validation | A target is exposed only if the Exynos CAL rate table contains that exact rate with a non-zero ASV voltage. A rejected cluster retains its existing ceiling. No voltage or table is copied from another SoC. |
| Governor | EMS/EAS plus schedutil remains dynamic; the CPUs are not locked at maximum frequency. Default transition limits are 2 ms up and 8 ms down. |
| CPU thermal policy | The first CPU cooling action starts at 65 C. Battery, charging, GPU, hotplug and higher emergency protections remain independent. |
| KernelSU | The pinned KernelSU-Next legacy integration and manual hooks are preserved. |
| Ramdisk | The supplied JDK V10 `/init` CPU/GPU/bus wrapper is removed and its native `init.real` is restored as `/init`. |
| DTBO | The supplied matching DTBO is not modified. |

## Runtime verification

After the first successful boot, verify which firmware OPPs were accepted:

```sh
adb shell "su -c 'dmesg | grep -E \"ALice OC|ALice OPP|CPU cooling onset|first CPU frequency cap\"'"
adb shell "su -c 'for p in /sys/devices/system/cpu/cpufreq/policy*; do echo ===$p===; cat $p/scaling_available_frequencies $p/scaling_max_freq; done'"
adb shell "su -c 'cat /sys/kernel/mm/lru_gen/enabled; cat /sys/block/zram0/comp_algorithm; cat /sys/block/zram0/disksize; cat /sys/block/zram0/max_comp_streams; pidof lmkd; ls -ld /sys/module/lowmemorykiller 2>&1'"
```

The selected ZRAM compressor is shown in brackets. The expected values are
`[zstd]`, `2684354560`, and `6`. MGLRU core should report enabled. A frequency
target is not considered active until both the boot log and cpufreq sysfs show
it on the phone.

Always keep the supplied original boot image available for recovery before
testing this build.
