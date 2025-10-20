import struct, random, time, os

########################################################################
# Configuration
########################################################################

DLT_EN10MB = 1  # Ethernet

TRICKY_FILTERS = [
    # Deep VLAN stack + variable offset
    "vlan 100 && vlan 200 && vlan 300 && ip[0] & 0xf != 5",

    # protochain recursion on UDP
    "protochain udp and (port 53 or 5353)",

    # Slice & bitwise arith
    "ether[12:2] == 0x8100 and ip[6:2] & 0x1fff != 0",

    # Geneve special-case path
    "geneve || (udp dst port 2152 and gtp)",

    # Length test with relational operator
    "len >= 1500 and not tcp",

    # PF keywords (hit error branches if disabled)
    'pf_ifname "eth0" and pf_rnr 4',

    # Wild host/port name resolution
    'host "example.com" and tcp port "http-alt"',

    # MPLS stack depth book-keeping
    "mpls 100 && mpls 200 && proto 47",

    # Negative offsets into TCP options (forces bounds checks)
    "tcp[((tcp[12] & 0xf0) >> 2):4] = 0x47455420",

    # IPv6 + extension-header chain
    "ip6 and (fragment or hopopt or dst)"
]

########################################################################
# Pcap builder helpers
########################################################################

def _pcap_global_hdr(snaplen=65535, dlt=DLT_EN10MB):
    return struct.pack(
        "<IHHIIII",
        0xa1b2c3d4,  # magic
        2, 4,        # version
        0, 0,        # thiszone, sigfigs
        snaplen,
        dlt
    )

def _pcap_packet_hdr(pkt_len, ts=None):
    if ts is None:
        ts = time.time()
    ts_sec  = int(ts)
    ts_usec = int((ts - ts_sec) * 1_000_000)
    return struct.pack("<IIII", ts_sec, ts_usec, pkt_len, pkt_len)

def make_min_eth_frame(payload_len=46):
    head = b"\x00" * 12 + b"\x08\x00"  # Ethernet header, type = IPv4
    body = b"\x00" * max(46, payload_len)
    return head + body

def build_pcap_bytes(packet_bytes=None):
    if packet_bytes is None:
        packet_bytes = make_min_eth_frame()
    return _pcap_global_hdr() + _pcap_packet_hdr(len(packet_bytes)) + packet_bytes

def build_fuzzer_input(filter_str: str, packet_bytes=None) -> bytes:
    if len(filter_str) > 255:
        raise ValueError("filter too long for single-byte length field")
    filt = filter_str.encode() + b"\x00"
    blob = bytes([len(filt)]) + filt
    blob += build_pcap_bytes(packet_bytes)
    return blob

########################################################################
# Corpus generation
########################################################################

if __name__ == "__main__":
    os.makedirs("afl_seeds", exist_ok=True)
    for i in range(10):
        filt = random.choice(TRICKY_FILTERS)
        blob = build_fuzzer_input(filt)
        with open(f"afl_seeds/seed_{i:02d}", "wb") as f:
            f.write(blob)
        print(f"Wrote afl_seeds/seed_{i:02d}  | filter = {filt}")

