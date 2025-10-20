#!/usr/bin/env python3
"""
generate_bpf_corpus.py
======================

Create seed files that maximise code-coverage inside libpcap's bpf_filter.c.

The harness we target expects:

    [ 1-byte length ][ filter bytes + NUL ][ arbitrary .pcap file ]

For each “interesting” BPF filter listed below we build a tiny classic-pcap
containing two Ethernet frames, then write everything to ./bpf_seeds/.
"""

import os, struct, time, random

###############################################################################
#  Crafty filters chosen to light up rarely-hit BPF opcodes
###############################################################################

FILTERS = [
    # Simple absolute load / equality jump
    "ether[12:2] == 0x0800",

    # Half-word load, AND, inequality test
    "ip[6:2] & 0x1fff != 0",

    # Arithmetic LEN opcode
    "len > 60 && len < 1514",

    # Shift-right, indirect load, variable offset slice, scratch store
    "tcp[((tcp[12] & 0xf0) >> 2):4] == 0x47455420",

    # Proto-chain recursion (walks header stack)
    "protochain udp and (port 53 or 5353)",

    # Deep VLAN stack (uses BPF_ST/LD scratch memory)
    "vlan 100 && vlan 200 && ip",

    # MPLS stack bookkeeping
    "mpls 100 && mpls 200 && proto 47",

    # IPv6 extension-header chain
    "ip6 and (fragment or dst)",

    # PF specific qualifiers → error vs. success branches
    'pf_ifname "eth0" and pf_rnr 4',

    # Name-resolution path (nametoaddr.c)
    'host "example.com" and tcp port "http-alt"',
]

###############################################################################
#  Minimal classic-pcap helpers
###############################################################################

DLT_EN10MB = 1  # Ethernet

def pcap_global_header(snaplen=65535, dlt=DLT_EN10MB):
    """24-byte classic (libpcap) global header, little-endian."""
    return struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, snaplen, dlt)

def pcap_pkt_header(pkt_len, ts=None):
    if ts is None:
        ts = time.time()
    sec = int(ts)
    usec = int((ts - sec) * 1_000_000)
    return struct.pack("<IIII", sec, usec, pkt_len, pkt_len)

def min_eth_frame(payload_bytes):
    """Return an Ethernet frame (dest/src = 00…, ethertype = IPv4)."""
    eth_hdr = b"\x00" * 12 + b"\x08\x00"
    return eth_hdr + payload_bytes

def build_pcap():
    """
    Two-packet pcap:
      * pkt0 – 10-byte truncated Ethernet   → out-of-range loads
      * pkt1 – 100-byte Ethernet (0xAA)     → full interpreter path
    """
    g = pcap_global_header()
    pkt0 = min_eth_frame(b"\x00" *  -4)[:10]         # intentionally short
    pkt1 = min_eth_frame(b"\xAA" * 86)               # 100 bytes total

    return (
        g +
        pcap_pkt_header(len(pkt0)) + pkt0 +
        pcap_pkt_header(len(pkt1)) + pkt1
    )

###############################################################################
#  Assemble harness-ready blobs
###############################################################################

def make_blob(filter_str: str) -> bytes:
    filt_bytes = filter_str.encode() + b"\x00"
    if len(filt_bytes) > 255:
        raise ValueError("filter too long for 1-byte length prefix")
    return bytes([len(filt_bytes)]) + filt_bytes + build_pcap()

###############################################################################
#  Write corpus
###############################################################################

if __name__ == "__main__":
    outdir = "bpf_seeds"
    os.makedirs(outdir, exist_ok=True)

    for i, fexpr in enumerate(FILTERS):
        path = f"{outdir}/seed_{i:02d}"
        with open(path, "wb") as fp:
            fp.write(make_blob(fexpr))
        print(f"Wrote {path:<20} | filter = {fexpr}")

