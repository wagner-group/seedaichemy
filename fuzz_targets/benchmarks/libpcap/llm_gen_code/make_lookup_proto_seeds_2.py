#!/usr/bin/env python3
"""
Generate AFL++ seed-corpus entries that exercise

    gen_scode() → case Q_PROTOCHAIN →
        lookup_proto() → case Q_LINK →
            pcap_nametoeproto() / pcap_nametollc()

Input format follows testprogs/fuzz/fuzz_both.c:
    [1-byte length L] [L bytes filter buf] [PCAP data]
The harness NUL-terminates the filter by clobbering its last byte,
so we store  N = len(filter) + 1  and add one dummy byte.
"""

from pathlib import Path
import struct

# ----------------------------------------------------------------------
# Minimal Ethernet PCAP (24-byte hdr + 16-byte packet hdr + 60-byte frame)
# ----------------------------------------------------------------------
def minimal_pcap() -> bytes:
    ghdr = struct.pack(
        "<IHHIIII",
        0xA1B2C3D4,    # magic (host-endian doesn’t matter offline)
        2, 4,          # version
        0, 0,          # thiszone, sigfigs
        65535,         # snaplen
        1,             # DLT_EN10MB
    )
    phdr = struct.pack("<IIII", 0, 0, 60, 60)
    payload = b"\0" * 60
    return ghdr + phdr + payload


# ----------------------------------------------------------------------
def make_input(filter_str: str) -> bytes:
    filt_bytes = filter_str.encode("ascii")
    L = len(filt_bytes) + 1           # +1 for dummy byte
    if L > 255:
        raise ValueError("filter too long")
    return (
        bytes([L]) +                  # length byte
        filt_bytes + b"\n" +          # filter + dummy
        minimal_pcap()                # packet data
    )


def main():
    seeds = {
        "link_protochain_ip.pcap":    "link protochain ip",
        "link_protochain_ipx.pcap":   "link protochain ipx",
        "link_protochain_bogus.pcap": "link protochain xyzzy",
    }

    outdir = Path("seeds_protochain")
    outdir.mkdir(exist_ok=True)

    for fname, fstr in seeds.items():
        data = make_input(fstr)
        (outdir / fname).write_bytes(data)
        print(f"Wrote {fname:28}  — filter: {fstr!r}")

    print("\nCopy or bind-mount 'seeds_protochain/' to your AFL++ "
          "CORPUS_DIR and start fuzzing.")


if __name__ == "__main__":
    main()

