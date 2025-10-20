#!/usr/bin/env python3
"""
make_llc_fallback_seeds.py
==========================

Create AFL/libFuzzer seed files that *force* libpcap to call

        pcap_nametollc()

Each seed = [1-byte length] [NUL-terminated filter string] [single-packet pcap].

Filter strings use the pattern  'link <unknown-id>' so that
pcap_nametoeproto() fails → PROTO_UNDEF → pcap_nametollc() is tried next.
"""

import os, struct, time

# ---------------------------------------------------------------------------
# Minimal classic-pcap helpers
# ---------------------------------------------------------------------------
MAGIC      = 0xA1B2C3D4
DLT_EN10MB = 1          # Ethernet

def pcap_global() -> bytes:
    """24-byte global header."""
    return struct.pack("<IHHIIII", MAGIC, 2, 4, 0, 0, 65535, DLT_EN10MB)

def pcap_pkt_hdr(nbytes: int) -> bytes:
    ts   = time.time()
    sec  = int(ts)
    usec = int((ts - sec) * 1_000_000)
    return struct.pack("<IIII", sec, usec, nbytes, nbytes)

def ethernet_frame() -> bytes:
    """Return a valid 60-byte Ethernet frame (type IPv4, zero payload)."""
    eth = b"\x00"*12 + b"\x08\x00"          # dst, src, ethertype = 0x0800
    return eth + b"\x00"*46                 # pad to min length

def single_pkt_pcap() -> bytes:
    pkt = ethernet_frame()
    return pcap_global() + pcap_pkt_hdr(len(pkt)) + pkt

# ---------------------------------------------------------------------------
# Build harness-ready blob   [len][filter][pcap]
# ---------------------------------------------------------------------------
def blob(filter_str: str) -> bytes:
    f = filter_str.encode() + b"\x00"
    if len(f) > 255:
        raise ValueError("filter too long for one-byte length prefix")
    return bytes([len(f)]) + f + single_pkt_pcap()

# ---------------------------------------------------------------------------
# Seeds: names that are (almost certainly) *missing* from eproto_db
# ---------------------------------------------------------------------------
FILTERS = [
    "link foobar",
    "link xyz123",
    "link fuzzsap",
    "link llmtest",
    "link unknown_proto",
    "link madeupllc",
]

# ---------------------------------------------------------------------------
# Write corpus
# ---------------------------------------------------------------------------
outdir = "llc_fallback_seeds"
os.makedirs(outdir, exist_ok=True)

for i, filt in enumerate(FILTERS):
    path = f"{outdir}/seed_{i:02d}"
    with open(path, "wb") as fp:
        fp.write(blob(filt))
    print(f"Wrote {path:<25} | filter = '{filt}'")

