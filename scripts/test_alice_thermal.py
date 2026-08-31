#!/usr/bin/env python3
"""Exercise the actual CPU-only onset transformation and allocator boundary."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def function(path, name):
    source = (ROOT / path).read_text()
    start = source.rfind("\nstatic ", 0, source.index(name + "(")) + 1
    return source[start:source.index("\n}", start) + 2]

unit = r'''
#include <assert.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#define IS_ENABLED(x) 1
#define min(a,b) ((a)<(b)?(a):(b))
#define dev_info(...) ((void)0)
#define dev_warn(...) ((void)0)
enum { THERMAL_TRIP_ACTIVE, THERMAL_TRIP_PASSIVE, THERMAL_TRIP_HOT,
       THERMAL_TRIP_CRITICAL };
struct thermal_trip { int type, temperature, hysteresis; };
struct __thermal_bind_params { unsigned int trip_id; unsigned long value; };
struct __thermal_zone {
    int ntrips, num_tbps;
    struct thermal_trip *trips;
    struct __thermal_bind_params *tbps;
};
struct params { char *governor_name; };
struct thermal_zone_device;
struct ops { int (*get_trip_temp)(struct thermal_zone_device *, int, int *); };
struct thermal_zone_device {
    const char *type; int trips, temperature, passive;
    struct __thermal_zone *devdata; struct params *tzp;
    struct ops *ops; void *governor_data;
};
struct exynos_tmu_data { struct thermal_zone_device *tzd; };
struct power_allocator_params { int trip_switch_on, trip_max_desired_temperature; };
static int allowed, allocated, reset;
static void reset_pid_controller(struct power_allocator_params *p,
                                 struct thermal_zone_device *tz) { reset++; }
static void allow_maximum_power(struct thermal_zone_device *tz) { allowed++; }
static int allocate_power(struct thermal_zone_device *tz, int temp)
{ assert(temp == 83000); allocated++; return 0; }
static int get_temp(struct thermal_zone_device *tz, int trip, int *out)
{ *out=tz->devdata->trips[trip].temperature; return 0; }
'''
unit += function("drivers/thermal/samsung/exynos_tmu.c", "exynos_tmu_cpu_cooling_onset")
unit += function("drivers/thermal/power_allocator.c", "power_allocator_throttle")
unit += r'''
int main(void) {
    struct thermal_trip original[] = {
        {0,20000,5000}, {0,55000,2000}, {1,83000,5000},
        {0,95000,5000}, {2,115000,5000}, {3,120000,5000}
    }, trip[6];
    struct __thermal_zone zone = {6,0,trip,0};
    struct params params = {"power_allocator"};
    struct ops ops = {get_temp};
    struct power_allocator_params pa = {1,2};
    struct thermal_zone_device tz = {"BIG",6,0,0,&zone,&params,&ops,&pa};
    struct exynos_tmu_data data = {&tz};
    const char *unchanged[] = {"G3D", "ISP", "battery", "skin", "usb"};
    for (unsigned int i=0; i<sizeof(unchanged)/sizeof(*unchanged); ++i) {
        memcpy(trip,original,sizeof(trip)); tz.type=unchanged[i];
        exynos_tmu_cpu_cooling_onset(&data);
        assert(!memcmp(trip,original,sizeof(trip)));
    }
    const char *cpu[] = {"BIG", "MID"};
    for (int c=0;c<2;c++) {
        memcpy(trip,original,sizeof(trip)); tz.type=cpu[c];
        exynos_tmu_cpu_cooling_onset(&data);
        assert(trip[1].temperature==65000 && trip[1].hysteresis==0);
        assert(!memcmp(trip+2,original+2,4*sizeof(*trip)));
        for (int t=20000;t<65000;t+=1000) {
            tz.temperature=t; allowed=allocated=reset=0;
            power_allocator_throttle(&tz,2);
            assert(allowed==1 && reset==1 && !allocated && !tz.passive);
        }
        tz.temperature=65000; allowed=allocated=0;
        power_allocator_throttle(&tz,2);
        assert(!allowed && allocated==1 && tz.passive);
        trip[2].temperature=64000; trip[1].temperature=50000;
        exynos_tmu_cpu_cooling_onset(&data);
        assert(trip[1].temperature==50000); /* keep a stricter safety target */
    }
    struct __thermal_bind_params maps[] = {
        {0,1950000},{1,1846000},{2,1742000},{3,1500000},{4,1000000},{5,500000}
    };
    memcpy(trip,original,sizeof(trip));
    trip[1].temperature=76000; trip[2].temperature=81000;
    zone.num_tbps=6; zone.tbps=maps; tz.type="LITTLE";
    params.governor_name="step_wise";
    exynos_tmu_cpu_cooling_onset(&data);
    assert(trip[1].temperature==65000 && trip[1].hysteresis==0);
    assert(trip[0].temperature==20000 && trip[2].temperature==81000);
    assert(!memcmp(trip+3,original+3,3*sizeof(*trip)));
    assert(maps[1].value==1846000);
    zone.tbps=0; exynos_tmu_cpu_cooling_onset(&data);
    puts("PASS: 65C onset, below-onset release, ECT-style caps, emergency and non-CPU isolation");
}
'''
with tempfile.TemporaryDirectory() as d:
    source, binary = Path(d)/"test.c", Path(d)/"test"
    source.write_text(unit)
    subprocess.run(["gcc","-std=gnu11","-Wall","-Wextra","-Werror",
                    "-Wno-sign-compare","-Wno-unused-parameter","-fsanitize=undefined",
                    str(source),"-o",str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
