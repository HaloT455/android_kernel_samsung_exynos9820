# ALice S10+ V9R5 TEST: governor correctness and bounded ZRAM concurrency

Base: V9R2 e5d1d15b2f2705253ee0ef685c1014c0c49df11a.
Branch: agent/beyond2lte-v9r5-balanced. V4 and V9R2 branches are unchanged.
Device: Galaxy S10+ Exynos9820, beyond2lte. This is not an M51 kernel.

## Evidence and limits

The user reports Wi-Fi/Bluetooth audio pauses and faster battery drain on V9R2.
The supplied log predates a precisely marked audio pause. It shows successful
Wi-Fi runtime suspend/resume cycles, with no captured firmware hang proving the
cause of the reported pause. V4 and V9R2 use the same radio driver sources.
Two short YouTube tests with MGLRU off/on showed similar percentage loss;
neither test establishes the cause of all battery drain.

This is a test build, not a claim of measured battery improvement or a proven
radio/ROM fix. M51-like battery life cannot be inferred from a successful build.

## Changes

| Area | Change and reason |
| --- | --- |
| schedutil queued work | Accept a newer target while work is queued; snapshot the target and clear work_in_progress together under update_lock. An update during a transition queues another run, so an idle downscale is not discarded. Follows the locking pattern in upstream Linux v4.19. |
| schedutil rate cache | Invalidate cached raw frequency if the up/down rate gate rejects it; otherwise a later identical raw request can retain the wrong previous target. |
| I/O boost | Reset boost after an idle tick even if the next event is IOWAIT. Sparse I/O starts from minimum instead of doubling stale boost. Follows upstream v4.19 IOWAIT reset semantics. |
| Audio RT load | Retain V4's effective CFS/SchedTune signal and add measured RT load, which the old final assignment discarded. Remove the overwritten EMS/freqvar calculation; do not introduce its previously ineffective low-frequency boost. EMS placement and active-ratio adjustment stay in place. |
| ZRAM | CONFIG_ZRAM_COMPRESSION_CONCURRENCY=4: at most four simultaneous codec calls per device, with short shared locks only around crypto calls. Per-CPU buffers and hotplug lifecycle remain intact. No lock spans zsmalloc or allocation. This is a concurrency cap, not affinity to CPUs 0-3 or a background four-thread daemon. It may reduce throughput and needs device measurements. |
| ZRAM sysfs | max_comp_streams reports min(online CPUs, 4). Legacy writes >=4 are accepted and capped at 4; requests below the build-time limit return EOPNOTSUPP. The original per-CPU behavior remains when the new config is zero. |
| Bluetooth wake tails | Correct __pm_wakeup_event arguments from HZ/2 and HZ (125/250 ms with HZ=250) to the intended 500/1000 ms. This targets premature sleep; it lengthens the tail, so it is a reliability fix, not a battery-saving claim. |
| Radio logging | Move seven routine Wi-Fi runtime-PM/queue state messages and two Bluetooth wake transition logs out of the default error/info stream. Keep actual failure messages and power-saving logic. |
| Fingerprint debug | Make the debug-only status timer deferrable, so periodic diagnostics do not wake an otherwise idle CPU. Fingerprint IRQ and authentication logic are unchanged. |

## Retained profile

- MGLRU enabled by default, runtime capability mask expected 0x0001. No new
  page-table walking capability, min_ttl or swappiness policy is imposed.
- Android lmkd, PSI and MEMCG enabled; legacy kernel LMK disabled.
- ZRAM size controlled by ROM (8 GiB previously observed), LZ4 default.
  Writeback support is unchanged. No swapoff, reset or resizing at runtime.
- KernelSU longuirom ABI 32567 pinned to
  7bd071c11f5a4d22729d73179d149493a6362a26, automatic syscall-table hook,
  SUSFS 2.2 and Try Umount; V9R2 sucompat allowlist fix retained.
- EROFS enabled. V4 frequency-only OC M4 2.912 / A75 2.400 / A55 2.106 GHz,
  existing voltages, frequency limits and thermal protections retained.
  This build does not introduce the failed V7 65-degree thermal policy.
- Existing 4 ms freqvar rate tables retained; no forced maximum/minimum clock,
  CPU offline policy, network power-save disable, or periodic tuning daemon.
- No services.jar or EPIC framework modification bundled in the boot image.
  The separately investigated AIDL/HIDL mismatch requires a separate ROM test.

## Validation

CI compiles the complete ARM64 kernel and checks linked MGLRU/SUSFS symbols,
KSU profile, LMKD prerequisites, EROFS, LZ4 and the concurrency cap. Host tests
compile the actual changed governor and codec-wrapper functions with mocked
kernel primitives: sparse/burst IOWAIT, rate-cache retry, queued coalescing,
in-flight downscale and policy-limit refresh. Eight pthread callers execute
3200 wrapper calls, including codec failures, and verify at most four active
calls with no leaked gate on failure. These tests do not emulate ARM64 memory
ordering, real compression, radio firmware, suspend or Android boot.

Packaging must use the working V9R2 ramdisk/header/DTB and replace only the
kernel payload, retaining its DTBO byte-for-byte. The repository-ramdisk boot
produced by build.sh is a CI intermediate, not the phone deliverable.

## Phone acceptance

1. Boot the TEST image, verify uname contains V9R5, root works, lmkd is running,
   lru_gen/enabled is 0x0001 and max_comp_streams is 4 with all CPUs online.
2. Check Wi-Fi plus Bluetooth audio with screen on and off, then local audio
   over Bluetooth with Wi-Fi off. Record the exact time of any pause.
3. Repeat the same unplugged YouTube workload/brightness/network for 30-60
   minutes and an unplugged screen-off interval. Compare to V4 under the same
   conditions; do not use an ADB/USB-powered idle interval as a battery test.
4. If pauses, new heat, instability or worse drain occur, restore the previous
   working boot and supply the timestamped log collected by the supplied tool.

Primary reference for governor queue and IOWAIT handling:
https://github.com/torvalds/linux/blob/v4.19/kernel/sched/cpufreq_schedutil.c
