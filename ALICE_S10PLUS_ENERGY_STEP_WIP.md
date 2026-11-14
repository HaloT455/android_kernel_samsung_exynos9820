# ALice S10+ Exynos9820 — EMS energy_step kernel branch (EXPERIMENTAL)

**Device:** Galaxy S10+ Exynos 9820, beyond2lte, CPU0–3 Cortex-A55, CPU4–5 Cortex-A75, CPU6–7 Exynos M4.

**Branch:** `alice-s10plus-v9r2-ems-energy-step-20261114`, based on the V9R2 MGLRU + LZ4KD branch.

## Source implementation
- On the S10+ configuration, **`CONFIG_CPU_FREQ_DEFAULT_GOV_ENERGY_STEP=y`** and `CONFIG_CPU_FREQ_GOV_ENERGY_STEP=y`; the default schedutil governor choice is disabled.
- The registered CPUFreq governor is **`energy_step`**, not `schedutil`.
- It chooses frequency using existing Exynos9820 Samsung EMS **capacity/power operating-point tables** (`ems_pick_energy_step`), with a utilization-based fallback before the EMS table is initialized.
- Keeping existing `sugov_*` functions and `CONFIG_CPU_FREQ_GOV_SCHEDUTIL=y` is an **internal kernel/Android ABI requirement**, not a second running schedutil governor.
- CPUFreq parser maps userspace requests for `schedutil` to the new `energy_step`, because vendor Android init scripts may request schedutil.
- **EAS/EMS scheduling is retained**, since EAS assigns tasks to CPU clusters whereas CPUFreq governors select their clocks.
- V9R2's MGLRU, KernelSU/SUSFS, ZRAM LZ4KD, PSI, Exynos NPU and stock thermal protections are retained.

## Precise technical qualification
This is an **Exynos9820-specific EMS OPP energy-step governor implementation**, not a verbatim backport of Samsung Exynos2100's ~43 KB `kernel/sched/ems/energy_step.c`, which expects a different kernel scheduler/EMS API. It is not honest to call the original Exynos2100 governor directly supported without deeper porting.

## Build and testing
The GitHub workflow `.github/workflows/alice-v9r2-ems-energy-step.yml` verifies a successful kernel build and requires `energy_step` in vmlinux, EMS picker symbol, `CONFIG_CPU_FREQ_DEFAULT_GOV_ENERGY_STEP=y`, MGLRU, and LZ4KD. **Source changes are not proof of stability**.

Before using any image: verify CPU policies on device, test light/bursty load, RT/DL, CPU hotplug, suspend, GPU and CPU temperature, throttling, battery drain, Wi-Fi stability, and back up original boot. 63°C remains a thermal throttling *target*, not a guaranteed maximum; stock thermal safety has not been disabled.

Use after flashing a verified compatible image:
```sh
adb shell 'for p in /sys/devices/system/cpu/cpufreq/policy*; do echo "$p: $(cat "$p/scaling_governor" 2>/dev/null)"; done'
adb shell 'cat /sys/block/zram0/comp_algorithm'
```
Do not use `su` directly on the ThinkPad to obtain Android root. Use `adb shell su -c ...` with phone-side authorization if root access is required.
