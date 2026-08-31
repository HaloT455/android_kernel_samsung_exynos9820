#!/system/bin/sh
# Read-only kernel evidence; only the report directory is written.
set -eu
umask 077
out=${1:-/data/local/tmp/alice-evidence-$(date +%Y%m%d-%H%M%S)}
case "$out" in
  /*) ;;
  *) printf '%s\n' 'Use an absolute output directory.' >&2; exit 1 ;;
esac
if [ "$(id -u)" != 0 ]; then
  printf '%s\n' 'Run through su; no clocks or security settings will be changed.' >&2
  exit 1
fi
if [ -e "$out" ]; then
  printf '%s\n' 'Output already exists; choose a new directory.' >&2
  exit 1
fi
mkdir -p "$out"

read_node() {
  printf '\n[%s]\n' "$1"
  if [ -r "$1" ]; then
    cat "$1" || printf '%s\n' 'READ FAILED'
  else
    printf '%s\n' 'UNAVAILABLE'
  fi
}

{
  uname -a
  for prop in ro.product.device ro.product.model ro.boot.hardware ro.build.version.release ro.build.version.incremental; do
    printf '%s=' "$prop"
    getprop "$prop"
  done
  for policy in /sys/devices/system/cpu/cpufreq/policy*; do
    [ -d "$policy" ] || continue
    for node in related_cpus affected_cpus cpuinfo_min_freq cpuinfo_max_freq scaling_min_freq scaling_max_freq scaling_available_frequencies scaling_governor scaling_cur_freq stats/time_in_state schedutil/up_rate_limit_us schedutil/down_rate_limit_us; do
      read_node "$policy/$node"
    done
  done
  read_node /proc/sys/kernel/sched_cpu_ui_hints
  read_node /proc/swaps
  for zone in /sys/class/thermal/thermal_zone*; do
    [ -d "$zone" ] || continue
    read_node "$zone/type"
    read_node "$zone/temp"
    for trip in "$zone"/trip_point_*_temp "$zone"/trip_point_*_type; do
      [ -r "$trip" ] && read_node "$trip"
    done
  done
} > "$out/device.txt" 2>&1

# Restrict the shared log to CPU clock, allocator and ASV evidence.
if dmesg 2> "$out/dmesg-access.txt" | grep -E 'ALice OPP:|CPUFREQ of domain|exynos-hiu:|CPU cooling onset|first CPU frequency cap|ASV_TABLE|asv_table_ver' > "$out/clock-thermal-log.txt"; then
  :
else
  printf '%s\n' 'No matching lines, or dmesg access unavailable.' >> "$out/dmesg-access.txt"
fi

if [ -r /sys/firmware/fdt ]; then
  cat /sys/firmware/fdt > "$out/running.dtb"
else
  printf '%s\n' '/sys/firmware/fdt unavailable; no partition was read.' > "$out/dtb-unavailable.txt"
fi

# Read an already exposed ECT dump; do not mount debugfs or trigger a dump write.
if [ -r /sys/kernel/debug/ect/all_dump ]; then
  cat /sys/kernel/debug/ect/all_dump > "$out/ect.txt"
fi
printf '%s\n' 'OC targets 2900000/2500000/2100000 kHz are NOT enabled by this script.' \
  'Review outputs before sharing. The running DTB may include device identifiers.' \
  'If ALice OPP lines are absent, only currently exposed CPUFreq rates were captured.' > "$out/README.txt"
printf 'Report written to %s\n' "$out"
