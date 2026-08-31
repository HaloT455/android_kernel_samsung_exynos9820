# ALice S10+ UI1 / EMS / schedutil / EROFS — R1 test

## Inputs and scope

- Device: Galaxy S10+ Exynos9820, `beyond2lte`, identified from all ten supplied DTBO overlays.
- Requested source base: `HaloT455/android_kernel_samsung_exynos9820`, commit `5ae7dac3c4e0fb8e02dfcb9a63eaea47c5848114`.
- Primary policy reference: `HaloT455/dream2lte-45`, UI1 commit `887e9cc5e5678e6c8ee92bd9c8e0edecdaef4856`.
- Original boot kernel: Linux 4.14.356-openela-rc1-ArtisanKRNL-v3.1.0.1+, Android Clang r547379 / 20.0.0.
- The requested repository is newer than the kernel named in the boot (repository defconfig says v3.5.0_EOL). The original kernel's exact source commit is unknown. This is a rebuild from the requested repository, not a claim that all upstream changes since v3.1 have been isolated.
- The supplied boot and dtbo are retained as rollback files. Hardware testing is still required.
- **Requested OC is pending:** M4 2.9GHz / A75 2.5GHz / A55 2.1GHz are targets, not implemented clocks in this R1 baseline. The supplied boot/DTBO do not supply the running firmware's complete CAL/FVMAP/ASV data. No verified 2.5GHz A75 OPP has been established. Do not label this image as the completed OC build.

## Policy changes

| Component | R1 behavior |
| --- | --- |
| Primary algorithm | Port the UI1 CPU-cgroup hints and latest-request schedutil queue logic. Do not transplant S8+ CPU masks, frequency tables, watchdog or suspend patches. |
| UI hints | `top-app`: SPC boost 10 and prefer-idle; `foreground` / `foreground_window`: SPC boost 5. These are percentages of unused utilization capacity, not fixed frequency floors. |
| Native SchedTune | A mounted native controller takes precedence, even with boost zero. No double boosting. |
| Idle and battery | Sleeping / throttled groups do not retain fallback boosts; no new polling daemon, wake lock or forced offline rule. |
| Governor | Accept newer requests while work is pending; worker snapshots the latest target under the update lock. Preserve Samsung's worker placement and driver locking. |
| EMS signal | Retain normalized EMS load, RT load and freqvar result; remove the subsequent generic-util overwrite. |
| Energy costing | Account for schedutil's 25% OPP headroom and use each cluster's actual highest-OPP capacity when saturated. This is an estimate, not a measured energy model. |
| Rate limits | 2ms up / 8ms down, including native freqvar initialization. UI1 used 2.5ms / 8ms on S8+; the S10 freqvar tables use whole milliseconds. Runtime controls remain writable. |
| CPU heat | Apply software cooling onset at 65°C after firmware ECT parsing, so a DT-only edit cannot be overwritten by ECT. BIG/MID allocator target temperatures and higher safety trips remain unchanged; LITTLE retains its frequency-cap table with first effective cap at 65°C. |
| Other protection | Battery, charger, skin limits, GPU, hardware thermal protection, hotplug safety and emergency shutdown remain in force. |
| EROFS | Preserve built-in EROFS with LZ4 decompression, xattrs, POSIX ACL and SELinux labels; retain original EROFS/ext4 fallback fstab entries. EROFS was already enabled in the supplied boot and repository. No partition is reformatted. |
| Memory | Preserve original memory configuration except disable zram writeback/LRU writeback to UFS. No SimpleLMK port and no new swapfile. Android may still have its own swap configuration; check `/proc/swaps`. |
| Root / security | Preserve the original extracted KSU configuration, manual hooks, SELinux configuration and pinned repository submodule. SUSFS remains disabled as in the supplied boot. |
| Hardware | No CPU/GPU OPP overclock, voltage, ASV, cpuset or DTBO change. |
| OC evidence | Log the actual CAL frequency and FVMAP voltage table once at CPUFreq initialization, including filtered entries. The read-only collection script captures those lines and the running base DTB, when available, for the next OC change. |

65°C is the onset of thermal regulation, not a guarantee that measured temperature never exceeds 65°C or that every CPU is forced to its maximum at 65°C. Below onset, schedutil may request the full supported range when load warrants it. Battery/charger/firmware safety limits may still restrict clocks. Raising onset can increase heat and battery consumption during sustained load.

## Required ramdisk correction

The supplied `/init` is a small custom `JDK V10` executable, not native Android init. Its embedded strings describe M4-gated A75 operation, forced M4/A75 offline on screen-off and CPU/GPU/bus frequency writes. Keeping it would conflict with autonomous EMS/schedutil policy.

The repacker restores the already-supplied `/init.real` byte-for-byte as `/init`, removes the wrapper and the redundant `/init.real` entry, and preserves every other CPIO entry and both fstab files. Boot addresses, command line, OS version, patch level and board field are retained. The Android boot-v1 SHA1 ID is recalculated. The output stays within the supplied 57,671,680-byte image size; unknown signed/nonzero trailers cause the repacker to refuse the input.

## Build and checks

Requirements: Android Clang `clang-r547379`, make, GCC/host compiler, flex, bison, m4, bc, cpio, xz, Perl, OpenSSL development headers, Python 3. Initialize the pinned `KernelSU-Next` submodule without changing its commit. Its full history and tags are required: this checkout must report 2,982 commits, tag `v3.2.0-legacy`, and KernelSU version 33132. A shallow checkout incorrectly changes the compiled KernelSU version; the build script refuses it.

```sh
git submodule update --init KernelSU-Next
# If shallow, fetch the history before building:
# git -C KernelSU-Next fetch --unshallow --tags
CLANG_DIR=/absolute/path/clang-r547379 JOBS=8 bash scripts/alice_build.sh
python3 scripts/test_cpu_ui_hints.py
python3 scripts/test_schedutil_work.py
python3 scripts/test_alice_energy.py
python3 scripts/test_alice_thermal.py
python3 scripts/alice_verify_config.py out-alice/.config
python3 scripts/alice_repack.py --boot /path/boot-original.img \
  --dtbo /path/dtbo-original.img --kernel out-alice/arch/arm64/boot/Image \
  --output /path/ALice_S10Plus_UI1_EAS65_R1_TEST.img
```

Host tests compile actual modified C functions with mocks and UBSan. They check UI group inheritance/lifetime, native precedence, idle and quota behavior, request coalescing and driver interleavings, rate limits, EMS signal preservation, saturated energy costing and CPU-only thermal boundaries. They do not prove real SMP, suspend, driver, frame-time, power or hardware-temperature behavior.

## Device trial and recovery

1. Only trial on the S10+ `beyond2lte` associated with these inputs. Do not flash to S8+, S9+, Note10+, S10e, S10 or Snapdragon models.
2. Keep a working recovery/download route and backups of the currently working boot/dtbo and important data. The uploaded rollback boot is useful only if it actually boots the current ROM; that has not been verified remotely.
3. The `FILES.zip` bundle is a normal archive, not a recovery installer. Extract it. Flash only the candidate `.img` to **Boot** using a compatible recovery's image-flash function. Do not flash to Recovery, System, Vendor or DTBO.
4. Leave DTBO untouched: the included original is byte-identical and only for reference/rollback. No wipe or filesystem conversion is required.
5. Test first boot, KernelSU, touch, mobile/Wi-Fi, camera, charging/unplugging, repeated screen-off/wake and idle on battery before sustained loads. Stop if it hangs, reboots, becomes unusually hot or loses functionality.
6. On failure restore the previous working boot using recovery/download tools. Do not erase data to try to fix a kernel mismatch.

Useful read-only checks after boot:

```sh
adb shell su -c 'uname -a; cat /proc/swaps; cat /proc/sys/kernel/sched_cpu_ui_hints'
adb shell su -c 'cat /sys/devices/system/cpu/cpufreq/policy*/scaling_governor'
adb shell su -c 'cat /sys/devices/system/cpu/cpufreq/policy*/schedutil/*rate_limit*'
adb shell su -c 'dmesg | grep -E "CPU cooling onset|first CPU frequency cap|erofs"'
adb shell su -c 'cat /sys/class/thermal/thermal_zone*/type /sys/class/thermal/thermal_zone*/temp'
```

Compare UI frame times and battery behavior against the original under similar app, brightness, temperature and network conditions. Do not assume a faster clock or successful compilation proves smoother UI or longer battery life.

## Complete the requested OC only after firmware inspection

`exynos-acme.c` obtains actual rates from CAL and voltage entries from FVMAP; changing a Device Tree `max-freq` alone cannot create a missing OPP. M4 also uses HIU/HAFM levels and firmware limits. Its nominal DT maximum is not its final boost limit. Any OC patch must keep CPUFreq, HIU, ASV voltage, DVFS constraints and energy/cooling tables consistent, and requires device testing. Do not invent a 2.5GHz A75 rate or write directly to PLL registers without the corresponding firmware evidence.

Run the collector on the currently working kernel first; it does not require flashing R1. If `ALice OPP` lines are unavailable, the output says so. Those extra lines become available only after a successful R1 trial. Do not trial a new kernel solely to collect logs if a known recovery path is unavailable.

```sh
adb push scripts/alice_collect_device.sh /data/local/tmp/alice_collect_device.sh
adb shell su -c 'sh /data/local/tmp/alice_collect_device.sh /data/local/tmp/alice-evidence'
adb pull /data/local/tmp/alice-evidence
```

The collector only reads sysfs/procfs and filtered kernel logs; it writes its output directory but does not change governors, clocks, voltages, thermal controls, mounts or partitions. A timestamped default output path avoids overwriting an earlier report; an explicitly existing output path is refused. Review the report before sharing it. Missing permissions/files are recorded, not worked around by disabling security.
