import struct

# This script generates 5 PCAP files with packets designed to trigger:
# pcap_parse -> gen_scode -> lookup_proto -> pcap_nametollc
#
# The code path is triggered by filter expressions that reference LLC protocol names
# (like "llc", "llc dsap", "llc ssap", etc.), so we need packets with LLC headers.

# Minimal PCAP global header (little endian, Ethernet)
PCAP_GLOBAL_HEADER = (
    b'\xd4\xc3\xb2\xa1'  # magic number
    b'\x02\x00'          # version major
    b'\x04\x00'          # version minor
    b'\x00\x00\x00\x00'  # thiszone
    b'\x00\x00\x00\x00'  # sigfigs
    b'\xff\xff\x00\x00'  # snaplen
    b'\x01\x00\x00\x00'  # network (Ethernet)
)

def make_pcap_packet(payload):
    # PCAP Packet Header (little endian)
    ts_sec = 0
    ts_usec = 0
    incl_len = len(payload)
    orig_len = len(payload)
    header = struct.pack('<IIII', ts_sec, ts_usec, incl_len, orig_len)
    return header + payload

def make_llc_packet(dsap, ssap, control):
    # Ethernet header (dest MAC, src MAC, type/length)
    eth_dst = b'\xaa\xbb\xcc\xdd\xee\xff'
    eth_src = b'\x11\x22\x33\x44\x55\x66'
    eth_type = struct.pack('!H', 46)  # Length field, <1500 triggers 802.3+LLC
    # LLC header: DSAP, SSAP, Control
    llc_hdr = struct.pack('BBB', dsap, ssap, control)
    # Pad payload to minimum Ethernet frame
    payload = eth_dst + eth_src + eth_type + llc_hdr + b'\x00' * (60 - 14 - 3)
    return payload

# LLC protocol names from pcap_nametollc table (see pcap-namedb.c)
# We'll use some common ones: SNAP (0xaa), IP (0x06), NetBEUI (0xf8), etc.
llc_seeds = [
    (0xaa, 0xaa, 0x03),  # SNAP
    (0x06, 0x06, 0x03),  # IP
    (0xf8, 0xf8, 0x03),  # NetBEUI
    (0xe0, 0xe0, 0x03),  # PROWAY
    (0xfe, 0xfe, 0x03),  # ISO
]

for i, (dsap, ssap, control) in enumerate(llc_seeds):
    pcap_data = PCAP_GLOBAL_HEADER
    pkt = make_llc_packet(dsap, ssap, control)
    pcap_data += make_pcap_packet(pkt)
    with open(f"seed_{i+1}.pcap", "wb") as f:
        f.write(pcap_data)
