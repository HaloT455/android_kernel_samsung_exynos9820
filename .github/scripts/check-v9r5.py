#!/usr/bin/env python3
"""Host regression harness: compile the actual changed C functions.

Kernel locks/driver/crypto are substituted. This tests governor event ordering
and codec concurrency/error paths, not ARM64 boot, radio firmware or battery.
"""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]

def function(src, name):
    import re
    match = re.search(r'^(?:static )?(?:inline )?[\w *]+\b' + name + r'\([^;]*?\)\n\{', src, re.M)
    assert match, name
    start = match.start()
    pos = src.index('{', match.start())
    depth = 1
    end = pos + 1
    while depth:
        depth += (src[end] == '{') - (src[end] == '}')
        end += 1
    return src[start:end]

sg = (ROOT / 'kernel/sched/cpufreq_schedutil.c').read_text()
zc = (ROOT / 'drivers/block/zram/zcomp.c').read_text()
header = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include <pthread.h>
#include <stdatomic.h>
#include <unistd.h>
typedef uint64_t u64;
typedef int64_t s64;
#define TICK_NSEC 4000000LL
#define SCHED_CPUFREQ_IOWAIT 1
#define CPUFREQ_RELATION_L 0
#define unlikely(x) (x)
#define container_of(p,t,m) ((t *)((char *)(p)-offsetof(t,m)))
struct kthread_work { int unused; };
struct cpufreq_policy { bool fast_switch_enabled; unsigned int min,max,cur; int cpu,rwsem; };
struct sugov_policy { struct cpufreq_policy *policy; u64 last_freq_update_time; s64 min_rate_limit_ns,up_rate_delay_ns,down_rate_delay_ns; unsigned int next_freq,cached_raw_freq; bool work_in_progress,need_freq_update; int irq_work,update_lock,work_lock; struct kthread_work work; };
struct sugov_cpu { struct sugov_policy *sg_policy; bool iowait_boost_pending; unsigned int iowait_boost,iowait_boost_max; u64 last_update; };
static int queued,resolve_calls,inject_update;
static unsigned int applied;
static struct sugov_policy *current_policy;
static bool cpufreq_can_do_remote_dvfs(struct cpufreq_policy *p) { (void)p; return true; }
static unsigned int cpufreq_driver_fast_switch(struct cpufreq_policy *p,unsigned int f) { (void)p; return f; }
static int sugov_select_scaling_cpu(void) { return 0; }
static int smp_processor_id(void) { return 0; }
static void trace_cpu_frequency(unsigned int f,int cpu) { (void)f; (void)cpu; }
static void trace_cpu_frequency_sugov(unsigned int f,unsigned long u,int cpu) { (void)f; (void)u; (void)cpu; }
static void irq_work_queue_on(int *w,int cpu) { (void)w; (void)cpu; queued++; }
static bool arch_scale_freq_invariant(void) { return true; }
static unsigned int cpufreq_driver_resolve_freq(struct cpufreq_policy *p,unsigned int f) { resolve_calls++; return f < p->min ? p->min : f > p->max ? p->max : f; }
#define down_write(x) ((void)(x))
#define up_write(x) ((void)(x))
#define mutex_lock(x) ((void)(x))
#define mutex_unlock(x) ((void)(x))
#define raw_spin_lock_irqsave(x,f) do { (void)(x); (f)=0; } while(0)
#define raw_spin_unlock_irqrestore(x,f) do { (void)(x); (void)(f); } while(0)
static void __cpufreq_driver_target(struct cpufreq_policy *,unsigned int,int);
'''
funcs = '\n'.join(function(sg,n) for n in ['sugov_should_update_freq','sugov_up_down_rate_limit','sugov_update_commit','get_next_freq','sugov_set_iowait_boost','sugov_iowait_boost','sugov_work'])
test = r'''
static void __cpufreq_driver_target(struct cpufreq_policy *p,unsigned int f,int relation) {
 (void)p; (void)relation; applied=f;
 if(inject_update) { inject_update=0; sugov_update_commit(current_policy,30000000,100); }
}
static void governor_tests(void) {
 struct cpufreq_policy p={.min=100,.max=1000};
 struct sugov_policy s={.policy=&p,.next_freq=100,.up_rate_delay_ns=4000000,.down_rate_delay_ns=4000000,.min_rate_limit_ns=4000000};
 struct sugov_cpu c={.sg_policy=&s,.iowait_boost=800,.iowait_boost_max=1000,.last_update=1,.iowait_boost_pending=true};
 current_policy=&s;
 sugov_set_iowait_boost(&c,2*TICK_NSEC,SCHED_CPUFREQ_IOWAIT);
 assert(c.iowait_boost==100 && c.iowait_boost_pending);
 c.last_update=2*TICK_NSEC;
 sugov_set_iowait_boost(&c,2*TICK_NSEC+1,SCHED_CPUFREQ_IOWAIT);
 assert(c.iowait_boost==100);
 c.iowait_boost_pending=false;
 sugov_set_iowait_boost(&c,2*TICK_NSEC+2,SCHED_CPUFREQ_IOWAIT);
 assert(c.iowait_boost==200);
 c.iowait_boost=800; c.iowait_boost_pending=false;
 sugov_set_iowait_boost(&c,2*TICK_NSEC+3,SCHED_CPUFREQ_IOWAIT);
 assert(c.iowait_boost==1000);
 sugov_set_iowait_boost(&c,4*TICK_NSEC,0);
 assert(c.iowait_boost==0 && !c.iowait_boost_pending);
 c.iowait_boost=100; c.iowait_boost_pending=false;
 unsigned long util=0,max=1000;
 sugov_iowait_boost(&c,&util,&max); assert(c.iowait_boost==0);
 s.next_freq=1000; s.last_freq_update_time=10000000;
 unsigned int f=get_next_freq(&s,80,1000); assert(f==100);
 sugov_update_commit(&s,11000000,f);
 assert(s.next_freq==1000 && s.cached_raw_freq==UINT_MAX);
 int before=resolve_calls;
 f=get_next_freq(&s,80,1000); assert(f==100 && resolve_calls==before+1);
 sugov_update_commit(&s,15000000,f); assert(s.next_freq==100 && queued==1);
 assert(sugov_should_update_freq(&s,20000000)); /* queued worker may be busy */
 sugov_update_commit(&s,20000000,500); assert(s.next_freq==500 && queued==1);
 sugov_work(&s.work); assert(applied==500 && !s.work_in_progress);
 sugov_update_commit(&s,25000000,800); assert(queued==2);
 inject_update=1; sugov_work(&s.work);
 assert(applied==800 && s.next_freq==100 && s.work_in_progress && queued==3);
 sugov_work(&s.work); assert(applied==100 && !s.work_in_progress);
 s.need_freq_update=true; assert(sugov_should_update_freq(&s,30000001));
 assert(s.next_freq==UINT_MAX && !s.need_freq_update);
 puts("PASS: governor sparse/burst IOWAIT, rate-cache retry, queued coalescing, in-flight downscale, limits");
}
#define CONFIG_ZRAM_COMPRESSION_CONCURRENCY 4
#define PAGE_SIZE 4096
struct zcomp_strm { void *buffer; void *tfm; pthread_spinlock_t *codec_lock; };
#define spin_lock(x) pthread_spin_lock(x)
#define spin_unlock(x) pthread_spin_unlock(x)
static atomic_int active,peak;
static _Thread_local int calls;
static int codec(const void *src,void *dst) {
 int n=atomic_fetch_add(&active,1)+1;
 int old=atomic_load(&peak);
 while(n>old && !atomic_compare_exchange_weak(&peak,&old,n)) {}
 assert(n<=4);
 usleep(100);
 memcpy(dst,src,32);
 atomic_fetch_sub(&active,1);
 return ++calls%17==0 ? -5 : 0;
}
static int crypto_comp_compress(void *tfm,const void *src,unsigned int len,void *dst,unsigned int *out) { (void)tfm; assert(len==4096 && *out==8192); *out=32; return codec(src,dst); }
static int crypto_comp_decompress(void *tfm,const void *src,unsigned int len,void *dst,unsigned int *out) { (void)tfm; assert(len==32 && *out==4096); return codec(src,dst); }
'''
codec_funcs='\n'.join(function(zc,n) for n in ['zcomp_compress','zcomp_decompress'])
last=r'''
static pthread_spinlock_t gates[4];
static pthread_barrier_t start;
static void *codec_worker(void *arg) {
 uintptr_t cpu=(uintptr_t)arg;
 unsigned char src[4096],compressed[8192],restored[4096];
 memset(src,(int)cpu+1,sizeof(src));
 struct zcomp_strm s={.buffer=compressed,.codec_lock=&gates[cpu%4]};
 pthread_barrier_wait(&start);
 for(int i=0;i<200;i++) {
  unsigned int len=0; int before=calls;
  int r=zcomp_compress(&s,src,&len);
  assert(r==((before+1)%17==0 ? -5 : 0) && len==32);
  assert(!memcmp(src,compressed,32));
  before=calls; r=zcomp_decompress(&s,compressed,32,restored);
  assert(r==((before+1)%17==0 ? -5 : 0));
  assert(!memcmp(src,restored,32));
 }
 return NULL;
}
int main(void) {
 governor_tests();
 pthread_t t[8]; pthread_barrier_init(&start,NULL,8);
 for(int i=0;i<4;i++) pthread_spin_init(&gates[i],PTHREAD_PROCESS_PRIVATE);
 for(uintptr_t i=0;i<8;i++) assert(!pthread_create(&t[i],NULL,codec_worker,(void *)i));
 for(int i=0;i<8;i++) pthread_join(t[i],NULL);
 assert(atomic_load(&active)==0 && atomic_load(&peak)==4);
 puts("PASS: 8 callers, 3200 actual wrapper calls, maximum 4 concurrent codecs, error-path unlocks");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='alice-v9r5-') as td:
    c=Path(td)/'regression.c'; exe=Path(td)/'regression'
    c.write_text(header+funcs+test+codec_funcs+last)
    subprocess.run([os.environ.get('HOSTCC','cc'),'-std=gnu11','-O2','-Wall','-Wextra','-Werror','-pthread',str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=30)
