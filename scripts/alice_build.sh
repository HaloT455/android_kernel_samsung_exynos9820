#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${CLANG_DIR:?Set CLANG_DIR to the extracted Android clang-r547379 directory}"
if [ "$(git -C KernelSU-Next rev-parse --is-shallow-repository)" = true ]; then
	printf '%s\n' 'KernelSU history is shallow; run git -C KernelSU-Next fetch --unshallow --tags first.' >&2
	exit 1
fi
test "$(git -C KernelSU-Next rev-parse HEAD)" = \
	fc33995cedc5e0ebf719745c71fe15e78694260f
export PATH="$CLANG_DIR/bin:$PATH"
export ARCH=arm64 PLATFORM_VERSION=11 ANDROID_MAJOR_VERSION=r
export KBUILD_BUILD_USER=ALice KBUILD_BUILD_HOST=kernel-build
alice_out="${ALICE_OUT:-out-alice}"
make LLVM=1 LLVM_IAS=1 O="$alice_out" alice_beyond2lte_defconfig
make LLVM=1 LLVM_IAS=1 O="$alice_out" -j"${JOBS:-8}" Image
python3 scripts/alice_verify_config.py "$alice_out/.config"
test -s "$alice_out/arch/arm64/boot/Image"
sha256sum "$alice_out/arch/arm64/boot/Image"
