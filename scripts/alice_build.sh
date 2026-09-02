#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -n "${CLANG_DIR:-}" ] && [ -x "$CLANG_DIR/bin/clang-20" ]; then
	export PATH="$CLANG_DIR/bin:$PATH"
elif command -v clang >/dev/null 2>&1; then
	echo "Using runner-provided $(clang --version | head -1)"
else
	echo "No usable LLVM/Clang toolchain found" >&2
	exit 1
fi
if [ "$(git -C KernelSU-Next rev-parse --is-shallow-repository)" = true ]; then
	printf '%s\n' 'KernelSU history is shallow; run git -C KernelSU-Next fetch --unshallow --tags first.' >&2
	exit 1
fi
test "$(git -C KernelSU-Next rev-parse HEAD)" = \
	fc33995cedc5e0ebf719745c71fe15e78694260f
export ARCH=arm64 PLATFORM_VERSION=11 ANDROID_MAJOR_VERSION=r
export KBUILD_BUILD_USER=ALice KBUILD_BUILD_HOST=kernel-build
alice_out="${ALICE_OUT:-out-alice}"
make LLVM=1 LLVM_IAS=1 O="$alice_out" alice_beyond2lte_defconfig
make LLVM=1 LLVM_IAS=1 O="$alice_out" -j"${JOBS:-8}" Image
python3 scripts/alice_verify_config.py "$alice_out/.config"
test -s "$alice_out/arch/arm64/boot/Image"
sha256sum "$alice_out/arch/arm64/boot/Image"
