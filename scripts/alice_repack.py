#!/usr/bin/env python3
"""Replace this supplied S10+ boot's kernel and retire its JDK V10 wrapper.

Never writes a device. Refuses unexpected inputs, signed trailers or size growth.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct

BOOT_SHA = "fb56472b9e5c00323f89adf093c4332ee29e023d460bbb43f05d0afedccef371"
DTBO_SHA = "39601edea8c20c9bc4dfd82882271981f7885eb8cca8c4cb56a2a28bfd891dc4"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def align(n, page=4):
    return (n + page - 1) // page * page

def unpack_boot(raw):
    assert raw[:8] == b"ANDROID!"
    fields = struct.unpack_from("<10I", raw, 8)
    page = fields[7]
    assert fields[8] == 1 and page == 2048
    assert struct.unpack_from("<IQI", raw, 1632) == (0, 0, 1648)
    offset, parts = page, []
    for size in (fields[0], fields[2], fields[4]):
        part = raw[offset:offset+size]
        assert len(part) == size
        parts.append(part)
        offset += align(size, page)
    assert not any(raw[offset:]), "Unknown nonzero trailer; do not discard it"
    return bytearray(raw[:page]), parts

def boot_id(parts):
    digest = hashlib.sha1()
    for part in parts + [b""]:  # boot-v1 includes the empty recovery DTBO
        digest.update(part)
        digest.update(struct.pack("<I", len(part)))
    return digest.digest() + bytes(12)

def cpio_read(raw):
    offset, records = 0, []
    while True:
        assert raw[offset:offset+6] == b"070701", "Unsupported CPIO format"
        h = [int(raw[offset+6+i*8:offset+14+i*8], 16) for i in range(13)]
        name_end = offset + 110 + h[11]
        assert raw[name_end-1] == 0
        name = raw[offset+110:name_end-1].decode()
        start = align(name_end)
        data = raw[start:start+h[6]]
        assert len(data) == h[6]
        records.append((name, h, data))
        offset = align(start+h[6])
        if name == "TRAILER!!!":
            assert not any(raw[offset:])
            return records

def cpio_write(records):
    raw = bytearray()
    for name, fields, data in records:
        fields = fields.copy()
        encoded = name.encode() + b"\0"
        fields[6], fields[11] = len(data), len(encoded)
        raw += b"070701" + b"".join(f"{n:08x}".encode() for n in fields)
        raw += encoded
        raw += bytes(align(len(raw))-len(raw))
        raw += data
        raw += bytes(align(len(raw))-len(raw))
    raw += bytes(align(len(raw),512)-len(raw))
    return bytes(raw)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boot", required=True)
    parser.add_argument("--dtbo", required=True)
    parser.add_argument("--kernel", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    original = Path(args.boot).read_bytes()
    dtbo = Path(args.dtbo).read_bytes()
    kernel = Path(args.kernel).read_bytes()
    assert sha(original) == BOOT_SHA and sha(dtbo) == DTBO_SHA
    header, parts = unpack_boot(original)
    assert header[576:608] == boot_id(parts), "Original boot ID mismatch"
    assert kernel[56:60] == b"ARMd"
    assert b"-ALice-S10P-UI1-EAS65-R1" in kernel
    records = cpio_read(gzip.decompress(parts[1]))
    by_name = {name: (name, fields, data) for name, fields, data in records}
    assert len(by_name) == len(records)
    wrapper = by_name["init"][2]
    real = by_name["init.real"]
    assert b"jdk_init_v10.c" in wrapper and b"SCREEN OFF STRICT" in wrapper
    assert real[2][:4] == b"\x7fELF" and struct.unpack_from("<H",real[2],18)[0] == 183
    rebuilt = []
    for name, fields, data in records:
        if name == "init":
            rebuilt.append(("init", real[1], real[2]))
        elif name != "init.real":
            rebuilt.append((name, fields, data))
    ramdisk = gzip.compress(cpio_write(rebuilt), compresslevel=9, mtime=0)
    new_parts = [kernel, ramdisk, parts[2]]
    struct.pack_into("<I", header, 8, len(kernel))
    struct.pack_into("<I", header, 16, len(ramdisk))
    header[576:608] = boot_id(new_parts)
    image = header
    for part in new_parts:
        image += part + bytes(align(len(part),2048)-len(part))
    assert len(image) <= len(original), "Boot exceeds supplied partition image"
    image += bytes(len(original)-len(image))
    # Independently parse the packed result before writing it.
    checked_header, checked = unpack_boot(image)
    assert checked == new_parts and checked_header[576:608] == boot_id(checked)
    new_records = {n:(h,d) for n,h,d in cpio_read(gzip.decompress(checked[1]))}
    assert new_records["init"][1] == real[2] and "init.real" not in new_records
    for name, fields, data in records:
        if name not in ("init", "init.real"):
            assert new_records[name] == (fields,data), name
    before_header = bytearray(original[:2048])
    for a,b in ((8,12),(16,20),(576,608)):
        before_header[a:b] = checked_header[a:b]
    assert before_header == checked_header, "Unrelated boot header changed"
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image)
    report = {
        "status":"PACKAGING VERIFIED; NOT DEVICE-TESTED",
        "boot_original_sha256":BOOT_SHA, "boot_candidate_sha256":sha(image),
        "dtbo_unchanged_sha256":DTBO_SHA, "size_bytes":len(image),
        "kernel_sha256":sha(kernel), "kernel_size":len(kernel),
        "original_native_init_sha256":sha(real[2]),
        "restored_init_sha256":sha(new_records["init"][1]),
        "removed":"JDK V10 init wrapper and its CPU/GPU/bus control daemon",
        "preserved":"All other ramdisk entries, both fstabs, boot header addresses/OS fields, dtbo",
        "boot_id":"SHA1 boot-v1 verified",
    }
    output.with_suffix(".audit.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__ == "__main__":
    main()
