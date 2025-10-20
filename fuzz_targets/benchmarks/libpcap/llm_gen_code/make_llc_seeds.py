#!/usr/bin/env python3
"""Generate corpus files that force libpcap -> gencode -> pcap_nametollc()."""

import os, struct, time

# ---------------------------------------------------------------------------
# Helper functions to write a minimal classic-pcap file (link-type Ethernet)
# ---------------------------------------------------------------------------
MAGIC   = 0xA1B2C3D4
DLT_EN10MB = 1

def pcap_global() -> bytes:
    return struct.pack("<IHHIIII", MAGIC, 2, 4, 0, 0, 65535, DLT_EN10MB)

def pcap_pkt_header(nbytes: int) -> bytes:
    ts = time.time()
    sec = int(ts)
    usec = int((ts - sec) * 1_000_000)
    return struct.pack("<IIII", sec, usec, nbytes, nbytes)

def minimal_frame() -> bytes:
    eth_hdr = b"\x00"*12 + b"\x08\x00"      # dst, src, ethertype = IPv4
    payload = b"\x00"*46                    # pad to 60-byte Ethernet
    return eth_hdr + payload

def single_pkt_pcap() -> bytes:
    pkt = minimal_frame()
    return pcap_global() + pcap_pkt_header(len(pkt)) + pkt

# ---------------------------------------------------------------------------
# Build a fuzzer blob: [len][filter][pcap]
# ---------------------------------------------------------------------------
def blob(filter_str: str) -> bytes:
    f = filter_str.encode() + b"\x00"
    if len(f) > 255:
        raise ValueError("filter too long for one-byte length field")
    return bytes([len(f)]) + f + single_pkt_pcap()

# ---------------------------------------------------------------------------
# Generate the four seeds
# ---------------------------------------------------------------------------
FILTERS = [
    'link stp',         # Spanning-Tree Protocol – LLCSAP_8021D
    'link iso',         # ISO network layer – LLCSAP_ISONS
    'link ipx',         # Novell IPX – LLCSAP_IPX
    'link netbeui',     # NetBEUI – LLCSAP_NETBEUI
]

os.makedirs("llc_seeds", exist_ok=True)
for i, fstr in enumerate(FILTERS):
    path = f"llc_seeds/seed_{i:02d}"
    with open(path, "wb") as fp:
        fp.write(blob(fstr))
    print(f"Wrote {path}  |  filter = '{fstr}'")

