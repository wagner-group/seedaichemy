#!/usr/bin/env python3
"""
Generate many_idb.pcapng
  – SHB + 10 Interface-Description-Blocks (IDBs)
  – enough IDBs to drive add_interface() through its realloc/doubling path
"""

import struct

SHB_TYPE = 0x0A0D0D0A
IDB_TYPE = 0x00000001

def add_block(buf, btype, body):
    total = 8 + len(body) + 4
    pad = (4 - (len(body) % 4)) % 4
    buf += struct.pack("<II", btype, total)
    buf += body + b"\x00" * pad
    buf += struct.pack("<I", total)

def shb():
    body = struct.pack("<IHHq", 0x1A2B3C4D, 1, 0, -1)
    return body

def idb():
    return struct.pack("<HHI", 1, 0, 65535)  # Ethernet, snaplen 65535

def build(path, idb_count=10):
    buf = bytearray()
    add_block(buf, SHB_TYPE, shb())
    for _ in range(idb_count):
        add_block(buf, IDB_TYPE, idb())
    with open(path, "wb") as f:
        f.write(buf)

if __name__ == "__main__":
    build("many_idb.pcapng")
    print("generated many_idb.pcapng with 10 IDBs")

