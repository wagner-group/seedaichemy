#!/bin/bash
set -e

echo "core" | tee /proc/sys/kernel/core_pattern

# Set a permissive umask so that new files are created with broad permissions.
umask 000

: "${FUZZER_BIN:=$OUT/fuzz_both}"

# If FUZZER_ID is not provided, use the container's hostname (ensuring uniqueness in scaled environments)
if [ -z "$FUZZER_ID" ]; then
    FUZZER_ID=$(hostname)
fi

# Step 1: Build the target
cd "$SRC"
./build.sh

# Step 2: Run AFL++ fuzzer
echo "Input corpus: $CORPUS_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Fuzzer binary: $FUZZER_BIN"
echo "Running afl-fuzz in master mode."

exec afl-fuzz -M "$FUZZER_ID" -i "$CORPUS_DIR" -o "$OUTPUT_DIR" -- "$FUZZER_BIN" @@
