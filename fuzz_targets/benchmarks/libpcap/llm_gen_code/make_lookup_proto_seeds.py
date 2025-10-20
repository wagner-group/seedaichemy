#!/usr/bin/env python3
"""
Generate AFL++ seed-corpus files that hit gencode.c::lookup_proto()
in libpcap via the OSS-Fuzz `fuzz_both` harness.

Each output file layout:
   [1-byte len] [filter string] [minimal Ethernet PCAP]

Author: Jim Jiang (2025-06-22)
"""

from pathlib import Path
import struct

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def build_minimal_pcap() -> bytes:
    """
    Return bytes for a valid little-endian Ethernet pcap containing one
    dummy 60-byte frame. 24-byte global hdr + 16-byte pkt hdr + payload.
    """
    # pcap global header (little-endian)
    magic      = 0xD4C3B2A1            # little-endian magic
    ver_major  = 2
    ver_minor  = 4
    thiszone   = 0                     # GMT
    sigfigs    = 0
    snaplen    = 65535
    network    = 1                     # DLT_EN10MB (Ethernet)

    global_hdr = struct.pack(
        "<IHHIIII",
        magic, ver_major, ver_minor,
        thiszone, sigfigs, snaplen, network
    )

    # single packet header
    ts_sec     = 0
    ts_usec    = 0
    incl_len   = 60
    orig_len   = 60
    pkt_hdr    = struct.pack("<IIII", ts_sec, ts_usec, incl_len, orig_len)

    payload    = b"\x00" * incl_len

    return global_hdr + pkt_hdr + payload


def make_seed(filter_str: str) -> bytes:
    """
    Compose the seed layout required by fuzz_both:
        len(filter) (1 byte) + filter (ASCII) + minimal pcap
    """
    filt_bytes = filter_str.encode("ascii")
    if len(filt_bytes) > 255:
        raise ValueError("Filter string must be ≤255 bytes")
    return bytes([len(filt_bytes)]) + filt_bytes + build_minimal_pcap()


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    seeds_dir = Path("seeds")
    seeds_dir.mkdir(exist_ok=True)

    filters = {
        "link_ip.pcap":  "link ip",   # hits pcap_nametoeproto()
        "link_ipx.pcap": "link ipx",  # falls through to pcap_nametollc()
    }

    for fname, fstr in filters.items():
        seed_path = seeds_dir / fname
        seed_path.write_bytes(make_seed(fstr))
        print(f"[*] Wrote {seed_path}  ({len(fstr)}-byte filter)")

    print("\nDone!  Copy or bind-mount the 'seeds/' dir into your AFL++ "
          "container (CORPUS_DIR) and start fuzzing.\n")


if __name__ == "__main__":
    main()

