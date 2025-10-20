#!/usr/bin/env python3
"""
gen_pcapng_next_packet.py
Create a minimal pcap-ng file that drives libpcap into pcap_ng_next_packet().

Layout:
  1. SHB  – Section Header Block (version 1.0)
  2. IDB  – Interface-Description Block (Ethernet, snaplen 65535)
  3. EPB  – Enhanced Packet Block referencing interface 0, 4-byte payload

Output: trigger_next_packet.pcapng
"""

import struct

# Block-type constants
SHB_TYPE = 0x0A0D0D0A
IDB_TYPE = 0x00000001
EPB_TYPE = 0x00000006

def add_block(buf: bytearray, blktype: int, body: bytes) -> None:
    """Append a 32-bit-aligned block (header + body + trailer) to buf."""
    pad = (4 - (len(body) % 4)) % 4            # align to 4 bytes
    total_len = 8 + len(body) + pad + 4        # header+body+pad+trailer
    buf += struct.pack("<II", blktype, total_len)
    buf += body + b"\x00" * pad
    buf += struct.pack("<I", total_len)

def make_shb() -> bytes:
    """Return raw SHB body."""
    return struct.pack("<IHHq",
                       0x1A2B3C4D,  # byte-order magic
                       1, 0,        # version 1.0
                       -1)          # section length: unspecified

def make_idb() -> bytes:
    """Return raw IDB body (Ethernet, snaplen 65535)."""
    return struct.pack("<HHI", 1, 0, 65535)

def make_epb(payload: bytes = b"\xCA\xFE\xBA\xBE") -> bytes:
    """Return raw EPB body with given packet payload."""
    caplen = origlen = len(payload)
    hdr = struct.pack("<IIIIII",
                      0,      # interface ID
                      0, 0,   # timestamp hi/lo
                      caplen,
                      origlen,
                      0)      # placeholder – trimmed below
    return hdr[:-4] + payload  # remove last int so header == 20 bytes

def build(path: str = "trigger_next_packet.pcapng") -> None:
    """Generate the corpus file."""
    buf = bytearray()
    add_block(buf, SHB_TYPE, make_shb())
    add_block(buf, IDB_TYPE, make_idb())
    add_block(buf, EPB_TYPE, make_epb())
    with open(path, "wb") as f:
        f.write(buf)
    print(f"Generated {path}")

if __name__ == "__main__":
    build()

