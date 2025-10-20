# edge_pcaps.py
"""
Write 3 PCAP edge-cases for libpcap's pcap_check_header():

  1. swapped_ok.pcap      – byte-swapped magic; full, version-2 header
  2. swapped_trunc.pcap   – byte-swapped magic; header deliberately truncated
  3. archaic_v1.pcap      – normal-endian magic; full header but version 1.0

Run this once, then give the produced files to AFL++ (or your standalone
harness) as seed corpus.
"""
from pathlib import Path
import struct
import os

# --- constants ---------------------------------------------------------------
STD_MAGIC        = 0xA1B2C3D4  # host-byte-order match
SWAPPED_MAGIC    = 0xD4C3B2A1  # opposite byte order → triggers swap path
PCAP_VMAJOR      = 2           # current major version (2.4 format) :contentReference[oaicite:0]{index=0}
PCAP_VMINOR      = 4
SNAPLEN          = 65535
DLT_EN10MB       = 1           # Ethernet

def _pack_hdr(endian: str, v_major: int) -> bytes:
    """Return a complete pcap_file_header in the supplied endianess."""
    return struct.pack(
        f"{endian}IHHIIII",
        STD_MAGIC if endian == "<" else STD_MAGIC,  # placeholder, will overwrite
        v_major, PCAP_VMINOR,
        0,             # thiszone
        0,             # sigfigs
        SNAPLEN,
        DLT_EN10MB
    )

def make_edge_pcaps(outdir: str | Path = "edge_pcaps") -> list[Path]:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []

    # ------------------------------------------------------------------ 1/3 --
    # Byte-swapped file -- full, valid header (exercises lines 170-183 & 208-214)
    be_hdr = _pack_hdr(">", PCAP_VMAJOR)
    be_hdr = struct.pack(">I", SWAPPED_MAGIC) + be_hdr[4:]  # real magic
    p = outdir / "swapped_ok.pcap"
    p.write_bytes(be_hdr)          # no packet records needed for header parsing
    paths.append(p)

    # ------------------------------------------------------------------ 2/3 --
    # Same as above but purposefully truncated → fread() short (lines 190-202)
    p = outdir / "swapped_trunc.pcap"
    p.write_bytes(struct.pack(">I", SWAPPED_MAGIC) + be_hdr[4:14])  # only half
    paths.append(p)

    # ------------------------------------------------------------------ 3/3 --
    # Normal-endian magic, but *archaic* version 1.0 (lines 217-222)
    le_hdr = _pack_hdr("<", 1)                          # version 1
    le_hdr = struct.pack("<I", STD_MAGIC) + le_hdr[4:]  # correct magic
    p = outdir / "archaic_v1.pcap"
    p.write_bytes(le_hdr)
    paths.append(p)

    return paths


if __name__ == "__main__":
    for f in make_edge_pcaps():
        print(f"wrote {f.resolve()}")

