# ALice S10+ V9R2 + MGLRU + LZ4KD source patch — WIP

**Branch base:** `agent/beyond2lte-v9-mglru-diag` (not default `main`). This base contains the ALice V9R2 configuration with `CONFIG_LOCALVERSION="-ALice-S10P-V9R2-MGLRU"`, `CONFIG_LRU_GEN=y`, `CONFIG_LRU_GEN_ENABLED=y`. We **preserve these settings**.

## Implemented
- Copied real Huawei LZ4KD compressor/decompressor source and headers from [Andrey0800770/samsung_sdm845-kernel](https://github.com/Andrey0800770/samsung_sdm845-kernel) into `lib/lz4kd/`, `include/linux/lz4kd.h` and `crypto/lz4kd.c`, preserving copyright credits.
- Wired symbols `CONFIG_CRYPTO_LZ4KD`, `CONFIG_LZ4KD_COMPRESS`, `CONFIG_LZ4KD_DECOMPRESS` into Kconfig and Kbuild.
- Registered the `lz4kd` backend for ZRAM; default ZRAM codec becomes LZ4KD *when the codec is built in*, with the existing LZ4 fallback retained.
- Enabled `CONFIG_CRYPTO_LZ4KD=y` **only in** `arch/arm64/configs/beyond2lte.config`.
- Fixed upstream crypto wrapper's return handling for incompressible pages: return an error for encoder result <=0, so ZRAM can store the page uncompressed.

## Limits
- **Not yet compiled or tested. Not a flashable firmware or boot image.**
- The original Huawei implementation was ported from a different Samsung Snapdragon kernel; ABI and toolchain compatibility with Exynos9820 kernel 4.14 must be verified.
- No Wi-Fi firmware/driver power hacks; 5 GHz priority and 2.4 GHz fallback require Android framework/ROM and saved network information.
- LMKD is in Android userspace; kernel already provides PSI/MGLRU. No old `simple_lmk` backport.
- `CONFIG_EXYNOS_NPU=y` is present in the provided boot image. Neural-network inference uses compatible runtime/model/firmware; NPU cannot replace Mali GPU as graphical renderer.
- Avoid CPU/GPU overclock and thermal-throttle bypass as counterproductive for sustained stability and battery.

## Uploaded boot image baseline
`ALice_S10Plus_V9R2_TEST(1).img`: 57,671,680 bytes, SHA256 `5c1396b17ee22d2dee09b97cc86515ff649d63ff3cf0245ac65d6fc755884284`. Reported Linux `4.14.356-openela-rc1-ALice-S10P-V9R2-MGLRU+`, header board `JDKA15V10SO`; kernel source builder currently uses `SRPRI17C016KU` board for beyond2lte. Do NOT assume the builder's boot.img is a drop-in replacement without inspecting DTB/DTBO, ramdisk, header and Android 16 ROM compatibility.

## Validation to do before flashing
1. Check source/toolchain, enabled MGLRU and LZ4KD config via actual generated `.config`.
2. Compile `./build.sh -m beyond2lte -k n` on a Linux build machine with the repo's toolchain/submodules. Build script is not certified for this image.
3. Run LZ4KD round-trip unit tests on compressible/incompressible pages, crypto/zram stress, suspend/resume, low-memory pressure and corruption tests.
4. On a spare S10+ with full verified boot image backup, validate `/sys/block/zram0/comp_algorithm`, `/proc/swaps`, PSI, MGLRU, thermals and power.
5. Repack with **matching image header/DTB/DTBO** only after all tests, do not flash unverified repo default artifacts.

Source code modified on this branch, **no ready-to-flash build is claimed.**
