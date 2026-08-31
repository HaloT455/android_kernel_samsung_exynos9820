#!/usr/bin/env python3
"""Test actual EMS OPP costing and schedutil's EMS/RT signal preservation."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT/"kernel/sched/ems/energy.c").read_text()
start = source.index("unsigned int calculate_energy(")
energy = source[start:source.index("\n}", start)+2]
source = (ROOT/"kernel/sched/cpufreq_schedutil.c").read_text()
start = source.index("static void sugov_get_util(")
get_util = source[start:source.index("\n}", start)+2]
unit = r'''
#include <assert.h>
#include <stdbool.h>
#include <limits.h>
#include <stdio.h>
#define NR_CPUS 2
#define SCHED_CAPACITY_SCALE 1024
#define SCHED_CAPACITY_SHIFT 10
#define CONFIG_SCHED_EMS 1
#define IS_ENABLED(x) 1
#define unlikely(x) (x)
#define per_cpu(x,cpu) ((x)[cpu])
#define min_t(type,a,b) ((type)(a)<(type)(b)?(type)(a):(type)(b))
#define min(a,b) ((a)<(b)?(a):(b))
#define for_each_cpu(cpu,mask) for(cpu=0;cpu<2;cpu++) if((mask)&(1U<<cpu))
#define cpu_active_mask 3U
#define cpu_coregroup_mask(cpu) 3U
#define cpumask_first(mask) 0
struct task_struct { int sse, cpu; };
struct energy_state { unsigned long cap,cap_s,power,power_s; };
struct energy_table { int nr_states; struct energy_state *states; };
static struct energy_state states[] = {{100,100,10,10},{200,200,40,40}};
static struct energy_table energy_table[2] = {{2,states},{2,states}};
static bool ready=true;
static unsigned long loads[2], ems_util=310, rt_util=50, generic_util=75;
static bool get_energy_table_status(void) { return ready; }
static unsigned long ml_task_attached_cpu_util(int c,struct task_struct *p) { return loads[c]; }
static unsigned long ml_cpu_util_wake(int c,struct task_struct *p) { return loads[c]; }
static unsigned long __ml_cpu_util(int c,int sse) { return sse?0:loads[c]; }
static unsigned long ml_cpu_util_ratio(int c,int sse) { return __ml_cpu_util(c,sse)*1024/200; }
static unsigned long ml_task_util_est(struct task_struct *p) { return 0; }
#define task_cpu(p) ((p)->cpu)
static unsigned long arch_scale_cpu_capacity(void *unused,int cpu) { return 512; }
static unsigned long sched_get_rt_rq_util(int cpu) { return rt_util; }
static unsigned long ml_boosted_cpu_util(int cpu) { return ems_util; }
static unsigned long boosted_cpu_util(int cpu) { return generic_util; }
static unsigned long freqvar_boost_vector(int cpu,unsigned long u) { return u*11/10; }
static void part_cpu_active_ratio(unsigned long *u,unsigned long *max,int cpu) { }
'''
unit += energy + get_util + r'''
int main(void) {
    struct task_struct task={0,0}; unsigned long util,max;
    ready=false; assert(calculate_energy(&task,0)==UINT_MAX); ready=true;
    loads[0]=90;
    assert(calculate_energy(&task,0)==(90U*1024/200)*40); /* reserve headroom */
    loads[0]=190;
    assert(calculate_energy(&task,0)==(190U*1024/200)*40); /* highest OPP capacity */
    loads[0]=20;
    assert(calculate_energy(&task,0)==(20U*1024/100)*10);
    sugov_get_util(&util,&max,0);
    assert(util==396 && max==512); /* EMS + RT, then freqvar; no overwrite */
    ems_util=500; sugov_get_util(&util,&max,0); assert(util==512);
    puts("PASS: EMS headroom, cluster capacity saturation and governor signal path");
}
'''
with tempfile.TemporaryDirectory() as d:
    c,binary=Path(d)/"test.c",Path(d)/"test"
    c.write_text(unit)
    subprocess.run(["gcc","-std=gnu11","-O2","-Wall","-Wextra","-Werror",
                    "-Wno-unused-parameter","-Wno-unused-function","-fsanitize=undefined",
                    str(c),"-o",str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
