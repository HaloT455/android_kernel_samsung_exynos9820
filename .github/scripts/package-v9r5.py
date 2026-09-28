#!/usr/bin/env python3
"""Reproduce the verified V9R5 boot from CI kernel and tracked ramdisk files."""
import argparse
import base64
import gzip
import hashlib
import json
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / '.github/v9r5-package'
KERNEL_SHA = '98123bd1f74c8400ac78a0adde41d2c6da8058acd6b936c4b9bf1e03681e48d8'
BOOT_SHA = '2c4a8d8130598891af33b8b1395221ba45c440ef52ef5734fdbdc977d6f22583'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def package(ci, output):
    recipe = json.loads((ASSETS / 'ramdisk-recipe.json').read_text())
    chunks = []
    for item in recipe['segments']:
        if 'source' in item:
            path = (ROOT / item['source']).resolve()
            assert path.is_relative_to(ROOT / 'build/ramdisk')
            data = path.read_bytes()
            assert len(data) == item['size'] and sha(data) == item['sha256']
        else:
            data = base64.b64decode(item['literal_b64'], validate=True)
        chunks.append(data)
    cpio = b''.join(chunks)
    assert sha(cpio) == recipe['cpio_sha256'], 'Ramdisk contents differ'
    ramdisk = gzip.compress(cpio, compresslevel=9, mtime=0)
    # Original gzip header uses Unix OS=3; normalize Python version differences.
    ramdisk = ramdisk[:9] + b'\x03' + ramdisk[10:]
    assert sha(ramdisk) == recipe['ramdisk_sha256'], 'Ramdisk gzip differs'

    kernel = (ci / 'ALice_S10Plus_V9R5_KSU32567_MGLRU_Image').read_bytes()
    assert sha(kernel) == KERNEL_SHA, 'Unexpected kernel artifact'
    assert kernel[56:60] == b'ARMd' and b'ALice-S10P-V9R5-MGLRU' in kernel
    header = bytearray(base64.b64decode(recipe['base_header_b64'], validate=True))
    assert header[:8] == b'ANDROID!'
    page = struct.unpack_from('<I', header, 36)[0]
    assert page == len(header) == 2048
    assert struct.unpack_from('<I', header, 16)[0] == len(ramdisk)
    assert struct.unpack_from('<I', header, 24)[0] == 0
    assert struct.unpack_from('<I', header, 40)[0] == 1
    assert struct.unpack_from('<IQI', header, 1632) == (0, 0, 1648)
    struct.pack_into('<I', header, 8, len(kernel))
    ident = hashlib.sha1()
    for payload in (kernel, ramdisk, b''):
        ident.update(payload)
        ident.update(struct.pack('<I', len(payload)))
    ident.update(struct.pack('<I', 0))  # v1 empty recovery_dtbo size
    header[576:608] = ident.digest() + b'\0' * 12
    image = bytes(header)
    for payload in (kernel, ramdisk):
        image += payload + b'\0' * (-len(payload) % page)
    assert len(image) <= recipe['boot_size']
    image += b'\0' * (recipe['boot_size'] - len(image))
    assert sha(image) == BOOT_SHA, 'Boot differs from locally verified package'

    output.mkdir(parents=True, exist_ok=True)
    assert not any(output.iterdir()), 'Output must be empty'
    (output / 'ALice_S10Plus_V9R5_TEST.img').write_bytes(image)
    for name in ('BUILD_MANIFEST.json', 'HUONG_DAN_V9R5.md',
                 'HOST_TEST_RESULT.txt', 'SOURCE_URL.txt',
                 'V4_V9R2_COMPARISON.json', 'collect-v9r5.sh'):
        shutil.copyfile(ASSETS / name, output / name)
    shutil.copyfile(ci / 'ALice_S10Plus_V9.config', output / 'ALice_S10Plus_V9R5.config')
    shutil.copyfile(ci / 'ALice_S10Plus_V9_LINKED_SYMBOLS.txt', output / 'LINKED_SYMBOLS.txt')
    sums = ''.join(f'{sha(p.read_bytes())}  {p.name}\n'
                   for p in sorted(output.iterdir()))
    (output / 'SHA256SUMS').write_text(sums)
    print(f'Verified boot: {BOOT_SHA} ({len(image)} bytes)')
    print('Ramdisk identical to working V9R2; DTBO unchanged, not included.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ci', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    package(args.ci, args.output)
