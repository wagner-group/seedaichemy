#!/bin/bash
set -e

echo "core" | tee /proc/sys/kernel/core_pattern

# Set a permissive umask so that new files are created with broad permissions.
umask 000

# One-time seed copy
if [ -d "/init_corpus" ] && [ ! -f "/corpus/.copied" ]; then
    echo "[+] Seeding /corpus from /init_corpus"
    mkdir -p /corpus
    cp -r /init_corpus/* /corpus/ || true
    touch /corpus/.copied
fi

: "${FUZZER_BIN:=$OUT/fuzz_both}"

# If FUZZER_ID is not provided, use the container's hostname (ensuring uniqueness in scaled environments)
if [ -z "$FUZZER_ID" ]; then
    FUZZER_ID=$(hostname)
fi
: "${CODE_DIR:=/src/libpcap}"
: "${PROFILE_DIR:=${OUTPUT_DIR}/${FUZZER_ID}/profraw}"
: "${REPORT_DIR:=${OUTPUT_DIR}/llvm-cov-web}"
# Step 1: Build the target
cd "$SRC"
./build.sh

# Step 2: Run AFL++ fuzzer
echo "Input corpus: $CORPUS_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Fuzzer binary: $FUZZER_BIN"
echo "Running afl-fuzz in master mode."
exec timeout 25h afl-fuzz -M "$FUZZER_ID" -i "$CORPUS_DIR" -o "$OUTPUT_DIR" -- "$FUZZER_BIN" @@


