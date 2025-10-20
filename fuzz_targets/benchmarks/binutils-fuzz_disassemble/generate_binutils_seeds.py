import os
import struct

# Directory to save seeds
os.makedirs("seeds", exist_ok=True)

# List of example seeds for different architectures
# These are tuples: (filename_prefix, raw_bytes, flavour, mach, arch)
# You can get mach/arch from binutils/bfd headers (like archures.c or include/bfd.h)

seed_specs = [
    # x86_64 (arch = 3, mach = 62)
    ("x86_64_mov", b"\x48\x89\xe5", 0, 62, 3),  # mov rbp, rsp

    # x86 (arch = 3, mach = 3)
    ("x86_push", b"\x55", 0, 3, 3),  # push ebp

    # ARM (arch = 40, mach = 0)
    ("arm_nop", b"\x00\xf0\x20\xe3", 0, 0, 40),  # NOP (MOV R0, R0)

    # AArch64 (arch = 42, mach = 0)
    ("aarch64_nop", b"\x1f\x20\x03\xd5", 0, 0, 42),  # NOP

    # MIPS (arch = 8, mach = 8)
    ("mips_nop", b"\x00\x00\x00\x00", 0, 8, 8),  # NOP (SLL $0, $0, 0)
]

for name, insn_bytes, flavour, mach, arch in seed_specs:
    fname = f"seeds/{name}.bin"

    # Construct the trailing 10 bytes: [flavour][mach (8 bytes little endian)][arch]
    trailer = struct.pack("<BQB", flavour, mach, arch)

    with open(fname, "wb") as f:
        f.write(insn_bytes)
        f.write(trailer)

    print(f"Generated {fname} with arch={arch}, mach={mach}, flavour={flavour}")

