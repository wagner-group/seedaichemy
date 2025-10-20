#!/bin/bash
trap 'echo "Received termination signal. Shutting down..."; exit 0' SIGTERM SIGINT
set -e

# Set a permissive umask so that new files are created with broad permissions.
umask 000

# Set the default corpus, output directory, and corpus minimization output directory if not provided.
: "${CORPUS_DIR:=/corpus}"
: "${OUTPUT_DIR:=/afl-output}"

# Fuzzer binary (your compiled fuzzing target)
: "${FUZZER_BIN:=/home/fuzz/bplist_fuzzer}"

# If FUZZER_ID is not provided, use the container's hostname (ensuring uniqueness in scaled environments)
if [ -z "$FUZZER_ID" ]; then
    FUZZER_ID=$(hostname)
fi

echo "Using FUZZER_ID: $FUZZER_ID"

MODE=$1
shift || true
# MODE=${1:-fuzz}      # if no first argument, default to "fuzz"

echo "Mode: $MODE"

echo "Input corpus: $CORPUS_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Fuzzer binary: $FUZZER_BIN"
echo "Running afl-fuzz in master mode."

exec afl-fuzz -M "$FUZZER_ID" -i "$CORPUS_DIR" -o "$OUTPUT_DIR" -- "$FUZZER_BIN" @@
