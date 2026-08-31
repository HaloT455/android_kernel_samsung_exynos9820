#!/usr/bin/env python3
"""Reject a build that silently drops required device/profile features."""
import sys
from pathlib import Path

values = {}
for line in Path(sys.argv[1]).read_text().splitlines():
    if line.startswith("CONFIG_") and "=" in line:
        key, value = line.split("=", 1)
        values[key] = value
required = (
    "SOC_EXYNOS9820", "SCHED_EMS", "SIMPLIFIED_ENERGY_MODEL", "SCHED_TUNE",
    "FAIR_GROUP_SCHED", "SCHED_CPU_UI_HINTS", "ALICE_EAS_BALANCED",
    "ALICE_A75_2400", "ALICE_ZRAM_PROFILE", "CRYPTO_ZSTD",
    "CPU_FREQ_DEFAULT_GOV_SCHEDUTIL", "CPU_FREQ_GOV_SCHEDUTIL",
    "EROFS_FS", "EROFS_FS_XATTR", "EROFS_FS_POSIX_ACL", "EROFS_FS_SECURITY",
    "EROFS_FS_ZIP", "ZRAM", "KSU", "KSU_MANUAL_HOOK",
    "TOUCHSCREEN_SEC_TS_Y771", "SENSORS_SSP_BEYOND", "SECURITY_SELINUX",
)
for key in required:
    assert values.get("CONFIG_" + key) == "y", key
for key in ("ZRAM_WRITEBACK", "ZRAM_LRU_WRITEBACK", "KSU_SUSFS", "SCHED_WALT"):
    assert values.get("CONFIG_" + key) != "y", key
print("Required device, UI1, EMS, schedutil, EROFS and RAM-only zram options present")
