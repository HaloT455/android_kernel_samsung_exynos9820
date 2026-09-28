#!/system/bin/sh
# One read-only snapshot. No settings, service restarts or swap changes.
if [ "$(id -u)" != 0 ]; then
    echo 'Run with su: su -c "sh /data/local/tmp/collect-v9r5.sh"'
    exit 1
fi
section() { printf '\n===== %s =====\n' "$1"; }
section 'Time and kernel'
date '+%Y-%m-%dT%H:%M:%S%z'
uname -a
cat /proc/uptime
getprop ro.build.fingerprint
getprop sys.boot_completed
section 'CPU and schedutil'
cat /sys/devices/system/cpu/online
for p in /sys/devices/system/cpu/cpufreq/policy*; do
    [ -d "$p" ] || continue
    echo "$p"
    for a in related_cpus scaling_governor scaling_min_freq scaling_max_freq scaling_cur_freq stats/time_in_state schedutil/up_rate_limit_us schedutil/down_rate_limit_us; do
        [ -r "$p/$a" ] && { echo "$a"; cat "$p/$a"; }
    done
done
section 'MGLRU, ZRAM, memory pressure, lmkd'
for p in /sys/kernel/mm/lru_gen/enabled /sys/kernel/mm/lru_gen/min_ttl_ms /proc/swaps /proc/meminfo /proc/pressure/memory /proc/vmstat; do
    echo "$p"; cat "$p" 2>&1
done
for p in /sys/block/zram*; do
    [ -d "$p" ] || continue
    echo "$p"
    for a in comp_algorithm max_comp_streams disksize mm_stat io_stat bd_stat backing_dev; do
        [ -r "$p/$a" ] && { echo "$a"; cat "$p/$a"; }
    done
done
pidof lmkd
getprop init.svc.lmkd
section 'Battery counters'
for a in capacity status temp voltage_now current_now charge_counter charge_full charge_full_design cycle_count; do
    p="/sys/class/power_supply/battery/$a"
    [ -r "$p" ] && { echo "$a"; cat "$p"; }
done
section 'Thermal zones'
for p in /sys/class/thermal/thermal_zone*; do
    [ -r "$p/type" ] && { echo "$p"; cat "$p/type" "$p/temp"; }
done
section 'Wake sources (only if already mounted)'
cat /sys/kernel/debug/wakeup_sources 2>&1
section 'CPU snapshots'
timeout 10 top -b -n 2 -d 2
section 'Power'
timeout 15 dumpsys power
section 'Bluetooth'
timeout 15 dumpsys bluetooth_manager
section 'Wi-Fi'
timeout 15 dumpsys wifi
section 'Audio'
timeout 15 dumpsys media.audio_flinger
section 'Battery history/statistics'
timeout 20 dumpsys batterystats
section 'Recent Android logs'
timeout 15 logcat -b all -d -v threadtime -t 2500
section 'Kernel log'
dmesg
section 'End time'
date '+%Y-%m-%dT%H:%M:%S%z'
cat /proc/uptime
