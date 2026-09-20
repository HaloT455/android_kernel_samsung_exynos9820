#!/usr/bin/env python3
"""Execute the actual sucompat authorization function with stub credentials.

This regression check must reject native non-root callers without a KSU grant,
including system UID 1000, even when seccomp is absent. The original 32567b
function fails that case. Kernel build/link checks are still required.
"""
import pathlib
import subprocess
import sys
import tempfile

source = pathlib.Path(sys.argv[1]).read_text()
start = source.index("static __always_inline bool is_su_allowed(")
opening = source.index("{", start)
depth = 1
end = opening + 1
while depth:
    depth += (source[end] == "{") - (source[end] == "}")
    end += 1
function = source[start:end]

stubs = r'''
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <sys/types.h>
#undef __always_inline
#define __always_inline inline __attribute__((always_inline))
#define CONFIG_KSU_TAMPER_SYSCALL_TABLE 1
#define likely(x) (x)
#define unlikely(x) (x)
static uid_t caller;
static bool seccomp, ksu_domain, granted;
struct test_uid { uid_t val; };
static struct test_uid current_uid(void) { return (struct test_uid){caller}; }
static bool ksu_is_seccomp_enabled(void) { return seccomp; }
static bool is_ksu_domain(void) { return ksu_domain; }
static bool __ksu_is_allow_uid_copy(uid_t uid) { return granted; }
'''

cases = r'''
int main(void)
{
    const struct {
        const char *name;
        uid_t uid;
        bool seccomp, domain, grant, allowed;
    } cases[] = {
        {"system-ungranted", 1000, false, false, false, false},
        {"native-service-ungranted", 1001, false, false, false, false},
        {"native-service-high-uid", 2900, false, false, false, false},
        {"app-ungranted-no-seccomp", 10123, false, false, false, false},
        {"app-grant-revoked", 10123, false, false, false, false},
        {"shell-ungranted", 2000, false, false, false, false},
        {"shell-granted", 2000, false, false, true, true},
        {"app-granted", 10123, false, false, true, true},
        {"manager-allowlist-result", 10234, false, false, true, true},
        {"system-explicit-grant", 1000, false, false, true, true},
        {"root-ksu-domain", 0, false, true, false, true},
        {"root-other-domain", 0, false, false, true, false},
        {"sandbox-app", 10123, true, false, true, false},
        {"sandbox-root", 0, true, true, true, false},
    };
    unsigned int failures = 0, checks = 0;
    for (unsigned int i = 0; i < sizeof(cases) / sizeof(cases[0]); i++) {
        caller = cases[i].uid;
        seccomp = cases[i].seccomp;
        ksu_domain = cases[i].domain;
        granted = cases[i].grant;
        for (unsigned int p = 0; p < 3; p++) {
            const void *filename = p == 1 ? NULL : "/system/bin/su";
            const void **arg = p == 2 ? NULL : &filename;
            bool expected = cases[i].allowed && p == 0;
            bool actual = is_su_allowed(arg);
            checks++;
            if (actual != expected) {
                fprintf(stderr, "FAIL %s pointer=%u expected=%d actual=%d\n",
                        cases[i].name, p, expected, actual);
                failures++;
            }
        }
    }
    printf("sucompat: %u checks, %u failures\n", checks, failures);
    return failures ? 1 : 0;
}
'''

with tempfile.TemporaryDirectory(prefix="v9-sucompat-") as temporary:
    directory = pathlib.Path(temporary)
    test_source = directory / "gate.c"
    test_binary = directory / "gate"
    test_source.write_text(stubs + function + cases)
    subprocess.run(["cc", "-std=gnu11", "-O2", "-Wall", "-Werror",
                    str(test_source), "-o", str(test_binary)], check=True)
    subprocess.run([str(test_binary)], check=True)
