#!/bin/bash
trap 'echo "Received termination signal. Shutting down..."; exit 0' SIGTERM SIGINT
set -e

# Set a permissive umask so that new files are created with broad permissions.
umask 000

# Set the defaults if not provided.
: "${CORPUS_DIR:=/corpus}"
: "${OUTPUT_DIR:=/afl-output}"
: "${FUZZER_ID:=}"
: "${FUZZER_BIN:=/out/libxml2_reader_fuzzer}"


# Unique ID: master vs secondaries
if [ -z "$FUZZER_ID" ]; then
    FUZZER_ID=$(hostname)
fi

echo "Using FUZZER_ID: $FUZZER_ID"
echo "[*] Running afl-fuzz on $FUZZER_BIN …"

if [ "$FUZZER_ID" = "master" ]; then
    echo "→ Master mode"
    exec afl-fuzz -M "$FUZZER_ID" \
        -i "$CORPUS_DIR" \
        -o "$OUTPUT_DIR" \
        -f /tmp/input \
        -- "$FUZZER_BIN"
else
    echo "→ Secondary mode"
    exec afl-fuzz -S "$FUZZER_ID" \
        -i "$CORPUS_DIR" \
        -o "$OUTPUT_DIR" \
        -f /tmp/input \
        -- "$FUZZER_BIN"
fi
